# Kaggle GPU runtime check

**18 November 2026 · Documentation review**

Kaggle training and [Fedora CPU inference](08-fedora-cpu-runtime.md) have separate environments. The published Kaggle v173 GPU build uses a Colab GPU base, preserves its PyTorch dependencies, and targets Python 3.13 package paths. This identifies the published build recipe. The exact Python patch version, PyTorch build, driver, and image assigned to a live notebook still need measurement. [Kaggle image releases](https://github.com/Kaggle/docker-python/releases) · [Pinned image recipe](https://github.com/Kaggle/docker-python/blob/6a20e87c19bd8cca659798152419cb785795461e/Dockerfile.tmpl)

PyTorch publishes a CPython 3.13 Linux x86-64 wheel for `torch==2.11.0+cu126`. Its release support matrix includes the T4's Turing architecture. Use this as the proposed GPU pin, subject to live driver and kernel checks. If the notebook already has the required build, reuse it. If it differs, record the observed versions before deciding whether to create an isolated training environment. [CUDA 12.6 wheel index](https://download.pytorch.org/whl/cu126/torch/) · [PyTorch 2.11 architecture matrix](https://dev-discuss.pytorch.org/t/dropping-volta-support-from-cuda-12-8-binaries-for-release-2-11/3290)

## Use one GPU for training

- Request `NvidiaTeslaT4` using the Kaggle CLI accelerator option. It provisions **two T4s**.
- Start the training process with `CUDA_VISIBLE_DEVICES=0` before importing PyTorch. In that process, verify exactly one CUDA device is visible and its name and compute capability match a T4. Use `cuda:0` with one process and no distributed training.
- Record the live Python version, PyTorch version, CUDA build, driver, visible device, and compute capability. Run a GRU forward pass and repeated-target CTC loss and gradient check on synthetic tensors before relying on the runtime for training. [Kaggle CLI accelerator documentation](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) · [PyTorch CUDA environment variables](https://docs.pytorch.org/docs/stable/cuda_environment_variables.html)

## Preflight script and local results

Run [kaggle_preflight.py](../kaggle_preflight.py) as a fresh Python process in the GPU-enabled environment. It sets `CUDA_VISIBLE_DEVICES=0` before importing PyTorch, requires exactly one visible T4 with compute capability 7.5, reads the driver version with `nvidia-smi`, and prints a JSON report after the GRU forward and repeated-target CTC backward checks pass. It returns a failing exit status when a prerequisite or kernel check fails. The script uses synthetic tensors and takes no dataset input. It records the observed PyTorch build for comparison with the proposed pin.

On the Fedora CPU environment, the shared tensor checks passed with finite gradients and CTC loss **1.647918**. Running the GPU entry point there failed as expected with zero visible CUDA devices. All 13 discovered repository tests passed. The [local CPU import warning](08-fedora-cpu-runtime.md#verified-local-environment) about optional NumPy was present again. GPU execution and the live Kaggle version metadata remain unverified.

## Live Kaggle result

The authorized synthetic preflight ran as version 1 of a private notebook. Kaggle reported `enable_gpu=true`, `machine_shape=NvidiaTeslaT4`, and internet disabled. The notebook had no data sources. Kaggle reported image digest `sha256:0717e81990be591f8c5f98f033d29ab23e9ffde057e5b3a6bd4371f93969e962`. [Private notebook]([private notebook URL removed])

The job ended with status `ERROR`. Its log shows a Python 3.13 package path and the preflight message `expected one visible CUDA device, found 0`. The check stopped before running the GPU kernels or writing a runtime report. Notebook settings confirm the request, while the log establishes only what PyTorch could see. The underlying cause remains open.

## Diagnostic run

Version 2 explicitly requested the T4 accelerator again. Kaggle still reported the same image digest, GPU enabled, and `NvidiaTeslaT4`. The notebook completed and wrote the diagnostic report.

| Check | Observed |
| --- | --- |
| Python | 3.13.18 |
| PyTorch | 2.11.0+cpu |
| PyTorch CUDA build | None |
| Initial CUDA and NVIDIA device masks | Unset |
| `nvidia-smi` | Unavailable |
| CUDA devices visible to PyTorch | 0 before and after setting the mask |

The notebook executed with a CPU-only PyTorch build. The image and driver visibility need correction or confirmation before changing Python packages. The observations do not establish whether a physical GPU was assigned to the job. Only synthetic inputs were used.

## Next decision

**Proposed, pending approval:** Explicitly switch the same private notebook to Kaggle's GPU image and select T4 ×2 in the runtime settings, then rerun the synthetic diagnostic. Verify the saved version reports a GPU image and the diagnostic sees a T4 before considering any package installation. [Kaggle GPU image documentation](https://github.com/Kaggle/docker-python)
