"""Open a model bundle and serve predictions over local pipes."""

import argparse

import torch

from model_pilot.bundle import load_bundle
from scratchpad.process_predictor import serve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle")
    args = parser.parse_args()
    torch.set_num_threads(1)
    predictor = load_bundle(args.bundle)
    # Untrained models can legitimately return no word during warm-up.
    try:
        predictor.predict("a")
    except ValueError:
        pass
    serve(predictor.predict)


if __name__ == "__main__":
    main()
