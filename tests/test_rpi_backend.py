"""Tests for the Raspberry Pi driver.

Its readings cannot be tested off a Pi, so these check the parts that can be:
that it refuses to load without the hardware libraries instead of failing
obscurely, that its pin map is internally consistent, and that its pure
conversion helpers are right.
"""

from __future__ import annotations

import inspect

import pytest

from freshkeeper.hardware import rpi_backend as rpi
from freshkeeper.hardware.base import SensorBackend


def test_refuses_to_initialise_without_pi_libraries():
    with pytest.raises(rpi.HardwareUnavailableError, match="Raspberry Pi"):
        rpi.RaspberryPiSensorBackend()


def test_conforms_to_the_backend_interface():
    assert issubclass(rpi.RaspberryPiSensorBackend, SensorBackend)
    for name in ("warm_up", "read_slot", "capture_image"):
        assert callable(getattr(rpi.RaspberryPiSensorBackend, name))
        assert not getattr(getattr(rpi.RaspberryPiSensorBackend, name),
                           "__isabstractmethod__", False)


def test_gpio_pins_are_distinct():
    pins = [rpi.PIN_DHT22, rpi.PIN_HX711_DOUT, rpi.PIN_HX711_SCK, rpi.PIN_LED_GATE]
    assert len(set(pins)) == len(pins), "two peripherals share a pin"


def test_pins_avoid_the_spi_bus():
    # SPI0 uses GPIO 7-11; assigning any of them elsewhere breaks the ADC.
    for pin in (rpi.PIN_DHT22, rpi.PIN_HX711_DOUT, rpi.PIN_HX711_SCK, rpi.PIN_LED_GATE):
        assert pin not in range(7, 12), f"GPIO {pin} collides with SPI0"


def test_adc_channels_are_distinct_and_in_range():
    assert rpi.ADC_CHANNEL_MQ135 != rpi.ADC_CHANNEL_MQ3
    assert all(0 <= c <= 7 for c in (rpi.ADC_CHANNEL_MQ135, rpi.ADC_CHANNEL_MQ3))


def test_weight_read_is_separated_from_the_gas_heaters():
    assert rpi.WEIGHT_SETTLE_DELAY > 0, (
        "gas heaters and the HX711 share the 5 V rail; reading them together "
        "couples switching noise into the weight channel"
    )


def test_adc_resistance_conversion():
    backend = rpi.RaspberryPiSensorBackend.__new__(rpi.RaspberryPiSensorBackend)
    assert backend._adc_to_resistance(0) == float("inf")
    mid = backend._adc_to_resistance(512, load_resistance=10_000.0)
    assert 0 < mid < 1e6
    # More gas lowers Rs, which raises the measured voltage, which raises the code.
    assert (backend._adc_to_resistance(800, 10_000.0)
            < backend._adc_to_resistance(300, 10_000.0))


def test_adc_read_rejects_invalid_channels():
    backend = rpi.RaspberryPiSensorBackend.__new__(rpi.RaspberryPiSensorBackend)
    with pytest.raises(ValueError, match="channels 0-7"):
        backend._read_adc(9)


def test_module_documents_that_it_is_unvalidated():
    # The thesis must not imply these readings were checked against instruments.
    assert "not been validated" in inspect.getdoc(rpi)


def test_heater_gate_pin_is_distinct_and_off_spi():
    pins = [rpi.PIN_DHT22, rpi.PIN_HX711_DOUT, rpi.PIN_HX711_SCK,
            rpi.PIN_LED_GATE, rpi.PIN_HEATER_GATE]
    assert len(set(pins)) == len(pins)
    assert rpi.PIN_HEATER_GATE not in range(7, 12)


def test_adc_conversion_undoes_the_input_divider():
    # The MCP3008 sees the sensor voltage scaled by the divider. Ignoring that
    # inflates every resistance by the same ratio; the earlier driver did.
    backend = rpi.RaspberryPiSensorBackend.__new__(rpi.RaspberryPiSensorBackend)
    backend.gas_divider_ratio = rpi.GAS_DIVIDER_RATIO
    undivided = backend._adc_to_resistance(512, 10_000.0, divider_ratio=1.0)
    divided = backend._adc_to_resistance(512, 10_000.0)
    assert divided < undivided
    # A full-scale code corresponds to the sensor's 5 V rail after un-dividing.
    assert backend._adc_to_resistance(1023, 10_000.0) == pytest.approx(0.0, abs=1.0)


def test_read_all_switches_heaters_off_even_if_a_read_fails(monkeypatch):
    monkeypatch.setattr(rpi, "GAS_WARMUP_SECONDS", 0.0)

    class FakeGPIO:
        def __init__(self): self.states = {}
        def output(self, pin, value): self.states[pin] = bool(value)

    backend = rpi.RaspberryPiSensorBackend.__new__(rpi.RaspberryPiSensorBackend)
    backend._gpio = FakeGPIO()
    backend.slot_count = 1
    backend.camera_enabled = True
    def boom(slot_id): raise IOError("sensor fault")
    backend.read_slot = boom
    with pytest.raises(IOError):
        backend.read_all()
    assert backend._gpio.states[rpi.PIN_HEATER_GATE] is False
