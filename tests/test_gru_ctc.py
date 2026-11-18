from importlib.util import find_spec
import unittest


@unittest.skipUnless(find_spec("torch"), "PyTorch is required for model pilot tests")
class GruCtcTest(unittest.TestCase):
    def test_mixed_lengths_and_blank_separated_repeats(self):
        import torch

        from model_pilot.data import Vocabulary, collate
        from model_pilot.gru_ctc import GruCtc

        rows = [{"latin": "T7", "arabic": "طط"}, {"latin": "t", "arabic": "ت"}]
        vocab = Vocabulary.from_training(rows)
        batch = collate(rows, vocab)
        single = collate(rows[1:], vocab)
        model = GruCtc(vocab).eval()

        logits, lengths = model(batch.inputs, batch.input_lengths)
        self.assertEqual(logits.shape, (2, 18, 3))
        self.assertEqual(lengths.tolist(), [18, 9])
        single_logits, _ = model(single.inputs, single.input_lengths)
        torch.testing.assert_close(logits[1, :9], single_logits[0])
        loss = model.loss(batch)
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(all(p.grad is not None and p.grad.isfinite().all() for p in model.parameters()))

        with torch.no_grad():
            model.output.weight.zero_()
            bias = model.output.bias.reshape(9, 3)
            bias.zero_()
            for frame, token in enumerate([2, 2, 0, 2, 2, 0, 0, 0, 0]):
                bias[frame, token] = 1
        self.assertEqual(model.greedy(batch.inputs, batch.input_lengths), ["طططط", "طط"])

        with torch.no_grad():
            bias.zero_()
            for frame in range(9):
                bias[frame, 1 + frame % 2] = 1
        longer = collate([{"latin": "TT7", "arabic": "طط"}, rows[1]], vocab)
        self.assertEqual(model.greedy(longer.inputs, longer.input_lengths), [None, "تطتطتطتطت"])

        with torch.no_grad():
            model.output.bias.zero_()
        self.assertEqual(model.greedy(batch.inputs, batch.input_lengths), [None, None])
