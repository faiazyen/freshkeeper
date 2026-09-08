"""Simulation backend: synthesises sensor readings from the spoilage physics.

This is the backend the prototype runs on when no Raspberry Pi is attached.
It is not a stub that returns canned numbers. Each slot holds a simulated item
with a commodity profile and an age; every read integrates the spoilage model
over the conditions that slot has actually experienced and converts the result
into the voltages a real sensor would produce, complete with the noise,
quantisation and drift of the parts named in the bill of materials.

Two things make the output realistic rather than merely plausible:

* The fridge has a thermal model. The compressor cycles, the door gets opened,
  and the temperature wanders in a way that changes spoilage outcomes.
* Readings pass through the actual transfer functions of the specified parts:
  the MQ power law, the 10-bit MCP3008 quantisation, the DHT22's stated
  accuracy, and the HX711's noise floor.

Every noise source is seeded, so a run is reproducible from its seed.
"""

from __future__ import annotations

import math
import random
import zlib
from dataclasses import dataclass, field

from .base import SensorBackend, SensorSample, utcnow
from .spoilage_model import (
    FoodProfile,
    integrate_spoilage,
    mq_ppm_from_ratio,
    mq_ratio_from_ppm,
    profile_for,
)

# --------------------------------------------------------------------------
# Part characteristics, taken from datasheets
# --------------------------------------------------------------------------

#: MQ-3 power-law fit for ethanol, as ppm = A * (Rs/R0)^-B. The widely cited
#: fit is in mg/L; 0.4095 mg/L at unit ratio converts to 217.4 ppm using the
#: molar volume of ethanol vapour at room temperature.
MQ3_ETHANOL_A, MQ3_ETHANOL_B = 217.4, 1.6926
#: MQ-135 power-law fit for ammonia (Hanwei MQ-135 datasheet), same form.
MQ135_AMMONIA_A, MQ135_AMMONIA_B = 102.2, 2.473

#: Background VOC concentration in a domestic fridge headspace. Never zero:
#: there is always something outgassing in there.
AMBIENT_ETHANOL_PPM = 1.8
AMBIENT_AMMONIA_PPM = 0.9

#: MCP3008 is a 10-bit ADC, so the analogue chain resolves 1 part in 1024.
ADC_LEVELS = 1024
ADC_VREF = 3.3

#: DHT22 accuracy from its datasheet: +-0.5 degC and +-2% RH.
DHT22_TEMP_SIGMA = 0.25
DHT22_RH_SIGMA = 1.0

#: HX711 with a 5 kg cell settles to roughly +-1 g in this configuration.
HX711_NOISE_SIGMA_G = 0.4

#: Baseline clean-air resistance ratio the MQ sensors sit at, and the slow
#: drift they show as the heater ages.
MQ_BASELINE_RATIO = 1.0
MQ_DRIFT_PER_DAY = 0.004


@dataclass
class FridgeThermalModel:
    """Compressor cycling and door openings in a domestic refrigerator.

    A real fridge does not hold a setpoint. The compressor runs until the
    cabinet reaches the lower bound, stops until it drifts back to the upper
    bound, and every door opening dumps in warm room air that decays away over
    the following half hour. Items therefore see a sawtooth with spikes, and
    the spoilage integral over that is measurably worse than over a flat line.
    """

    setpoint_c: float = 4.0
    #: Half-width of the compressor deadband.
    deadband_c: float = 1.2
    #: Compressor cycle period in hours.
    cycle_hours: float = 1.6
    #: Expected door openings per day.
    openings_per_day: float = 8.0
    #: Peak temperature rise from one door opening, in degrees.
    opening_rise_c: float = 3.5
    #: Time constant for the cabinet to recover after an opening, in hours.
    recovery_hours: float = 0.5
    ambient_c: float = 21.0
    #: Relative humidity the cabinet settles at, as a fraction.
    base_humidity: float = 0.85

    def series(self, hours: float, interval_hours: float, rng: random.Random
               ) -> tuple[list[float], list[float]]:
        """Generate temperature and humidity series over ``hours``.

        Door-opening warmth decays exponentially, so instead of summing every
        past opening at every step -- which is quadratic and made generating a
        60-day pomegranate trajectory take minutes -- the accumulated excess is
        carried forward with one multiply per step.
        """
        steps = max(1, int(round(hours / interval_hours)))
        decay = math.exp(-interval_hours / self.recovery_hours)
        # Expected openings within one step, for a Poisson draw.
        rate_per_step = self.openings_per_day * interval_hours / 24.0

        temps: list[float] = []
        humidity: list[float] = []
        excess = 0.0
        for i in range(steps):
            t = i * interval_hours
            # Compressor sawtooth around the setpoint.
            phase = (t % self.cycle_hours) / self.cycle_hours
            temp = self.setpoint_c + self.deadband_c * (2.0 * abs(phase - 0.5) - 0.5)

            # Openings in this step, then decay of everything before it.
            excess *= decay
            if rate_per_step > 0:
                openings = _poisson(rate_per_step, rng)
                excess += openings * self.opening_rise_c
            temp += excess + rng.gauss(0.0, 0.08)
            temps.append(temp)

            # Warmer air holds more water, so RH dips when the cabinet warms,
            # and an open door lets dry room air in.
            rh = self.base_humidity - 0.012 * (temp - self.setpoint_c) + rng.gauss(0.0, 0.006)
            humidity.append(min(0.99, max(0.30, rh)))

        return temps, humidity


def _poisson(lam: float, rng: random.Random) -> int:
    """Small-lambda Poisson draw by Knuth's product method."""
    if lam <= 0:
        return 0
    if lam > 30:  # normal approximation; never hit at realistic door rates
        return max(0, int(rng.gauss(lam, math.sqrt(lam))))
    target = math.exp(-lam)
    product = 1.0
    k = 0
    while True:
        product *= rng.random()
        if product <= target:
            return k
        k += 1


@dataclass
class SimulatedItem:
    """One item occupying one slot."""

    slot_id: int
    fruit_type: str
    profile: FoodProfile
    initial_mass_g: float
    #: How long the item had already been stored when the run started.
    age_hours_at_start: float = 0.0
    label: str = "fresh"
    spoilage_extent: float = 0.0
    current_mass_g: float = 0.0
    ethanol_ppm: float = 0.0
    ammonia_ppm: float = 0.0

    def __post_init__(self) -> None:
        if not self.current_mass_g:
            self.current_mass_g = self.initial_mass_g


class SimulatedSensorBackend(SensorBackend):
    """A full sensing platform with no hardware behind it.

    Args:
        slot_count: number of shelf slots to simulate.
        interval_hours: simulated time between measurement cycles. The default
            of 0.5 matches the 30-minute duty cycle of the real system.
        time_acceleration: how many simulated hours pass per ``read_all``
            call. Set above ``interval_hours`` to compress weeks of storage
            into a short run, which is what the dataset generator does.
        seed: seed for every noise source, so runs are reproducible.
    """

    def __init__(
        self,
        slot_count: int = 6,
        interval_hours: float = 0.5,
        time_acceleration: float | None = None,
        seed: int = 20260908,
        fridge: FridgeThermalModel | None = None,
    ) -> None:
        self.slot_count = slot_count
        self.interval_hours = interval_hours
        self.step_hours = time_acceleration or interval_hours
        self.seed = seed
        self.rng = random.Random(seed)
        self.fridge = fridge or FridgeThermalModel()
        self.elapsed_hours = 0.0
        self.items: dict[int, SimulatedItem] = {}
        self._warmed = False
        for slot in range(slot_count):
            self.place_item(slot, self._random_commodity())

    # -- item management ---------------------------------------------------

    def _random_commodity(self) -> str:
        from .spoilage_model import FOOD_PROFILES
        return self.rng.choice(sorted(FOOD_PROFILES))

    def place_item(self, slot_id: int, fruit_type: str,
                   age_hours: float = 0.0, mass_g: float | None = None) -> SimulatedItem:
        """Put a (possibly already partly aged) item into a slot."""
        profile = profile_for(fruit_type)
        mass = mass_g if mass_g is not None else profile.typical_mass_g * self.rng.uniform(0.85, 1.15)
        item = SimulatedItem(
            slot_id=slot_id, fruit_type=fruit_type, profile=profile,
            initial_mass_g=mass, age_hours_at_start=age_hours,
        )
        self.items[slot_id] = item
        return item

    # -- SensorBackend -----------------------------------------------------

    def warm_up(self) -> None:
        """No physical heater, but advance simulated time by one step.

        Advancing here rather than in :meth:`read_slot` means every slot in a
        cycle sees the same instant, which is what the real hardware does.
        """
        self.elapsed_hours += self.step_hours
        self._warmed = True
        self._recompute()

    def _recompute(self) -> None:
        """Integrate every item forward over the conditions it has seen."""
        for item in self.items.values():
            total_hours = item.age_hours_at_start + self.elapsed_hours
            # Per-item seed derived with crc32, not hash(): Python salts str
            # hashes per process, so hash() made every run differ despite the
            # documented seed. The audit that found this is in tests/.
            item_seed = (self.seed * 1_000_003 + item.slot_id * 7_919
                         + zlib.crc32(item.fruit_type.encode())) & 0x7FFF_FFFF
            temps, rh = self.fridge.series(total_hours, self.interval_hours,
                                           random.Random(item_seed))
            if not temps:
                continue
            states = integrate_spoilage(
                item.profile, temps, rh, self.interval_hours, item.initial_mass_g)
            final = states[-1]
            item.spoilage_extent = final.spoilage_extent
            item.label = final.label
            item.current_mass_g = final.mass_g
            item.ethanol_ppm = final.ethanol_ppm
            item.ammonia_ppm = final.ammonia_ppm
            self._last_conditions = (temps[-1], rh[-1])

    def _quantise_gas(self, ppm: float, coeff_a: float, coeff_b: float,
                      ambient_ppm: float) -> float:
        """Push a concentration through the real analogue signal chain.

        Concentration becomes a resistance ratio via the datasheet power law,
        the ratio becomes a voltage across the load resistor, the MCP3008
        quantises that voltage to 10 bits, and the firmware then inverts the
        chain. The round trip is lossy on purpose: the recovered ppm is not the
        ppm we started with, and that quantisation error is part of what the
        fusion model has to cope with.
        """
        true_ppm = ppm + ambient_ppm
        ratio = mq_ratio_from_ppm(true_ppm, coeff_a, coeff_b)
        # Slow upward drift of the baseline as the heater element ages.
        drift = 1.0 + MQ_DRIFT_PER_DAY * (self.elapsed_hours / 24.0)
        ratio *= drift

        # Voltage divider: Vout = Vref * RL / (Rs + RL) with RL chosen equal to
        # R0, which reduces to Vref / (1 + Rs/R0).
        vout = ADC_VREF / (1.0 + ratio)
        vout += self.rng.gauss(0.0, 0.004)  # analogue front-end noise
        code = min(ADC_LEVELS - 1, max(1, int(round(vout / ADC_VREF * (ADC_LEVELS - 1)))))
        vout_q = code / (ADC_LEVELS - 1) * ADC_VREF

        recovered_ratio = max(1e-6, (ADC_VREF / vout_q) - 1.0) / drift
        return round(mq_ppm_from_ratio(recovered_ratio, coeff_a, coeff_b), 3)

    def read_slot(self, slot_id: int) -> SensorSample:
        if not self._warmed:
            raise RuntimeError("warm_up() must be called before reading gas sensors")
        item = self.items[slot_id]
        temp_true, rh_true = getattr(self, "_last_conditions", (4.0, 0.85))

        temp = round(temp_true + self.rng.gauss(0.0, DHT22_TEMP_SIGMA), 1)
        rh = round(rh_true * 100.0 + self.rng.gauss(0.0, DHT22_RH_SIGMA), 1)
        mass = round(item.current_mass_g + self.rng.gauss(0.0, HX711_NOISE_SIGMA_G), 1)

        return SensorSample(
            slot_id=slot_id,
            timestamp=utcnow(),
            temperature_c=temp,
            humidity_pct=min(100.0, max(0.0, rh)),
            ethanol_ppm=self._quantise_gas(
                item.ethanol_ppm, MQ3_ETHANOL_A, MQ3_ETHANOL_B, AMBIENT_ETHANOL_PPM),
            ammonia_ppm=self._quantise_gas(
                item.ammonia_ppm, MQ135_AMMONIA_A, MQ135_AMMONIA_B, AMBIENT_AMMONIA_PPM),
            mass_g=mass,
            mass_delta_g=round(mass - item.initial_mass_g, 1),
            image_path=None,
        )

    def capture_image(self, slot_id: int) -> str | None:
        """No camera attached. The dataset generator supplies real images.

        Returning None rather than a fake path keeps the honesty boundary
        explicit: this backend simulates the sensor array, never the imagery.
        """
        return None

    def ground_truth(self, slot_id: int) -> tuple[str, float]:
        """Label and spoilage extent for a slot, for building training data."""
        item = self.items[slot_id]
        return item.label, item.spoilage_extent
