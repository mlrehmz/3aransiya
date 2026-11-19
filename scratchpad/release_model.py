"""Build and load the offline model used by the 3aransiya release."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from .phrases import shorten


PROFILE_FILES = ("profile.json", "routing.json", "encoder", "ctc")
CORRECTIONS = {"Xa": "شا", "xa": "شا"}


def training_references(rows, source, minimum, agreement, excluded=()):
    counts = defaultdict(Counter)
    for row in rows:
        if row["source"] == source and row["latin"] not in excluded:
            counts[row["latin"]][row["arabic"]] += 1
    lexicon = {}
    for word, alternatives in counts.items():
        winner = min(alternatives, key=lambda ref: (-alternatives[ref], ref))
        support = alternatives[winner]
        if support >= minimum and support * 100 >= alternatives.total() * agreement:
            lexicon[word] = winner
    return set(counts), lexicon


def human_references(rows):
    return training_references(rows, "doda_human", 3, 90)


def routed_predict(word, encoder, ctc, human_forms, lexicon):
    if word in lexicon:
        return lexicon[word]
    if word not in human_forms:
        try:
            return ctc(word)
        except ValueError:
            pass
    return encoder(word)


def file_digest(path):
    return sha256(path.read_bytes()).hexdigest()


def profile_inputs(directory):
    return [directory / name for name in PROFILE_FILES[:2]] + [
        directory / model / name
        for model in PROFILE_FILES[2:] for name in ("manifest.json", "weights.pt")
    ]


def load_profile(directory):
    from model_pilot.bundle import load_bundle, read_bounded
    from model_pilot.data import MAX_INPUT_LENGTH

    directory = Path(directory)
    profile = json.loads(read_bounded(directory / "profile.json", 4096))
    if profile.get("format") != 1:
        raise ValueError("unsupported release model profile")
    routing_bytes = read_bounded(directory / "routing.json", 8_000_000)
    if sha256(routing_bytes).hexdigest() != profile.get("routing_sha256"):
        raise ValueError("routing data checksum mismatch")
    for role, architecture in (("encoder", "gru_encoder_decoder_v1"),
                               ("ctc", "bidirectional_gru_ctc_v1")):
        manifest = read_bounded(directory / role / "manifest.json", 8192)
        if (sha256(manifest).hexdigest() != profile.get(role + "_sha256")
                or json.loads(manifest).get("architecture") != architecture):
            raise ValueError(f"incompatible {role} bundle")

    routing = json.loads(routing_bytes)
    human = frozenset(routing["human_forms"])
    lexicon = routing["lexicon"]
    encoder = load_bundle(directory / "encoder").predict
    ctc = load_bundle(directory / "ctc").predict

    def predict(word):
        word = shorten(word)
        if not 1 <= len(word) <= MAX_INPUT_LENGTH or not word.isalnum():
            raise ValueError("invalid word")
        return routed_predict(word, encoder, ctc, human, lexicon)

    return predict


def build_profile(dataset, encoder, ctc, output):
    from model_pilot.data import load_development_data

    if output.exists():
        raise FileExistsError(output)
    rows = load_development_data(dataset, version="v2").training
    human, lexicon = human_references(rows)
    _, grounded = training_references(rows, "doda_grounded", 5, 90, human)
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temporary:
        directory = Path(temporary) / "profile"
        directory.mkdir()
        for role, source in (("encoder", encoder), ("ctc", ctc)):
            destination = directory / role
            destination.mkdir()
            for name in ("manifest.json", "weights.pt"):
                shutil.copyfile(source / name, destination / name)
        routing = directory / "routing.json"
        routing.write_text(json.dumps(
            {"human_forms": sorted(human), "lexicon": lexicon | grounded | CORRECTIONS},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ), encoding="utf-8")
        (directory / "profile.json").write_text(json.dumps({
            "format": 1,
            "routing_sha256": file_digest(routing),
            "encoder_sha256": file_digest(directory / "encoder/manifest.json"),
            "ctc_sha256": file_digest(directory / "ctc/manifest.json"),
        }, indent=2) + "\n", encoding="utf-8")
        if load_profile(directory)("Xa") != CORRECTIONS["Xa"]:
            raise ValueError("release profile failed its spelling check")
        directory.rename(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="assemble the offline release profile")
    for argument in ("dataset", "encoder", "ctc", "output"):
        build.add_argument(argument, type=Path)
    server = commands.add_parser("serve", help="serve word predictions on local pipes")
    server.add_argument("profile", type=Path)
    args = parser.parse_args()
    import torch

    torch.set_num_threads(1)
    if args.command == "serve":
        from .process_predictor import serve

        predictor = load_profile(args.profile)
        predictor("salam")
        serve(predictor)
    else:
        build_profile(args.dataset, args.encoder, args.ctc, args.output)
        print(args.output)


if __name__ == "__main__":
    main()
