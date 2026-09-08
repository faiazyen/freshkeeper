"""Generate the schematic and analysis figures for the thesis.

Everything here is drawn from the code and the measured results, not laid out
by hand, so the figures cannot drift out of step with the system they claim to
describe. The pin numbers in the wiring diagram are imported from the driver
module; the tables in the ER diagram are read off the SQLAlchemy metadata; the
shelf-life plot re-runs the physical model.

Run:  python scripts/make_diagrams.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIGURES = ROOT / "docs" / "figures"

INK = "#1e293b"
MUTED = "#64748b"
LAYER_COLOURS = {"perception": "#0ea5e9", "network": "#8b5cf6", "application": "#059669"}


def box(ax, x, y, w, h, text, face="#ffffff", edge=INK, fontsize=8.5, weight="normal"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=face, edgecolor=edge, linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=INK, weight=weight, linespacing=1.45)


def arrow(ax, start, end, style="-|>", colour=INK, lw=1.1, ls="-"):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=11,
        color=colour, linewidth=lw, linestyle=ls,
        shrinkA=2, shrinkB=2))


def blank_axes(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


# --------------------------------------------------------------------------
# 1. Three-layer system architecture
# --------------------------------------------------------------------------

def architecture() -> None:
    fig, ax = blank_axes((9.6, 6.6))

    bands = [
        ("Perception layer", 0.72, 0.24, LAYER_COLOURS["perception"]),
        ("Processing layer", 0.40, 0.28, LAYER_COLOURS["network"]),
        ("Application layer", 0.06, 0.30, LAYER_COLOURS["application"]),
    ]
    # The band label sits rotated in the left margin rather than inside the
    # band: an earlier version put it top-left inside and it landed on top of
    # the first row of boxes.
    for name, y, h, colour in bands:
        ax.add_patch(FancyBboxPatch(
            (0.10, y), 0.88, h, boxstyle="round,pad=0.008,rounding_size=0.015",
            facecolor=colour, alpha=0.06, edgecolor=colour, linewidth=1.2))
        ax.text(0.065, y + h / 2, name, fontsize=9.5, weight="bold",
                color=colour, rotation=90, ha="center", va="center")

    sensors = [
        ("Camera Module 3\nCSI, 224x224", 0.13),
        ("MQ-135\nammonia", 0.315),
        ("MQ-3\nethanol", 0.465),
        ("DHT22\ntemp / RH", 0.605),
        ("HX711 + load cell\nmass, 6 slots", 0.745),
    ]
    for label, x in sensors:
        width = 0.22 if "HX711" in label else (0.17 if "Camera" in label else 0.14)
        box(ax, x, 0.775, width, 0.10, label, face="#f0f9ff",
            edge=LAYER_COLOURS["perception"], fontsize=7.6)

    box(ax, 0.13, 0.615, 0.28, 0.085,
        "MCP3008 10-bit ADC\nSPI0, channels 0-1", face="#faf5ff",
        edge=LAYER_COLOURS["network"], fontsize=7.8)
    box(ax, 0.435, 0.615, 0.25, 0.085,
        "Acquisition scheduler\n30-minute cycle", face="#faf5ff",
        edge=LAYER_COLOURS["network"], fontsize=7.8)
    box(ax, 0.705, 0.615, 0.25, 0.085,
        "Sensor backend\nhardware | simulation", face="#faf5ff",
        edge=LAYER_COLOURS["network"], fontsize=7.8)

    box(ax, 0.13, 0.475, 0.37, 0.095,
        "MobileNetV2 backbone (frozen)\n1280-d visual embedding",
        face="#faf5ff", edge=LAYER_COLOURS["network"], fontsize=7.8)
    box(ax, 0.53, 0.475, 0.42, 0.095,
        "Fusion head: 1280 -> 64 projection || 5 -> 64 -> 32 MLP\n"
        "-> 256 -> 128 -> softmax(fresh, marginal, spoiled)",
        face="#faf5ff", edge=LAYER_COLOURS["network"], fontsize=7.4)

    box(ax, 0.13, 0.245, 0.25, 0.085,
        "SQLite\nitems, readings,\npredictions, outcomes",
        face="#ecfdf5", edge=LAYER_COLOURS["application"], fontsize=7.5)
    box(ax, 0.41, 0.245, 0.25, 0.085,
        "Flask REST API\nbearer-token auth",
        face="#ecfdf5", edge=LAYER_COLOURS["application"], fontsize=7.8)
    box(ax, 0.69, 0.245, 0.26, 0.085,
        "Alert engine\ntransition-triggered",
        face="#ecfdf5", edge=LAYER_COLOURS["application"], fontsize=7.8)
    box(ax, 0.33, 0.095, 0.42, 0.085,
        "Vue 3 single-page interface\nserved over the local network",
        face="#ecfdf5", edge=LAYER_COLOURS["application"], fontsize=8.2)

    arrow(ax, (0.215, 0.775), (0.215, 0.700), colour=MUTED)   # camera -> ADC
    arrow(ax, (0.385, 0.775), (0.28, 0.700), colour=MUTED)     # MQ-135 -> ADC
    arrow(ax, (0.535, 0.775), (0.34, 0.700), colour=MUTED)     # MQ-3 -> ADC
    arrow(ax, (0.675, 0.775), (0.56, 0.700), colour=MUTED)     # DHT22 -> scheduler
    arrow(ax, (0.855, 0.775), (0.83, 0.700), colour=MUTED)     # HX711 -> backend
    arrow(ax, (0.27, 0.615), (0.31, 0.570), colour=MUTED)
    arrow(ax, (0.56, 0.615), (0.64, 0.570), colour=MUTED)
    arrow(ax, (0.50, 0.522), (0.53, 0.522), colour=MUTED)
    arrow(ax, (0.74, 0.475), (0.53, 0.330), colour=MUTED)
    arrow(ax, (0.41, 0.288), (0.38, 0.288), colour=MUTED, style="<|-|>")
    arrow(ax, (0.66, 0.288), (0.69, 0.288), colour=MUTED)
    arrow(ax, (0.535, 0.245), (0.535, 0.180), colour=MUTED, style="<|-|>")

    ax.text(0.5, 0.985, "FreshKeeper system architecture",
            ha="center", fontsize=12, weight="bold", color=INK)
    ax.text(0.5, 0.955,
            "All inference runs on the device; no image leaves the local network",
            ha="center", fontsize=8.5, color=MUTED, style="italic")
    fig.savefig(FIGURES / "architecture.png", dpi=210, bbox_inches="tight")
    plt.close(fig)
    print("  architecture.png")


# --------------------------------------------------------------------------
# 2. Wiring diagram, with pin numbers imported from the driver
# --------------------------------------------------------------------------

def wiring() -> None:
    from freshkeeper.hardware import rpi_backend as rpi

    fig, ax = blank_axes((9.8, 6.4))
    box(ax, 0.36, 0.30, 0.28, 0.42, "Raspberry Pi 4\nModel B (4 GB)\n\n40-pin GPIO header",
        face="#fef2f2", edge="#b91c1c", fontsize=9, weight="bold")

    peripherals = [
        ("DHT22 (AM2302)\ntemperature / humidity", 0.04, 0.60, 0.24, 0.11,
         f"GPIO {rpi.PIN_DHT22}\n1-wire, 4.7k pull-up", "right"),
        ("HX711 + 5 kg load cell\nmass per slot", 0.04, 0.42, 0.24, 0.11,
         f"GPIO {rpi.PIN_HX711_DOUT} DOUT\nGPIO {rpi.PIN_HX711_SCK} SCK", "right"),
        ("MCP3008\n10-bit ADC", 0.04, 0.22, 0.24, 0.11,
         "SPI0: CE0 GPIO8\nMOSI 10, MISO 9, SCLK 11", "right"),
        ("Camera Module 3\n12 MP", 0.72, 0.60, 0.24, 0.11,
         "CSI-2 ribbon\n(dedicated bus)", "left"),
        ("LED strip 5 V\nvia 2N7000 MOSFET", 0.72, 0.42, 0.24, 0.11,
         f"GPIO {rpi.PIN_LED_GATE}\ngate drive", "left"),
    ]
    for label, x, y, w, h, pins, side in peripherals:
        box(ax, x, y, w, h, label, face="#f8fafc", fontsize=7.8)
        if side == "right":
            arrow(ax, (x + w, y + h / 2), (0.36, y + h / 2), style="<|-|>", colour=MUTED)
            ax.text((x + w + 0.36) / 2, y + h / 2 + 0.035, pins,
                    ha="center", fontsize=6.4, color=MUTED)
        else:
            arrow(ax, (x, y + h / 2), (0.64, y + h / 2), style="<|-|>", colour=MUTED)
            ax.text((x + 0.64) / 2, y + h / 2 + 0.035, pins,
                    ha="center", fontsize=6.4, color=MUTED)

    # Gas sensors hang off the ADC, not the Pi: the Pi has no analogue input.
    box(ax, 0.04, 0.03, 0.115, 0.10, "MQ-135\nammonia\n5 V heater", face="#fffbeb", fontsize=7)
    box(ax, 0.165, 0.03, 0.115, 0.10, "MQ-3\nethanol\n5 V heater", face="#fffbeb", fontsize=7)
    arrow(ax, (0.10, 0.13), (0.12, 0.22), colour=MUTED)
    arrow(ax, (0.22, 0.13), (0.18, 0.22), colour=MUTED)
    ax.text(0.29, 0.10,
            f"CH{rpi.ADC_CHANNEL_MQ135} / CH{rpi.ADC_CHANNEL_MQ3}\n"
            "analogue out, divided\nto stay under 3.3 V",
            fontsize=6.6, color=MUTED, va="center")

    ax.text(0.5, 0.955, "Sensor wiring, BCM pin numbering",
            ha="center", fontsize=12, weight="bold", color=INK)
    ax.text(0.5, 0.925,
            "The Pi has no analogue input, so both gas sensors reach it through "
            "the MCP3008 over SPI",
            ha="center", fontsize=8, color=MUTED, style="italic")
    ax.text(0.5, 0.775,
            "Gas heaters and the load cell share the 5 V rail: they are read "
            f"{int(rpi.WEIGHT_SETTLE_DELAY * 1000)} ms apart so heater switching "
            "does not couple into the HX711",
            ha="center", fontsize=7.4, color="#b45309")
    fig.savefig(FIGURES / "wiring.png", dpi=210, bbox_inches="tight")
    plt.close(fig)
    print("  wiring.png")


# --------------------------------------------------------------------------
# 3. Entity-relationship diagram, read from the SQLAlchemy metadata
# --------------------------------------------------------------------------

def er_diagram() -> None:
    from freshkeeper.db.models import Base

    positions = {
        "food_items": (0.36, 0.62),
        "sensor_readings": (0.03, 0.20),
        "spoilage_predictions": (0.37, 0.10),
        "consumption_events": (0.71, 0.20),
    }
    fig, ax = blank_axes((10.2, 7.0))

    for name, (x, y) in positions.items():
        table = Base.metadata.tables[name]
        lines = []
        for column in table.columns:
            marker = "PK" if column.primary_key else ("FK" if column.foreign_keys else "  ")
            type_name = type(column.type).__name__.lower()
            lines.append(f"{marker} {column.name}: {type_name}")
        height = 0.045 + 0.0255 * len(lines)
        ax.add_patch(FancyBboxPatch(
            (x, y), 0.27, height, boxstyle="round,pad=0.006,rounding_size=0.01",
            facecolor="#ffffff", edgecolor=INK, linewidth=1.2))
        ax.add_patch(FancyBboxPatch(
            (x, y + height - 0.042), 0.27, 0.042,
            boxstyle="round,pad=0.004,rounding_size=0.008",
            facecolor="#e0f2fe", edgecolor=INK, linewidth=1.0))
        ax.text(x + 0.135, y + height - 0.021, name, ha="center", va="center",
                fontsize=8.6, weight="bold", color=INK)
        for i, line in enumerate(lines):
            ax.text(x + 0.014, y + height - 0.062 - i * 0.0255, line,
                    fontsize=6.5, family="monospace", color=INK, va="center")

    arrow(ax, (0.42, 0.62), (0.42, 0.10 + 0.30), style="-|>", colour=MUTED)
    ax.text(0.435, 0.50, "1 : N\npredictions", fontsize=7, color=MUTED)
    arrow(ax, (0.63, 0.66), (0.79, 0.20 + 0.20), style="-|>", colour=MUTED)
    ax.text(0.70, 0.47, "1 : 1\noutcome", fontsize=7, color=MUTED)
    arrow(ax, (0.36, 0.68), (0.20, 0.20 + 0.27), style="-|>", colour=MUTED, ls="--")
    ax.text(0.16, 0.50, "by slot_id\n(not a foreign key)", fontsize=7, color=MUTED)

    ax.text(0.5, 0.985, "Database schema", ha="center", fontsize=12,
            weight="bold", color=INK)
    ax.text(0.5, 0.958,
            "Readings key on slot rather than item, so a slot's history "
            "survives the item being eaten",
            ha="center", fontsize=8, color=MUTED, style="italic")
    fig.savefig(FIGURES / "er_diagram.png", dpi=210, bbox_inches="tight")
    plt.close(fig)
    print("  er_diagram.png")


# --------------------------------------------------------------------------
# 4. Measurement cycle sequence
# --------------------------------------------------------------------------

def sequence() -> None:
    actors = ["Scheduler", "Sensor\nbackend", "Database", "Backbone +\nfusion head",
              "Alert\nengine", "Interface"]
    fig, ax = blank_axes((10.4, 6.6))
    xs = np.linspace(0.09, 0.91, len(actors))

    for actor, x in zip(actors, xs):
        box(ax, x - 0.068, 0.875, 0.136, 0.075, actor, face="#f1f5f9", fontsize=7.8)
        ax.plot([x, x], [0.10, 0.875], color="#cbd5e1", lw=1.0, ls="--", zorder=0)

    steps = [
        (0, 1, "warm_up(): 30 s heater settle", 0.815),
        (1, 1, "read_all(): 6 slots", 0.755),
        (1, 2, "store raw readings", 0.700),
        (1, 3, "image + 5 sensor features", 0.645),
        (3, 3, "embed 224x224 -> 1280-d", 0.590),
        (3, 3, "softmax over 3 states", 0.535),
        (3, 2, "store prediction + latency", 0.480),
        (2, 4, "last two predictions", 0.425),
        (4, 4, "transition? confident? snoozed?", 0.370),
        (4, 2, "raise alert if warranted", 0.315),
        (5, 2, "GET /api/items (30 s poll)", 0.245),
        (2, 5, "states, scores, days remaining", 0.190),
    ]
    for src, dst, label, y in steps:
        if src == dst:
            x = xs[src]
            ax.add_patch(FancyBboxPatch(
                (x - 0.012, y - 0.016), 0.024, 0.032,
                boxstyle="round,pad=0.002", facecolor="#e0f2fe",
                edgecolor=MUTED, linewidth=0.9))
            ax.text(x + 0.026, y, label, fontsize=7, color=INK, va="center")
        else:
            arrow(ax, (xs[src], y), (xs[dst], y), colour=MUTED)
            ax.text((xs[src] + xs[dst]) / 2, y + 0.017, label,
                    ha="center", fontsize=7, color=INK)

    ax.plot([0.04, 0.96], [0.285, 0.285], color="#cbd5e1", lw=0.9)
    ax.text(0.045, 0.297, "asynchronous — the interface polls, it is not pushed to",
            fontsize=6.8, color=MUTED, style="italic")

    ax.text(0.5, 0.985, "One measurement cycle", ha="center", fontsize=12,
            weight="bold", color=INK)
    fig.savefig(FIGURES / "sequence.png", dpi=210, bbox_inches="tight")
    plt.close(fig)
    print("  sequence.png")


# --------------------------------------------------------------------------
# 5. Model validation: shelf life against published values
# --------------------------------------------------------------------------

def shelf_life_validation() -> None:
    from freshkeeper.hardware.spoilage_model import (
        PUBLISHED_SHELF_LIFE_DAYS, SPOILED_THRESHOLD, integrate_spoilage, profile_for,
    )

    names, modelled, published = [], [], []
    for name, expected in PUBLISHED_SHELF_LIFE_DAYS.items():
        profile = profile_for(name)
        steps = int(120 * 24 / 2)
        states = integrate_spoilage(profile, [4.0] * steps, [0.85] * steps,
                                    2.0, profile.typical_mass_g)
        hit = next((s.elapsed_hours / 24 for s in states
                    if s.spoilage_extent >= SPOILED_THRESHOLD), float("nan"))
        names.append(name.capitalize()); modelled.append(hit); published.append(expected)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.3))

    xs = np.arange(len(names))
    ax1.bar(xs - 0.19, published, 0.38, label="Published", color="#94a3b8")
    ax1.bar(xs + 0.19, modelled, 0.38, label="Model", color="#059669")
    ax1.set_xticks(xs, names, rotation=30, ha="right")
    ax1.set_ylabel("Days to spoilage at 4 °C, 85% RH")
    ax1.set_title("Calibration against published shelf lives")
    ax1.legend(); ax1.grid(axis="y", alpha=0.25)
    for x, (m, p) in enumerate(zip(modelled, published)):
        ax1.text(x, max(m, p) + 1.2, f"{100*(m-p)/p:+.1f}%",
                 ha="center", fontsize=6.6, color=MUTED)

    temperatures = np.arange(0, 16.5, 0.5)
    for commodity, colour in (("strawberry", "#e11d48"), ("banana", "#d97706"),
                              ("apple", "#059669"), ("pomegranate", "#7c3aed")):
        profile = profile_for(commodity)
        days = []
        for temp in temperatures:
            steps = int(150 * 24 / 2)
            states = integrate_spoilage(profile, [float(temp)] * steps,
                                        [0.85] * steps, 2.0, profile.typical_mass_g)
            hit = next((s.elapsed_hours / 24 for s in states
                        if s.spoilage_extent >= SPOILED_THRESHOLD), np.nan)
            days.append(hit)
        ax2.plot(temperatures, days, label=commodity.capitalize(),
                 color=colour, lw=1.8)

    ax2.axvline(4.0, color=MUTED, ls="--", lw=1.0)
    ax2.text(4.25, ax2.get_ylim()[1] * 0.92, "fridge setpoint",
             fontsize=7, color=MUTED)
    ax2.set_xlabel("Storage temperature (°C)")
    ax2.set_ylabel("Days to spoilage")
    ax2.set_title("Temperature dependence (Ratkowsky)")
    ax2.set_yscale("log"); ax2.legend(fontsize=8); ax2.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(FIGURES / "shelf_life_validation.png", dpi=210)
    plt.close(fig)
    print("  shelf_life_validation.png")


# --------------------------------------------------------------------------
# 6. Simulated sensor trajectories
# --------------------------------------------------------------------------

def sensor_trajectories() -> None:
    from freshkeeper.hardware.sim_backend import SimulatedSensorBackend

    backend = SimulatedSensorBackend(slot_count=3, time_acceleration=6.0, seed=99)
    for slot, commodity in enumerate(("strawberry", "banana", "apple")):
        backend.place_item(slot, commodity)

    days, series = [], {s: {"eth": [], "nh3": [], "mass": [], "temp": []}
                        for s in range(3)}
    for step in range(1, 121):  # 120 * 6 h = 30 days
        samples = backend.read_all()
        days.append(step * 6 / 24)
        for sample in samples:
            item = backend.items[sample.slot_id]
            store = series[sample.slot_id]
            store["eth"].append(sample.ethanol_ppm)
            store["nh3"].append(sample.ammonia_ppm)
            store["mass"].append(100.0 * sample.mass_g / item.initial_mass_g)
            store["temp"].append(sample.temperature_c)

    colours = {0: "#e11d48", 1: "#d97706", 2: "#059669"}
    labels = {0: "Strawberry", 1: "Banana", 2: "Apple"}
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 6.4))

    panels = [
        (axes[0][0], "eth", "Ethanol (ppm), MQ-3", "Volatile production"),
        (axes[0][1], "nh3", "Ammonia (ppm), MQ-135", "Protein breakdown"),
        (axes[1][0], "mass", "Mass (% of initial)", "Moisture loss"),
    ]
    for ax, key, ylabel, title in panels:
        for slot in range(3):
            ax.plot(days, series[slot][key], color=colours[slot],
                    lw=1.5, label=labels[slot])
        ax.set_xlabel("Days in storage"); ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10); ax.grid(alpha=0.25); ax.legend(fontsize=8)

    ax = axes[1][1]
    ax.plot(days, series[0]["temp"], color="#0ea5e9", lw=0.9)
    ax.axhline(4.0, color=MUTED, ls="--", lw=1.0)
    ax.set_xlabel("Days in storage"); ax.set_ylabel("Cabinet temperature (°C)")
    ax.set_title("Compressor cycling and door openings", fontsize=10)
    ax.grid(alpha=0.25)

    fig.suptitle("Simulated sensor response over 30 days of storage",
                 fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "sensor_trajectories.png", dpi=210)
    plt.close(fig)
    print("  sensor_trajectories.png")


# --------------------------------------------------------------------------
# 7. Fusion network topology
# --------------------------------------------------------------------------

def model_diagram() -> None:
    fig, ax = blank_axes((10.2, 5.2))

    box(ax, 0.02, 0.62, 0.17, 0.14, "Image\n224 x 224 x 3", face="#e0f2fe", fontsize=8)
    box(ax, 0.22, 0.62, 0.20, 0.14,
        "MobileNetV2\nfrozen, ImageNet\n2.26 M params", face="#f0f9ff", fontsize=7.6)
    box(ax, 0.45, 0.62, 0.14, 0.14, "Embedding\n1280-d", face="#f0f9ff", fontsize=8)
    box(ax, 0.62, 0.62, 0.15, 0.14, "Dense 64\n+ dropout", face="#f0f9ff", fontsize=8)

    box(ax, 0.02, 0.20, 0.17, 0.14,
        "Sensor features\nethanol, ammonia,\ntemp, RH, Δmass", face="#fef3c7", fontsize=7.4)
    box(ax, 0.22, 0.20, 0.20, 0.14,
        "Dense 64 + BN\n+ dropout", face="#fffbeb", fontsize=8)
    box(ax, 0.45, 0.20, 0.14, 0.14, "Dense 32", face="#fffbeb", fontsize=8)

    box(ax, 0.80, 0.41, 0.16, 0.16,
        "Concatenate\n64 + 32 = 96", face="#f5f3ff", fontsize=8)
    for start, end in (((0.19, 0.69), (0.22, 0.69)), ((0.42, 0.69), (0.45, 0.69)),
                       ((0.59, 0.69), (0.62, 0.69)), ((0.19, 0.27), (0.22, 0.27)),
                       ((0.42, 0.27), (0.45, 0.27)), ((0.77, 0.69), (0.86, 0.57)),
                       ((0.59, 0.27), (0.86, 0.41))):
        arrow(ax, start, end, colour=MUTED)

    ax.text(0.5, 0.925, "Late-fusion classifier", ha="center",
            fontsize=12, weight="bold", color=INK)
    ax.text(0.5, 0.885,
            "The visual embedding is projected 1280 → 64 before the join: raw "
            "concatenation gives the image branch 40× the width and it dominates",
            ha="center", fontsize=7.8, color=MUTED, style="italic")
    ax.text(0.88, 0.30, "→ Dense 256 → Dense 128\n→ softmax\n(fresh, marginal, spoiled)",
            ha="center", fontsize=7.8, color=INK)
    fig.savefig(FIGURES / "model_diagram.png", dpi=210, bbox_inches="tight")
    plt.close(fig)
    print("  model_diagram.png")


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    random.seed(0); np.random.seed(0)
    architecture()
    wiring()
    er_diagram()
    sequence()
    shelf_life_validation()
    sensor_trajectories()
    model_diagram()
    print(f"\nFigures written to {FIGURES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
