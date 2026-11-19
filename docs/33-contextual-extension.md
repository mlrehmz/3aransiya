# Contextual scratchpad release

The final GNOME extension uses the tuned offline GRU and CTC profile. A 49 KB table adds 1,826 adjacent-word rules learned from the pinned human training pairs. Rules apply to forms with competing Arabic spellings and require at least four matching observations and 90% agreement in that context. Conflicting left and right rules defer to the existing word predictor.

The renderer preserves the exact source characters of English and French clauses that pass a conservative function-word check. It also renders reviewed Arabic expressions, including **علمت عنه من خلال قراءتي بعض كتب السلف**. These rules run before word rendering, so an English or French selection in a detected clause can be copied verbatim. The matcher is clause-based and does not reliably identify short or unpunctuated switches. The formal Arabic improvement is explicit phrase coverage and does not establish general MSA accuracy.

## Development checks

| Candidate | Exact sentences out of 512 | Character error rate | Foreign spans copied out of 5 |
| --- | ---: | ---: | ---: |
| Previous word release | 203 | 5.93% | 0 |
| Phrase and copy rules only | 203 | 5.93% | 5 |
| Contextual release | 204 | 5.88% | 5 |

The comparison reuses the fixed human DODa development sample and independently authored probes from the [Transformer pilot](32-sentence-transformer-pilot.md). Both new configurations also recovered the formal Arabic passage from the user draft. The 512-sentence sample shows a small Darija improvement. The five copy probes check specific errors and are too few to estimate generalization. The original locked word-test results belong to the previous release.

The full draft now renders as:

> [redacted Darija sample], علمت عنه من خلال قراءتي بعض كتب السلف, [redacted English sample]

## Build

Build the [base model](31-release.md#reproduce-the-model) first. The contextual builder verifies the human training pairs, writes a new profile, and verifies the context checksum. The source checkout includes the original symbolic **ض** icon outline.

```sh
.venv/bin/python -m project_tools.build_context_profile outputs/3aransiya-release \
  data/doda-word-pairs-v1.json outputs/3aransiya-contextual
/usr/bin/python extension/install.py --profile outputs/3aransiya-contextual
gnome-extensions enable scratchpad@3aransiya
```

Reproduce the comparison against the same development examples:

```sh
.venv/bin/python -m project_tools.evaluate_context data/doda-sentences.csv \
  data/doda-split-v2-candidate.json outputs/3aransiya-contextual
```

The local profile manifest SHA-256 is `a3b75a42f0a97a0551b426a1794242d6c6b63552e783831d8b5f2f1c58db51a7`.

## Fedora verification

The real GTK test verified the full pasted draft, unchanged source text, whole-draft copying, verbatim copying of a selection inside the English clause, reset, and loading the 16-pixel icon. The unit suite passed across the CPU environment and system GTK. GNOME reported the extension active, and a second launcher invocation refocused the existing contextual scratchpad.

The generated `outputs/scratchpad@3aransiya.shell-extension.zip` passed the archive integrity check. Its launcher refers to the checkout and profile on this Fedora machine. Use the installer above from a fresh checkout to generate those paths for another machine.
