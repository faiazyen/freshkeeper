"""Bounded retention for the monitoring database.

A device that watches a fridge does not need a permanent record of what a
household ate. Readings older than 90 days and predictions older than 30 are
removed at the end of each measurement cycle. Items and their consumption
outcomes are kept, because they are what the evaluation is measured against.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from .models import SensorReading, SpoilagePrediction
from .session import session_scope

READING_RETENTION_DAYS = 90
PREDICTION_RETENTION_DAYS = 30


def purge_expired(session_factory, now: datetime | None = None,
                  reading_days: int = READING_RETENTION_DAYS,
                  prediction_days: int = PREDICTION_RETENTION_DAYS) -> dict[str, int]:
    """Delete rows past their retention window. Returns counts removed."""
    now = now or datetime.now(timezone.utc)
    with session_scope(session_factory) as session:
        readings = session.execute(
            delete(SensorReading).where(
                SensorReading.recorded_at < now - timedelta(days=reading_days))
        ).rowcount
        predictions = session.execute(
            delete(SpoilagePrediction).where(
                SpoilagePrediction.predicted_at < now - timedelta(days=prediction_days))
        ).rowcount
    return {"readings": readings, "predictions": predictions}
