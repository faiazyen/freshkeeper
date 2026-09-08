"""Tests for the alert engine.

Most of these exist to hold the line on alert fatigue. A system that notifies
on every cycle gets muted, and a muted system saves no food.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from freshkeeper.alerts import (
    AlertType, MIN_CONFIDENCE, STALE_AFTER_DAYS, USE_SOON_SCORE,
    estimate_days_remaining, evaluate_item, freshness_score, snooze_until,
)
from freshkeeper.db.models import FoodItem, SpoilagePrediction, SpoilageState

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)


def make_item(**overrides) -> FoodItem:
    defaults = dict(id=1, slot_id=0, name="Strawberries", commodity="strawberry",
                    initial_mass_g=250.0, added_at=NOW - timedelta(days=2))
    defaults.update(overrides)
    return FoodItem(**defaults)


def make_prediction(p_fresh, p_marginal, p_spoiled, state, when=NOW, score=None):
    return SpoilagePrediction(
        item_id=1, state=state, p_fresh=p_fresh, p_marginal=p_marginal,
        p_spoiled=p_spoiled, predicted_at=when,
        freshness_score=(score if score is not None
                         else freshness_score(p_fresh, p_marginal, p_spoiled)),
    )


class TestFreshnessScore:
    def test_endpoints(self):
        assert freshness_score(1, 0, 0) == 100.0
        assert freshness_score(0, 0, 1) == 0.0
        assert freshness_score(0, 1, 0) == 50.0

    def test_uses_the_whole_distribution(self):
        # Torn between fresh and spoiled should land mid-range, not flip with
        # the argmax.
        assert freshness_score(0.5, 0.0, 0.5) == pytest.approx(50.0)

    def test_handles_a_degenerate_distribution(self):
        assert freshness_score(0, 0, 0) == 0.0

    def test_normalises_unnormalised_input(self):
        assert freshness_score(2, 0, 0) == 100.0


class TestAlertGeneration:
    def test_fires_on_the_transition_into_spoiled(self):
        alert = evaluate_item(
            make_item(),
            make_prediction(0.05, 0.15, 0.80, SpoilageState.SPOILED),
            make_prediction(0.60, 0.30, 0.10, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW)
        assert alert is not None
        assert alert.alert_type is AlertType.SPOILAGE_DETECTED

    def test_stays_silent_while_it_remains_spoiled(self):
        spoiled = make_prediction(0.05, 0.15, 0.80, SpoilageState.SPOILED)
        previous = make_prediction(0.05, 0.15, 0.80, SpoilageState.SPOILED,
                                   NOW - timedelta(hours=1))
        assert evaluate_item(make_item(), spoiled, previous, NOW) is None

    def test_use_soon_on_crossing_the_threshold(self):
        # 0.10 + 0.5*0.55 = 0.375 -> score 37.5, just under the threshold,
        # with a top-class probability that still clears the confidence floor.
        alert = evaluate_item(
            make_item(),
            make_prediction(0.10, 0.55, 0.35, SpoilageState.MARGINAL),
            make_prediction(0.80, 0.15, 0.05, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW)
        assert alert is not None and alert.alert_type is AlertType.USE_SOON
        assert alert.freshness_score <= USE_SOON_SCORE

    def test_no_repeat_use_soon(self):
        current = make_prediction(0.10, 0.55, 0.35, SpoilageState.MARGINAL)
        previous = make_prediction(0.12, 0.56, 0.32, SpoilageState.MARGINAL,
                                   NOW - timedelta(hours=1))
        assert evaluate_item(make_item(), current, previous, NOW) is None

    def test_low_confidence_predictions_stay_quiet(self):
        unsure = make_prediction(0.40, 0.35, 0.25, SpoilageState.FRESH)
        assert max(unsure.p_fresh, unsure.p_marginal, unsure.p_spoiled) < MIN_CONFIDENCE
        assert evaluate_item(
            make_item(), unsure,
            make_prediction(0.9, 0.05, 0.05, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW) is None

    def test_snoozing_suppresses_everything(self):
        item = make_item(snoozed_until=NOW + timedelta(hours=6))
        assert evaluate_item(
            item, make_prediction(0.02, 0.08, 0.90, SpoilageState.SPOILED),
            make_prediction(0.9, 0.05, 0.05, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW) is None

    def test_an_expired_snooze_stops_suppressing(self):
        item = make_item(snoozed_until=NOW - timedelta(hours=1))
        assert evaluate_item(
            item, make_prediction(0.02, 0.08, 0.90, SpoilageState.SPOILED),
            make_prediction(0.9, 0.05, 0.05, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW) is not None

    def test_a_manual_override_silences_the_model(self):
        item = make_item(manual_state="fresh")
        assert evaluate_item(
            item, make_prediction(0.02, 0.08, 0.90, SpoilageState.SPOILED),
            make_prediction(0.9, 0.05, 0.05, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW) is None

    def test_stale_reminder_for_a_long_lived_item(self):
        item = make_item(added_at=NOW - timedelta(days=STALE_AFTER_DAYS))
        alert = evaluate_item(
            item, make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH),
            make_prediction(0.86, 0.11, 0.03, SpoilageState.FRESH,
                            NOW - timedelta(hours=1)),
            NOW)
        assert alert is not None and alert.alert_type is AlertType.STALE_ITEM

    def test_stale_reminder_fires_once_per_week_not_once_per_cycle(self):
        # Two cycles thirty minutes apart, both on day 7: the first crosses the
        # boundary and fires, the second must stay silent. The original
        # implementation fired on every cycle of day 7, 14, 21...
        added = NOW - timedelta(days=7, hours=8)
        item = make_item(added_at=added)
        earlier = make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH,
                                  NOW - timedelta(minutes=30))
        first = evaluate_item(
            item, make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH,
                                  NOW - timedelta(minutes=30)),
            make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH,
                            NOW - timedelta(days=1, hours=8)),
            NOW - timedelta(minutes=30))
        assert first is not None and first.alert_type is AlertType.STALE_ITEM
        second = evaluate_item(
            item, make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH), earlier, NOW)
        assert second is None

    def test_stale_reminder_repeats_at_the_next_week_boundary(self):
        item = make_item(added_at=NOW - timedelta(days=14, minutes=10))
        alert = evaluate_item(
            item, make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH),
            make_prediction(0.85, 0.12, 0.03, SpoilageState.FRESH,
                            NOW - timedelta(minutes=30)),
            NOW)
        assert alert is not None and alert.alert_type is AlertType.STALE_ITEM

    def test_first_ever_prediction_can_alert(self):
        alert = evaluate_item(
            make_item(),
            make_prediction(0.02, 0.08, 0.90, SpoilageState.SPOILED),
            None, NOW)
        assert alert is not None

    def test_naive_timestamps_are_treated_as_utc(self):
        # SQLite returns naive datetimes; this must not raise.
        item = make_item(added_at=datetime(2026, 9, 1, 12, 0))
        evaluate_item(item, make_prediction(0.9, 0.05, 0.05, SpoilageState.FRESH),
                      None, NOW)


class TestDaysRemaining:
    def test_needs_enough_points(self):
        assert estimate_days_remaining([]) is None
        assert estimate_days_remaining(
            [make_prediction(0.9, 0.1, 0, SpoilageState.FRESH)]) is None

    def test_extrapolates_a_decline(self):
        history = [
            make_prediction(0.9, 0.1, 0, SpoilageState.FRESH,
                            NOW - timedelta(days=d), score=score)
            for d, score in ((3, 90), (2, 78), (1, 66), (0, 54))
        ]
        estimate = estimate_days_remaining(history)
        assert estimate is not None and 1.0 < estimate < 2.0

    def test_returns_none_when_not_declining(self):
        history = [
            make_prediction(0.9, 0.1, 0, SpoilageState.FRESH,
                            NOW - timedelta(days=d), score=90)
            for d in (3, 2, 1, 0)
        ]
        assert estimate_days_remaining(history) is None

    def test_zero_when_already_past_the_threshold(self):
        history = [
            make_prediction(0.2, 0.3, 0.5, SpoilageState.MARGINAL,
                            NOW - timedelta(days=d), score=score)
            for d, score in ((3, 60), (2, 50), (1, 42), (0, 30))
        ]
        assert estimate_days_remaining(history) == 0.0


def test_snooze_window_is_in_the_future():
    assert snooze_until(NOW) > NOW
