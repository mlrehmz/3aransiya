# Training-only word alignment pilot

**18 November 2026 · Exploratory review**

This pilot tested whether a simple positional match provides plausible word supervision. It verified the [locked v2 assignment](02-doda-sentence-split.md#locked-v2-assignment) and source checksums before sampling. Only the 38,999 training sentences were eligible. Record 2287 was flagged during the earlier split review. Its suitability for extraction depends on its v2 assignment and the extraction rules.

## Method

- Tokenize with the split's NFC and Unicode alphanumeric rules, keeping Latin case and dropping Arabic nonspacing marks. Screen for equal token counts and require each position to contain a Latin-bearing token and an Arabic-bearing token, or identical standalone ASCII digits. Permit embedded ASCII digits. Exclude standalone digit pairs from the candidate word count.
- Select 40 occurrences per stratum in this order: one-character Latin tokens, tokens containing any of `235789`, likely French loanwords, words in sentences with matching standalone digit tokens, and a general sample. The digit-anchor stratum probes alignment around numbers and mixed-language boundaries. It does not directly sample every merge/split pattern because the initial gate requires equal lengths.
- Build pools in CSV record order and ascending token position. For each stratum, filter out previously selected records, shuffle with a shared Python 3.15.2 `random.Random(42)`, and take the first 40 occurrences from distinct sentences. This yielded 200 unique sentences. The loanword stratum uses exact membership after lowercasing in this exploratory list:

  ```text
  auto avion banque basket bus café cafe camion classe coca collège college
  docteur école ecole film garage hôtel hotel internet match métro metro
  musique parking police portable radio restaurant sac sandwich sport stade
  taxi téléphone telephone téléphon train télé tele tomobil tomobile visa
  ```

- Review each pair with both full tokenized sentences. Accept a plausible spelling of the corresponding word at that position, including common orthographic variation. Reject a shifted pairing, a translation in place of a transliteration, or a clear reference mismatch. Mark unclear readings for exclusion pending review. One reviewer judged the sample.

## Results

Of the 38,999 training sentences, 35,948 had equal token counts and 35,879 passed the script screen. Together they supplied 156,227 candidate word occurrences.

| Stratum | Plausible | Reject | Unclear |
| --- | ---: | ---: | ---: |
| Single-character Latin token | 39 | 1 | 0 |
| Arabizi digit | 40 | 0 | 0 |
| Likely French loanword | 40 | 0 | 0 |
| Sentence with matching standalone digits | 36 | 1 | 3 |
| General sample | 37 | 1 | 2 |
| **Total** | **192** | **3** | **5** |

This is a deliberately stratified diagnostic. The 192/200 result describes the reviewed sample and does not estimate corpus-wide precision or the release accuracy gate. The small loanword list and single-reviewer judgments limit coverage.

Record numbers below refer to the pinned source. Token indices are zero-based.

| Record and token | Judgment | Reason |
| --- | --- | --- |
| 19156:1 | Reject | A separated Latin prefix maps positionally to a whole Arabic verb. Another boundary difference offsets the merge, so the sentence passes the equal-length screen. |
| 13084:3 | Reject | French `mois` is translated as شهور rather than transliterated. |
| 2102:2 | Reject | The reference غنا does not match the expected reading of `8na` in the sentence. |
| 12919:2, 44345:3, 13215:1 | Unclear | The words or context are too unclear to confirm the mapping confidently. |
| 25219:6, 31963:0 | Unclear | The Latin and Arabic spellings track one another loosely, but the intended reading is unclear in context. |

Some plausible pairs still have more than one acceptable reference. For example, `tomobil` occurs with initial ت and ط. Single-character inputs can also expand legitimately, as with `f` → في, so token length alone is a poor rejection rule.

## Next decision

**Proposed, pending approval:** Implement a conservative first extractor using equal token counts and script-compatible positions. Preserve Latin case, source IDs, and offsets. Pass identical standalone digits through the audit as anchors and exclude them from model examples. Keep a record/token exclusion list for the eight reviewed rejects and unclear cases, and report conflicting references without silently selecting a spelling. Use the approved split manifest to restrict development to train and validation.

The screen admits some silent boundary shifts and reference errors. Measure the resulting coverage and audit further examples before adding merge/split recovery or a more complex aligner.

## First extractor results

The approved [extractor](../word_pairs.py) verifies both input digests, reads only train and validation records for extraction, and writes an ignored local artifact. It preserves NFC Latin case and stores half-open character offsets into both original CSV fields. The eight reviewed exclusions were all applied. Matching standalone ASCII digits serve as alignment anchors and produce no word pairs.

| Measure | Train | Validation |
| --- | ---: | ---: |
| Assigned sentences | 38,999 | 5,039 |
| Sentences passing the screen | 35,879 (92.0%) | 4,649 (92.3%) |
| Unequal token counts | 3,051 | 380 |
| Incompatible scripts or numbers | 69 | 10 |
| Digit anchors | 146 | 25 |
| Review exclusions | 8 | 0 |
| Extracted word occurrences | 156,219 | 20,081 |
| Distinct case-sensitive Latin forms | 37,365 | 8,357 |
| Latin forms with multiple Arabic targets within the split | 4,109 | 472 |

Each emitted record belonged to its stated split. All source spans round-tripped to the emitted token after normalization. A repeat with a different Python hash seed produced identical bytes. The command rejected the v1 assignment and preserved the existing output. The v1 word-pair artifact SHA-256 is `842ba2460f0d4219cb90a41cca0cdc079d18fd1146d6756a9562833c9f2fbfbb`.

```sh
python -m word_pairs data/doda-sentences.csv data/doda-split-v2-candidate.json \
  data/doda-word-pairs-v1.json
```

### Fresh manual review

After extraction, I drew 15 candidate occurrences each from train and validation, using a shared `random.Random(20261118)`. For each split in that order, I sampled 40 output indices without replacement and took the first 15 from distinct sentences. I inspected both source sentences and the selected pair.

| Split | Plausible | Reject | Unclear |
| --- | ---: | ---: | ---: |
| Train | 14 | 1 | 0 |
| Validation | 13 | 1 | 1 |
| **Total** | **27** | **2** | **1** |

- Train record 3367, token 1 pairs `tomobil` with الطوموبيل, which adds the definite article. The same noun is recognizable, but the pair changes what the user typed.
- Validation record 13995, token 0 pairs `ilama` with إلا. The negation moves to the next Arabic token, so the positional pair loses part of the input.
- Validation record 23588, token 0 pairs `mxina` with مخينا. In context the intended verb appears to be “we went,” but the Arabic consonant differs from the reading suggested by the Latin form.

The fresh review shows that matching token counts still admits boundary and reference errors. These observations are recorded for the next rule decision. The output above includes all three newly flagged pairs. This small, single-reviewer sample cannot establish corpus-wide precision. No locked test pairs were reviewed.

**Proposed next decision:** Audit the 500 most frequent eligible training forms for reference ambiguity and measure their coverage and best-single-reference agreement on validation. This will help decide whether to tighten extraction before freezing the scoring protocol or training either model.
