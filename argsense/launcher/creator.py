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
from .path import ASSETS
from .path import DESKTOP
from .path import RCEDIT
from .path import STUB


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
                    binaries from argsense repository or build by yourself.

                    (a) The repository link: 
                        https://github.com/likianta/argsense-cli/tree/main/misc

                        Fetch "rcedit.exe" and "stub.exe" then put them under 
                        `<argsense>/launcher/assets` folder.
                    
                    (b) Build by yourself:

                        - rcedit.exe: download it from the official releases 
                            (https://github.com/electron/rcedit/releases), put
                            it under `<argsense>/launcher/assets` folder.

                        - stub.exe: install V compiler (at least v0.5.x) then:
                            ```
                            python -m argsense.launcher.misc build_stub
                            ```
                            It generates a "stub.exe" in 
                            `<argsense>/launcher/assets`.
                    """
                )
            )
        return True

    try:
        if source:
            assert source.endswith('.py') and os.path.exists(source)

        if kind == 'exe':
            assert os.path.exists(STUB), dedent(
                """
                Cannot find "stub.exe" in "{PATH}". This is usual problem if 
                you see it at first time after `pip install argsense`, because 
                argsense does not ship this binary with its ".whl" package.
                
                To get it, you can download from the repository site's "misc" 
                folder (link: {LINK}), or -- if you have installed V (0.5.x) in 
                your computer -- you can build it by yourself by 
                `python -m argsense.launcher.misc build_stub`.
                """
            ).format(
                PATH=ASSETS,
                LINK='https://github.com/likianta/argsense-cli/tree/main/misc',
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

                        To get it, you can download from the repository site's 
                        "misc" folder (link: {LINK}), or download it from the 
                        official releases 
                        (https://github.com/electron/rcedit/releases).

                        Finally put it under `<argsense>/launcher/assets` 
                        folder.
                        """
                    ).format(
                        PATH=ASSETS,
                        LINK='https://github.com/likianta/argsense-cli/tree'
                        '/main/misc',
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
) -> tp.Tuple[str, LaunchConfig]:
    """
    Write the launcher (and, optionally, a shortcut to it on the desktop).
    Returns the files written, in the order they were created.
    """
    if target:
        name = os.path.basename(target).rsplit('.', 1)[0]
    else:
        name = os.path.basename(source).removesuffix('.py')
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
        script=source,
        cwd=os.getcwd(),
        args=(':gui',),
        name=name,
        icon=icon,
        port=port,
        window_size=window_size,
        window_title=window_title,
        show_console=show_console,
    )

    if kind == 'exe':
        return make_exe(cfg, target), cfg
    else:
        return make_lnk(cfg, target), cfg


def _file_to_unique_id(file: str) -> str:
    with open(file, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
