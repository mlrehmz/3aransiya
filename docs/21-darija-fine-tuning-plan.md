# Targeted Darija fine-tuning plan

Start from the verified epoch-six encoder–decoder `bundle-d4307181ae640820`. Keep its architecture, ordered alphabets, and decoding limits. Both models already support پ. The [spelling baseline](20-darija-correction-set-draft.md#baseline-before-fine-tuning) points to a limited test of data coverage before spending time on architecture changes or Modern Standard Arabic (MSA) pretraining.

## Training data and schedule

1. Freeze the reviewed spelling labels and held-out word families in versioned files with checksums. Keep `2o`, the pizza spellings, and the full provisional `prizontasyon` label out of training until confirmed. Retain the excluded labels in the review notes so decisions remain traceable.
2. Read the existing checksum-verified DODa development artifact. Use only original training rows for replay. Exclude rows for the declared held-out families and remove exact correction inputs that conflict with the reviewed target. Report eligible and removed counts. The starting weights can still reflect earlier DODa exposure to attested forms.
3. Run one short Colab T4 experiment with a fresh AdamW optimizer, learning rate `0.0001`, gradient clipping at `1.0`, seed 42, and **128 optimizer steps**. Start with four reviewed correction examples and 124 original training occurrences per batch. Cycle deterministically through the small correction set and draw replay occurrences in a reproducible order without replacement. This is a starting recipe. Record the observed correction mix and exact settings.
4. Keep checkpoints in a fresh local Colab output directory. Record the starting bundle digest, corpus and label digests, optimizer state, random state, and next batch position. Use the existing two-slot checkpoint pattern and save after each optimizer step. A runtime reset requires restoring downloaded outputs to resume. Export the final bundle in the existing v1 format for the Fedora helper.

## Checks and decision

- Score the starting model and the fixed step-128 candidate with the same inference path. Report exact matches for the reviewed correction examples and the held-out families. Break out the novel `X7al` and `xrebt` spellings, the خ controls, and the hamza controls. Keep the held-out spellings closed during training and use them for this before-and-after comparison.
- Run the unchanged development benchmark on both models. Report strict and variant-aware common, overall, and unseen scores with counts and missing predictions. Flag a decrease greater than **0.5 percentage points** in any strict slice for review before considering the candidate for daily use. That threshold is a proposed pilot safeguard. Also show individual gains and regressions on the small spelling set because one example changes its percentage substantially.
- Record whether the candidate corrects `Xa` and preserves previously correct controls such as `khobz`, `ka2s`, and `ra2y`. If corrections improve but novel spellings do not, add more reviewed training families before trying another schedule. Keep the locked release test closed and the current Fedora bundle selected until the comparison is reviewed.

For a later MSA experiment, use the same architecture and Darija fine-tuning protocol with a separately prepared MSA start. Compare final scores against this Darija-only pilot. MSA corpus selection and training are separate decisions.

**Proposed next action:** Review the draft labels, then prepare the resumable notebook from the approved label set. Keep unresolved labels excluded unless their expected Arabic is supplied.
