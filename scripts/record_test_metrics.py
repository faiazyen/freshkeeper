"""Run the suite with coverage and write the numbers the thesis quotes.

The thesis states the test count, the number of test modules and per-module
coverage. Those were typed in by hand once and went stale within a day. Now
they come from here.

Run:  python scripts/record_test_metrics.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> int:
    cov_json = RESULTS / "coverage.json"
    RESULTS.mkdir(exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--cov=freshkeeper",
         f"--cov-report=json:{cov_json}", "--cov-report=term"],
        cwd=ROOT, capture_output=True, text=True)
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    m = re.search(r"(\d+) passed", tail)
    if proc.returncode != 0 or not m:
        print(proc.stdout[-2000:]); print(proc.stderr[-2000:])
        return 1
    passed = int(m.group(1))
    modules = sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))

    cov = json.loads(cov_json.read_text())
    files = {}
    for name, data in cov["files"].items():
        rel = Path(name).as_posix()
        rel = rel[rel.index("freshkeeper/"):] if "freshkeeper/" in rel else rel
        files[rel] = {
            "statements": data["summary"]["num_statements"],
            "covered": data["summary"]["covered_lines"],
            "percent": round(data["summary"]["percent_covered"], 1),
        }
    total = round(cov["totals"]["percent_covered"], 1)

    # Lines and files of the prototype itself, excluding the thesis generator.
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True).stdout.split()
    tracked = [t for t in tracked if not t.startswith("thesis_build/")]
    py_lines = sum(len((ROOT / t).read_text().splitlines())
                   for t in tracked if t.endswith(".py"))

    report = {
        "tests_passed": passed,
        "test_modules": modules,
        "coverage_total_percent": total,
        "coverage_files": files,
        "tracked_files": len(tracked),
        "python_lines": py_lines,
    }
    (RESULTS / "test_metrics.json").write_text(json.dumps(report, indent=2))
    print(f"{passed} passed across {len(modules)} modules; coverage {total}%; "
          f"{py_lines:,} lines in {len(tracked)} tracked files")
    print(f"Wrote {RESULTS / 'test_metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
