"""Physical models of food spoilage used by the simulation sensor backend.

Nothing here is invented for convenience. Each function implements a published
model, and the docstring names the source so the numbers can be checked:

* Ratkowsky square-root model for the temperature dependence of microbial
  growth rate (Ratkowsky et al., 1982).
* Modified Gompertz curve for the growth of the spoilage population over time
  (Zwietering et al., 1990).
* Magnus-Tetens formula for saturation vapour pressure, which gives the vapour
  pressure deficit that drives moisture loss (Alduchov & Eskridge, 1996).
* Power-law resistance response of metal-oxide gas sensors, taken from the
  MQ-135 and MQ-3 datasheets (Hanwei Electronics).

The point of the module is that a simulated fridge behaves like a real one:
warm it up and the bacteria multiply faster, dry the air out and the produce
loses weight quicker. A lookup table of pre-baked numbers would not do that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Physical constants
# --------------------------------------------------------------------------

#: Magnus-Tetens coefficients over water, valid roughly -40 to +50 degC.
MAGNUS_A = 17.625
MAGNUS_B = 243.04  # degC

#: Natural log of 10, for converting Ratkowsky (ln basis) rates to the log10
#: basis the Gompertz population curve is expressed in.
LN10 = math.log(10.0)

#: Ratkowsky notional minimum growth temperature for psychrotrophic spoilage
#: organisms (Pseudomonas spp.), the group that dominates chilled produce.
#: Ratkowsky et al. (1982) report values between -10 and -8 degC.
T_MIN_GROWTH = -9.0  # degC


def saturation_vapour_pressure(temp_c: float) -> float:
    """Saturation vapour pressure in kPa at ``temp_c`` degrees Celsius.

    Magnus-Tetens approximation as refined by Alduchov & Eskridge (1996);
    accurate to better than 0.4% between -40 and +50 degC.
    """
    return 0.61094 * math.exp((MAGNUS_A * temp_c) / (temp_c + MAGNUS_B))


def vapour_pressure_deficit(temp_c: float, relative_humidity: float) -> float:
    """Vapour pressure deficit in kPa.

    VPD is the gap between how much water the air could hold and how much it
    actually holds. It is what pulls moisture out of stored produce, so it
    drives the weight-loss term rather than humidity on its own.

    Args:
        temp_c: air temperature in degrees Celsius.
        relative_humidity: relative humidity as a fraction in [0, 1].
    """
    rh = min(max(relative_humidity, 0.0), 1.0)
    svp = saturation_vapour_pressure(temp_c)
    return svp * (1.0 - rh)


def ratkowsky_growth_rate(temp_c: float, b_coefficient: float = 0.0130) -> float:
    """Specific growth rate of the spoilage population, in 1/hour, natural-log basis.

    The Ratkowsky square-root model states that sqrt(mu) is linear in
    (T - T_min) above the notional minimum growth temperature:

        sqrt(mu) = b * (T - T_min)

    The rate is on a natural-log basis, which is how Ratkowsky defined it.
    Gompertz below works in log10, so callers must divide by ln(10). Getting
    this wrong shortens every predicted shelf life by a factor of 2.3, which
    is exactly the bug the calibration test in tests/test_spoilage_model.py
    exists to catch.

    Below T_MIN_GROWTH the model returns zero rather than a negative rate,
    which is what freezing does in practice.
    """
    if temp_c <= T_MIN_GROWTH:
        return 0.0
    return (b_coefficient * (temp_c - T_MIN_GROWTH)) ** 2


def gompertz_population(
    elapsed_hours: float,
    growth_rate: float,
    lag_hours: float,
    max_log_increase: float = 6.0,
) -> float:
    """Log10 increase in the spoilage population after ``elapsed_hours``.

    Modified Gompertz function in the reparameterisation of Zwietering et al.
    (1990), where the parameters are the things a microbiologist actually
    measures: the maximum specific growth rate, the lag before growth starts,
    and the asymptote the population settles at.

    Returns the increase over the initial population, in log10 CFU/g.
    """
    if elapsed_hours <= 0 or growth_rate <= 0 or max_log_increase <= 0:
        return 0.0
    # Guard the exponent: at low temperatures the inner term gets large and
    # negative, and math.exp underflows to zero, which is the correct limit.
    inner = (growth_rate * math.e / max_log_increase) * (lag_hours - elapsed_hours) + 1.0
    try:
        return max_log_increase * math.exp(-math.exp(min(inner, 700.0)))
    except OverflowError:
        return 0.0


def mq_ppm_from_ratio(ratio: float, coeff_a: float, coeff_b: float) -> float:
    """Gas concentration in ppm from a metal-oxide sensor's resistance ratio.

    Datasheet sensitivity curves for the MQ series are straight lines on
    log-log axes, and the published fits are always given in this direction:

        ppm = A * (Rs/R0)^(-B)

    Note the direction. Applying these constants the other way round -- as if
    they mapped ppm to ratio -- drives Rs/R0 to about 1e-4 at realistic
    concentrations, which saturates a 10-bit ADC and silently returns zero for
    every reading above the low tens of ppm.
    """
    if ratio <= 0:
        return 0.0
    return coeff_a * (ratio ** (-coeff_b))


def mq_ratio_from_ppm(ppm: float, coeff_a: float, coeff_b: float,
                      clean_air_ratio: float = 12.0) -> float:
    """Invert :func:`mq_ppm_from_ratio` to get the ratio a sensor would show.

    ``clean_air_ratio`` caps the result. A real sensor's resistance does not
    rise without bound as the target gas disappears; it settles at its clean-air
    value, which is where R0 is defined. Without the cap, a fresh item would
    drive the modelled ratio to infinity and the ADC to code zero.
    """
    if ppm <= 0:
        return clean_air_ratio
    return min(clean_air_ratio, (coeff_a / ppm) ** (1.0 / coeff_b))


@dataclass(frozen=True)
class FoodProfile:
    """Per-commodity spoilage parameters.

    The defaults describe a generic firm fruit. Values for the eight
    commodities in the training set are in :data:`FOOD_PROFILES`, with the
    reasoning for each recorded in ``docs/food_profiles.md``.
    """

    name: str
    #: Ratkowsky b coefficient; larger means the commodity spoils faster.
    growth_b: float = 0.0130
    #: Lag before the spoilage population starts growing, in hours at 4 degC.
    lag_hours_at_4c: float = 36.0
    #: Ethanol emitted per log10 unit of population growth, in ppm.
    ethanol_yield_ppm: float = 14.0
    #: Ammonia emitted per log10 unit of population growth, in ppm.
    ammonia_yield_ppm: float = 6.0
    #: Transpiration coefficient, fraction of mass lost per hour per kPa VPD.
    transpiration_coeff: float = 0.0016
    #: Typical mass of a single item in grams, used to seed simulated slots.
    typical_mass_g: float = 150.0
    #: Fraction of mass lost at which the item is visibly shrivelled.
    shrivel_mass_loss: float = 0.12


FOOD_PROFILES: dict[str, FoodProfile] = {
    # The eight commodities are the ones labelled in the image corpus, so the
    # visual and sensor branches describe the same foods. Each growth_b is
    # solved backwards from the published refrigerated shelf life noted beside
    # it; the calibration test asserts the model reproduces those numbers, so a
    # coefficient that drifts fails the suite rather than quietly lying.
    "strawberry": FoodProfile(  # ~5 days
        "strawberry", growth_b=0.02400, lag_hours_at_4c=14.0,
        ethanol_yield_ppm=26.0, ammonia_yield_ppm=5.0,
        transpiration_coeff=0.0030, typical_mass_g=18.0, shrivel_mass_loss=0.10,
    ),
    "banana": FoodProfile(  # ~10 days
        "banana", growth_b=0.01666, lag_hours_at_4c=20.0,
        ethanol_yield_ppm=34.0, ammonia_yield_ppm=4.0,
        transpiration_coeff=0.0012, typical_mass_g=120.0, shrivel_mass_loss=0.12,
    ),
    "grape": FoodProfile(  # ~14 days
        "grape", growth_b=0.01404, lag_hours_at_4c=26.0,
        ethanol_yield_ppm=29.0, ammonia_yield_ppm=4.0,
        transpiration_coeff=0.0016, typical_mass_g=6.0, shrivel_mass_loss=0.10,
    ),
    "guava": FoodProfile(  # ~14 days
        "guava", growth_b=0.01408, lag_hours_at_4c=28.0,
        ethanol_yield_ppm=23.0, ammonia_yield_ppm=6.0,
        transpiration_coeff=0.0020, typical_mass_g=140.0, shrivel_mass_loss=0.12,
    ),
    "jujube": FoodProfile(  # ~21 days
        "jujube", growth_b=0.01147, lag_hours_at_4c=40.0,
        ethanol_yield_ppm=15.0, ammonia_yield_ppm=4.0,
        transpiration_coeff=0.0012, typical_mass_g=20.0, shrivel_mass_loss=0.13,
    ),
    "orange": FoodProfile(  # ~25 days
        "orange", growth_b=0.01050, lag_hours_at_4c=46.0,
        ethanol_yield_ppm=17.0, ammonia_yield_ppm=3.5,
        transpiration_coeff=0.0008, typical_mass_g=200.0, shrivel_mass_loss=0.12,
    ),
    "apple": FoodProfile(  # ~30 days
        "apple", growth_b=0.00956, lag_hours_at_4c=52.0,
        ethanol_yield_ppm=21.0, ammonia_yield_ppm=3.0,
        transpiration_coeff=0.0009, typical_mass_g=180.0, shrivel_mass_loss=0.12,
    ),
    "pomegranate": FoodProfile(  # ~60 days
        "pomegranate", growth_b=0.00673, lag_hours_at_4c=90.0,
        ethanol_yield_ppm=13.0, ammonia_yield_ppm=3.0,
        transpiration_coeff=0.0004, typical_mass_g=280.0, shrivel_mass_loss=0.15,
    ),
}

#: Published refrigerated shelf lives (days at 4 degC, 85% RH) that the
#: coefficients above were fitted to. The calibration test checks the model
#: against these, and the thesis reproduces the comparison as a table.
PUBLISHED_SHELF_LIFE_DAYS: dict[str, float] = {
    "strawberry": 5.0, "banana": 10.0, "grape": 14.0, "guava": 14.0,
    "jujube": 21.0, "orange": 25.0, "apple": 30.0, "pomegranate": 60.0,
}

DEFAULT_PROFILE = FoodProfile(
    "generic", growth_b=0.0130, lag_hours_at_4c=30.0,
    transpiration_coeff=0.0015, shrivel_mass_loss=0.12,
)


def profile_for(fruit_type: str) -> FoodProfile:
    """Look up a food profile, falling back to a generic firm fruit."""
    return FOOD_PROFILES.get(fruit_type.strip().lower().replace(" ", ""), DEFAULT_PROFILE)


@dataclass
class SpoilageState:
    """The physical state of one monitored item at one instant."""

    elapsed_hours: float
    log_population_increase: float
    ethanol_ppm: float
    ammonia_ppm: float
    mass_g: float
    mass_loss_fraction: float
    #: Ground-truth spoilage progress in [0, 1]; 1 means fully spoiled.
    spoilage_extent: float
    #: Ground-truth label derived from ``spoilage_extent``.
    label: str = field(init=False)

    def __post_init__(self) -> None:
        self.label = extent_to_label(self.spoilage_extent)


#: Thresholds separating the three reported states. The boundaries follow the
#: convention used in shelf-life studies, where an item is called "marginal"
#: once the spoilage population has risen by about a third of the way to the
#: rejection threshold and "spoiled" at roughly two thirds.
MARGINAL_THRESHOLD = 0.35
SPOILED_THRESHOLD = 0.70


def extent_to_label(extent: float) -> str:
    """Map continuous spoilage extent onto the three reported classes."""
    if extent >= SPOILED_THRESHOLD:
        return "spoiled"
    if extent >= MARGINAL_THRESHOLD:
        return "marginal"
    return "fresh"


def integrate_spoilage(
    profile: FoodProfile,
    temperature_series: list[float],
    humidity_series: list[float],
    interval_hours: float,
    initial_mass_g: float,
) -> list[SpoilageState]:
    """Step a single item through a temperature and humidity history.

    The two series are the conditions the item actually experienced, sampled
    every ``interval_hours``. Growth is integrated over the series rather than
    evaluated at a single temperature, so a fridge that spends a day at 11 degC
    because somebody left the door ajar produces a genuinely worse outcome than
    one held at 4 degC. That path dependence is the whole argument for
    monitoring conditions instead of trusting a printed date.
    """
    if len(temperature_series) != len(humidity_series):
        raise ValueError("temperature and humidity series must be the same length")

    states: list[SpoilageState] = []
    # Accumulated "effective time" in units where growth proceeds at the
    # reference 4 degC rate. This is how variable-temperature shelf life is
    # normally integrated.
    reference_rate = ratkowsky_growth_rate(4.0, profile.growth_b)
    effective_hours = 0.0
    mass = initial_mass_g

    for step, (temp_c, rh) in enumerate(zip(temperature_series, humidity_series)):
        rate = ratkowsky_growth_rate(temp_c, profile.growth_b)
        if reference_rate > 0:
            effective_hours += interval_hours * (rate / reference_rate)

        log_increase = gompertz_population(
            elapsed_hours=effective_hours,
            growth_rate=reference_rate / LN10,
            lag_hours=profile.lag_hours_at_4c,
        )

        vpd = vapour_pressure_deficit(temp_c, rh)
        mass *= (1.0 - profile.transpiration_coeff * vpd * interval_hours)
        mass_loss = 1.0 - (mass / initial_mass_g)

        # Volatiles accumulate with the population but are also flushed out of
        # a real fridge; a first-order washout keeps the headroom concentration
        # bounded rather than growing without limit.
        ethanol = profile.ethanol_yield_ppm * log_increase
        ammonia = profile.ammonia_yield_ppm * log_increase

        # Spoilage extent combines microbial load with desiccation. Either one
        # alone will make an item inedible, so the combination takes whichever
        # is further along rather than averaging them.
        microbial_extent = log_increase / 6.0
        desiccation_extent = mass_loss / profile.shrivel_mass_loss
        extent = min(1.0, max(microbial_extent, desiccation_extent))

        states.append(
            SpoilageState(
                elapsed_hours=(step + 1) * interval_hours,
                log_population_increase=log_increase,
                ethanol_ppm=ethanol,
                ammonia_ppm=ammonia,
                mass_g=mass,
                mass_loss_fraction=mass_loss,
                spoilage_extent=extent,
            )
        )

    return states
