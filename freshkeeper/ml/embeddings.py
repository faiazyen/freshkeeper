"""Precompute frozen-backbone embeddings for the image corpus.

Stage-one transfer learning holds the backbone frozen, which means every epoch
recomputes exactly the same 1280-dimensional vector for every image. Doing that
once and caching it turns an hours-long CPU job into a few minutes, and gives
numerically identical results.

The cached embeddings are also what the fusion model consumes, so this runs
once and serves both training stages.

Run:  python -m freshkeeper.ml.embeddings
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras

from .model import IMAGE_SIZE, build_backbone

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "processed" / "manifest.csv"
GROUPED_MANIFEST = ROOT / "data" / "processed" / "manifest_grouped.csv"
OUT_DIR = ROOT / "data" / "embeddings"
BATCH_SIZE = 64


def load_manifest() -> list[dict]:
    """Prefer the group-aware manifest once the audit has produced one.

    The naive manifest splits near-duplicate variants across train and test,
    which inflates every score computed from it. See scripts/audit_dataset.py.
    """
    path = GROUPED_MANIFEST if GROUPED_MANIFEST.exists() else MANIFEST
    with path.open() as fh:
        return list(csv.DictReader(fh))


def _decode(path: tf.Tensor) -> tf.Tensor:
    raw = tf.io.read_file(path)
    img = tf.io.decode_jpeg(raw, channels=3)
    img = tf.image.resize(img, IMAGE_SIZE)
    return keras.applications.mobilenet_v2.preprocess_input(img)


def build_pipeline(paths: list[str]) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices(paths)
    ds = ds.map(_decode, num_parallel_calls=tf.data.AUTOTUNE)
    return ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)


def main() -> int:
    rows = load_manifest()
    if not rows:
        print("Empty manifest; run scripts/prepare_dataset.py first.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # The audit already embedded the whole corpus in manifest order. Reuse it
    # rather than paying for 12,335 forward passes again.
    cache = OUT_DIR / "corpus_x.npy"
    corpus = np.load(cache) if cache.exists() else None
    backbone = None if corpus is not None else build_backbone(trainable=False)

    for split in ("train", "val", "test"):
        idx = [i for i, r in enumerate(rows) if r["split"] == split]
        subset = [rows[i] for i in idx]
        labels = np.array([int(r["label"]) for r in subset], dtype=np.int32)
        fruits = np.array([r["fruit_type"] for r in subset])

        start = time.time()
        if corpus is not None:
            features = corpus[idx]
        else:
            paths = [str(ROOT / r["path"]) for r in subset]
            features = backbone.predict(build_pipeline(paths), verbose=0)
        elapsed = time.time() - start

        np.save(OUT_DIR / f"{split}_x.npy", features.astype(np.float32))
        np.save(OUT_DIR / f"{split}_y.npy", labels)
        np.save(OUT_DIR / f"{split}_fruit.npy", fruits)
        print(f"  {split:5s} {features.shape}  {elapsed:6.2f}s")

    print(f"\nEmbeddings written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
