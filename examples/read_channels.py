"""Read every input of an MCP3208 wired to /dev/spidev0.0."""

from scietex.hal.adc import MCP3208


def main() -> None:
    adc = MCP3208(device=0, v_ref=3.3)
    try:
        print("Single-ended inputs:")
        for channel in adc.channels:
            print(
                f"  IN{channel.index}: code={channel.value:4d}  {channel.voltage:.3f} V"
            )

        print("Differential pairs:")
        for pair in adc.differential:
            print(
                f"  IN{pair.plus}-IN{pair.minus}: "
                f"code={pair.value:4d}  {pair.voltage:.3f} V"
            )
    finally:
        adc.close()


if __name__ == "__main__":
    main()
