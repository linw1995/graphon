import pytest

from graphon.runtime import CancellationError, CancellationToken


def test_cancel_only_succeeds_once() -> None:
    token = CancellationToken()

    assert token.cancel("timeout") is True
    assert token.cancel("user requested stop") is False

    assert token.cancelled is True
    assert token.reason == "timeout"


def test_raise_if_cancelled_uses_reason() -> None:
    token = CancellationToken()
    token.raise_if_cancelled()

    token.cancel("timeout")

    with pytest.raises(CancellationError, match="Execution was cancelled: timeout"):
        token.raise_if_cancelled()
