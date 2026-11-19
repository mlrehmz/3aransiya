"""Shared development data, vocabulary, and batch encoding for the model pilot."""

from dataclasses import dataclass
from hashlib import sha256
import json
import unicodedata

import torch
from torch.nn.utils.rnn import pad_sequence

from validation_benchmark import ARTIFACT_SHA256, V2_ARTIFACT_SHA256

PAD = 0
UNK = 1
MAX_INPUT_LENGTH = 18
MAX_TARGET_LENGTH = 17
CTC_EXPANSION = 9
DATASETS = {"v1": ARTIFACT_SHA256, "v2": V2_ARTIFACT_SHA256}
V2_MISALIGNED = {(265842, 7), (419166, 13)}


@dataclass(frozen=True)
class Vocabulary:
    input_chars: tuple[str, ...]
    target_chars: tuple[str, ...]

    @classmethod
    def from_training(cls, pairs):
        inputs = set()
        targets = set()
        for pair in pairs:
            inputs.update(pair["latin"])
            targets.update(pair["arabic"])
        return cls(tuple(sorted(inputs)), tuple(sorted(targets)))

    def input_ids(self):
        return {char: index for index, char in enumerate(self.input_chars, start=2)}

    def target_ids(self):
        return {char: index for index, char in enumerate(self.target_chars, start=1)}

    def encode_input(self, word):
        ids = self.input_ids()
        return [ids.get(char, UNK) for char in unicodedata.normalize("NFC", word)]


@dataclass(frozen=True)
class Batch:
    inputs: torch.Tensor
    input_lengths: torch.Tensor
    targets: torch.Tensor
    target_lengths: torch.Tensor


def check_pair(input_length, target, expansion):
    if not 1 <= input_length <= MAX_INPUT_LENGTH:
        raise ValueError(f"input length {input_length} outside 1–{MAX_INPUT_LENGTH}")
    if not 1 <= len(target) <= MAX_TARGET_LENGTH:
        raise ValueError(f"target length {len(target)} outside 1–{MAX_TARGET_LENGTH}")
    repeated = sum(left == right for left, right in zip(target, target[1:]))
    required = len(target) + repeated
    available = input_length * expansion
    if required > available:
        raise ValueError(f"target requires {required} CTC frames, only {available} available")


def collate(pairs, vocabulary, *, ctc_expansion=CTC_EXPANSION):
    """Build padded batch-first tensors with unpadded CPU lengths.

    Target characters start at 1. Zero is padding outside target lengths
    and represents blank only in CTC model outputs.
    """
    inputs, targets = [], []
    input_ids = vocabulary.input_ids()
    target_ids = vocabulary.target_ids()
    for pair in pairs:
        latin = unicodedata.normalize("NFC", pair["latin"])
        arabic = pair["arabic"]
        check_pair(len(latin), arabic, ctc_expansion)
        try:
            target = [target_ids[char] for char in arabic]
        except KeyError as error:
            raise ValueError(f"target character {error.args[0]!r} absent from training vocabulary") from error
        targets.append(torch.tensor(target, dtype=torch.long))
        inputs.append(torch.tensor([input_ids.get(char, UNK) for char in latin], dtype=torch.long))
    if not inputs:
        raise ValueError("cannot collate an empty batch")
    return Batch(
        inputs=pad_sequence(inputs, batch_first=True, padding_value=PAD),
        input_lengths=torch.tensor([len(row) for row in inputs]),
        targets=pad_sequence(targets, batch_first=True, padding_value=PAD),
        target_lengths=torch.tensor([len(row) for row in targets]),
    )


@dataclass(frozen=True)
class DevelopmentData:
    training: list
    validation_forms: tuple[str, ...]
    vocabulary: Vocabulary
    validation: tuple = ()


def load_development_data(path, *, version="v1"):
    """Verify the artifact and preflight both candidates on every training pair."""
    data = path.read_bytes()
    if sha256(data).hexdigest() != DATASETS[version]:
        raise ValueError(f"word-pair artifact does not match the {version} digest")

    pairs = json.loads(data)["pairs"]
    training = pairs["train"]
    if version == "v2":
        training = [pair for pair in training if not (
            pair["source"] == "doda_grounded" and (pair["record"], pair["token"]) in V2_MISALIGNED
        )]
        removed = len(pairs["train"]) - len(training)
        if removed != len(V2_MISALIGNED):
            raise ValueError("unexpected v2 alignment exclusion count")
        print(f"Excluded {removed} reviewed boundary errors from both models", flush=True)
    for pair in training:
        try:
            check_pair(len(pair["latin"]), pair["arabic"], CTC_EXPANSION)
        except ValueError as error:
            raise ValueError(f"training record {pair['record']} token {pair['token']}: {error}") from error
    return DevelopmentData(
        training=training,
        validation_forms=tuple(sorted({pair["latin"] for pair in pairs["validation"]})),
        vocabulary=Vocabulary.from_training(training),
        validation=tuple(pairs["validation"]),
    )
