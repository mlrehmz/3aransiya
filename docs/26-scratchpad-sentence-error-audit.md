# Scratchpad sentence error audit

The GNOME launcher points to the epoch-six encoder–decoder bundle `bundle-d4307181ae640820`. The scratchpad submits individual words to its predictor and renders their outputs with the original separators. We replayed the original sentence's tokens through that same installed bundle on Fedora CPU and reproduced the reported output token for token. We then shortened runs of three or more identical letters to at most two and queried the same model again.

| Original | Original output | Shortened | Output after shortening |
| --- | --- | --- | --- |
| `ssss` | السني | `ss` | الس |
| `yaaaaaaaa` | يارا | `yaa` | يا |
| `haaaaaaa` | هارا | `haa` | ها |
| `xtiiiiiii` | ختيريبي | `xtii` | ختي |
| `sallllllla` | ساللة | `salla` | سالا |
| `llllaho` | الله | `llaho` | الله |

The expected phrase is **صلى الله عليه وسلم**. The shortened input produces **سالا الله عاليه وصلام**. The app submits `3alayhi` and `wasallam` independently, so they produce the same outputs in isolation as in the phrase. Shortening helps with expressive elongation in this example. The phrase errors require a separate check.

The intended spelling or meaning of `ssss`, `wlahramar`, `ahayani`, and `dksti` needs user review before those tokens can be scored. The sample is a development example. It provides no estimate of corpus-wide accuracy. The app, model, and locked test were untouched.

## Proposed next experiment

Build a small local comparison on reviewed examples. Test a cap of two repeated Latin letters and a narrow phrase lookup for known expressions with accepted spellings. Include ordinary words with doubled letters, variants of the full phrase, and near matches that should pass through. Measure which errors each change fixes and time both paths on Fedora before proposing an app change or a training run.
