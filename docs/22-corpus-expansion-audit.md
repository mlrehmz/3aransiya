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
