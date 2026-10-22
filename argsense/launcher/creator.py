"""
Build a launcher: the decisions, and the two forms they turn into.

`argsense/__main__.py` owns the command (and its user-facing docstring); this
module holds what that command delegates to.
"""

import hashlib
import os
import typing as tp
from textwrap import dedent

from .config import LaunchConfig
from .exe import make_exe
from .icon import png_to_ico
from .interpreter import fix_pythonw
from .interpreter import get_interpreter_path
from .interpreter import get_pythonw
from .interpreter import is_real_pythonw
from .lnk import make_lnk
from .misc import BRANCH
from .path import ASSETS
from .path import DESKTOP
from .path import RCEDIT
from .path import STUB


def is_module_source(source: str) -> bool:
    if source.endswith('.py'):
        return False
    return all(part.isidentifier() for part in source.split('.'))


def check_requirements(
    source: str = '',
    kind: str = '',
    icon: str = '',
    show_console: bool = False,
    # ---
    all: bool = False,
    autofix: bool = False,
    quiet: bool = False,
) -> bool:

    if all:  # `all=True` ignores `quiet` and `autofix` settings.
        if not is_real_pythonw(get_pythonw()):
            fix_pythonw()
        if not os.path.exists(STUB) or not os.path.exists(RCEDIT):
            raise Exception(
                dedent(
                    """
                    ArgSense does not ship "rcedit.exe" and "stub.exe" with its
                    ".whl" package, so to get the full ability of generating 
                    launcher from a function, you need to download those 
                    binaries. Run this once:

                        python -m argsense pull-launcher-misc

                    (add `--mirror-site` when github is slow or unreachable.)

                    If that does not work, put both files under 
                    "<argsense>/launcher/assets" by hand:

                    (a) The repository link: 
                        https://github.com/likianta/argsense-cli/tree/{BRANCH}/misc

                    (b) Build by yourself:

                        - rcedit.exe: download it from the official releases 
                            (https://github.com/electron/rcedit/releases).

                        - stub.exe: install V compiler (at least v0.5.x) then:
                            ```
                            python argsense/launcher/src/build.py
                            ```
                    """
                ).format(BRANCH=BRANCH)
            )
        return True

    try:
        if source:
            assert is_module_source(source) or (
                source.endswith('.py') and os.path.exists(source)
            ), 'no such script or module: {!r}'.format(source)

        if kind == 'exe':
            assert os.path.exists(STUB), dedent(
                """
                Cannot find "stub.exe" in "{PATH}". This is usual problem if 
                you see it at first time after `pip install argsense`, because 
                argsense does not ship this binary with its ".whl" package.
                
                To get it, run `python -m argsense pull-launcher-misc` (add 
                `--mirror-site` when github is slow or unreachable), or 
                download it from the repository site's "misc" folder 
                (link: {LINK}).
                """
            ).format(
                PATH=ASSETS,
                LINK='https://github.com/likianta/argsense-cli/tree/{}/misc'.format(
                    BRANCH
                ),
            )

        if not show_console and (not quiet or autofix):
            pythonw = get_pythonw()
            if not is_real_pythonw(pythonw):
                if autofix:
                    fix_pythonw()
                elif not quiet:
                    print(
                        ':pv6',
                        dedent(
                            """
                            The pythonw.exe ({}) is not a real pythonw which is 
                            shipped with official python interpreter.

                            It is usual that `uv` (and possibly other tools) 
                            create a venv's `pythonw.exe` as a plain copy of 
                            `python.exe`.
                            
                            To build a no-console-window GUI application, 
                            argsense will try to replace it with the real 
                            pythonw at appropriate time if needed. You don't 
                            worry about this.
                            """.format(pythonw)
                        ),
                    )

        if icon:
            assert icon.endswith(('.ico', '.png'))
            assert os.path.exists(icon)

            if icon.endswith('.png'):
                try:
                    import PIL  # noqa
                except ImportError as e:
                    raise Exception(
                        'pillow (pip install pillow) is required to convert a '
                        '".png" icon to ".ico" format.'
                    ) from e

            if kind == 'exe' and not os.path.exists(RCEDIT):
                raise Exception(
                    dedent(
                        """
                        Cannot find "rcedit.exe" in "{PATH}". This is usual 
                        problem if you see it at first time after 
                        `pip install argsense`, because argsense does not ship 
                        this binary with its ".whl" package.

                        To get it, run `python -m argsense pull-launcher-misc` 
                        (add `--mirror-site` when github is slow or 
                        unreachable), or download "rcedit.exe" from the 
                        repository's "misc" folder (link: {LINK}), or from 
                        the official releases 
                        (https://github.com/electron/rcedit/releases).

                        Finally put it under `<argsense>/launcher/assets` 
                        folder.
                        """
                    ).format(
                        PATH=ASSETS,
                        LINK='https://github.com/likianta/argsense-cli/tree'
                        '/{}/misc'.format(BRANCH),
                    )
                )
    except Exception:
        if quiet:
            return False
        else:
            raise
    else:
        return True


def create_launcher(
    source: str,
    target: str = '',
    *,
    kind: tp.Literal['exe', 'lnk'] = 'exe',
    icon: str = '',
    window_title: str = '',
    window_size: tp.Optional[tp.Tuple[int, int]] = None,
    port: int = 0,
    show_console: bool = False,
    args: tp.Sequence[str] = (':gui',),
) -> tp.Tuple[str, LaunchConfig]:
    """
    Write the launcher (and, optionally, a shortcut to it on the desktop).
    Returns the files written, in the order they were created.

    `source` is either a ".py" file to start, or a dotted module to run with
    `-m` (the form of `python -m foo.bar`). `args` are handed to the target
    after its script / module name, and default to the `:gui` token.
    """
    is_module = is_module_source(source)
    if target:
        name = os.path.basename(target).rsplit('.', 1)[0]
    else:
        name = (
            source.rsplit('.', 1)[-1]
            if is_module
            else os.path.basename(source).removesuffix('.py')
        )
        target = '{}/{}.{}'.format(DESKTOP, name, kind)

    if icon and icon.endswith('.png'):
        icon = png_to_ico(
            icon,
            '{}/generated_icons/{}.ico'.format(
                ASSETS, _file_to_unique_id(icon)
            ),
        )

    cfg = LaunchConfig(
        python=get_interpreter_path(show_console),
        # absolute: the launcher may be double-clicked from anywhere, and
        # the stub checks the file before it enters `cwd`.
        script='' if is_module else os.path.abspath(source),
        cwd=os.getcwd(),
        args=tuple(args),
        name=name,
        module=source if is_module else '',
        icon=icon,
        port=port,
        window_size=window_size,
        window_title=window_title,
        show_console=show_console,
    )

    os.makedirs(os.path.dirname(target) or '.', exist_ok=True)
    if kind == 'exe':
        return make_exe(cfg, target), cfg
    else:
        return make_lnk(cfg, target), cfg


def _file_to_unique_id(file: str) -> str:
    with open(file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
