# DODa sentence grouping and split proposal

**18 November 2026 · V2 assignment locked**

The corpus preparation command needs to assign whole sentences to training, validation, or locked test before extracting word pairs. The [exploratory audit](01-doda-data-exploration.md) found enough candidate pairs to proceed and showed that lowercasing introduces conflicting Arabic targets.

## Group sentences before assigning splits

1. Read the pinned CSV after verifying its checksum and required columns. Identify each sentence by its logical CSV record number and retain both original strings for replay.
2. Create a full-sentence key for each script. Normalize to NFC and compare sequences of Unicode alphanumeric tokens, preserving token boundaries and digits. Preserve Latin case and strip Arabic nonspacing marks as in the exploratory audit. Keep punctuation and whitespace in the original strings for replay. A row with an empty key on either side is rejected with a recorded reason.
3. Link rows when either script's key matches exactly. Use connected components so that exact duplicates and identifiable variants stay together even through an intermediate row. Keep each row's original spellings and provenance. For example, illustrative pairs `salam 3likom` → سلام عليكم and `salam 3likum` → سلام عليكم share an Arabic key. If a third row shares either Latin key but spells the Arabic differently, it stays in the same group as well.
4. Use a versioned SHA-256 hash of each component's sorted source record numbers, encoded unambiguously as compact JSON, to assign the entire group. Interpret the first eight hash bytes as an unsigned big-endian integer and take modulo 100. Buckets 0–79 are training, 80–89 validation, and 90–99 locked test. These are target proportions. Report achieved counts and percentages by group and sentence, and review any large component or material imbalance before locking the split.

Matching either script catches more identifiable spelling variants than matching the full bilingual pair. It can also join unrelated readings of the same Latin sentence. Reporting component sizes makes that tradeoff visible. Exact normalized keys can miss variants that differ on both sides. A diagnostic using lowercased Latin keys can flag possible cross-split matches for review before the split is locked. Lowercasing can also merge meaningful DODa casing distinctions, so those matches need separate judgment. [Pinned DODa spelling guidelines](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/README.md#guidelines--recommendations)

## Verify the handoff

- Start with a fixture containing a duplicate, a spelling variant, a transitive match, an unrelated sentence, and an empty key. Check that all linked rows stay together and each accepted record appears exactly once. On the pinned corpus, require zero cross-split overlap on both primary sentence keys. Report lowercased Latin key overlap in aggregate. Common word forms are expected to recur across splits because the holdout unit is the sentence group.
- Produce a canonical, record-ordered assignment manifest with the source checksum, rule version, split hashes, group sizes, and counts. Check that repeating the run on the same input yields identical assignments and hashes. A checksum, schema, or invariant failure stops the run before publishing the manifest. Write the validated manifest to a temporary file in the output directory and atomically replace the destination.
- Treat the assignment manifest as the authority for later extraction. Extract word pairs with source record references and offsets within each split, fit vocabularies on training data, and use validation for development. After the split is locked, keep test records in the local evaluation path and out of training and tuning. Publish aggregate counts and hashes in the portfolio.

## First candidate results

| Split | Groups | Sentences | Share of sentences |
| --- | ---: | ---: | ---: |
| Train | 38,049 | 39,075 | 80.008% |
| Validation | 4,774 | 4,921 | 10.076% |
| Test candidate | 4,725 | 4,843 | 9.916% |

All 48,839 records were assigned exactly once. There were 47,548 groups, including 46,727 singletons. The two largest groups each contained 16 sentences. **Zero primary Latin keys and zero Arabic keys crossed splits.** Five lowercased Latin keys crossed splits. See the review below.

The CLI fixture passed for duplicate and transitive grouping, rejection of empty keys, repeatability, and preservation of an existing manifest on checksum failure. On Fedora with Python 3.15.2, two runs on the pinned corpus produced byte-identical manifests, including a run with a different Python hash seed. The candidate manifest SHA-256 is `b43cccf66ed51a4e28bd32ecd33b57b62ff00a3647b5895c8853374d16b06372`.

Reproduce locally from the pinned CSV in the ignored `data/` directory.

```sh
python -m unittest discover -s tests
python -m project_tools.sentence_split data/doda-sentences.csv data/doda-split-candidate.json \
  --sha256 f5c001982237b2e0c095db3e0fc2f7e3123cee044762ed1e855e24bfde35d62d
```

The CLI uses the Python standard library. Its versioned hash input is compact JSON containing the rule name and the sorted record numbers. Record numbers are one-based after the header. The original strings remain in the checksum-verified CSV and can be retrieved by record number.

## Review of the five cross-split matches

Compared the Latin and Arabic strings and used the English gloss as a clue when a reference differed. Record numbers refer to the pinned CSV. The table gives the judgment for each pair without reproducing the source sentences.

| CSV records | Candidate splits | Judgment |
| --- | --- | --- |
| 1788, 2056 | Train / test | Same short affirmation. The glosses differ slightly in phrasing. Capitalization, punctuation, and the initial Arabic vowel letter vary. |
| 2243, 8310 | Train / test | Same question about playing basketball. The Arabic references vary in spelling and in whether the article is attached. |
| 2287, 3854 | Validation / test | Likely same intended sentence. Both English glosses mean “I don't think so.” The Arabic reference in 2287 instead reads “I don't laugh.” Flag 2287 for a separate alignment decision. |
| 8623, 9811 | Test / train | Same apology for interrupting. Both scripts have spelling differences. |
| 10967, 10968 | Validation / train | Same morning greeting. The Arabic references differ in the spelling of the word for morning. |

Four pairs appear to be spelling or punctuation variants. The fifth appears to share an intended sentence and has a reference mismatch. Grouping all five prevents these near-duplicates from crossing splits. Group membership and suitability as a training example are separate decisions.

## Second candidate results

The approved v2 rule adds a match on lowercased full-sentence Latin tokens to the existing grouping keys. Both original spellings remain available in the pinned CSV. The version tag also changes the assignment hash, so groups can change splits even when their membership stays the same.

| Split | Groups | Sentences | Share of sentences |
| --- | ---: | ---: | ---: |
| Train | 37,977 | 38,999 | 79.852% |
| Validation | 4,873 | 5,039 | 10.318% |
| Test candidate | 4,688 | 4,801 | 9.830% |

All 48,839 records were assigned exactly once, with zero rejections. V2 produced 47,538 groups, ten fewer than v1. The largest groups still contain 16 sentences. All five reviewed pairs share a group. Zero case-preserving Latin, lowercased Latin, or Arabic keys cross splits. Variants whose keys differ in both scripts can still escape detection.

Both CLI tests passed. Two v2 runs with different Python hash seeds produced byte-identical manifests. A fresh v1 run also reproduced the original candidate byte for byte. The v2 candidate manifest SHA-256 is `c4b55713980227c36695b3f946b1a186cb9544e1702a7e98908dcb0e351dd58e`.

```sh
python -m project_tools.sentence_split data/doda-sentences.csv data/doda-split-v2-candidate.json \
  --sha256 f5c001982237b2e0c095db3e0fc2f7e3123cee044762ed1e855e24bfde35d62d --rule v2
```

## Locked v2 assignment

Approved and locked on 18 November 2026. The authoritative assignment is the exact v2 manifest identified below. The local filename and embedded candidate status are generation metadata. This record identifies the frozen bytes.

- Manifest SHA-256 `c4b55713980227c36695b3f946b1a186cb9544e1702a7e98908dcb0e351dd58e`
- Source CSV SHA-256 `f5c001982237b2e0c095db3e0fc2f7e3123cee044762ed1e855e24bfde35d62d`

| Split | Sentences | Assignment SHA-256 |
| --- | ---: | --- |
| Train | 38,999 | `0143daccc03d9c68f47bc211356b95259d1a4a7bed63e1509905e7fc2c9ddc76` |
| Validation | 5,039 | `08f970fbc6520cb9f01eeac3a6012b057c0aab91a45b8a21f2d61a46997b10a6` |
| Test | 4,801 | `1a6332f54aced89bb10334e08e30021af0850366138ee2734630f81dddf8a33b` |

The source digest, manifest digest, and each split digest were recomputed at lock time and matched the reviewed values. Regenerate using the v2 command above and verify the manifest digest before consuming the assignments. Use training and validation for development and reserve the 4,801 test sentences for final evaluation. The earlier five-pair review took place before the lock.

## Next decision

**Proposed, pending approval:** Run a local pilot of word alignment on training sentences only. Draft a reproducible sampling and review rubric for roughly 200 candidate alignments, with coverage of Arabizi digits, single-letter words, French loanwords, and plausible boundary mismatches. Use the results to decide which alignment rules to implement.
