"""
Make the `.exe` form: the stub, a payload, and a face.

The stub is copied rather than linked to, because the file is meant to be
moved to a desktop and double-clicked there.
"""

import shutil
import subprocess
import typing as tp
from pathlib import Path

from .config import Built
from .config import LaunchConfig
from .config import append_payload

ASSETS = Path(__file__).parent / 'assets'
STUB = ASSETS / 'stub.exe'
RCEDIT = ASSETS / 'rcedit.exe'


def make_exe(
    config: LaunchConfig, file_o: tp.Union[str, Path], *, icon: str = ''
) -> Built:
    """Copy the stub to `file_o`, append `config`, then paint the icon on."""
    target = Path(file_o)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not STUB.exists():
        raise FileNotFoundError(
            'the launcher stub is missing, run '
            '`python -m argsense.launcher.src.build`: {}'.format(STUB)
        )

    shutil.copy2(STUB, target)

    # the icon goes on before the payload: rcedit rebuilds the resource
    # section, and in doing so throws away anything appended after the last
    # section -- which is exactly where the payload lives.
    if icon:
        if not RCEDIT.exists():
            raise FileNotFoundError('rcedit is missing: {}'.format(RCEDIT))
        _rcedit(target, '--set-icon', icon)

    append_payload(target, config)

    return Built(target, config)


def _rcedit(file_exe: Path, *args: str) -> None:
    result = subprocess.run(
        (str(RCEDIT), str(file_exe), *args), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            'rcedit failed ({}): {} {}'.format(
                result.returncode, result.stdout.strip(), result.stderr.strip()
            )
        )
