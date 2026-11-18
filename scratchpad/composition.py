"""Compose one word and emit changes for the document owner to apply."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionRequest:
    revision: int
    word: str
    separator: str | None = None


@dataclass(frozen=True)
class Commit:
    text: str


@dataclass(frozen=True)
class Preview:
    text: str


@dataclass(frozen=True)
class Failure:
    message: str
    separator: str | None


class Composition:
    def __init__(self) -> None:
        self._word = ''
        self._revision = 0
        self._pending: PredictionRequest | None = None

    @property
    def word(self) -> str:
        return self._word

    def edit(self, word: str) -> PredictionRequest | None:
        """Replace the complete active word, including after backspace."""
        self._check_editable()
        self._word = word
        self._revision += 1
        if not word or word.isdecimal():
            self._pending = None
            return None
        self._pending = PredictionRequest(self._revision, word)
        return self._pending

    def finish(self, separator: str) -> PredictionRequest | Commit:
        """Finalize the word; an empty separator adds no text."""
        self._check_editable()
        self._revision += 1
        if not self.word or self.word.isdecimal():
            text = self.word + separator
            self._word = ''
            self._pending = None
            return Commit(text)
        self._pending = PredictionRequest(self._revision, self.word, separator)
        return self._pending

    def resolve(
        self, request: PredictionRequest, output: object
    ) -> Preview | Commit | Failure | None:
        """Accept a result once, only for the current request object."""
        if not isinstance(request, PredictionRequest) or request is not self._pending:
            return None
        self._pending = None
        if not isinstance(output, str) or not output or any(c.isspace() for c in output):
            return Failure('Invalid prediction', request.separator)
        if request.separator is None:
            return Preview(output)
        self._word = ''
        return Commit(output + request.separator)

    def reject(self, request: PredictionRequest) -> Failure | None:
        """Report a failed prediction without removing the source word."""
        if not isinstance(request, PredictionRequest) or request is not self._pending:
            return None
        self._pending = None
        return Failure('Prediction failed', request.separator)

    def _check_editable(self) -> None:
        if self._pending is not None and self._pending.separator is not None:
            raise RuntimeError('Resolve or reject the pending commit before editing')
