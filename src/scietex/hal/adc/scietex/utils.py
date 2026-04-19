"""Scietex-related utilities."""


def baudrate_check(baudrate: int) -> int:
    """Adjust baudrate to the supported values."""
    if baudrate <= 9600:
        return 9600
    if baudrate <= 14400:
        return 14400
    if baudrate <= 19200:
        return 19200
    if baudrate <= 38400:
        return 38400
    if baudrate <= 57600:
        return 57600
    return 115200


def address_check(address: int) -> int:
    """Adjust address to the supported values."""
    return max(1, min(address, 247))
