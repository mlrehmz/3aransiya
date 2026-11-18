# DODa data exploration

**18 November 2026 · Exploratory audit before training**

We checked whether human-authored Darija sentences could supply word-level supervision for an offline Latin/Arabizi-to-Arabic scratchpad. We also tested whether lowercasing would discard useful spelling distinctions.

## Source and method

- DODa revision `feb88ff23153283c47d83dd677b432fe0cbac15a`, human sentence file `sentences/sentences.csv`, columns `darija` and `darija_ar`. CSV SHA-256 `f5c001982237b2e0c095db3e0fc2f7e3123cee044762ed1e855e24bfde35d62d`. [Pinned CSV](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/sentences/sentences.csv)
- Normalize both sides to NFC, remove Unicode nonspacing marks from the Arabic side, and tokenize both sides into runs of Unicode alphanumerics. Keep equal-length rows whose corresponding tokens use the expected scripts. The check permits ASCII digits in script-bearing tokens and allows matching standalone ASCII digit tokens, which are excluded from word counts. Pair the remaining tokens by position.
- Count Arabic targets per Latin form with original case and after Python `str.lower()`. Draw 40 candidate occurrences in CSV and token order using `random.Random(42).sample` and inspect each in sentence context. Run the audit in memory with no Kaggle upload.

## Results

| Measure | Count |
| --- | ---: |
| Candidate sentence rows | 48,839 |
| Equal token counts | 45,005 |
| Passed token script checks | 44,922 (91.98%) |
| Candidate word occurrences | 195,301 |
| Sampled occurrences with a plausible positional alignment | 40 of 40 |

The sample gives an initial plausibility check. Equal token counts can hide compensating splits, joins, or reordered words. Sampling occurrences favors common forms and can draw several words from one sentence. The screen measures candidate volume. The larger targeted audit is still pending.

| Input handling | Distinct forms | Forms with conflicting Arabic targets | In-sample best single target per form |
| --- | ---: | ---: | ---: |
| Preserve case | 43,620 | 4,929 | 92.83% |
| Lowercase | 42,801 | 5,060 | 92.62% |

Lowercasing created **179 conflicting groups across 1,010 occurrences** whose constituent case-sensitive forms each had a single target. For example, `nadi` mapped to نادي 34 times and `naDi` mapped to ناضي four times. DODa documents uppercase `T`, `S`, and `D` as distinctions in its spelling convention. [Pinned spelling guidelines](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/README.md#guidelines--recommendations)

The last column sums each form's most frequent target count and divides by 195,301. It describes ambiguity across the unsplit candidate corpus, including spelling variation and potential alignment noise. The 99% release gate applies to held-out common words under a separate scoring protocol. This audit took place before any locked test was established.

## Decisions and open questions

- Keep DODa as a candidate for local corpus preparation. The pinned license permits noncommercial sharing and adaptation with attribution, a license link, and disclosure of changes. Private Kaggle upload remains unresolved because Kaggle's submission terms also require rights to operate the service. [Pinned license](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE) · [Kaggle Terms, section 9](https://www.kaggle.com/terms)
- **Approved and completed:** Set up the minimal repository and [record the target machine](../README.md#verified-target-machine). The audit establishes enough candidate volume to proceed with local preparation. During corpus preparation, group and split the sentences before extracting pairs, then use training data for the targeted alignment audit and a comparison of case-handling rules. Use validation to assess coverage and ambiguity among common words before committing to the training pilot.
