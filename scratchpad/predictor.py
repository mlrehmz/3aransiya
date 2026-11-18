"""Artificial predictions for editor development, never real transliterations."""


class MockPredictor:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def predict(self, word: str) -> str:
        if self.fail:
            raise RuntimeError('Mock prediction failed')
        return f'تجربة{len(word)}'


class SyntheticHelperPredictor:
    """Start the development helper on the first worker request."""

    def __init__(self, python):
        self._python = python
        self._process = None

    def predict(self, word):
        from .process_predictor import ProcessPredictor

        if self._process is None or self._process.closed:
            self._process = ProcessPredictor([self._python, "-m", "scratchpad.synthetic_helper"])
        return self._process.predict(word)

    def close(self):
        if self._process is not None:
            self._process.close()
