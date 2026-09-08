#!/usr/bin/env bash
# Download the image corpus.
#
# Project-AgML/fresh_rotten_fruit_classification, augmented configuration:
# 12,335 JPEGs of eight commodities labelled fresh or rotten, CC-BY-4.0.
# Roughly 840 MB over two parquet shards.
set -euo pipefail

DEST="$(dirname "$0")/../data/raw"
BASE="https://huggingface.co/datasets/Project-AgML/fresh_rotten_fruit_classification/resolve/main/augmented"

mkdir -p "$DEST"
for i in 0 1; do
  f="train-0000${i}-of-00002.parquet"
  if [[ -f "$DEST/$f" ]]; then
    echo "  $f already present"
  else
    echo "  fetching $f"
    curl -sSL --fail -o "$DEST/$f" "$BASE/$f"
  fi
done
echo "Dataset in $DEST"
