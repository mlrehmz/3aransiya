import unittest
from queue import Queue
from threading import Event

from scratchpad.composition import Commit, Failure
from scratchpad.controller import InputController


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.ready = Queue()
        self.events = []
        self.started = Event()
        self.release = Event()
        self.attempts = 0

        def predict(word):
            if word == 'salam':
                self.attempts += 1
                if self.attempts == 1:
                    self.started.set()
                    if not self.release.wait(3):
                        raise TimeoutError
                if self.fail and self.attempts <= 2:
                    raise ValueError
            return 'تجربة'

        self.fail = False
        self.controller = InputController(
            predict, lambda: self.ready.put(None), self.events.append,
            max_commands=2, max_characters=8,
        )
        self.addCleanup(self.cleanup_controller)

    def cleanup_controller(self):
        self.controller.close()
        self.release.set()
        self.assertTrue(self.controller.join(3))

    def drain(self):
        self.ready.get(timeout=3)
        self.controller.drain()

    def begin(self):
        self.assertTrue(self.controller.append('salam'))
        self.assertTrue(self.started.wait(3))
        self.assertTrue(self.controller.separator('! '))

    def test_later_typing_commits_after_complete_word(self):
        self.begin()
        self.assertTrue(self.controller.append('123'))
        self.assertTrue(self.controller.separator(','))
        self.assertFalse(self.controller.append('x'))
        self.release.set()
        self.drain()
        self.assertEqual(self.events, [])
        self.drain()
        self.assertEqual(self.events, [Commit('تجربة! '), Commit('123,')])

    def test_retry_preserves_failed_word_and_queued_input(self):
        self.fail = True
        self.begin()
        self.assertTrue(self.controller.append('123'))
        self.assertTrue(self.controller.separator(','))
        self.release.set()
        self.drain()
        self.drain()
        self.assertEqual(self.events, [Failure('Prediction failed', '! ')])
        self.assertTrue(self.controller.retry())
        self.assertFalse(self.controller.retry())
        self.drain()
        self.assertEqual(self.events, [
            Failure('Prediction failed', '! '), Commit('تجربة! '), Commit('123,'),
        ])

    def test_character_limit_rejects_whole_command(self):
        self.begin()
        self.assertFalse(self.controller.append('123456789'))
        self.assertTrue(self.controller.append('123'))
        self.assertTrue(self.controller.backspace())
        self.release.set()
        self.drain()
        self.drain()
        self.assertTrue(self.controller.separator('.'))
        self.assertEqual(self.events, [Commit('تجربة! '), Commit('12.')])

    def test_close_discards_queued_input(self):
        self.begin()
        self.assertTrue(self.controller.append('123'))
        self.controller.close()
        self.release.set()
        self.assertTrue(self.controller.join(3))
        self.controller.drain()
        self.assertFalse(self.controller.separator('.'))
        self.assertEqual(self.events, [])
