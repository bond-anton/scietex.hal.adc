"""ADC abstract interface."""

from abc import ABC, abstractmethod

from .data import ADCError, ADCParameters, VoltageTuple


class ADC(ABC):
    """ADC interface class."""

    channels_number: int = 1

    error_codes: dict[int, ADCError] = {0: ADCError(code=0, message="No error")}
    error_codes_com: dict[int, ADCError] = {0: ADCError(code=0, message="No error")}

    # Error processing methods
    @abstractmethod
    async def get_error_code(self, comm: bool = False) -> int:
        """Read error code from the device"""

    def parse_error_code(self, code: int, comm: bool = False) -> ADCError:
        """Parse error code from the device"""
        if comm:
            if code in self.error_codes_com:
                return self.error_codes_com[code]
        else:
            if code in self.error_codes:
                return self.error_codes[code]
        return ADCError(code=code, message="Unknown error")

    @abstractmethod
    async def clear_error(self, comm: bool = False) -> int:
        """Clear error from the device."""

    # Device information methods
    @abstractmethod
    async def get_vendor(self) -> str:
        """Get device vendor name."""

    @abstractmethod
    async def get_product_name(self) -> str:
        """Get device product name."""

    @abstractmethod
    async def get_serial_number(self) -> str:
        """Get device serial number."""

    @abstractmethod
    async def get_version(self) -> str:
        """get device firmware version."""

    # ADC measurement setup

    # @abstractmethod
    # async def get_mcu_frequency(self) -> int:
    #     """GET MCU frequency."""

    # @abstractmethod
    # async def get_gate_time(self) -> float:
    #     """Get gate time in ms"""

    # @abstractmethod
    # async def set_gate_time(self, gate_time_ms: float) -> float:
    #     """Set gate time in ms"""

    # @abstractmethod
    # async def get_averaging(self) -> int:
    #     """Get averaging window"""

    # @abstractmethod
    # async def set_averaging(self, averaging_window: int) -> int:
    #     """Set averaging window."""

    # Voltage measurement methods

    @abstractmethod
    async def get_voltage(self) -> VoltageTuple:
        """Get all channels voltages."""

    @abstractmethod
    async def get_channel_voltage(self, channel: int) -> float | None:
        """Get voltage value for a specific channel."""

    # Read ADC parameters in single call

    @abstractmethod
    async def read_parameters(self) -> ADCParameters:
        """Read ADC Parameters"""
