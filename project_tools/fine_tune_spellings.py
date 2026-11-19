"""Test spelling augmentation with human Darija replay on Fedora."""

import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import random

import torch

from project_tools.compare_model_routes import human_references
from model_pilot.bundle import load_bundle, write_bundle
from model_pilot.data import DATASETS, collate, load_development_data
from model_pilot.train import source_digest, validate


PROBES = {
    "X7al": "شحال", "xrebt": "شربت", "ch7al": "شحال", "chrebt": "شربت",
    "khobz": "خبز", "5obz": "خبز", "khouya": "خويا", "REX": "ريكس",
    "ra2y": "رأي", "mas2oul": "مسؤول", "ms2oul": "مسؤول", "so2": "سوء",
    "kas": "كاس", "o": "و",
}
HELD_OUT_STEMS = ("7al", "reb", "rb")


def spelling_examples(rows):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row["latin"]][row["arabic"]] += 1
    _, lexicon = human_references(rows)
    examples = {"Xa": "شا", "xa": "شا", "ka2s": "كاس", "sport": "سپور"}
    for word, target in sorted(lexicon.items()):
        if not word.startswith("ch") or not target.startswith("ش"):
            continue
        stem = word[2:]
        if not stem or stem.startswith(HELD_OUT_STEMS):
            continue
        for variant in ("x" + stem, "X" + stem):
            existing = counts.get(variant)
            if existing is None or set(existing) == {target}:
                examples.setdefault(variant, target)
    return [{"latin": word, "arabic": target} for word, target in sorted(examples.items())]


def probe_predictions(predictor):
    outputs = {}
    for word in (*PROBES, "Xa", "ka2s", "sport", "prizontasyon", "2o"):
        try:
            outputs[word] = predictor.predict(word)
        except ValueError:
            outputs[word] = None
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    torch.set_num_threads(2)
    torch.manual_seed(42)
    rng = random.Random(42)
    data = load_development_data(args.dataset, version="v2")
    predictor = load_bundle(args.bundle)
    model, vocab = predictor._model, predictor._vocabulary
    data = replace(data, vocabulary=vocab)
    inputs, targets = set(vocab.input_chars), set(vocab.target_chars)
    human = [row for row in data.training if row["source"] == "doda_human"
             and set(row["latin"]) <= inputs and set(row["arabic"]) <= targets]
    examples = [row for row in spelling_examples(human)
                if set(row["latin"]) <= inputs and set(row["arabic"]) <= targets]
    if len(examples) < 8:
        raise ValueError("bundle vocabulary supports fewer than eight correction pairs")
    pairs = {"train": data.training, "validation": data.validation}
    args.output.mkdir(parents=True, exist_ok=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0002)
    checkpoints = (0, 32, 128)
    revision = sha256((source_digest() + sha256(Path(__file__).read_bytes()).hexdigest()).encode()).hexdigest()
    print(f"{len(examples)} spelling pairs with human replay", flush=True)

    for step in range(checkpoints[-1] + 1):
        if step in checkpoints:
            # Serialize once so the validation report and exported bundle share an identity.
            checkpoint = args.output / f"step-{step}.pt"
            torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(), "step": step},
                       checkpoint)
            digest = sha256(checkpoint.read_bytes()).hexdigest()
            validation = validate(model, data, pairs, args.output / f"validation-{step}.json",
                                  digest, torch.device("cpu"), 128, preserve_v1_slices=True)
            probes = probe_predictions(predictor)
            report = {"held_out_correct": sum(probes[w] == a for w, a in PROBES.items()),
                      "held_out_total": len(PROBES), "predictions": probes}
            (args.output / f"probes-{step}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
            if step:
                bundle = args.output / f"bundle-step-{step}"
                write_bundle(bundle, "gru_encoder_decoder_v1", vocab, model,
                             source_checkpoint_sha256=digest, word_pairs_sha256=DATASETS["v2"],
                             source_revision=revision)
                assert probe_predictions(load_bundle(bundle)) == probes
            print(f"step {step}: overall {validation['slices']['overall']['strict_accuracy']:.2%}, "
                  f"held out {report['held_out_correct']}/{len(PROBES)}", flush=True)
        if step == checkpoints[-1]:
            break
        model.train()
        batch = collate(rng.sample(human, 120) + rng.sample(examples, 8), vocab)
        optimizer.zero_grad(set_to_none=True)
        loss = model.loss(batch)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()


if __name__ == "__main__":
    main()
