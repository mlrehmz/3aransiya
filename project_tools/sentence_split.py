"""Assign whole DODa sentence groups to deterministic data splits."""

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import tempfile
import unicodedata

RULES = ("v1", "v2")
LOWERCASE_LATIN = "lowercase_latin"
FIELDS = ("darija", "darija_ar")
SPLITS = ("train", "validation", "test")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def sentence_keys(latin, arabic):
    latin = unicodedata.normalize("NFC", latin)
    arabic = unicodedata.normalize("NFC", arabic)
    arabic = "".join(char for char in arabic if unicodedata.category(char) != "Mn")
    return tuple(tuple(re.findall(r"[^\W_]+", text)) for text in (latin, arabic))


def split_for(rule, records):
    digest = sha256(canonical([rule, records])).digest()
    bucket = int.from_bytes(digest[:8], "big") % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def build_manifest(data, expected_checksum, version="v1"):
    rule = f"doda-sentence-split-{version}"
    grouping_keys = (*FIELDS, LOWERCASE_LATIN) if version == "v2" else FIELDS
    checksum = sha256(data).hexdigest()
    if checksum != expected_checksum:
        raise ValueError(f"source checksum mismatch: got {checksum}")

    source = io.StringIO(data.decode("utf-8-sig"), newline="")
    reader = csv.DictReader(source, strict=True)
    fields = reader.fieldnames or []
    if any(fields.count(field) != 1 for field in FIELDS):
        raise ValueError("CSV must contain one darija and one darija_ar column")

    parents = {}
    first_records = {}
    keys_by_record = {}
    rejected = []

    def root(record):
        while parents[record] != record:
            parents[record] = parents[parents[record]]
            record = parents[record]
        return record

    for record, row in enumerate(reader, 1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"wrong column count in record {record}")
        keys = sentence_keys(*(row[field] for field in FIELDS))
        if not all(keys):
            rejected.append({"record": record, "reason": "empty key"})
            continue

        keys_by_record[record] = (*keys, tuple(token.lower() for token in keys[0]))
        parents[record] = record
        for field, key in zip(grouping_keys, keys_by_record[record]):
            first = first_records.setdefault((field, key), record)
            first_root, current_root = root(first), root(record)
            parents[max(first_root, current_root)] = min(first_root, current_root)

    if not parents:
        raise ValueError("CSV contains no accepted records")

    components = defaultdict(list)
    for record in parents:
        components[root(record)].append(record)
    group_splits = {group: split_for(rule, records) for group, records in components.items()}

    assignments = []
    assignments_by_split = {split: [] for split in SPLITS}
    key_splits = {field: defaultdict(set) for field in (*FIELDS, LOWERCASE_LATIN)}
    for record, keys in keys_by_record.items():
        group = root(record)
        split = group_splits[group]
        assignment = {"record": record, "group": group, "split": split}
        assignments.append(assignment)
        assignments_by_split[split].append(assignment)
        for field, key in zip(key_splits, keys):
            key_splits[field][key].add(split)

    overlap = {
        field: sum(len(splits) > 1 for splits in matches.values())
        for field, matches in key_splits.items()
    }
    if any(overlap[field] for field in grouping_keys):
        raise ValueError("sentence key appears in more than one split")

    group_counts = Counter(group_splits.values())
    return {
        "source_sha256": checksum,
        "rule": rule,
        "status": "candidate",
        "assignments": assignments,
        "rejected": rejected,
        "group_size_histogram": dict(Counter(str(len(rows)) for rows in components.values())),
        "overlapping_keys": overlap,
        "splits": {
            split: {
                "groups": group_counts[split],
                "sentences": len(rows),
                "sha256": sha256(canonical(rows)).hexdigest(),
            }
            for split, rows in assignments_by_split.items()
        },
    }


def write_manifest(destination, manifest):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temp_path = Path(output.name)
            output.write(canonical(manifest) + b"\n")
        temp_path.replace(destination)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--rule", choices=RULES, default="v1")
    args = parser.parse_args()
    try:
        if args.source.resolve() == args.manifest.resolve():
            raise ValueError("source and manifest must use different paths")
        manifest = build_manifest(args.source.read_bytes(), args.sha256.lower(), args.rule)
        write_manifest(args.manifest, manifest)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
