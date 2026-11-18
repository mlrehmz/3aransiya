# Offline inference bundle v1 proposal

The Kaggle training export should produce a small, versioned directory that the Fedora prediction helper can open locally. Both [GRU candidates](07-shared-model-pilot-design.md) share the format. The app continues to send one word at a time through the [predictor process](13-headless-predictor-adapter.md).

## Files and compatibility

The bundle has two fixed filenames. Pass its directory explicitly to the helper.

| File | Contents |
| --- | --- |
| `manifest.json` | UTF-8 JSON, at most 32 KiB, with the fields below |
| `weights.pt` | At most 8 MiB, containing only the model state dictionary of detached CPU FP32 tensors |

| Manifest field | v1 contract |
| --- | --- |
| `format_version` | Integer `1` |
| `architecture` | `gru_encoder_decoder_v1` or `bidirectional_gru_ctc_v1`. Each ID selects a fixed class in the shipped code. |
| `input_chars`, `target_chars` | Training vocabulary arrays of unique, NFC-normalized, single characters, in exact ID order. Preserve the saved ordering. |
| `normalization` | `nfc_case_sensitive_v1`. Preserve case and embedded Arabizi digits. |
| `max_input_length`, `max_target_length` | Integers `18` and `17`, measured in normalized Unicode code points. |
| `ctc_expansion` | Integer `9` for GRU/CTC and JSON null for the encoder–decoder. |
| `weights_sha256` | SHA-256 of the exact `weights.pt` bytes, as 64 lowercase hexadecimal characters. |
| `source_checkpoint_sha256`, `word_pairs_sha256` | Identifiers for the training checkpoint and development artifact used by the export. |
| `source_revision`, `export_torch_version` | Code revision and full PyTorch version used to export. |

Vocabulary IDs follow the [shared loader](10-shared-model-data.md). Input padding and unknown are 0 and 1. Arabic characters start at 1. Target ID 0 is padding or CTC blank according to the architecture. The encoder–decoder appends BOS and EOS after the target character IDs. An incompatible change to layout or decoding requires a different architecture or format version.

## Export and load

1. On Kaggle, restore the chosen training checkpoint and construct the matching model using its saved vocabulary. Export its state dictionary as CPU FP32. Keep the optimizer, scheduler, corpus, and training checkpoint outside the inference bundle.
2. Write the two files into a new staging directory, then check the saved metadata, digest, and greedy output parity. Publish the complete directory under a new versioned path. A failed export leaves the previously selected directory available. Record the manifest SHA-256 with the exported artifact so the recipient can verify both files against the trusted export record.
3. On Fedora, bound reads and validate the manifest version, architecture, vocabulary, and limits before loading weights. Hash the bytes that will be loaded, compare with the manifest, and use explicit `torch.load(..., map_location="cpu", weights_only=True)` on those verified bytes. Require exact tensor names, shapes, CPU FP32 dtype, and finite values. Use trusted project exports. The embedded digest detects corruption and does not authenticate the publisher. [PyTorch 2.11 serialization notes](https://docs.pytorch.org/docs/2.11/notes/serialization.html#weights-only-security)
4. The helper constructs the allowlisted model, switches it to evaluation mode, sets one PyTorch inference thread, and runs a warm-up before sending readiness. Once ready, it accepts one NFC-normalized word per request. Encode unknown input characters with UNK. Return one valid word drawn from the target vocabulary or a prediction error for empty, unfinished, or overlength output. An overlength input fails without truncation. Failed prediction or startup preserves the GTK draft through the existing error path. The model path uses local files and pipes. Typed words are not logged. The existing GTK tokenizer controls which inputs reach it, including standalone digit passthrough.

## Acceptance checks

- For both architectures, compare the original checkpoint-loaded model on CPU with the exported bundle opened by the Fedora loader. Require identical greedy results for a fixed development fixture, including case and embedded digits, maximum-length input, and repeated Arabic output where applicable. Include at least one nonempty result for each trained candidate. Keep the locked test closed.
- Before training, run the same checks with synthetic states for both architectures and at least one controlled successful prediction per architecture. Exercise missing and corrupted files, unsupported versions, and incompatible tensor shapes. Verify that load failures prevent readiness and that an individual bad word does not stop subsequent requests.
- Verify local prediction with networking disabled and a fresh helper. Measure cold startup and warm inference separately once real weights exist.

**Proposed next step:** Implement the v1 bundle writer and CPU loader. Test both candidates with synthetic weights through the headless protocol before connecting a model-backed GTK launch.

## Implementation and verification

The [bundle writer and loader](../model_pilot/bundle.py) implement the v1 format. The exporter takes a model already restored by the training code, verifies its architecture and vocabulary, and returns the published manifest digest. It reloads the staged bundle before making it visible at the destination. The [inference helper](../model_pilot/inference_helper.py) loads and warms the model on one CPU thread before accepting requests over local pipes.

Synthetic state round trips returned identical greedy outputs before export and through the helper for both architectures. The checks covered case, embedded digits, an unknown character, maximum-length input, and a recoverable overlength request. Missing weights, a corrupted checksum, an unsupported version, and incompatible tensor shapes were rejected. The corrupted bundle exited before sending readiness. The isolated CPU environment passed 30 tests and skipped four GTK tests. System Python passed 29 tests and skipped five PyTorch tests.

Checkpoint restore from a Kaggle run, trained-weight parity, and model-backed GTK launch remain to be verified.

**Proposed next step:** Add an explicit bundle option to the GTK launcher and smoke-test the normal editor with a synthetic v1 bundle. Check that valid predictions reach the Arabic output row and that a bad bundle preserves the source draft.

## GTK bundle launch

From the repository root, launch the model-backed editor with Fedora's system Python. The model helper uses the existing project virtual environment.

```sh
python -m scratchpad --bundle /path/to/bundle
```

Each bundle path has its own GTK application identity. Reopening the same bundle focuses its existing window. The first prediction starts and warms the helper off the GTK thread. The standard and GNOME top-bar launch still use the development predictor.

On Fedora, a synthetic CTC bundle converted `T7!` to `ت!` in the Arabic row while preserving `T7!` in the source draft. With corrupted weights, the editor reported the failure and preserved the same draft. Both workers shut down. Trained weights have yet to be exercised in GTK.
