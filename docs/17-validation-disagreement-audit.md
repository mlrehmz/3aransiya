# Validation disagreement audit

Ran both archived bundles on the 8,357 distinct validation forms using the Fedora CPU loader. Selected validation occurrences where exactly one prediction matched under the existing pilot spelling rules. This was an error review, with no timing measurements.

There were 260 common occurrences matching only the encoder–decoder and 64 matching only GRU/CTC. On unseen forms, 288 matched only the encoder–decoder and 632 matched only GRU/CTC. Within each of those four groups, shuffled occurrences with a shared seed of 42 in sorted group order and retained the first five distinct forms. Reviewed each selected occurrence in its original DODa sentence. The balanced sample is intended to surface failure modes and cannot estimate their prevalence.

| Group | Record | Form | What the sentence shows |
| --- | ---: | --- | --- |
| Common, CTC only | 18376 | `taman` | تامان and تمان represent price. They differ in a written vowel. |
| Common, CTC only | 19578 | `tb9a` | تبقا and تبقى represent the same verb in context. |
| Common, CTC only | 6515 | `kolchi` | كولشي and كلشي both represent “everything” here. |
| Common, CTC only | 15524 | `lmochkil` | Encoder–decoder adds a final ي to المشكل. The source gives no support for the added ending. |
| Common, CTC only | 36486 | `hia` | هيا and هي both express the feminine pronoun here. |
| Common, encoder–decoder only | 22098 | `yallah` | CTC drops one ل in يالله. Whether to accept ياله needs an orthography decision. |
| Common, encoder–decoder only | 27701 | `tbib` | CTC writes ت in place of ط in طبيب. |
| Common, encoder–decoder only | 6908 | `kolchi` | The reference is كلشي here. The two models emitted the same outputs as in record 6515, whose reference was كولشي. |
| Common, encoder–decoder only | 30405 | `lhadra` | The encoder–decoder match uses a pilot equivalence. CTC's الهدرا is another plausible spelling in context. |
| Common, encoder–decoder only | 26927 | `lyouma` | CTC adds a final ا. The intended word remains recognizable. |
| Unseen, CTC only | 36577 | `wkat7es` | The two outputs differ in whether they write an internal ا. Both preserve the word and conjunction. |
| Unseen, CTC only | 39511 | `ytsdou` | The encoder–decoder transposes the consonants corresponding to `t` and `s`. |
| Unseen, CTC only | 4342 | `likayrb7o` | The encoder–decoder drops final و, losing the plural ending present in the source. |
| Unseen, CTC only | 3482 | `nnoD` | The encoder–decoder predicts ز and omits the doubled ن. |
| Unseen, CTC only | 31278 | `ouakha` | The encoder–decoder misses خ and introduces an extra syllable in “even if.” |
| Unseen, encoder–decoder only | 22234 | `nt7aawer` | CTC drops the written long vowel in نتحاور. |
| Unseen, encoder–decoder only | 9592 | `lmya` | الميا and المية both refer to one hundred in context. |
| Unseen, encoder–decoder only | 14028 | `mand5olx` | The Latin includes negation. The reference and matching encoder–decoder output omit the final ش. CTC ends in س. Neither preserves the expected negation spelling. |
| Unseen, encoder–decoder only | 9852 | `msta3edd` | CTC inserts ا in the word for “ready.” The intended reading is recognizable, but the vowel differs. |
| Unseen, encoder–decoder only | 43104 | `3ajabni` | CTC introduces an extra written vowel in عجبني. |

Two occurrences of `kolchi` show how reference choice can reverse which prediction is scored as correct. The negative `mand5olx` shows how agreement can reward a reference error. On unseen forms, the sample also contained recognizable model mistakes, including lost endings, reordered consonants, and missing or extra written vowels. These are single-reviewer judgments. No scoring rule, reference, or locked-test data was changed.

**Proposed next action:** Prepare one configurable, longer Colab comparison using the same corpus and scoring. Track validation by epoch for both models to see whether the encoder–decoder's common-word lead and CTC's unseen-word lead persist. Use a separate run directory to preserve the two-epoch baseline.
