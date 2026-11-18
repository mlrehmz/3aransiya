# Draft Darija correction set

The following labels are proposed for review. Counts come from exact case-sensitive forms in the verified DODa training pairs unless otherwise indicated. Authored spellings are additions for this experiment. The locked release test stays closed.

## Proposed fine-tuning examples

Each slash-separated form is a separate input with the same proposed output.

| Word family | Latin inputs | Proposed output | Evidence |
| --- | --- | --- | --- |
| Reported syllable | `Xa` / `xa` / `cha` | شا | User supplied the `Xa` reading. Training has one matching `cha` occurrence. |
| Look | `Xouf` / `xouf` / `chouf` | شوف | Training has 36 matching `chouf` occurrences. The x forms are authored. |
| Why | `3lax` / `3laX` / `3lach` | علاش | 481 matching `3lach` occurrences and 10 of 14 `3lax` occurrences. `3laX` is authored. |
| Bread, خ control | `khobz` / `5obz` | خبز | Both forms are attested with this target. |
| Cup | `ka2s` / `kas` | كاس | One and 27 training occurrences respectively, all كاس. |
| Opinion, hamza control | `ra2y` | رأي | 11 of 13 training occurrences use this target. |
| Conjunction control | `o` | و | 459 of 468 training occurrences use this target. |
| Presentation | `prizontasyon` | پريزونتاسيون | User specified initial پ. The rest of the spelling is proposed for review. There are no exact training occurrences. |
| Sport, پ example | `sport` | سپور | Twelve matching occurrences and one with سـبـور. |

## Held out from the correction set

Keep these word families out of the corrective examples. The starting model may already have seen attested forms in DODa. The authored variants check transfer to new spellings.

| Word family | Latin inputs | Proposed output | Evidence |
| --- | --- | --- | --- |
| How much | `X7al` / `ch7al` | شحال | Authored uppercase form and 289 attested `ch7al` occurrences. |
| I drank | `xrebt` / `chrebt` | شربت | Authored x form and one attested `chrebt` occurrence. |
| My brother, خ control | `khouya` | خويا | All 18 training occurrences use this target. |
| Name, uppercase X control | `REX` | ريكس | One exact occurrence. |
| Responsible, hamza control | `mas2oul` / `ms2oul` | مسؤول | Authored expanded spelling. Three exact `ms2oul` matches. |
| Harm, final hamza control | `so2` | سوء | One exact occurrence. |
| Pizza, پ contrast | `piza` / `pizza` | پيتزا | Proposed user-convention check. DODa has six `pizza` occurrences under بيتزا. Confirm before treating پ as required. |

## Open labels

- `2o` → أو if the intended word is “or,” or و if it is the user's spelling of “and.” Both current bundles emit أو. Leave it out until the intended reading is confirmed.
- Leave `xno` and `x7al` out pending review because they have conflicting corpus references.
- Confirm the full spelling of `prizontasyon` and where پ is required in loanwords. Both bundles already have پ in their output vocabulary. It appears in 183 training occurrences, but neither bundle used it for `prizontasyon`. The encoder–decoder returned برزيتونيش and GRU/CTC returned بريزنتسيون. Case-insensitive searches found no `prizontasyon`, `presentation`, `présentation`, `prezentasyon`, or `prezontasyon` in training.

**Proposed next action:** Review these labels and record a pre-fine-tuning score on the held-out examples. Compare a later Darija fine-tune with the current model on those examples and on unchanged validation. Include replay from original training data in the fine-tuning plan to measure regressions. Evaluate MSA pretraining separately.

## Baseline before fine-tuning

Ran both epoch-six bundles locally and compared outputs by normalized exact match. The draft examples and held-out word families were scored separately. The provisional `prizontasyon` label was checked separately. Standalone `2o` and both proposed pizza inputs were excluded.

| Slice | Encoder–decoder | GRU/CTC |
| --- | ---: | ---: |
| Draft examples | 9 / 16 | 8 / 16 |
| Held-out word families | 6 / 9 | 5 / 9 |
| Provisional `prizontasyon` example | 0 / 1 | 0 / 1 |

Both models missed the six draft x/X forms and the two authored held-out x/X forms, `X7al` and `xrebt`. Their paired ch spellings matched. Both preserved خ in `khobz`, `5obz`, and `khouya`. Neither matched the held-out name `REX` despite its one training occurrence. The encoder–decoder matched both cup spellings and both “responsible” spellings. CTC missed `ka2s` and `mas2oul`. For `sport`, the encoder–decoder used ب and CTC used پ but added ت.

This small baseline is intended to catch specific regressions after fine-tuning. The held-out families were excluded from the correction set. Some of their established forms were in the original training corpus. No fine-tuning or locked-test evaluation took place.
