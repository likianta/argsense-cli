"""
Build a launcher: the decisions, and the two forms they turn into.

`argsense/__main__.py` owns the command (and its user-facing docstring); this
module holds what that command delegates to.
"""

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

# what the launcher starts the script with: the gui is the point, otherwise
# the launcher would only be a slower way to type a command.
DEFAULT_ARGS = (':gui',)

KINDS = ('exe', 'lnk')
KINDS_SUFFIXES = ('.exe', '.lnk')


def create(
    script: tp.Union[str, Path],
    *,
    result: str = '',
    kind: str = 'auto',
    window_title: str = '',
    window_size: str = '',
    window_icon: str = '',
    port: int = 0,
    show_console: bool = False,
    add_to_desktop_shortcut: bool = True,
) -> tp.List[Path]:
    """
    Write the launcher (and, optionally, a shortcut to it on the desktop).

    Returns the files written, in the order they were created.
    """
    source = Path(script).resolve()
    if not source.is_file():
        raise FileNotFoundError('no such script: {}'.format(source))

    kind = _deduce_kind(kind, result, window_icon)
    target = _resolve_result(source, result, kind)
    _require_assets(kind, with_icon=bool(window_icon))

    icon = _prepare_icon(window_icon, target.stem)
    config = LaunchConfig(
        python=str(_interpreter(show_console)),
        script=str(source),
        cwd=os.getcwd(),
        args=DEFAULT_ARGS,
        name=target.stem,
        log=str(_app_dir() / 'logs' / '{}.log'.format(target.stem)),
        icon=str(icon) if icon else '',
        port=port,
        window_size=window_size,
        window_title=window_title,
        show_console=show_console,
    )

    built = (
        make_exe(config, target, icon=config.icon)
        if kind == 'exe'
        else _make_lnk(config, target)
    )

    written = [built.path]
    desktop = desktop_dir()
    if add_to_desktop_shortcut and built.path.parent != desktop:
        written.append(_shortcut_on_desktop(built, config, desktop))
    return written


def _deduce_kind(kind: str, result: str, window_icon: str) -> str:
    """
    Settle on 'exe' or 'lnk'.

    An explicit `kind` wins, as long as it agrees with the suffix of
    `result`. Otherwise the suffix decides, and failing that the `.exe` form
    is preferred (an icon was asked for, or both binaries are present), since
    it looks like a normal application; `.lnk` is the fallback that needs no
    binaries at all.
    """
    suffix = _result_suffix(result)
    if kind != 'auto':
        if kind not in KINDS:
            raise ValueError(
                '`kind` should be one of {}, not {!r}.'.format(KINDS, kind)
            )
        if suffix and suffix != '.' + kind:
            raise ValueError(
                '`kind` is {!r}, but `result` ends with {!r}.'.format(
                    kind, suffix
                )
            )
        return kind

    if suffix:
        return suffix[1:]
    if window_icon or not missing_assets('stub.exe', 'rcedit.exe'):
        return 'exe'
    return 'lnk'


def _resolve_result(source: Path, result: str, kind: str) -> Path:
    """Where the launcher file goes (see the command's docstring)."""
    text = result.strip()
    if not text:
        return source.with_suffix('.' + kind)

    suffix = _result_suffix(text)
    if suffix:
        if Path(text).name.lower() == suffix:
            # a bare ".exe" / ".lnk": the script's name, the chosen suffix.
            return source.with_suffix(suffix)
        return Path(text).absolute()

    path = Path(text)
    if path.is_dir():
        return path.absolute() / '{}.{}'.format(source.stem, kind)
    raise ValueError(
        '`result` should end with ".exe" or ".lnk", or name an existing '
        'directory: {!r}.'.format(result)
    )


def _result_suffix(result: str) -> str:
    text = result.strip().lower()
    if text in KINDS_SUFFIXES:
        return text
    return Path(text).suffix.lower() if text else ''


def _require_assets(kind: str, *, with_icon: bool) -> None:
    """Fail early, with instructions, when a binary that is not shipped is
    missing."""
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
        raise FileNotFoundError('no such icon: {}'.format(source))
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


def _shortcut_on_desktop(
    built: Built, config: LaunchConfig, desktop: Path
) -> Path:
    link = desktop / '{}.lnk'.format(built.path.stem)
    if built.path.suffix.lower() == '.exe':
        # a shortcut to the exe: windows takes the icon from it, so there is
        # nothing else to say.
        return make_lnk(
            link,
            target=built.path,
            workdir=config.cwd,
            icon=built.path,
            description=config.name,
        )
    return _make_lnk(config, link).path


def _arguments(config: LaunchConfig) -> str:
    """
    The command line a shortcut carries.

    A shortcut can point at a program and pass arguments, but it has no way
    to set environment variables -- so everything the `.exe` form keeps in
    its payload becomes an `--argsense-*` option here.
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
