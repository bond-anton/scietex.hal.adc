"""MCP320x SPI frame codec and device base class."""

from ..__helpers import check_bool, check_integer
from ..adc import ADC
from ..errors import ADCFrameError

_FRAME_LENGTH = 3


def _check_frame_word(word: int, frame: list[int]) -> int:
    """
    Validate one received frame word.

    :param word: Received word.
    :param frame: Whole received frame, used in the error message.
    :return: The word as int.
    :raises ADCFrameError: If `word` is not an integer in 0..255.
    """
    try:
        value = check_integer(word)
    except (TypeError, ValueError) as exc:
        raise ADCFrameError(f"malformed SPI frame: {frame!r}") from exc
    if not 0 <= value <= 0xFF:
        raise ADCFrameError(f"malformed SPI frame: {frame!r}")
    return value


def encode_command(*, single_ended: bool, select: int) -> list[int]:
    """
    Build the 3-byte SPI request frame.

    `single_ended` sets the SGL/DIFF bit. In single-ended mode `select` is the
    channel number; in differential mode it is the 3-bit code of DS21298E
    Tables 5-1 and 5-2, `2 * pair + polarity`.

    Bit 2 of the channel field is a don't-care on the MCP3204; it is always
    driven low, which is safe for both parts.

    :param single_ended: True to request a single-ended input (bool).
    :param select: Channel number or differential code, 0..7 (int).
    :return: Request frame of three bytes.
    :raises TypeError: If `select` is not a real number, or `single_ended` is
        not a bool.
    :raises ValueError: If `select` is fractional or outside 0..7.
    """
    select = check_integer(select)
    if not 0 <= select <= 7:
        raise ValueError(f"Expected a channel or pair code in 0..7, got {select}")
    mode = 0x40 if check_bool(single_ended) else 0x00
    return [0x80 | mode | (select << 3), 0x00, 0x00]


def decode_code(data: list[int]) -> int:
    """
    Decode the 12-bit code from a 3-byte SPI response.

    The device returns the result right-aligned: bits 11:8 in the low nibble
    of byte 1, bits 7:0 in byte 2.

    :param data: Response frame of three bytes.
    :return: Raw 12-bit code.
    :raises ADCFrameError: If the frame is not three bytes long or holds a
        word that is not an integer in 0..255.
    """
    if len(data) != _FRAME_LENGTH:
        raise ADCFrameError(f"malformed SPI frame: {data!r}")
    words = [_check_frame_word(word, data) for word in data]
    return ((words[1] & 0x0F) << 8) | words[2]


class MCP320x(ADC):
    """
    Base class for the MCP3204 and MCP3208 12-bit SPI converters.

    Subclasses set the channel geometry; frame encoding and decoding are
    shared. `_read_single_ended` and `_read_differential` each perform exactly
    one transfer and return the raw code.
    """

    _RESOLUTION = 12

    def _read_single_ended(self, channel: int) -> int:
        """
        Read one single-ended input as a raw code.

        :param channel: Input number (int).
        :return: Raw code of the input.
        :raises TransportError: If the bus transaction fails.
        :raises ADCFrameError: If the response frame is malformed.
        """
        frame = encode_command(single_ended=True, select=channel)
        return decode_code(self.transport.transfer(frame))

    def _read_differential(self, pair: int) -> int:
        """
        Read one differential pair as a raw code.

        The fixed pair collection measures IN+ on the even input, so the
        polarity bit stays clear (Tables 5-1 and 5-2).

        :param pair: Pair number (int).
        :return: Raw code of the input difference.
        :raises TransportError: If the bus transaction fails.
        :raises ADCFrameError: If the response frame is malformed.
        """
        frame = encode_command(single_ended=False, select=2 * pair)
        return decode_code(self.transport.transfer(frame))
