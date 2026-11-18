# Six-epoch Colab T4 comparison

The `t4-comparison-6epoch-v1` run used the same development corpus and scoring as the [two-epoch pilot](16-colab-pilot-results.md). Both final checkpoints record 7,326 optimizer steps on a Tesla T4 with PyTorch 2.14.1+cu130. For each candidate, the final validation report matches the epoch-six report, the report and bundle point to the same final checkpoint, and the weight file matches the manifest checksum.

## Validation by epoch

All scores below are strict exact match. Each epoch scored 9,901 common, 20,081 overall, and 3,389 unseen validation occurrences.

| Epoch | Encoder–decoder common | Overall | Unseen | GRU/CTC common | Overall | Unseen |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 93.46% | 69.98% | 30.63% | 86.95% | 69.54% | 46.65% |
| 2 | 94.69% | 76.34% | 42.46% | 92.73% | 75.82% | 52.61% |
| 3 | 94.99% | 78.89% | 46.39% | 93.42% | 77.21% | 52.82% |
| 4 | **95.02%** | 79.84% | 48.83% | 93.50% | 78.33% | 54.68% |
| 5 | 94.83% | 80.67% | 51.28% | 93.95% | 79.01% | 55.59% |
| 6 | 94.79% | **81.19%** | 52.14% | 94.22% | 79.54% | **56.21%** |

The encoder–decoder's common-word score peaked in epoch 4 at 95.02% strict and 96.11% variant-aware. Its overall score continued rising through epoch 6. GRU/CTC improved across all three slices at every reported epoch and retained a 4.07 percentage point lead on unseen words at epoch 6.

| Available epoch-six bundle | Common variants | Overall variants | Unseen variants | Missing outputs |
| --- | ---: | ---: | ---: | ---: |
| Encoder–decoder `bundle-d4307181ae640820` | 96.05% | 81.81% | 52.14% | 0 |
| GRU/CTC `bundle-efd647d570f21bcc` | 95.51% | 80.17% | 56.21% | 0 |

The archive retains checkpoints for steps 7,325 and 7,326 for both candidates. Epoch 4 has a validation report but no retained weights. This was an artifact review. No new training, inference benchmark, or locked-test scoring was run.

**Proposed next action:** Try the exported epoch-six encoder–decoder in the Fedora scratchpad with a short manual typing and copy check. Its overall result makes it the better first app candidate on this validation set. Keep GRU/CTC available for comparison on unfamiliar words.
