from __future__ import annotations

import threading
from typing import final


class CancellationError(RuntimeError):
    def __init__(self, reason: str | None = None) -> None:
        self.reason = reason
        message = "Execution was cancelled"
        if reason:
            message = f"{message}: {reason}"
        super().__init__(message)


@final
class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._reason: str | None = None

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    @property
    def reason(self) -> str | None:
        return self._reason

    def cancel(self, reason: str | None = None) -> bool:
        if self._event.is_set():
            return False

        with self._lock:
            if self._event.is_set():
                return False
            self._reason = reason
            self._event.set()
            return True

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise CancellationError(self._reason)
