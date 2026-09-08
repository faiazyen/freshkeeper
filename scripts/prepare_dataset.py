"""Decode the image corpus from HuggingFace parquet into a split on disk.

Source: Project-AgML/fresh_rotten_fruit_classification (CC-BY-4.0), the
augmented configuration, 12,335 JPEG images of eight commodities labelled
fresh or rotten.

The split is stratified on (commodity, label) jointly rather than on the label
alone. Stratifying on the label only would let, say, most of the strawberries
land in training and most of the pomegranates in test, and the test score would
then be measuring how well the model transfers between fruits rather than how
well it detects spoilage.

Run:  python scripts/prepare_dataset.py
"""

from __future__ import annotations

import csv
import io
import random
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
IMAGE_SIZE = (224, 224)  # MobileNetV2's native input size
SPLITS = {"train": 0.70, "val": 0.15, "test": 0.15}
SEED = 20260908
LABEL_NAMES = {0: "fresh", 1: "rotten"}


def main() -> int:
    files = sorted(RAW_DIR.glob("*.parquet"))
    if not files:
        print(f"No parquet files in {RAW_DIR}. Run scripts/download_dataset.sh first.")
        return 1

    # Group row references by (commodity, label) so the split is stratified.
    buckets: dict[tuple[str, int], list[tuple[Path, int]]] = defaultdict(list)
    for path in files:
        table = pq.read_table(path, columns=["label", "fruit_type"])
        for idx, (label, fruit) in enumerate(
                zip(table["label"].to_pylist(), table["fruit_type"].to_pylist())):
            buckets[(fruit, label)].append((path, idx))

    rng = random.Random(SEED)
    assignment: dict[tuple[Path, int], str] = {}
    for key, rows in sorted(buckets.items()):
        rng.shuffle(rows)
        n = len(rows)
        n_train = int(n * SPLITS["train"])
        n_val = int(n * SPLITS["val"])
        for i, row in enumerate(rows):
            if i < n_train:
                assignment[row] = "train"
            elif i < n_train + n_val:
                assignment[row] = "val"
            else:
                assignment[row] = "test"

    for split in SPLITS:
        for label in LABEL_NAMES.values():
            (OUT_DIR / split / label).mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    written = 0
    for path in files:
        table = pq.read_table(path)
        images = table["image"].to_pylist()
        labels = table["label"].to_pylist()
        fruits = table["fruit_type"].to_pylist()
        for idx in range(len(labels)):
            split = assignment[(path, idx)]
            label = labels[idx]
            fruit = fruits[idx]
            name = LABEL_NAMES[label]
            try:
                img = Image.open(io.BytesIO(images[idx]["bytes"])).convert("RGB")
            except Exception as exc:
                print(f"  skipping unreadable image {path.name}:{idx} ({exc})")
                continue
            img = img.resize(IMAGE_SIZE, Image.BILINEAR)
            filename = f"{fruit}_{idx:05d}_{path.stem[-1]}.jpg"
            out = OUT_DIR / split / name / filename
            img.save(out, quality=92)
            manifest_rows.append({
                "path": str(out.relative_to(ROOT)),
                "split": split,
                "label": label,
                "label_name": name,
                "fruit_type": fruit,
            })
            written += 1
            if written % 1000 == 0:
                print(f"  {written} images written")

    manifest = OUT_DIR / "manifest.csv"
    with manifest.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["path", "split", "label", "label_name", "fruit_type"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    counts: dict[str, int] = defaultdict(int)
    for row in manifest_rows:
        counts[row["split"]] += 1
    print(f"\nWrote {written} images -> {OUT_DIR}")
    for split in SPLITS:
        print(f"  {split:5s} {counts[split]:6d}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
