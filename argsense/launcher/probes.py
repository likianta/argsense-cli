"""
Checks the launcher runs before it builds anything.

`ensure_gui_pythonw` fixes a venv whose `pythonw.exe` is not the windowed
interpreter it promises to be; `require_assets` explains what to do when the
binaries that are deliberately *not* shipped with argsense are missing.
"""

import shutil
import struct
import sys
import typing as tp
from pathlib import Path

ASSETS = Path(__file__).parent / 'assets'

# the binaries live outside the package (and outside the wheel): they are
# ~2.5 MB, and a `.lnk` launcher does not need them at all, so paying for
# them on every `pip install` was judged a bad trade.
MISC_URL = 'https://github.com/likianta/argsense-cli/tree/main/misc'
RCEDIT_URL = 'https://github.com/electron/rcedit/releases'


def pe_subsystem(file: tp.Union[str, Path]) -> int:
    """
    The subsystem field of a windows executable's PE header.

    `2` is a gui program (no console), `3` is a console program. Anything
    else (`1` native, `9`/`10` efi) is not something we ever launch, but it
    is returned as is rather than raising, so the caller can report a useful
    message.
    """
    with open(file, 'rb') as f:
        dos_header = f.read(0x40)
        pe_offset = struct.unpack_from('<I', dos_header, 0x3C)[0]
        # the optional header starts right after the 4-byte signature and the
        # 20-byte COFF header; `Subsystem` sits at +68 for pe32 and pe32+.
        f.seek(pe_offset + 24 + 68)
        return struct.unpack('<H', f.read(2))[0]


def is_gui_subsystem(file: tp.Union[str, Path]) -> bool:
    return pe_subsystem(file) == 2


def base_pythonw() -> Path:
    """
    The windowed interpreter of the *base* install.

    `sys._base_executable` points at the base `python.exe` even when we are
    running inside a venv; the base install's `pythonw.exe` is the genuine
    gui-subsystem one.
    """
    base = getattr(sys, '_base_executable', sys.executable)
    return Path(base).with_name('pythonw.exe')


def ensure_gui_pythonw(
    venv_dir: tp.Union[str, Path], *, dry_run: bool = False
) -> tp.Tuple[Path, bool]:
    """
    Make sure `venv/Scripts/pythonw.exe` really is a windowed interpreter.

    `uv` (and possibly other tools) create a venv's `pythonw.exe` as a plain
    copy of `python.exe`, and that copy is a *console* binary: starting it
    still opens a black window. A launcher aimed at such a file flashes a
    console on every double-click, no matter what flags the launcher passes,
    because the window comes from the interpreter itself.

    The base install does ship a real `pythonw.exe` (subsystem 2), and copying
    it next to `pyvenv.cfg` is exactly what cpython's own `venv` does on
    windows. The copy still resolves the venv -- that is decided by
    `pyvenv.cfg` sitting in `Scripts`'s parent, not by the binary.

    The replaced file needs no backup: it was a copy of `python.exe`, which
    is still there.

    Returns the path and whether it had to be replaced.
    """
    target = Path(venv_dir) / 'Scripts' / 'pythonw.exe'
    if not target.exists():
        raise FileNotFoundError(target)

    if is_gui_subsystem(target):
        return target, False

    source = base_pythonw()
    if not source.exists():
        raise FileNotFoundError(
            'the venv has no windowed interpreter and the base one is '
            'missing: {}'.format(source)
        )
    if not is_gui_subsystem(source):
        raise RuntimeError(
            'the base install has no gui-subsystem pythonw either: {}'.format(
                source
            )
        )

    if not dry_run:
        shutil.copy2(source, target)
    return target, True


def missing_assets(*names: str) -> tp.List[str]:
    """Which of `names` are not sitting in the package's `assets` folder."""
    return [name for name in names if not (ASSETS / name).is_file()]


def assets_hint(missing: tp.Iterable[str]) -> str:
    """What to tell someone whose `assets` folder is empty."""
    names = ', '.join(missing)
    return (
        'argsense does not ship these binaries, so {names} is missing.\n'
        '\n'
        'either download it from the repository\n'
        '    {misc}\n'
        'and put it in\n'
        '    {assets}\n'
        '\n'
        'or build / fetch it yourself\n'
        '    stub.exe    compile src/stub.v with v:\n'
        '                python -m argsense.launcher.src.build\n'
        '    rcedit.exe  {rcedit}\n'
        '\n'
        'a `.lnk` launcher (--kind lnk) needs neither of them.'
    ).format(names=names, misc=MISC_URL, assets=ASSETS, rcedit=RCEDIT_URL)


def require_assets(*names: str) -> None:
    """Raise with the instructions above when a binary is missing."""
    missing = missing_assets(*names)
    if missing:
        raise RuntimeError(assets_hint(missing))
