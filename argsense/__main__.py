import os.path
import typing as tp

from .cli import CommandLineInterface
from .launcher import ASSETS
from .launcher import DESKTOP
from .launcher import check_requirements
from .launcher import create_launcher as _do_create_launcher
from .launcher import is_module_source
from .launcher import make_lnk


def create_launcher(
    source: str,
    name: str = '',
    output_directory: str = DESKTOP,
    kind: tp.Literal['auto', 'exe', 'lnk'] = 'auto',
    title: str = '',
    size: str = '',
    icon: str = '{}/launcher.png'.format(ASSETS),
    port: int = 0,
    show_console: bool = False,
    add_to_desktop_shortcut: bool = True,
) -> None:
    """
    Wrap a script (or a module) in a launcher that can be double-clicked.
    For a practical scene, we suggest passing at least `source` and `name` to -
    this command.

    Args:
        source (-s): The path to ".py" file, or module form like "aaa.bbb.ccc".
        name (-n):
            The name can be one of the three forms:

            1. `<stem>`, for example "MyApp".
                The extension will be deduced by `kind` param.
            2. `<stem>.<kind>`, for example "MyApp.exe" or "MyApp.lnk".
                It creates file with the exact name under `output_directory`.
            3. `.<kind>`, can only be ".exe" or ".lnk".
                The name stem borrows from `source`.

            To give a name contains whitespaces, you need to quote it as the -
            convention of regular command line args.
        output_directory (-o): Be default, it outputs to Desktop path.
        kind (-k):
            'auto': auto deduce the proper value, it prefers "exe" if possible -
            else fallback to "lnk".
            Or you can explicitly set "exe" or "lnk".
            Be noted if the `kind` conflicts with `name` (if set), it raises -
            an error.
        title (-t): The text in the window's title bar.
        size (-z): The window size, written as "980x820".
        icon (-i): A ".png" or ".ico" file. Both for launcher and window.
        port (-p):
            The port to serve on. 0 means always picking a free one at each -
            start.
        show_console (-c): Keep a console window open, for debugging.
        add_to_desktop_shortcut (-d):
            If target launcher is not generated to desktop (i.e. if you set -
            `output_directory` a specific path), enable this option so we will -
            create a desktop shortcut points to the origin launcher.
    """
    check_requirements(
        source=source,
        kind=('exe' if _is_exe_tooling_ready(icon) else 'lnk')
        if kind == 'auto'
        else kind,
        icon=icon,
        show_console=show_console,
        autofix=True,
    )
    source, file_target, file_shortcut, kind, size = _parse_params(**locals())

    _, cfg = _do_create_launcher(
        source=source,
        target=file_target,
        kind=kind,
        icon=icon,
        window_title=title,
        window_size=size,
        port=port,
        show_console=show_console,
    )

    if file_shortcut:  # add_to_desktop_shortcut
        # the shortcut points at the launcher itself, and carries no
        # arguments of its own: the launcher already knows what to start.
        cfg.python = file_target
        cfg.args = ()
        cfg.icon = file_target if kind == 'exe' else icon
        make_lnk(cfg, file_shortcut, arguments='')
        print(
            ':tv4',
            'done. see launcher at "{}" and its desktop shortcut "{}"'.format(
                file_target, os.path.basename(file_shortcut)
            ),
        )
    else:
        print(':tv4', 'done. see launcher at "{}"'.format(file_target))


def _is_exe_tooling_ready(icon: str = '') -> bool:
    return check_requirements(
        kind='exe',
        # icon='{}/launcher.png'.format(ASSETS),
        icon=icon,
        show_console=False,
        quiet=True,
    )


def _parse_params(
    *,
    source: str,
    name: str,
    output_directory: str,
    kind: str,
    icon: str,
    size: tp.Any,
    add_to_desktop_shortcut: bool,
    **_,
) -> tuple:
    if not (
        is_module_source(source)
        or (source.endswith('.py') and os.path.exists(source))
    ):
        raise ValueError(
            '`source` should be an existing ".py" file, or a module name '
            'like "aaa.bbb.ccc": {!r}'.format(source)
        )
    if icon:
        assert icon.endswith(('.ico', '.png')) and os.path.exists(icon)

    # resolve name_stem, and the kind its suffix claims (if any).
    name_stem: str
    name_kind: str = ''
    if name.endswith(('.exe', '.lnk')):
        name_kind = name[-3:]
        name_stem = name[:-4] or _default_stem(source)
    else:
        name_stem = name or _default_stem(source)

    # resolve kind: an explicit one wins, then the name's suffix, and 'auto'
    # falls back to whichever form can be built here.
    if kind == 'auto':
        kind = name_kind or _prefer_kind(icon)
    else:
        assert kind in ('exe', 'lnk')
        if name_kind:
            assert kind == name_kind

    # resolve final paths. the target is absolute because a shortcut on the
    # desktop can only point at an absolute path.
    file_target = os.path.abspath(
        '{}/{}.{}'.format(output_directory, name_stem, kind)
    )
    file_shortcut = (
        '{}/{}.{}'.format(DESKTOP, name_stem, 'lnk')
        if add_to_desktop_shortcut and not file_target.startswith(DESKTOP)
        else ''
    )

    if size:
        w, _, h = size.partition('x')
        size = (int(w), int(h))
    else:
        size = None

    return (source, file_target, file_shortcut, kind, size)


def _default_stem(source: str) -> str:
    """The name a launcher borrows from `source`: "bar" for "foo.bar"."""
    if is_module_source(source):
        return source.rsplit('.', 1)[-1]
    return os.path.basename(source).removesuffix('.py')


def _prefer_kind(icon: str) -> tp.Literal['exe', 'lnk']:
    """
    Settle on 'exe' or 'lnk' when the caller left it to us. 'exe' looks like a
    normal application, so it wins whenever its tooling is there; 'lnk' needs
    no binaries at all and is the fallback.
    """
    return 'exe' if _is_exe_tooling_ready(icon) else 'lnk'


if __name__ == '__main__':
    # python -m argsense -h
    # python -m argsense create_launcher -h
    CommandLineInterface().run((create_launcher,))
