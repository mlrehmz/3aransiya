# Expanded v2 results and human-weighted follow-up

Both candidates completed 9,146 batches on a Tesla T4 with PyTorch 2.14.1+cu130, according to the supplied Colab logs. The run used 1,170,570 training occurrences after the two shared alignment exclusions. The logging rerun resumed from complete checkpoints and reported successful bundle verification. Local bundle files have yet to be inspected.

| Strict exact match | v1 encoder–decoder, epoch 6 | v2 encoder–decoder, one pass | v1 GRU/CTC, epoch 6 | v2 GRU/CTC, one pass |
| --- | ---: | ---: | ---: | ---: |
| Common, 9,901 occurrences | 94.79% | 92.22% | 94.22% | 91.18% |
| Overall, 20,081 occurrences | 81.19% | 74.67% | 79.54% | 73.99% |
| Original unseen, 3,389 occurrences | 52.14% | 43.26% | 56.21% | 47.74% |
| Newly seen in v2, 677 occurrences | — | 59.23% | — | 58.79% |
| Still unseen in v2, 2,712 occurrences | — | 39.27% | — | 44.99% |

The encoder–decoder produced an output for every validation occurrence. GRU/CTC missed one still-unseen occurrence. The v2 encoder–decoder led overall, while GRU/CTC retained its lead on unseen words. Both models fell below their own v1 scores on the comparable slices. The comparison changes the corpus, vocabulary, and number of passes, so it cannot establish that synthetic data caused the decline. Keep the current v1 deployment while reviewing the results. [V1 comparison](18-six-epoch-colab-comparison.md)

The encoder–decoder bundle is `bundle-abd46313d049373a` with reported manifest SHA-256 `d6b08dfc04b4538bd25406227d27a0be76ed096591a05165482fedecf7cd6270`. The GRU/CTC bundle is `bundle-c55e9875fb33f721` with reported manifest SHA-256 `3df86c9597b8f33a8ab0d88769091fc41f7b6d7fecb373a78bf45535864d33a9`.

## Proposed follow-up

Run one v2 encoder–decoder from scratch at **25% human and 75% grounded synthetic** training occurrences. Compare it with the completed v2 encoder–decoder run, whose human share was 13.35%. Test one architecture first because it currently leads overall. This isolates the training mix more directly than comparing with v1.

Use 32 human and 96 grounded occurrences per full batch. Draw deterministically without replacement within each source pool and reshuffle a source only when its pool is exhausted. Use 2 human and 8 grounded occurrences in the last batch to match the existing run's final batch size. Keep the ordered v2 vocabulary, FP32 AdamW, learning rate 0.001, clipping at 1.0, seed 42, and 9,146 optimizer steps. Use the existing restartable checkpoint format in a new run directory. The mix deliberately gives some human rows multiple exposures and presents fewer synthetic rows at the fixed compute budget. Report actual counts and unique exposures by source.

At step 9,146, report strict and variant-aware scores and missing outputs using the same v1-defined slices and the same v2 coverage breakdown. Evaluate both checkpoints on the fixed spelling probes separately. If common and overall accuracy improve while still-unseen accuracy holds, the result supports giving human examples more weight at this budget. If the slices trade off, report both effects before choosing another run. The locked test remains closed.

## Notebook and local verification

Open [the 25% human-data notebook](../notebooks/colab_t4_v2_human25.ipynb) on a Colab T4 and upload `doda-word-pairs-v2.json` directly to `/content/`. The notebook embeds the required code. Its independent run directory is `/content/outputs/t4-v2-human25/gru_encoder_decoder_v1/`. It saves after every update and exports validation reports, source counts, and the Fedora inference bundle. To recover after a full Colab reset, keep a copy of the run directory and restore it along with the dataset.

A local audit of the pinned v2 dataset confirmed the same deterministic order on a repeat run, 9,145 batches of 128 and a final batch of 10, with the mix checked in every batch.

| Source | Scheduled exposures | Distinct source rows |
| --- | ---: | ---: |
| Human Darija | 292,642 | 156,219 |
| Grounded synthetic | 877,928 | 877,928 |

The sampler groups examples by length within each source and shuffles full batches. The comparison measures the resulting sampling policy, which changes both exposure weights and batch order. Three local checkpoint tests passed, including exact equality between resumed and uninterrupted weights for the weighted sampler on a synthetic fixture.

The next decision is whether to run the notebook on Colab. The corpus run and spelling-probe comparison are pending.
