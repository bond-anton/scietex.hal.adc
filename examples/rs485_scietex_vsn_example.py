"""Example of RS485 gated FTM operation."""

import asyncio
import logging

from scietex.hal.serial import (
    ModbusSerialConnectionConfig,
    SerialConnectionConfig,
    VirtualSerialNetwork,
)
from scietex.hal.serial.utilities.serial_port_finder import find_rs485

from scietex.hal.adc.scietex import VdpADC


async def main(
    modbus_config: ModbusSerialConnectionConfig,
    address: int,
):
    """Main coroutine."""
    adc = VdpADC(modbus_config, address=address, label="Scietex ADC")
    orig_baudrate = await adc.get_baudrate()
    orig_address = await adc.get_address()
    print(f"BR: {orig_baudrate}, ADDR: {orig_address}")

    parameters = await adc.read_parameters()
    print(f"Parameters: {parameters}")
    data = await adc.read_data()
    print(f"Parameters: {data}")


if __name__ == "__main__":
    logger = logging.getLogger()
    vsn = VirtualSerialNetwork(
        virtual_ports_num=0, external_ports=None, loopback=False, logger=logger
    )
    vsn.start()
    rs485_ports = find_rs485()
    if rs485_ports:
        vsn.add([SerialConnectionConfig(port=rs485_ports[0], baudrate=19200, timeout=1.5)])
    else:
        print("No RS485 ports found.")
    vp = vsn.create(1)
    print(vp)
    connection_config = ModbusSerialConnectionConfig(port=vp[0], baudrate=19200, timeout=1)
    asyncio.run(main(connection_config, address=1))

    vsn.stop()
