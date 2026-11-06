"""MCP3208 device class."""

from .mcp320x import MCP320x


class MCP3208(MCP320x):
    """
    MCP3208: 8-channel 12-bit SPI analog-to-digital converter.

    Provides 8 single-ended inputs and 4 pseudo-differential pairs.
    """

    _CHANNELS = 8
    _PAIRS = 4
