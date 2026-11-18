# Common-word reference audit

**18 November 2026 · Train and validation**

The current release protocol calls for 99% exact match on common-word commits, with one reference per occurrence and one output per case-sensitive Latin input. We measured how often the current references agree before freezing that protocol or training a model.

## Method

Use the [v1 word-pair artifact](03-training-alignment-pilot.md#first-extractor-results), verified by SHA-256. Count eligible training occurrences by case-sensitive Latin form. Rank by descending count, breaking ties by ascending Unicode string order, and take the first 500. The cutoff was 32 occurrences. Eight of the 16 forms tied at the cutoff were selected. The locked test was excluded.

For each covered form, count normalized Arabic references by occurrence. Sum the largest count per form to get the maximum agreement a deterministic word-only predictor could achieve on those observed references. The validation maximum uses validation labels for this diagnostic. The training-majority baseline selects the most frequent Arabic reference from training, with the same Unicode tie break, then evaluates that fixed choice on validation.

## Results

| Measure | Train | Validation |
| --- | ---: | ---: |
| Covered common forms | 500 | 498 |
| Common occurrences | 77,229 | 9,901 |
| Share of extracted occurrences | 49.44% | 49.31% |
| Covered common forms with conflicting references | 286 | 145 |
| Best single output per form | 73,210 / 77,229 (94.80%) | 9,468 / 9,901 (95.63%) |
| Training-majority baseline | 73,210 / 77,229 (94.80%) | 9,417 / 9,901 (95.11%) |

On validation, the training-majority baseline averaged 90.46% when every covered form was weighted equally. For example, `m3a` had 47 instances of مع and 39 of معا. The short form `f` had 99 instances of ف and 15 of في. These counts show the effect of scoring exact strings when the corpus supplies different renderings for the same input. The disagreements can include valid variants, context-dependent choices, or extraction and reference errors. The audit did not adjudicate them.

Even the best single output per form misses 433 of the 9,901 validation occurrences. At this denominator, 99% allows at most 99 misses. The maximum applies to the current validation references and the word-only interface. It does not estimate locked-test performance.

## Next decision

**Proposed, pending approval:** Audit the most frequent conflicting references against their training sentence contexts. Write down how to distinguish valid spelling variants, context-dependent forms, and alignment or labeling errors. Use those findings to propose a scoring policy before freezing the protocol. Keep the numerical 99% target and the locked test assignment.
