# scietex.hal.adc

The `scietex.hal.adc` package is a Python library for interfacing with ADC.
It provides an abstract class `ADC`, and a base class for ADCs with RS485 communication
interface, which in its turn inherits `scietex.hal.serial.RS485Client`.
The concrete implementation for the ADC manufactured by Scietex is provided.


## License

This project is licensed under the **MIT License** - see the LICENSE file for details.
