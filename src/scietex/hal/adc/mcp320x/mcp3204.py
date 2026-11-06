"""MCP3204 device class."""

from .mcp320x import MCP320x


class MCP3204(MCP320x):
    """
    MCP3204: 4-channel 12-bit SPI analog-to-digital converter.

    Provides 4 single-ended inputs and 2 pseudo-differential pairs. The part
    has one differential channel-select bit (D2) that is a don't-care, so only
    single-ended channels 0..3 and the two pairs are exposed.
    """

    _CHANNELS = 4
    _PAIRS = 2
