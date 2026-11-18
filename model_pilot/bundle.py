"""Write and load the v1 offline inference bundle."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unicodedata

import torch

from model_pilot.data import CTC_EXPANSION, MAX_INPUT_LENGTH, MAX_TARGET_LENGTH, Vocabulary
from model_pilot.encoder_decoder import EncoderDecoder
from model_pilot.gru_ctc import GruCtc

ARCHITECTURES = {
    "gru_encoder_decoder_v1": (EncoderDecoder, None),
    "bidirectional_gru_ctc_v1": (GruCtc, CTC_EXPANSION),
}
MANIFEST_LIMIT = 32 * 1024
WEIGHTS_LIMIT = 8 * 1024 * 1024
DIGEST_FIELDS = ("weights_sha256", "source_checkpoint_sha256", "word_pairs_sha256")


def read_bounded(path, limit):
    with path.open("rb") as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError(f"{path.name} exceeds the bundle size limit")
    return content


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ValueError("bundle manifest must be a JSON object")
    for field, expected in {
        "format_version": 1,
        "normalization": "nfc_case_sensitive_v1",
        "max_input_length": MAX_INPUT_LENGTH,
        "max_target_length": MAX_TARGET_LENGTH,
    }.items():
        value = manifest.get(field)
        if type(value) is not type(expected) or value != expected:
            raise ValueError(f"unsupported bundle {field}")

    name = manifest.get("architecture")
    if not isinstance(name, str) or name not in ARCHITECTURES:
        raise ValueError("unsupported bundle architecture")
    model_type, expansion = ARCHITECTURES[name]
    value = manifest.get("ctc_expansion")
    if "ctc_expansion" not in manifest or type(value) is not type(expansion) or value != expansion:
        raise ValueError("unsupported bundle ctc_expansion")

    vocabularies = []
    for field in ("input_chars", "target_chars"):
        chars = manifest.get(field)
        if not isinstance(chars, list) or not chars or any(
            not isinstance(char, str) or len(char) != 1 or char.isspace()
            or unicodedata.normalize("NFC", char) != char
            for char in chars
        ) or len(set(chars)) != len(chars):
            raise ValueError(f"invalid bundle {field}")
        vocabularies.append(tuple(chars))

    for field in DIGEST_FIELDS:
        digest = manifest.get(field)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"invalid bundle {field}")
    for field in ("source_revision", "export_torch_version"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing bundle {field}")
    return model_type, Vocabulary(*vocabularies)


class BundlePredictor:
    def __init__(self, model, vocabulary):
        self._model = model
        self._vocabulary = vocabulary

    def predict(self, word):
        ids = self._vocabulary.encode_input(word)
        if not 1 <= len(ids) <= MAX_INPUT_LENGTH or any(char.isspace() for char in word):
            raise ValueError("invalid input word length or whitespace")
        output, = self._model.greedy(torch.tensor([ids]), torch.tensor([len(ids)]))
        if output is None:
            raise ValueError("model produced no usable word")
        return output


def load_bundle(directory):
    """Load the verified bytes from a trusted project bundle onto CPU."""
    directory = Path(directory)
    manifest = json.loads(read_bounded(directory / "manifest.json", MANIFEST_LIMIT).decode("utf-8"))
    model_type, vocabulary = validate_manifest(manifest)
    content = read_bounded(directory / "weights.pt", WEIGHTS_LIMIT)
    if sha256(content).hexdigest() != manifest["weights_sha256"]:
        raise ValueError("weights checksum mismatch")

    model = model_type(vocabulary)
    state = torch.load(BytesIO(content), map_location="cpu", weights_only=True)
    expected = model.state_dict()
    if not isinstance(state, dict) or state.keys() != expected.keys():
        raise ValueError("incompatible weight tensor names")
    for name, tensor in state.items():
        if (type(tensor) is not torch.Tensor or tensor.layout != torch.strided
                or tensor.device.type != "cpu" or tensor.dtype != torch.float32
                or tensor.shape != expected[name].shape or not tensor.isfinite().all()):
            raise ValueError(f"incompatible tensor: {name}")
    model.load_state_dict(state, strict=True)
    model.eval()
    return BundlePredictor(model, vocabulary)


def write_bundle(directory, architecture, vocabulary, model, *,
                 source_checkpoint_sha256, word_pairs_sha256, source_revision):
    """Export a restored model into a new directory and return the manifest digest."""
    destination = Path(directory)
    if architecture not in ARCHITECTURES:
        raise ValueError("unsupported bundle architecture")
    model_type, expansion = ARCHITECTURES[architecture]
    if type(model) is not model_type or model.vocabulary != vocabulary:
        raise ValueError("model does not match the supplied architecture or vocabulary")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)

    manifest = {
        "format_version": 1,
        "architecture": architecture,
        "input_chars": list(vocabulary.input_chars),
        "target_chars": list(vocabulary.target_chars),
        "normalization": "nfc_case_sensitive_v1",
        "max_input_length": MAX_INPUT_LENGTH,
        "max_target_length": MAX_TARGET_LENGTH,
        "ctc_expansion": expansion,
        "source_checkpoint_sha256": source_checkpoint_sha256,
        "word_pairs_sha256": word_pairs_sha256,
        "source_revision": source_revision,
        "export_torch_version": str(torch.__version__),
    }
    with TemporaryDirectory(dir=destination.parent) as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        weights = staging / "weights.pt"
        torch.save({
            key: tensor.detach().to(device="cpu", dtype=torch.float32)
            for key, tensor in model.state_dict().items()
        }, weights)
        manifest["weights_sha256"] = sha256(read_bounded(weights, WEIGHTS_LIMIT)).hexdigest()
        content = (json.dumps(manifest, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        (staging / "manifest.json").write_bytes(content)
        load_bundle(staging)
        staging.rename(destination)
    return sha256(content).hexdigest()
