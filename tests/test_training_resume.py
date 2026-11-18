from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(find_spec("torch"), "PyTorch is required for model pilot tests")
class TrainingResumeTest(unittest.TestCase):
    def test_interruption_and_torn_slot_resume_both_candidates(self):
        import torch

        from model_pilot.bundle import ARCHITECTURES
        from model_pilot.data import DevelopmentData, Vocabulary
        from model_pilot.train import Schedule, train

        rows = [
            {"latin": "T7", "arabic": "طط"},
            {"latin": "t", "arabic": "ت"},
            {"latin": "7", "arabic": "ح"},
            {"latin": "tt", "arabic": "تت"},
            {"latin": "h", "arabic": "ح"},
        ]
        data = DevelopmentData(rows, (), Vocabulary.from_training(rows))
        schedule = Schedule(2, 2, 42)
        for architecture in ARCHITECTURES:
            with self.subTest(architecture=architecture), TemporaryDirectory() as temp:
                root = Path(temp)
                first, second = root / "first", root / "second"
                first.mkdir()
                second.mkdir()
                args = (schedule, torch.device("cpu"), "fixed-fixture")
                uninterrupted, _, _, total = train(data, architecture, first, *args)
                _, checkpoint, step, _ = train(data, architecture, second, *args, step_limit=2)
                self.assertEqual((step, total), (2, 6))
                self.assertEqual(checkpoint.generation, 2)
                _, checkpoint, step, _ = train(data, architecture, second, *args, step_limit=1)
                self.assertEqual((step, checkpoint.generation), (3, 3))
                (second / "checkpoint-1.bin").write_bytes(b"incomplete")
                resumed, checkpoint, step, _ = train(data, architecture, second, *args)
                self.assertEqual((step, checkpoint.generation), (6, 6))
                for name, expected in uninterrupted.state_dict().items():
                    torch.testing.assert_close(resumed.state_dict()[name], expected, rtol=0, atol=0)
                digest = checkpoint.digest()
                _, checkpoint, step, _ = train(data, architecture, second, *args)
                self.assertEqual(step, 6)
                self.assertEqual(checkpoint.digest(), digest)

    def test_resume_retries_epoch_validation_before_training_more_batches(self):
        import torch

        from model_pilot.data import DevelopmentData, Vocabulary
        from model_pilot.train import Schedule, train

        rows = [{"latin": "t", "arabic": "ت"}]
        data = DevelopmentData(rows, (), Vocabulary.from_training(rows))
        args = (Schedule(2, 1, 42), torch.device("cpu"), "validation-fixture")
        with TemporaryDirectory() as temp:
            root = Path(temp)
            attempts = []

            def interrupted(epoch, model, digest):
                self.assertTrue((root / "checkpoint-1.bin").is_file())
                attempts.append((epoch, digest))
                raise InterruptedError("validation interrupted")

            with self.assertRaises(InterruptedError):
                train(data, "gru_encoder_decoder_v1", root, *args, on_epoch=interrupted)

            def record(epoch, model, digest):
                attempts.append((epoch, digest))

            _, _, step, _ = train(data, "gru_encoder_decoder_v1", root, *args, on_epoch=record)
            self.assertEqual(step, 2)
            self.assertEqual([epoch for epoch, _ in attempts], [1, 1, 2])
            self.assertEqual(attempts[0], attempts[1])
            self.assertNotEqual(attempts[1][1], attempts[2][1])
