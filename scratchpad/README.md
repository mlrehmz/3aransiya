# Scratchpad composition core

This package currently provides headless, single-word composition and an artificial
predictor. It is not yet a graphical application or a transliteration model.
It requires Python 3.10 or later and no third-party packages. The current verified
interpreter is Python 3.15.2 on Fedora 45.

Run the tests from the repository root:

```sh
python -m unittest discover -s tests
```

## Use

```python
from scratchpad.composition import Composition
from scratchpad.predictor import MockPredictor

composition = Composition()
preview_request = composition.edit('salam')
commit_request = composition.finish('! ')
predictor = MockPredictor()
result = composition.resolve(commit_request, predictor.predict(commit_request.word))
assert result.text == 'تجربة5! '
assert composition.resolve(preview_request, 'قديم') is None
```

`edit` accepts the entire current source word, including replacements caused by
backspace. It returns a prediction request, or `None` for an empty word or a
Unicode decimal-digit-only token. Embedded Arabizi digits remain model input.
The caller splits text into words and separators; this module does not tokenize
keystrokes or manage selection.

`finish` accepts the exact separator string. An empty string requests finalization
without inserting a separator. It returns a prediction request, or a direct
`Commit` for an empty word or digit-only token. A `Commit` contains the full text
for the document owner to insert. A successful prediction clears the active word
only when it finalizes that word; `Preview` leaves the source word intact.

Pass the same request object back to `resolve` or `reject`. Superseded, foreign,
and already-consumed requests have no effect. Nonempty prediction strings without
whitespace are accepted; language-specific model-output validation is not yet
implemented. Invalid results produce `Failure` and preserve the source word.
`reject` handles a predictor exception in the same way. Failure events retain the
separator so the caller can offer retry without losing punctuation. Exceptions
and typed words are not logged by these components.

A pending finalization must be resolved or rejected before another edit or
finalization; otherwise `RuntimeError` is raised without changing state. A future
UI controller must preserve and order subsequent input while waiting. This core
is synchronous and confined to one owner thread; it provides no worker, input
queue, GTK buffer, clipboard integration, or performance guarantees yet.

The mock returns `تجربة` followed by the source word's character count. This is
artificial test output, not a Darija prediction. `MockPredictor(fail=True)` raises
an error for failure-path checks. Tests deliver results in a chosen order to
simulate delayed predictions without timers. Replace `predict(word) -> str` with
the real model adapter when its runtime and bundle are available.

## Launch the mock editor

On Fedora with GTK 4 and PyGObject installed, run this from the repository root:

```sh
python -m scratchpad
```

Type a word using ASCII Latin letters and Arabizi digits. The mock preview
appears above the Arabizi editor in a right-to-left reading row. Type a separator to replace the source word with
artificial output after a short delay. Standalone digits stay as typed. The
close button hides the window and keeps its draft in memory. Run the launcher
again to reopen it, or use Ctrl+Q to quit.

This development window handles single-character insertions at separators.
Multi-character paste remains literal. It uses GTK's default clipboard
behavior. Automatic conversion before copying and the GNOME top-bar button
are future work.

The compact bar puts Copy and Hide on the left. Enter inserts a line break immediately. Copy takes the selection,
or the whole draft if nothing is selected. Hide keeps the draft in the running
application. A second launch prints a confirmation when it opens that window.
Drag the preview area to move the bar. Backdrop blur depends on the desktop
compositor.

## GNOME top-bar control

On GNOME Shell 51, install the extension from this checkout with the same
Python you use to run the app:

```sh
python extension/install.py
gnome-extensions enable scratchpad@3aransiya
```

If GNOME does not discover the extension immediately, log out and back in
before enabling it. The top-bar icon opens the scratchpad near the bottom of
the active monitor on first launch. If it is already running, the icon moves
it to the active workspace and focuses it. The inline Hide icon minimizes
the window and keeps the draft and window position.

Rerun the installer after moving the checkout or changing Python. After
updating the extension, log out and back in to reload its JavaScript.
To remove it, run `gnome-extensions uninstall scratchpad@3aransiya`.

The Arabizi row keeps the source text after you press Space. The upper row
shows the Arabic preview and committed output. The Copy icon copies the
Arabic output for the selected range, or for the whole draft when nothing is
selected. Use Ctrl+Shift+N to start over and Ctrl+Z to restore that draft.
