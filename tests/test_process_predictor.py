import sys
from threading import Event
import unittest

from scratchpad.composition import PredictionRequest
from scratchpad.process_predictor import PredictorError, ProcessPredictor
from scratchpad.worker import PredictionWorker


HELPER = """
from scratchpad.process_predictor import serve
from time import sleep

def predict(word):
    if word == 'slow':
        sleep(30)
    if word == 'fail':
        return None
    return 'تجربة' + str(len(word))

serve(predict)
"""


class ProcessPredictorTests(unittest.TestCase):
    def test_worker_uses_one_helper_for_consecutive_requests(self):
        predictor = ProcessPredictor([sys.executable, "-c", HELPER])
        ready = Event()
        worker = PredictionWorker(predictor.predict, ready.set)
        try:
            for revision, (word, output) in enumerate([
                ("T7", "تجربة2"), ("fail", None), ("darija", "تجربة6"),
            ]):
                request = PredictionRequest(revision, word)
                self.assertTrue(worker.submit(request))
                self.assertTrue(ready.wait(3))
                ready.clear()
                result = worker.take_result()
                self.assertIs(result.request, request)
                self.assertEqual(result.output, output)
                self.assertEqual(result.failed, output is None)
        finally:
            worker.close()
            self.assertTrue(worker.join(3))
            predictor.close()
        with self.assertRaisesRegex(PredictorError, "closed"):
            predictor.predict("word")

    def test_prediction_timeout_closes_helper(self):
        predictor = ProcessPredictor(
            [sys.executable, "-c", HELPER], prediction_timeout=0.1
        )
        try:
            with self.assertRaisesRegex(PredictorError, "timed out"):
                predictor.predict("slow")
            with self.assertRaisesRegex(PredictorError, "closed"):
                predictor.predict("word")
        finally:
            predictor.close()

    def test_startup_timeout(self):
        with self.assertRaisesRegex(PredictorError, "timed out"):
            ProcessPredictor(
                [sys.executable, "-c", "import time; time.sleep(30)"], startup_timeout=0.1
            )

    def test_invalid_protocol_closes_helper(self):
        code = "print('{\"ready\":true}', flush=True); input(); print('bad', flush=True)"
        predictor = ProcessPredictor([sys.executable, "-c", code])
        try:
            with self.assertRaisesRegex(PredictorError, "invalid predictor response"):
                predictor.predict("word")
            with self.assertRaisesRegex(PredictorError, "closed"):
                predictor.predict("word")
        finally:
            predictor.close()
