# Development validation benchmark

**18 November 2026 · Verified baseline**

The benchmark compares one fixed output per case-sensitive Latin form on the same validation occurrences as the [spelling pilot](05-common-word-scoring-rubric.md#expanded-validation-pilot). It verifies the v1 word-pair artifact digest and ranks common forms by descending training count, with Unicode order breaking ties. Unseen forms have no extracted training occurrence.

```sh
python -m validation_benchmark data/doda-word-pairs-v1.json
python -m validation_benchmark data/doda-word-pairs-v1.json --predictions data/model-predictions.json
```

Without a predictions file, the command picks the most frequent training reference for each seen form. A model can provide a JSON object mapping each original case-sensitive Latin form to a single output string. The benchmark normalizes outputs to NFC and removes nonspacing marks. Missing predictions count as misses. The JSON report includes counts and accuracies for strict exact match and the twelve pilot spelling equivalences.

| Validation slice | Occurrences | Distinct forms | Strict | Variant-aware | Missing |
| --- | ---: | ---: | ---: | ---: | ---: |
| Common | 9,901 | 498 | 9,417 (95.11%) | 9,527 (96.22%) | 0 |
| Overall | 20,081 | 8,357 | 14,983 (74.61%) | 15,093 (75.16%) | 3,389 |
| Unseen | 3,389 | 3,296 | 0 (0.00%) | 0 (0.00%) | 3,389 |

The command reproduced the earlier common-word counts. An external predictions file using baseline outputs, including a diacritized output for one word, returned a byte-identical report. A small fixture verified that an unseen prediction can score a hit, a missing unseen prediction stays in the denominator, and a pilot spelling can add a match. Malformed prediction values were rejected. Existing tests passed.

This benchmark measures word prediction agreement on development data. Keystroke replay, latency, and release scoring are separate deliverables. The locked test stayed closed.

## Next decision

**Proposed, pending approval:** Draft the smallest shared model pilot design for the GRU encoder–decoder and bidirectional GRU/CTC candidates. Define the training vocabulary, length and CTC feasibility checks, and the validation prediction export before implementing either model.
