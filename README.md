# 3aransiya

An offline GNOME scratchpad for writing Moroccan Darija in Arabizi and copying it in Arabic script. Open it from the **ض** icon in the top bar, type or paste into the lower row, and copy the result from the upper row.

Try `Xa kas 123` for **شا كاس 123** or `asba7na wa asbaha lmolko lilah` for **أصبحنا وأصبح الملك لله**.

<!-- Add the GNOME top-bar and scratchpad screenshots here. -->

## Results

On the locked DODa test set of 18,993 word occurrences, the release reached **82.27% strict accuracy** and **82.80% variant-aware accuracy**. The previous encoder reached 81.02% strict accuracy. On words absent from all v2 training data, accuracy increased from **49.65% to 52.16%**.

Median local prediction was **0.93 ms per word** on an Intel Core i5-8250U, excluding startup, interprocess communication, and GTK rendering. The release uses a fine-tuned character GRU, a CTC fallback, and exact spelling lookups. A short list of reviewed phrases supports whole-expression rendering and clitic spacing. [Final evaluation and limitations](docs/31-release.md)

The contextual profile preserves detected English and French clauses and uses neighboring words to choose among attested Darija spellings. It preserved all five foreign-language spans in the development probes. Exact Darija sentence matches moved from 203 to 204 out of 512 in the same sample. [Contextual release results](docs/33-contextual-extension.md)

## Run locally

Verified on **Fedora 45**, **GNOME Shell 51.1**, and **Wayland**. Install GTK 4 and Python GObject bindings if needed, then create the separate CPU inference environment from the repository root.

```sh
sudo dnf install gtk4 python3-gobject
uv venv --python 3.14.8 --managed-python .venv
uv pip install --python .venv/bin/python --index-url https://download.pytorch.org/whl/cpu -r requirements-cpu.txt
```

Build the base model using the [reproduction steps](docs/31-release.md#reproduce-the-model). Then assemble the contextual profile and launch it with the system Python for GTK.

```sh
.venv/bin/python build_context_profile.py outputs/3aransiya-release \
  data/doda-word-pairs-v1.json outputs/3aransiya-contextual
/usr/bin/python -m scratchpad --profile outputs/3aransiya-contextual
```

To open it from the GNOME top bar, install the extension and enable it.

```sh
/usr/bin/python extension/install.py --profile outputs/3aransiya-contextual
gnome-extensions enable scratchpad@3aransiya
```

Keep the checkout and model folder in place while the extension uses them. If GNOME has yet to discover the extension, log out and back in, then enable it. **Ctrl+S** clears the draft. The copy button uses the current selection or the whole draft. It preserves unresolved source words, so wait for the preview to finish before copying a draft.

## Project notes

- [Data exploration](docs/01-doda-data-exploration.md), [locked sentence split](docs/02-doda-sentence-split.md), and [alignment pilot](docs/03-training-alignment-pilot.md)
- [Corpus expansion audit](docs/22-corpus-expansion-audit.md) and [Fedora CPU training](docs/27-fedora-cpu-training-pilot.md)
- [Spelling fine-tuning](docs/30-spelling-enrichment-fine-tuning.md) and [release evaluation](docs/31-release.md)

Original project code is under the [MIT License](LICENSE). The source Darija corpus is provided by the DODa maintainers under [CC BY-NC 4.0](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE). The data and trained profile are local build artifacts.
