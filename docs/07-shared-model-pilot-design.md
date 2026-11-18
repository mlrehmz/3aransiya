# Shared GRU model pilot design

**18 November 2026 · Proposal before implementation**

Compare two character models on the same [development word pairs](03-training-alignment-pilot.md#first-extractor-results) using the [validation benchmark](06-validation-benchmark.md). Measure how they generalize to unseen forms and how their inference cost differs on the target CPU. The locked test remains reserved for final evaluation.

## Shared data contract

Verify the pinned word-pair artifact before loading it. Build deterministic character vocabularies from training occurrences in Unicode order. Preserve input case and embedded Arabizi digits. Allocate Latin PAD and UNK IDs separately from the 64 observed characters. Use the same 51 observed Arabic characters for both models, with decoder-specific special tokens. Keep each eligible training occurrence and its single reference, with the same seed, batch composition, and epoch budget for both candidates. The spelling pilot applies to scoring.

| Measured property | Train | Validation |
| --- | ---: | ---: |
| Word occurrences | 156,219 | 20,081 |
| Maximum Latin length | 18 | 15 |
| Maximum Arabic length | 17 | 12 |
| Occurrences with unseen input or output characters | 0 | 0 |
| Largest minimum CTC expansion factor | 9 | 4 |

Use a pilot input limit of 18 characters and an output limit of 17 Arabic characters, plus an end step for the encoder–decoder. Encode unknown input characters with UNK and count affected words. Treat overlength inputs and invalid or unfinished outputs as missing predictions, which still count in scoring. The pilot bounds cover every current development pair and should be reviewed before packaging.

## Candidates and expected inference cost

Both candidates use 32-dimensional input embeddings and a single bidirectional GRU with 64 hidden units per direction. Use actual sequence lengths when encoding padded batches. Compare eager CPU inference with batch size one and one inference thread.

| Candidate | Head and greedy decoding | Estimated parameters |
| --- | --- | ---: |
| GRU encoder–decoder | Concatenate encoder terminal states to initialize the 128-unit decoder. Use 32-dimensional target embeddings with PAD, BOS, and EOS, teacher forcing during training, and sequential greedy decoding up to the output bound. | 110,646 |
| Bidirectional GRU with CTC | Project each 128-dimensional encoder state to nine frames of logits over 51 Arabic characters plus blank. Take framewise argmax, collapse adjacent duplicates, then remove blanks. | 100,116 |

The CTC path needs one encoder pass and a batched projection, with up to 162 frames. The encoder–decoder runs up to 18 sequential decoder steps after encoding. These are operation bounds. Measure latency before selecting a model. Parameter estimates assume a bias-enabled GRU and linear projections. [PyTorch GRU API](https://docs.pytorch.org/docs/2.15/generated/torch.nn.GRU.html)

A CTC target needs at least its character count plus one frame for each adjacent repeated character. The pilot computes this per training pair from unpadded lengths. Factor nine covers every pair, including the two most extreme factors of seven and nine. Factor four would leave 14 training occurrences infeasible. Start with nine to keep the comparison on the same rows. Reject infeasible pairs during preflight and report the cause if the artifact changes. [PyTorch CTC loss API](https://docs.pytorch.org/docs/2.15/generated/torch.nn.CTCLoss.html)

## Pilot handoff and checks

- A shared data loader owns vocabulary IDs, lengths, and batches. Each model owns its training loss and greedy decoding. The prediction exporter takes a trained model and emits the [benchmark JSON mapping](06-validation-benchmark.md) for distinct validation Latin forms in sorted order. The scorer owns reference normalization and scoring. Omit failed outputs and report the reasons.
- Start with a small fixture that exercises case preservation, an adjacent repeated Arabic letter, and shorter sequences in a padded batch. Verify the CTC preflight catches a deliberately infeasible frame count. Check emitted predictions end to end through the benchmark and verify missing outputs remain in the denominator.
- Use a local random-weight timing check, including the longest supported input and a decoder run that reaches its bound. Then overfit a tiny training batch for each model. A failed preflight or tiny-batch check stops the launch. Run the agreed two-epoch comparison only after both checks pass and the runtime and corpus permissions for the training environment are confirmed.
- Keep the first implementation local. Verify Python and PyTorch compatibility on the target host before pinning and installing the CPU runtime. Verify Kaggle compatibility and resolve private upload terms before any corpus transfer. The CPU timing check and GPU pilot are separate stages.

## Next decision

**Proposed, pending approval:** Verify a compatible PyTorch CPU build for the Fedora host and Python environment. Record the smallest supported runtime choice before adding dependencies or writing model code.
