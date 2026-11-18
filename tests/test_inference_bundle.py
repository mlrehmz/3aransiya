from hashlib import sha256
from importlib.util import find_spec
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from scratchpad.process_predictor import PredictorError, ProcessPredictor


@unittest.skipUnless(find_spec("torch"), "PyTorch is required for model pilot tests")
class InferenceBundleTest(unittest.TestCase):
    def test_roundtrip_both_candidates_through_helper(self):
        import torch

        from model_pilot.bundle import ARCHITECTURES, write_bundle
        from model_pilot.data import Vocabulary
        from model_pilot.encoder_decoder import EncoderDecoder

        vocab = Vocabulary(("t", "T", "7"), ("ت",))
        for arch, (model_type, _) in ARCHITECTURES.items():
            with self.subTest(architecture=arch), TemporaryDirectory() as folder:
                model = model_type(vocab).eval()
                with torch.no_grad():
                    for p in model.parameters():
                        p.zero_()
                    if isinstance(model, EncoderDecoder):
                        model.target_embedding.weight[model.bos, 0] = 1
                        model.decoder.weight_ih_l0[256, 0] = 2
                        model.output.weight[1, 0] = 4
                        model.output.bias[model.eos] = 1.4
                    else:
                        model.output.bias.reshape(9, 2)[:, 1] = 1
                directory = Path(folder) / "bundle"
                digest = write_bundle(
                    directory, arch, vocab, model, source_checkpoint_sha256="0" * 64,
                    word_pairs_sha256="1" * 64, source_revision="synthetic-test",
                )
                self.assertEqual(digest, sha256((directory / "manifest.json").read_bytes()).hexdigest())
                helper = ProcessPredictor([sys.executable, "-m", "model_pilot.inference_helper", directory])
                try:
                    for word in ("T7", "t7" * 9, "T?"):
                        ids = vocab.encode_input(word)
                        expected, = model.greedy(torch.tensor([ids]), torch.tensor([len(ids)]))
                        self.assertEqual(expected, "ت")
                        self.assertEqual(helper.predict(word), expected)
                    with self.assertRaisesRegex(PredictorError, "could not convert"):
                        helper.predict("t" * 19)
                    self.assertEqual(helper.predict("T7"), "ت")
                finally:
                    helper.close()

    def test_invalid_bundles_are_rejected_before_readiness(self):
        import torch

        from model_pilot.bundle import load_bundle, write_bundle
        from model_pilot.data import Vocabulary
        from model_pilot.gru_ctc import GruCtc

        with TemporaryDirectory() as folder:
            directory = Path(folder) / "bundle"
            vocab = Vocabulary(("t",), ("ت",))
            model = GruCtc(vocab)
            write_bundle(
                directory, "bidirectional_gru_ctc_v1", vocab, model,
                source_checkpoint_sha256="0" * 64, word_pairs_sha256="1" * 64,
                source_revision="synthetic-test",
            )
            manifest_path = directory / "manifest.json"
            weights = directory / "weights.pt"
            original = manifest_path.read_bytes()
            manifest = json.loads(original)
            manifest["format_version"] = 2
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "format_version"):
                load_bundle(directory)
            manifest_path.write_bytes(original)

            weights.unlink()
            with self.assertRaises(FileNotFoundError):
                load_bundle(directory)
            weights.write_bytes(b"broken")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_bundle(directory)
            with self.assertRaisesRegex(PredictorError, "exited without a response"):
                ProcessPredictor([sys.executable, "-m", "model_pilot.inference_helper", directory])

            state = model.state_dict()
            state["output.bias"] = torch.zeros(1)
            torch.save(state, weights)
            manifest = json.loads(original)
            manifest["weights_sha256"] = sha256(weights.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "incompatible tensor: output.bias"):
                load_bundle(directory)
