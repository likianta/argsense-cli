import os.path
import typing as tp

from .cli import CommandLineInterface
from .launcher import ASSETS
from .launcher import DESKTOP
from .launcher import check_requirements
from .launcher import create_launcher as _do_create_launcher
from .launcher import make_lnk


def create_launcher(
    script: str,
    name: str = '',
    output_directory: str = DESKTOP,
    port: int = 0,
    kind: tp.Literal['auto', 'exe', 'lnk'] = 'auto',
    title: str = '',
    size: str = '',
    icon: str = '{}/python.png'.format(ASSETS),
    show_console: bool = False,
    add_to_desktop_shortcut: bool = True,
) -> None:
    """
    Wrap a script in a launcher that can be double-clicked.
    For a practical scene, we suggest passing at least `script` and `name` to -
    this command.

    Args:
        script (-s): The path of the ".py" file to start.
        output_directory (-o): Be default, it outputs to Desktop path.
        name (-n):
            The name can be one of the three forms:

            1. `<stem>`, for example "MyApp".
                The extension will be deduced by `kind` param.
            2. `<stem>.<kind>`, for example "MyApp.exe" or "MyApp.lnk".
                It creates file with the exact name under `output_directory`.
            3. `.<kind>`, can only be ".exe" or ".lnk".
                The name stem borrows from `script`.

            To give a name contains whitespaces, you need to quote it as the -
            convention of regular command line args.
        kind (-k):
            'auto': auto deduce the proper value, it prefers "exe" if possible -
            else fallback to "lnk".
            Or you can explicitly set "exe" or "lnk".
            Be noted if the `kind` conflicts with `name` (if set), it raises -
            an error.
        title: The text in the window's title bar.
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
        source=script,
        kind=('exe' if _is_exe_tooling_ready(icon) else 'lnk')
        if kind == 'auto'
        else kind,
        icon=icon,
        show_console=show_console,
        autofix=True,
    )
    script, file_target, file_shortcut, kind, size = _parse_params(**locals())

    _, cfg = _do_create_launcher(
        source=script,
        target=file_target,
        kind=kind,
        icon=icon,
        window_title=title,
        window_size=size,
        port=port,
        show_console=show_console,
    )

    if (
        file_shortcut and file_shortcut != file_target
    ):  # add_to_desktop_shortcut
        cfg.python = file_target  # FIXME
        cfg.icon = file_target  # FIXME
        make_lnk(cfg, file_shortcut)
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
    script: str,
    name: str,
    output_directory: str,
    kind: str,
    icon: str,
    size: tp.Any,
    add_to_desktop_shortcut: bool,
    **_,
) -> tuple:
    assert script.endswith('.py') and os.path.exists(script)
    if icon:
        assert icon.endswith(('.ico', '.png')) and os.path.exists(icon)

    # resolve name_stem
    if name:
        if name.endswith(('.exe', '.lnk')):
            name_stem = name[:-4] or os.path.basename(script).removesuffix(
                '.py'
            )
            if kind == 'auto':
                kind = name[-3:]
            else:
                assert kind == name[-3:]
        else:
            name_stem = name
    else:
        name_stem = os.path.basename(script).removesuffix('.py')

    # resolve kind
    if kind == 'auto':
        kind = _prefer_kind(icon)
    else:
        assert kind in ('exe', 'lnk')

    # resolve final paths
    file_target = '{}/{}.{}'.format(output_directory, name_stem, kind)
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

    return (script, file_target, file_shortcut, kind, size)


def _prefer_kind(window_icon: str) -> tp.Literal['exe', 'lnk']:
    """
    Settle on 'exe' or 'lnk'. We prefer 'exe' if any condition meets it; if -
    none of the conditions meet, fallback to 'lnk' or raise error.
    """
    if window_icon:
        if os.path.exists('{}/rcedit.exe'.format(ASSETS)):
            return 'exe'
        else:
            raise Exception
    else:
        if os.path.exists('{}/stub.exe'.format(ASSETS)):
            return 'exe'
        else:
            return 'lnk'


if __name__ == '__main__':
    # python -m argsense -h
    # python -m argsense create_launcher -h
    CommandLineInterface().run((create_launcher,))
