"""Tests for the MCP320x SPI frame codec."""

import pytest

from scietex.hal.adc.errors import ADCFrameError
from scietex.hal.adc.mcp320x.mcp320x import decode_code, encode_command

SINGLE_ENDED_MCP3208 = [
    (0, 0x06, 0x00),
    (1, 0x06, 0x40),
    (2, 0x06, 0x80),
    (3, 0x06, 0xC0),
    (4, 0x07, 0x00),
    (5, 0x07, 0x40),
    (6, 0x07, 0x80),
    (7, 0x07, 0xC0),
]

DIFFERENTIAL_MCP3208 = [
    (0, 0x04, 0x00),
    (1, 0x04, 0x40),
    (2, 0x04, 0x80),
    (3, 0x04, 0xC0),
    (4, 0x05, 0x00),
    (5, 0x05, 0x40),
    (6, 0x05, 0x80),
    (7, 0x05, 0xC0),
]


@pytest.mark.parametrize(("select", "first_byte", "second_byte"), SINGLE_ENDED_MCP3208)
def test_single_ended_command_bytes(
    select: int, first_byte: int, second_byte: int
) -> None:
    """Every MCP3208 single-ended channel maps to its documented bytes."""
    assert encode_command(single_ended=True, select=select) == [
        first_byte,
        second_byte,
        0x00,
    ]


@pytest.mark.parametrize(
    ("select", "first_byte", "second_byte"), SINGLE_ENDED_MCP3208[:4]
)
def test_mcp3204_reuses_the_first_four_single_ended_bytes(
    select: int, first_byte: int, second_byte: int
) -> None:
    """The MCP3204 channels 0..3 send the same four single-ended bytes."""
    assert encode_command(single_ended=True, select=select) == [
        first_byte,
        second_byte,
        0x00,
    ]


@pytest.mark.parametrize(("select", "first_byte", "second_byte"), DIFFERENTIAL_MCP3208)
def test_differential_command_bytes(
    select: int, first_byte: int, second_byte: int
) -> None:
    """Every MCP3208 differential code clears SGL/DIFF and sets its own D2..D0."""
    assert encode_command(single_ended=False, select=select) == [
        first_byte,
        second_byte,
        0x00,
    ]


@pytest.mark.parametrize(
    ("select", "first_byte", "second_byte"), DIFFERENTIAL_MCP3208[:4]
)
def test_mcp3204_reuses_the_first_four_differential_bytes(
    select: int, first_byte: int, second_byte: int
) -> None:
    """The MCP3204 differential codes 0..3 send the same four bytes."""
    assert encode_command(single_ended=False, select=select) == [
        first_byte,
        second_byte,
        0x00,
    ]


@pytest.mark.parametrize("select", [-1, 8, 9, 42])
def test_select_outside_range_raises(select: int) -> None:
    """A channel or pair code outside 0..7 is a ValueError."""
    with pytest.raises(ValueError):
        encode_command(single_ended=True, select=select)


@pytest.mark.parametrize("select", [0.5, 1.25])
def test_fractional_select_raises(select: float) -> None:
    """A fractional channel number is not a channel."""
    with pytest.raises(ValueError):
        encode_command(single_ended=False, select=select)


@pytest.mark.parametrize("select", ["1", None, [1]])
def test_non_numeric_select_raises(select: object) -> None:
    """A non-numeric channel number is a TypeError."""
    with pytest.raises(TypeError):
        encode_command(single_ended=True, select=select)  # type: ignore[arg-type]


@pytest.mark.parametrize("single_ended", [0, 1, "yes", None, 0.0])
def test_non_bool_single_ended_raises(single_ended: object) -> None:
    """The SGL/DIFF bit accepts a bool only."""
    with pytest.raises(TypeError):
        encode_command(single_ended=single_ended, select=0)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ([0, 0x00, 0x00], 0),
        ([0, 0x0F, 0xFF], 4095),
        ([0, 0x08, 0x00], 2048),
        ([0, 0xF7, 0x00], 0x700),
    ],
)
def test_decode_code(data: list[int], expected: int) -> None:
    """The code sits right-aligned across bytes 1 and 2."""
    assert decode_code(data) == expected


@pytest.mark.parametrize("data", [[], [0], [0, 0], [0, 0, 0, 0], [0, 0, 0, 0, 0]])
def test_decode_wrong_length_raises(data: list[int]) -> None:
    """A frame that is not three bytes long is rejected with its content."""
    with pytest.raises(ADCFrameError) as excinfo:
        decode_code(data)
    assert repr(data) in str(excinfo.value)


@pytest.mark.parametrize("word", [-1, 256, 1000])
def test_decode_out_of_range_word_raises(word: int) -> None:
    """A word outside 0..255 is reported together with the whole frame."""
    data = [0x00, 0x00, word]
    with pytest.raises(ADCFrameError) as excinfo:
        decode_code(data)
    assert repr(data) in str(excinfo.value)


@pytest.mark.parametrize("word", [1.5, None, "0x00"])
def test_decode_non_integer_word_raises(word: object) -> None:
    """A word that is not an integer is a frame error, not a TypeError."""
    data = [0x00, 0x00, word]
    with pytest.raises(ADCFrameError) as excinfo:
        decode_code(data)  # type: ignore[list-item]
    assert repr(data) in str(excinfo.value)


def test_decode_ignores_byte_zero() -> None:
    """Byte 0 carries no code bit."""
    assert decode_code([0xFF, 0x0F, 0xFF]) == 4095
