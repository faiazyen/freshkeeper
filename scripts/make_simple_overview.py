"""A very simple system overview figure, plain and basic on purpose.

Few boxes, big text, simple arrows. Not a designed graphic. The kind of block
diagram a student draws in a slide.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

FIG = Path(__file__).resolve().parents[1] / "docs" / "figures"


def box(ax, x, y, w, h, text, fill="#ffffff", fs=12, bold=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor="black", linewidth=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, weight="bold" if bold else "normal", color="black")


def arrow(ax, x0, y0, x1, y1, colour="black"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=18, color=colour, linewidth=1.6))


def main():
    fig, ax = plt.subplots(figsize=(8.6, 8.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    # 1. Food on the shelf
    box(ax, 3.4, 9.0, 3.2, 0.8, "Food on the shelf", fs=13, bold=True)
    arrow(ax, 5.0, 9.0, 5.0, 8.4)

    # 2. Sensors (one row)
    labels = ["Camera", "Gas\nsensors", "Weight", "Temp and\nhumidity"]
    xs = [0.7, 3.05, 5.4, 7.75]
    for lab, x in zip(labels, xs):
        box(ax, x, 7.4, 2.0, 1.0, lab, fs=11)
        arrow(ax, x + 1.0, 7.4, 5.0, 6.7)

    # 3. Raspberry Pi
    box(ax, 3.0, 5.7, 4.0, 1.0, "Raspberry Pi\nruns the model", fs=12, bold=True)
    arrow(ax, 5.0, 5.7, 5.0, 5.0)

    # 4. Three results
    box(ax, 1.0, 3.9, 2.4, 1.0, "Fresh", fill="#dff0d8", fs=12, bold=True)
    box(ax, 3.8, 3.9, 2.4, 1.0, "Use soon", fill="#fcf3cf", fs=12, bold=True)
    box(ax, 6.6, 3.9, 2.4, 1.0, "Spoiled", fill="#f5d5d0", fs=12, bold=True)
    arrow(ax, 5.0, 5.0, 2.2, 4.9)
    arrow(ax, 5.0, 5.0, 5.0, 4.9)
    arrow(ax, 5.0, 5.0, 7.8, 4.9)

    # 5. Phone app + alert (green for ok path, red for alert path)
    arrow(ax, 2.2, 3.9, 3.8, 3.1, colour="green")
    arrow(ax, 5.0, 3.9, 5.0, 3.1)
    arrow(ax, 7.8, 3.9, 6.2, 3.1, colour="red")
    box(ax, 2.6, 2.1, 4.8, 1.0, "Phone app\nshows the status and warns you", fs=12, bold=True)

    ax.text(5.0, 1.4, "The camera and sensors watch the food. The Raspberry Pi decides if it is\n"
                      "fresh, use soon, or spoiled. The phone app shows this and warns you in time.",
            ha="center", va="top", fontsize=10, color="black")

    fig.savefig(FIG / "architecture_simple.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote architecture_simple.png")


if __name__ == "__main__":
    main()
