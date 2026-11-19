# Scratchpad sentence error audit

This local audit traced a mixed Darija and formal Arabic input through the installed GNOME scratchpad, the persistent predictor process, and the epoch-six word model. It confirmed that the app sends one word at a time and restores separators around each prediction. The word-level model reproduced the observed errors on the same tokens, so the mismatch came from model output rather than punctuation assembly.

The audit also checked whether limiting repeated Latin characters could recover elongated spellings. That normalization improved a few tokens in the example but did not resolve the phrase-level errors. Applying the cap globally was therefore evaluated separately against unchanged validation data; it did not become the primary fix.

The main engineering finding was that some errors require phrase context and spacing decisions beyond independent word prediction. These cases motivated explicit phrase checks and the separate sentence-level Transformer pilot. This audit used development material only; it did not change the model or access the locked test.
