import unittest

from scratchpad.composition import Commit, Composition, Failure, Preview
from scratchpad.predictor import MockPredictor


class CompositionTests(unittest.TestCase):
    def test_immediate_separator_commits_complete_word(self):
        composition = Composition()
        composition.edit('sala')
        composition.edit('salam')
        request = composition.finish('! ')
        output = MockPredictor().predict(request.word)
        self.assertEqual(request.word, 'salam')
        self.assertEqual(composition.resolve(request, output), Commit('تجربة5! '))
        self.assertEqual(composition.word, '')

    def test_backspace_discards_old_preview_and_accepts_current_preview(self):
        composition = Composition()
        old = composition.edit('salam')
        current = composition.edit('sala')
        self.assertIsNone(composition.resolve(old, 'قديم'))
        self.assertEqual(composition.word, 'sala')
        self.assertEqual(composition.resolve(current, 'تجربة4'), Preview('تجربة4'))
        self.assertEqual(composition.word, 'sala')
        self.assertIsNone(composition.resolve(current, 'مكرر'))

    def test_preview_cannot_replace_a_pending_commit(self):
        composition = Composition()
        preview = composition.edit('salam')
        final = composition.finish(' ')
        self.assertIsNone(composition.resolve(preview, 'قديم'))
        self.assertEqual(composition.resolve(final, 'تجربة5'), Commit('تجربة5 '))

    def test_failed_commit_keeps_source_and_separator_for_retry(self):
        composition = Composition()
        composition.edit('salam')
        request = composition.finish('!')
        self.assertEqual(composition.reject(request), Failure('Prediction failed', '!'))
        self.assertEqual(composition.word, 'salam')
        retry = composition.finish('!')
        self.assertEqual(composition.resolve(retry, 'تجربة5'), Commit('تجربة5!'))
        self.assertIsNone(composition.reject(request))

    def test_numbers_commit_without_a_prediction(self):
        composition = Composition()
        self.assertIsNone(composition.edit('123'))
        self.assertEqual(composition.finish(', '), Commit('123, '))
        self.assertEqual(composition.word, '')

    def test_pending_commit_cannot_be_overwritten(self):
        composition = Composition()
        composition.edit('salam')
        request = composition.finish(' ')
        with self.assertRaises(RuntimeError):
            composition.edit('next')
        with self.assertRaises(RuntimeError):
            composition.finish('!')
        self.assertEqual(composition.resolve(request, 'تجربة5'), Commit('تجربة5 '))

    def test_mock_failure_can_be_reported_without_losing_input(self):
        composition = Composition()
        request = composition.edit('salam')
        with self.assertRaises(RuntimeError):
            MockPredictor(fail=True).predict(request.word)
        self.assertEqual(composition.reject(request), Failure('Prediction failed', None))
        self.assertEqual(composition.word, 'salam')

    def test_invalid_prediction_keeps_word_and_separator(self):
        for output in ('', 'two words', None, 123):
            with self.subTest(output=output):
                composition = Composition()
                composition.edit('salam')
                request = composition.finish(' ')
                self.assertEqual(composition.resolve(request, output),
                                 Failure('Invalid prediction', ' '))
                self.assertEqual(composition.word, 'salam')

    def test_clearing_word_invalidates_preview(self):
        composition = Composition()
        request = composition.edit('salam')
        self.assertIsNone(composition.edit(''))
        self.assertIsNone(composition.resolve(request, 'قديم'))
        self.assertEqual(composition.finish('\n'), Commit('\n'))

    def test_other_composition_cannot_supply_a_result(self):
        composition = Composition()
        request = composition.edit('salam')
        foreign = Composition().edit('salam')
        self.assertIsNone(composition.resolve(foreign, 'قديم'))
        self.assertEqual(composition.resolve(request, 'تجربة5'), Preview('تجربة5'))

    def test_arabizi_is_predicted_but_decimal_digits_pass_through(self):
        composition = Composition()
        request = composition.edit('3lach')
        self.assertEqual(request.word, '3lach')
        self.assertIsNone(composition.edit('١٢٣'))
        self.assertIsNone(composition.resolve(request, 'قديم'))
        self.assertEqual(composition.finish('!'), Commit('١٢٣!'))


if __name__ == '__main__':
    unittest.main()
