"""Artificial predictions for editor development, never real transliterations."""


from hashlib import sha256
import os
from pathlib import Path


APP_ID = 'io.github.aransiya.Scratchpad'


def application_id(bundle=None):
    if bundle is None:
        return APP_ID
    digest = sha256(os.fsencode(Path(bundle).resolve())).hexdigest()[:16]
    return f'{APP_ID}.Model{digest}'


class MockPredictor:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def predict(self, word: str) -> str:
        if self.fail:
            raise RuntimeError('Mock prediction failed')
        return f'تجربة{len(word)}'


class HelperPredictor:
    """Start the configured helper on the first worker request."""

    def __init__(self, command):
        self._command = command
        self._process = None

    def predict(self, word):
        from .process_predictor import ProcessPredictor

        if self._process is None or self._process.closed:
            self._process = ProcessPredictor(self._command)
        return self._process.predict(word)

    def close(self):
        if self._process is not None:
            self._process.close()
