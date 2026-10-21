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
from .probes import require_assets

ASSETS = Path(__file__).parent / 'assets'
STUB = ASSETS / 'stub.exe'
RCEDIT = ASSETS / 'rcedit.exe'


def make_exe(
    config: LaunchConfig, file_o: tp.Union[str, Path], *, icon: str = ''
) -> Built:
    """Copy the stub to `file_o`, append `config`, then paint the icon on."""
    target = Path(file_o)
    target.parent.mkdir(parents=True, exist_ok=True)
    require_assets('stub.exe')

    shutil.copy2(STUB, target)

    # the icon goes on before the payload: rcedit rebuilds the resource
    # section, and in doing so throws away anything appended after the last
    # section -- which is exactly where the payload lives.
    if icon:
        require_assets('rcedit.exe')
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
