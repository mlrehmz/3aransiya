from base64 import b64encode
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from textwrap import wrap
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

files = sorted(Path("model_pilot").glob("*.py")) + [Path("validation_benchmark.py")]
archive = BytesIO()
with ZipFile(archive, "w", ZIP_DEFLATED) as output:
    for file in files:
        output.writestr(ZipInfo(file.as_posix()), file.read_bytes(), compress_type=ZIP_DEFLATED)
source = archive.getvalue()
encoded = "\n".join(f"    {line!r}" for line in wrap(b64encode(source).decode(), 96))
cells = [
    ("intro", "markdown", """# 3aransiya · resumable Colab T4 pilot

Train the GRU encoder–decoder and bidirectional GRU/CTC on the same development corpus. The code is embedded in this notebook. The locked test stays closed.

1. Put the prepared `doda-word-pairs-v1.json` in the `3aransiya` folder in your private Google Drive.
2. In Colab choose **Runtime → Change runtime type → T4 GPU**, then run all cells.
3. After a disconnect, select the same runtime, reconnect Drive, and rerun with the same run name and training settings. Completed candidates skip training. Run one session per run folder.

The default saves after each optimizer step. If Drive writes become a bottleneck, increase `SAVE_EVERY` and accept replay of unsaved steps. The two checkpoint slots survive typical interrupted writes. Drive can still lose writes it hasn't synchronized.

[Colab runtime and Drive limits](https://research.google.com/colaboratory/faq.html)
"""),
    ("settings", "code", """from pathlib import Path
from google.colab import drive

drive.mount("/content/drive")
DRIVE_ROOT = Path("/content/drive/MyDrive/3aransiya")
RUN_NAME = "t4-pilot-v1"
CANDIDATES = ["gru_encoder_decoder_v1", "bidirectional_gru_ctc_v1"]
EPOCHS = 2
BATCH_SIZE = 128
SEED = 42
SAVE_EVERY = 1
STEPS_THIS_SESSION = None  # e.g. 100 to stop after 100 additional batches per candidate
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
WORD_PAIRS = LOCAL / "doda-word-pairs-v1.json"
if not WORD_PAIRS.exists() or sha256(WORD_PAIRS.read_bytes()).hexdigest() != EXPECTED_DATA:
    prepared = DRIVE_ROOT / WORD_PAIRS.name
    if not prepared.is_file():
        raise FileNotFoundError(f"Put the prepared development artifact at {{prepared}}")
    content = prepared.read_bytes()
    if sha256(content).hexdigest() != EXPECTED_DATA:
        raise ValueError("The prepared word-pair artifact has the wrong checksum")
    WORD_PAIRS.write_bytes(content)

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
    ("train", "code", """import os
import subprocess
import sys

for architecture in CANDIDATES:
    run = DRIVE_ROOT / "runs" / RUN_NAME / architecture
    command = [
        sys.executable, "-m", "model_pilot.train", str(WORD_PAIRS), str(run),
        "--architecture", architecture, "--epochs", str(EPOCHS),
        "--batch-size", str(BATCH_SIZE), "--seed", str(SEED), "--save-every", str(SAVE_EVERY),
    ]
    if STEPS_THIS_SESSION is not None:
        command.extend(["--steps-this-session", str(STEPS_THIS_SESSION)])
    subprocess.run(command, cwd=LOCAL, env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"}, check=True)
"""),
    ("results", "markdown", """## Results

Look under `3aransiya/runs/<RUN_NAME>/<architecture>/` in Drive. Each finished candidate writes `validation.json` and prints the verified bundle directory and manifest SHA-256. Download the complete `bundle-…` directory for Fedora.

Keep the same code, Python, PyTorch, GPU type, and training settings when resuming. A changed runtime or configuration stops with an error to prevent a silent continuation under different assumptions. The two architectures have independent checkpoints.
"""),
]
notebook_cells = []
for id_, kind, body in cells:
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
Path("notebooks/colab_t4_pilot.ipynb").write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n")
