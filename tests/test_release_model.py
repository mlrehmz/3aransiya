import unittest

from scratchpad.context import context_choice, foreign_clause, learn_context
from scratchpad.phrases import render_text
from scratchpad.release_model import routed_predict, training_references


class ReleaseModelTest(unittest.TestCase):
    def test_phrase_boundaries_and_unmodified_separators(self):
        text = "123, sallllllla llllaho 3alayhi wasallam!\nsalla, allaho 3alayhi wasallam"
        actual = render_text(text, lambda m: m[0], phrases=True)
        self.assertEqual(actual, "123, صلى الله عليه وسلم!\nsalla, allaho 3alayhi wasallam")
        text = "asba7na wa asbaha lmolko lilah"
        self.assertEqual(render_text(text, lambda m: m[0], phrases=True), "أصبحنا وأصبح الملك لله")
        text = "salla\nallaho 3alayhi wasallam"
        self.assertEqual(render_text(text, lambda m: m[0], phrases=True), text)

    def test_context_preserves_code_switches_and_selection(self):
        text = "salam, I will be there tomorrow.\nje suis déjà là, wach nta 9rib?"
        word = lambda match: {"salam": "سلام", "wach": "واش", "nta": "نتا", "9rib": "قريب"}[match[0]]
        expected = "سلام, I will be there tomorrow.\nje suis déjà là, واش نتا قريب?"
        self.assertEqual(render_text(text, word, phrases=True, context={}), expected)
        start = text.index("will")
        self.assertEqual(render_text(text, word, phrases=True, context={},
                                     bounds=(start, start + len("will be"))), "will be")
        self.assertFalse(foreign_clause("wach nta 9rib"))
        self.assertFalse(foreign_clause("salam labas ach khbark"))
        self.assertFalse(foreign_clause("lfilm"))

    def test_context_repairs_formal_phrase_without_crossing_punctuation(self):
        draft = "3alimto 3nho min khilali 9ira2ati ba3di kotobi ssalaf"
        word = lambda match: match[0]
        self.assertEqual(render_text(draft, word, phrases=True, context={}),
                         "علمت عنه من خلال قراءتي بعض كتب السلف")
        interrupted = draft.replace("min ", "min, ")
        self.assertEqual(render_text(interrupted, word, phrases=True, context={}), interrupted)

    def test_adjacent_context_requires_support_and_resolves_conflicts(self):
        examples = [
            {"record": record, "token": token, "latin": latin, "arabic": arabic}
            for record in range(8)
            for token, (latin, arabic) in enumerate(
                (("a", "أ"), ("f", "في")) if record < 4 else (("b", "ب"), ("f", "ف"))
            )
        ]
        context = learn_context(examples)
        self.assertEqual(context_choice(context, "f", "a", None), "في")
        self.assertIsNone(context_choice(context, "f", "c", None))
        context[1, "f", "c"] = "ف"
        self.assertIsNone(context_choice(context, "f", "a", "c"))

    def test_grounded_lookup_requires_support_and_keeps_human_forms(self):
        rows = [{"source": "doda_grounded", "latin": "kas", "arabic": "كاس"}] * 5
        rows += [{"source": "doda_grounded", "latin": "hak", "arabic": "هاك"}] * 4
        rows += [{"source": "doda_grounded", "latin": "dar", "arabic": "دار"}] * 6
        _, lookups = training_references(rows, "doda_grounded", 5, 90, {"dar"})
        self.assertEqual(lookups, {"kas": "كاس"})

    def test_routing_uses_one_model_and_recovers_from_empty_ctc(self):
        def encoder(word):
            return "encoder"

        def ctc(word):
            if word == "empty":
                raise ValueError("empty output")
            return "ctc"

        args = encoder, ctc, {"known"}, {"exact": "lookup"}
        self.assertEqual(routed_predict("exact", *args), "lookup")
        self.assertEqual(routed_predict("known", *args), "encoder")
        self.assertEqual(routed_predict("novel", *args), "ctc")
        self.assertEqual(routed_predict("empty", *args), "encoder")
