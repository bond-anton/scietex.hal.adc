"""Lock-in amplifier with RS485 communication interface."""

from logging import Logger
from typing import Any

from pymodbus.framer import FramerBase
from pymodbus.pdu import DecodePDU, ModbusPDU
from scietex.hal.serial import (
    ModbusSerialConnectionConfig,
    RS485Client,
    SerialConnectionConfig,
)

from ...version import __version__
from .. import ADC
from ..data import ADCParameters, VoltageTuple


class RS485ADC(ADC, RS485Client):
    """ADC with RS485 communication interface."""

    def __init__(
        self,
        channels_number: int,
        con_params: SerialConnectionConfig | ModbusSerialConnectionConfig,
        address: int = 1,
        label: str = "RS485 ADC",
        custom_framer: type[FramerBase] | None = None,
        custom_decoder: type[DecodePDU] | None = None,
        custom_response: list[type[ModbusPDU]] | None = None,
        chunk_size: int | None = None,
        write_chunk_size: int | None = None,
        logger: Logger | None = None,
        **kwargs,
    ):
        RS485Client.__init__(
            self,
            con_params=con_params,
            address=address,
            custom_framer=custom_framer,
            custom_decoder=custom_decoder,
            custom_response=custom_response,
            chunk_size=chunk_size,
            write_chunk_size=write_chunk_size,
            logger=logger,
        )
        self.channels_number = channels_number

    # Error processing methods

    async def get_error_code(self, comm: bool = False) -> int:
        """Read error code from the ADC."""
        code = 0
        if comm:
            self.logger.debug("%s: Communication error code %d.", self.label, code)
        else:
            self.logger.debug("%s: Error code %d.", self.label, code)
        return code

    async def clear_error(self, comm: bool = False) -> int:
        """Clear error from the ADC."""
        if comm:
            self.logger.debug("%s: Clear communication error.", self.label)
        else:
            self.logger.debug("%s: Clear error.", self.label)
        return await self.get_error_code()

    # Device information methods

    async def get_vendor(self) -> str:
        """Get ADC vendor name."""
        vendor: str = "n/d"
        self.logger.debug("%s vendor: %s", self.label, vendor)
        return vendor

    async def get_product_name(self) -> str:
        """Get ADC product name."""
        self.logger.debug("%s prod. name: %s", self.label, self.label)
        return self.label

    async def get_serial_number(self) -> str:
        """Get ADC serial number."""
        sn = "n/d"
        self.logger.debug("%s SN: %s", self.label, sn)
        return sn

    async def get_version(self) -> str:
        """Get ADC firmware version."""
        self.logger.debug("%s version: %s.", self.label, __version__)
        return __version__

    # Voltage measurement methods

    async def get_voltage(self) -> VoltageTuple:
        """Get all channels voltages."""
        self.logger.debug("%s: get_voltage call", self.label)
        voltage: VoltageTuple = (None,) * self.channels_number
        return voltage

    async def get_channel_voltage(self, channel: int) -> float | None:
        """Get X channel voltage value."""
        self.logger.debug("%s: get_channel_voltage[%d] call", self.label, channel)
        return None

    # RS485 address and baudrate

    async def get_address(self) -> int:
        """Get RS-485 address."""
        self.logger.debug("%s: get_address call", self.label)
        return 1

    async def set_address(self, address: int) -> int:
        """Set RS-485 address."""
        self.logger.debug("%s: set_address(%d) call", self.label, address)
        return await self.get_address()

    async def get_baudrate(self) -> int:
        """Get RS-485 baudrate value."""
        self.logger.debug("%s: get_baudrate call", self.label)
        return 9600

    async def set_baudrate(self, baudrate: int) -> int:
        """Set RS-485 baudrate."""
        self.logger.debug("%s: set_baudrate(%d) call", self.label, baudrate)
        return await self.get_baudrate()

    async def check_connection(self) -> bool:
        """Set RS-485 baudrate."""
        self.logger.debug("%s: check_connection call", self.label)
        return False

    # Read Lock-in state in a single request

    async def read_parameters(self) -> ADCParameters:
        """Read ADC Parameters."""
        self.logger.debug("%s: read_parameters call", self.label)
        voltage: VoltageTuple = await self.get_voltage()
        connected: bool = await self.check_connection()
        parameters = ADCParameters(
            channels_number=self.channels_number,
            voltage=voltage,
            connected=connected,
        )
        return parameters

    async def read_data(self) -> dict[str, int | float | list[int | float]]:
        """Read Lockin data in a single request."""
        parameters = await self.read_parameters()
        return {f: getattr(parameters, f) for f in parameters.__struct_fields__}

    async def process_message(self, message: dict[str, Any]) -> None:
        await super().process_message(message)
