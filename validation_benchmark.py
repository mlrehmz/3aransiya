"""Score fixed word predictions on the v1 DODa validation occurrences."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import unicodedata

ARTIFACT_SHA256 = "842ba2460f0d4219cb90a41cca0cdc079d18fd1146d6756a9562833c9f2fbfbb"
PILOT_SPELLINGS = {
    "m3a": {"مع", "معا"},
    "kayna": {"كاينة", "كاينا"},
    "f": {"ف", "في"},
    "imta": {"إمتا", "امتا"},
    "achno": {"أشنو", "اشنو", "آشنو"},
    "hiya": {"هي", "هيا"},
    "lma": {"الما", "لما", "الماء"},
    "lhadra": {"لهدرا", "لهادرا"},
}
SLICES = ("common", "overall", "unseen")


def normalize_arabic(text):
    return "".join(
        char for char in unicodedata.normalize("NFC", text)
        if unicodedata.category(char) != "Mn"
    )


def benchmark(pairs, predictions=None):
    training = defaultdict(Counter)
    for pair in pairs["train"]:
        training[pair["latin"]][pair["arabic"]] += 1
    common_order = sorted(training, key=lambda word: (-training[word].total(), word))[:500]
    common = set(common_order)
    if predictions is None:
        predictions = {
            word: min(counts, key=lambda ref: (-counts[ref], ref))
            for word, counts in training.items()
        }

    predictions = {word: normalize_arabic(output) for word, output in predictions.items()}
    counts = {
        name: dict(occurrences=0, strict_correct=0, variant_correct=0, missing=0)
        for name in SLICES
    }
    covered = {name: set() for name in SLICES}
    for pair in pairs["validation"]:
        word, reference = pair["latin"], pair["arabic"]
        output = predictions.get(word)
        strict = output == reference
        alternatives = PILOT_SPELLINGS.get(word, ())
        variant = strict or (output in alternatives and reference in alternatives)
        slices = ["overall"]
        if word in common:
            slices.append("common")
        if word not in training:
            slices.append("unseen")
        for name in slices:
            result = counts[name]
            result["occurrences"] += 1
            result["strict_correct"] += strict
            result["variant_correct"] += variant
            result["missing"] += output is None
            covered[name].add(word)

    for name, result in counts.items():
        result["distinct_forms"] = len(covered[name])
        for metric in ("strict", "variant"):
            total = result["occurrences"]
            result[f"{metric}_accuracy"] = result[f"{metric}_correct"] / total if total else None

    return {"common_forms": len(common), "slices": counts}


def read_predictions(path):
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict) or any(not isinstance(value, str) for value in payload.values()):
        raise ValueError("predictions must be a JSON object mapping Latin forms to strings")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("word_pairs", type=Path)
    parser.add_argument("--predictions", type=Path, help="JSON object mapping Latin forms to outputs")
    args = parser.parse_args()
    try:
        data = args.word_pairs.read_bytes()
        if sha256(data).hexdigest() != ARTIFACT_SHA256:
            raise ValueError("word-pair artifact does not match the v1 digest")
        predictions = read_predictions(args.predictions) if args.predictions else None
        report = benchmark(json.loads(data)["pairs"], predictions)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
