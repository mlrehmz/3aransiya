import unittest
from queue import Queue
from threading import Event

from scratchpad.composition import PredictionRequest
from scratchpad.worker import PredictionWorker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.started = Queue()
        self.ready = Queue()
        self.release = Event()

        def predict(word):
            self.started.put(word)
            if word == 'blocked' and not self.release.wait(3):
                raise TimeoutError
            if word == 'fail':
                raise ValueError('private text')
            return word.upper()

        self.worker = PredictionWorker(predict, lambda: self.ready.put(None))
        self.addCleanup(self.cleanup_worker)

    def cleanup_worker(self):
        self.worker.close()
        self.release.set()
        self.assertTrue(self.worker.join(3))

    def result(self, request):
        self.ready.get(timeout=3)
        result = self.worker.take_result()
        self.assertIs(result.request, request)
        return result

    def test_commit_runs_before_latest_waiting_preview(self):
        running = PredictionRequest(1, 'blocked')
        commit = PredictionRequest(3, 'complete', '!')
        latest = PredictionRequest(5, 'latest')
        self.assertTrue(self.worker.submit(running))
        self.assertEqual(self.started.get(timeout=3), 'blocked')
        self.assertTrue(self.worker.submit(PredictionRequest(2, 'obsolete')))
        self.assertTrue(self.worker.submit(commit))
        self.assertFalse(self.worker.submit(PredictionRequest(4, 'extra', ' ')))
        self.assertTrue(self.worker.submit(PredictionRequest(4, 'older')))
        self.assertTrue(self.worker.submit(latest))
        self.release.set()
        self.assertEqual(self.result(running).output, 'BLOCKED')
        self.assertEqual(self.result(commit).output, 'COMPLETE')
        self.assertEqual(self.result(latest).output, 'LATEST')
        self.assertEqual([self.started.get_nowait() for _ in range(2)], ['complete', 'latest'])
        self.assertTrue(self.started.empty())

    def test_failure_is_reported_and_worker_recovers(self):
        failed = PredictionRequest(1, 'fail')
        self.worker.submit(failed)
        self.assertTrue(self.result(failed).failed)
        next_request = PredictionRequest(2, 'next')
        self.worker.submit(next_request)
        self.assertEqual(self.result(next_request).output, 'NEXT')

    def test_close_discards_running_and_waiting_work(self):
        self.worker.submit(PredictionRequest(1, 'blocked'))
        self.assertEqual(self.started.get(timeout=3), 'blocked')
        self.worker.submit(PredictionRequest(2, 'waiting', ' '))
        self.worker.close()
        self.worker.close()
        self.assertFalse(self.worker.submit(PredictionRequest(3, 'late')))
        self.release.set()
        self.assertTrue(self.worker.join(3))
        self.assertIsNone(self.worker.take_result())
        self.assertTrue(self.ready.empty())
        self.assertTrue(self.started.empty())

    def test_close_clears_unread_result_and_wakes_worker(self):
        self.worker.submit(PredictionRequest(1, 'ready'))
        self.ready.get(timeout=3)
        self.worker.close()
        self.assertTrue(self.worker.join(3))
        self.assertIsNone(self.worker.take_result())
