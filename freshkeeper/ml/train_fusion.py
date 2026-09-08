"""Train the fusion model and its two ablation baselines.

Three models are trained on identical splits:

    vision_only   the CNN embedding alone, classified into three states
    sensor_only   the five sensor features alone
    fusion        both, joined late

The comparison is the point. If fusion does not beat both single-modality
baselines, the gas sensors, the load cell and the DHT22 are not earning their
place in the bill of materials, and the honest conclusion would be to ship a
camera and nothing else.

Read the provenance warning in freshkeeper.ml.sensor_corpus before quoting any
number this produces. The images are real; the sensor features are simulated.

Run:  python -m freshkeeper.ml.train_fusion
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from tensorflow import keras
from tensorflow.keras import layers

from .model import (
    CLASS_NAMES, build_fusion_model, build_sensor_only_model, compile_multiclass,
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "sensor_corpus"
MODEL_DIR = ROOT / "models"
RESULTS = ROOT / "results"

EPOCHS = 60
BATCH_SIZE = 64
SEED = 20260908


def load(split: str):
    return (
        np.load(CORPUS / f"{split}_embedding.npy"),
        np.load(CORPUS / f"{split}_sensor.npy"),
        np.load(CORPUS / f"{split}_y.npy"),
    )


def standardiser(train_sensor: np.ndarray):
    """Z-score parameters from the training split only.

    Fitting the scaler on all splits leaks test-set statistics into training.
    The effect is small for five features, but it is free to avoid and
    impossible to argue away afterwards.

    The five channels span ppm, degrees, percent and grams; without scaling,
    humidity around 85 dominates the first layer's gradients purely because
    of its magnitude.
    """
    mean = train_sensor.mean(axis=0)
    std = train_sensor.std(axis=0)
    std[std < 1e-6] = 1.0
    return mean, std


def build_vision_only(dropout: float = 0.3) -> keras.Model:
    """Three-class classifier over the CNN embedding alone."""
    inputs = keras.Input(shape=(1280,), name="image_embedding")
    x = layers.Dense(256, activation="relu")(inputs)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(dropout)(x)
    outputs = layers.Dense(len(CLASS_NAMES), activation="softmax", name="state")(x)
    return keras.Model(inputs, outputs, name="vision_only_model")


def fit(model, train_inputs, ytr, val_inputs, yva, name: str) -> dict:
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_accuracy", mode="max",
                                      patience=12, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                          patience=5, min_lr=1e-6),
    ]
    start = time.time()
    history = model.fit(
        train_inputs, ytr, validation_data=(val_inputs, yva),
        epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=0, callbacks=callbacks,
    )
    elapsed = time.time() - start
    best = float(max(history.history["val_accuracy"]))
    print(f"  {name:12s} {len(history.history['loss']):3d} epochs  "
          f"{elapsed:5.1f}s  best val_acc={best:.4f}")
    return {
        "epochs_run": len(history.history["loss"]),
        "seconds": elapsed,
        "best_val_accuracy": best,
        "history": {k: [float(v) for v in vals] for k, vals in history.history.items()},
    }


def main() -> int:
    keras.utils.set_random_seed(SEED)
    MODEL_DIR.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)

    emb_tr, sen_tr, ytr = load("train")
    emb_va, sen_va, yva = load("val")

    mean, std = standardiser(sen_tr)
    np.save(MODEL_DIR / "sensor_scaler.npy", np.stack([mean, std]))
    ztr = (sen_tr - mean) / std
    zva = (sen_va - mean) / std

    print(f"train {len(ytr)}  val {len(yva)}  classes {CLASS_NAMES}")
    report = {}

    print("\nTraining:")
    vision = compile_multiclass(build_vision_only())
    report["vision_only"] = fit(vision, emb_tr, ytr, emb_va, yva, "vision_only")
    vision.save(MODEL_DIR / "vision_only.keras")

    sensor = compile_multiclass(build_sensor_only_model())
    report["sensor_only"] = fit(sensor, ztr, ytr, zva, yva, "sensor_only")
    sensor.save(MODEL_DIR / "sensor_only.keras")

    # Naive late fusion: raw 1280-wide embedding straight into the join.
    fusion_raw = compile_multiclass(build_fusion_model(image_projection=None))
    report["fusion_raw"] = fit(fusion_raw, [emb_tr, ztr], ytr,
                               [emb_va, zva], yva, "fusion_raw")
    fusion_raw.save(MODEL_DIR / "fusion_raw.keras")

    # Balanced late fusion: visual embedding projected to 64 first.
    fusion = compile_multiclass(build_fusion_model(image_projection=64))
    report["fusion"] = fit(fusion, [emb_tr, ztr], ytr, [emb_va, zva], yva, "fusion")
    fusion.save(MODEL_DIR / "fusion.keras")

    report["config"] = {
        "epochs": EPOCHS, "batch_size": BATCH_SIZE, "seed": SEED,
        "sensor_mean": mean.tolist(), "sensor_std": std.tolist(),
        "train_n": int(len(ytr)), "val_n": int(len(yva)),
    }
    with (RESULTS / "fusion_training.json").open("w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWrote {RESULTS / 'fusion_training.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
