# Path to 600,000 training word pairs

**18 November 2026 · Source and yield audit**

The target is **at least 600,000 accepted training word-pair occurrences**, with validation and test held separately. The existing v1 training data supplies 156,219 occurrences, leaving 443,781 to find. Repeating a batch or copying a sentence does not add corpus coverage. Report distinct Latin forms, distinct paired spellings, and source composition alongside the total.

## DODa-500K

DODa's maintainers report 500,350 sentence rows with Darija in both Latin and Arabic script, provenance, and an English column. The 48,350 human rows come from the existing DODa sentence collection. Treat these as overlapping until checked and keep the pinned human v1 split as the starting point. Of the 452,000 generated rows, half are DODa-grounded and half exploratory. Both synthetic groups require alignment review. [Dataset README](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/README.md#doda-500k-combined-parallel-file) · [Maintainers' expansion write-up](https://epistemicnoise.com/projects/how-we-expanded-doda-to-500k/)

At revision `feb88ff23153283c47d83dd677b432fe0cbac15a`, the combined file is stored in Git LFS. The pointer records 229,170,725 bytes and SHA-256 `76bf4df07676eb2ccadd1ed26a7c23ddd633794f6abb8e6c8e05aa93d1fa000a`. The upstream repository license is CC BY-NC 4.0. Check the intended cloud use and distribution separately before moving a prepared artifact off this machine. [Pinned LFS entry](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/doda-500k/darija_parallel.jsonl) · [Pinned license](https://github.com/darija-open-dataset/dataset/blob/feb88ff23153283c47d83dd677b432fe0cbac15a/LICENSE)

| Synthetic pool | Published source rows | Net additional training pairs needed per published row |
| --- | ---: | ---: |
| DODa-grounded only | 226,000 | 1.964 |
| Grounded and exploratory | 452,000 | 0.982 |

The average includes rows that yield zero after grouping, holdout exclusion, or filtering. For example, two net accepted pairs per grounded source row would give approximately 608,219 total training occurrences. The human v1 training screen yielded about four accepted pairs per assigned training sentence. That is a rough point of comparison. The synthetic yield and quality remain unmeasured.

A secondary Darija option, DODa-10K, offers human-reviewed Arabic and Latin Darija columns and an MSA translation. It derives from DODa, so it may duplicate source rows. Its MSA column has no corresponding MSA Arabizi transcription. [DODa-10K data card](https://huggingface.co/datasets/MBZUAI-Paris/DODa-10K)

## MSA and phrase coverage

The reported phrase `asba7na wa asbaha lmolko lilah` is an invocation, **أصبحنا وأصبح الملك لله**, typed using informal Arabizi. A reference source provides the Arabic text and a formal romanization, which differs from the user's Latin spelling. DODa-500K is a Darija expansion. We found no verified large corpus of human MSA pairs with Moroccan-style Latin input. A separate reviewed phrase set would measure this register directly and retain the original spaces and attached clitics for editor replay. Word-pair expansion alone cannot verify phrase spacing or context behavior. [Arabic text and formal transcription](https://sunnah.com/hisn:77) · [Arabizi dataset study and treatment of MSA](https://aclanthology.org/2026.findings-emnlp.900.pdf)

## Proposed next action

Fetch the pinned combined object locally and verify the LFS checksum. Sample grounded and exploratory rows independently with a fixed seed. Measure schema validity, sentence overlap, alignment yield, and manually check candidate word pairs for shifted boundaries, incorrect characters, and spelling conventions. Use the grounded sample first to decide whether it can cover the gap. Keep synthetic additions out of the existing validation and test assignments and filter overlaps against their sentence keys before word extraction. No corpus rows were downloaded during this source audit.

## Verified local sample

Downloaded the full 229,170,725-byte object from GitHub's LFS batch endpoint and verified the pinned SHA-256. The direct media URL timed out. A streaming scan counted 48,350 human, 226,000 grounded, and 226,000 exploratory rows and confirmed the source fields `darija_latin`, `darija_arabic`, and `generation_mode`.

Sampled 1,000 rows per synthetic group using Python `Random(42)` and row positions within each group. Compared normalized full-sentence keys with the original human corpus, removed exact normalized bilingual sentence duplicates within each sample, and split both sides on whitespace. Required equal token counts, one normalized token per whitespace segment, and compatible scripts or matched digit anchors. Excluded digit-only anchors from the pair count and applied the current model's input and output length bounds.

| Sample | Rows passing | Candidate occurrences | Distinct Latin–Arabic pairs | Distinct pairs new versus v1 training |
| --- | ---: | ---: | ---: | ---: |
| Grounded | 464 / 1,000 | 4,383 | 2,542 | 1,641 |
| Exploratory | 301 / 1,000 | 2,674 | 1,518 | 962 |

Unequal whitespace counts affected 355 grounded and 398 exploratory rows. A further 167 and 291 respectively had segments with multiple normalized tokens or no token, such as text split by internal punctuation. No sampled rows matched the normalized human sentence keys or duplicated a full pair within their own sample. Neither observation rules out overlap in a full scan.

Reviewed 30 candidate occurrences per group in sentence context. Many were plausible, but equal lengths still admitted shifted pairings. In grounded row 10121, `drari` aligned to غايحدر and `f` aligned to الدراري after a missing Latin name token and an attached Arabic preposition offset each other. In exploratory row 412672, `man` aligned to ما, losing part of the word at a boundary. These examples are why positional matches need alignment checks before they become training labels.

The grounded sample yields 4.383 screened occurrences per source row, above the 1.964 needed for the occurrence target. This is a count of candidates. It does not establish accepted yield or a total of 600,000 distinct pairs. Unique counts from a small sample cannot be scaled linearly because later sentences reuse words. V1 itself has 156,219 training occurrences, 42,698 distinct Latin–Arabic pairs, and 37,365 distinct Latin forms.

**Proposed next action:** Scan the full grounded subset and count candidates both before and after deduplication by `(Latin, Arabic)`. Report the full counts, overlap, and conflicting references before selecting a training dataset. Retain occurrence counts as metadata so we can compare uniform sampling over distinct pairs with controlled replay of common forms later. The corpus remains local and no training ran.

## Full grounded scan

Applied the sample screen to all 226,000 grounded rows of the verified object. Deduplicated full sentences by the combined lowercased Latin and Arabic keys, and excluded matches against either normalized human sentence key. Counted word occurrences before deduplicating exact, case-sensitive `(Latin, Arabic)` pairs.

| Measure | Count |
| --- | ---: |
| Grounded rows passing the screen | 109,476 |
| Rejected for unequal whitespace counts | 78,760 |
| Rejected for non-single-token segments | 35,509 |
| Rejected for incompatible scripts or number anchors | 2,195 |
| Duplicate grounded sentences skipped | 53 |
| Human sentence overlaps skipped | 7 |
| Grounded candidate word occurrences | 1,025,464 |
| Distinct grounded Latin–Arabic pairs | 124,712 |
| Distinct pairs absent from v1 training | 115,108 |
| Distinct grounded Latin forms | 98,984 |
| Grounded Latin forms with multiple Arabic references | 14,591 |
| Combined v1 and grounded candidate occurrences | 1,181,683 |
| Combined v1 and grounded distinct pairs | 157,806 |

The grounded pool exceeds the occurrence target before additional alignment quality checks. Even the combined pool remains far below 600,000 distinct pairs. Conflicting references can be valid spelling variants or alignment errors. This scan counted them without choosing a target. It excluded full-sentence matches by the existing keys. Near-duplicate overlap and indirect variant links still require review before using the pool as training data.

**Proposed next action:** Test a small alignment quality filter against manually reviewed pairs and measure the resulting yield. Use the grounded pool first since it already has enough candidate occurrences to support filtering. Keep exact pair counts and occurrence weights available for the sampling decision.

## Frequent-word reference check

Tested one proposed quality rule on the same 1,000-row grounded sample. It flags a candidate when the exact Latin form appears at least 20 times in v1 training and the candidate Arabic spelling never appeared with that form. The rule flagged 67 of 4,383 candidates (1.53%).

Using seed 42, drew 16 flagged and 16 unflagged occurrences without replacement, after drawing the grounded sentence sample. Reviewed each candidate in context. “Plausible” allows a spelling variant that preserves the word and grammatical content. “Unclear” includes cases where the intended interpretation needs another reviewer.

| Review group | Plausible | Clear mismatch | Unclear |
| --- | ---: | ---: | ---: |
| Flagged | 11 | 4 | 1 |
| Unflagged | 16 | 0 | 0 |

Flags caught shifted `f` → الدراري, added negation in `ghadi` → غاديش, an added preposition in `l3am` → للعام, and a register change from `hadi` to هذه. They also caught plausible spellings such as `yallah` → يلاه, `hit` → حيت, and `akhor` → اخر. The `mochkil` → مشكلة example was unclear because the reference changes the word's form and gender. The sample deliberately oversampled flagged pairs. It cannot establish population precision, false-negative rate, or recall.

**Decision proposed:** Keep the rule as a review flag. Treating it as an automatic filter would discard 11 plausible pairs in the 16 reviewed flags. Try a sentence-level alignment check that requires multiple known word pairs to support a consistent shift before rejecting a sentence. Measure it on a fresh sample so the examples that motivated it do not determine its score. No corpus labels or splits changed in this check.

## Sentence-level shift check

Drew a new sample of 3,000 grounded rows with seed 43. Used the same whitespace, script, length, and human-overlap checks. Of the 1,488 sentences that passed the row screen, 12 (0.81%) were flagged for a possible one-position shift.

The rule requires two adjacent, distinct Latin forms that each occur at least 20 times in v1 training. Their current positional references must be unseen for those forms, and both references one position away in the same direction must be attested at least twice in v1. The rule flags the sentence for exclusion review and does not attempt to repair its alignments.

| Reviewed sentences | Confirmed boundary shift | No clear boundary shift |
| --- | ---: | ---: |
| All flagged | 12 | 0 |
| Random sample of unflagged | 0 | 16 |

For example, row 286343 splits the name `fatimezahra` into فاطمة الزهراء, shifting several following words. A later boundary change offsets the name split, so sentence token counts still agree. Row 304516 attaches the Latin conjunction and following Arabic token differently, and several positions then align one word away. In contrast with the earlier single-reference flag, the reviewed matches show a consistent shift across multiple words. This small sample does not establish recall or the precision of the rule on the full pool.

**Proposed next action:** Apply this shift check to the full grounded pool and build a reproducible candidate manifest. Report surviving counts, exact pair deduplication, conflicting references, and sentence overlap with the existing splits. Choose a 600,000-occurrence training mix only after reviewing those counts. No corpus labels or splits changed in this evaluation.

## Grounded candidate manifest after shift screening

The [manifest builder](../grounded_manifest.py) verified the source and v1 input checksums. It recorded the accepted one-based source line numbers in the ignored local file `data/doda-grounded-candidate.json`. The manifest SHA-256 is `6b5650ec43ac7eb385addd3d98b658fe44225d76d21c33376b1b326c27c887bd`.

The full shift screen removed 532 of the previously accepted grounded sentences, leaving 108,944. Seven human sentence-key overlaps were skipped, all from train. No exact normalized matches with validation or test were detected. This check does not cover all near-duplicate sentences.

| Candidate pool | Occurrences | Distinct Latin–Arabic pairs | Distinct Latin forms | Forms with multiple Arabic references |
| --- | ---: | ---: | ---: | ---: |
| Grounded after screening | 1,014,353 | 119,415 | 98,173 | 13,808 |
| Grounded plus v1 train | 1,170,572 | 152,520 | 123,775 | 18,537 |

There are 109,822 grounded pairs absent from v1 training. These are automatically screened candidates and retain potential reference errors. No new model was trained. The user approved using roughly one million occurrences, so there is no need to trim the pool to 600,000.

**Proposed next action:** Build one local Colab-ready training artifact with the surviving grounded rows and original human training data. Preserve the exact-pair counts and human versus synthetic provenance so training can control how often repeated pairs are sampled. Keep the existing validation data for direct comparison.

## Local v2 training artifact

The [dataset builder](../build_grounded_dataset.py) assembled `data/doda-word-pairs-v2.json` from the verified candidate manifest. It contains **1,170,572 training occurrences**, consisting of 156,219 original human rows and 1,014,353 screened grounded rows. It records source and record identifiers per training occurrence and separate human and grounded counts for each of the **152,520 distinct pairs**. Its 20,081 validation rows exactly equal v1 validation. The artifact contains train and validation only.

The local file is 124,135,191 bytes. SHA-256 `0ce61f1d95a6aa9c4932e883e116b82b009d3411149d8e9e6fce852e88a9121e`. Reopened the output and checked the original human rows, validation equality, and every source-specific pair count. Corpus files remain ignored by Git.

```sh
python -m project_tools.build_grounded_dataset data/doda-500k.jsonl data/doda-grounded-candidate.json \
  data/doda-word-pairs-v1.json data/doda-word-pairs-v2.json
```

**Proposed next action:** Add a v2 Colab notebook configuration that verifies the new digest and compares both architectures using the same v1 validation slices. Preserve the v1 definitions of common and unseen for comparison, since using v2 training frequency alone would change what those slices measure. The current notebook still expects the v1 filename and checksum.
