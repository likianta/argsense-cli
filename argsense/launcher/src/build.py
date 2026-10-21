"""
Compile `src/stub.v` into `assets/stub.exe`.

Run by the maintainer, once, not by the people who build launchers: the
compiled binary is downloaded from the repository rather than shipped with
argsense, so a user never needs a v toolchain to make a `.exe` launcher (and
never has to trust one either).

The binary is kept in *two* places: `assets/` (what the code runs) and the
repository's `misc/` (what gets pushed). This script writes both, so a change
to `stub.v` cannot end up in one and not the other.

`-cc tcc` rather than v's default: on a machine with msvc installed, v picks
it for `-prod` builds, and msvc's linker spells the gui subsystem differently
(`/SUBSYSTEM:WINDOWS`), which the `#flag` in the source does not match. tcc
is bundled with v, so it is also the one backend that is always there.
"""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / 'stub.v'
TARGET = ROOT.parent / 'assets' / 'stub.exe'
# the copy that travels with the repository (the wheel has no binaries).
MISC = ROOT.parents[2] / 'misc'


def main() -> int:
    v = shutil.which('v')
    if v is None:
        print('v is not on PATH. see https://vlang.io/')
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run((v, '-cc', 'tcc', '-o', str(TARGET), str(SOURCE)))
    if result.returncode == 0:
        # v drops a debug symbol file next to the binary; it is not part of
        # what ships, and leaving it in the package only adds noise.
        pdb = TARGET.with_suffix('.pdb')
        if pdb.exists():
            pdb.unlink()
        print('built: {} ({} bytes)'.format(TARGET, TARGET.stat().st_size))
        if MISC.is_dir():
            shutil.copy2(TARGET, MISC / 'stub.exe')
            print('also updated: {}'.format(MISC / 'stub.exe'))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
