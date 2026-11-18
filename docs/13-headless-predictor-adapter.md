# Headless predictor adapter

The scratchpad's [prediction worker](../scratchpad/worker.py) accepts a callable that takes a word and returns one prediction. The [process adapter](../scratchpad/process_predictor.py) fits that interface and keeps a helper alive across requests. This lets the GTK launcher use Fedora's system Python while the helper uses the project's Python 3.14 PyTorch environment.

The helper signals readiness after its predictor is initialized. Each subsequent request and response is one size-limited JSON line over local pipes. The parent sends one request at a time. A per-word prediction error leaves the process available for the next word. Startup failures, timeouts, and malformed responses close and reap the child. Callers serialize prediction and cleanup, and arrange startup and teardown outside the GTK event loop.

Four synthetic tests covered worker integration, continued use after a per-word error, startup and prediction timeouts, malformed responses, and cleanup. A separate check sent two requests from Fedora's system Python to the same project Python 3.14 helper. System Python passed 29 tests and skipped three PyTorch tests. The project environment passed 28 tests and skipped four GTK tests. This step used synthetic predictions and made no GTK or GNOME extension changes.

**Proposed next step:** Add an opt-in helper launch to the GTK app and exercise it with the synthetic predictor. Verify that startup stays off the GTK event loop and that a helper failure keeps the current draft intact before connecting trained weights.

## Opt-in GTK smoke test

From the repository root, launch the synthetic helper mode with Fedora's system Python. The helper uses the existing project Python 3.14 environment at `.venv/bin/python`.

```sh
ARANSIYA_SYNTHETIC_HELPER=1 python -m scratchpad
```

This mode uses a separate GTK application ID so it can run alongside the standard scratchpad. The first word request starts the helper on the prediction worker thread. Successful previews and separator commits use the existing Arabic output row. Typing `fail!` triggers a synthetic per-word failure and leaves the Arabizi draft intact. Subsequent words can use the same process. The worker closes the helper on exit, and the launcher waits for cleanup after the GTK event loop returns.

A smoke test on the Fedora desktop verified the thread used for startup, preview and commit, draft preservation after failure, a successful subsequent commit using the same helper, and worker shutdown. It used synthetic input and output. The GNOME extension and standard mock launch were outside this change.
