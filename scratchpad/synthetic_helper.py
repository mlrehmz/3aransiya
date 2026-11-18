"""Serve the opt-in synthetic prediction fixture."""

from .predictor import MockPredictor
from .process_predictor import serve


def main():
    predictor = MockPredictor()

    def predict(word):
        if word == "fail":
            raise RuntimeError("synthetic failure")
        return predictor.predict(word)

    serve(predict)


if __name__ == "__main__":
    main()
