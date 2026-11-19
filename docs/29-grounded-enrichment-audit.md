# Grounded v2 enrichment audit

The pinned Darija v2 pool has 1,170,570 usable training occurrences. Of its Latin forms, 86,410 appear in grounded synthetic training only. We counted exact Arabic targets per Latin form and compared each eligible form's most frequent target with the epoch-six CTC output, which is the fallback for these forms in the strongest route. Eligibility used training counts only. Scores use the existing development validation.

| Minimum matching occurrences | Target agreement | Eligible training forms | Validation occurrences covered | CTC correct | Lookup correct |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 90% | 16,470 | 234 | 150 | 163 |
| 5 | 90% | 10,034 | 158 | 100 | 114 |
| 10 | 95% | 3,846 | 84 | 55 | 60 |

At five occurrences and 90% agreement, the lookup gained 14 correct predictions, equivalent to roughly 0.07 percentage points across the 20,081 validation occurrences. This is a development estimate because the thresholds were compared on the same validation set. Grounded occurrences can share sentence sources, so frequency alone does not establish independent confirmation.

The next training experiment should enrich the existing pool with reviewed spelling variants and report results separately for forms still unseen in v2. Separate rows by spelling family before creating variants so validation can reveal transfer to new families. Keep reviewed MSA phrases as a separate slice with phrase-level references and clitic spacing. The current pool contains Darija word pairs, and this audit measures the value of observed spelling coverage. No training, app change, or locked-test evaluation ran.
