"""Check the Kaggle runtime on one visible T4 using synthetic tensors."""

import json
import os
import subprocess
import sys


def check_kernels(torch, device):
    gru = torch.nn.GRU(4, 8, batch_first=True, bidirectional=True, device=device)
    sample = torch.zeros(1, 3, 4, device=device)
    with torch.no_grad():
        output, state = gru(sample)
    if output.shape != (1, 3, 16) or state.shape != (2, 1, 8):
        raise RuntimeError("GRU returned unexpected tensor shapes")
    if not (output.isfinite().all() and state.isfinite().all()):
        raise RuntimeError("GRU returned nonfinite values")

    logits = torch.zeros(3, 1, 3, device=device, requires_grad=True)
    targets = torch.tensor([1, 1], device=device)
    loss = torch.nn.CTCLoss()(logits.log_softmax(2), targets, (3,), (2,))
    loss.backward()
    if not (loss.isfinite() and logits.grad.isfinite().all()):
        raise RuntimeError("CTC returned nonfinite loss or gradients")
    return loss.item()


def main():
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    try:
        import torch

        visible = torch.cuda.device_count()
        if visible != 1:
            raise RuntimeError(f"expected one visible CUDA device, found {visible}")
        device = torch.device("cuda:0")
        name = torch.cuda.get_device_name(device)
        capability = torch.cuda.get_device_capability(device)
        if "T4" not in name.split() or capability != (7, 5):
            raise RuntimeError(f"expected an NVIDIA T4 (7.5), found {name} {capability}")

        driver = subprocess.check_output(
            ["nvidia-smi", "--id=0", "--query-gpu=driver_version", "--format=csv,noheader"],
            text=True,
            timeout=15,
        ).strip()
        loss = check_kernels(torch, device)
    except (ImportError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"preflight failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps({
        "python": sys.version.split()[0],
        "torch": str(torch.__version__),
        "torch_cuda": torch.version.cuda,
        "driver": driver,
        "visible_devices": visible,
        "device": name,
        "compute_capability": capability,
        "gru_forward": "passed",
        "ctc_loss_and_backward": "passed",
        "ctc_loss": loss,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
