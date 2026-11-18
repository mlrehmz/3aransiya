from importlib.util import find_spec
import unittest


@unittest.skipUnless(find_spec("torch"), "PyTorch is required for model pilot tests")
class EncoderDecoderTest(unittest.TestCase):
    def test_mixed_lengths_and_end_of_sequence(self):
        import torch

        from model_pilot.data import Vocabulary, collate
        from model_pilot.encoder_decoder import EncoderDecoder

        rows = [{"latin": "T7", "arabic": "طط"}, {"latin": "t", "arabic": "ت"}]
        vocab = Vocabulary.from_training(rows)
        batch = collate(rows, vocab)
        single = collate(rows[1:], vocab)
        model = EncoderDecoder(vocab).eval()
        logits = model(batch)
        self.assertEqual(tuple(logits.shape), (2, 3, 5))
        torch.testing.assert_close(logits[1, :2], model(single)[0])
        loss = model.loss(batch)
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(all(p.grad is not None and p.grad.isfinite().all() for p in model.parameters()))

        with torch.no_grad():
            model.output.weight.zero_()
            model.output.bias.zero_()
            model.output.bias[model.eos] = 1
        steps = []
        handle = model.output.register_forward_hook(lambda *args: steps.append(1))
        try:
            self.assertEqual(model.greedy(batch.inputs, batch.input_lengths), [None, None])
            self.assertEqual(len(steps), 1)
            steps.clear()
            with torch.no_grad():
                model.output.bias.zero_()
                model.output.bias[1] = 1
            self.assertEqual(model.greedy(batch.inputs, batch.input_lengths), [None, None])
            self.assertEqual(len(steps), 18)
        finally:
            handle.remove()

        def end_at_bound(module, args, output):
            steps.append(1)
            if len(steps) == 18:
                output[..., model.eos] = 2

        steps.clear()
        handle = model.output.register_forward_hook(end_at_bound)
        try:
            self.assertEqual(model.greedy(batch.inputs, batch.input_lengths), ["ت" * 17] * 2)
        finally:
            handle.remove()
