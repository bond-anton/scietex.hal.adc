"""Error types raised by the package."""

from collections.abc import Sequence

import pytest
from conftest import fake
from scietex.hal.spi import TransportError

import scietex.hal.adc as adc_package
from scietex.hal.adc import MCP3208, ADCFrameError


class _FixedFrameTransport:
    """Transport that answers every request with the same frame."""

    def __init__(self, response: list[object]) -> None:
        self._response = response
        self.closed = False

    def transfer(self, tx: Sequence[int]) -> list[int]:
        """Return the scripted frame regardless of the request length."""
        return list(self._response)  # type: ignore[return-value]

    def close(self) -> None:
        """Mark the stand-in closed."""
        self.closed = True


def test_transport_error_propagates() -> None:
    """A bus failure never turns into a frame error."""
    adc = MCP3208(transport=fake())
    with pytest.raises(TransportError) as excinfo:
        _ = adc.channel(0).value
    assert not isinstance(excinfo.value, ADCFrameError)


def test_frame_error_is_a_value_error() -> None:
    """A malformed frame is a ValueError, unrelated to transport failures."""
    assert issubclass(ADCFrameError, ValueError)
    assert not issubclass(ADCFrameError, TransportError)


def test_frame_error_is_exported_from_the_package_root() -> None:
    """Callers can catch the error without reaching into a submodule."""
    assert adc_package.ADCFrameError is ADCFrameError
    assert "ADCFrameError" in adc_package.__all__


@pytest.mark.parametrize("response", [[0, 0], [0, 0, 0, 0]])
def test_malformed_response_length_raises_frame_error(response: list[int]) -> None:
    """A device answer that is not three words is a frame error."""
    adc = MCP3208(transport=_FixedFrameTransport(response))
    with pytest.raises(ADCFrameError) as excinfo:
        _ = adc.channel(0).value
    assert repr(response) in str(excinfo.value)


@pytest.mark.parametrize("response", [[0, 0, -1], [0, 0, 300]])
def test_malformed_response_word_raises_frame_error(response: list[int]) -> None:
    """A word outside 0..255 is a frame error naming the frame."""
    adc = MCP3208(transport=_FixedFrameTransport(response))
    with pytest.raises(ADCFrameError) as excinfo:
        _ = adc.channel(0).value
    assert repr(response) in str(excinfo.value)
