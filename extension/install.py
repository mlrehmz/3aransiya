"""Install the GNOME extension for the current user."""

import argparse
from pathlib import Path
import os
import shlex
import shutil
import sys


def main():
    source = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, help='local v1 model bundle directory')
    bundle = parser.parse_args().bundle
    if bundle is not None:
        bundle = bundle.resolve()
        if not all((bundle / name).is_file() for name in ('manifest.json', 'weights.pt')):
            parser.error('--bundle must contain manifest.json and weights.pt')

    sys.path.insert(0, str(source.parent))
    from scratchpad.predictor import application_id

    command = [sys.executable, '-m', 'scratchpad']
    if bundle is not None:
        command.extend(('--bundle', str(bundle)))
    data_home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    target = data_home / 'gnome-shell/extensions/scratchpad@3aransiya'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('metadata.json', 'extension.js', '3aransiya-symbolic.svg'):
        shutil.copyfile(source / name, target / name)
    (target / 'application-id').write_text(application_id(bundle) + '\n', encoding='ascii')
    launcher = target / 'launch-scratchpad'
    launcher.write_text(
        '#!/bin/sh\n'
        f'cd {shlex.quote(str(source.parent))} || exit 1\n'
        f'exec {shlex.join(command)}\n',
        encoding='utf-8',
    )
    launcher.chmod(0o755)
    print(f'Installed to {target}')


if __name__ == '__main__':
    main()
