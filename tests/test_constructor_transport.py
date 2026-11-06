"""Constructor wiring, transport ownership, and lifecycle."""

import sys
import types
from unittest import mock

import pytest
import scietex.hal.spi.spidev_spi as spidev_spi
from conftest import fake, recording

from scietex.hal.adc import MCP3208

GPIOZERO_BACKEND = "scietex.hal.spi.gpiozero_spi"


class _RecordingGpiozeroTransport:
    """Stand-in for GpiozeroSpiTransport that records its keywords."""

    instances: list["_RecordingGpiozeroTransport"] = []

    def __init__(self, **spi_args: object) -> None:
        self.spi_args = spi_args
        self.closed = False
        _RecordingGpiozeroTransport.instances.append(self)

    def transfer(self, tx: list[int]) -> list[int]:
        """Answer with a zero frame of the request length."""
        return [0] * len(tx)

    def close(self) -> None:
        """Mark the stand-in closed."""
        self.closed = True


def _fake_gpiozero_module() -> types.ModuleType:
    """Build a stand-in for the gpiozero backend module."""
    module = types.ModuleType(GPIOZERO_BACKEND)
    module.GpiozeroSpiTransport = _RecordingGpiozeroTransport
    return module


def test_default_transport_is_spidev_bus0_device0() -> None:
    """No keywords open /dev/spidev0.0."""
    with mock.patch.object(spidev_spi, "SpiDevTransport") as constructor:
        adc = MCP3208()
    constructor.assert_called_once_with(bus=0, device=0)
    assert adc.transport is constructor.return_value


def test_explicit_device_zero_matches_the_default() -> None:
    """device=0 is the same chip select the default picks."""
    with mock.patch.object(spidev_spi, "SpiDevTransport") as constructor:
        MCP3208(device=0)
    constructor.assert_called_once_with(bus=0, device=0)


def test_port_and_device_select_the_spidev_bus() -> None:
    """port maps to the spidev bus number, device to the chip select."""
    with mock.patch.object(spidev_spi, "SpiDevTransport") as constructor:
        MCP3208(port=1, device=2)
    constructor.assert_called_once_with(bus=1, device=2)


def test_pin_keywords_select_the_gpiozero_transport() -> None:
    """Any pin keyword switches the constructor to the gpiozero backend."""
    _RecordingGpiozeroTransport.instances = []
    with mock.patch.dict(sys.modules, {GPIOZERO_BACKEND: _fake_gpiozero_module()}):
        adc = MCP3208(clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=8)
    transport = _RecordingGpiozeroTransport.instances[0]
    assert adc.transport is transport
    assert transport.spi_args == {
        "clock_pin": 11,
        "mosi_pin": 10,
        "miso_pin": 9,
        "select_pin": 8,
    }


@pytest.mark.parametrize(
    "keyword",
    [{"clock_pin": 11}, {"mosi_pin": 10}, {"miso_pin": 9}, {"select_pin": 8}],
)
def test_backend_keywords_with_a_transport_are_rejected(
    keyword: dict[str, int],
) -> None:
    """The pins configure a transport; they cannot accompany one."""
    name = next(iter(keyword))
    with pytest.raises(TypeError) as excinfo:
        MCP3208(transport=fake(0), **keyword)
    assert name in str(excinfo.value)


def test_non_transport_object_is_rejected() -> None:
    """An injected object must offer transfer() and close()."""
    with pytest.raises(TypeError):
        MCP3208(transport=object())


def test_missing_spidev_names_the_spi_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without spidev the constructor names the extra that provides it."""
    monkeypatch.setitem(sys.modules, "spidev", None)
    with pytest.raises(ImportError) as excinfo:
        MCP3208(device=0)
    assert "scietex.hal.spi[spi]" in str(excinfo.value)


def test_injected_transport_imports_no_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A supplied transport keeps both optional backends untouched."""
    monkeypatch.setitem(sys.modules, "spidev", None)
    monkeypatch.setitem(sys.modules, "gpiozero", None)
    adc = MCP3208(transport=fake(7))
    assert adc.channel(0).value == 7


@pytest.mark.parametrize("v_ref", [0, 0.0, -1, -0.5, float("nan"), float("inf")])
def test_v_ref_rejects_non_positive_values(v_ref: float) -> None:
    """A reference voltage must be a positive finite number."""
    with pytest.raises(ValueError):
        MCP3208(transport=fake(0), v_ref=v_ref)


@pytest.mark.parametrize("v_ref", ["3.3", True])
def test_v_ref_rejects_non_numbers(v_ref: object) -> None:
    """A reference voltage is a number, not a string or a flag."""
    with pytest.raises(TypeError):
        MCP3208(transport=fake(0), v_ref=v_ref)  # type: ignore[arg-type]


def test_label_accepts_str_and_none() -> None:
    """The label names the logger; None keeps the class name."""
    assert MCP3208(transport=fake(0), label="adc").label == "adc"
    assert MCP3208(transport=fake(0), label=None).label is None


@pytest.mark.parametrize("label", [1, 1.5, b"adc", ["adc"]])
def test_label_rejects_non_str(label: object) -> None:
    """A label is not coerced from another type."""
    with pytest.raises(TypeError):
        MCP3208(transport=fake(0), label=label)  # type: ignore[arg-type]


@pytest.mark.parametrize("label", ["", "   "])
def test_label_rejects_empty_text(label: str) -> None:
    """A blank label is a ValueError."""
    with pytest.raises(ValueError):
        MCP3208(transport=fake(0), label=label)


def test_built_transport_is_closed_when_a_later_step_fails() -> None:
    """The device releases a transport it built itself."""
    with (
        mock.patch.object(spidev_spi, "SpiDevTransport") as constructor,
        pytest.raises(ValueError),
    ):
        MCP3208(v_ref=0)
    constructor.return_value.close.assert_called_once()


def test_supplied_transport_is_left_open_when_a_later_step_fails() -> None:
    """A caller-supplied transport still belongs to the caller."""
    transport = fake(0)
    with pytest.raises(ValueError):
        MCP3208(transport=transport, v_ref=0)
    assert transport.closed is False


def test_close_delegates_to_the_transport_once() -> None:
    """close() is one transport close() call plus the device's own flag."""
    transport = recording(fake(0))
    adc = MCP3208(transport=transport)
    adc.close()
    assert transport.close_calls == 1
    assert transport.inner.closed is True
    assert adc.closed is True


def test_closed_reflects_the_transport_state() -> None:
    """A transport closed behind the device's back still reports closed."""
    transport = fake(0)
    adc = MCP3208(transport=transport)
    assert adc.closed is False
    transport.close()
    assert adc.closed is True


def test_close_closes_a_supplied_transport() -> None:
    """Device close() owns the bus handle even when the transport was injected."""
    transport = fake(0)
    MCP3208(transport=transport).close()
    assert transport.closed is True


def test_context_manager_closes_on_exit() -> None:
    """Leaving the with block closes the transport."""
    transport = fake(0)
    with MCP3208(transport=transport) as adc:
        assert adc.closed is False
    assert transport.closed is True
