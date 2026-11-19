import argparse
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from textwrap import wrap
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

parser = argparse.ArgumentParser(description="Build a Colab training notebook")
parser.add_argument("--v2", action="store_true", help="build the expanded dataset notebook")
parser.add_argument("--human-weighted", action="store_true", help="build the 25%% human v2 experiment")
options = parser.parse_args()

files = sorted(Path("model_pilot").glob("*.py")) + [
    Path(name) for name in (
        "validation_benchmark.py",
        "scratchpad/__init__.py",
        "scratchpad/process_predictor.py",
        "tests/test_training_resume.py",
        "tests/test_inference_bundle.py",
    )
]
archive = BytesIO()
with ZipFile(archive, "w", ZIP_DEFLATED) as output:
    for file in files:
        output.writestr(ZipInfo(file.as_posix()), file.read_bytes(), compress_type=ZIP_DEFLATED)
source = archive.getvalue()
encoded = "\n".join(f"    {line!r}" for line in wrap(b64encode(source).decode(), 96))
cells = [
    ("intro", "markdown", """# 3aransiya · resumable six-epoch Colab comparison

Train the GRU encoder–decoder and bidirectional GRU/CTC on the same development corpus. The code is embedded in this notebook. The locked test stays closed.

1. Upload `doda-word-pairs-v1.json` through Colab’s Files panel so it is at `/content/doda-word-pairs-v1.json`.
2. In Colab choose **Runtime → Change runtime type → T4 GPU**, then run all cells.
3. Outputs go to `/content/outputs/`. Download anything you want to keep before the runtime resets. Rerunning in the same runtime resumes from its newest valid local checkpoint.

The default saves after each optimizer step. A full runtime reset clears local files. To resume on a fresh runtime, upload the dataset and restore the saved `outputs/` folder before rerunning.

[Colab runtime limits](https://research.google.com/colaboratory/faq.html)
"""),
    ("settings", "code", """from pathlib import Path
CONTENT = Path("/content")
OUTPUTS = CONTENT / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)
RUN_NAME = "t4-comparison-6epoch-v1"
CANDIDATES = ["gru_encoder_decoder_v1", "bidirectional_gru_ctc_v1"]
EPOCHS = 6
BATCH_SIZE = 128
SEED = 42
SAVE_EVERY = 1
STEPS_THIS_SESSION = None  # e.g. 100 to stop after 100 additional batches per candidate
RUN_SYNTHETIC_TESTS = True
"""),
    ("inputs", "code", f"""from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

import torch

if not torch.cuda.is_available() or "T4" not in torch.cuda.get_device_name(0).split():
    raise RuntimeError("Select a T4 GPU in Colab Runtime → Change runtime type")
print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))

EXPECTED_DATA = "842ba2460f0d4219cb90a41cca0cdc079d18fd1146d6756a9562833c9f2fbfbb"
LOCAL = Path("/content/3aransiya-pilot")
LOCAL.mkdir(exist_ok=True)
WORD_PAIRS = CONTENT / "doda-word-pairs-v1.json"
if not WORD_PAIRS.is_file():
    raise FileNotFoundError(f"Upload the prepared development artifact to {{WORD_PAIRS}}")
if sha256(WORD_PAIRS.read_bytes()).hexdigest() != EXPECTED_DATA:
    raise ValueError("The prepared word-pair artifact has the wrong checksum")

# Embedded project source snapshot for this notebook.
source = b64decode(
{encoded}
)
assert sha256(source).hexdigest() == "{sha256(source).hexdigest()}"
with ZipFile(BytesIO(source)) as archive:
    for member in archive.namelist():
        path = LOCAL / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(archive.read(member))
"""),
    ("testing_note", "markdown", """## Tests before corpus training

Run the synthetic recovery and bundle tests on CPU. They compare an interrupted run with an uninterrupted run, exercise the fallback after a damaged checkpoint, and check prediction parity and bundle rejection. These tests write only temporary files.
"""),
    ("testing", "code", """import os
import subprocess
import sys

if RUN_SYNTHETIC_TESTS:
    for pattern in ("test_training_resume.py", "test_inference_bundle.py"):
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern],
            cwd=LOCAL,
            env={**os.environ, "OMP_NUM_THREADS": "1", "CUDA_VISIBLE_DEVICES": ""},
            check=True,
        )
"""),
    ("train_note", "markdown", """## Train or resume on T4"""),
    ("train", "code", """import os
import subprocess
import sys

for architecture in CANDIDATES:
    run = OUTPUTS / RUN_NAME / architecture
    command = [
        sys.executable, "-m", "model_pilot.train", str(WORD_PAIRS), str(run),
        "--architecture", architecture, "--epochs", str(EPOCHS),
        "--batch-size", str(BATCH_SIZE), "--seed", str(SEED), "--save-every", str(SAVE_EVERY),
    ]
    if STEPS_THIS_SESSION is not None:
        command.extend(["--steps-this-session", str(STEPS_THIS_SESSION)])
    print()
    print(f"Training or resuming {architecture} → {run}", flush=True)
    with subprocess.Popen(
        command, cwd=LOCAL, env={**os.environ, "CUDA_VISIBLE_DEVICES": "0", "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    ) as process:
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
        except KeyboardInterrupt:
            process.terminate()
            raise
        if process.wait():
            raise subprocess.CalledProcessError(process.returncode, command)
"""),
    ("validation_note", "markdown", """## Validation on held-out development words

The trainer scores both candidates after each epoch on the same validation occurrences. Reports are available after a partial run, too. Strict scores use the retained reference. Variant-aware scores use the twelve pilot spelling equivalences. Missing predictions count as misses in both columns. The locked release test is separate and is reserved for the final selected model.
"""),
    ("validation", "code", """import json

completed = {}
def percent(value):
    return "n/a" if value is None else f"{value:.2%}"

for architecture in CANDIDATES:
    run = OUTPUTS / RUN_NAME / architecture
    epoch_reports = sorted(run.glob("validation-epoch-*.json"))
    print()
    print(architecture)
    if epoch_reports:
        print(f"{'Epoch':>5} {'Slice':<10} {'Strict':>9} {'Variants':>9} {'Missing':>8}")
        for report_path in epoch_reports:
            epoch = int(report_path.stem.rsplit("-", 1)[1])
            slices = json.loads(report_path.read_text())["scores"]["slices"]
            for name in slices:
                scores = slices[name]
                strict = percent(scores["strict_accuracy"])
                variants = percent(scores["variant_accuracy"])
                print(f"{epoch:>5} {name:<10} {strict:>9} {variants:>9} {scores['missing']:>8}")

    report_path = run / "validation.json"
    if not report_path.is_file():
        print(f"{architecture}: final export pending until training completes")
        continue
    report = json.loads(report_path.read_text())
    completed[architecture] = (run, report["checkpoint_sha256"])
    print("Final validation coverage")
    print(f"{'Slice':<10} {'Words':>8} {'Forms':>8} {'Strict':>9} {'Variants':>9} {'Missing':>8}")
    for name, scores in report["scores"]["slices"].items():
        strict = percent(scores["strict_accuracy"])
        variants = percent(scores["variant_accuracy"])
        print(f"{name:<10} {scores['occurrences']:>8} {scores['distinct_forms']:>8} "
              f"{strict:>9} {variants:>9} {scores['missing']:>8}")
"""),
    ("export_note", "markdown", """## Test the exported bundle

Load each completed bundle via the same local pipe protocol the Fedora app uses. Check that a fixed word produces output and that an overlength word is rejected while the helper stays available. This is an integration smoke test. Use the validation table for development accuracy.
"""),
    ("export_test", "code", """for architecture, (run, checkpoint_digest) in completed.items():
    bundle = run / f"bundle-{checkpoint_digest[:16]}"
    subprocess.run(
        [sys.executable, "-c", '''
import json
from pathlib import Path
import sys
from scratchpad.process_predictor import PredictorError, ProcessPredictor

bundle = Path(sys.argv[1])
manifest = json.loads((bundle / "manifest.json").read_text())
if manifest["source_checkpoint_sha256"] != sys.argv[2]:
    raise ValueError("inference bundle does not match the validation checkpoint")
helper = ProcessPredictor([sys.executable, "-m", "model_pilot.inference_helper", bundle])
try:
    for word in ("salam", "T7", "t7" * 9, "kanchouf", "bghit", "3lach"):
        try:
            expected = helper.predict(word)
        except PredictorError:
            if helper.closed:
                raise
            continue
        break
    else:
        raise RuntimeError("no successful prediction on the fixed fixture")
    try:
        helper.predict("t" * 19)
    except PredictorError:
        if helper.closed:
            raise
    else:
        raise RuntimeError("helper accepted an overlength word")
    if helper.predict(word) != expected:
        raise RuntimeError("prediction changed after a rejected request")
finally:
    helper.close()
''', str(bundle), checkpoint_digest],
        cwd=LOCAL,
        env={**os.environ, "CUDA_VISIBLE_DEVICES": ""},
        check=True,
    )
    print(f"{architecture}: exported bundle passed · {bundle}")
"""),
    ("results", "markdown", """## Results and restart

Look under `/content/outputs/<RUN_NAME>/<architecture>/`. Download the complete `bundle-…` directory for Fedora. Each epoch report records the exact checkpoint digest. A restart after an interrupted validation step resumes from the completed epoch’s saved weights.

Keep the same code, Python, PyTorch, GPU type, and training settings when resuming. A changed runtime or configuration stops with an error to prevent a silent continuation under different assumptions. The two architectures have independent checkpoints.
"""),
]
notebook_cells = []
for id_, kind, body in cells:
    if options.v2 or options.human_weighted:
        body = (body.replace("resumable six-epoch Colab comparison", "expanded v2 Colab comparison")
                .replace("doda-word-pairs-v1.json", "doda-word-pairs-v2.json")
                .replace("842ba2460f0d4219cb90a41cca0cdc079d18fd1146d6756a9562833c9f2fbfbb",
                         "0ce61f1d95a6aa9c4932e883e116b82b009d3411149d8e9e6fce852e88a9121e")
                .replace("t4-comparison-6epoch-v1", "t4-v2-one-pass")
                .replace("EPOCHS = 6", "EPOCHS = 1")
                .replace('"--epochs", str(EPOCHS)', '"--dataset-version", "v2", "--epochs", str(EPOCHS)'))
    if options.human_weighted:
        body = (body.replace("expanded v2 Colab comparison", "25% human-data v2 comparison")
                .replace("Train the GRU encoder–decoder and bidirectional GRU/CTC on the same development corpus.",
                         "Train the existing GRU encoder–decoder with 25% human and 75% grounded examples.")
                .replace("t4-v2-one-pass", "t4-v2-human25")
                .replace("then run all cells.", "then run the code cells one at a time in order. Check the setup and synthetic tests before starting training.")
                .replace("upload the dataset and restore the saved `outputs/` folder before rerunning.",
                         "upload the dataset and restore the saved run folder under `/content/outputs/` before rerunning.")
                .replace("# Embedded project source snapshot for this notebook.",
                         'print(f"Dataset verified: {WORD_PAIRS}")\n\n# Embedded project source snapshot for this notebook.')
                .replace('["gru_encoder_decoder_v1", "bidirectional_gru_ctc_v1"]',
                         '["gru_encoder_decoder_v1"]')
                .replace('"--dataset-version", "v2", "--epochs"', '"--dataset-version", "v2", "--human-weighted", "--epochs"')
                .replace("The two architectures have independent checkpoints.",
                         "The sampling report records occurrence exposures and unique rows by source."))
    cell = {"id": id_, "cell_type": kind, "metadata": {}, "source": body.splitlines(keepends=True)}
    if kind == "code":
        compile(body, f"colab:{id_}", "exec")
        cell.update(execution_count=None, outputs=[])
    notebook_cells.append(cell)
notebook = {
    "nbformat": 4, "nbformat_minor": 5, "cells": notebook_cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4"},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    },
}
if options.human_weighted:
    name = "colab_t4_v2_human25.ipynb"
elif options.v2:
    name = "colab_t4_v2.ipynb"
else:
    name = "colab_t4_pilot.ipynb"
Path("notebooks", name).write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n")
