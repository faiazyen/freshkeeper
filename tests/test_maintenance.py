"""Retention purge and the camera privacy switch."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from freshkeeper.db.maintenance import purge_expired
from freshkeeper.db.models import FoodItem, SensorReading, SpoilagePrediction, SpoilageState
from freshkeeper.db.session import session_scope

NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


def seed(factory):
    with session_scope(factory) as s:
        item = FoodItem(slot_id=0, name="x", commodity="apple", initial_mass_g=100.0)
        s.add(item); s.flush()
        for days in (1, 29, 31, 89, 91):
            when = NOW - timedelta(days=days)
            s.add(SensorReading(slot_id=0, recorded_at=when, temperature_c=4, humidity_pct=85,
                                ethanol_ppm=1, ammonia_ppm=1, mass_g=100))
            s.add(SpoilagePrediction(item_id=item.id, predicted_at=when, state=SpoilageState.FRESH,
                                     p_fresh=1, p_marginal=0, p_spoiled=0, freshness_score=100))


def test_purge_respects_both_windows(session_factory):
    seed(session_factory)
    removed = purge_expired(session_factory, now=NOW)
    # Ages 1, 29, 31, 89, 91 days: one reading is past 90; three predictions
    # are past 30.
    assert removed == {"readings": 1, "predictions": 3}
    with session_scope(session_factory) as s:
        assert s.query(SensorReading).count() == 4
        assert s.query(SpoilagePrediction).count() == 2
        assert s.query(FoodItem).count() == 1  # items are never purged


def test_purge_is_idempotent(session_factory):
    seed(session_factory)
    purge_expired(session_factory, now=NOW)
    assert purge_expired(session_factory, now=NOW) == {"readings": 0, "predictions": 0}


class TestCameraSwitch:
    def test_settings_roundtrip(self, client, auth):
        assert client.get("/api/settings", headers=auth).get_json() == {"camera_enabled": True}
        r = client.post("/api/settings", headers=auth, json={"camera_enabled": False})
        assert r.status_code == 200 and r.get_json() == {"camera_enabled": False}
        assert client.get("/api/settings", headers=auth).get_json() == {"camera_enabled": False}

    def test_rejects_non_boolean(self, client, auth):
        assert client.post("/api/settings", headers=auth, json={"camera_enabled": "no"}).status_code == 400
        assert client.post("/api/settings", headers=auth, json={}).status_code == 400

    def test_switch_reaches_the_backend(self, session_factory):
        from freshkeeper.api.app import create_app
        from freshkeeper.hardware.sim_backend import SimulatedSensorBackend
        from freshkeeper.ml.inference import InferenceService
        backend = SimulatedSensorBackend(slot_count=1, seed=1)
        service = InferenceService(backend, session_factory, load_models=False)
        app = create_app(":memory:", auth_token="t", inference_service=service)
        c = app.test_client()
        c.post("/api/settings", headers={"Authorization": "Bearer t"}, json={"camera_enabled": False})
        assert backend.camera_enabled is False
