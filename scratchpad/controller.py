"""Order input commands around asynchronous word commits."""

from collections import deque
from collections.abc import Callable
from typing import Literal

from .composition import Commit, Composition, Failure, PredictionRequest, Preview
from .worker import PredictionWorker

Command = Literal['append', 'backspace', 'separator']


class InputController:
    """Own one composition on the calling thread.

    The caller schedules drain on the owner thread when the worker calls
    on_ready. emit runs on the owner thread and must not reenter the controller.
    The caller supplies word fragments and separators separately.
    """

    def __init__(
        self,
        predict: Callable[[str], str],
        on_ready: Callable[[], None],
        emit: Callable[[Commit | Preview | Failure], None],
        *,
        max_commands: int = 256,
        max_characters: int = 16_384,
    ) -> None:
        if max_commands < 1 or max_characters < 1:
            raise ValueError('Queue limits must be positive')
        self._composition = Composition()
        self._emit = emit
        self._commands: deque[tuple[Command, str]] = deque()
        self._queued_characters = 0
        self._max_commands = max_commands
        self._max_characters = max_characters
        self._commit: PredictionRequest | None = None
        self._failed_separator: str | None = None
        self._closed = False
        self._worker = PredictionWorker(predict, on_ready)

    def append(self, text: str) -> bool:
        return self._submit('append', text)

    def backspace(self) -> bool:
        return self._submit('backspace', '')

    def separator(self, text: str) -> bool:
        return self._submit('separator', text)

    def retry(self) -> bool:
        if self._closed or self._failed_separator is None:
            return False
        separator = self._failed_separator
        self._failed_separator = None
        self._finish(separator)
        return True

    def drain(self) -> None:
        if self._closed:
            return
        result = self._worker.take_result()
        if result is None:
            return
        if result.failed:
            event = self._composition.reject(result.request)
        else:
            event = self._composition.resolve(result.request, result.output)
        if result.request is self._commit:
            self._commit = None
            if isinstance(event, Failure):
                self._failed_separator = event.separator
        if event is not None:
            self._emit(event)
        self._advance()

    def close(self) -> None:
        self._closed = True
        self._commands.clear()
        self._queued_characters = 0
        self._commit = None
        self._failed_separator = None
        self._composition = Composition()
        self._worker.close()

    def join(self, timeout: float) -> bool:
        return self._worker.join(timeout)

    def _submit(self, command: Command, text: str) -> bool:
        if self._closed:
            return False
        if (
            len(self._commands) >= self._max_commands
            or self._queued_characters + len(text) > self._max_characters
        ):
            return False
        self._commands.append((command, text))
        self._queued_characters += len(text)
        self._advance()
        return True

    def _advance(self) -> None:
        while self._commands and self._commit is None and self._failed_separator is None:
            command, text = self._commands.popleft()
            self._queued_characters -= len(text)
            if command == 'separator':
                self._finish(text)
                continue
            word = self._composition.word
            word = word + text if command == 'append' else word[:-1]
            request = self._composition.edit(word)
            if request is not None:
                self._worker.submit(request)

    def _finish(self, separator: str) -> None:
        result = self._composition.finish(separator)
        if isinstance(result, Commit):
            self._emit(result)
        else:
            self._commit = result
            # Only one final request can be pending.
            if not self._worker.submit(result):
                raise RuntimeError('Worker rejected the only pending commit')
