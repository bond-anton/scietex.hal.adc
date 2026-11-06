# scietex.hal.adc

Synchronous SPI analog-to-digital converters: the Microchip MCP3204 and
MCP3208, 12-bit, 4- and 8-channel parts.

The library talks to the converter over a plain blocking SPI transaction. There
is no polling loop, no background thread, and no serial protocol: reading a
channel is one `transfer()` call on a `scietex.hal.spi` transport.

> Only the MCP3208 has been validated against silicon. MCP3204 support is
> derived from the datasheet (DS21298E) and shares the same frame format and
> unsupported-channel rules.

## Install

```bash
pip install scietex.hal.adc[spi]        # Linux spidev backend
pip install scietex.hal.adc[gpiozero]   # gpiozero backend
```

The base package installs without either backend. A device built from the
default keywords needs `spidev`; pin keywords (`clock_pin`, `mosi_pin`,
`miso_pin`, `select_pin`) need `gpiozero`. A missing backend raises
`ImportError` naming the extra to install.

## Wiring

| Signal | Connection |
| --- | --- |
| SCLK | SPI clock |
| MOSI (DIN) | SPI MOSI |
| MISO (DOUT) | SPI MISO |
| CS/SHDN | SPI chip select |
| V_REF | Reference voltage, also the full-scale input |
| V_DD | Supply, 2.7 V to 5.5 V |
| V_SS | Ground |

DS21298E notes:

- The part is **not** a true differential converter. In differential mode
  `IN−` must stay within ±100 mV of `V_SS`; it is a pseudo-differential input
  used to reject a small common-mode offset.
- Unused single-ended inputs should be tied to `V_SS` rather than left
  floating, so an adjacent channel's sample-and-hold does not pick up noise.

## Usage

```python
from scietex.hal.adc import MCP3208

device = MCP3208(device=0, v_ref=3.3)  # /dev/spidev0.0
try:
    code = device.channel(0).value  # raw 12-bit code, 0..4095
    voltage = device.channel(0).voltage
    print(code, voltage)
finally:
    device.close()
```

`MCP3208(device=0, v_ref=3.3)` is also a context manager; leaving the `with`
block closes the transport:

```python
with MCP3208(device=0, v_ref=3.3) as device:
    print(device.read_all())
```

Constructor keywords:

| Keyword | Meaning |
| --- | --- |
| `v_ref` | Reference voltage in volts, or omitted while unknown |
| `transport` (alias `spi`) | Any object with `transfer(tx)` and `close()` |
| `port`, `device` | spidev bus and chip select |
| `clock_pin`, `mosi_pin`, `miso_pin`, `select_pin` | gpiozero pin wiring |
| `label`, `log_level` | Logger name and level |

## Codes and voltages

`channel.value` is the raw code the converter returned. It is a live read:
every access is a new bus transaction, nothing is cached. `channel.value` is an
`int` in `0..4095`.

`channel.voltage` scales that code by the reference:

```
voltage = code * v_ref / 4096
```

With no `v_ref` configured, `voltage` is `None` — the library will not guess a
reference. Setting `device.v_ref = 3.3` later starts scaling new readings; the
codes themselves never change.

## Differential inputs

`device.differential` holds one channel per pair, `device.differential_channel(n)`
returns one by index. `channel.pair`, `channel.plus` and `channel.minus` expose
the mapping: pair `n` measures input `2n` against input `2n + 1`.

The result is **unsigned and unipolar** (DS21298E Tables 5-1 and 5-2):

- `000h` when `IN+ <= IN-`;
- `FFFh` at `(V_REF + IN-) - 1 LSB`;
- in between, `code = 4096 * (IN+ - IN-) / V_REF`.

A negative difference therefore reads 0, never a signed value.

## Geometry

| Part | Single-ended inputs | Differential pairs |
| --- | --- | --- |
| MCP3204 | 4 (`channel(0)`..`channel(3)`) | 2 (`differential_channel(0)`..`(1)`) |
| MCP3208 | 8 (`channel(0)`..`channel(7)`) | 4 (`differential_channel(0)`..`(3)`) |

`device.channels` and `device.differential` are tuples in index order.
`channel(n)` and `differential_channel(p)` raise `IndexError` outside that
range.

## Read everything

```python
codes = device.read_all()  # one code per single-ended input
pairs = device.read_differential()  # one code per differential pair
```

Both return tuples in index order, and every element is a separate bus
transaction — the calls read the inputs, they do not replay a cached buffer.

## Errors

- `TransportError` (from `scietex.hal.spi`) means the bus transaction failed.
- `ADCFrameError` (a `ValueError`) means the device answered with a malformed
  frame: wrong length, or a word outside `0..255`. It is exported from the
  package root.

## Testing

```bash
pytest                 # unit tests, no hardware needed
RUN_HARDWARE_TESTS=1 pytest tests/test_hardware.py
```

The unit tests drive a scripted transport and never open a real bus. The
hardware test needs an MCP3208 on `/dev/spidev0.0` and is skipped unless
`RUN_HARDWARE_TESTS=1` is set; CI never enables it.

Other checks:

```bash
tox -e format,lint,type
```

## Migrating from 0.0.x

0.0.x was a serial (RS485) library. This is now a synchronous SPI library and
the old surface is gone:

- `ADC` is no longer the RS485 base class; it is the SPI device container.
- `RS485ADC` is gone.
- `VdpADC` is gone.
- `scietex.hal.adc.scietex` is gone.

`msgspec` and `scietex.hal.serial` are no longer dependencies. Use
`MCP3204`/`MCP3208` with `scietex.hal.spi` transports instead.

## License

This project is licensed under the **MIT License** - see the LICENSE file for
details.
