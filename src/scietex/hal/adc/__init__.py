"""Synchronous SPI analog-to-digital converters."""

from .adc import ADC
from .channel import ADCChannel, DifferentialChannel, SingleEndedChannel
from .errors import ADCFrameError
from .mcp320x import MCP3204, MCP3208
from .version import __version__

__all__ = [
    "__version__",
    "ADC",
    "ADCChannel",
    "DifferentialChannel",
    "SingleEndedChannel",
    "ADCFrameError",
    "MCP3204",
    "MCP3208",
]
