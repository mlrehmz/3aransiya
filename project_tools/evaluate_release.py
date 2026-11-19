"""Score a frozen release profile and the original encoder on the locked DODa test."""

import argparse
from contextlib import redirect_stdout
import json
from pathlib import Path
import sys

import torch

from project_tools.compare_model_routes import measure
from model_pilot.bundle import load_bundle
from model_pilot.data import load_development_data
from scratchpad.release_model import file_digest, load_profile
from project_tools.validation_benchmark import benchmark
from project_tools.word_pairs import extract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("dataset", "sentences", "assignment", "baseline", "profile"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()

    torch.set_num_threads(1)
    profile_digest = file_digest(args.profile / "profile.json")
    release = load_profile(args.profile)
    baseline = load_bundle(args.baseline).predict
    with redirect_stdout(sys.stderr):
        rows = load_development_data(args.dataset, version="v2").training
    test = extract(args.sentences.read_bytes(), args.assignment.read_bytes(), final_test=True)
    test_rows = test["pairs"]["test"]
    words = sorted({row["latin"] for row in test_rows})
    pairs = {"train": rows, "validation": test_rows}

    scores = {}
    for name, predict in (("epoch6_encoder", baseline), ("release", release)):
        predict("salam")  # Exclude model warm-up.
        predictions, latency = measure(words, predict)
        scores[name] = {
            "scores": benchmark(pairs, predictions, preserve_v1_slices=True)["slices"],
            "latency": latency,
        }
    print(json.dumps({
        "profile_sha256": profile_digest,
        "test_extraction": test["counts"]["test"],
        "candidates": scores,
    }, indent=2))


if __name__ == "__main__":
    main()
