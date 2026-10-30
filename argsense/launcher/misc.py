import os
import shutil
import subprocess
import typing as tp
import urllib.error
import urllib.request
from pathlib import Path

from .path import ASSETS
from .path import PKG_ROOT
from .path import STUB

REPO = 'https://github.com/likianta/argsense-cli'
BRANCH = 'master'
NAMES = ('rcedit.exe', 'stub.exe')
#   both are looked up in the repository's "misc" folder, and written under
#   `<argsense>/launcher/assets` (the only place the code reads them from).
RAW = 'https://raw.githubusercontent.com/likianta/argsense-cli/{}/misc/{}'
#   `--mirror-site`: a github proxy, for when raw.githubusercontent.com is
#   slow or blocked. It takes the full url as a suffix.
MIRROR_PREFIX = 'https://ghproxy.net/'
TIMEOUT = 30
CHUNK = 64 * 1024


def pull_assets(
    mirror_site: bool = False, force: bool = False
) -> tp.List[Path]:
    """
    Download the binaries into `<argsense>/launcher/assets`.

    Files that are already there are left alone unless `force` is set.
    Returns the files actually written.
    """
    assets = Path(ASSETS)
    assets.mkdir(parents=True, exist_ok=True)

    written: tp.List[Path] = []
    for name in NAMES:
        file_o = assets / name
        if file_o.is_file() and not force:
            print(
                '{} is already there ({:,} bytes), skipped.'.format(
                    file_o, file_o.stat().st_size
                )
            )
            continue
        _download(_url_of(name, mirror_site), file_o)
        written.append(file_o)
    return written


def build_launcher_stub(file_o: str = STUB) -> None:
    """
    Compile `src/stub.v` into `assets/stub.exe`.
    """
    v = shutil.which('v')
    if v is None:
        raise Exception('`v` is not on PATH. see https://vlang.io/')

    target = Path(file_o)
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        (v, '-cc', 'tcc', '-o', str(target), f'{PKG_ROOT}/launcher/stub.v')
    )
    if result.returncode == 0:
        # v drops a debug symbol file next to the binary; it is not part of
        # what ships, and leaving it in the package only adds noise.
        pdb = target.with_suffix('.pdb')
        if pdb.exists():
            pdb.unlink()
        print('built: {} ({} bytes)'.format(target, target.stat().st_size))

        possible_proj_path = os.path.dirname(PKG_ROOT)
        if (
            os.path.exists(f'{possible_proj_path}/.git')
            and os.path.exists(f'{possible_proj_path}/pyproject.toml')
            and os.path.exists(f'{possible_proj_path}/misc')
        ):
            shutil.copy2(target, f'{possible_proj_path}/misc/stub.exe')
            print(
                'also updated: {}'.format(f'{possible_proj_path}/misc/stub.exe')
            )
    else:
        print('v compile failed. return code: {}'.format(result.returncode))


def _url_of(name: str, mirror_site: bool) -> str:
    raw = RAW.format(BRANCH, name)
    return MIRROR_PREFIX + raw if mirror_site else raw


def _download(url: str, file_o: Path) -> None:
    """Stream `url` into `file_o`, via a `.part` file that only gets renamed
    once the bytes are complete and look like a windows executable."""
    part = file_o.with_name(file_o.name + '.part')
    print('downloading {} ...'.format(url))

    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            total = int(response.headers.get('Content-Length') or 0)
            with open(part, 'wb') as f:
                while chunk := response.read(CHUNK):
                    f.write(chunk)
    except (urllib.error.URLError, OSError) as ex:
        part.unlink(missing_ok=True)
        raise RuntimeError(
            'failed to download {}: {}\n'
            'If github is unreachable from here, try again with '
            '`python -m argsense pull-launcher-misc --mirror-site`, or fetch '
            'the file by hand from {}/tree/{}/misc.'.format(
                url, ex, REPO, BRANCH
            )
        ) from ex

    size = part.stat().st_size
    if total and size != total:
        part.unlink(missing_ok=True)
        raise RuntimeError(
            'the download stopped early ({} of {} bytes): {}'.format(
                size, total, url
            )
        )

    # A proxy that answers with an error page still answers with 200. Both
    # files are windows executables, so the dos header is a cheap check that
    # what arrived is the binary and not a web page.
    with open(part, 'rb') as f:
        magic = f.read(2)
    if magic != b'MZ':
        part.unlink(missing_ok=True)
        raise RuntimeError(
            'what came back is not a windows executable (starts with {!r}): '
            '{}'.format(magic, url)
        )

    os.replace(part, file_o)
    print('  saved {} ({:,} bytes)'.format(file_o, size))


if __name__ == '__main__':
    build_launcher_stub()
