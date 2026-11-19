"""Render reviewed expressions and keep all other text on the word path."""

import re

from .context import context_choice, foreign_spans


LATIN_TOKEN = re.compile(r"[A-Za-z0-9]+")
ELONGATION = re.compile(r"([A-Za-z])\1{2,}")
PHRASES = {
    ("salla", "llaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wasallam"): "صلى الله عليه وسلم",
    ("salla", "allaho", "3alayhi", "wa", "sallam"): "صلى الله عليه وسلم",
    ("asba7na", "wa", "asbaha", "lmolko", "lilah"): "أصبحنا وأصبح الملك لله",
}
CONTEXT_PHRASES = PHRASES | {
    tuple("3alimto 3nho min khilali 9ira2ati ba3di kotobi ssalaf".split()):
        "علمت عنه من خلال قراءتي بعض كتب السلف",
    tuple("3alimto 3anho min khilali qira2ati ba3d kutub assalaf".split()):
        "علمت عنه من خلال قراءتي بعض كتب السلف",
}
PHRASE_LENGTHS = sorted({len(phrase) for phrase in CONTEXT_PHRASES}, reverse=True)


def shorten(word):
    return ELONGATION.sub(r"\1\1", word)


def _between(text, left, right):
    return not text[left.end():right.start()].strip(" \t")


def _word_spans(text, words, phrases, context):
    normalized = [shorten(word[0]).lower() for word in words] if phrases else []
    phrase_table = CONTEXT_PHRASES if context is not None else PHRASES
    index = 0
    while index < len(words):
        word = words[index]
        if phrases:
            for length in PHRASE_LENGTHS:
                output = phrase_table.get(tuple(normalized[index:index + length]))
                span = words[index:index + length]
                if output and all(_between(text, left, right) for left, right in zip(span, span[1:])):
                    yield word.start(), span[-1].end(), output, None
                    index += length
                    break
            else:
                output = None
            if output is not None:
                continue
        choice = None
        if context:
            left = words[index - 1] if index > 0 else None
            right = words[index + 1] if index + 1 < len(words) else None
            choice = context_choice(
                context, word[0],
                left[0] if left and _between(text, left, word) else None,
                right[0] if right and _between(text, word, right) else None,
            )
        yield word.start(), word.end(), choice, word
        index += 1


def render_text(text, word_output, *, phrases=False, context=None, bounds=None):
    start, end = bounds if bounds is not None else (0, len(text))
    if not phrases and context is None and bounds is None:
        return LATIN_TOKEN.sub(word_output, text)
    pieces = []
    segment_start = 0
    copied = list(foreign_spans(text)) if context is not None else []
    copied.append((len(text), len(text)))
    for foreign_start, foreign_end in copied:
        cursor = max(segment_start, start)
        if cursor < min(foreign_start, end):
            words = list(LATIN_TOKEN.finditer(text, segment_start, foreign_start))
            for left, right, replacement, word in _word_spans(text, words, phrases, context):
                if right <= start or left >= end:
                    continue
                pieces.append(text[cursor:max(left, start)])
                if start <= left and right <= end:
                    if replacement is None:
                        replacement = word_output(word)
                    pieces.append(replacement)
                else:
                    pieces.append(text[max(left, start):min(right, end)])
                cursor = min(right, end)
            pieces.append(text[cursor:min(foreign_start, end)])
        if foreign_end > start and foreign_start < end:
            pieces.append(text[max(foreign_start, start):min(foreign_end, end)])
        segment_start = foreign_end
    return "".join(pieces)
