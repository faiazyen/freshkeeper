"""Raspberry Pi sensor backend: the drivers for the physical build.

This module talks to real hardware over GPIO, SPI and CSI. It is written to be
deployed on a Raspberry Pi 4 running Raspberry Pi OS Bookworm, and the imports
it needs (``RPi.GPIO``, ``spidev``, ``adafruit_dht``, ``picamera2``) only exist
there. Importing this module on a development machine therefore raises
:class:`HardwareUnavailableError` with a message saying so, rather than
crashing with an opaque ImportError.

The prototype evaluated in this thesis ran against
:class:`~freshkeeper.hardware.sim_backend.SimulatedSensorBackend`. This module
is the deployment path for the physical build, and it exists so that moving to
hardware is a configuration change rather than a rewrite. It has been checked
for syntax and interface conformance by the test suite, but its readings have
not been validated against instruments, and the thesis does not claim they
have been.

Pin assignment (BCM numbering), matching the wiring diagram in the appendix:

    GPIO 4    DHT22 data (single-wire, 4.7k pull-up to 3V3)
    GPIO 5    HX711 DOUT
    GPIO 6    HX711 SCK
    GPIO 18   LED strip gate, via 2N7000 N-channel MOSFET
    GPIO 17   MQ heater supply gate, via IRLZ44N logic-level MOSFET
    SPI0      MCP3008 ADC: CE0=GPIO8, MOSI=GPIO10, MISO=GPIO9, SCLK=GPIO11
      CH0     MQ-135 analogue out (ammonia)
      CH1     MQ-3 analogue out (ethanol)
    CSI       Camera Module 3
"""

from __future__ import annotations

import time
from pathlib import Path

from .base import SensorBackend, SensorSample, utcnow
from .spoilage_model import mq_ppm_from_ratio

# Pin map, BCM numbering.
PIN_DHT22 = 4
PIN_HX711_DOUT = 5
PIN_HX711_SCK = 6
PIN_LED_GATE = 18
PIN_HEATER_GATE = 17
ADC_CHANNEL_MQ135 = 0
ADC_CHANNEL_MQ3 = 1

#: Seconds the MQ heaters need before their output is stable after being
#: switched on. The datasheet asks for a much longer burn-in on first ever
#: power-up; 30 s is the settling time between duty cycles once the sensor has
#: been conditioned. Heaters are gated so they draw power only while a cycle
#: is measuring, which is where most of the power budget in the thesis goes.
GAS_WARMUP_SECONDS = 30.0

#: The MQ modules output up to their 5 V supply, but the MCP3008 must not see
#: more than 3.3 V, so a resistive divider sits between them. This is the
#: fraction of the true sensor voltage that reaches the converter.
GAS_DIVIDER_RATIO = 3.3 / 5.0

#: Samples averaged per gas reading, and the gap between them.
GAS_SAMPLE_COUNT = 25
GAS_SAMPLE_INTERVAL = 0.2

#: The load cell and the gas heaters share a supply rail. Reading them at the
#: same moment couples heater switching noise into the HX711, which showed up
#: as multi-gram steps on the weight channel. Separating them in time fixes it.
WEIGHT_SETTLE_DELAY = 0.5

from .sim_backend import (  # noqa: E402  (constants shared with the simulator)
    MQ3_ETHANOL_A,
    MQ3_ETHANOL_B,
    MQ135_AMMONIA_A,
    MQ135_AMMONIA_B,
)


class HardwareUnavailableError(RuntimeError):
    """Raised when the Pi-only libraries are not importable."""


class RaspberryPiSensorBackend(SensorBackend):
    """Drives the physical sensor array.

    Args:
        slot_count: shelf slots; each has its own load cell and camera ROI.
        r0_mq135, r0_mq3: clean-air reference resistances in ohms, established
            by the calibration routine and stored in the config file. Without
            them the power-law conversion has no anchor and readings are
            meaningless in absolute terms.
        load_cell_scale: HX711 counts per gram, from the calibration routine.
        image_dir: where captured JPEGs are written.
    """

    def __init__(
        self,
        slot_count: int = 6,
        r0_mq135: float = 76000.0,
        r0_mq3: float = 60000.0,
        load_cell_scale: float = 428.0,
        load_cell_offset: int = 0,
        image_dir: str | Path = "data/captures",
        gas_divider_ratio: float = GAS_DIVIDER_RATIO,
    ) -> None:
        self.slot_count = slot_count
        self.r0_mq135 = r0_mq135
        self.r0_mq3 = r0_mq3
        self.load_cell_scale = load_cell_scale
        self.load_cell_offset = load_cell_offset
        self.gas_divider_ratio = gas_divider_ratio
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self._roi: dict[int, tuple[int, int, int, int]] = {}
        self._init_hardware()

    def _init_hardware(self) -> None:
        try:
            import RPi.GPIO as GPIO  # type: ignore
            import spidev  # type: ignore
            import adafruit_dht  # type: ignore
            import board  # type: ignore
            from picamera2 import Picamera2  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on host
            raise HardwareUnavailableError(
                "Raspberry Pi libraries are not available on this machine. "
                "Use SimulatedSensorBackend for development, or run on a Pi "
                "with RPi.GPIO, spidev, adafruit-circuitpython-dht and "
                "picamera2 installed."
            ) from exc

        self._gpio = GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(PIN_LED_GATE, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_HEATER_GATE, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_HX711_DOUT, GPIO.IN)
        GPIO.setup(PIN_HX711_SCK, GPIO.OUT, initial=GPIO.LOW)

        self._spi = spidev.SpiDev()
        self._spi.open(0, 0)
        self._spi.max_speed_hz = 1_350_000

        self._dht = adafruit_dht.DHT22(board.D4)

        self._camera = Picamera2()
        self._camera.configure(
            self._camera.create_still_configuration(main={"size": (1640, 1232)}))
        self._camera.start()
        time.sleep(2.0)  # auto-exposure needs a moment to settle

    # -- low-level reads ---------------------------------------------------

    def _read_adc(self, channel: int) -> int:
        """One 10-bit conversion from the MCP3008.

        The three-byte SPI transaction is the sequence given in the MCP3008
        datasheet: a start bit, then the single-ended channel select, then ten
        bits of result straddling the last two returned bytes.
        """
        if not 0 <= channel <= 7:
            raise ValueError(f"MCP3008 has channels 0-7, got {channel}")
        raw = self._spi.xfer2([1, (8 + channel) << 4, 0])
        return ((raw[1] & 3) << 8) + raw[2]

    def _adc_to_resistance(self, code: int, load_resistance: float = 10_000.0,
                           divider_ratio: float | None = None) -> float:
        """Convert an ADC code to the sensor's resistance Rs, in ohms.

        The MQ module puts its sensing element in series with a load resistor.
        With Vcc across the pair and Vout measured across the load,
        Rs = RL * (Vcc - Vout) / Vout.

        The converter reads the divided-down voltage, so it is scaled back up
        by ``divider_ratio`` before the formula is applied. An earlier version
        skipped that step and would have reported every resistance too high by
        the divider ratio -- undetectable without hardware, which is exactly why
        it is spelled out.
        """
        ratio = (getattr(self, "gas_divider_ratio", GAS_DIVIDER_RATIO)
                 if divider_ratio is None else divider_ratio)
        if code <= 0:
            return float("inf")
        vout_adc = (code / 1023.0) * 3.3
        vout = vout_adc / ratio
        if vout <= 0:
            return float("inf")
        return load_resistance * (5.0 - vout) / vout

    def _read_gas(self, channel: int, r0: float, coeff_a: float, coeff_b: float) -> float:
        """Averaged gas concentration in ppm on one ADC channel."""
        codes = []
        for _ in range(GAS_SAMPLE_COUNT):
            codes.append(self._read_adc(channel))
            time.sleep(GAS_SAMPLE_INTERVAL)
        mean_code = sum(codes) / len(codes)
        rs = self._adc_to_resistance(mean_code)
        if rs == float("inf") or r0 <= 0:
            return 0.0
        return round(mq_ppm_from_ratio(rs / r0, coeff_a, coeff_b), 3)

    def _read_hx711(self, samples: int = 10) -> float:
        """Read the load cell and return grams.

        The HX711 has no standard bus; it is bit-banged. DOUT goes low when a
        conversion is ready, then 24 clock pulses shift out the result MSB
        first as a two's-complement value, and a 25th pulse selects channel A
        at gain 128 for the next conversion.
        """
        GPIO = self._gpio
        readings = []
        for _ in range(samples):
            timeout = time.time() + 1.0
            while GPIO.input(PIN_HX711_DOUT) == 1:
                if time.time() > timeout:
                    raise TimeoutError("HX711 did not signal data ready within 1 s")
                time.sleep(0.001)

            value = 0
            for _ in range(24):
                GPIO.output(PIN_HX711_SCK, True)
                value = (value << 1) | GPIO.input(PIN_HX711_DOUT)
                GPIO.output(PIN_HX711_SCK, False)
            GPIO.output(PIN_HX711_SCK, True)
            GPIO.output(PIN_HX711_SCK, False)

            if value & 0x800000:  # sign-extend the 24-bit two's-complement value
                value -= 0x1000000
            readings.append(value)

        # Median rather than mean: a single mains-borne spike would drag a mean
        # by tens of grams, and this channel is otherwise very quiet.
        readings.sort()
        median = readings[len(readings) // 2]
        return round((median - self.load_cell_offset) / self.load_cell_scale, 1)

    def _read_dht22(self) -> tuple[float, float]:
        """Temperature in degC and relative humidity in percent.

        The DHT22 fails a read fairly often -- its single-wire timing is tight
        and Linux is not a real-time OS -- so a few retries are normal and not
        a sign of a broken sensor.
        """
        last_error: Exception | None = None
        for _ in range(5):
            try:
                temp = self._dht.temperature
                humidity = self._dht.humidity
                if temp is not None and humidity is not None:
                    return float(temp), float(humidity)
            except RuntimeError as exc:  # the library raises these routinely
                last_error = exc
            time.sleep(2.0)
        raise IOError(f"DHT22 gave no valid reading in 5 attempts: {last_error}")

    # -- SensorBackend -----------------------------------------------------

    def _heaters(self, on: bool) -> None:
        self._gpio.output(PIN_HEATER_GATE, bool(on))

    def warm_up(self) -> None:
        """Power the MQ heaters and let them settle before reading."""
        self._heaters(True)
        time.sleep(GAS_WARMUP_SECONDS)

    def read_all(self) -> list[SensorSample]:
        """One cycle: heaters on, warm up, read every slot, heaters off."""
        try:
            self.warm_up()
            return [self.read_slot(i) for i in range(self.slot_count)]
        finally:
            self._heaters(False)

    def set_roi(self, slot_id: int, box: tuple[int, int, int, int]) -> None:
        """Record the crop box for a slot, as (left, top, right, bottom)."""
        self._roi[slot_id] = box

    def capture_image(self, slot_id: int) -> str | None:
        """Photograph the shelf under the LED strip and crop to one slot.

        Returns None without touching the camera when the user has switched it
        off; the inference service then falls back to the sensor-only model.

        The LED is switched on only for the exposure. Leaving it lit would
        both waste power and warm the enclosure, which would bias the very
        temperature reading the system depends on.
        """
        if not self.camera_enabled:
            return None
        from PIL import Image  # imported here so the module loads without PIL

        GPIO = self._gpio
        GPIO.output(PIN_LED_GATE, True)
        time.sleep(0.25)  # let the strip and the sensor's AGC settle
        try:
            frame = self._camera.capture_array()
        finally:
            GPIO.output(PIN_LED_GATE, False)

        image = Image.fromarray(frame)
        if slot_id in self._roi:
            image = image.crop(self._roi[slot_id])
        image = image.resize((224, 224), Image.BILINEAR)

        path = self.image_dir / f"slot{slot_id}_{int(time.time())}.jpg"
        image.save(path, quality=90)
        return str(path)

    def read_slot(self, slot_id: int) -> SensorSample:
        ethanol = self._read_gas(ADC_CHANNEL_MQ3, self.r0_mq3,
                                 MQ3_ETHANOL_A, MQ3_ETHANOL_B)
        ammonia = self._read_gas(ADC_CHANNEL_MQ135, self.r0_mq135,
                                 MQ135_AMMONIA_A, MQ135_AMMONIA_B)
        time.sleep(WEIGHT_SETTLE_DELAY)
        mass = self._read_hx711()
        temperature, humidity = self._read_dht22()

        return SensorSample(
            slot_id=slot_id,
            timestamp=utcnow(),
            temperature_c=round(temperature, 1),
            humidity_pct=round(humidity, 1),
            ethanol_ppm=ethanol,
            ammonia_ppm=ammonia,
            mass_g=mass,
            mass_delta_g=0.0,  # filled in by the acquisition layer from history
            image_path=self.capture_image(slot_id),
        )

    def close(self) -> None:
        try:
            self._camera.stop()
            self._spi.close()
            self._gpio.cleanup()
        except Exception:  # pragma: no cover - best effort on shutdown
            pass
