"""Measure CPU transliteration routing on the pinned development split."""

import argparse
from contextlib import redirect_stdout
from functools import partial
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import torch

from model_pilot.bundle import load_bundle
from model_pilot.data import load_development_data
from scratchpad.phrases import render_text, shorten
from scratchpad.release_model import human_references, routed_predict, training_references
from validation_benchmark import benchmark


PROBES = (
    ("sallllllla llllaho 3alayhi wasallam", "صلى الله عليه وسلم"),
    ("salla allaho 3alayhi wa sallam", "صلى الله عليه وسلم"),
    ("asba7na wa asbaha lmolko lilah", "أصبحنا وأصبح الملك لله"),
    ("salla, allaho 3alayhi wasallam", None),
    ("salla allaho 3alayhi", None),
    ("yaaaaaaaa haaaaaaa xtiiiiiii", "يا ها ختي"),
)


def render_probe(text, predict, *, repair=False):
    def word_output(match):
        word = match[0]
        if word.isdecimal():
            return word
        try:
            return predict(shorten(word) if repair else word)
        except ValueError:
            return word

    return render_text(text, word_output, phrases=repair)


def measure(words, predict):
    predictions = {}
    durations = []
    for word in words:
        start = perf_counter()
        try:
            predictions[word] = predict(word)
        except ValueError:
            pass
        durations.append(perf_counter() - start)
    ordered = sorted(durations)
    return predictions, {
        "median_ms": 1000 * median(ordered),
        "p95_ms": 1000 * ordered[(95 * len(ordered) - 1) // 100],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("encoder", type=Path)
    parser.add_argument("ctc", type=Path)
    parser.add_argument("--weighted", type=Path)
    parser.add_argument("--fine-tuned", type=Path)
    args = parser.parse_args()

    torch.set_num_threads(1)
    with redirect_stdout(sys.stderr):
        data = load_development_data(args.dataset, version="v2")
    pairs = {"train": data.training, "validation": data.validation}
    human_forms, lexicon = human_references(data.training)
    encoder = load_bundle(args.encoder).predict
    ctc = load_bundle(args.ctc).predict
    candidates = {
        "epoch6_encoder": encoder,
        "epoch6_ctc": ctc,
        "routed": partial(routed_predict, encoder=encoder, ctc=ctc,
                          human_forms=human_forms, lexicon=lexicon),
    }
    _, grounded = training_references(data.training, "doda_grounded", 5, 90, human_forms)
    enriched_lexicon = lexicon | grounded
    candidates["routed_grounded"] = partial(routed_predict, encoder=encoder, ctc=ctc,
                                            human_forms=human_forms, lexicon=enriched_lexicon)
    if args.fine_tuned:
        fine_tuned = load_bundle(args.fine_tuned).predict
        candidates["fine_tuned_routed"] = partial(
            routed_predict, encoder=fine_tuned, ctc=ctc, human_forms=human_forms,
            lexicon=enriched_lexicon,
        )
    candidates["routed_shortened"] = lambda word: candidates["routed"](shorten(word))
    if args.weighted:
        weighted = load_bundle(args.weighted).predict
        candidates["weighted_encoder"] = weighted
        candidates["weighted_routed"] = partial(routed_predict, encoder=weighted, ctc=ctc,
                                                human_forms=human_forms, lexicon=lexicon)
    results = {}
    for name, predict in candidates.items():
        predictions, latency = measure(data.validation_forms, predict)
        results[name] = {
            "scores": benchmark(pairs, predictions, preserve_v1_slices=True)["slices"],
            "latency": latency,
        }
    best = candidates["routed"]
    results["probes"] = [
        {
            "input": text, "expected": expected,
            "epoch6_encoder": render_probe(text, encoder),
            "routed": render_probe(text, best),
            "routed_with_repair": render_probe(text, best, repair=True),
            **({"weighted_encoder": render_probe(text, weighted)} if args.weighted else {}),
        }
        for text, expected in PROBES
    ]
    word_probes = ("Xa", "ka2s", "kas", "2o", "prizontasyon", "X7al", "xrebt", "khobz", "sport")
    results["word_probes"] = {
        name: measure(word_probes, predict)[0] for name, predict in candidates.items()
    }
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
