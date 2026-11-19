"""Compare sentence decoding and the release renderer on the same development set."""

import argparse
import json
from pathlib import Path
import random
import re
from statistics import median
from time import perf_counter

import torch

from scratchpad.context import load_context
from scratchpad.phrases import render_text
from scratchpad.release_model import load_profile
from .data import MAX_CHARS, normalize, read_pairs
from .train import load_model


MIXED = (
    ("salam labas, please send the address", "please send the address"),
    ("wach jay? I will be there tomorrow.", "I will be there tomorrow."),
    ("chokran, je te rappelle demain.", "je te rappelle demain."),
    ("je suis déjà là, wach nta 9rib?", "je suis déjà là"),
    ("[redacted mixed-language sample], "
     "3alimto 3nho min khilali 9ira2ati ba3di kotobi ssalaf, "
     "[redacted English sample]", "[redacted English sample]"),
)
PHRASE = "علمت عنه من خلال قراءتي بعض كتب السلف"


def edit_distance(left, right):
    prior = list(range(len(right) + 1))
    for index, char in enumerate(left, 1):
        row = [index]
        for offset, reference in enumerate(right, 1):
            row.append(min(prior[offset] + 1, row[-1] + 1, prior[offset - 1] + (char != reference)))
        prior = row
    return prior[-1]


def baseline_renderer(profile, *, context=None):
    predict_word = load_profile(profile)

    def output(match):
        text = match[0]
        if text.isdecimal():
            return text
        try:
            return predict_word(text)
        except ValueError:
            return text

    return lambda batch: [render_text(text, output, phrases=True, context=context) for text in batch]


def split_probe(text, predict):
    parts = re.split(r"([,;،] +)", text)
    parts[::2] = predict(parts[::2])
    return "".join(parts)


def report(predict, pairs):
    predictions = []
    for start in range(0, len(pairs), 32):
        predictions.extend(predict([source for source, _ in pairs[start:start + 32]]))
    expected = [target for _, target in pairs]
    predictions = [normalize(output) for output in predictions]
    timed = []
    for source, _ in pairs[:12]:
        start = perf_counter()
        predict([source])
        timed.append(1000 * (perf_counter() - start))

    probes = []
    for text, span in MIXED:
        if len(text) > MAX_CHARS:
            raise ValueError("probe exceeds the training length bound")
        output, = predict([text])
        split = split_probe(text, predict)
        probes.append({
            "source": text, "output": output, "copy_exact": span in output,
            "split_output": split, "split_copy_exact": span in split,
        })
    return {
        "sentences": len(expected),
        "exact_matches": sum(a == b for a, b in zip(predictions, expected)),
        "character_error_rate": sum(edit_distance(a, b) for a, b in zip(predictions, expected))
        / sum(map(len, expected)),
        "median_cpu_ms_per_sentence": median(timed),
        "mixed_spans_preserved": sum(probe["copy_exact"] for probe in probes),
        "formal_span_exact": PHRASE in probes[-1]["output"],
        "split_mixed_spans_preserved": sum(probe["split_copy_exact"] for probe in probes),
        "split_formal_span_exact": PHRASE in probes[-1]["split_output"],
        "probes": probes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("sentences", "assignment", "checkpoint", "baseline"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--sample", type=int, default=512)
    parser.add_argument("--adapted", type=Path)
    args = parser.parse_args()
    if args.sample < 12:
        parser.error("--sample must be at least 12")
    torch.set_num_threads(1)
    pairs = read_pairs(args.sentences, args.assignment)["validation"]
    pairs = random.Random(112).sample(pairs, min(len(pairs), args.sample))
    transformer, step = load_model(args.checkpoint)
    result = {
        "checkpoint_step": step,
        "baseline": report(baseline_renderer(args.baseline), pairs),
        "transformer": report(transformer.predict, pairs),
    }
    if args.adapted:
        adapted, adaptation_step = load_model(args.adapted)
        result["copy_adaptation_step"] = adaptation_step
        result["transformer_copy_adapted"] = report(adapted.predict, pairs)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
