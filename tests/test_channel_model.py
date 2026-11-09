"""Tests for the channel objects of a single-ended input."""

import pytest
from conftest import fake, recording

from scietex.hal.adc import MCP3208


def test_max_code_and_index() -> None:
    """A channel exposes the 12-bit full scale and its own index."""
    adc = MCP3208(transport=fake(0))
    channel = adc.channel(3)
    assert channel.max_code == 4095
    assert channel.index == 3


def test_value_issues_one_three_byte_transfer() -> None:
    """Reading a code is exactly one three-word request."""
    transport = recording(fake(2048))
    adc = MCP3208(transport=transport)
    assert adc.channel(5).value == 2048
    assert len(transport.requests) == 1
    assert transport.requests[0] == [0x07, 0x40, 0x00]


def test_voltage_is_none_without_v_ref() -> None:
    """No reference means no scaling, and no bus traffic either."""
    transport = recording(fake(2048))
    adc = MCP3208(transport=transport)
    assert adc.channel(0).voltage is None
    assert transport.requests == []


def test_voltage_scales_the_code() -> None:
    """Voltage is code * v_ref / 4096."""
    adc = MCP3208(transport=fake(4095), v_ref=3.3)
    assert adc.channel(0).voltage == pytest.approx(4095 * 3.3 / 4096)


def test_setting_v_ref_later_changes_voltage_not_code() -> None:
    """v_ref only rescales; the raw code stays the device's answer."""
    transport = recording(fake(2048, 2048, 2048))
    adc = MCP3208(transport=transport)
    channel = adc.channel(0)
    assert channel.value == 2048
    assert channel.voltage is None
    adc.v_ref = 5.0
    assert channel.voltage == pytest.approx(2048 * 5.0 / 4096)
    assert channel.value == 2048
    assert len(transport.requests) == 3


def test_value_is_a_live_read() -> None:
    """Two reads are two transfers, never a cached code."""
    transport = recording(fake(1, 2))
    adc = MCP3208(transport=transport)
    channel = adc.channel(0)
    assert channel.value == 1
    assert channel.value == 2
    assert len(transport.requests) == 2
