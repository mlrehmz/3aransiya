# Shared model pilot data loader

**18 November 2026 · Verified on Fedora**

Both GRU candidates will load the same [pinned development artifact](03-training-alignment-pilot.md#first-extractor-results) through [model_pilot.data](../model_pilot/data.py). The loader verifies the artifact digest, builds sorted character vocabularies from training only, and enumerates distinct validation inputs for prediction export.

Batches carry padded input and target tensors and their original lengths on CPU. Input IDs reserve zero for padding and one for unknown characters. Target characters start at one, with zero used for padding outside the target length and for blank in CTC outputs. The encoder–decoder can add its own sequence markers when it builds decoder sequences.

The loader checks the 18-character input and 17-character Arabic target bounds and verifies CTC feasibility for every training row. Its frame calculation adds one frame for each adjacent repeat in the target. Invalid training rows report their source record and token index.

| Verified result | Value |
| --- | ---: |
| Training occurrences accepted | 156,219 |
| Distinct validation inputs | 8,357 |
| Observed Latin / Arabic characters | 64 / 51 |
| Example batch input / target shape | 128 × 10 / 128 × 8 |

A fixture verified casing, Arabizi digits, unknown input IDs, padding, and rejection of a repeated-letter target under an insufficient frame budget. The CPU environment passed 22 tests and skipped four GTK-dependent tests. System Python passed 25 tests and skipped the PyTorch-dependent fixture. No training or Kaggle run was performed.

**Proposed next step:** Implement the encoder–decoder's forward pass and bounded greedy decoding. Verify it on synthetic batches locally, including a batch with mixed input lengths and the end-of-sequence limit. Keep corpus training on Kaggle.
