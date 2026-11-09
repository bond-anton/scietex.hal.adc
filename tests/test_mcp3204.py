"""Geometry and reads of the MCP3204."""

import pytest
from conftest import fake

from scietex.hal.adc import MCP3204


def test_geometry() -> None:
    """The part has four single-ended inputs and two pseudo-differential pairs."""
    adc = MCP3204(transport=fake())
    assert [channel.index for channel in adc.channels] == [0, 1, 2, 3]
    assert [channel.pair for channel in adc.differential] == [0, 1]


def test_channel_tuples_are_immutable() -> None:
    """Both collections are tuples, not lists."""
    adc = MCP3204(transport=fake())
    assert isinstance(adc.channels, tuple)
    assert isinstance(adc.differential, tuple)
    with pytest.raises(TypeError):
        adc.channels[0] = adc.channels[1]  # type: ignore[index]


@pytest.mark.parametrize("index", [-1, 4, 5])
def test_channel_outside_the_geometry_raises(index: int) -> None:
    """Only channels 0..3 exist."""
    adc = MCP3204(transport=fake())
    with pytest.raises(IndexError):
        adc.channel(index)


@pytest.mark.parametrize("pair", [-1, 2, 3])
def test_differential_pair_outside_the_geometry_raises(pair: int) -> None:
    """Only pairs 0..1 exist."""
    adc = MCP3204(transport=fake())
    with pytest.raises(IndexError):
        adc.differential_channel(pair)


def test_read_all_reads_every_channel_in_order() -> None:
    """read_all returns one code per input, in index order."""
    adc = MCP3204(transport=fake(10, 20, 30, 40))
    assert adc.read_all() == (10, 20, 30, 40)
    assert adc.transport.calls == [
        [0x06, 0x00, 0x00],
        [0x06, 0x40, 0x00],
        [0x06, 0x80, 0x00],
        [0x06, 0xC0, 0x00],
    ]


def test_read_differential_reads_every_pair_in_order() -> None:
    """read_differential returns one code per pair, in pair order."""
    adc = MCP3204(transport=fake(100, 200))
    assert adc.read_differential() == (100, 200)
    assert adc.transport.calls == [
        [0x04, 0x00, 0x00],
        [0x04, 0x80, 0x00],
    ]
