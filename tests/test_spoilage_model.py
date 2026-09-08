"""Tests for the physical spoilage model.

The calibration test is the important one. Every growth coefficient was solved
backwards from a published shelf life, so if a coefficient is edited without
updating the reference, this fails and says so. A silently miscalibrated model
would still produce plausible-looking curves and completely wrong predictions.
"""

from __future__ import annotations

import math

import pytest

from freshkeeper.hardware.spoilage_model import (
    FOOD_PROFILES, LN10, MARGINAL_THRESHOLD, PUBLISHED_SHELF_LIFE_DAYS,
    SPOILED_THRESHOLD, T_MIN_GROWTH, extent_to_label, gompertz_population,
    integrate_spoilage, mq_ppm_from_ratio, mq_ratio_from_ppm, profile_for,
    ratkowsky_growth_rate, saturation_vapour_pressure, vapour_pressure_deficit,
)


def days_to_spoilage(commodity: str, temp_c: float = 4.0, rh: float = 0.85,
                     horizon_days: int = 150) -> float | None:
    profile = profile_for(commodity)
    steps = int(horizon_days * 24 / 2)
    states = integrate_spoilage(profile, [temp_c] * steps, [rh] * steps, 2.0,
                                profile.typical_mass_g)
    return next((s.elapsed_hours / 24 for s in states
                 if s.spoilage_extent >= SPOILED_THRESHOLD), None)


class TestVapourPressure:
    def test_matches_reference_values(self):
        # Reference saturation vapour pressures, in kPa.
        for temp_c, expected in [(0.0, 0.6109), (10.0, 1.2281), (20.0, 2.3392),
                                 (30.0, 4.2470)]:
            assert saturation_vapour_pressure(temp_c) == pytest.approx(expected, rel=0.01)

    def test_deficit_is_zero_at_saturation(self):
        assert vapour_pressure_deficit(4.0, 1.0) == pytest.approx(0.0, abs=1e-9)

    def test_deficit_grows_as_air_dries(self):
        assert (vapour_pressure_deficit(4.0, 0.50)
                > vapour_pressure_deficit(4.0, 0.85)
                > vapour_pressure_deficit(4.0, 0.95))

    def test_humidity_is_clamped(self):
        assert vapour_pressure_deficit(4.0, 1.5) >= 0.0
        assert vapour_pressure_deficit(4.0, -0.2) > 0.0


class TestRatkowsky:
    def test_no_growth_at_or_below_minimum(self):
        assert ratkowsky_growth_rate(T_MIN_GROWTH) == 0.0
        assert ratkowsky_growth_rate(T_MIN_GROWTH - 5) == 0.0

    def test_rate_increases_with_temperature(self):
        rates = [ratkowsky_growth_rate(t) for t in (0, 4, 10, 20, 30)]
        assert rates == sorted(rates)

    def test_square_root_relationship_holds(self):
        b = 0.0130
        for temp_c in (0.0, 5.0, 12.0):
            assert (math.sqrt(ratkowsky_growth_rate(temp_c, b))
                    == pytest.approx(b * (temp_c - T_MIN_GROWTH), rel=1e-9))


class TestGompertz:
    def test_starts_at_zero(self):
        assert gompertz_population(0, 0.02, 24) == 0.0

    def test_is_monotonic(self):
        values = [gompertz_population(h, 0.02, 24) for h in range(0, 500, 25)]
        assert all(b >= a for a, b in zip(values, values[1:]))

    def test_saturates_at_the_asymptote(self):
        assert gompertz_population(10_000, 0.02, 24, max_log_increase=6.0) \
            == pytest.approx(6.0, rel=1e-3)

    def test_no_growth_without_a_rate(self):
        assert gompertz_population(500, 0.0, 24) == 0.0


class TestMQSensorConversion:
    def test_round_trip(self):
        for ppm in (5.0, 25.0, 120.0):
            ratio = mq_ratio_from_ppm(ppm, 102.2, 2.473)
            assert mq_ppm_from_ratio(ratio, 102.2, 2.473) == pytest.approx(ppm, rel=1e-6)

    def test_higher_concentration_lowers_resistance(self):
        low = mq_ratio_from_ppm(5.0, 102.2, 2.473)
        high = mq_ratio_from_ppm(80.0, 102.2, 2.473)
        assert high < low

    def test_clean_air_ratio_caps_the_result(self):
        # Without the cap, zero ppm sends the ratio to infinity and the ADC to
        # code zero, which is how the ethanol channel once read a flat zero.
        assert mq_ratio_from_ppm(0.0, 102.2, 2.473, clean_air_ratio=12.0) == 12.0
        assert mq_ratio_from_ppm(1e-9, 102.2, 2.473, clean_air_ratio=12.0) == 12.0


class TestLabelThresholds:
    def test_boundaries(self):
        assert extent_to_label(0.0) == "fresh"
        assert extent_to_label(MARGINAL_THRESHOLD - 1e-9) == "fresh"
        assert extent_to_label(MARGINAL_THRESHOLD) == "marginal"
        assert extent_to_label(SPOILED_THRESHOLD - 1e-9) == "marginal"
        assert extent_to_label(SPOILED_THRESHOLD) == "spoiled"
        assert extent_to_label(1.0) == "spoiled"


class TestCalibration:
    @pytest.mark.parametrize("commodity,expected", sorted(PUBLISHED_SHELF_LIFE_DAYS.items()))
    def test_reproduces_published_shelf_life(self, commodity, expected):
        actual = days_to_spoilage(commodity)
        assert actual is not None, f"{commodity} never spoiled inside the horizon"
        assert actual == pytest.approx(expected, rel=0.05), (
            f"{commodity}: model gives {actual:.1f} d, literature says {expected:.1f} d. "
            "Either growth_b was edited without updating PUBLISHED_SHELF_LIFE_DAYS, "
            "or the Ratkowsky rate is being fed to Gompertz on the wrong log basis."
        )

    def test_every_profile_has_a_reference(self):
        assert set(FOOD_PROFILES) == set(PUBLISHED_SHELF_LIFE_DAYS)

    def test_log_basis_conversion_is_applied(self):
        # Guards the specific bug that made everything spoil 2.3x too fast.
        assert LN10 == pytest.approx(2.302585, rel=1e-5)
        assert days_to_spoilage("apple") > days_to_spoilage("strawberry") * 3


class TestPathDependence:
    def test_warmer_storage_spoils_faster(self):
        cold = days_to_spoilage("banana", temp_c=2.0)
        normal = days_to_spoilage("banana", temp_c=4.0)
        warm = days_to_spoilage("banana", temp_c=10.0)
        assert cold > normal > warm

    def test_q10_is_biologically_plausible(self):
        # A ten-degree rise should speed spoilage by roughly 2-4x.
        at_5 = days_to_spoilage("banana", temp_c=5.0)
        at_15 = days_to_spoilage("banana", temp_c=15.0)
        assert 2.0 <= at_5 / at_15 <= 4.5

    def test_a_warm_excursion_costs_shelf_life(self):
        # This is the argument for monitoring conditions rather than trusting a
        # printed date: two items of the same age, different histories.
        profile = profile_for("strawberry")
        steady = [4.0] * 240
        excursion = [4.0] * 100 + [14.0] * 40 + [4.0] * 100  # ~3 days warm
        rh = [0.85] * 240
        a = integrate_spoilage(profile, steady, rh, 1.0, profile.typical_mass_g)[-1]
        b = integrate_spoilage(profile, excursion, rh, 1.0, profile.typical_mass_g)[-1]
        assert b.spoilage_extent > a.spoilage_extent

    def test_drier_air_drives_more_mass_loss(self):
        profile = profile_for("strawberry")
        humid = integrate_spoilage(profile, [4.0] * 200, [0.95] * 200, 1.0, 100.0)[-1]
        dry = integrate_spoilage(profile, [4.0] * 200, [0.55] * 200, 1.0, 100.0)[-1]
        assert dry.mass_g < humid.mass_g


def test_mismatched_series_lengths_are_rejected():
    with pytest.raises(ValueError):
        integrate_spoilage(profile_for("apple"), [4.0] * 10, [0.85] * 5, 1.0, 100.0)
