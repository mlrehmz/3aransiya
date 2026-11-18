"""Run an offline word predictor in a separate, persistent Python process."""

import json
import os
import selectors
import subprocess
import sys
from time import monotonic


_MAX_LINE = 4096


class PredictorError(RuntimeError):
    """The helper could not produce a usable prediction."""


class ProcessPredictor:
    """Own one helper process. Calls to predict and close must be serialized."""

    def __init__(self, command, *, startup_timeout=15.0, prediction_timeout=1.0):
        self._timeout = prediction_timeout
        self._buffer = bytearray()
        self._process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0,
        )
        try:
            if self._read(startup_timeout) != {"ready": True}:
                raise PredictorError("predictor did not send a readiness message")
        except BaseException:
            self.close()
            raise

    def _read(self, timeout):
        deadline = monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self._process.stdout, selectors.EVENT_READ)
            while True:
                end = self._buffer.find(b"\n")
                if end >= 0:
                    line = bytes(self._buffer[:end])
                    del self._buffer[:end + 1]
                    try:
                        return json.loads(line)
                    except (UnicodeError, ValueError) as error:
                        raise PredictorError("invalid predictor response") from error
                if len(self._buffer) >= _MAX_LINE:
                    raise PredictorError("predictor response exceeded size limit")
                remaining = deadline - monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise PredictorError("predictor response timed out")
                chunk = os.read(self._process.stdout.fileno(), _MAX_LINE - len(self._buffer))
                if not chunk:
                    raise PredictorError("predictor exited without a response")
                self._buffer.extend(chunk)

    @property
    def closed(self):
        return self._process.stdin.closed

    def predict(self, word):
        process = self._process
        if self.closed:
            raise PredictorError("predictor is closed")
        message = json.dumps(word).encode("ascii") + b"\n"
        if len(message) > _MAX_LINE:
            raise PredictorError("predictor request exceeded size limit")
        try:
            written = process.stdin.write(message)
            if written != len(message):
                raise PredictorError("incomplete predictor request")
            response = self._read(self._timeout)
            if response != {"error": True}:
                if (not isinstance(response, dict) or set(response) != {"output"}
                        or not _valid_output(response["output"])):
                    raise PredictorError("invalid predictor response")
                return response["output"]
        except (OSError, PredictorError):
            self.close()
            raise
        raise PredictorError("predictor could not convert the word")

    def close(self):
        process = self._process
        process.stdin.close()
        try:
            process.wait(timeout=0.2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        finally:
            process.stdout.close()


def _valid_output(output):
    return isinstance(output, str) and bool(output) and not any(c.isspace() for c in output)


def serve(predict):
    """Serve an initialized predictor over stdin and stdout."""
    print('{"ready":true}', flush=True)
    while line := sys.stdin.buffer.readline(_MAX_LINE + 1):
        if len(line) > _MAX_LINE or not line.endswith(b"\n"):
            return
        try:
            word = json.loads(line)
            output = predict(word) if isinstance(word, str) else None
            if not _valid_output(output):
                raise PredictorError("invalid prediction")
            response = json.dumps({"output": output})
            if len(response) >= _MAX_LINE:
                raise PredictorError("prediction exceeded size limit")
        except Exception:
            response = '{"error":true}'
        print(response, flush=True)
