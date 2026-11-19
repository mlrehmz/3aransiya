"""Extract candidate word pairs from the locked DODa development splits."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import unicodedata as ud

from project_tools.sentence_split import write_manifest

LOCKED_SHA256 = "c4b55713980227c36695b3f946b1a186cb9544e1702a7e98908dcb0e351dd58e"
DEVELOPMENT_SPLITS = ("train", "validation")
EXCLUDED = {
    (19156, 1), (13084, 3), (2102, 2), (12919, 2),
    (44345, 3), (13215, 1), (25219, 6), (31963, 0),
}


def tokenize(text, *, strip_marks=False):
    """Yield normalized values and half-open character offsets into the source."""
    start = None
    for index, char in enumerate(text + " "):
        if char.isalnum() or (start is not None and ud.category(char).startswith("M")):
            if start is None:
                start = index
        elif start is not None:
            value = ud.normalize("NFC", text[start:index])
            if strip_marks:
                value = "".join(char for char in value if ud.category(char) != "Mn")
            yield value, [start, index]
            start = None


def has_script(word, script):
    names = [ud.name(char, "") for char in word]
    return any(script in name for name in names) and all(
        script in name or char in "0123456789"
        for char, name in zip(word, names)
    )


def digit_anchor(latin, arabic):
    return latin == arabic and latin.isascii() and latin.isdecimal()


def extract(csv_bytes, manifest_bytes, *, final_test=False):
    splits = ("test",) if final_test else DEVELOPMENT_SPLITS
    if sha256(manifest_bytes).hexdigest() != LOCKED_SHA256:
        raise ValueError("assignment manifest does not match the locked digest")
    manifest = json.loads(manifest_bytes)
    if sha256(csv_bytes).hexdigest() != manifest["source_sha256"]:
        raise ValueError("source checksum does not match the locked manifest")

    development = {
        row["record"]: row["split"]
        for row in manifest["assignments"] if row["split"] in splits
    }
    pairs = {split: [] for split in splits}
    counts = {split: Counter() for split in splits}
    targets = {split: defaultdict(set) for split in splits}
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"), newline=""))
    for record, row in enumerate(reader, 1):
        split = development.get(record)
        if split is None:
            continue
        tally = counts[split]
        tally["source_sentences"] += 1
        latin = list(tokenize(row["darija"]))
        arabic = list(tokenize(row["darija_ar"], strip_marks=True))
        if len(latin) != len(arabic):
            tally["unequal_token_count"] += 1
            continue
        aligned = list(zip(latin, arabic))
        if not aligned or not all(
            digit_anchor(left, right) or (
                has_script(left, "LATIN") and has_script(right, "ARABIC LETTER")
            )
            for (left, _), (right, _) in aligned
        ):
            tally["incompatible_scripts"] += 1
            continue

        tally["screened_sentences"] += 1
        for index, ((left, left_span), (right, right_span)) in enumerate(aligned):
            if digit_anchor(left, right):
                tally["digit_anchors"] += 1
                continue
            if split == "train" and (record, index) in EXCLUDED:
                tally["review_exclusions"] += 1
                continue
            pairs[split].append({
                "record": record, "token": index, "latin": left, "arabic": right,
                "latin_span": left_span, "arabic_span": right_span,
            })
            targets[split][left].add(right)

    for split in splits:
        tally = counts[split]
        tally["pairs"] = len(pairs[split])
        tally["distinct_latin"] = len(targets[split])
        tally["conflicting_latin"] = sum(len(values) > 1 for values in targets[split].values())
    return {
        "rule": "doda-word-pairs-test-v1" if final_test else "doda-word-pairs-v1",
        "assignment_sha256": LOCKED_SHA256,
        "source_sha256": manifest["source_sha256"],
        "counts": counts,
        "pairs": pairs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("assignment", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.output.resolve() in {args.source.resolve(), args.assignment.resolve()}:
            raise ValueError("output must differ from the input paths")
        result = extract(args.source.read_bytes(), args.assignment.read_bytes())
        write_manifest(args.output, result)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
