# Headless predictor adapter

The scratchpad's [prediction worker](../scratchpad/worker.py) accepts a callable that takes a word and returns one prediction. The [process adapter](../scratchpad/process_predictor.py) fits that interface and keeps a helper alive across requests. This lets the GTK launcher use Fedora's system Python while the helper uses the project's Python 3.14 PyTorch environment.

The helper signals readiness after its predictor is initialized. Each subsequent request and response is one size-limited JSON line over local pipes. The parent sends one request at a time. A per-word prediction error leaves the process available for the next word. Startup failures, timeouts, and malformed responses close and reap the child. Callers serialize prediction and cleanup, and arrange startup and teardown outside the GTK event loop.

Four synthetic tests covered worker integration, continued use after a per-word error, startup and prediction timeouts, malformed responses, and cleanup. A separate check sent two requests from Fedora's system Python to the same project Python 3.14 helper. System Python passed 29 tests and skipped three PyTorch tests. The project environment passed 28 tests and skipped four GTK tests. This step used synthetic predictions and made no GTK or GNOME extension changes.

**Proposed next step:** Add an opt-in helper launch to the GTK app and exercise it with the synthetic predictor. Verify that startup stays off the GTK event loop and that a helper failure keeps the current draft intact before connecting trained weights.
