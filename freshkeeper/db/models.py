"""SQLAlchemy schema for the monitoring database.

Four tables:

``food_items``          one row per item being tracked
``sensor_readings``     one row per slot per measurement cycle
``spoilage_predictions``one row per item per cycle, holding the model output
``consumption_events``  what actually happened to an item, for measuring the
                        system against reality

The fourth table is the one that makes the system evaluable. Without a record
of whether an item was eaten or binned, and when relative to the alert, there
is no way to say whether the predictions were any good. Logging predictions
alone would produce a system that can never be shown to be wrong.

SQLite is the engine. It needs no server process, the whole database is one
file that can be copied off the device, and the write volume here, six slots
every thirty minutes, roughly 300 rows a day, is far below the point where
its single-writer limit matters.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SpoilageState(str, enum.Enum):
    """The three states reported to the user."""

    FRESH = "fresh"
    MARGINAL = "marginal"
    SPOILED = "spoiled"


class ItemStatus(str, enum.Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    DISCARDED = "discarded"


class Outcome(str, enum.Enum):
    """What became of an item, recorded when it leaves the shelf."""

    EATEN = "eaten"
    BINNED = "binned"


class FoodItem(Base):
    """One tracked item occupying one slot."""

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    #: One of the eight commodities the model was trained on, lowercase.
    commodity: Mapped[str] = mapped_column(String(40), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    initial_mass_g: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus), default=ItemStatus.ACTIVE, nullable=False, index=True)
    #: Set when the user overrides the model; None means the model is trusted.
    manual_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    #: Alerts are suppressed until this time when the user snoozes one.
    snoozed_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    predictions: Mapped[list["SpoilagePrediction"]] = relationship(
        back_populates="item", cascade="all, delete-orphan")
    consumption: Mapped["ConsumptionEvent | None"] = relationship(
        back_populates="item", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        CheckConstraint("initial_mass_g > 0", name="ck_initial_mass_positive"),
        CheckConstraint("slot_id >= 0", name="ck_slot_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<FoodItem {self.id} {self.name!r} slot={self.slot_id} {self.status.value}>"


class SensorReading(Base):
    """One measurement cycle for one slot.

    Stored per slot rather than per item so that readings survive the item
    being removed. A slot's history is a property of the shelf, and throwing
    it away when an item is eaten would make it impossible to look back at the
    conditions that preceded a bad outcome.
    """

    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    ethanol_ppm: Mapped[float] = mapped_column(Float, nullable=False)
    ammonia_ppm: Mapped[float] = mapped_column(Float, nullable=False)
    mass_g: Mapped[float] = mapped_column(Float, nullable=False)
    mass_delta_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # Almost every query is "recent readings for this slot", so the index
        # is on the pair with time descending.
        Index("ix_readings_slot_time", "slot_id", "recorded_at"),
        CheckConstraint("humidity_pct >= 0 AND humidity_pct <= 100",
                        name="ck_humidity_range"),
    )


class SpoilagePrediction(Base):
    """One model output for one item at one instant."""

    __tablename__ = "spoilage_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE"), nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False)
    state: Mapped[SpoilageState] = mapped_column(Enum(SpoilageState), nullable=False)
    p_fresh: Mapped[float] = mapped_column(Float, nullable=False)
    p_marginal: Mapped[float] = mapped_column(Float, nullable=False)
    p_spoiled: Mapped[float] = mapped_column(Float, nullable=False)
    #: 0 (certainly spoiled) to 100 (certainly fresh).
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False)
    #: Days remaining, extrapolated from the freshness trajectory. None until
    #: there are enough points to fit a trend.
    days_remaining: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Wall-clock milliseconds for this inference, for the latency figures.
    inference_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    item: Mapped[FoodItem] = relationship(back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_item_time", "item_id", "predicted_at"),
        CheckConstraint("freshness_score >= 0 AND freshness_score <= 100",
                        name="ck_freshness_range"),
    )


class ConsumptionEvent(Base):
    """What actually happened to an item.

    ``alert_lead_time_hours`` is the number the whole evaluation turns on: how
    long before the item was thrown away did the system first warn about it. A
    negative value means the warning came too late to be useful.
    """

    __tablename__ = "consumption_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False)
    outcome: Mapped[Outcome] = mapped_column(Enum(Outcome), nullable=False)
    #: Mass actually thrown away, where the user reports it.
    wasted_mass_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Hours between the first spoilage alert and this event.
    alert_lead_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    item: Mapped[FoodItem] = relationship(back_populates="consumption")
