# Spelling enrichment and fine-tuning

The 1,170,570-occurrence v2 pool supplied the grounded spelling lookup and the existing validation slices. A separate fine-tune started from the epoch-six encoder–decoder and used human replay. The correction pool contains manually reviewed spelling examples and conservative initial `ch` to `x` or `X` variants from high-agreement human rows whose Arabic target begins with ش. We skipped generated forms that conflict with observed human targets and reserved the `ch7al` and `chrebt` stem groups from augmentation. The original bundle vocabulary determines training and validation encoding. This is important because the v2 vocabulary has different character IDs.

The 220 correction pairs were paired with human replay in batches of 128, with 8 correction examples and 120 replay examples. The run used AdamW at 0.0002, gradient clipping at 1, and seed 42. Reported checkpoints were 0, 32, and 128. The 14-word probe set includes both the reserved x spellings and controls. Several controls occurred in original DODa. The probe therefore measures transfer and regressions from the correction set rather than performance on a corpus-independent test.

| Updates | Common strict | Overall strict | Still unseen in v2 strict | Spelling probes |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 94.79% | 81.19% | 49.52% | 11/14 |
| 32 | 94.85% | 81.44% | 51.03% | 11/14 |
| 128 | 94.92% | 81.58% | 50.92% | 11/14 |

Step 128 fixed `xrebt` to **شربت** and retained the correct bread and cup spellings. It produced **سپور** for `sport`, an explicit correction example. It regressed `ra2y` from **رأي** to **رائي**. `Xa`, `X7al`, and `prizontasyon` remain incorrect. Both tuned exports reproduced their pre-export spelling probes exactly. No MSA corpus was added. This run addresses Darija word spellings. MSA phrase quality remains a separate evaluation problem.

Find the training artifacts under `outputs/fedora-v2-spellings-v1/`. The locked test remains reserved.

## Combined candidate

The routing comparison used the same 20,081 validation occurrences and one CPU thread. It measured one prediction per distinct form after loading the bundles.

| Candidate | Common strict | Overall strict | Overall variant-aware | Still unseen strict | Median word prediction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Installed epoch-six encoder | 94.79% | 81.19% | 81.81% | 49.52% | 2.20 ms |
| Previous best route | 94.79% | 82.37% | 82.99% | 54.65% | 1.15 ms |
| Previous route with grounded lookup | 94.79% | 82.44% | 83.06% | 54.65% | 1.17 ms |
| Grounded lookup and step-128 tuned encoder | 94.92% | 82.60% | 83.17% | 54.65% | 1.17 ms |

The grounded lookup requires five agreeing training occurrences and at least 90% agreement for a form absent from human training. The combined route retains CTC for unresolved forms absent from human training, so it does not inherit the tuned encoder's improvement on `xrebt`. The full report is `outputs/fedora-v2-spellings-v1/routing-validation.json`. The installed scratchpad still loads the earlier encoder bundle.
