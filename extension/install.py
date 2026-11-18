"""Install the GNOME extension for the current user."""

from pathlib import Path
import os
import shlex
import shutil
import sys


def main():
    source = Path(__file__).resolve().parent
    data_home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    target = data_home / 'gnome-shell/extensions/scratchpad@3aransiya'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('metadata.json', 'extension.js'):
        shutil.copyfile(source / name, target / name)
    launcher = target / 'launch-scratchpad'
    launcher.write_text(
        '#!/bin/sh\n'
        f'cd {shlex.quote(str(source.parent))} || exit 1\n'
        f'exec {shlex.quote(sys.executable)} -m scratchpad\n',
        encoding='utf-8',
    )
    launcher.chmod(0o755)
    print(f'Installed to {target}')


if __name__ == '__main__':
    main()
