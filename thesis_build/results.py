"""Read every number the thesis quotes from the pipeline's result files.

Nothing numeric in the content modules should be a literal. If a value is not
here, it has no source and should not be in the thesis. The first draft typed
its tables in by hand and three of them were wrong within a day.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "freshkeeper"
RES = ROOT / "results"


def _load(name: str, required: bool = True):
    path = RES / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f"{path} missing: run the pipeline stage that writes it")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        if required:
            raise ValueError(f"{path} is not valid JSON: {exc}") from exc
        print(f"  warning: optional {path.name} unreadable ({exc}); treating as absent")
        return None


class Results:
    def __init__(self) -> None:
        self.ev = _load("evaluation.json")
        self.train = _load("fusion_training.json")
        self.cnn = _load("cnn_training_history.json")
        self.cnn_naive = _load("cnn_training_history_naive_split.json", required=False)
        self.pipe = _load("pipeline_benchmark.json")
        self.tflite = _load("tflite_benchmark.json")
        self.audit = _load("dataset_audit.json")
        self.corpus = _load("sensor_corpus_meta.json")
        self.shelf = _load("shelf_life_validation.json")
        self.demo = _load("demo_run.json")
        self.metrics = _load("test_metrics.json")
        self.per_commodity = _load("per_commodity.json")

    # -- formatting helpers ------------------------------------------------
    @staticmethod
    def f4(x: float) -> str: return f"{x:.4f}"
    @staticmethod
    def pct(x: float, d: int = 1) -> str: return f"{100 * x:.{d}f}%"
    @staticmethod
    def n(x: int) -> str: return f"{x:,}"

    # -- derived values used in prose --------------------------------------
    @property
    def visual(self): return self.ev["visual_cnn_binary"]
    def acc(self, model): return self.ev[model]["accuracy"]
    def macro_f1(self, model): return self.ev[model]["macro_f1"]
    def spoiled_recall(self, model): return self.ev[model]["spoiled_recall"]
    def spoiled_precision(self, model): return self.ev[model]["spoiled_precision"]
    def per_class(self, model, cls, key): return self.ev[model]["per_class"][cls][key]
    def cm(self, model): return self.ev[model]["confusion_matrix"]

    @property
    def fusion_gap_points(self) -> float:
        """Sensor-only minus best fusion, in percentage points."""
        return 100 * (self.acc("sensor_only") - self.acc("fusion"))

    @property
    def projection_gain_points(self) -> float:
        return 100 * (self.acc("fusion") - self.acc("fusion_raw"))

    @property
    def stage1_epochs(self): return len(self.cnn["history"]["stage1"]["loss"])
    @property
    def stage2_epochs(self): return len(self.cnn["history"]["stage2"]["loss"])
    @property
    def stage1_final_val(self): return self.cnn["history"]["stage1"]["val_accuracy"][-1]
    @property
    def stage2_best_val(self): return max(self.cnn["history"]["stage2"]["val_accuracy"])
    @property
    def stage2_minutes(self): return self.cnn["stage2_seconds"] / 60
    @property
    def naive_best_val(self):
        if not self.cnn_naive: return None
        return max(self.cnn_naive["history"]["stage2"]["val_accuracy"])

    @property
    def naive_leak(self): return self.audit["naive_split"]["test_leakage_fraction"]
    @property
    def naive_median_nn(self): return self.audit["naive_split"]["nearest_neighbour_percentiles"]["p50"]
    @property
    def anomaly(self): return self.audit["label_anomaly_centroid_cosine"]

    def stage(self, name, key="mean"): return self.pipe["stages_ms"][name][key]
    @property
    def pi_factor(self): return self.pipe["pi4_slowdown_factor"]
    @property
    def pi_ms(self): return self.pipe["projected_pi4_total_ms"]
    @property
    def duty(self): return self.pipe["cycle_budget_utilisation"]

    def tfl(self, model, variant, key): return self.tflite["models"][model]["variants"][variant][key]
    def keras_mb(self, model): return self.tflite["models"][model]["keras_bytes"] / 1e6

    @property
    def tests(self): return self.metrics["tests_passed"]
    @property
    def test_modules(self): return len(self.metrics["test_modules"])
    def cov(self, path): return self.metrics["coverage_files"][path]
    @property
    def cov_total(self): return self.metrics["coverage_total_percent"]
    @property
    def loc(self): return self.metrics["python_lines"]
    @property
    def files(self): return self.metrics["tracked_files"]

    def demo_rows(self, days=(0.5, 2.5, 5.0, 7.5, 10.0)):
        """Selected days plus the final cycle, whatever day that falls on."""
        log = self.demo["log"]
        chosen = [e for e in log if any(abs(e["day"] - d) < 1e-6 for d in days)]
        if log and log[-1] not in chosen:
            chosen.append(log[-1])
        return [[f"{e['day']:.1f}"] + [f"{it['state']} {it['score']:.0f}" for it in e["items"]]
                for e in chosen]
    @property
    def demo_names(self): return [s["name"] for s in self.demo["shelf"]]
    @property
    def demo_days(self): return self.demo["hours_per_cycle"] * self.demo["cycles"] / 24


R = Results  # constructed lazily by build.py once all files exist
