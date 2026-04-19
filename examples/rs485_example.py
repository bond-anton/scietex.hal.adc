"""Example of RS485 gated FTM operation."""

import asyncio

from scietex.hal.serial import ModbusSerialConnectionConfig
from scietex.hal.serial.utilities.serial_port_finder import find_rs485

from scietex.hal.adc.base.rs485 import RS485ADC
from scietex.hal.adc.scietex import VdpADC


async def main(
    adc_cls: type[RS485ADC],
    modbus_config: ModbusSerialConnectionConfig,
    address: int,
):
    """Main coroutine."""
    adc = adc_cls(1, modbus_config, address=address, label="Scietex ADC")
    orig_baudrate = await adc.get_baudrate()
    orig_address = await adc.get_address()
    print(f"BR: {orig_baudrate}, ADDR: {orig_address}")
    parameters = await adc.read_parameters()
    print(f"Parameters: {parameters}")
    data = await adc.read_data()
    print(f"Parameters: {data}")


if __name__ == "__main__":
    adc_models = [VdpADC]
    rs485_ports = find_rs485()
    if rs485_ports:
        connection_config = ModbusSerialConnectionConfig(
            port=rs485_ports[0], baudrate=19200, timeout=0.5
        )
        asyncio.run(main(adc_models[0], connection_config, address=1))
    else:
        print("No RS485 ports found.")
