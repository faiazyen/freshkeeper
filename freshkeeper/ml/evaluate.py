"""Evaluate every trained model on the held-out test split and plot the results.

Produces:
    results/evaluation.json          all metrics, machine-readable
    docs/figures/confusion_*.png     confusion matrices
    docs/figures/training_curves.png learning curves
    docs/figures/ablation.png        the modality comparison

Recall on the spoiled class is reported separately throughout, because the two
error directions do not cost the same. Calling a spoiled item fresh may make
somebody ill. Calling a fresh item spoiled wastes one piece of fruit, which is
the exact thing the system exists to prevent, so neither is free, but they
are not equal, and a single accuracy figure hides the difference.

Run:  python -m freshkeeper.ml.evaluate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
    precision_recall_fscore_support, roc_auc_score,
)
from tensorflow import keras

from .model import CLASS_NAMES

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "sensor_corpus"
EMB_DIR = ROOT / "data" / "embeddings"
MODEL_DIR = ROOT / "models"
RESULTS = ROOT / "results"
FIGURES = ROOT / "docs" / "figures"

PALETTE = {"fresh": "0.7", "marginal": "0.45", "spoiled": "0.2"}


def plot_confusion(cm: np.ndarray, labels: list[str], title: str, path: Path) -> None:
    """Confusion matrix with both counts and row-normalised percentages."""
    normalised = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(1.55 * len(labels) + 1.6, 1.45 * len(labels) + 1.4))
    im = ax.imshow(normalised, cmap="Greys", vmin=0, vmax=1)

    ax.set_xticks(range(len(labels)), [l.capitalize() for l in labels])
    ax.set_yticks(range(len(labels)), [l.capitalize() for l in labels])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(title)

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f"{cm[i, j]}\n{normalised[i, j]*100:.1f}%",
                    ha="center", va="center", fontsize=9,
                    color="white" if normalised[i, j] > 0.55 else "#1e293b")

    fig.colorbar(im, ax=ax, fraction=0.046, label="Row-normalised")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def evaluate_multiclass(name: str, y_true: np.ndarray, probs: np.ndarray) -> dict:
    y_pred = probs.argmax(axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=range(len(CLASS_NAMES)), zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=range(len(CLASS_NAMES)))
    plot_confusion(cm, CLASS_NAMES, f"{name} (test set)",
                   FIGURES / f"confusion_{name}.png")

    spoiled = CLASS_NAMES.index("spoiled")
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "spoiled_recall": float(recall[spoiled]),
        "spoiled_precision": float(precision[spoiled]),
        "per_class": {
            CLASS_NAMES[i]: {
                "precision": float(precision[i]), "recall": float(recall[i]),
                "f1": float(f1[i]), "support": int(support[i]),
            } for i in range(len(CLASS_NAMES))
        },
        "confusion_matrix": cm.tolist(),
        "report": classification_report(
            y_true, y_pred, target_names=CLASS_NAMES, zero_division=0, digits=4),
    }


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    out: dict = {}

    # ---- visual CNN, binary fresh/rotten on real labels -----------------
    cnn_path = MODEL_DIR / "visual_cnn.keras"
    if cnn_path.exists():
        head = keras.models.load_model(cnn_path)
        xte = np.load(EMB_DIR / "test_x.npy")
        yte = np.load(EMB_DIR / "test_y.npy")
        # Score through the saved head over cached embeddings; identical to
        # running the full model, and it avoids re-decoding 1,837 JPEGs.
        dense = head.get_layer("p_rotten")
        w, b = dense.get_weights()
        p = 1.0 / (1.0 + np.exp(-(xte @ w + b))).ravel()
        pred = (p >= 0.5).astype(int)
        cm = confusion_matrix(yte, pred, labels=[0, 1])
        plot_confusion(cm, ["fresh", "rotten"],
                       "Visual CNN, fresh vs rotten (test set)",
                       FIGURES / "confusion_visual_cnn.png")
        pr, rc, f1, sup = precision_recall_fscore_support(
            yte, pred, labels=[0, 1], zero_division=0)
        out["visual_cnn_binary"] = {
            "accuracy": float(accuracy_score(yte, pred)),
            "auc": float(roc_auc_score(yte, p)),
            "macro_f1": float(f1_score(yte, pred, average="macro")),
            "rotten_recall": float(rc[1]),
            "rotten_precision": float(pr[1]),
            "confusion_matrix": cm.tolist(),
            "n": int(len(yte)),
            "note": ("Real images, real labels. The fresh/rotten distinction in "
                     "this corpus is visually stark, so a high score here does "
                     "not imply the system can detect early spoilage."),
        }
        print(f"visual CNN (binary): acc={out['visual_cnn_binary']['accuracy']:.4f} "
              f"auc={out['visual_cnn_binary']['auc']:.4f}")

    # ---- three-state models ---------------------------------------------
    emb = np.load(CORPUS / "test_embedding.npy")
    sen = np.load(CORPUS / "test_sensor.npy")
    y = np.load(CORPUS / "test_y.npy")
    mean, std = np.load(MODEL_DIR / "sensor_scaler.npy")
    z = (sen - mean) / std

    specs = [
        ("vision_only", "vision_only.keras", emb),
        ("sensor_only", "sensor_only.keras", z),
        ("fusion_raw", "fusion_raw.keras", [emb, z]),
        ("fusion", "fusion.keras", [emb, z]),
    ]
    print()
    for name, filename, inputs in specs:
        path = MODEL_DIR / filename
        if not path.exists():
            continue
        model = keras.models.load_model(path)
        probs = model.predict(inputs, verbose=0)
        out[name] = evaluate_multiclass(name, y, probs)
        print(f"{name:12s} acc={out[name]['accuracy']:.4f}  "
              f"macroF1={out[name]['macro_f1']:.4f}  "
              f"spoiled recall={out[name]['spoiled_recall']:.4f}")

    # ---- ablation figure -------------------------------------------------
    present = [n for n, *_ in specs if n in out]
    if present:
        fig, ax = plt.subplots(figsize=(7.2, 4.0))
        metrics = ["accuracy", "macro_f1", "spoiled_recall"]
        titles = ["Accuracy", "Macro F1", "Recall (spoiled)"]
        width = 0.26
        xs = np.arange(len(present))
        _bar_grey = ["0.8", "0.55", "0.3"]
        _bar_hatch = ["", "//", ".."]
        for k, (metric, title) in enumerate(zip(metrics, titles)):
            values = [out[n][metric] for n in present]
            bars = ax.bar(xs + (k - 1) * width, values, width, label=title,
                          color=_bar_grey[k], hatch=_bar_hatch[k], edgecolor="black")
            ax.bar_label(bars, fmt="%.3f", fontsize=7, padding=2)
        ax.set_xticks(xs, [n.replace("_", "\n") for n in present])
        ax.set_ylim(0, 1.10)
        ax.set_ylabel("Score")
        ax.set_title("Modality ablation on the held-out test split")
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIGURES / "ablation.png", dpi=200)
        plt.close(fig)

    # ---- training curves -------------------------------------------------
    hist_path = RESULTS / "fusion_training.json"
    if hist_path.exists():
        history = json.loads(hist_path.read_text())
        fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8))
        _line_styles = {"vision_only": "-", "sensor_only": "--",
                        "fusion_raw": ":", "fusion": "-."}
        for name in present:
            h = history.get(name, {}).get("history", {})
            if not h:
                continue
            ls = _line_styles.get(name, "-")
            axes[0].plot(h["val_accuracy"], label=name, color="black", linestyle=ls)
            axes[1].plot(h["val_loss"], label=name, color="black", linestyle=ls)
        axes[0].set_title("Validation accuracy"); axes[0].set_xlabel("Epoch")
        axes[1].set_title("Validation loss"); axes[1].set_xlabel("Epoch")
        for ax in axes:
            ax.grid(alpha=0.25); ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGURES / "training_curves.png", dpi=200)
        plt.close(fig)

    with (RESULTS / "evaluation.json").open("w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nWrote {RESULTS / 'evaluation.json'} and figures to {FIGURES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
