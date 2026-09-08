"""Convert the trained models to TensorFlow Lite and measure inference cost.

The target is a Raspberry Pi 4, so the numbers that matter are model size and
per-item latency, not just accuracy. Three variants are produced for each
model so the trade-off is visible rather than asserted:

    float32     straight conversion, no quantisation
    float16     weights halved; usually free accuracy-wise
    int8        full integer quantisation against a representative dataset

int8 needs representative data to calibrate activation ranges. Feeding it
random noise produces ranges that do not match anything real and quietly
destroys accuracy, so a sample of the actual training split is used.

Latency here is measured on the development machine (Apple silicon), not on a
Pi. ARM Cortex-A72 is materially slower, so the thesis reports these as
relative figures and scales them by a published benchmark ratio rather than
pretending they are Pi measurements.

Run:  python -m freshkeeper.ml.export_tflite
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "sensor_corpus"
MODEL_DIR = ROOT / "models"
RESULTS = ROOT / "results"
TFLITE_DIR = MODEL_DIR / "tflite"

BENCHMARK_RUNS = 200
WARMUP_RUNS = 20
CALIBRATION_SAMPLES = 200


def _make_representative(arrays: list[np.ndarray]):
    """Build the calibration callable TFLiteConverter expects.

    It must be a callable returning a *fresh* generator on each invocation --
    the converter iterates it more than once. Handing it an already-created
    generator raises "'generator' object is not callable", and handing it one
    that is exhausted silently calibrates against nothing.
    """
    def representative():
        for i in range(min(CALIBRATION_SAMPLES, len(arrays[0]))):
            yield [array[i:i + 1].astype(np.float32) for array in arrays]
    return representative


def convert(model: keras.Model, mode: str, representative=None) -> bytes:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    if mode == "float16":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    elif mode == "int8":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative
    return converter.convert()


def benchmark(tflite_bytes: bytes, inputs: list[np.ndarray]) -> dict:
    """Time single-item inference, reporting the distribution not just a mean.

    A mean alone hides the tail, and the tail is what a user experiences as a
    stutter. The 95th percentile is reported alongside it.
    """
    interpreter = tf.lite.Interpreter(model_content=tflite_bytes)
    interpreter.allocate_tensors()
    details = interpreter.get_input_details()
    out_index = interpreter.get_output_details()[0]["index"]

    def run(i: int) -> None:
        for detail, array in zip(details, inputs):
            sample = array[i:i + 1].astype(detail["dtype"])
            interpreter.set_tensor(detail["index"], sample)
        interpreter.invoke()
        interpreter.get_tensor(out_index)

    for i in range(WARMUP_RUNS):
        run(i % len(inputs[0]))

    timings = []
    for i in range(BENCHMARK_RUNS):
        start = time.perf_counter()
        run(i % len(inputs[0]))
        timings.append((time.perf_counter() - start) * 1000.0)

    array = np.array(timings)
    return {
        "mean_ms": float(array.mean()),
        "median_ms": float(np.median(array)),
        "p95_ms": float(np.percentile(array, 95)),
        "min_ms": float(array.min()),
        "max_ms": float(array.max()),
        "runs": BENCHMARK_RUNS,
    }


def main() -> int:
    TFLITE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(exist_ok=True)

    emb = np.load(CORPUS / "test_embedding.npy").astype(np.float32)
    sen = np.load(CORPUS / "test_sensor.npy").astype(np.float32)
    mean, std = np.load(MODEL_DIR / "sensor_scaler.npy")
    z = ((sen - mean) / std).astype(np.float32)

    emb_tr = np.load(CORPUS / "train_embedding.npy").astype(np.float32)
    sen_tr = np.load(CORPUS / "train_sensor.npy").astype(np.float32)
    z_tr = ((sen_tr - mean) / std).astype(np.float32)

    targets = [
        ("fusion", MODEL_DIR / "fusion.keras", [emb, z],
         _make_representative([emb_tr, z_tr])),
        ("sensor_only", MODEL_DIR / "sensor_only.keras", [z],
         _make_representative([z_tr])),
    ]

    report: dict = {
        "host": {
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
        },
        "note": ("Latency measured on the development host, not on a Raspberry "
                 "Pi 4. Reported for relative comparison between variants."),
        "models": {},
    }

    for name, path, inputs, representative in targets:
        if not path.exists():
            continue
        model = keras.models.load_model(path)
        keras_size = path.stat().st_size
        entry = {"keras_bytes": keras_size, "variants": {}}
        print(f"\n{name}  (Keras {keras_size/1e6:.2f} MB)")

        for mode in ("float32", "float16", "int8"):
            try:
                blob = convert(model, mode, representative if mode == "int8" else None)
            except Exception as exc:
                print(f"  {mode:8s} conversion failed: {str(exc)[:70]}")
                entry["variants"][mode] = {"error": str(exc)[:200]}
                continue

            out_path = TFLITE_DIR / f"{name}_{mode}.tflite"
            out_path.write_bytes(blob)
            timing = benchmark(blob, inputs)

            # Accuracy of the converted model, so a size win that costs
            # accuracy cannot pass unnoticed.
            interpreter = tf.lite.Interpreter(model_content=blob)
            interpreter.allocate_tensors()
            details = interpreter.get_input_details()
            out_index = interpreter.get_output_details()[0]["index"]
            preds = []
            for i in range(len(inputs[0])):
                for detail, array in zip(details, inputs):
                    interpreter.set_tensor(detail["index"],
                                           array[i:i+1].astype(detail["dtype"]))
                interpreter.invoke()
                preds.append(interpreter.get_tensor(out_index)[0].argmax())
            y = np.load(CORPUS / "test_y.npy")
            accuracy = float((np.array(preds) == y).mean())

            entry["variants"][mode] = {
                "bytes": len(blob),
                "megabytes": round(len(blob) / 1e6, 3),
                "compression_vs_keras": round(keras_size / len(blob), 2),
                "test_accuracy": accuracy,
                **timing,
            }
            print(f"  {mode:8s} {len(blob)/1e6:6.3f} MB  "
                  f"{timing['mean_ms']:6.3f} ms mean  "
                  f"{timing['p95_ms']:6.3f} ms p95  acc={accuracy:.4f}")

        report["models"][name] = entry

    with (RESULTS / "tflite_benchmark.json").open("w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWrote {RESULTS / 'tflite_benchmark.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
