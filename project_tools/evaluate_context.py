"""Compare the word release with bounded contextual rendering on development sentences."""

import argparse
import json
from pathlib import Path
import random

import torch

from scratchpad.context import load_context
from sentence_pilot.data import read_pairs
from sentence_pilot.evaluate import baseline_renderer, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("sentences", "assignment", "profile"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    torch.set_num_threads(1)
    pairs = read_pairs(args.sentences, args.assignment)["validation"]
    pairs = random.Random(112).sample(pairs, 512)
    context = load_context(args.profile)
    if context is None:
        parser.error("expected a contextual profile")
    print(json.dumps({
        "word_release": report(baseline_renderer(args.profile), pairs),
        "contextual": report(baseline_renderer(args.profile, context=context), pairs),
        "copy_and_phrases_only": report(baseline_renderer(args.profile, context={}), pairs),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
