"""
`python -m argsense create-launcher <target> ...`

Turns "this script, started with these arguments" into something that can be
double-clicked: a `.exe` (the stub with a payload telling it what to run) or
a `.lnk` (a shortcut to the interpreter, for people who would rather not
build a binary).
"""

import argparse
import os
import sys
import typing as tp
from pathlib import Path

from .config import Built
from .config import LaunchConfig
from .exe import make_exe
from .icon import to_ico
from .lnk import make_lnk
from .probes import assets_hint
from .probes import ensure_gui_pythonw
from .probes import missing_assets

DEFAULT_ARGS = (':gui',)


def main(argv: tp.Optional[tp.Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)

    target = Path(args.target).resolve()
    if not target.is_file():
        raise SystemExit('target not found: {}'.format(target))

    name = args.name or target.stem
    out_dir = Path(args.out) if args.out else desktop_dir()
    _require_assets(args.kind, with_icon=bool(args.window_icon))
    icon = _prepare_icon(args.window_icon, name)
    log = _app_dir() / 'logs' / '{}.log'.format(name)

    config = LaunchConfig(
        python=str(_interpreter(args.show_console)),
        script=str(target),
        cwd=args.cwd or os.getcwd(),
        args=tuple(args.preset_args) or DEFAULT_ARGS,
        name=name,
        log=str(log),
        icon=str(icon) if icon else '',
        port=args.port,
        window_size=args.window_size,
        window_title=args.window_title,
        show_console=args.show_console,
    )

    if args.kind == 'exe':
        built = make_exe(
            config, out_dir / '{}.exe'.format(name), icon=config.icon
        )
    else:
        built = _make_lnk(config, out_dir / '{}.lnk'.format(name))

    print(built.path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='argsense create-launcher',
        description='Wrap a script and its arguments into a desktop launcher.',
    )
    parser.add_argument('target', help='the ".py" file the launcher starts.')
    parser.add_argument(
        'preset_args',
        nargs='*',
        help='arguments baked into the launcher (default: ":gui").',
    )

    console = parser.add_mutually_exclusive_group()
    console.add_argument(
        '--show-console',
        dest='show_console',
        action='store_true',
        help='keep the console window visible (for debugging).',
    )
    console.add_argument(
        '--not-show-console',
        dest='show_console',
        action='store_false',
        help='start without a console window (the default).',
    )
    parser.set_defaults(show_console=False)

    parser.add_argument(
        '--window-title', default='', help='the title bar text.'
    )
    parser.add_argument(
        '--window-size', default='', help='the window size, e.g. "980x820".'
    )
    parser.add_argument(
        '--window-icon', default='', help='a ".png" or ".ico" for the window.'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=0,
        help='the port to serve on; 0 (the default) picks a free one.',
    )
    parser.add_argument(
        '--kind',
        choices=('exe', 'lnk'),
        default='exe',
        help='an executable (default) or a shortcut.',
    )
    parser.add_argument('--name', default='', help='the file name to write.')
    parser.add_argument(
        '--out', default='', help='where to write it (default: the desktop).'
    )
    parser.add_argument(
        '--cwd', default='', help='the directory to run in (default: here).'
    )
    return parser


def _require_assets(kind: str, *, with_icon: bool) -> None:
    """
    Fail early, and with instructions, when a binary is not there.

    They are not part of the wheel (see `probes`), so a plain `pip install`
    starts out without them -- checking before the icon is converted keeps
    the message the first thing the caller sees.
    """
    if kind != 'exe':
        return
    needed = ['stub.exe'] + (['rcedit.exe'] if with_icon else [])
    missing = missing_assets(*needed)
    if missing:
        raise SystemExit(assets_hint(missing))


def _interpreter(show_console: bool) -> Path:
    """
    The interpreter to start.

    A console-less launch needs a gui-subsystem `pythonw.exe`; a venv made by
    uv may have a plain copy of `python.exe` instead, which `ensure_gui_pythonw`
    replaces (see its docstring for why the copy still resolves the venv).
    """
    if show_console:
        return Path(sys.executable)

    path, replaced = ensure_gui_pythonw(sys.prefix)
    if replaced:
        print(
            "replaced {} with the base install's windowed interpreter".format(
                path
            ),
            file=sys.stderr,
        )
    return path


def _prepare_icon(file: str, name: str) -> tp.Optional[Path]:
    if not file:
        return None
    source = Path(file)
    if not source.is_file():
        raise SystemExit('icon not found: {}'.format(source))
    if source.suffix.lower() == '.ico':
        return source.resolve()
    return to_ico(source, _app_dir() / 'icons' / '{}.ico'.format(name))


def _make_lnk(config: LaunchConfig, file_o: Path) -> Built:
    return Built(
        make_lnk(
            file_o,
            target=config.python,
            arguments=_arguments(config),
            workdir=config.cwd,
            icon=config.icon,
            description=config.name,
        ),
        config,
    )


def _arguments(config: LaunchConfig) -> str:
    """
    The command line a shortcut carries.

    A shortcut can point at a program and pass arguments, but it has no way to
    set environment variables -- so everything the `.exe` form puts in its
    payload becomes an `--argsense-*` option here.
    """
    parts = [_quote(config.script)]
    parts.extend(_quote(x) for x in config.args)
    parts += ['--argsense-port', str(config.port)]
    if config.window_size:
        parts += ['--argsense-window-size', _quote(config.window_size)]
    if config.window_title:
        parts += ['--argsense-window-title', _quote(config.window_title)]
    if config.icon:
        parts += ['--argsense-window-icon', _quote(config.icon)]
    if config.log:
        parts += ['--argsense-log', _quote(config.log)]
    return ' '.join(parts)


def _quote(text: str) -> str:
    return '"{}"'.format(text) if ' ' in text else text


def _app_dir() -> Path:
    root = os.environ.get('LOCALAPPDATA') or str(Path.home())
    return Path(root) / 'argsense'


def desktop_dir() -> Path:
    """The desktop, following a redirect to onedrive when there is one."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer'
            r'\User Shell Folders',
        )
        value, _ = winreg.QueryValueEx(key, 'Desktop')
        return Path(os.path.expandvars(value))
    except Exception:
        return Path.home() / 'Desktop'


if __name__ == '__main__':
    raise SystemExit(main())
