"""Assemble the verified grounded training pool and original validation rows."""

import argparse
from collections import Counter
from hashlib import file_digest
import json
from pathlib import Path
import tempfile

from grounded_manifest import SOURCE_SHA256, screen, verify
from validation_benchmark import ARTIFACT_SHA256
from word_pairs import digit_anchor

MANIFEST_SHA256 = "6b5650ec43ac7eb385addd3d98b658fe44225d76d21c33376b1b326c27c887bd"


def dump(stream, value):
    json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))


def grounded_rows(source, accepted):
    remaining = iter(accepted)
    expected = next(remaining, None)
    with source.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if expected is None:
                break
            if number != expected:
                continue
            row = json.loads(line)
            if row["generation_mode"] != "doda_grounded":
                raise ValueError(f"unexpected generation mode at source line {number}")
            error, pairs = screen(row["darija_latin"], row["darija_arabic"])
            if error is not None:
                raise ValueError(f"accepted source line {number} fails the screen: {error}")
            for token, (latin, arabic) in enumerate(pairs):
                if not digit_anchor(latin, arabic) and 1 <= len(latin) <= 18 and 1 <= len(arabic) <= 17:
                    yield {
                        "latin": latin, "arabic": arabic, "record": number,
                        "token": token, "source": "doda_grounded",
                    }
            expected = next(remaining, None)
    if expected is not None:
        raise ValueError(f"accepted source line {expected} was not found")


def build(source, manifest, v1, destination):
    totals = manifest["combined_with_v1"]
    v1_counts = Counter((row["latin"], row["arabic"]) for row in v1["train"])
    grounded_counts = Counter()
    run_counts = {}
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write('{"rule":"doda-grounded-training-v2","provenance":')
            dump(stream, {
                "grounded_source_sha256": SOURCE_SHA256,
                "grounded_manifest_sha256": MANIFEST_SHA256,
                "v1_artifact_sha256": ARTIFACT_SHA256,
                "record_conventions": {
                    "doda_human": "one-based CSV record after header",
                    "doda_grounded": "one-based JSONL source line",
                },
            })
            stream.write(',"pairs":{"train":[\n')
            for index, row in enumerate(v1["train"]):
                if index:
                    stream.write(",\n")
                dump(stream, {**row, "source": "doda_human"})
            for row in grounded_rows(source, manifest["accepted_source_lines"]):
                grounded_counts[row["latin"], row["arabic"]] += 1
                stream.write(",\n")
                dump(stream, row)
            stream.write('\n],"validation":')
            dump(stream, v1["validation"])
            stream.write('},"pair_counts":[\n')
            unique = v1_counts.keys() | grounded_counts.keys()
            run_counts = {
                "train_human": v1_counts.total(),
                "train_grounded": grounded_counts.total(),
                "train": v1_counts.total() + grounded_counts.total(),
                "validation": len(v1["validation"]),
                "distinct_train_pairs": len(unique),
            }
            if (
                run_counts["train_grounded"] != manifest["grounded"]["occurrences"]
                or run_counts["train"] != totals["occurrences"]
                or len(unique) != totals["distinct_pairs"]
            ):
                raise ValueError("dataset counts do not match the candidate manifest")
            for index, (latin, arabic) in enumerate(sorted(unique)):
                if index:
                    stream.write(",\n")
                dump(stream, {
                    "latin": latin, "arabic": arabic, "human": v1_counts[latin, arabic],
                    "grounded": grounded_counts[latin, arabic],
                })
            stream.write('\n],"counts":')
            dump(stream, run_counts)
            stream.write('}\n')
            stream.close()
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    return run_counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("v1", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.resolve() in {path.resolve() for path in (args.source, args.manifest, args.v1)}:
        parser.error("output must differ from the input paths")
    verify(args.source, SOURCE_SHA256)
    verify(args.manifest, MANIFEST_SHA256)
    verify(args.v1, ARTIFACT_SHA256)
    manifest = json.loads(args.manifest.read_bytes())
    v1 = json.loads(args.v1.read_bytes())["pairs"]
    counts = build(args.source, manifest, v1, args.output)
    with args.output.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    print(json.dumps({"counts": counts, "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
