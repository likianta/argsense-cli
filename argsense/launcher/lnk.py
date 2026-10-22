"""
Write a windows shortcut, without pywin32.

`WScript.Shell` is the one shortcut writer every windows install already has,
so it is driven through powershell rather than through a COM binding of our
own: no dependency, and a single place to quote paths correctly.
"""

import subprocess
import typing as tp

from .config import LaunchConfig


def make_lnk(
    config: LaunchConfig,
    file_o: str,
    *,
    description: str = '',
    arguments: tp.Optional[str] = None,
) -> str:
    """
    Create (or overwrite) `file_o` pointing at `config.python`.

    `arguments` defaults to the command line built from `config`; pass `''`
    when the target is a launcher that already knows what to start.
    """

    parts = [
        '$s=(New-Object -ComObject WScript.Shell).CreateShortcut({});'.format(
            _quote_psarg(file_o)
        ),
        '$s.TargetPath={};'.format(_quote_psarg(config.python)),
        '$s.Arguments={};'.format(
            _quote_psarg(
                _stringify_arguments(config) if arguments is None else arguments
            )
        ),
        '$s.WorkingDirectory={};'.format(_quote_psarg(config.cwd)),
        '$s.Description={};'.format(_quote_psarg(description or config.name)),
    ]
    # leaving `IconLocation` out keeps the target's own icon; setting it to
    # an empty string stores a literal ",0", which means the same thing but
    # reads like a mistake in the shortcut's properties.
    if config.icon:
        parts.append(
            '$s.IconLocation={};'.format(
                _quote_psarg('{},0'.format(config.icon))
            )
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
    return file_o


def _stringify_arguments(config: LaunchConfig) -> str:
    """
    The command line a shortcut carries.

    A shortcut can point at a program and pass arguments, but it has no way
    to set environment variables -- so everything the `.exe` form keeps in
    its payload becomes an `--argsense-*` option here.
    """
    parts = []

    parts.append(_quote_arg(config.script))
    parts.extend(_quote_arg(x) for x in config.args)

    parts.append('--argsense-port')
    parts.append(str(config.port))

    if config.window_size:
        parts.append('--argsense-window-size')
        parts.append(
            _quote_arg(LaunchConfig.size_tuple_to_str(config.window_size))
        )

    if config.window_title:
        parts.append('--argsense-window-title')
        parts.append(_quote_arg(config.window_title))

    if config.icon:
        parts.append('--argsense-window-icon')
        parts.append(_quote_arg(config.icon))

    if config.log:
        parts.append('--argsense-log')
        parts.append(_quote_arg(config.log))

    return ' '.join(parts)


def _quote_arg(text: str) -> str:
    return '"{}"'.format(text) if ' ' in text else text


def _quote_psarg(text: str) -> str:
    """A powershell single-quoted literal (the only escaping it needs)."""
    return "'{}'".format(text.replace("'", "''"))
