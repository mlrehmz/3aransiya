"""Launch the GTK scratchpad with the development predictor."""

from collections import deque
import re
from time import sleep

from .word_range import Replacement, WordRange
from gi.repository import Gio, GLib, Gtk

from .composition import PredictionRequest
from .predictor import MockPredictor
from .worker import PredictionWorker

WORD = re.compile(r'[A-Za-z0-9]+\Z')
MAX_WORD = 128
MAX_WAITING = 16


class ScratchpadWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title='3aransiya', default_width=540,
                         default_height=280, hide_on_close=True)
        self.editor = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.editor.set_direction(Gtk.TextDirection.RTL)
        self.buffer = self.editor.get_buffer()
        self.buffer.set_enable_undo(True)
        self.preview = Gtk.Label(label='Mock predictor')
        self.status = Gtk.Label()
        scroller = Gtk.ScrolledWindow(vexpand=True)
        scroller.set_child(self.editor)
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for widget in (scroller, self.preview, self.status):
            layout.append(widget)
        self.set_child(layout)

        self._revision = 0
        self._preview_request = None
        self._pending = None
        self._waiting = deque()
        self._deferred = None
        self._applying = False
        self._closed = False
        self._refresh_source = 0
        mock = MockPredictor()

        def predict(word):
            sleep(0.08)
            return mock.predict(word)

        self.worker = PredictionWorker(predict, self._schedule_drain)
        self.buffer.connect_after('insert-text', self._inserted)
        self.buffer.connect('changed', self._schedule_refresh)
        self.buffer.connect('mark-set', self._schedule_refresh)
        for action in ('undo', 'redo'):
            self.buffer.connect(action, self._history_start)
            self.buffer.connect_after(action, self._history_end)

    def _history_start(self, *_):
        self._applying = True

    def _history_end(self, *_):
        self._applying = False
        self._schedule_refresh()

    def _schedule_drain(self):
        GLib.idle_add(self._drain)

    def _schedule_refresh(self, *_):
        if not self._applying and not self._closed and not self._refresh_source:
            self._refresh_source = GLib.idle_add(self._refresh)

    def _request(self, word, separator=None):
        self._revision += 1
        return PredictionRequest(self._revision, word, separator)

    def _word_before(self, end):
        start = end.copy()
        start.backward_chars(MAX_WORD + 1)
        match = WORD.search(self.buffer.get_text(start, end, True))
        if match is None or len(match[0]) > MAX_WORD:
            return None
        start = end.copy()
        start.backward_chars(len(match[0]))
        return start, match[0]

    def _inserted(self, buffer, position, text, _length):
        if self._applying or self._closed or len(text) != 1:
            return
        if WORD.fullmatch(text):
            return
        end = position.copy()
        if not end.backward_char():
            return
        candidate = self._word_before(end)
        if candidate is None:
            return
        start, word = candidate
        if word.isdecimal():
            return
        if len(self._waiting) >= MAX_WAITING:
            self.status.set_text('Prediction busy. This word was kept as typed.')
            return
        request = self._request(word, text)
        self._waiting.append((request, WordRange(buffer, start, end)))
        self._preview_request = None
        self._start_next()

    def _start_next(self):
        if self._pending or self._deferred or not self._waiting:
            return
        self._pending = self._waiting.popleft()
        request, marked = self._pending
        if not self.worker.submit(request):
            marked.close()
            self._pending = None
            self.status.set_text('Prediction unavailable. The word was kept as typed.')

    def _refresh(self):
        self._refresh_source = 0
        if self._closed:
            return False
        if self._deferred is not None:
            marked, output = self._deferred
            if self._replace(marked, output) is not Replacement.DEFERRED:
                self._deferred = None
                self._start_next()
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        candidate = self._word_before(cursor)
        if self.buffer.get_has_selection() or candidate is None or candidate[1].isdecimal():
            self._preview_request = None
            self.preview.set_text('Mock predictor')
        elif self._preview_request is None or candidate[1] != self._preview_request.word:
            self.preview.set_text('Mock predictor')
            request = self._request(candidate[1])
            if self.worker.submit(request):
                self._preview_request = request
        return False

    def _replace(self, marked, output):
        self._applying = True
        try:
            return marked.replace(output)
        finally:
            self._applying = False

    def _drain(self):
        if self._closed:
            return False
        result = self.worker.take_result()
        if result is None:
            return False
        if self._pending is not None and result.request is self._pending[0]:
            _, marked = self._pending
            self._pending = None
            if result.failed:
                marked.close()
                self.status.set_text('Prediction failed. Your text was kept.')
            elif self._replace(marked, result.output) is Replacement.DEFERRED:
                self._deferred = marked, result.output
            self._start_next()
            self._schedule_refresh()
        elif result.request is self._preview_request and not result.failed:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            candidate = self._word_before(cursor)
            if candidate and candidate[1] == result.request.word and not self.buffer.get_has_selection():
                self.preview.set_text(f'Mock preview   {result.output}')
        return False

    def shutdown(self):
        self._closed = True
        self.worker.close()
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
            self._refresh_source = 0
        if self._pending:
            self._pending[1].close()
        if self._deferred:
            self._deferred[0].close()
        for _, marked in self._waiting:
            marked.close()
        self._waiting.clear()


class ScratchpadApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.aransiya.Scratchpad')
        self.window = None

    def do_activate(self):
        if self.window is None:
            self.window = ScratchpadWindow(self)
            self.add_action(self._quit_action())
            self.set_accels_for_action('app.quit', ['<Primary>q'])
        self.window.present()
        self.window.editor.grab_focus()

    def _quit_action(self):
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', lambda *_: self.quit())
        return action

    def do_shutdown(self):
        if self.window is not None:
            self.window.shutdown()
        Gtk.Application.do_shutdown(self)


if __name__ == '__main__':
    raise SystemExit(ScratchpadApplication().run())
