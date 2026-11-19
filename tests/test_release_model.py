import unittest

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
