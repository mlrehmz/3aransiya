# 3aransiya

**An offline Arabizi scratchpad for Moroccan Darija on GNOME.**

[![Watch the 3aransiya demo](demo/demo1.gif)](demo/demo1.mp4)

[Open or download the demo video](demo/demo1.mp4).

## What it does

- Runs locally on Fedora using a compact offline model profile.
- Uses nearby words to resolve some Darija spelling choices.
- Preserves recognized English and French clauses in their original script.
- Renders a small set of reviewed phrases, including common formal Arabic expressions.
- Copies the selected text or full draft. Press **Ctrl+S** to clear the draft.

The current build combines a character GRU, a CTC fallback, high-agreement spelling lookups, contextual spelling rules learned from human Darija sentences, and reviewed phrase rules.

## Evaluation

The locked DODa test measures word predictions and routing. Contextual rendering was evaluated separately on development sentences and mixed-language probes. These scores describe different evaluations.

| Measure | Previous word release | Current contextual release |
|---|---:|---:|
| Locked word test, strict accuracy | 81.02% | **82.27%** |
| Locked test words still unseen in v2 training | 49.65% | **52.16%** |
| Development sentences exactly matched | 203 / 512 | **204 / 512** |
| English and French probe spans preserved | 0 / 5 | **5 / 5** |

The locked test scores cover word predictions. Sentence accuracy and foreign-span preservation come from separate development checks, not the locked test. The user's mixed Darija, formal Arabic, and English example now renders as follows.

> [redacted Darija sample], علمت عنه من خلال قراءتي بعض كتب , [redacted English sample]

On the Fedora Intel Core i5-8250U, median word prediction was 0.93 ms, excluding model startup, process communication, and GTK rendering. See the [locked model evaluation](docs/31-release.md) and [contextual evaluation and limits](docs/33-contextual-extension.md).

## Get started on Fedora

The verified setup is Fedora 45, GNOME Shell 51.1, and Wayland. From the repository root, install the system GTK bindings, create the pinned CPU environment, and install its dependencies.

```sh
sudo dnf install gtk4 python3-gobject
uv venv --python 3.14.8 --managed-python .venv
UV_CACHE_DIR=data/uv-cache uv sync --locked
```

Build the base model profile as described in the [reproduction guide](docs/31-release.md#reproduce-the-model). Add the contextual rules, install the extension, then enable it.

```sh
.venv/bin/python -m project_tools.build_context_profile \
  outputs/3aransiya-release data/doda-word-pairs-v1.json outputs/3aransiya-contextual
/usr/bin/python extension/install.py --profile outputs/3aransiya-contextual
gnome-extensions enable scratchpad@3aransiya
```

Log out and back in if GNOME has not discovered the extension. Keep the checkout and model profile in place because the launcher uses them. You can launch the scratchpad directly.

```sh
/usr/bin/python -m scratchpad --profile outputs/3aransiya-contextual
```

The repository contains model code, notebooks, and tools, but not the licensed training corpus or trained weights. Follow the data preparation and training steps in the [reproduction guide](docs/31-release.md#reproduce-the-model) before building a profile. To run the CPU test suite, use `.venv/bin/python -m unittest discover -s tests`.

## Research and engineering

The project documents corpus exploration, leakage-aware splits, alignment screening, resumable Colab and CPU training, model comparisons, and a sentence-level Transformer experiment. The Transformer pilot did not outperform the word-level model. The final build uses constrained context-based spelling choices and preserves recognized foreign-language clauses.

- [Data and split decisions](docs/01-doda-data-exploration.md)
- [CPU training pilot](docs/27-fedora-cpu-training-pilot.md)
- [Locked word evaluation](docs/31-release.md)
- [Contextual extension evaluation](docs/33-contextual-extension.md)
- [Sentence Transformer pilot](docs/32-sentence-transformer-pilot.md)

## Data and license

Original project code is available under the [MIT License](LICENSE). DODa is provided by its maintainers under [CC BY-NC 4.0](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE). Corpus files and trained profiles are local build artifacts and are not included in this repository.

General MSA transliteration, short or unpunctuated language switches, and unfamiliar spellings such as `prizontasyon` remain limitations. Contextual results come from a small development sample and need broader speaker review.
