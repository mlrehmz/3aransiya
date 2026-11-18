"""Run word predictions off the editor thread with bounded storage."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Condition, Thread

from .composition import PredictionRequest


@dataclass(frozen=True)
class PredictionResult:
    request: PredictionRequest
    output: object = None
    failed: bool = False


class PredictionWorker:
    """Own one predictor thread and a single unread result.

    The ready callback runs on the worker thread. It must be nonblocking
    and must not raise. It only schedules a wakeup for the owner to drain.
    A wakeup already in flight can arrive after close with no result.
    """

    def __init__(
        self, predict: Callable[[str], str], on_ready: Callable[[], None]
    ) -> None:
        self._predict = predict
        self._on_ready = on_ready
        self._condition = Condition()
        self._closed = False
        self._preview: PredictionRequest | None = None
        self._commit: PredictionRequest | None = None
        self._result: PredictionResult | None = None
        self._thread = Thread(target=self._run, name='word-predictor', daemon=True)
        self._thread.start()

    def submit(self, request: PredictionRequest) -> bool:
        """Return false if closed or the waiting commit slot is full."""
        with self._condition:
            if self._closed:
                return False
            if request.separator is None:
                self._preview = request
            else:
                if self._commit is not None:
                    return False
                self._commit = request
                self._preview = None
            self._condition.notify_all()
            return True

    def take_result(self) -> PredictionResult | None:
        """Drain the result without waiting for a prediction."""
        with self._condition:
            result = self._result
            self._result = None
            self._condition.notify_all()
            return result

    def close(self) -> None:
        """Drop waiting work and suppress results from running work."""
        with self._condition:
            self._closed = True
            self._commit = None
            self._preview = None
            self._result = None
            self._condition.notify_all()

    def join(self, timeout: float) -> bool:
        """Wait up to timeout seconds for exit. Call outside the UI loop."""
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def _can_run(self) -> bool:
        return self._closed or (
            self._result is None and (self._commit is not None or self._preview is not None)
        )

    def _run(self) -> None:
        while True:
            with self._condition:
                self._condition.wait_for(self._can_run)
                if self._closed:
                    return
                if self._commit is not None:
                    request = self._commit
                    self._commit = None
                else:
                    request = self._preview
                    self._preview = None
            assert request is not None
            try:
                result = PredictionResult(request, self._predict(request.word))
            except Exception:
                result = PredictionResult(request, failed=True)

            with self._condition:
                if self._closed:
                    return
                self._result = result
            self._on_ready()
