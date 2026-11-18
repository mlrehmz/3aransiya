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
