"""
Fetch the two launcher binaries from the repository.

The wheel leaves `rcedit.exe` and `stub.exe` out (see `check_requirements`),
so a fresh install has to pull them once. `python -m argsense
pull-launcher-misc` is the command that does it; this module is the part
that talks to the network.
"""

import os
import typing as tp
import urllib.error
import urllib.request
from pathlib import Path

from .path import ASSETS

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
