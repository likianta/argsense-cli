"""
Record the help interface of a target script.

It runs the target script with `-h`, catches the help interface that rich
prints, saves it to an SVG, rasterizes the SVG to a PNG with a headless
Chrome / Edge, and finally prints the markdown snippet that inserts the image
into a document.

Usage (run from the project root):
    python sidework/record_help_interface.py <target_script> [<title>] \
        [<save_image_to>]

For example:
    python sidework/record_help_interface.py test/temp/main.py
    python sidework/record_help_interface.py test/temp/main.py groups
"""

from __future__ import annotations

import math
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import typing as t
from datetime import datetime
from pathlib import Path

import argsense
from rich.console import Console

import argsense.renderer.rich.render as R
from argsense import cli
from argsense.cli import CommandLineInterface

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

WIDTH = 120
#   keep it consistent with the screenshots used in the README.
SCALE = 2
#   export at 2x for a crisp look on retina screens.
FONT = 'Paper Mono Medium'
#   a monospace font installed locally; rich defaults to Fira Code and embeds an
#   @font-face that points to a CDN, which we replace (see `_use_local_font`).

_BROWSERS = (
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
)

_ORIGIN_CONSOLE = R.console


def main(
    target_script: str, title: str = '', save_image_to: str = 'docs/images'
):
    """
    Record the help interface of a target script.

    params:
        target_script: The path of the script to record. It is run with `-h`,
            and a relative path is resolved from the project root.
        title: The title of the image, and also the name of the png file when
            it is given. If it is omitted, a timestamp is used as the name.
        save_image_to: The directory that the png is written to. A relative path
            is resolved from the project root.
    """
    target = _resolve(target_script)
    if not target.exists():
        raise FileNotFoundError(target)

    dst = _resolve(save_image_to)
    dst.mkdir(parents=True, exist_ok=True)

    name = title or datetime.now().strftime('%y%m%d-%H%M%S')
    png = dst / '{}.png'.format(name)

    # the svg is only an intermediate, and is not kept in the repository.
    staging = Path(tempfile.mkdtemp(prefix='argsense-help-'))
    svg = staging / '{}.svg'.format(target.stem)
    try:
        _record(target, svg, title)
        _svg_to_png(svg, png)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print('wrote {}'.format(png.relative_to(ROOT)))
    print('![]({})'.format(png.relative_to(ROOT).as_posix()))


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _record(target: Path, svg: Path, title: str) -> None:
    """
    Run the target script and capture everything it prints through rich.
    """
    console = Console(
        width=WIDTH,
        record=True,
        force_terminal=True,
        color_system='truecolor',
        # keep the rounded panels (`rich.box.ROUNDED`) that a modern terminal
        # shows. without this, rich substitutes them for a "safe" square
        # variant, because `safe_box` defaults to true.
        safe_box=False,
        file=open(os.devnull, 'w', encoding='utf-8'),
    )
    R.console = console

    # the target script registers its commands into the module level `cli`
    # singleton. give it a fresh one, so that what the wrapper script has
    # registered (e.g. the `main` function of this tool) does not appear in the
    # recorded help interface.
    origin_cli = argsense.cli
    argsense.cli = CommandLineInterface()

    origin_argv = sys.argv
    sys.argv = [str(target), '-h']
    try:
        runpy.run_path(str(target), run_name='__main__')
    finally:
        sys.argv = origin_argv
        argsense.cli = origin_cli
        R.console = _ORIGIN_CONSOLE

    console.save_svg(str(svg), title=title or 'argsense')
    _use_local_font(svg)


def _use_local_font(svg: Path) -> None:
    # drop the @font-face that points to a CDN, and use a locally installed
    # font instead.
    text = svg.read_text(encoding='utf-8')
    text = re.sub(r'\s*@font-face \{.*?\}', '', text, flags=re.S)
    text = text.replace(
        'font-family: Fira Code, monospace;',
        "font-family: '{}', monospace;".format(FONT),
    )
    svg.write_text(text, encoding='utf-8')


# ------------------------------------------------------------------------------
# svg to png


def _svg_to_png(svg: Path, png: Path) -> None:
    width, height = _viewbox_size(svg)
    subprocess.run(
        [
            _find_browser(),
            '--headless=new',
            '--disable-gpu',
            '--hide-scrollbars',
            '--force-device-scale-factor={}'.format(SCALE),
            '--window-size={},{}'.format(width, height),
            '--screenshot={}'.format(png.resolve()),
            svg.resolve().as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _find_browser() -> str:
    for path in _BROWSERS:
        if Path(path).exists():
            return path
    for name in ('chrome', 'msedge'):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit('no chrome / edge found; cannot convert svg to png.')


def _viewbox_size(svg: Path) -> t.Tuple[int, int]:
    match = re.search(
        r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text('utf-8')
    )
    if not match:
        raise SystemExit('cannot read the viewBox from {}'.format(svg))
    return math.ceil(float(match.group(1))), math.ceil(float(match.group(2)))


if __name__ == '__main__':
    cli.run(main)
