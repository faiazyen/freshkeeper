"""Alert generation and the freshness score.

The model emits three class probabilities. That is not what a person wants to
see on a phone at eight in the morning, so this module turns probabilities into
a number, a trend and, when it is worth interrupting someone, an alert.

The design constraint that shapes everything here is alert fatigue. A system
that cries wolf gets ignored, and an ignored system saves no food at all. Three
mechanisms hold the notification rate down:

* An alert fires on a *state transition*, never on a state. An item that is
  spoiled today and still spoiled tomorrow generates one alert, not two.
* Snoozing suppresses everything for an item for a fixed window.
* Predictions must clear a confidence floor. A 40/35/25 split across three
  classes is the model saying it does not know, and that is not worth a push
  notification.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .db.models import FoodItem, SpoilagePrediction, SpoilageState

#: Freshness score below which an item should be eaten soon.
USE_SOON_SCORE = 40.0
#: Freshness score below which an item is treated as spoiled.
SPOILED_SCORE = 20.0
#: Minimum P(spoiled) for a spoilage alert on probability grounds alone.
SPOILED_PROBABILITY = 0.70
#: Below this top-class probability the model is not confident enough to
#: interrupt anyone.
MIN_CONFIDENCE = 0.55
#: Days an item can sit untouched before it gets a reminder regardless of state.
STALE_AFTER_DAYS = 7.0
#: How long a snooze lasts.
SNOOZE_HOURS = 24.0


class AlertType(str, enum.Enum):
    USE_SOON = "use_soon"
    SPOILAGE_DETECTED = "spoilage_detected"
    STALE_ITEM = "stale_item"


@dataclass(frozen=True)
class Alert:
    item_id: int
    item_name: str
    alert_type: AlertType
    message: str
    freshness_score: float
    raised_at: datetime


def freshness_score(p_fresh: float, p_marginal: float, p_spoiled: float) -> float:
    """Collapse three class probabilities into a 0-100 score.

    The score is the expected freshness under the predicted distribution, with
    fresh worth 100, marginal 50 and spoiled 0. Using the full distribution
    rather than the top class means an item the model is torn between fresh
    and spoiled lands in the middle, where it belongs, instead of flipping
    between the extremes as the argmax changes.
    """
    total = p_fresh + p_marginal + p_spoiled
    if total <= 0:
        return 0.0
    return round(100.0 * (p_fresh + 0.5 * p_marginal) / total, 1)


def estimate_days_remaining(history: list[SpoilagePrediction],
                            min_points: int = 3) -> float | None:
    """Extrapolate days until the score reaches the use-soon threshold.

    A straight line is fitted through the recent score history by least
    squares and extended forward. A line is a poor description of a spoilage
    curve over its whole span, but over the last day or two of samples it is
    a decent local approximation, and the alternative -- fitting a sigmoid to
    six noisy points -- is worse.

    Returns None when there are too few points or the item is not declining,
    because "no estimate" is more honest than a number invented from noise.
    """
    if len(history) < min_points:
        return None

    points = sorted(history, key=lambda p: p.predicted_at)[-12:]
    t0 = points[0].predicted_at
    xs = [(p.predicted_at - t0).total_seconds() / 86400.0 for p in points]
    ys = [p.freshness_score for p in points]

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator

    # A flat or rising score means no decline to extrapolate. Scores do drift
    # upward slightly on noise, so require a real downward trend.
    if slope >= -0.5:
        return None

    current = ys[-1]
    if current <= USE_SOON_SCORE:
        return 0.0
    return round((current - USE_SOON_SCORE) / -slope, 1)


def _confident(prediction: SpoilagePrediction) -> bool:
    return max(prediction.p_fresh, prediction.p_marginal,
               prediction.p_spoiled) >= MIN_CONFIDENCE


def evaluate_item(
    item: FoodItem,
    current: SpoilagePrediction,
    previous: SpoilagePrediction | None,
    now: datetime | None = None,
) -> Alert | None:
    """Decide whether this item warrants an alert right now.

    Args:
        item: the tracked item.
        current: its newest prediction.
        previous: the prediction before that, or None if this is the first.
        now: injectable clock, so the tests are not timing-dependent.

    Returns at most one alert. When an item qualifies for several, the most
    urgent wins; sending two notifications about one tomato is how a user
    learns to swipe the app away.
    """
    now = now or datetime.now(timezone.utc)

    if item.snoozed_until and item.snoozed_until > now:
        return None
    if item.manual_state is not None:
        # The user has overridden the model. Respect that and stay quiet.
        return None
    if not _confident(current):
        return None

    score = current.freshness_score
    was_spoiled = previous is not None and previous.state == SpoilageState.SPOILED
    spoiled_now = (
        current.state == SpoilageState.SPOILED
        or score <= SPOILED_SCORE
        or current.p_spoiled >= SPOILED_PROBABILITY
    )

    if spoiled_now and not was_spoiled:
        return Alert(
            item_id=item.id, item_name=item.name,
            alert_type=AlertType.SPOILAGE_DETECTED,
            message=f"{item.name} looks spoiled. Check it before eating.",
            freshness_score=score, raised_at=now,
        )

    was_below = previous is not None and previous.freshness_score <= USE_SOON_SCORE
    if not spoiled_now and score <= USE_SOON_SCORE and not was_below:
        return Alert(
            item_id=item.id, item_name=item.name,
            alert_type=AlertType.USE_SOON,
            message=f"{item.name} is going over. Use it in the next day or two.",
            freshness_score=score, raised_at=now,
        )

    age_days = (now - _aware(item.added_at)).total_seconds() / 86400.0
    if age_days >= STALE_AFTER_DAYS and not spoiled_now:
        # Fire once when the item crosses each seven-day boundary, and not
        # again until the next one. The first version tested
        # int(age_days) % 7 == 0, which is true for the whole of day seven --
        # on a thirty-minute cycle that is forty-eight reminders in a day, the
        # exact fatigue failure this module exists to prevent. Comparing the
        # week index of this cycle with the previous one fires exactly once.
        this_week = int(age_days // STALE_AFTER_DAYS)
        if previous is None:
            crossed = True
        else:
            prev_age = (_aware(previous.predicted_at)
                        - _aware(item.added_at)).total_seconds() / 86400.0
            crossed = int(prev_age // STALE_AFTER_DAYS) < this_week
        if crossed:
            return Alert(
                item_id=item.id, item_name=item.name,
                alert_type=AlertType.STALE_ITEM,
                message=f"{item.name} has been in there {int(age_days)} days.",
                freshness_score=score, raised_at=now,
            )

    return None


def _aware(value: datetime) -> datetime:
    """SQLite hands back naive datetimes; treat those as UTC."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def snooze_until(now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)) + timedelta(hours=SNOOZE_HOURS)
