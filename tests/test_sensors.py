"""Tests for the sensor abstraction and the simulated backend."""

from __future__ import annotations

import pytest

from freshkeeper.hardware.base import SENSOR_FEATURE_NAMES, SensorSample, utcnow
from freshkeeper.hardware.sim_backend import (
    ADC_LEVELS, FridgeThermalModel, SimulatedSensorBackend,
)


class TestSensorSample:
    def test_feature_vector_order_matches_the_declared_names(self):
        sample = SensorSample(0, utcnow(), 4.2, 85.1, 12.0, 3.4, 178.0, -2.0)
        values = dict(zip(SENSOR_FEATURE_NAMES, sample.feature_vector()))
        assert values == {
            "ethanol_ppm": 12.0, "ammonia_ppm": 3.4, "temperature_c": 4.2,
            "humidity_pct": 85.1, "mass_delta_g": -2.0,
        }

    def test_timestamps_are_timezone_aware(self):
        # Naive local timestamps corrupt an hour of history twice a year.
        assert utcnow().tzinfo is not None

    def test_serialises_to_json_safe_types(self):
        payload = SensorSample(0, utcnow(), 4.0, 85.0, 1.0, 1.0, 100.0, 0.0).to_dict()
        assert isinstance(payload["timestamp"], str)


class TestFridgeThermalModel:
    def test_series_lengths_agree(self):
        import random
        temps, humidity = FridgeThermalModel().series(48.0, 0.5, random.Random(1))
        assert len(temps) == len(humidity) == 96

    def test_stays_in_a_plausible_range(self):
        import random
        temps, humidity = FridgeThermalModel().series(24 * 30, 0.5, random.Random(2))
        assert -2.0 < min(temps) < 8.0
        assert max(temps) < 25.0  # door openings, not a power cut
        assert all(0.30 <= h <= 0.99 for h in humidity)

    def test_door_openings_raise_the_mean(self):
        import random
        quiet = FridgeThermalModel(openings_per_day=1.0).series(
            24 * 14, 0.5, random.Random(3))[0]
        busy = FridgeThermalModel(openings_per_day=40.0).series(
            24 * 14, 0.5, random.Random(3))[0]
        assert sum(busy) / len(busy) > sum(quiet) / len(quiet)

    def test_generation_is_fast_enough_for_long_horizons(self):
        # The corpus generator runs this thousands of times; the original
        # quadratic version made a single 60-day trajectory take minutes.
        import random, time
        start = time.perf_counter()
        FridgeThermalModel().series(24 * 180, 0.5, random.Random(4))
        assert time.perf_counter() - start < 1.0


class TestSimulatedBackend:
    def test_reading_before_warm_up_is_refused(self):
        backend = SimulatedSensorBackend(slot_count=1)
        with pytest.raises(RuntimeError, match="warm_up"):
            backend.read_slot(0)

    def test_read_all_covers_every_slot(self):
        backend = SimulatedSensorBackend(slot_count=4, seed=1)
        samples = backend.read_all()
        assert [s.slot_id for s in samples] == [0, 1, 2, 3]

    def test_same_seed_gives_the_same_readings(self):
        a = SimulatedSensorBackend(slot_count=2, seed=77)
        b = SimulatedSensorBackend(slot_count=2, seed=77)
        for x, y in zip(a.read_all(), b.read_all()):
            assert x.ethanol_ppm == y.ethanol_ppm
            assert x.mass_g == y.mass_g

    def test_readings_are_physically_plausible(self):
        backend = SimulatedSensorBackend(slot_count=3, time_acceleration=12.0, seed=5)
        for _ in range(20):
            for sample in backend.read_all():
                assert -5.0 < sample.temperature_c < 30.0
                assert 0.0 <= sample.humidity_pct <= 100.0
                assert sample.ethanol_ppm >= 0.0
                assert sample.ammonia_ppm >= 0.0
                assert sample.mass_g > 0.0

    def test_volatiles_rise_as_an_item_spoils(self):
        backend = SimulatedSensorBackend(slot_count=1, time_acceleration=24.0, seed=11)
        backend.place_item(0, "strawberry")
        early = backend.read_all()[0]
        for _ in range(9):
            late = backend.read_all()[0]
        assert late.ethanol_ppm > early.ethanol_ppm
        assert late.mass_g < early.mass_g

    def test_firm_fruit_outlasts_soft_fruit(self):
        backend = SimulatedSensorBackend(slot_count=2, time_acceleration=24.0, seed=13)
        backend.place_item(0, "strawberry")
        backend.place_item(1, "pomegranate")
        for _ in range(8):
            backend.read_all()
        assert backend.ground_truth(0)[1] > backend.ground_truth(1)[1]

    def test_gas_readings_are_quantised_by_the_adc(self):
        # Readings pass through a 10-bit ADC, so they cannot be continuous.
        backend = SimulatedSensorBackend(slot_count=1, time_acceleration=6.0, seed=21)
        backend.place_item(0, "banana")
        values = {backend.read_all()[0].ethanol_ppm for _ in range(40)}
        assert len(values) < ADC_LEVELS

    def test_camera_returns_none_rather_than_a_fake_path(self):
        # The simulator models the sensor array, never the imagery.
        backend = SimulatedSensorBackend(slot_count=1, seed=1)
        assert backend.capture_image(0) is None


class TestCrossProcessReproducibility:
    def test_readings_do_not_depend_on_pythonhashseed(self):
        """The seed must be the only source of randomness.

        An earlier version derived per-item seeds from hash() of a string,
        which Python salts per interpreter process. Same seed, different
        process, different readings -- while the thesis claimed exact
        reproducibility. Run the simulation in two subprocesses with different
        hash seeds and require identical output.
        """
        import os, subprocess, sys
        code = (
            "import sys; sys.path.insert(0, %r)\n"
            "from freshkeeper.hardware.sim_backend import SimulatedSensorBackend\n"
            "b = SimulatedSensorBackend(slot_count=2, time_acceleration=24.0, seed=42)\n"
            "b.place_item(0, 'strawberry'); b.place_item(1, 'apple')\n"
            "for _ in range(5): s = b.read_all()\n"
            "print(s[0].ethanol_ppm, s[1].mass_g, s[0].temperature_c)\n"
        ) % os.getcwd()
        outputs = []
        for seed in ("1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            outputs.append(subprocess.run(
                [sys.executable, "-c", code], env=env, capture_output=True,
                text=True, check=True).stdout.strip())
        assert outputs[0] == outputs[1], (
            f"readings differ across processes: {outputs}")
