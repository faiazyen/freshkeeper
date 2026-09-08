"""Train the visual fresh/rotten classifier.

Two stages, which is the standard transfer-learning recipe:

Stage 1 fits only the classifier head, with the backbone frozen. Because the
backbone is frozen its outputs never change, so this stage trains against the
cached embeddings and takes seconds.

Stage 2 unfreezes the top of the backbone and fine-tunes it on the images
themselves at a tenth of the learning rate. Fine-tuning from a randomly
initialised head would destroy the pretrained filters in the first few batches,
which is why stage 1 has to happen first.

Augmentation is applied only in stage 2, and only to the training split. Flips,
small rotations, brightness and zoom are all label-preserving for this task: a
rotated strawberry is still a rotten strawberry. Nothing that changes colour
balance aggressively is used, because colour is most of the signal here.

Run:  python -m freshkeeper.ml.train_cnn
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras

from .model import IMAGE_SIZE, build_visual_cnn, build_visual_head, compile_binary

ROOT = Path(__file__).resolve().parents[2]
EMB_DIR = ROOT / "data" / "embeddings"
_NAIVE_MANIFEST = ROOT / "data" / "processed" / "manifest.csv"
_GROUPED_MANIFEST = ROOT / "data" / "processed" / "manifest_grouped.csv"
MANIFEST = _GROUPED_MANIFEST if _GROUPED_MANIFEST.exists() else _NAIVE_MANIFEST
MODEL_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

STAGE1_EPOCHS = 40
STAGE2_EPOCHS = 8
STAGE2_UNFREEZE_LAYERS = 40
BATCH_SIZE = 32
SEED = 20260908


def load_split(split: str, emb_dir: Path = EMB_DIR):
    x = np.load(emb_dir / f"{split}_x.npy")
    y = np.load(emb_dir / f"{split}_y.npy")
    return x, y


def image_dataset(split: str, shuffle: bool, augment: bool) -> tf.data.Dataset:
    with MANIFEST.open() as fh:
        rows = [r for r in csv.DictReader(fh) if r["split"] == split]
    paths = [str(ROOT / r["path"]) for r in rows]
    labels = [int(r["label"]) for r in rows]

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(len(paths), seed=SEED, reshuffle_each_iteration=True)

    def _load(path, label):
        img = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
        img = tf.image.resize(img, IMAGE_SIZE)
        return img, label

    ds = ds.map(_load, num_parallel_calls=tf.data.AUTOTUNE)

    if augment:
        def _augment(img, label):
            img = tf.image.random_flip_left_right(img, seed=SEED)
            img = tf.image.random_brightness(img, max_delta=25.0, seed=SEED)
            img = tf.image.random_contrast(img, 0.85, 1.15, seed=SEED)
            return tf.clip_by_value(img, 0.0, 255.0), label
        ds = ds.map(_augment, num_parallel_calls=tf.data.AUTOTUNE)

    # No preprocess_input here. build_visual_cnn applies it as the first layer
    # of the model, so that inference takes raw pixels and cannot be fed
    # wrongly-scaled input by a caller. Normalising here as well would map the
    # already-[-1,1] tensor into a band about 0.008 wide, which trains to
    # exactly chance, as it did on the first run.
    return ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


def main() -> int:
    global MANIFEST
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=None,
                        help="split manifest to train on (default: grouped if present)")
    parser.add_argument("--tag", default="",
                        help="suffix for the saved model and history, e.g. naive_split")
    parser.add_argument("--embedding-dir", default=None,
                        help="directory holding {train,val,test}_x.npy for stage 1")
    args = parser.parse_args()
    if args.manifest:
        MANIFEST = Path(args.manifest).resolve()
    emb_dir = Path(args.embedding_dir) if args.embedding_dir else EMB_DIR
    suffix = f"_{args.tag}" if args.tag else ""

    MODEL_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    keras.utils.set_random_seed(SEED)

    history_log: dict[str, list] = {}

    # ---- Stage 1: head over cached embeddings --------------------------
    print("Stage 1: training classifier head on frozen-backbone embeddings")
    xtr, ytr = load_split("train", emb_dir)
    xva, yva = load_split("val", emb_dir)

    head = compile_binary(build_visual_head(), learning_rate=1e-3)
    t0 = time.time()
    h1 = head.fit(
        xtr, ytr,
        validation_data=(xva, yva),
        epochs=STAGE1_EPOCHS,
        batch_size=BATCH_SIZE,
        verbose=0,
        callbacks=[keras.callbacks.EarlyStopping(
            monitor="val_auc", mode="max", patience=8, restore_best_weights=True)],
    )
    stage1_time = time.time() - t0
    history_log["stage1"] = {k: [float(v) for v in vals] for k, vals in h1.history.items()}
    print(f"  {len(h1.history['loss'])} epochs in {stage1_time:.1f}s  "
          f"val_acc={h1.history['val_accuracy'][-1]:.4f} "
          f"val_auc={h1.history['val_auc'][-1]:.4f}")

    # ---- Stage 2: fine-tune the top of the backbone --------------------
    print(f"\nStage 2: fine-tuning top {STAGE2_UNFREEZE_LAYERS} backbone layers")
    model = build_visual_cnn()
    # Carry the stage-1 head weights across so fine-tuning starts from a
    # sensible decision boundary rather than random noise.
    model.get_layer("p_rotten").set_weights(head.get_layer("p_rotten").get_weights())

    backbone = model.backbone
    backbone.trainable = True
    for layer in backbone.layers[:-STAGE2_UNFREEZE_LAYERS]:
        layer.trainable = False
    # BatchNorm statistics must stay frozen. Updating them on small batches
    # from a new domain is a classic way to make fine-tuning diverge.
    for layer in backbone.layers:
        if isinstance(layer, keras.layers.BatchNormalization):
            layer.trainable = False

    compile_binary(model, learning_rate=1e-4)
    trainable = sum(int(np.prod(w.shape)) for w in model.trainable_weights)
    print(f"  trainable parameters: {trainable:,}")

    train_ds = image_dataset("train", shuffle=True, augment=True)
    val_ds = image_dataset("val", shuffle=False, augment=False)

    # Sanity check before any fine-tuning: with the stage-1 head transferred,
    # the assembled model must already score what stage 1 scored. If it does
    # not, the image pipeline disagrees with the embedding pipeline, and
    # fine-tuning from here would be training on mangled input.
    pre = model.evaluate(val_ds, verbose=0, return_dict=True)
    print(f"  transferred head, pre-fine-tune val_acc={pre['accuracy']:.4f} "
          f"val_auc={pre['auc']:.4f}")
    if pre["accuracy"] < 0.90:
        raise RuntimeError(
            f"Assembled model scores {pre['accuracy']:.3f} on validation but "
            f"stage 1 scored {h1.history['val_accuracy'][-1]:.3f}. The image "
            "pipeline and the embedding pipeline are not equivalent."
        )

    t0 = time.time()
    h2 = model.fit(
        train_ds, validation_data=val_ds, epochs=STAGE2_EPOCHS, verbose=2,
        callbacks=[
            keras.callbacks.EarlyStopping(
                monitor="val_auc", mode="max", patience=3, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
        ],
    )
    stage2_time = time.time() - t0
    history_log["stage2"] = {k: [float(v) for v in vals] for k, vals in h2.history.items()}
    print(f"  {len(h2.history['loss'])} epochs in {stage2_time/60:.1f} min")

    model.save(MODEL_DIR / f"visual_cnn{suffix}.keras")
    # Serialise fully before opening the file: an exception raised mid-dump
    # (a relative manifest path once did it) otherwise leaves a truncated,
    # unreadable result file behind.
    payload = json.dumps({
            "history": history_log,
            "stage1_seconds": stage1_time,
            "stage2_seconds": stage2_time,
            "manifest": str(MANIFEST.resolve().relative_to(ROOT.resolve())),
            "config": {
                "stage1_epochs": STAGE1_EPOCHS, "stage2_epochs": STAGE2_EPOCHS,
                "unfrozen_layers": STAGE2_UNFREEZE_LAYERS,
                "batch_size": BATCH_SIZE, "seed": SEED,
            },
        }, indent=2)
    (RESULTS_DIR / f"cnn_training_history{suffix}.json").write_text(payload)
    print(f"\nSaved {MODEL_DIR / f'visual_cnn{suffix}.keras'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
