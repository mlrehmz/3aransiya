# 3aransiya

**An offline Arabizi-to-Arabic scratchpad for Moroccan Darija on GNOME.**

[![Watch the demo](demo/demo1.gif)](demo/demo1.mp4)

The GIF is an 8× speed preview; the linked [video](demo/demo1.mp4) plays at normal speed.

## The project

3aransiya explores a practical question: can people type Moroccan Darija in familiar Latin Arabizi and get useful Arabic-script text immediately, without sending their writing to a server?

The result is a compact GNOME scratchpad that predicts while you type, keeps the source draft available, and lets you copy Arabic output. It preserves supported English and French spans and renders a small, explicitly reviewed set of Arabic phrases. Inference runs locally. The project also includes the data preparation, model experiments, evaluation, and extension code used to build the release.

## How the approach evolved

1. **Build a fast word baseline.** Character-level GRU encoder–decoder and CTC models established a reproducible starting point and exposed weak generalization to spellings missing from training.
2. **Expand the evidence carefully.** The project screened and aligned over one million grounded word occurrences, grouped duplicate sentences before splitting, and kept validation and locked test data separate from training.
3. **Test alternatives and measure limits.** A small sentence Transformer was evaluated for contextual spelling and mixed-language preservation. It did not outperform the simpler word-level system on the sentence checks, so it was not shipped.
4. **Ship a constrained hybrid.** The release combines neural word prediction, high-agreement lookups, local context rules, and a small reviewed phrase set. This kept the interface fast while improving the measured locked word score. It is still a Darija-focused system, not a general Arabic transliterator.

## Results

| Evaluation | Earlier word model | Current release |
| --- | ---: | ---: |
| Locked DODa word test, strict accuracy | 81.02% | **82.27%** |
| Locked test forms still unseen in v2 training | 49.65% | **52.16%** |
| Human development sentences exactly matched | 203 / 512 | **204 / 512** |
| English/French spans preserved in targeted probes | 0 / 5 | **5 / 5** |

The locked test numbers measure word prediction. Sentence accuracy and language-span preservation come from separate development checks; the five preservation probes are too small to estimate broad generalization. On the verified Fedora Intel Core i5-8250U, median warm word prediction was **0.93 ms** and p95 was **2.40 ms**. These timings exclude model startup, process communication, and GTK rendering. The full protocol, slices, and limitations are in the [release evaluation](docs/31-release.md) and [contextual evaluation](docs/33-contextual-extension.md).

## Run locally on Fedora

The verified desktop setup is Fedora 45, GNOME Shell 51.1, and Wayland. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), GTK 4, and PyGObject, then prepare the locked Python environment:

```sh
sudo dnf install gtk4 python3-gobject
uv venv --python 3.14.8 --managed-python .venv
uv sync --locked
```

`pyproject.toml` declares the Python package and pinned CPU PyTorch dependency; `uv.lock` locks the full Python environment. GTK and PyGObject are system packages because the desktop app uses the system GTK runtime.

Run the automated checks:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

To inspect the scratchpad UI without downloading a corpus or model, start the synthetic helper. It returns artificial output for UI checks; it is not a Darija model.

```sh
ARANSIYA_SYNTHETIC_HELPER=1 /usr/bin/python -m scratchpad
```

To use the real offline model, first build a local profile using the data and model steps in the [reproduction guide](docs/31-release.md#reproduce-the-model), then launch it:

```sh
/usr/bin/python -m scratchpad --profile outputs/3aransiya-contextual
```

To install the GNOME top-bar extension for that profile:

```sh
/usr/bin/python extension/install.py --profile outputs/3aransiya-contextual
gnome-extensions enable scratchpad@3aransiya
```

The extension launcher uses the checkout and profile paths, so keep them in place. Log out and back in if GNOME has not discovered the extension.

## Reproduce the model

Model training and profile construction are documented in the [release reproduction guide](docs/31-release.md#reproduce-the-model). It includes pinned data sources, split preparation, training, profile generation, and locked evaluation commands. To avoid redistributing restricted data and large generated artifacts, this repository does not include the DODa corpus, trained model weights, or a built release profile. The DODa data is licensed [CC BY-NC 4.0](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE); the project’s original code is available under the [MIT License](LICENSE). Review each dataset’s license and attribution requirements before using or redistributing derived artifacts.

## Project map

- [Release evaluation and reproduction](docs/31-release.md)
- [Contextual rules, sentence checks, and limitations](docs/33-contextual-extension.md)
- [Corpus expansion and data screening](docs/22-corpus-expansion-audit.md)
- [CPU training and routing results](docs/27-fedora-cpu-training-pilot.md) · [follow-up evaluation](docs/28-fedora-training-and-routing-results.md)
- [Sentence Transformer experiment](docs/32-sentence-transformer-pilot.md)
- [Documentation index and suggested reading order](docs/README.md)
- [Scratchpad interaction and keyboard guide](scratchpad/README.md)

## Scope and limitations

The system targets Moroccan Darija written in Latin Arabizi. It does not provide general MSA transliteration, reliably resolve every short or unpunctuated language switch, or guarantee a preferred spelling for unfamiliar forms. Context rules come from a limited corpus and sentence checks. The reported results should be read with their evaluation sizes and limits above.

## Local data and credentials

Typed text is processed locally by the app. The repository does not contain account credentials, training corpora, or trained model exports. Local `.env` files, Kaggle credentials, data, checkpoints, outputs, and virtual environments are excluded by `.gitignore`.

## Demo preview

The GIF is generated from the normal-speed MP4 with FFmpeg and keeps the source frame dimensions:

```sh
python project_tools/make_demo_gif.py
```

Install FFmpeg to regenerate the preview. Adjust its playback speed and frame rate with `--speed` and `--fps`.
