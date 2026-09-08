"""Hardware abstraction for the sensing platform.

The rest of the system talks to :class:`SensorBackend` and never imports a
GPIO library directly. Two implementations exist: :mod:`rpi_backend` drives
real hardware on a Raspberry Pi, and :mod:`sim_backend` synthesises readings
from the spoilage physics in :mod:`spoilage_model`.

Keeping the seam here is what lets the backend, the API, the alert logic and
the whole test suite run on a laptop with no sensors attached, and it means
swapping in real hardware later changes one line of configuration rather than
touching application code.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class SensorSample:
    """One complete measurement cycle for one shelf slot."""

    slot_id: int
    timestamp: datetime
    temperature_c: float
    humidity_pct: float
    #: MQ-3 reading, converted from resistance ratio to ppm ethanol equivalent.
    ethanol_ppm: float
    #: MQ-135 reading, converted to ppm ammonia equivalent.
    ammonia_ppm: float
    mass_g: float
    #: Change in mass since the item was registered, in grams. Negative means
    #: the item has dried out, which is the usual direction.
    mass_delta_g: float
    #: Path to the JPEG captured for this slot, or None if the camera is off.
    image_path: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    def feature_vector(self) -> list[float]:
        """The five numeric features the fusion model's MLP branch consumes.

        Order matters and is fixed here so that training and inference cannot
        disagree about it. :mod:`freshkeeper.ml.model` imports this ordering
        rather than restating it.
        """
        return [
            self.ethanol_ppm,
            self.ammonia_ppm,
            self.temperature_c,
            self.humidity_pct,
            self.mass_delta_g,
        ]


#: Names of the numeric sensor features, in the order returned by
#: :meth:`SensorSample.feature_vector`.
SENSOR_FEATURE_NAMES = [
    "ethanol_ppm",
    "ammonia_ppm",
    "temperature_c",
    "humidity_pct",
    "mass_delta_g",
]


class SensorBackend(abc.ABC):
    """Interface every sensing implementation must provide."""

    #: Number of physically addressable slots on the monitored shelf.
    slot_count: int = 6
    #: Privacy switch. When False, capture_image() must return None without
    #: exposing the sensor; the service then runs sensor-only.
    camera_enabled: bool = True

    @abc.abstractmethod
    def warm_up(self) -> None:
        """Bring the gas sensor heaters to a stable operating point.

        MQ-series sensors read high and drift for the first several seconds
        after the heater is powered. Callers must invoke this before a
        measurement cycle and discard anything read during it.
        """

    @abc.abstractmethod
    def read_slot(self, slot_id: int) -> SensorSample:
        """Take one complete reading for a single slot."""

    @abc.abstractmethod
    def capture_image(self, slot_id: int) -> str | None:
        """Capture and store an image for a slot; return its path."""

    def read_all(self) -> list[SensorSample]:
        """Read every slot in one cycle, warming up the gas sensors once."""
        self.warm_up()
        return [self.read_slot(i) for i in range(self.slot_count)]

    def close(self) -> None:
        """Release hardware resources. The default is a no-op."""


def utcnow() -> datetime:
    """Timezone-aware UTC timestamp.

    Readings are stored in UTC and converted for display. A prototype that
    logs naive local timestamps produces a corrupt hour of history twice a
    year, which is a tedious thing to debug months later.
    """
    return datetime.now(timezone.utc)
