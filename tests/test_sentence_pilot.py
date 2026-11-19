from importlib.util import find_spec
import unittest


@unittest.skipUnless(find_spec("torch"), "PyTorch is required")
class SentencePilotTest(unittest.TestCase):
    def test_finite_gradient_and_bounded_decode_on_mixed_lengths(self):
        import torch

        from sentence_pilot.data import Alphabet, encode_batch
        from sentence_pilot.model import SentenceTransformer

        pairs = [("salam", "سلام"), ("labas! / hi", "لاباس! / hi")]
        alphabet = Alphabet.from_pairs(pairs)
        model = SentenceTransformer(alphabet)
        loss = model.loss(*encode_batch(pairs, alphabet))
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        outputs = model.eval().predict([pair[0] for pair in pairs])
        self.assertEqual(len(outputs), len(pairs))
        self.assertTrue(all(len(output) <= 2 * len(pair[0]) + 8 for output, pair in zip(outputs, pairs)))

    def test_normalize_preserves_loanword_accents_and_punctuation(self):
        from sentence_pilot.data import normalize

        self.assertEqual(normalize(" café   سَلَام! "), "café سلام!")
