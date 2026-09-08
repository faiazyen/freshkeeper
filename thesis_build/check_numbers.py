"""Cross-check every result-derived number in the built thesis against the
result files, and list any number in the text that has no source.

    python check_numbers.py "../Main thesis.docx"
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import docx
from results import Results

def main() -> int:
    R = Results()
    z = docx.Document(sys.argv[1] if len(sys.argv) > 1 else "../Main thesis.docx")
    text = " ".join(p.text for p in z.paragraphs)
    for t in z.tables:
        for row in t.rows:
            text += " " + " ".join(c.text for c in row.cells)
    expect = {
        "visual accuracy": R.f4(R.visual["accuracy"]), "visual auc": R.f4(R.visual["auc"]),
        "visual rotten recall": R.f4(R.visual["rotten_recall"]),
        "visual rotten precision": R.f4(R.visual["rotten_precision"]),
        "visual macro f1": R.f4(R.visual["macro_f1"]),
        **{f"{m} {k}": R.f4(R.ev[m][k]) for m in ("vision_only","sensor_only","fusion_raw","fusion")
           for k in ("accuracy","macro_f1","spoiled_recall","spoiled_precision")},
        **{f"{m} {c} {k}": R.f4(R.ev[m]["per_class"][c][k]) for m in ("sensor_only","fusion")
           for c in ("fresh","marginal","spoiled") for k in ("precision","recall","f1")},
        "backbone ms": f"{R.stage('backbone'):.2f}", "total ms": f"{R.stage('total'):.2f}",
        "pi ms": f"{R.pi_ms:.0f} ms", "pi factor": f"{R.pi_factor:.1f}×",
        "tflite int8 MB": f"{R.tfl('fusion','int8','megabytes'):.3f}",
        "tflite int8 acc": R.f4(R.tfl('fusion','int8','test_accuracy')),
        "groups": R.n(R.audit["n_groups"]), "largest group": str(R.audit["largest_group"]),
        "naive leak": R.pct(R.naive_leak), "naive median nn": f"{R.naive_median_nn:.3f}",
        "stage1 epochs": f"{R.stage1_epochs} epochs", "stage2 best": R.pct(R.stage2_best_val),
        "tests": f"{R.tests} ", "loc": R.n(R.loc), "files": f"{R.files} tracked",
        "shelf max err": f"{max(abs(r['error_percent']) for r in R.shelf['rows']):.1f}%",
    }
    if R.naive_best_val: expect["naive best val"] = R.pct(R.naive_best_val)
    for r in R.per_commodity:
        expect[f"{r['commodity']} acc"] = R.f4(r["accuracy"])
        expect[f"{r['commodity']} auc"] = R.f4(r["auc"])
    for v in ("float32", "float16", "int8"):
        expect[f"tflite {v} acc"] = R.f4(R.tfl("fusion", v, "test_accuracy"))
    expect["tflite sensor int8 acc"] = R.f4(R.tfl("sensor_only", "int8", "test_accuracy"))
    missing = [(k, v) for k, v in expect.items() if v not in text]
    print(f"result-derived values found in text: {len(expect)-len(missing)}/{len(expect)}")
    for k, v in missing: print(f"  MISSING {k}: {v}")
    # numbers that look like results but are not any expected value
    stale = []
    known = set(expect.values())
    for m in set(re.findall(r"\b0\.9\d{3}\b", text)):
        if m not in known: stale.append(m)
    print("4-decimal values in text with no matching result:", sorted(stale) or "none")
    return 1 if missing or stale else 0

if __name__ == "__main__":
    sys.exit(main())
