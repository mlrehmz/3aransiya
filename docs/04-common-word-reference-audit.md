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

## Training context review

Ranked the 500 common forms by occurrences outside their training majority reference, with Unicode string order breaking ties. Reviewed the top eight forms and up to two distinct training sentences for each of their three most frequent references. References were ranked by count and then Unicode order. Sentences were sampled from sorted record IDs with a shared Python `random.Random(42)`. The review covered 40 form/reference contexts. It used the pinned DODa sentences and the v1 extracted pairs.

| Latin form | Non-majority occurrences | What the reviewed contexts showed |
| --- | ---: | --- |
| `m3a` | 302 | مع and معا both express the preposition “with” in the sampled contexts, including before a noun phrase. |
| `f` | 139 | ف and في express the same preposition. The rare يتسجل reference is a shifted verb, caused by sentence token boundaries (record 3019). |
| `imta` | 91 | إمتا and امتا are spellings of “when.” |
| `achno` | 79 | أشنو, اشنو, and آشنو represent “what” in reviewed questions. The fourth reference was outside this context sample. |
| `hiya` | 75 | هي and هيا occur with the same feminine pronoun reading in comparable contexts. The sample also includes a copular use. أكبر is the next word, so the positional pair is shifted (record 35740). |
| `lma` | 74 | الما, لما, and الماء all refer to water in the sampled contexts. The last is the standard Arabic spelling. |
| `kayna` | 58 | كاينة and كاينا express feminine existence or presence. The rare كاين drops the feminine ending visible in the source (record 3952). |
| `lhadra` | 58 | The three reviewed references all occur in contexts about speech or talk. The حض spelling merits a second reading before inclusion in a scoring rule. Six less frequent references were outside this sample. |

The eight forms account for 876 of the 4,019 training occurrences outside their form's majority reference. That count ranks review priority. It includes references beyond those manually examined. Most examples reviewed illustrate spelling or register variation. The sample also confirmed two shifted alignments and a reference that drops a grammatical distinction. It did not establish any case where context requires two different valid outputs for the same form. No validation or test sentences were examined for this review.

## Recommended scoring policy

Keep the 99% occurrence-weighted target and report single-reference exact match as a separate diagnostic. For the release gate, propose exact match against a small, versioned set of reviewer-approved spellings for each eligible reference. Derive and review these equivalences on training data, require the prediction to preserve the word and grammatical content of the reference, and freeze the policy before locked-test evaluation. Allow equivalence only for the specified form and reference. A spelling seen elsewhere for the same Latin input does not automatically qualify.

Correct or exclude confirmed alignment and reference errors under a written rule, and report every resulting change to coverage and the denominator. Where context genuinely changes the required output, keep the references distinct and report that slice so we can see how the word-only interface handles it. Do not add equivalences in response to locked-test predictions. This proposal changes what qualifies as a match and needs approval before implementation.

**Proposed next action:** Draft the equivalence and exclusion rubric as a short Markdown specification. Use examples from this review to define what counts as the same word, how to handle doubtful forms, and what gets reported before we measure the revised protocol on validation.
