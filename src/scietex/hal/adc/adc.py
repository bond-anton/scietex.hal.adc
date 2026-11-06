"""Base class for synchronous SPI analog-to-digital converters."""

from contextlib import suppress
from types import TracebackType
from typing import Any

from scietex.hal.spi import (
    GPIOZERO_SPI_ARGS,
    SpiTransport,
    build_default_transport,
    is_spi_transport,
)

from .__helpers import check_label, check_positive
from .__logger import get_logger
from .channel import DifferentialChannel, SingleEndedChannel


class ADC:
    """
    Container for the channels of an SPI analog-to-digital converter.

    The device owns one synchronous SPI transport and builds its channels once
    from the class-level geometry: `channels` holds the single-ended inputs and
    `differential` holds the pseudo-differential pairs, both in index order.
    Reading a code is a plain blocking bus transaction.

    `ADCChannel.value` is a live read: every access transfers one frame and
    decodes the response, nothing is cached. `ADCChannel.voltage` scales that
    code by `v_ref`, and returns None while `v_ref` is unset.

    The object can be used as a context manager; leaving the block closes the
    transport.
    """

    _CHANNELS: int = 0
    _PAIRS: int = 0
    _RESOLUTION: int = 12

    def __init__(  # noqa: PLR0913
        self,
        *,
        v_ref: float | None = None,
        transport: SpiTransport | None = None,
        spi: SpiTransport | None = None,
        port: Any = None,
        device: Any = None,
        clock_pin: Any = None,
        mosi_pin: Any = None,
        miso_pin: Any = None,
        select_pin: Any = None,
        label: str | None = None,
        log_level: int | str | None = None,
    ) -> None:
        """
        Build the device from an SPI transport or from the backend keywords.

        When neither `transport` nor `spi` is supplied, the keyword-only
        settings build a transport: `SpiDevTransport` by default, or
        `GpiozeroSpiTransport` when any pin keyword is given.

        :param v_ref: Reference voltage in volts used by the channel `voltage`
            properties, or None when the scaling is unknown (float | None).
        :param transport: Canonical SPI transport to use (SpiTransport).
        :param spi: Legacy alias for `transport`, used only when `transport`
            is None.
        :param port: spidev bus number, or the gpiozero SPI port when a pin
            keyword is given.
        :param device: spidev chip-select line, or the gpiozero SPI device
            when a pin keyword is given.
        :param clock_pin: GPIO pin used as SPI clock; any pin keyword selects
            the gpiozero backend.
        :param mosi_pin: GPIO pin used as SPI MOSI; selects the gpiozero
            backend.
        :param miso_pin: GPIO pin used as SPI MISO; selects the gpiozero
            backend.
        :param select_pin: GPIO pin used as SPI chip select; selects the
            gpiozero backend.
        :param label: Logger name, defaults to the class name (str).
        :param log_level: Logging level such as `logging.DEBUG`; defaults to
            `logging.ERROR`.
        :raises TypeError: If the supplied transport lacks transfer() or
            close(), if backend keywords accompany an explicit transport, or
            if `v_ref` or `label` has the wrong type.
        :raises ValueError: If `v_ref` is not positive or `label` is empty.
        :raises ImportError: If the optional package for the selected backend
            is missing.
        """
        supplied = {
            "port": port,
            "device": device,
            "clock_pin": clock_pin,
            "mosi_pin": mosi_pin,
            "miso_pin": miso_pin,
            "select_pin": select_pin,
        }
        built_here = False
        if transport is None and spi is not None:
            transport = spi
        if transport is not None:
            rejected = [
                name for name in GPIOZERO_SPI_ARGS if supplied[name] is not None
            ]
            if rejected:
                raise TypeError(
                    f"{', '.join(rejected)} cannot be combined with "
                    "transport/spi; pass either a transport or backend keywords"
                )
        else:
            transport = build_default_transport(**supplied)
            built_here = True
        try:
            if not is_spi_transport(transport):
                raise TypeError(
                    "Expected an SPI transport with transfer() and close(), "
                    f"got {type(transport)}"
                )
            self._transport = transport
            self._closed = False
            self.v_ref = v_ref
            self.label = None if label is None else check_label(label)
            self.logger = get_logger(self.label or type(self).__name__, log_level)
            self.channels: tuple[SingleEndedChannel, ...] = tuple(
                SingleEndedChannel(self, index) for index in range(self._CHANNELS)
            )
            self.differential: tuple[DifferentialChannel, ...] = tuple(
                DifferentialChannel(self, pair) for pair in range(self._PAIRS)
            )
        except Exception:
            # Only a transport built here is ours to release; a caller-supplied
            # one stays open because the caller still owns it.
            if built_here:
                with suppress(Exception):
                    transport.close()
            raise

    @property
    def v_ref(self) -> float | None:
        """Reference voltage in volts, or None when the scaling is unknown."""
        return self._v_ref

    @v_ref.setter
    def v_ref(self, v_ref: float | None) -> None:
        """
        Set the reference voltage used by the channel `voltage` properties.

        :param v_ref: Positive reference voltage in volts, or None (float | None).
        :raises TypeError: If `v_ref` is not a real number, or is a `bool`.
        :raises ValueError: If `v_ref` is zero, negative, infinite, or `NaN`.
        """
        self._v_ref = None if v_ref is None else float(check_positive(v_ref))

    @property
    def transport(self) -> SpiTransport:
        """SPI transport used by the device."""
        return self._transport

    @property
    def spi(self) -> Any:
        """Backend's raw handle when the transport wraps one."""
        return getattr(self._transport, "raw", self._transport)

    @property
    def closed(self) -> bool:
        """
        True when `close()` has run or the transport reports itself closed.

        A callable `closed` attribute is called first. The reported value is
        coerced with `bool`. A transport whose `closed` probe raises counts as
        not closed; the device's own flag still applies.
        """
        try:
            reported = getattr(self._transport, "closed", False)
            if callable(reported):
                reported = reported()
            reported = bool(reported)
        except Exception:  # noqa: BLE001 - a broken probe must not leak
            reported = False
        return self._closed or reported

    def close(self) -> None:
        """
        Close the underlying transport and mark the device closed.

        The device is marked closed even when the transport's `close()` raises;
        the exception is still propagated.
        """
        try:
            self._transport.close()
        finally:
            self._closed = True

    def __enter__(self) -> "ADC":
        """Return the device itself."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the transport when leaving the context."""
        self.close()

    def channel(self, index: int) -> SingleEndedChannel:
        """
        Return the single-ended channel at `index`.

        :param index: Channel index, 0-based (int).
        :return: `SingleEndedChannel` for that input.
        :raises IndexError: If `index` is outside `0..channels - 1`.
        """
        if not 0 <= index < self._CHANNELS:
            raise IndexError(f"Channel {index} does not exist")
        return self.channels[index]

    def differential_channel(self, pair: int) -> DifferentialChannel:
        """
        Return the differential pair at `pair`.

        :param pair: Pair index, 0-based (int).
        :return: `DifferentialChannel` for that pair.
        :raises IndexError: If `pair` is outside `0..pairs - 1`.
        """
        if not 0 <= pair < self._PAIRS:
            raise IndexError(f"Differential pair {pair} does not exist")
        return self.differential[pair]

    def read_all(self) -> tuple[int, ...]:
        """
        Read every single-ended channel.

        No value is cached: each element is a separate bus transaction.

        :return: Raw codes in channel index order (tuple of int).
        """
        return tuple(channel.value for channel in self.channels)

    def read_differential(self) -> tuple[int, ...]:
        """
        Read every differential pair.

        No value is cached: each element is a separate bus transaction.

        :return: Raw codes in pair index order (tuple of int).
        """
        return tuple(channel.value for channel in self.differential)

    def _read_single_ended(self, channel: int) -> int:
        """
        Read one single-ended input as a raw code.

        The base class has no frame format; `MCP320x` implements it.

        :param channel: Input number (int).
        :return: Raw code of the input.
        :raises NotImplementedError: Always, the base class has no codec.
        """
        raise NotImplementedError

    def _read_differential(self, pair: int) -> int:
        """
        Read one differential pair as a raw code.

        The base class has no frame format; `MCP320x` implements it.

        :param pair: Pair number (int).
        :return: Raw code of the input difference.
        :raises NotImplementedError: Always, the base class has no codec.
        """
        raise NotImplementedError
