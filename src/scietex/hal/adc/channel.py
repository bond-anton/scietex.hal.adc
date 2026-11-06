"""Channel objects for SPI analog-to-digital converters."""

from typing import TYPE_CHECKING

from .__helpers import check_integer

if TYPE_CHECKING:
    from .adc import ADC

#: Full-scale divisor of a 12-bit converter, also the voltage scaling factor.
_FULL_SCALE = 1 << 12


class ADCChannel:
    """
    One measured input of an `ADC` device.

    The channel holds only its device and index, no cached code: reading
    `value` transfers a frame over the bus every time, so a reading is always
    the current state of the input.
    """

    max_code: int = _FULL_SCALE - 1

    def __init__(self, adc: "ADC", index: int) -> None:
        self._adc = adc
        self.index = check_integer(index)

    @property
    def value(self) -> int:
        """
        Raw code of the input, read from the device.

        :return: 12-bit code in `0..max_code` (int).
        """
        raise NotImplementedError

    @property
    def voltage(self) -> float | None:
        """
        Input voltage scaled by the device reference.

        The device reports `code = 4096 * V_IN / V_REF` (DS21298E section
        4.2), so the top code stays one LSB below `v_ref`.

        :return: Voltage in volts, or None when the device has no `v_ref`.
        """
        v_ref = self._adc.v_ref
        if v_ref is None:
            return None
        return self.value * v_ref / _FULL_SCALE

    def __repr__(self) -> str:
        """Official string representation (used in debugging)."""
        return f"{type(self).__name__}(index={self.index})"


class SingleEndedChannel(ADCChannel):
    """Single-ended input, measured against the device ground."""

    @property
    def value(self) -> int:
        """
        Raw code of this input, read from the device.

        :return: 12-bit code in `0..max_code` (int).
        """
        return self._adc._read_single_ended(self.index)


class DifferentialChannel(ADCChannel):
    """
    Pseudo-differential input pair.

    The part is unipolar, not a true differential converter: DS21298E
    Tables 5-1 and 5-2 define the output as clamping at `000h` when
    `IN+ <= IN-` and at `FFFh` at `(V_REF + IN-) - 1 LSB`. A negative input
    difference therefore reads 0, never a signed value.
    """

    @property
    def pair(self) -> int:
        """Pair index, identical to `index`."""
        return self.index

    @property
    def plus(self) -> int:
        """Number of the non-inverting input, `2 * pair`."""
        return 2 * self.index

    @property
    def minus(self) -> int:
        """Number of the inverting input, `2 * pair + 1`."""
        return 2 * self.index + 1

    @property
    def value(self) -> int:
        """
        Unsigned code of the input difference, read from the device.

        The conversion is unipolar, so a negative difference reads 0 and the
        result never leaves `0..max_code`.

        :return: 12-bit code in `0..max_code` (int).
        """
        return self._adc._read_differential(self.index)
