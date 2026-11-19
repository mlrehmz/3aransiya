# Fedora CPU runtime check

**18 November 2026 · Wheel compatibility verified**

The target runs Fedora 45 on x86-64 with glibc 2.44 and a system Python 3.15.2. The i5-8250U reports AVX2 and FMA. The host already has uv 0.13.1. These values came from `python -VV`, `getconf GNU_LIBC_VERSION`, `lscpu`, and `uv --version`.

The official CPU index lists `torch-2.11.0+cpu-cp314-cp314-manylinux_2_28_x86_64.whl`. Its x86-64 and glibc 2.28 minimum match the target, and its CPython 3.14 ABI requires a separate 3.14 interpreter. PyTorch 2.11.0 has no CPython 3.15 wheel in that index. [Official CPU wheel index](https://download.pytorch.org/whl/cpu/torch/) · [PyTorch 2.11 installation instructions](https://pytorch.org/get-started/previous-versions/)

## Recommended pin

Use standard CPython **3.14** in a project-local virtual environment and install **`torch==2.11.0+cpu`** from the official CPU wheel index. Use the existing uv installation to provision the interpreter and environment. Record the exact Python patch version and resolved dependency versions after installation. The pilot requires only PyTorch from the PyTorch package family.

This check verified the published wheel tags against the host. Installation, import, and execution of GRU and CTC kernels remain to be verified.

## Verified local environment

Provisioned CPython **3.14.8** with uv and installed **PyTorch 2.11.0+cpu** in the ignored `.venv/`. The root `pyproject.toml` declares the direct dependency and `uv.lock` pins the resolved environment. Reproduce from the repository root:

```sh
uv venv --python 3.14.8 --managed-python .venv
uv sync --locked
```

Verified the exact Python and PyTorch versions and the CPU-only build. At one inference thread, a bidirectional GRU forward pass returned finite tensors with the expected shapes. CTC loss and gradients were finite for a repeated target with three available frames. The dependency check and all five discovered tests passed. PyTorch emitted an optional NumPy import warning. The checked tensor operations succeeded without NumPy.

This environment supports Fedora inference development, latency measurement, and resumable CPU training. Synthetic tensors were used for the runtime preflight.
