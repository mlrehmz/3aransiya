from importlib.util import find_spec
import unittest


@unittest.skipUnless(find_spec("torch"), "PyTorch is required for model pilot tests")
class ModelDataTest(unittest.TestCase):
    def test_training_vocabulary_padding_and_repeated_target_preflight(self):
        from model_pilot.data import Vocabulary, collate

        training = [
            {"latin": "T7", "arabic": "طط"},
            {"latin": "t", "arabic": "ت"},
        ]
        vocab = Vocabulary.from_training(training)
        batch = collate(training, vocab)
        self.assertEqual(batch.inputs.tolist(), [[3, 2], [4, 0]])
        self.assertEqual(batch.input_lengths.tolist(), [2, 1])
        self.assertEqual(batch.targets.tolist(), [[2, 2], [1, 0]])
        self.assertEqual(batch.target_lengths.tolist(), [2, 1])
        self.assertEqual(vocab.encode_input("T?"), [3, 1])
        with self.assertRaisesRegex(ValueError, "requires 3 CTC frames"):
            collate(training, vocab, ctc_expansion=1)
