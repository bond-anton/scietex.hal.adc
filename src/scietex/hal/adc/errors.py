"""Errors raised by the ADC package."""


class ADCFrameError(ValueError):
    """Raised when the device returns a malformed SPI frame."""
