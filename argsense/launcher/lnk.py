"""
Write a windows shortcut, without pywin32.

`WScript.Shell` is the one shortcut writer every windows install already has,
so it is driven through powershell rather than through a COM binding of our
own: no dependency, and a single place to quote paths correctly.
"""

import subprocess
import typing as tp
from pathlib import Path


def make_lnk(
    file_o: tp.Union[str, Path],
    *,
    target: tp.Union[str, Path],
    arguments: str = '',
    workdir: tp.Union[str, Path] = '',
    icon: tp.Union[str, Path] = '',
    description: str = '',
) -> Path:
    """Create (or overwrite) `file_o` pointing at `target`."""
    path = Path(file_o)
    path.parent.mkdir(parents=True, exist_ok=True)

    parts = [
        '$s=(New-Object -ComObject WScript.Shell).CreateShortcut({});'.format(
            _quote(str(path))
        ),
        '$s.TargetPath={};'.format(_quote(str(target))),
        '$s.Arguments={};'.format(_quote(arguments)),
        '$s.WorkingDirectory={};'.format(_quote(str(workdir))),
        '$s.Description={};'.format(_quote(description)),
    ]
    # leaving `IconLocation` out keeps the target's own icon; setting it to
    # an empty string stores a literal ",0", which means the same thing but
    # reads like a mistake in the shortcut's properties.
    if icon:
        parts.append(
            '$s.IconLocation={};'.format(_quote('{},0'.format(Path(icon))))
        )
    parts.append('$s.Save()')

    subprocess.run(
        (
            'powershell',
            '-NoProfile',
            '-NonInteractive',
            '-Command',
            ''.join(parts),
        ),
        check=True,
        capture_output=True,
    )
    return path


def _quote(text: str) -> str:
    """A powershell single-quoted literal (the only escaping it needs)."""
    return "'{}'".format(text.replace("'", "''"))
