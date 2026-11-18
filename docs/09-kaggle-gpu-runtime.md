# Kaggle GPU runtime check

**18 November 2026 · Documentation review**

Kaggle training and [Fedora CPU inference](08-fedora-cpu-runtime.md) have separate environments. The published Kaggle v173 GPU build uses a Colab GPU base, preserves its PyTorch dependencies, and targets Python 3.13 package paths. This identifies the published build recipe. The exact Python patch version, PyTorch build, driver, and image assigned to a live notebook still need measurement. [Kaggle image releases](https://github.com/Kaggle/docker-python/releases) · [Pinned image recipe](https://github.com/Kaggle/docker-python/blob/6a20e87c19bd8cca659798152419cb785795461e/Dockerfile.tmpl)

PyTorch publishes a CPython 3.13 Linux x86-64 wheel for `torch==2.11.0+cu126`. Its release support matrix includes the T4's Turing architecture. Use this as the proposed GPU pin, subject to live driver and kernel checks. If the notebook already has the required build, reuse it. If it differs, record the observed versions before deciding whether to create an isolated training environment. [CUDA 12.6 wheel index](https://download.pytorch.org/whl/cu126/torch/) · [PyTorch 2.11 architecture matrix](https://dev-discuss.pytorch.org/t/dropping-volta-support-from-cuda-12-8-binaries-for-release-2-11/3290)

## Use one GPU for training

- Request `NvidiaTeslaT4` using the Kaggle CLI accelerator option. It provisions **two T4s**.
- Start the training process with `CUDA_VISIBLE_DEVICES=0` before importing PyTorch. In that process, verify exactly one CUDA device is visible and its name and compute capability match a T4. Use `cuda:0` with one process and no distributed training.
- Record the live Python version, PyTorch version, CUDA build, driver, visible device, and compute capability. Run a GRU forward pass and repeated-target CTC loss and gradient check on synthetic tensors before relying on the runtime for training. [Kaggle CLI accelerator documentation](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) · [PyTorch CUDA environment variables](https://docs.pytorch.org/docs/stable/cuda_environment_variables.html)

## Next decision

**Proposed, pending approval:** Draft and locally check a small Kaggle preflight script that prints the runtime metadata and verifies the one-GPU setup with synthetic tensors. A live Kaggle run would be a separate approval. No Kaggle job, package installation, or corpus upload took place during this documentation check. The [DODa upload terms](01-doda-data-exploration.md#decisions-and-open-questions) remain unresolved.
