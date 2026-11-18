# Fedora CPU runtime check

**18 November 2026 · Wheel compatibility verified**

The target runs Fedora 45 on x86-64 with glibc 2.44 and a system Python 3.15.2. The i5-8250U reports AVX2 and FMA. The host already has uv 0.13.1. These values came from `python -VV`, `getconf GNU_LIBC_VERSION`, `lscpu`, and `uv --version`.

The official CPU index lists `torch-2.11.0+cpu-cp314-cp314-manylinux_2_28_x86_64.whl`. Its x86-64 and glibc 2.28 minimum match the target, and its CPython 3.14 ABI requires a separate 3.14 interpreter. PyTorch 2.11.0 has no CPython 3.15 wheel in that index. [Official CPU wheel index](https://download.pytorch.org/whl/cpu/torch/) · [PyTorch 2.11 installation instructions](https://pytorch.org/get-started/previous-versions/)

## Recommended pin

Use standard CPython **3.14** in a project-local virtual environment and install **`torch==2.11.0+cpu`** from the official CPU wheel index. Use the existing uv installation to provision the interpreter and environment. Record the exact Python patch version and resolved dependency versions after installation. The pilot requires only PyTorch from the PyTorch package family.

This check verified the published wheel tags against the host. Installation, import, and execution of GRU and CTC kernels remain to be verified.

## Next decision

**Proposed, pending approval:** Provision the isolated CPU environment, verify the version and CPU-only build at import, and run a small GRU forward pass and CTC loss check before implementing the models.
