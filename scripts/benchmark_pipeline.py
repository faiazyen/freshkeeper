"""Measure end-to-end per-item inference cost.

The TFLite figures for the fusion head alone are misleadingly small: the head
is 0.16 MB and runs in microseconds, but it cannot run until MobileNetV2 has
turned a photograph into an embedding, and that is where essentially all the
work is. This script times the whole path a real measurement cycle takes:

    JPEG decode -> resize -> preprocess -> backbone -> fusion head -> label

Numbers are from the development host. The thesis scales them to a Raspberry
Pi 4 using a published SPECint-style ratio rather than claiming they are Pi
measurements, and says so.

Run:  python scripts/benchmark_pipeline.py
"""

from __future__ import annotations

import csv
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freshkeeper.ml.model import CLASS_NAMES, IMAGE_SIZE, build_backbone  # noqa: E402

MANIFEST = ROOT / "data" / "processed" / "manifest_grouped.csv"
MODEL_DIR = ROOT / "models"
CORPUS = ROOT / "data" / "sensor_corpus"
RESULTS = ROOT / "results"

RUNS = 60
WARMUP = 10

#: Single-core integer throughput ratio, Apple M-series performance core to
#: Raspberry Pi 4 Cortex-A72 at 1.5 GHz. Used only to state an expected Pi
#: figure alongside the measured host figure; it is an estimate, not a
#: measurement, and the thesis labels it as such.
PI4_SLOWDOWN_FACTOR = 7.5


def main() -> int:
    with MANIFEST.open() as fh:
        rows = [r for r in csv.DictReader(fh) if r["split"] == "test"]
    paths = [str(ROOT / r["path"]) for r in rows[:RUNS + WARMUP]]

    backbone = build_backbone(trainable=False)
    head = keras.models.load_model(MODEL_DIR / "fusion.keras")
    mean, std = np.load(MODEL_DIR / "sensor_scaler.npy")
    sensors = np.load(CORPUS / "test_sensor.npy").astype(np.float32)

    stages: dict[str, list[float]] = {
        "decode_resize": [], "preprocess": [], "backbone": [],
        "fusion_head": [], "total": [],
    }

    for i, path in enumerate(paths):
        t_start = time.perf_counter()

        t0 = time.perf_counter()
        raw = tf.io.read_file(path)
        image = tf.io.decode_jpeg(raw, channels=3)
        image = tf.image.resize(image, IMAGE_SIZE)
        t1 = time.perf_counter()

        batch = keras.applications.mobilenet_v2.preprocess_input(
            tf.expand_dims(image, 0))
        t2 = time.perf_counter()

        embedding = backbone(batch, training=False)
        t3 = time.perf_counter()

        z = tf.constant(
            ((sensors[i % len(sensors)] - mean) / std).astype(np.float32)[None, :])
        probs = head([embedding, z], training=False).numpy()[0]
        _ = CLASS_NAMES[int(probs.argmax())]
        t4 = time.perf_counter()

        if i < WARMUP:
            continue
        stages["decode_resize"].append((t1 - t0) * 1000)
        stages["preprocess"].append((t2 - t1) * 1000)
        stages["backbone"].append((t3 - t2) * 1000)
        stages["fusion_head"].append((t4 - t3) * 1000)
        stages["total"].append((t4 - t_start) * 1000)

    report = {
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "tensorflow": tf.__version__,
        },
        "runs": len(stages["total"]),
        "stages_ms": {},
        "pi4_slowdown_factor": PI4_SLOWDOWN_FACTOR,
        "note": ("Measured on the development host. The projected Raspberry Pi 4 "
                 "figure is the host measurement multiplied by an assumed "
                 "single-core slowdown factor; it is an estimate, not a "
                 "measurement on hardware."),
    }

    print(f"{'stage':16s} {'mean':>8s} {'median':>8s} {'p95':>8s}   share")
    total_mean = float(np.mean(stages["total"]))
    for name, values in stages.items():
        arr = np.array(values)
        report["stages_ms"][name] = {
            "mean": float(arr.mean()), "median": float(np.median(arr)),
            "p95": float(np.percentile(arr, 95)),
            "share_of_total": float(arr.mean() / total_mean),
        }
        share = "" if name == "total" else f"{100*arr.mean()/total_mean:5.1f}%"
        print(f"{name:16s} {arr.mean():7.2f}ms {np.median(arr):7.2f}ms "
              f"{np.percentile(arr,95):7.2f}ms   {share}")

    projected = total_mean * PI4_SLOWDOWN_FACTOR
    report["projected_pi4_total_ms"] = projected
    # Six slots per cycle, one cycle every 30 minutes.
    report["cycle_budget_utilisation"] = projected * 6 / (30 * 60 * 1000)
    print(f"\nhost total          {total_mean:.2f} ms/item")
    print(f"projected Pi 4      {projected:.1f} ms/item (x{PI4_SLOWDOWN_FACTOR})")
    print(f"6 slots per cycle   {projected*6/1000:.2f} s of a 30-minute budget "
          f"({100*report['cycle_budget_utilisation']:.3f}%)")

    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "pipeline_benchmark.json").open("w") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nWrote {RESULTS / 'pipeline_benchmark.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
