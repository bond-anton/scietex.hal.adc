"""Scietex VdpADC."""

import struct
from logging import Logger

from scietex.hal.serial import ModbusSerialConnectionConfig
from scietex.hal.serial.utilities.numeric import ByteOrder

from ..base.data import ADCParameters, VoltageTuple
from ..base.rs485 import RS485ADC

VOLTAGE_SCALE = 1
BYTEORDER = ByteOrder.LITTLE_ENDIAN


class VdpADC(RS485ADC):
    """Scietex Van der Pauw ADC RS485 driver."""

    def __init__(
        self,
        con_params: ModbusSerialConnectionConfig,
        address: int = 1,
        label: str = "Scietex Van der Pauw ADC",
        logger: Logger | None = None,
        chunk_size: int | None = 8,
        write_chunk_size: int | None = 8,
        **kwargs,
    ):

        con_params.framer = "RTU"
        super().__init__(
            channels_number=4,
            con_params=con_params,
            address=address,
            label=label,
            logger=logger,
            chunk_size=chunk_size,
            write_chunk_size=write_chunk_size,
            **kwargs,
        )

    async def get_vendor(self) -> str:
        response = await self.read_registers(0, 10, holding=False)
        if response is not None:
            # Each register is 16-bit, containing two ASCII bytes
            bytes_list = []
            for reg in response:
                bytes_list.append((reg >> 8) & 0xFF)  # high byte
                bytes_list.append(reg & 0xFF)  # low byte
            vendor_bytes = bytes(bytes_list)
            # Decode and strip null bytes
            return vendor_bytes.decode("ascii", errors="ignore").rstrip("\x00")
        return ""

    async def get_product_name(self) -> str:
        response = await self.read_registers(10, 20, holding=False)
        if response is not None:
            # Each register is 16-bit, containing two ASCII bytes
            bytes_list = []
            for reg in response:
                bytes_list.append((reg >> 8) & 0xFF)  # high byte
                bytes_list.append(reg & 0xFF)  # low byte
            product_bytes = bytes(bytes_list)
            # Decode and strip null bytes
            return product_bytes.decode("ascii", errors="ignore").rstrip("\x00")
        return ""

    async def get_version(self) -> str:
        response = await self.read_registers(30, 3, holding=False)
        if response is not None:
            return f"{response[0]:d}.{response[1]:d}.{response[2]:d}"
        return ""

    async def get_serial_number(self) -> str:
        response = await self.read_two_registers_int(10, holding=True, byteorder=BYTEORDER)
        if response is not None:
            return f"{response:d}"
        return ""

    async def get_channel_voltage(self, channel: int) -> float | None:
        ch_idx = max(0, min(channel, self.channels_number - 1))
        start_register = 36 + ch_idx * 2
        response = await self.read_two_registers_float(
            start_register, holding=False, factor=VOLTAGE_SCALE, byteorder=BYTEORDER
        )
        if response is not None:
            return float(response)
        return None

    async def get_voltage(self) -> VoltageTuple:
        response = await self.read_registers(36, self.channels_number * 2, holding=False)
        if response is not None and len(response) == self.channels_number * 2:
            voltage = tuple(
                struct.unpack(">f", struct.pack(">HH", a, b))[0]
                # float_from_int(combine_32bit(a, b, byteorder=BYTEORDER), VOLTAGE_SCALE)
                if a is not None and b is not None
                else None
                for a, b in zip(response[::2], response[1::2])
            )
            return voltage
        return (None,) * self.channels_number

    async def get_address(self) -> int:
        response = await self.read_register(0, holding=True)
        if response is not None:
            return response
        return 0

    async def set_address(self, address: int) -> int:
        new_address = max(1, min(address, 247))
        await self.write_register(0, new_address)
        self.address = new_address
        response = await self.get_address()
        if response is not None and response > 0:
            self.address = response
            return response
        return 0

    async def get_baudrate(self) -> int:
        response = await self.read_register(1, holding=True)
        if response is not None:
            if response == 0:
                return 9600
            elif response == 1:
                return 14400
            elif response == 2:
                return 19200
            elif response == 5:
                return 115200
        return 0

    async def set_baudrate(self, baudrate: int) -> int:
        if baudrate <= 9600:
            new_baudrate = 9600
            baudrate_code = 0
        elif baudrate <= 14400:
            new_baudrate = 14400
            baudrate_code = 1
        elif baudrate <= 19200:
            new_baudrate = 19200
            baudrate_code = 12
        else:
            new_baudrate = 115200
            baudrate_code = 5
        response = await self.write_register(1, baudrate_code)
        new_con_params = self.con_params
        new_con_params.baudrate = new_baudrate
        self.con_params = new_con_params
        if response is not None:
            return response
        response = await self.read_register(1, holding=True)
        if response is not None:
            return response
        return 0

    async def check_connection(self):
        vendor = await self.get_vendor()
        if vendor:
            return True
        return False

    async def read_parameters(self) -> ADCParameters:
        voltage = await self.get_voltage()
        parameters = ADCParameters(
            connected=True,
            channels_number=self.channels_number,
            voltage=voltage,
        )
        return parameters
