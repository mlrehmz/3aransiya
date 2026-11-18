import unittest

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk
except (ImportError, ValueError):
    Gtk = None

if Gtk is not None:
    from scratchpad.word_range import Replacement, WordRange


@unittest.skipIf(Gtk is None, 'GTK 4 bindings are required')
class WordRangeTests(unittest.TestCase):
    def setUp(self):
        self.buffer = Gtk.TextBuffer()
        self.buffer.set_enable_undo(True)
        self.buffer.set_text('salam')
        self.word = WordRange(self.buffer, *self.buffer.get_bounds())
        self.addCleanup(self.word.close)

    def text(self):
        return self.buffer.get_text(*self.buffer.get_bounds(), True)

    def test_preserves_neighbors_and_undoes_as_one_action(self):
        self.buffer.insert(self.buffer.get_end_iter(), '، 123!')
        self.buffer.insert(self.buffer.get_start_iter(), 'قبل ')
        self.assertIs(self.word.replace('سلام'), Replacement.APPLIED)
        self.assertEqual(self.text(), 'قبل سلام، 123!')
        self.assertIs(self.word.replace('قديم'), Replacement.STALE)
        self.buffer.undo()
        self.assertEqual(self.text(), 'قبل salam، 123!')
        self.buffer.redo()
        self.assertEqual(self.text(), 'قبل سلام، 123!')

    def test_same_text_retyping_invalidates_range(self):
        at = self.buffer.get_iter_at_offset
        self.buffer.delete(at(1), at(2))
        self.buffer.insert(at(1), 'a')
        self.assertIs(self.word.replace('سلام'), Replacement.STALE)
        self.assertEqual(self.text(), 'salam')

    def test_selection_can_move_before_retry(self):
        at = self.buffer.get_iter_at_offset
        self.buffer.select_range(at(4), at(1))
        self.assertIs(self.word.replace('سلام'), Replacement.DEFERRED)
        self.assertEqual([it.get_offset() for it in self.buffer.get_selection_bounds()], [1, 4])
        self.buffer.place_cursor(at(5))
        self.assertIs(self.word.replace('سلام'), Replacement.APPLIED)

    def test_closed_range_cannot_apply(self):
        self.word.close()
        self.word.close()
        self.assertIs(self.word.replace('سلام'), Replacement.STALE)
        self.assertEqual(self.text(), 'salam')
