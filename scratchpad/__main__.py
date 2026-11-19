"""Launch the GTK scratchpad with an optional offline model bundle."""

from collections import deque
import argparse
import os
from pathlib import Path
import re

from .word_range import WordRange
from gi.repository import Gdk, Gio, GLib, Gtk, Pango

from .composition import PredictionRequest
from .phrases import LATIN_TOKEN, render_text
from .release_model import profile_inputs
from .predictor import HelperPredictor, MockPredictor, application_id
from .worker import PredictionWorker

WORD = re.compile(r'[A-Za-z0-9]+\Z')
MAX_WORD = 128
MAX_WAITING = 64
COPY_ICON = 'copy.svg'
HIDE_ICON = 'hide.svg'


class ScratchpadWindow(Gtk.ApplicationWindow):
    def __init__(self, application, *, helper_command=None, phrases=False):
        super().__init__(
            application=application, title='3aransiya', default_width=820,
            default_height=101, hide_on_close=True, decorated=False,
        )
        self._phrases = phrases
        self.add_css_class('scratchpad-window')
        self.editor = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.editor.set_direction(Gtk.TextDirection.LTR)
        self.editor.set_justification(Gtk.Justification.LEFT)
        self.editor.set_left_margin(10)
        self.editor.set_right_margin(10)
        self.editor.set_top_margin(1)
        self.editor.set_bottom_margin(1)
        self.buffer = self.editor.get_buffer()
        self.buffer.set_enable_undo(True)
        self.editor.set_tooltip_text('Arabizi input · Ctrl+S starts over')
        self.editor.update_property([Gtk.AccessibleProperty.LABEL], ['Arabizi input'])
        # GTK mirrors leading alignment in an RTL text view.
        self.preview = Gtk.TextView(
            editable=False, cursor_visible=False, focusable=False,
            wrap_mode=Gtk.WrapMode.WORD_CHAR, justification=Gtk.Justification.LEFT,
            right_margin=10, left_margin=10, top_margin=1, bottom_margin=1,
        )
        self.output_buffer = self.preview.get_buffer()
        self._shown_output = None
        self.preview.set_direction(Gtk.TextDirection.RTL)
        self.preview.add_css_class('scratchpad-preview')
        self.preview.set_tooltip_text('Arabic output')
        self._preview_output = None
        self.status = Gtk.Label(wrap=True, visible=False)
        self.status.add_css_class('scratchpad-status')
        self.status.connect('notify::label', lambda label, _: label.set_visible(bool(label.get_text())))
        scroller = Gtk.ScrolledWindow(hexpand=True, vexpand=True, min_content_height=29)
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)
        scroller.set_child(self.editor)
        output = Gtk.ScrolledWindow(hexpand=True, vexpand=True, min_content_height=35)
        output.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.EXTERNAL)
        output.set_child(self.preview)
        handle = Gtk.WindowHandle(hexpand=True, vexpand=True)
        handle.set_child(output)
        self.copy_button = self._icon(COPY_ICON, 'Copy selection or draft', self._copy)
        self.hide_button = self._icon(HIDE_ICON, 'Hide scratchpad', lambda _: self.minimize())
        self.copy_button.add_css_class('scratchpad-copy')
        self.hide_button.add_css_class('scratchpad-hide')
        row = Gtk.Box(spacing=6)
        row.set_direction(Gtk.TextDirection.LTR)
        controls = Gtk.Box(spacing=0)
        controls.append(self.copy_button)
        controls.append(self.hide_button)
        row.append(controls)
        row.append(handle)
        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        layout.add_css_class('scratchpad-bar')
        layout.append(row)
        layout.append(Gtk.Separator())
        layout.append(scroller)
        layout.append(self.status)
        self.set_child(layout)

        self._revision = 0
        self._preview_request = None
        self._pending = None
        self._waiting = deque()
        self._translations = {}
        self._applying = False
        self._closed = False
        self._refresh_source = 0
        self._copy_feedback = 0
        self._render_rows()
        if helper_command is not None:
            predictor = HelperPredictor(helper_command)
            self.worker = PredictionWorker(
                predictor.predict, self._schedule_drain, on_close=predictor.close
            )
        else:
            self.worker = PredictionWorker(MockPredictor().predict, self._schedule_drain)
        self.buffer.connect_after('insert-text', self._inserted)
        self.buffer.connect('changed', self._schedule_refresh)
        self.buffer.connect('mark-set', self._schedule_refresh)
        for action in ('undo', 'redo'):
            self.buffer.connect(action, self._history_start)
            self.buffer.connect_after(action, self._history_end)

    @staticmethod
    def _icon(name, label, callback):
        button = Gtk.Button(tooltip_text=label, valign=Gtk.Align.CENTER)
        button.set_child(ScratchpadWindow._glyph(name))
        button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        button.connect('clicked', callback)
        return button

    @staticmethod
    def _glyph(name):
        image = Gtk.Image.new_from_file(str(Path(__file__).with_name('icons') / name))
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        return image

    def _copy(self, _button):
        bounds = self.buffer.get_selection_bounds() or self.buffer.get_bounds()
        text = self._arabic_text(*bounds, keep_unresolved=True)
        if not text:
            return
        self.editor.get_clipboard().set(text)
        if self._copy_feedback:
            GLib.source_remove(self._copy_feedback)
        self.copy_button.set_label('✓')
        self.copy_button.add_css_class('copied')
        self._copy_feedback = GLib.timeout_add(1100, self._reset_copy_feedback)

    def _reset_copy_feedback(self):
        self._copy_feedback = 0
        self.copy_button.set_child(self._glyph(COPY_ICON))
        self.copy_button.remove_css_class('copied')
        return GLib.SOURCE_REMOVE

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
        if self._applying or self._closed or not text:
            return
        if len(text) == 1 and WORD.fullmatch(text):
            return
        before = position.copy()
        before.backward_chars(len(text))
        candidate = self._word_before(before)
        start_offset = candidate[0].get_offset() if candidate else before.get_offset()
        inserted = buffer.get_text(buffer.get_iter_at_offset(start_offset), position, True)
        for match in LATIN_TOKEN.finditer(inserted):
            if match.end() == len(inserted):
                break
            word = match[0]
            if word.isdecimal() or len(word) > MAX_WORD or word in self._translations:
                continue
            if len(self._waiting) >= MAX_WAITING:
                self.status.set_text('Prediction busy. Some words were kept as typed.')
                break
            request = self._request(word, inserted[match.end()])
            start = buffer.get_iter_at_offset(start_offset + match.start())
            end = buffer.get_iter_at_offset(start_offset + match.end())
            self._waiting.append((request, WordRange(buffer, start, end)))
        if self._waiting:
            self._preview_request = None
            self._preview_output = None
            self._start_next()

    def _start_next(self):
        if self._pending or not self._waiting:
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
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        candidate = self._word_before(cursor)
        if self.buffer.get_has_selection() or candidate is None or candidate[1].isdecimal():
            self._preview_request = None
            self._preview_output = None
        elif self._preview_request is None or candidate[1] != self._preview_request.word:
            self._preview_output = None
            request = self._request(candidate[1])
            if self.worker.submit(request):
                self._preview_request = request
        self._render_rows()
        return False

    def _arabic_text(self, start, end, *, keep_unresolved=False):
        draft = self.buffer.get_text(start, end, True)
        offset = start.get_offset()
        cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert()).get_offset()

        def render_token(match):
            token = match[0]
            if token.isdecimal():
                return token
            if token in self._translations:
                return self._translations[token]
            if (self._preview_output and self._preview_request
                    and offset + match.end() == cursor and token == self._preview_request.word):
                return self._preview_output
            return token if keep_unresolved else ''

        return render_text(draft, render_token, phrases=self._phrases)

    def _render_rows(self):
        output = self._arabic_text(*self.buffer.get_bounds())
        if output:
            self.preview.remove_css_class('empty')
        else:
            self.preview.add_css_class('empty')
        if output != self._shown_output:
            self._shown_output = output
            self.output_buffer.set_text(output or 'العربية')
        # Follow the corresponding line even when it is still empty.
        source_cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        line = source_cursor.get_line()
        found, target = self.output_buffer.get_iter_at_line(line)
        if found:
            self.output_buffer.place_cursor(target)
            self.preview.scroll_mark_onscreen(self.output_buffer.get_insert())

    def start_over(self):
        self._discard_requests()
        self.status.set_text('')
        self.buffer.begin_user_action()
        try:
            self.buffer.delete(*self.buffer.get_bounds())
        finally:
            self.buffer.end_user_action()
        self._render_rows()
        self.editor.grab_focus()

    def _discard_requests(self):
        self._preview_request = None
        self._preview_output = None
        if self._pending:
            self._pending[1].close()
        for _, marked in self._waiting:
            marked.close()
        self._waiting.clear()

    def _drain(self):
        if self._closed:
            return False
        result = self.worker.take_result()
        if result is None:
            return False
        if self._pending is not None and result.request is self._pending[0]:
            _, marked = self._pending
            self._pending = None
            if marked.is_current():
                if result.failed:
                    self.status.set_text('Prediction failed. Your text was kept.')
                else:
                    self._translations[result.request.word] = result.output
            marked.close()
            self._start_next()
            self._schedule_refresh()
        elif result.request is self._preview_request and not result.failed:
            cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert())
            candidate = self._word_before(cursor)
            if candidate and candidate[1] == result.request.word and not self.buffer.get_has_selection():
                self._preview_output = result.output
                self._render_rows()
        return False

    def shutdown(self):
        self._closed = True
        self.worker.close()
        if self._copy_feedback:
            GLib.source_remove(self._copy_feedback)
            self._copy_feedback = 0
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
            self._refresh_source = 0
        self._discard_requests()


class ScratchpadApplication(Gtk.Application):
    def __init__(self, *, synthetic_helper=False, bundle=None, profile=None):
        app_id = application_id(profile or bundle)
        self._phrases = profile is not None
        python = Path(__file__).resolve().parents[1] / '.venv/bin/python'
        self._helper_command = None
        if profile is not None:
            self._helper_command = [python, '-m', 'scratchpad.release_model', 'serve', profile.resolve()]
        elif bundle is not None:
            bundle = Path(bundle).resolve()
            self._helper_command = [python, '-m', 'model_pilot.inference_helper', bundle]
        elif synthetic_helper:
            app_id += '.Synthetic'
            self._helper_command = [python, '-m', 'scratchpad.synthetic_helper']
        super().__init__(
            application_id=app_id,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.window = None

    def do_command_line(self, command_line):
        if Gdk.Display.get_default() is None:
            command_line.printerr_literal(
                '3aransiya could not open a display. Launch it from your desktop session.\n'
            )
            return 1
        self.activate()
        if command_line.get_is_remote():
            command_line.print_literal('Opened the running 3aransiya window.\n')
        return 0

    def do_activate(self):
        if self.window is None:
            provider = Gtk.CssProvider()
            provider.load_from_path(str(Path(__file__).with_name('scratchpad.css')))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            self.window = ScratchpadWindow(self, helper_command=self._helper_command, phrases=self._phrases)
            self.add_action(self._quit_action())
            start_over = Gio.SimpleAction.new('start-over', None)
            start_over.connect('activate', lambda *_: self.window.start_over())
            self.add_action(start_over)
            self.set_accels_for_action('app.start-over', ['<Primary>s'])
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
    parser = argparse.ArgumentParser(description=__doc__)
    models = parser.add_mutually_exclusive_group()
    models.add_argument('--bundle', type=Path, help='local v1 inference bundle directory')
    models.add_argument('--profile', type=Path, help='local release model directory')
    options = parser.parse_args()
    if options.profile and not all(path.is_file() for path in profile_inputs(options.profile)):
        parser.error('--profile must point to a complete release model directory')
    synthetic_helper = os.environ.get('ARANSIYA_SYNTHETIC_HELPER') == '1'
    application = ScratchpadApplication(synthetic_helper=synthetic_helper, bundle=options.bundle, profile=options.profile)
    status = application.run([])
    if (synthetic_helper or options.bundle is not None or options.profile is not None) and application.window is not None:
        # Wait after the GTK loop so helper cleanup cannot block the editor.
        application.window.worker.join(17)
    raise SystemExit(status)
