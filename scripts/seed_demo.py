"""Populate a demo database by running an accelerated storage simulation.

Used to produce the interface screenshots in the thesis and to exercise the
whole stack end to end. It runs the real acquisition and inference path, the
same code the device runs, with simulated time compressed so that a
fortnight of storage happens in a few seconds.

Initial mass is read from the load cell at registration rather than typed in.
That is how the real system works, and getting it wrong in an earlier version
of this script fed the model a mass delta of -232 g and made every item read
as spoiled within a day.

Run:  python scripts/seed_demo.py
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freshkeeper.db.models import FoodItem, SpoilagePrediction  # noqa: E402
from freshkeeper.db.session import (  # noqa: E402
    init_db, make_engine, make_session_factory, session_scope,
)
from freshkeeper.hardware.sim_backend import SimulatedSensorBackend  # noqa: E402
from freshkeeper.ml.inference import InferenceService  # noqa: E402

DB_PATH = ROOT / "data" / "demo.db"
HOURS_PER_CYCLE = 12.0
CYCLES = 23  # a cycle at which an item has just crossed into a new state

SHELF = [
    (0, "Strawberries", "strawberry"),
    (1, "Bananas", "banana"),
    (2, "Red grapes", "grape"),
    (3, "Guavas", "guava"),
    (4, "Oranges", "orange"),
    (5, "Pomegranate", "pomegranate"),
]


def main() -> int:
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        extra = Path(str(DB_PATH) + suffix)
        if extra.exists():
            extra.unlink()

    engine = make_engine(DB_PATH)
    init_db(engine)
    factory = make_session_factory(engine)

    backend = SimulatedSensorBackend(
        slot_count=len(SHELF), time_acceleration=HOURS_PER_CYCLE, seed=4242)
    for slot, _, commodity in SHELF:
        backend.place_item(slot, commodity)

    # Register each item with the mass the load cell actually reports.
    with session_scope(factory) as session:
        for slot, name, commodity in SHELF:
            session.add(FoodItem(
                slot_id=slot, name=name, commodity=commodity,
                initial_mass_g=round(backend.items[slot].initial_mass_g, 1),
            ))

    service = InferenceService(backend, factory)
    print(f"Running {CYCLES} cycles at {HOURS_PER_CYCLE} simulated hours each "
          f"({CYCLES * HOURS_PER_CYCLE / 24:.0f} days)\n")

    log = []
    for cycle in range(1, CYCLES + 1):
        result = service.run_cycle()
        log.append({"cycle": cycle, "day": round(cycle * HOURS_PER_CYCLE / 24, 2),
                    "items": [{"name": r["item"], "state": r["state"],
                               "score": round(float(r["freshness_score"]), 1)}
                              for r in result["items"]]})
        if cycle % 5 == 0 or cycle == 1:
            day = cycle * HOURS_PER_CYCLE / 24
            summary = "  ".join(
                f"{r['item'][:11]:11s} {r['state']:8s} {r['freshness_score']:5.1f}"
                for r in result["items"])
            print(f"day {day:5.1f}   {summary}")

    # Spread the stored timestamps over the simulated span so the interface's
    # time-series charts show a fortnight rather than thirty points inside one
    # real second.
    with session_scope(factory) as session:
        predictions = session.query(SpoilagePrediction).order_by(
            SpoilagePrediction.id).all()
        by_item: dict[int, list] = {}
        for prediction in predictions:
            by_item.setdefault(prediction.item_id, []).append(prediction)
        for rows in by_item.values():
            base = rows[0].predicted_at - timedelta(hours=HOURS_PER_CYCLE * len(rows))
            for index, row in enumerate(rows):
                row.predicted_at = base + timedelta(hours=HOURS_PER_CYCLE * index)
        for item in session.query(FoodItem).all():
            item.added_at = item.added_at - timedelta(
                hours=HOURS_PER_CYCLE * CYCLES)

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "demo_run.json").write_text(json.dumps({
        "hours_per_cycle": HOURS_PER_CYCLE, "cycles": CYCLES,
        "shelf": [{"slot": s, "name": n, "commodity": c} for s, n, c in SHELF],
        "log": log,
    }, indent=2))
    print(f"\nWrote {DB_PATH} and {results_dir / 'demo_run.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
