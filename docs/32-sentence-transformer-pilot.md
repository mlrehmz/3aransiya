# Sentence-level Darija Transformer pilot

The first release scores individual words. In a single real draft, it converted an English clause into Arabic-looking text and did not recover the Arabic spelling of an adjacent formal phrase. The next model takes a complete Arabizi sentence and learns to output Arabic script with the original meaning, word order, and embedded foreign text. Sentence-level code-mixed transliteration has been studied on dialectal Arabic. The pilot uses the Moroccan DODa data for training and evaluation. [Prior sentence-level Arabizi work](https://aclanthology.org/2020.wanlp-1.15/)

The CPU model uses 64-dimensional character embeddings, two encoder layers, two decoder layers, and four attention heads. Training uses AdamW and length-bucketed batches of 64. Inputs retain Latin case, accents, and punctuation. The preparation step collapses whitespace and removes Arabic vocalization marks. Both strings must fit within 160 characters.

The baseline is the installed release's word routing and phrase renderer. The comparison holds the same development sentences fixed across models. It reports exact matches, character error rate, one-thread single-sentence latency, and exact preservation of named English or French spans in five independent probes. The long mixed draft is a development example. Its formal Arabic span and English tail are checked independently, since the intended rendering of all Darija words is not fully annotated. No new native-speaker evaluation took place.

The pilot uses the checksum-verified, locked human DODa assignments. It trains on 38,999 human sentence pairs and uses a fixed sample from the validation split for comparison. The release test remains outside this iteration. Grounded synthetic Darija and an independent MSA training corpus are still separate experiments.

## Reproduce

Use the [pinned Fedora CPU environment](08-fedora-cpu-runtime.md#verified-local-environment) and the [release's local data and model setup](31-release.md#reproduce-the-model).

```sh
.venv/bin/python -m sentence_pilot.train data/doda-sentences.csv data/doda-split-v2-candidate.json \
  outputs/sentence-transformer-human --epochs 4
.venv/bin/python -m project_tools.adapt_sentence_copy data/doda-sentences.csv data/doda-split-v2-candidate.json \
  outputs/sentence-transformer-human/epoch-4.pt outputs/sentence-transformer-copy
.venv/bin/python -m sentence_pilot.evaluate data/doda-sentences.csv data/doda-split-v2-candidate.json \
  outputs/sentence-transformer-human/epoch-4.pt outputs/3aransiya-release \
  --adapted outputs/sentence-transformer-copy/checkpoint.pt
```

The human-data trainer saves an atomic checkpoint every 100 updates and at the end of each epoch. Rerun the same command to resume. The copy adaptation starts from the epoch-four weights and uses 48 human Darija examples and 16 code-mixed examples per batch. English spans come from the English column of training rows. A small authored French list supplements them. The development probes are authored separately. They are useful checks for observed errors and are too few to estimate broad code-switching accuracy.

## Results

The four-epoch human run took 363 seconds on four Fedora CPU threads and completed 2,440 updates with 188,253 parameters. The copy adaptation added 300 updates using 4,722 generated mixed-sentence candidates. The local checkpoint and copied-span comparison are retained under `outputs/sentence-transformer-human/` and `outputs/sentence-transformer-copy/`.

| Candidate | Exact sentences out of 512 | Character error rate ↓ | Foreign spans copied out of 5 | Median CPU time per sentence ↓ |
| --- | ---: | ---: | ---: | ---: |
| Installed release | 203 | 5.93% | 0 | 1.59 ms |
| Human-data Transformer | 129 | 37.04% | 0 | 34.13 ms |
| Transformer with copy adaptation | 126 | 29.09% | 0 | 49.71 ms |

Exact matches and character error include punctuation and spaces after the shared normalization step. Timing uses 12 single sentences per model with one CPU thread. It excludes loading and GUI work. The prior release also had access to the grounded spelling lookup and its earlier model training, so this compares usable candidates with different training histories.

The copied-span fine-tune reduced character errors relative to the first Transformer, but failed to preserve any complete foreign span. Neither Transformer reproduced **علمت عنه من خلال قراءتي بعض كتب السلف** in the user's draft. Greedy decoding repeated fragments in long passages. Splitting the probes at commas failed both exact-span checks too, though the adapted model retained some English fragments.

Keep the release as the baseline. The next design should copy confirmed foreign spans verbatim and let a contextual model choose among plausible Arabic renderings or propose bounded edits. This preserves input structure when a sentence is ambiguous and gives the context model a smaller decision to learn. A native-speaker-reviewed sentence set should check this before any app integration.

The CPU suite passed with 38 tests executed and four GTK tests skipped in the virtual environment. Two new tests covered gradient computation, bounded mixed-length decoding, and input normalization. A separate resume check loaded update 610 and saved update 611 in a temporary run.
