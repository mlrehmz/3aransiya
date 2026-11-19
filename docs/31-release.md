# Release model and evaluation

3aransiya loads one offline profile from the scratchpad's background worker. The profile verifies checksums for its routing data and model manifests. The underlying bundle loader verifies the weights. For a word, the helper shortens runs of three or more identical Latin letters to two, then checks exact lookups. Other words from human training go to the step-128 fine-tuned encoder. Words absent from human training go to the epoch-six CTC model, with the encoder available if CTC cannot produce an output.

The human lookup requires three matching occurrences and at least 90% agreement. A grounded-only spelling requires five matching occurrences and the same agreement. The profile includes the explicitly reviewed `Xa` and `xa` spelling **شا**. The scratchpad recognizes a small set of reviewed full phrases, including **صلى الله عليه وسلم** and **أصبحنا وأصبح الملك لله**. It preserves punctuation outside matched phrases. These rules cover a few MSA expressions. General MSA transliteration and a separate MSA fine-tuning corpus remain outside the verified release.

## Locked evaluation

The profile was fixed before running the [locked sentence assignment](02-doda-sentence-split.md#locked-v2-assignment). The same positional extraction screen used on development data accepted 4,394 of 4,801 assigned test sentences, yielding 18,993 aligned word occurrences and 7,963 distinct Latin forms. Both candidates returned an output for every scored occurrence.

| Slice | Occurrences | Previous encoder strict | Release strict |
| --- | ---: | ---: | ---: |
| Common forms | 9,365 | 94.12% | 94.29% |
| Overall | 18,993 | 81.02% | 82.27% |
| Unseen in human training | 3,168 | 51.29% | 54.26% |
| Seen only in v2 grounded training | 626 | 57.99% | 62.78% |
| Still unseen in v2 | 2,542 | 49.65% | 52.16% |

The release added 238 strict matches. Variant-aware overall accuracy rose from 81.64% to 82.80%, while the common-form variant-aware slice moved from 95.38% to 95.36%. On the verified Fedora target, median single-thread word prediction fell from 1.71 ms to 0.93 ms and p95 from 2.61 ms to 2.40 ms. The timing excludes loading, pipe communication, and UI work.

These scores describe screened word pairs. The test groups normalized sentence duplicates and the grounded expansion screens exact normalized sentence overlaps. Near duplicates and alternate reference spellings can still affect the estimate. Phrase rendering was checked separately. `prizontasyon` and some unfamiliar `x/ch/kh` spellings remain weak.

Verified the real GTK path with pasted multiword input, Arabic phrase rendering, copying, and draft reset. The GNOME extension was active after installation and the installed launcher redirected a second launch to the existing scratchpad. The top-bar icon is available for the screenshot walkthrough. The combined test runs passed all 40 unit tests across the CPU environment and system GTK, and rebuilding from the same input bundles reproduced the profile byte for byte.

## Reproduce the model

Use the CPU environment in the [README](../README.md#run-locally). Run the data preparation steps from the repository root. Obtain the pinned [human sentence CSV](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/sentences/sentences.csv) and [DODa-500K LFS object](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/doda-500k/darija_parallel.jsonl) as `data/doda-sentences.csv` and `data/doda-500k.jsonl`. The builders verify input digests. The [data audit](22-corpus-expansion-audit.md) records the screening and provenance.

```sh
.venv/bin/python -m project_tools.sentence_split data/doda-sentences.csv data/doda-split-v2-candidate.json \
  --sha256 f5c001982237b2e0c095db3e0fc2f7e3123cee044762ed1e855e24bfde35d62d --rule v2
.venv/bin/python -m project_tools.word_pairs data/doda-sentences.csv data/doda-split-v2-candidate.json data/doda-word-pairs-v1.json
.venv/bin/python -m project_tools.grounded_manifest data/doda-500k.jsonl data/doda-sentences.csv \
  data/doda-split-v2-candidate.json data/doda-word-pairs-v1.json data/doda-grounded-candidate.json
.venv/bin/python -m project_tools.build_grounded_dataset data/doda-500k.jsonl data/doda-grounded-candidate.json \
  data/doda-word-pairs-v1.json data/doda-word-pairs-v2.json
```

The evaluated base bundles are from epoch six of the [original Colab comparison](18-six-epoch-colab-comparison.md). To train base bundles locally, run each architecture for six epochs. The trainer resumes from local checkpoints. Training on another runtime can produce different weights and scores.

```sh
for arch in gru_encoder_decoder_v1 bidirectional_gru_ctc_v1; do
  OMP_NUM_THREADS=2 .venv/bin/python -m model_pilot.train \
    data/doda-word-pairs-v1.json "outputs/base/$arch" --device cpu --architecture "$arch" --epochs 6
done
```

Set `ENCODER` and `CTC` to the two exported `bundle-…` directories printed by the trainer. The evaluated base bundles were `bundle-d4307181ae640820` and `bundle-efd647d570f21bcc` respectively. Fine-tune the encoder and assemble the profile.

```sh
.venv/bin/python -m project_tools.fine_tune_spellings data/doda-word-pairs-v2.json "$ENCODER" outputs/spelling-tune
.venv/bin/python -m scratchpad.release_model build data/doda-word-pairs-v2.json \
  outputs/spelling-tune/bundle-step-128 "$CTC" outputs/3aransiya-release
```

The profile contains two verified bundle directories and the generated routing table. It occupies about 1.5 MB before compression. The evaluated local profile's `profile.json` SHA-256 is `ed94a3a04ba1b73cdf239302e08e8fc3d55dbbd5bdf53b809462e6ee71cf0679`. Reuse the entire directory for offline inference.

Run this evaluation after selecting the candidate, so decisions use development data and the test stays useful as an independent check.

```sh
.venv/bin/python -m project_tools.evaluate_release data/doda-word-pairs-v2.json data/doda-sentences.csv \
  data/doda-split-v2-candidate.json "$ENCODER" outputs/3aransiya-release
```
