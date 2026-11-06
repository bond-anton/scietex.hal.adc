"""Tests for the pseudo-differential pair semantics."""

import pytest
from conftest import fake

from scietex.hal.adc import MCP3208


@pytest.mark.parametrize(
    ("pair", "plus", "minus"),
    [(0, 0, 1), (1, 2, 3), (2, 4, 5), (3, 6, 7)],
)
def test_pair_mapping(pair: int, plus: int, minus: int) -> None:
    """Pair n measures input 2n against input 2n+1."""
    channel = MCP3208(transport=fake()).differential_channel(pair)
    assert channel.pair == pair
    assert channel.index == pair
    assert channel.plus == plus
    assert channel.minus == minus


def test_value_is_unsigned_and_clamps_at_zero() -> None:
    """A negative input difference reads 000h, the top of the range reads FFFh."""
    adc = MCP3208(transport=fake(0x000, 0xFFF))
    channel = adc.differential_channel(0)
    assert channel.value == 0
    assert channel.value == 4095


def test_value_never_leaves_the_code_range() -> None:
    """Every code the pair reports fits the 12-bit, unipolar result."""
    adc = MCP3208(transport=fake(0x000, 0x7FF, 0xFFF), v_ref=3.3)
    channel = adc.differential_channel(0)
    codes = [channel.value for _ in range(3)]
    assert codes == [0, 0x7FF, 0xFFF]
    assert all(0 <= code <= channel.max_code for code in codes)


@pytest.mark.parametrize("pair", range(4))
def test_request_selects_the_pair(pair: int) -> None:
    """The request byte is 0x80 | (2 * pair << 3), polarity bit clear."""
    transport = fake(0)
    adc = MCP3208(transport=transport)
    _ = adc.differential_channel(pair).value
    assert transport.calls == [[0x80 | (2 * pair << 3), 0x00, 0x00]]
