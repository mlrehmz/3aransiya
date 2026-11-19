"""Render reviewed expressions and keep all other text on the word path."""

import re


LATIN_TOKEN = re.compile(r"[A-Za-z0-9]+")
ELONGATION = re.compile(r"([A-Za-z])\1{2,}")
PHRASES = {
    ("salla", "llaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wa", "sallam"): "صلى الله عليه وسلم",
    ("asba7na", "wa", "asbaha", "lmolko", "lilah"): "أصبحنا وأصبح الملك لله",
}
PHRASE_LENGTHS = sorted({len(phrase) for phrase in PHRASES}, reverse=True)


def shorten(word):
    return ELONGATION.sub(r"\1\1", word)


def render_text(text, word_output, *, phrases=False):
    if not phrases:
        return LATIN_TOKEN.sub(word_output, text)

    words = list(LATIN_TOKEN.finditer(text))
    normalized = [shorten(word[0]).lower() for word in words]
    pieces = []
    cursor = index = 0
    while index < len(words):
        word = words[index]
        pieces.append(text[cursor:word.start()])
        for length in PHRASE_LENGTHS:
            output = PHRASES.get(tuple(normalized[index:index + length]))
            span = words[index:index + length]
            if output and all(
                not text[left.end():right.start()].strip(" \t")
                for left, right in zip(span, span[1:])
            ):
                pieces.append(output)
                cursor = span[-1].end()
                index += length
                break
        else:
            pieces.append(word_output(word))
            cursor = word.end()
            index += 1
    pieces.append(text[cursor:])
    return "".join(pieces)
