"""
Compile `src/stub.v` into `assets/stub.exe`.

Run by the maintainer, once, not by the people who build launchers: the
compiled binary ships with argsense, so a user never needs a v toolchain to
make a `.exe` launcher (and never has to trust one either).

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
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
