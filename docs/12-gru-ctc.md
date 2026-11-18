# Bidirectional GRU with CTC

The [CTC candidate](../model_pilot/gru_ctc.py) expands each encoded input position into nine frames. It uses the unpadded frame counts for CTC loss and decoding. Greedy decoding collapses adjacent duplicates before dropping blanks so a blank preserves a repeated letter. Empty predictions and outputs longer than 17 characters are treated as missing.

The candidate has 100,116 parameters with the pinned training vocabulary. Synthetic CPU checks verified padded batches, frame counts, repeated letters, finite loss and gradients, and rejection of empty or overlength outputs. The isolated CPU suite passed 24 tests and skipped four GTK-dependent tests. System Python passed 25 tests and skipped three PyTorch-dependent tests. Corpus training remains on Kaggle.
