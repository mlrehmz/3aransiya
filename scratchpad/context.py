"""Small word-context table and conservative foreign-clause detection."""

from collections import Counter, defaultdict
from hashlib import sha256
import json
import re
from unicodedata import name


# A single loanword is weak evidence. Require markers from a complete clause.
MARKERS = (
    frozenset("i we you they am is are was will would could have has not yet the this that "
              "please send there tomorrow with today because what how where when from".split()),
    frozenset("je tu nous vous suis sommes êtes avec dans déjà là demain très pour merci "
              "pourquoi quand comment chez vraiment peux veux vais rappelle".split()),
)
FOREIGN_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
CLAUSE_BREAK = re.compile(r"[,،;؛.!?؟:\n]+")


def foreign_clause(text):
    words = FOREIGN_WORD.findall(text)
    if len(words) < 3:
        return False
    if any(char.isdigit() for char in text):
        return False
    if any(not all(char in "'’" or "LATIN" in name(char, "") for char in word) for word in words):
        return False
    forms = {word.lower() for word in words}
    return any(len(forms & markers) >= 2 and len(forms & markers) * 3 >= len(words) for markers in MARKERS)


def foreign_spans(text):
    start = 0
    for separator in CLAUSE_BREAK.finditer(text):
        if foreign_clause(text[start:separator.start()]):
            yield start, separator.start()
        start = separator.end()
    if foreign_clause(text[start:]):
        yield start, len(text)


def learn_context(rows):
    counts = defaultdict(Counter)
    neighbors = defaultdict(Counter)
    by_position = {(row["record"], row["token"]): row for row in rows}
    for row in rows:
        word, target = row["latin"], row["arabic"]
        counts[word][target] += 1
        for direction in (-1, 1):
            neighbor = by_position.get((row["record"], row["token"] + direction))
            if neighbor is not None:
                neighbors[direction, word, neighbor["latin"]][target] += 1
    context = {}
    for key, variants in neighbors.items():
        _, word, _ = key
        if len(counts[word]) < 2:
            continue
        preferred, support = variants.most_common(1)[0]
        if support >= 4 and support * 10 >= variants.total() * 9 and counts[word][preferred] >= 4:
            context[key] = preferred
    return context


def context_choice(context, word, left, right):
    before = context.get((-1, word, left))
    after = context.get((1, word, right))
    if before and after and before != after:
        return None
    return before or after


def load_context(profile):
    manifest = json.loads((profile / "profile.json").read_text())
    if "context_sha256" not in manifest:
        return None
    path = profile / "context.json"
    with path.open("rb") as stream:
        payload = stream.read(1_000_001)
    if len(payload) > 1_000_000 or sha256(payload).hexdigest() != manifest["context_sha256"]:
        raise ValueError("context data checksum mismatch")
    return {(direction, word, neighbor): target
            for direction, word, neighbor, target in json.loads(payload)}
