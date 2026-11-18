"""Guard a pending word replacement in a GTK 4 text buffer."""

from enum import Enum, auto

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class Replacement(Enum):
    APPLIED = auto()
    DEFERRED = auto()
    STALE = auto()


class WordRange:
    """Track one word on the GTK thread until replacement or close.

    Pass live iterators for a nonempty word in the given buffer. The caller
    must close abandoned ranges and may retry after a deferred replacement.
    """

    def __init__(
        self, buffer: Gtk.TextBuffer, start: Gtk.TextIter, end: Gtk.TextIter
    ) -> None:
        if start.compare(end) >= 0:
            raise ValueError('Expected a nonempty word range')
        self._buffer = buffer
        self._source = buffer.get_text(start, end, True)
        self._start = buffer.create_mark(None, start, False)
        self._end = buffer.create_mark(None, end, True)
        self._closed = False
        self._handlers = (
            buffer.connect('insert-text', self._before_insert),
            buffer.connect('delete-range', self._before_delete),
        )

    def replace(self, text: str) -> Replacement:
        if self._closed:
            return Replacement.STALE
        start, end = self._bounds()
        if start.compare(end) >= 0 or self._buffer.get_text(start, end, True) != self._source:
            self.close()
            return Replacement.STALE
        selection = self._buffer.get_selection_bounds()
        if selection and self._overlaps(start, end, *selection):
            return Replacement.DEFERRED

        offset = start.get_offset()
        self.close()
        self._buffer.begin_user_action()
        try:
            self._buffer.delete(start, end)
            self._buffer.insert(self._buffer.get_iter_at_offset(offset), text)
        finally:
            self._buffer.end_user_action()
        return Replacement.APPLIED

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for handler in self._handlers:
            self._buffer.disconnect(handler)
        self._buffer.delete_mark(self._start)
        self._buffer.delete_mark(self._end)

    def _bounds(self) -> tuple[Gtk.TextIter, Gtk.TextIter]:
        return (
            self._buffer.get_iter_at_mark(self._start),
            self._buffer.get_iter_at_mark(self._end),
        )

    @staticmethod
    def _overlaps(start, end, first, last) -> bool:
        return start.compare(last) < 0 and first.compare(end) < 0

    def _before_insert(self, buffer, position, text, length) -> None:
        start, end = self._bounds()
        if start.compare(position) < 0 and position.compare(end) < 0:
            self.close()

    def _before_delete(self, buffer, first, last) -> None:
        if self._overlaps(*self._bounds(), first, last):
            self.close()
