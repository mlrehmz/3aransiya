"""Artificial predictions for editor development, never real transliterations."""


class MockPredictor:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def predict(self, word: str) -> str:
        if self.fail:
            raise RuntimeError('Mock prediction failed')
        return f'تجربة{len(word)}'
