# Proposed common-word scoring rubric

**18 November 2026 · For approval before implementation**

The release target remains **at least 99% occurrence-weighted exact match** on eligible common-word commits. This proposal changes how a reference spelling can match. The [reference audit](04-common-word-reference-audit.md) found that even an ideal deterministic word-only system could match only 95.63% of the current validation references under strict single-reference scoring.

## Eligibility and accepted spellings

- Define common words as the 500 most frequent eligible training forms, with ties broken by ascending Unicode string order. Rank after the training eligibility rules are applied. Normalize inputs to NFC and preserve Latin case. Record the cutoff, ties, and list digest.
- Normalize Arabic references, approved alternatives, and predictions to NFC and remove Arabic nonspacing marks, as in the extraction pilot. Preserve base letters and written long vowels. Compare the complete normalized output with the reference or a listed alternative.
- Approve alternatives individually for a specific Latin form and source reference. Require training sentence evidence that the alternative preserves the intended word and its grammatical content in that use. Record the Latin form, reference, alternative, training record IDs, rationale, and review status. Review each permitted direction explicitly. No transitive or global spelling rules are inferred.
- For example, `m3a` → مع / معا is a candidate equivalence for the preposition “with.” `kayna` → كاينة / كاينا is a candidate where both preserve feminine agreement. The masculine كاين requires separate treatment. These examples illustrate the rubric and await approval as entries. [Training context review](04-common-word-reference-audit.md#training-context-review)
- Keep genuinely context-dependent readings distinct. If an alternative's spelling, meaning, or grammatical role is uncertain, leave that alternative unapproved and retain the original reference for scoring unless the reference is independently confirmed to be wrong.

## Reference corrections and exclusions

A reviewer examines the complete Latin and Arabic sentences together, with predictions hidden. Confirmed errors include shifted tokens, unmatched splits or joins, a translation in place of transliteration, or a reference that changes the intended word or grammatical content.

- Correct the aligned span or reference only when the source sentence supports one unambiguous repair. Keep the original reference, record ID, token index, correction, evidence, and reason in the audit log.
- If the error is clear but the correct alignment or reference is unresolved, exclude the occurrence from scoring and log the reason. Keep doubtful cases with their existing reference and flag them for review.
- Apply the same written eligibility rules to all splits. Report the number examined, corrected, excluded, and unresolved, including counts by reason and common-word coverage before and after review. For the final run, freeze the rules and training-derived alternatives before opening the locked test. Finalize the test reference corrections and exclusions before viewing any test predictions, and keep an auditable record of those decisions. A failed or missing app commit remains an error for an eligible occurrence.

## Release calculation

Replay each eligible word occurrence once. The denominator includes every eligible common-word commit. The primary numerator counts normalized outputs that match the retained reference, including a confirmed correction, or an approved alternative for that form and reference. Pass when `100 × correct ≥ 99 × eligible` with a positive denominator.

Report strict single-reference exact match on the same eligible occurrences, the number of additional matches due to alternatives, distinct common forms covered, per-form accuracy, and the context-dependent slice when present. Report separator preservation separately. Continue to report the other metrics from the project checklist.

## Two-equivalence validation pilot

The approved pilot verified the v1 word-pair artifact and used the [top-500 ranking and training-majority baseline](04-common-word-reference-audit.md#method). Each form had one fixed prediction, with Unicode order breaking training frequency ties. Both scores used the same 9,901 validation occurrences. Only the two listed equivalences were enabled, in both directions for the specified Latin form. No corrections or exclusions were applied and the locked test remained closed.

| Scope | Fixed prediction | Strict matches | Variant-aware matches | Added matches |
| --- | --- | ---: | ---: | ---: |
| `m3a` | مع | 47 / 86 | 86 / 86 | 39 |
| `kayna` | كاينة | 15 / 24 | 24 / 24 | 9 |
| All common occurrences | Training majority per form | 9,417 / 9,901 (95.11%) | 9,465 / 9,901 (95.60%) | 48 |

The two equivalences added **0.48 percentage points** before rounding. All added matches came from the two specified forms. At the same denominator, 99% requires 9,802 matches, leaving this baseline 337 matches short. This is a scoring sensitivity check with fixed predictions. Model performance and the full rubric remain untested.

## Proposed additions for the expanded pilot

The entries below use the [training context review](04-common-word-reference-audit.md#training-context-review). Record IDs refer to the pinned DODa training CSV. Each listed pair would be accepted explicitly in both directions for that Latin form. The six forms contribute ten two-way pairs. They remain proposals for this validation pilot.

| Latin form | Proposed reference pairs | Training evidence and rationale |
| --- | --- | --- |
| `f` | ف ↔ في | Records 9887, 9174, 5553, 4021. Both spellings express the same preposition in a following noun phrase. |
| `imta` | إمتا ↔ امتا | Records 45230, 11520, 7083, 11383. Both spellings express “when.” |
| `achno` | أشنو ↔ اشنو, أشنو ↔ آشنو, اشنو ↔ آشنو | Records 12467, 13071, 44199, 2218, 6255. All three spellings express “what” in questions. |
| `hiya` | هي ↔ هيا | Records 47481, 43796, 44075. All three use the feminine pronoun reading. |
| `lma` | الما ↔ لما, الما ↔ الماء, لما ↔ الماء | Records 25954, 2123, 7989, 24770, 16558, 12256. All three spellings refer to water in these contexts. |
| `lhadra` | لهدرا ↔ لهادرا | Records 18042, 37614, 30486, 33173. Both spellings refer to talk or speech. Defer الحضرة, whose spelling warrants a second review, and the six other unreviewed targets. |

### Confirmed data errors

| Training record and token | Observed pair | Finding |
| --- | --- | --- |
| 3019:6 | `f` → يتسجل | The Arabic verb corresponds to the preceding Latin verb. Token boundaries shift the positional match. |
| 24425:1 | `achno` → دبا | The Arabic target belongs to the preceding phrase. The intended question word appears at the next Arabic position. |
| 35740:4 | `hiya` → أكبر | The Arabic adjective corresponds to the following Latin word. The matching pronoun appears one position earlier. |
| 3952:0 | `kayna` → كاين | The target drops the feminine ending in the source form. |

Flag these for a separate extraction or reference decision. The proposed pilot uses the same predictions, references, and denominator as the two-equivalence run so the effect of the additional pairs can be measured directly. No validation or locked-test contexts were examined for this draft.

## Expanded validation pilot

Verified the same v1 word-pair artifact and regenerated the training-only majority predictions using the previous ranking and tie rules. The validation set, reference strings, and denominator were identical. The twelve approved pilot pairs were the only change from strict scoring. No reference corrections or exclusions were applied.

| Latin form | Validation occurrences | Strict matches | Variant-aware matches | Added matches |
| --- | ---: | ---: | ---: | ---: |
| `m3a` | 86 | 47 | 86 | 39 |
| `kayna` | 24 | 15 | 24 | 9 |
| `f` | 114 | 99 | 114 | 15 |
| `imta` | 27 | 14 | 27 | 13 |
| `achno` | 22 | 12 | 22 | 10 |
| `hiya` | 20 | 8 | 20 | 12 |
| `lma` | 18 | 8 | 18 | 10 |
| `lhadra` | 7 | 1 | 3 | 2 |
| **All common forms** | **9,901** | **9,417 (95.11%)** | **9,527 (96.22%)** | **110** |

The ten new pairs added 62 matches over the previous pilot, a gain of 0.63 percentage points before rounding. The expanded baseline needs 275 more matches to reach 9,802 of 9,901. These are sensitivity results for fixed predictions. The pilot did not train a model, inspect the locked test, or adopt a release policy.

## Validation ceiling under the pilot rules

For each covered common form, score every observed validation reference and every explicitly approved pilot spelling as a possible fixed output. Take the best result for that form and sum across forms. Any other output matches zero occurrences under these rules, so this gives the exact ceiling for one fixed output per form on this validation set.

The ceiling is **9,573 / 9,901 (96.69%)** with the twelve pilot equivalences. The training-majority baseline scores **9,527 / 9,901 (96.22%)**. Choosing the best outputs retrospectively adds only 46 matches. The remaining 328 occurrences cannot all be matched by one output per form under these rules. The calculation does not determine which disagreements are valid variants or data errors.

This is a development diagnostic based on validation labels. It is neither a deployable baseline nor a test-set estimate. The locked test stayed closed. Use strict and pilot variant-aware scores to track progress while iterating. Revisit reference quality and the release rubric after the first model comparison.

**Recommended next iteration, pending approval:** Turn the current validation calculation into a reusable headless benchmark. Reproduce the training-majority scores, then add a way to score model predictions on the same occurrences. Include overall and unseen-form exact match so the model pilot can measure generalization beyond frequent forms.
