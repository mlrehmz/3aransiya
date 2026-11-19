"""Build a contextual profile from the existing local release and pinned human pairs."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from scratchpad.context import learn_context, load_context
from validation_benchmark import ARTIFACT_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("base", "human_pairs", "destination"):
        parser.add_argument(argument, type=Path)
    args = parser.parse_args()
    if args.destination.exists():
        parser.error("destination already exists")
    pairs_bytes = args.human_pairs.read_bytes()
    if sha256(pairs_bytes).hexdigest() != ARTIFACT_SHA256:
        parser.error("human pair checksum mismatch")
    rows = json.loads(pairs_bytes)["pairs"]["train"]
    table = learn_context(rows)

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.destination.parent) as temporary:
        directory = Path(temporary) / "profile"
        copytree(args.base, directory)
        data = json.dumps([(*key, value) for key, value in sorted(table.items())],
                          ensure_ascii=False, separators=(",", ":")).encode()
        (directory / "context.json").write_bytes(data)
        manifest = directory / "profile.json"
        fields = json.loads(manifest.read_text())
        fields["context_sha256"] = sha256(data).hexdigest()
        manifest.write_text(json.dumps(fields, indent=2) + "\n")
        if load_context(directory) != table:
            raise ValueError("context profile did not round-trip")
        directory.rename(args.destination)
    print(f"Wrote {len(table):,} context rules to {args.destination}")


if __name__ == "__main__":
    main()
