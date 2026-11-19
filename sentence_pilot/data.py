"""Prepare whole-sentence pairs from the frozen human split."""

import csv
from hashlib import sha256
from io import StringIO
import json
import random
import re
import unicodedata

import torch
from torch.nn.utils.rnn import pad_sequence

from project_tools.word_pairs import LOCKED_SHA256


MAX_CHARS = 160
PAD, START, END, UNKNOWN = range(4)
ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
ENGLISH_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def normalize(text):
    return " ".join(ARABIC_MARKS.sub("", unicodedata.normalize("NFC", text)).split())


def read_pairs(sentences, assignment, *, mixed=False):
    manifest_bytes = assignment.read_bytes()
    if sha256(manifest_bytes).hexdigest() != LOCKED_SHA256:
        raise ValueError("assignment digest does not match the locked split")
    manifest = json.loads(manifest_bytes)
    source = sentences.read_bytes()
    if sha256(source).hexdigest() != manifest["source_sha256"]:
        raise ValueError("sentence digest does not match the locked split")

    split_by_record = {row["record"]: row["split"] for row in manifest["assignments"]}
    pairs = {"train": [], "validation": []}
    english = []
    for record, row in enumerate(csv.DictReader(StringIO(source.decode("utf-8-sig"))), 1):
        split = split_by_record[record]
        if split not in pairs:
            continue
        source, target = normalize(row["darija"]), normalize(row["darija_ar"])
        if min(len(source), len(target)) and max(len(source), len(target)) <= MAX_CHARS:
            pairs[split].append((source, target))
        if split == "train":
            words = ENGLISH_WORD.findall(row["eng"])
            if len(words) >= 4:
                english.append(words)

    if mixed:
        rng = random.Random(42)
        for source, target in rng.sample(pairs["train"], len(pairs["train"]) // 8):
            words = rng.choice(english)
            length = rng.randint(4, min(10, len(words)))
            start = rng.randrange(len(words) - length + 1)
            english_span = " ".join(words[start:start + length])
            if rng.randrange(2):
                pair = source + " / " + english_span, target + " / " + english_span
            else:
                pair = english_span + " / " + source, english_span + " / " + target
            if max(map(len, pair)) <= MAX_CHARS:
                pairs["train"].append(pair)
    return pairs


class Alphabet:
    def __init__(self, chars):
        self.chars = tuple(chars)
        self.ids = {char: index for index, char in enumerate(self.chars, 4)}

    @classmethod
    def from_pairs(cls, pairs):
        return cls(sorted({char for pair in pairs for text in pair for char in text}))

    def encode(self, text):
        return torch.tensor([self.ids.get(char, UNKNOWN) for char in text] + [END])

    def decode(self, tokens):
        return "".join(self.chars[token - 4] if token >= 4 else "�" for token in tokens)


def batches(pairs, batch_size, seed):
    rng = random.Random(seed)
    order = rng.sample(range(len(pairs)), len(pairs))
    block = batch_size * 32
    chunks = []
    for offset in range(0, len(order), block):
        bucket = sorted(order[offset:offset + block], key=lambda i: max(map(len, pairs[i])))
        chunks.extend(bucket[start:start + batch_size] for start in range(0, len(bucket), batch_size))
    rng.shuffle(chunks)
    return chunks


def encode_batch(pairs, alphabet):
    source, target = zip(*pairs)
    return (
        pad_sequence([alphabet.encode(text) for text in source], batch_first=True),
        pad_sequence([alphabet.encode(text) for text in target], batch_first=True),
    )
