# Fedora training and inference comparison

The two-thread PyTorch CPU run resumed from batch 56 and finished all 9,146 updates. Both v2 runs used the same development dataset, architecture, optimizer settings, and update budget. The Fedora run changed the training mix from 13.35% to 25% human examples, changed batch order, and ran on a different device and PyTorch build. This comparison cannot isolate each change's effect.

| Strict validation | Original v2 T4 | Human-weighted v2 CPU | Change |
| --- | ---: | ---: | ---: |
| Common | 92.22% | 93.15% | +0.93 pp |
| Overall | 74.67% | 77.30% | +2.62 pp |
| Original unseen | 43.26% | 47.39% | +4.13 pp |
| Newly seen in v2 | 59.23% | 62.48% | +3.25 pp |
| Still unseen in v2 | 39.27% | 43.62% | +4.35 pp |

Variant-aware overall accuracy rose from 75.24% to 77.85%. Both runs predicted all 20,081 validation occurrences. The final bundle is `outputs/fedora-v2-human25/threads-2/bundle-3a6d6bc2cccb72a2`. The trainer verified its exported predictions against the in-memory model. The bundle manifest SHA-256 is `87614caea41484a9c3f6b450adb925e839ae05466080944d8f872171bfb08703`.

## Routing and spelling probes

The [routing experiment](../compare_model_routes.py) chooses an exact human-training lookup when the leading Arabic spelling has at least three occurrences and 90% agreement. Other forms seen in human training go to the encoder–decoder. Forms unseen in human training go to the epoch-six CTC model, with the encoder–decoder as a fallback if CTC emits no usable output. Source counts come from training only. The evaluation uses the 20,081 development occurrences. The locked test remains closed.

| Candidate | Common strict | Overall strict | Still unseen strict | Median word prediction | P95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Installed epoch-six encoder | 94.79% | 81.19% | 49.52% | 1.74 ms | 2.70 ms |
| Epoch-six CTC | 94.22% | 79.54% | 54.65% | 0.80 ms | 1.20 ms |
| Epoch-six routed with lookup | 94.79% | 82.37% | 54.65% | 0.87 ms | 2.19 ms |
| Epoch-six routed with lookup and repeated-letter cap | 94.79% | 82.36% | 54.61% | 0.88 ms | 2.20 ms |
| Human-weighted v2 with routing and lookup | 93.40% | 80.25% | 54.65% | 1.12 ms | 2.96 ms |

The strongest route improves overall validation by 237 correct occurrences and retains the installed model's common-word score. Variant-aware overall accuracy is 82.99%, up from 81.81%. The single-thread timing covers 8,357 distinct validation forms after bundle loading. It excludes startup, interprocess communication, and GTK rendering.

The narrow lookup for whole phrases produced **صلى الله عليه وسلم** for two checked spellings and **أصبحنا وأصبح الملك لله** for the supplied phrase. It left the punctuation-separated and truncated near matches on the word prediction path. Shortening repeated letters recovered **يا ها ختي** in the expressive-spelling probe and cost one strict match on the broader validation set when applied globally. The phrase examples are development checks of explicit rules. They do not measure generalization to new phrases.

The routed prototype preserves `ka2s` and `kas` as **كاس** and recovers `sport` as **سپور**. `Xa` and `prizontasyon` remain incorrect. The weighted encoder emits **و** for `2o` and the routed prototype emits **أو**. The intended reading remains ambiguous in isolation and was excluded from scoring.

The installed extension still uses the epoch-six encoder. The strongest candidate to evaluate next in the app is the epoch-six route with the human lookup. The full validation and probe report is saved locally at `outputs/fedora-v2-human25/routing-validation.json`.
