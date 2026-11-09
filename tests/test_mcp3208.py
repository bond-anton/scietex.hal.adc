"""Geometry and reads of the MCP3208."""

import pytest
from conftest import fake

from scietex.hal.adc import MCP3208


def test_geometry() -> None:
    """The part has eight single-ended inputs and four pseudo-differential pairs."""
    adc = MCP3208(transport=fake())
    assert [channel.index for channel in adc.channels] == list(range(8))
    assert [channel.pair for channel in adc.differential] == list(range(4))


def test_channel_tuples_are_immutable() -> None:
    """Both collections are tuples, not lists."""
    adc = MCP3208(transport=fake())
    assert isinstance(adc.channels, tuple)
    assert isinstance(adc.differential, tuple)
    with pytest.raises(TypeError):
        adc.channels[0] = adc.channels[1]  # type: ignore[index]


@pytest.mark.parametrize("index", [-1, 8, 9])
def test_channel_outside_the_geometry_raises(index: int) -> None:
    """Only channels 0..7 exist."""
    adc = MCP3208(transport=fake())
    with pytest.raises(IndexError):
        adc.channel(index)


@pytest.mark.parametrize("pair", [-1, 4, 5])
def test_differential_pair_outside_the_geometry_raises(pair: int) -> None:
    """Only pairs 0..3 exist."""
    adc = MCP3208(transport=fake())
    with pytest.raises(IndexError):
        adc.differential_channel(pair)


def test_read_all_reads_every_channel_in_order() -> None:
    """read_all returns one code per input, in index order."""
    adc = MCP3208(transport=fake(1, 2, 3, 4, 5, 6, 7, 8))
    assert adc.read_all() == (1, 2, 3, 4, 5, 6, 7, 8)
    assert adc.transport.calls == [
        [0x06, 0x00, 0x00],
        [0x06, 0x40, 0x00],
        [0x06, 0x80, 0x00],
        [0x06, 0xC0, 0x00],
        [0x07, 0x00, 0x00],
        [0x07, 0x40, 0x00],
        [0x07, 0x80, 0x00],
        [0x07, 0xC0, 0x00],
    ]


def test_read_differential_reads_every_pair_in_order() -> None:
    """read_differential returns one code per pair, in pair order."""
    adc = MCP3208(transport=fake(100, 200, 300, 400))
    assert adc.read_differential() == (100, 200, 300, 400)
    assert adc.transport.calls == [
        [0x04, 0x00, 0x00],
        [0x04, 0x80, 0x00],
        [0x05, 0x00, 0x00],
        [0x05, 0x80, 0x00],
    ]
