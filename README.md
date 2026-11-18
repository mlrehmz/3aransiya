# 3aransiya

An offline GNOME scratchpad for typing Moroccan Darija in Latin characters and Arabizi, then copying the Arabic-script result. The project is in corpus exploration.

## Verified target machine

| Component | Detected |
| --- | --- |
| Operating system | Fedora Linux 45 |
| Desktop | GNOME Shell 51.1 |
| Display session | Wayland |
| Processor | Intel Core i5-8250U, x86-64 |

Verified on 18 November 2026 using `/etc/os-release`, `gnome-shell --version`, `XDG_SESSION_TYPE`, and `lscpu`.

## Project notes

- [DODa data exploration](docs/01-doda-data-exploration.md) records the pinned source, candidate word-pair coverage, and the effect of lowercasing.
- [DODa sentence split](docs/02-doda-sentence-split.md) records the grouping rule, comparison of two candidates, and the locked v2 assignment.
- Dependency versions will be pinned when the corresponding implementation is added.

Original project code is available under the [MIT License](LICENSE). The external DODa corpus is [CC BY-NC 4.0](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE).
