"""Screen grounded DODa-500K rows and record reproducible candidate counts."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import file_digest
import json
from pathlib import Path

from sentence_split import sentence_keys, write_manifest
from validation_benchmark import ARTIFACT_SHA256
from word_pairs import LOCKED_SHA256, digit_anchor, has_script, tokenize

SOURCE_SHA256 = "76bf4df07676eb2ccadd1ed26a7c23ddd633794f6abb8e6c8e05aa93d1fa000a"


def verify(path, expected):
    with path.open("rb") as stream:
        actual = file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"{path.name}: checksum mismatch")
    return actual


def keys(latin, arabic):
    left, right = sentence_keys(latin, arabic)
    return tuple(word.lower() for word in left), right


def human_keys(path, assignments):
    splits = {entry["record"]: entry["split"] for entry in assignments}
    left, right = defaultdict(set), defaultdict(set)
    with path.open(encoding="utf-8-sig", newline="") as source:
        for number, row in enumerate(csv.DictReader(source), 1):
            split = splits.get(number, "rejected")
            lk, rk = keys(row["darija"], row["darija_ar"])
            left[lk].add(split)
            right[rk].add(split)
    return left, right


def screen(latin, arabic):
    lt, at = latin.split(), arabic.split()
    if not lt or len(lt) != len(at):
        return "unequal_space_count", ()
    left = [list(tokenize(token)) for token in lt]
    right = [list(tokenize(token, strip_marks=True)) for token in at]
    if any(len(group) != 1 for group in (*left, *right)):
        return "non_single_token", ()
    pairs = [(l[0][0], r[0][0]) for l, r in zip(left, right)]
    if not all(
        digit_anchor(l, r) or (has_script(l, "LATIN") and has_script(r, "ARABIC LETTER"))
        for l, r in pairs
    ):
        return "incompatible_script_or_number", ()
    return None, pairs


def has_shift(pairs, form_counts, reference_counts):
    for offset in (-1, 1):
        previous = -2
        for index, (latin, arabic) in enumerate(pairs):
            neighbor = index + offset
            if (
                0 <= neighbor < len(pairs)
                and form_counts[latin] >= 20
                and not reference_counts[latin, arabic]
                and reference_counts[latin, pairs[neighbor][1]] >= 2
            ):
                if previous + 1 == index and pairs[previous][0] != latin:
                    return True
                previous = index
    return False


def build(source, human, locked, v1):
    anchored = Counter((p["latin"], p["arabic"]) for p in v1)
    form_counts = Counter()
    for (latin, _), count in anchored.items():
        form_counts[latin] += count
    human_left, human_right = human_keys(human, locked["assignments"])
    totals, overlaps, word_pairs = Counter(), Counter(), Counter()
    seen = set()
    accepted = []
    with source.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            row = json.loads(line)
            if row["generation_mode"] != "doda_grounded":
                continue
            totals["grounded_rows"] += 1
            latin, arabic = row["darija_latin"], row["darija_arabic"]
            lk, rk = keys(latin, arabic)
            matching = human_left.get(lk, set()) | human_right.get(rk, set())
            if matching:
                totals["human_overlap"] += 1
                overlaps.update(matching)
                continue
            if (lk, rk) in seen:
                totals["duplicate_sentence"] += 1
                continue
            seen.add((lk, rk))
            error, pairs = screen(latin, arabic)
            if error:
                totals[error] += 1
                continue
            if has_shift(pairs, form_counts, anchored):
                totals["shifted_sentence"] += 1
                continue
            candidates = [
                (l, r) for l, r in pairs
                if not digit_anchor(l, r) and 1 <= len(l) <= 18 and 1 <= len(r) <= 17
            ]
            if not candidates:
                totals["no_eligible_word_pairs"] += 1
                continue
            accepted.append(number)
            word_pairs.update(candidates)
    assert len(accepted) + sum(count for key, count in totals.items() if key != "grounded_rows") == totals["grounded_rows"]
    targets = Counter(latin for latin, _ in word_pairs)
    merged = word_pairs.keys() | anchored.keys()
    combined_targets = Counter(latin for latin, _ in merged)
    return {
        "rule": "doda-grounded-whitespace-shift-v1",
        "source_sha256": SOURCE_SHA256,
        "human_sha256": locked["source_sha256"],
        "locked_assignment_sha256": LOCKED_SHA256,
        "v1_artifact_sha256": ARTIFACT_SHA256,
        "row_counts": {**totals, "accepted": len(accepted)},
        "overlapping_human_splits": overlaps,
        "grounded": {
            "occurrences": word_pairs.total(),
            "distinct_pairs": len(word_pairs),
            "distinct_pairs_new_to_v1": len(word_pairs.keys() - anchored.keys()),
            "distinct_latin_forms": len(targets),
            "latin_forms_with_conflicts": sum(count > 1 for count in targets.values()),
        },
        "combined_with_v1": {
            "occurrences": word_pairs.total() + anchored.total(),
            "distinct_pairs": len(merged),
            "distinct_latin_forms": len(combined_targets),
            "latin_forms_with_conflicts": sum(count > 1 for count in combined_targets.values()),
        },
        "accepted_source_lines": accepted,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("human", type=Path)
    parser.add_argument("assignment", type=Path)
    parser.add_argument("v1", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.resolve() in {p.resolve() for p in (args.source, args.human, args.assignment, args.v1)}:
        parser.error("output must differ from the input paths")
    verify(args.source, SOURCE_SHA256)
    verify(args.assignment, LOCKED_SHA256)
    verify(args.v1, ARTIFACT_SHA256)
    locked = json.loads(args.assignment.read_bytes())
    verify(args.human, locked["source_sha256"])
    manifest = build(args.source, args.human, locked, json.loads(args.v1.read_bytes())["pairs"]["train"])
    write_manifest(args.output, manifest)
    print(json.dumps({key: value for key, value in manifest.items() if key != "accepted_source_lines"}, indent=2))


if __name__ == "__main__":
    main()
