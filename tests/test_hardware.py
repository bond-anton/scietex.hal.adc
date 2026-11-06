"""Hardware smoke test; opt in with RUN_HARDWARE_TESTS=1."""

import os

import pytest

from scietex.hal.adc import MCP3208

pytestmark = [
    pytest.mark.skipif(
        os.environ.get("RUN_HARDWARE_TESTS") != "1",
        reason="hardware tests are opt-in; set RUN_HARDWARE_TESTS=1",
    ),
    pytest.mark.skipif(
        not os.path.exists("/dev/spidev0.0"),
        reason="no SPI device node at /dev/spidev0.0",
    ),
]


def test_mcp3208_on_spidev0_0_reads_eight_codes() -> None:
    """A wired MCP3208 answers all eight single-ended channels."""
    adc = MCP3208(device=0, v_ref=3.3)
    try:
        codes = adc.read_all()
    finally:
        adc.close()
    assert len(codes) == 8
    assert all(0 <= code <= 4095 for code in codes)
