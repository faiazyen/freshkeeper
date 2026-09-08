"""Tests for the inference service and the measurement cycle.

A stub model stands in for the trained network so these run in milliseconds and
do not depend on training artefacts existing. What is being tested is the
plumbing: that readings are stored, that mass delta is measured against the
right baseline, that a missing camera falls back rather than crashing, and that
an absent model produces silence instead of a confident guess.
"""

from __future__ import annotations

import numpy as np
import pytest

from freshkeeper.db.models import (
    FoodItem, ItemStatus, SensorReading, SpoilagePrediction,
)
from freshkeeper.db.session import session_scope
from freshkeeper.hardware.sim_backend import SimulatedSensorBackend
from freshkeeper.ml.inference import InferenceService


class StubModel:
    """Returns a fixed distribution, so assertions are about plumbing."""

    def __init__(self, probs):
        self.probs = np.asarray(probs, dtype=np.float32)
        self.calls = 0

    def __call__(self, inputs, training=False):
        self.calls += 1
        batch = np.tile(self.probs, (1, 1))
        return type("Tensor", (), {"numpy": lambda _self: batch})()


@pytest.fixture
def service(session_factory):
    backend = SimulatedSensorBackend(slot_count=3, time_acceleration=24.0, seed=31)
    for slot, commodity in enumerate(("strawberry", "apple", "banana")):
        backend.place_item(slot, commodity)
    svc = InferenceService(backend, session_factory, load_models=False)
    svc.sensor_only = StubModel([0.7, 0.2, 0.1])
    # Scaler present but neutral, so feature values pass through unchanged.
    svc.scaler = np.stack([np.zeros(5), np.ones(5)])
    return svc


def register_items(session_factory, backend):
    with session_scope(session_factory) as session:
        for slot in range(3):
            session.add(FoodItem(
                slot_id=slot, name=f"Item {slot}",
                commodity=backend.items[slot].fruit_type,
                initial_mass_g=round(backend.items[slot].initial_mass_g, 1)))


class TestPredict:
    def test_uses_sensor_only_when_there_is_no_image(self, service):
        probs, elapsed_ms, used = service.predict([10.0, 2.0, 4.0, 85.0, -1.0], None)
        assert used == "sensor_only"
        assert probs.shape == (3,)
        assert elapsed_ms >= 0.0

    def test_falls_back_to_uniform_without_any_model(self, session_factory):
        backend = SimulatedSensorBackend(slot_count=1, seed=3)
        svc = InferenceService(backend, session_factory, load_models=False)
        probs, _, used = svc.predict([0, 0, 4, 85, 0], None)
        assert used == "uniform_fallback"
        # A flat distribution cannot clear the alert confidence floor, so the
        # system stays quiet when it knows nothing. That is the point.
        assert probs.max() == pytest.approx(1 / 3)

    def test_missing_image_path_does_not_raise(self, service):
        assert service._embed("/no/such/file.jpg") is None
        assert service._embed(None) is None

    def test_standardiser_applies_the_scaler(self, service):
        service.scaler = np.stack([np.full(5, 2.0), np.full(5, 4.0)])
        out = service._standardise([2.0, 6.0, 10.0, 2.0, -2.0])
        assert out.tolist() == [[0.0, 1.0, 2.0, 0.0, -1.0]]


class TestRunCycle:
    def test_stores_a_reading_for_every_slot(self, service, session_factory):
        result = service.run_cycle()
        assert result["cycle_completed"] and result["slots"] == 3
        with session_scope(session_factory) as session:
            assert session.query(SensorReading).count() == 3

    def test_predicts_only_for_registered_items(self, service, session_factory):
        assert service.run_cycle()["items"] == []
        register_items(session_factory, service.backend)
        assert len(service.run_cycle()["items"]) == 3

    def test_mass_delta_is_measured_against_the_registered_mass(
            self, service, session_factory):
        register_items(session_factory, service.backend)
        service.run_cycle()
        with session_scope(session_factory) as session:
            readings = session.query(SensorReading).filter(
                SensorReading.slot_id == 0).all()
            latest = readings[-1]
            item = session.query(FoodItem).filter(FoodItem.slot_id == 0).one()
            assert latest.mass_delta_g == pytest.approx(
                latest.mass_g - item.initial_mass_g, abs=0.11)
            # Registering a 250 g punnet against an 18 g simulated berry once
            # produced a -232 g delta and made everything read as spoiled.
            assert abs(latest.mass_delta_g) < 0.25 * item.initial_mass_g

    def test_predictions_accumulate_over_cycles(self, service, session_factory):
        register_items(session_factory, service.backend)
        for _ in range(4):
            service.run_cycle()
        with session_scope(session_factory) as session:
            assert session.query(SpoilagePrediction).count() == 12

    def test_prediction_fields_are_populated(self, service, session_factory):
        register_items(session_factory, service.backend)
        service.run_cycle()
        with session_scope(session_factory) as session:
            prediction = session.query(SpoilagePrediction).first()
            assert 0.0 <= prediction.freshness_score <= 100.0
            assert prediction.inference_ms is not None
            assert prediction.p_fresh + prediction.p_marginal + prediction.p_spoiled \
                == pytest.approx(1.0, abs=1e-5)

    def test_a_consumed_item_stops_being_predicted(self, service, session_factory):
        register_items(session_factory, service.backend)
        with session_scope(session_factory) as session:
            item = session.query(FoodItem).filter(FoodItem.slot_id == 0).one()
            item.status = ItemStatus.CONSUMED
        assert len(service.run_cycle()["items"]) == 2

    def test_readings_are_kept_for_an_empty_slot(self, service, session_factory):
        # Slot history is a property of the shelf, not of whatever sat on it.
        service.run_cycle()
        with session_scope(session_factory) as session:
            assert session.query(SensorReading).filter(
                SensorReading.slot_id == 0).count() == 1
