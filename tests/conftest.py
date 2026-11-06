"""Shared helpers for the ADC tests."""

from collections.abc import Sequence

from scietex.hal.spi import FakeSpiTransport


def frame(code: int) -> list[int]:
    """3-byte response a real MCP320x returns for `code`."""
    return [0x00, (code >> 8) & 0x0F, code & 0xFF]


def fake(*codes: int) -> FakeSpiTransport:
    """Transport queuing one response frame per code, in order."""
    return FakeSpiTransport(responses=[frame(code) for code in codes])


class RecordingTransport:
    """Transport wrapper that records every request the device sends."""

    def __init__(self, inner: FakeSpiTransport) -> None:
        self.inner = inner
        self.requests: list[list[int]] = []
        self.close_calls = 0

    @property
    def closed(self) -> bool:
        """Return the wrapped transport's closed state."""
        return self.inner.closed

    def transfer(self, tx: Sequence[int]) -> list[int]:
        """Record `tx` and forward it to the wrapped transport."""
        self.requests.append(list(tx))
        return self.inner.transfer(tx)

    def close(self) -> None:
        """Count the call and close the wrapped transport."""
        self.close_calls += 1
        self.inner.close()


def recording(inner: FakeSpiTransport) -> RecordingTransport:
    """Wrap `inner` so the outbound frames stay inspectable."""
    return RecordingTransport(inner)
