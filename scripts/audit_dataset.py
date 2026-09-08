"""Audit the image corpus for near-duplicate leakage and re-split by group.

Why this exists. The first training run scored 99.7% on validation, which is
not a believable number for spoilage classification from photographs. The
cause turned out to be the corpus itself: it is an augmented set, and variants
derived from the same original photograph were being split across train and
test. A model can memorise a photograph and appear to generalise.

There are no byte-identical duplicates, all 12,335 files hash differently --
so the problem is invisible to the obvious check. It shows up in feature
space: 27% of test images sat within cosine 0.95 of some training image.

What this script does:

1. Embeds every image once with the frozen backbone.
2. Builds a graph joining any pair above the similarity threshold.
3. Collapses connected components with union-find, so a whole family of
   variants becomes one group.
4. Splits by *group*, stratified on (commodity, label), so no group can
   straddle two splits.

The resulting accuracy is lower and means something.

Run:  python scripts/audit_dataset.py
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "data" / "processed" / "manifest.csv"
GROUPED_MANIFEST = ROOT / "data" / "processed" / "manifest_grouped.csv"
EMB_DIR = ROOT / "data" / "embeddings"
RESULTS = ROOT / "results"

SIMILARITY_THRESHOLD = 0.95
SPLITS = {"train": 0.70, "val": 0.15, "test": 0.15}
SEED = 20260908


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]  # path halving
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1


def embed_corpus(rows: list[dict]) -> np.ndarray:
    """Embed every image in manifest order with the frozen backbone."""
    import tensorflow as tf
    from tensorflow import keras
    from freshkeeper.ml.model import IMAGE_SIZE, build_backbone

    paths = [str(ROOT / r["path"]) for r in rows]

    def _decode(path):
        img = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
        img = tf.image.resize(img, IMAGE_SIZE)
        return keras.applications.mobilenet_v2.preprocess_input(img)

    ds = (tf.data.Dataset.from_tensor_slices(paths)
          .map(_decode, num_parallel_calls=tf.data.AUTOTUNE)
          .batch(64).prefetch(tf.data.AUTOTUNE))
    return build_backbone(trainable=False).predict(ds, verbose=0)


def main() -> int:
    with MANIFEST.open() as fh:
        rows = list(csv.DictReader(fh))
    print(f"Corpus: {len(rows)} images")

    cache = EMB_DIR / "corpus_x.npy"
    if cache.exists():
        features = np.load(cache)
        print(f"Loaded cached embeddings {features.shape}")
    else:
        print("Embedding corpus...")
        features = embed_corpus(rows)
        EMB_DIR.mkdir(parents=True, exist_ok=True)
        np.save(cache, features.astype(np.float32))
        print(f"  {features.shape}")

    unit = features / np.linalg.norm(features, axis=1, keepdims=True)

    # Join near-duplicates. Comparison is blocked to keep the 12k x 12k
    # similarity matrix off the heap in one piece.
    print(f"Linking pairs above cosine {SIMILARITY_THRESHOLD}...")
    uf = UnionFind(len(rows))
    edges = 0
    block = 512
    for i in range(0, len(unit), block):
        sims = unit[i:i + block] @ unit.T
        for local, row in enumerate(sims):
            gi = i + local
            row[gi] = -1.0  # never link an image to itself
            for gj in np.nonzero(row >= SIMILARITY_THRESHOLD)[0]:
                if gj > gi:
                    uf.union(gi, int(gj))
                    edges += 1

    groups: dict[int, list[int]] = defaultdict(list)
    for idx in range(len(rows)):
        groups[uf.find(idx)].append(idx)
    sizes = Counter(len(v) for v in groups.values())
    print(f"  {edges} linking pairs -> {len(groups)} groups "
          f"(was {len(rows)} independent images)")
    print("  group size distribution:")
    for size in sorted(sizes)[:8]:
        print(f"    size {size:3d}: {sizes[size]:5d} groups")
    largest = max(groups.values(), key=len)
    print(f"  largest group: {len(largest)} images")

    # Stratify groups on the (commodity, label) of their first member, then
    # split whole groups.
    rng = random.Random(SEED)
    by_stratum: dict[tuple[str, str], list[list[int]]] = defaultdict(list)
    for members in groups.values():
        head = rows[members[0]]
        by_stratum[(head["fruit_type"], head["label"])].append(members)

    assignment: dict[int, str] = {}
    for stratum, group_list in sorted(by_stratum.items()):
        rng.shuffle(group_list)
        total = sum(len(g) for g in group_list)
        target_train = total * SPLITS["train"]
        target_val = total * SPLITS["val"]
        running = 0
        for group in group_list:
            if running < target_train:
                split = "train"
            elif running < target_train + target_val:
                split = "val"
            else:
                split = "test"
            for idx in group:
                assignment[idx] = split
            running += len(group)

    for idx, row in enumerate(rows):
        row["naive_split"] = row["split"]
        row["split"] = assignment[idx]
        row["group_id"] = str(uf.find(idx))

    with GROUPED_MANIFEST.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["path", "split", "label", "label_name",
                            "fruit_type", "group_id", "naive_split"])
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(r["split"] for r in rows)
    print("\nGroup-aware split:")
    for split in SPLITS:
        print(f"  {split:5s} {counts[split]:6d}")

    # Confirm the fix: how similar is the new test set to the new train set?
    tr_idx = [i for i, r in enumerate(rows) if r["split"] == "train"]
    te_idx = [i for i, r in enumerate(rows) if r["split"] == "test"]
    TR, TE = unit[tr_idx], unit[te_idx]
    best = np.zeros(len(TE))
    for i in range(0, len(TE), 256):
        best[i:i + 256] = (TE[i:i + 256] @ TR.T).max(axis=1)
    leak = float((best >= SIMILARITY_THRESHOLD).mean())
    print(f"\nTest images within cosine {SIMILARITY_THRESHOLD} of a training "
          f"image: {leak * 100:.2f}% (was 27.2% under the naive split)")

    # The naive split's leakage is the number that motivated all of this, so
    # compute it here rather than quoting it from a console session.
    naive_tr = [i for i, r in enumerate(rows) if r.get("naive_split") == "train"]
    naive_te = [i for i, r in enumerate(rows) if r.get("naive_split") == "test"]
    naive_best = np.zeros(len(naive_te))
    NTR = unit[naive_tr]
    for i in range(0, len(naive_te), 256):
        naive_best[i:i + 256] = (unit[naive_te[i:i + 256]] @ NTR.T).max(axis=1)
    naive_leak = float((naive_best >= SIMILARITY_THRESHOLD).mean())
    print(f"Naive split, for the record: {naive_leak * 100:.2f}% of test images "
          f"within cosine {SIMILARITY_THRESHOLD} of a training image, median "
          f"nearest-neighbour similarity {np.median(naive_best):.3f}")

    # Label anomaly: fresh-apple files are named FreshOrange. Centroid cosines
    # settle whether the images or the filenames are wrong.
    def centroid(fruit, label):
        mask = np.array([r["fruit_type"] == fruit and r["label"] == label for r in rows])
        c = unit[mask].mean(axis=0)
        return c / np.linalg.norm(c)
    fa, ra, fo = centroid("apple", "0"), centroid("apple", "1"), centroid("orange", "0")
    anomaly = {"fresh_apple_vs_rotten_apple": float(fa @ ra),
               "fresh_apple_vs_fresh_orange": float(fa @ fo)}
    print(f"Fresh-apple centroid: cos to rotten-apple {anomaly['fresh_apple_vs_rotten_apple']:.3f}, "
          f"to fresh-orange {anomaly['fresh_apple_vs_fresh_orange']:.3f}")

    RESULTS.mkdir(exist_ok=True)
    report = {
        "naive_split": {
            "test_leakage_fraction": naive_leak,
            "nearest_neighbour_percentiles": {
                f"p{q}": float(np.percentile(naive_best, q)) for q in (50, 90, 95, 99, 100)},
        },
        "label_anomaly_centroid_cosine": anomaly,
        "corpus_size": len(rows),
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "linking_pairs": edges,
        "n_groups": len(groups),
        "largest_group": len(largest),
        "group_size_distribution": {str(k): v for k, v in sorted(sizes.items())},
        "split_counts": dict(counts),
        "residual_test_leakage_fraction": leak,
        "nearest_neighbour_percentiles": {
            f"p{q}": float(np.percentile(best, q)) for q in (50, 90, 95, 99, 100)
        },
    }
    with (RESULTS / "dataset_audit.json").open("w") as fh:
        json.dump(report, fh, indent=2)
    print(f"Wrote {RESULTS / 'dataset_audit.json'}")
    print(f"Wrote {GROUPED_MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
