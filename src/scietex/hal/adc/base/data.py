"""Data models for the ADC."""

# from enum import Enum

import msgspec

# class OutCTRLMode(Enum):
#     """Modes of the control output."""

#     HIGH = 1
#     LOW = 2
#     MANUAL = 3
#     DISABLED = 4


# class PwmCTRLMode(Enum):
#     """Modes of the PWM output."""

#     ABSOLUTE = 1
#     RELATIVE = 2
#     MANUAL = 3
#     DISABLED = 4


class ADCError(msgspec.Struct, frozen=True):
    """Model of an ADC error with code and message."""

    code: int
    message: str = "Unknown error"

    def __str__(self) -> str:
        return f"ADCError(code={self.code}, message='{self.message}')"


VoltageTuple = tuple[float | None, ...]


class ADCParameters(msgspec.Struct, frozen=True):
    """ADC parameters schema."""

    connected: bool = False  # ADC connection status
    channels_number: int | None = None  # Number of ADC channels
    voltage: VoltageTuple | None = None  # Channel voltages

    def __str__(self) -> str:
        """Human-readable representation."""
        if self.voltage is None:
            voltage_str = "None"
        elif not self.voltage:
            voltage_str = "[]"
        else:
            voltage_strs = [f"{v:.2f} V" if v is not None else "N/A" for v in self.voltage]
            voltage_str = f"[{', '.join(voltage_strs)}]"

        return (
            f"ADCParameters("
            f"channels_number={self.channels_number}, "
            f"voltage={voltage_str}, "
            f"connected={self.connected})"
        )

    def __repr__(self) -> str:
        """Official string representation (used in debugging)."""
        return (
            f"ADCParameters("
            f"connected={self.connected!r}, "
            f"channels_number={self.channels_number!r}, "
            f"voltage={self.voltage!r})"
        )
