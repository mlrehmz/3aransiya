"""Measure CPU transliteration routing on the pinned development split."""

import argparse
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from functools import partial
import json
from pathlib import Path
import re
from statistics import median
import sys
from time import perf_counter

import torch

from model_pilot.bundle import load_bundle
from model_pilot.data import load_development_data
from validation_benchmark import benchmark


def human_references(rows):
    counts = defaultdict(Counter)
    for row in rows:
        if row["source"] == "doda_human":
            counts[row["latin"]][row["arabic"]] += 1
    lexicon = {}
    for word, alternatives in counts.items():
        winner = min(alternatives, key=lambda ref: (-alternatives[ref], ref))
        support = alternatives[winner]
        if support >= 3 and support * 10 >= alternatives.total() * 9:
            lexicon[word] = winner
    return set(counts), lexicon


def routed_predict(word, encoder, ctc, human_forms, lexicon):
    if word in lexicon:
        return lexicon[word]
    if word not in human_forms:
        try:
            return ctc(word)
        except ValueError:
            pass
    return encoder(word)


LATIN_WORD = re.compile(r"[A-Za-z0-9]+")
ELONGATION = re.compile(r"([A-Za-z])\1{2,}")
PHRASES = {
    ("salla", "llaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wa", "sallam"): "صلى الله عليه وسلم",
    ("asba7na", "wa", "asbaha", "lmolko", "lilah"): "أصبحنا وأصبح الملك لله",
}
PROBES = (
    ("sallllllla llllaho 3alayhi wasallam", "صلى الله عليه وسلم"),
    ("salla allaho 3alayhi wa sallam", "صلى الله عليه وسلم"),
    ("asba7na wa asbaha lmolko lilah", "أصبحنا وأصبح الملك لله"),
    ("salla, allaho 3alayhi wasallam", None),
    ("salla allaho 3alayhi", None),
    ("yaaaaaaaa haaaaaaa xtiiiiiii", "يا ها ختي"),
)


def shorten(word):
    return ELONGATION.sub(r"\1\1", word)


def render_probe(text, predict, *, repair=False):
    words = list(LATIN_WORD.finditer(text))
    pieces = []
    cursor = 0
    index = 0
    while index < len(words):
        word = words[index]
        pieces.append(text[cursor:word.start()])
        match = None
        if repair:
            for phrase, arabic in PHRASES.items():
                span = words[index:index + len(phrase)]
                if tuple(shorten(w[0]).lower() for w in span) == phrase and all(
                    text[left.end():right.start()].strip(" \t") == ""
                    for left, right in zip(span, span[1:])
                ):
                    match = span, arabic
                    break
        if match is not None:
            span, arabic = match
            pieces.append(arabic)
            cursor = span[-1].end()
            index += len(span)
            continue
        try:
            token = word[0]
            pieces.append(token if token.isdecimal() else predict(shorten(token) if repair else token))
        except ValueError:
            pieces.append(word[0])
        cursor = word.end()
        index += 1
    pieces.append(text[cursor:])
    return "".join(pieces)


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
