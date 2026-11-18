# First GRU candidate

**18 November 2026 · Synthetic CPU verification**

The [encoder–decoder](../model_pilot/encoder_decoder.py) uses the [shared development vocabulary and padded batches](10-shared-model-data.md). It encodes valid input positions with a bidirectional GRU and concatenates the two terminal states to initialize the decoder. The loss predicts the Arabic characters and an end marker, ignoring positions beyond each target's end marker.

Greedy decoding returns one output per input. It emits at most 17 Arabic characters and can take one additional step to see an end marker. Empty predictions and predictions still unfinished after step 18 are reported as missing.

The candidate has **110,646 parameters** with the pinned training vocabulary. On synthetic CPU batches, the shorter row's valid logits matched its standalone forward pass, and the loss and all parameter gradients were finite. Controlled logits exercised immediate termination, a missing end marker, and acceptance of a 17-character output with an end marker on step 18. The CPU environment passed 23 tests and skipped four GTK-dependent tests. System Python passed 25 tests and skipped two model tests that require PyTorch.

This check used untrained weights and synthetic tensors. Model quality and latency remain unmeasured. Corpus training remains on Kaggle.

**Proposed next step:** Implement the bidirectional GRU/CTC forward pass and greedy collapse. Verify the frame lengths and repeated-letter behavior on synthetic batches before comparing the candidates.
