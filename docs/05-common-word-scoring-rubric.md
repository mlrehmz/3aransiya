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

## Next decision

**Proposed, pending approval:** Review the six remaining forms from the training context audit and draft a short list of equivalences with record-level evidence. Flag confirmed data errors separately. Bring the proposed entries back for approval before expanding the validation pilot. This bounds the annotation effort and keeps the decision about accepted spellings grounded in training evidence.
