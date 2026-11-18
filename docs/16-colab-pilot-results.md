# Colab T4 pilot results

Both candidates completed **2,442 optimizer steps**, corresponding to two epochs over 156,219 training occurrences at batch size 128. Each final checkpoint also records 2,442 checkpoint generations, seed 42, AdamW learning rate 0.001, and the runtime as Tesla T4, Python 3.13.16, and PyTorch 2.14.1+cu130. This was verified from the saved checkpoints. The archive does not establish how much training happened in the final session or its wall-clock duration.

For both candidates, the validation report and the bundle manifest point to the same archived final checkpoint, and the exported weight bytes match the manifest checksum.

| Validation slice | Occurrences | Encoder–decoder strict | Encoder–decoder variants | GRU/CTC strict | GRU/CTC variants |
| --- | ---: | ---: | ---: | ---: | ---: |
| Common | 9,901 | 94.69% | 95.90% | 92.73% | 93.92% |
| Overall | 20,081 | 76.34% | 76.94% | 75.82% | 76.41% |
| Unseen | 3,389 | 42.46% | 42.46% | 52.61% | 52.61% |

The encoder–decoder led by 194 strict matches on common occurrences and 104 overall. GRU/CTC correctly predicted 344 more unseen occurrences. Its sole missing output was on an unseen form. The training-majority baseline still leads both candidates on common forms at 95.11% strict. [Baseline results](06-validation-benchmark.md)

These are development scores after two epochs. The locked test stayed closed. This review verified the archived results and did not rerun inference or measure latency.

**Proposed next action:** Compare a small sample of validation words where the models disagree. Inspect source context to distinguish model errors from reference and alignment issues before choosing the next training change.
