# Short Arabizi error check

Ran the two epoch-six bundles on the reported spellings and counted exact matches in the checksum-verified training pairs. The locked test was excluded.

| Input | Encoder–decoder | GRU/CTC | Exact training evidence |
| --- | --- | --- | --- |
| `Xa` | ها | إأأ | None |
| `xa` | كا | خا | None |
| `cha` | شا | شا | One occurrence, شا |
| `kha` | خا | خا | None |
| `2o` | أو | أو | None |
| `o` | و | و | 459 of 468 occurrences are و |
| `ka2s` | كاس | كاأس | One occurrence, كاس |
| `kas` | كاس | كاس | 27 occurrences, all كاس |

The expected `Xa` reading uses ش, like `cha`. The training split has only one uppercase `X` occurrence, in `REX` → ريكس. Lowercase `x` occurs 929 times across 387 forms and can appear with other readings. These observations support adding targeted examples for the intended convention. A universal `X` or `x` substitution would also affect names and other valid uses.

Both models output أو for the unseen form `2o`, while plain `o` maps to و. The expected Arabic for standalone `2o` needs confirmation before using it as a training label. The deployed encoder–decoder already maps `ka2s` and `kas` to كاس on direct requests. The app behavior reported for those examples was not reproduced in this word-only check.

**Proposed next action:** Draft a small reviewed Darija correction set and separate held-out variants for `x/ch/kh` and `2` spellings. Use it to test a targeted fine-tune of the existing model. Treat MSA pretraining as a separate experiment so its effect can be measured against the Darija-only change. This check ran no training and measured no latency.
