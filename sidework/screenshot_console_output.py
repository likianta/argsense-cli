"""
Record the console output of a scenario script.

Unlike `record_help_interface.py`, which only captures the `-h` interface of a
target script, this tool records an arbitrary console session: the scenario
script owns the logic, so it can print shell prompts, render several help
interfaces, run functions and mix in their plain `print()` output.

The session is captured with a recording rich `Console`, saved to an SVG,
rasterized to a PNG with a headless Chrome / Edge, and the markdown snippet
that inserts the image into a document is printed at the end.

Usage (run from the project root):
    python sidework/screenshot_console_output.py <scenario> \
        [--argv "<extra words>"] [--title <str>] [--save-image-to <dir>]

For example:
    python sidework/screenshot_console_output.py test/depsland_like.py
    python sidework/screenshot_console_output.py test/depsland_like.py \
        --argv "runx -h"
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
from datetime import timedelta
from pathlib import Path

import argsense
from rich.console import Console
from rich.text import Text

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
    scenario: str,
    argv: str = '',
    title: str = '',
    save_image_to: str = 'docs/images',
):
    """
    Record the console output produced by a scenario script.

    params:
        scenario: The path of the scenario script to record. It is executed
            with `__name__ == '__main__'`, and a relative path is resolved from
            the project root.
        argv: Extra command line words to append after the scenario path, for
            example "runx -h". It becomes the `sys.argv` of the scenario.
        title: The window caption of the recorded image. If it is omitted,
            "argsense" is used.
        save_image_to: The directory that the png is written to. A relative path
            is resolved from the project root.
    """
    target = _resolve(scenario)
    if not target.exists():
        raise FileNotFoundError(target)

    dst = _resolve(save_image_to)
    dst.mkdir(parents=True, exist_ok=True)
    png = _unique_path(dst)

    # the svg is only an intermediate, and is not kept in the repository.
    staging = Path(tempfile.mkdtemp(prefix='argsense-shot-'))
    svg = staging / '{}.svg'.format(target.stem)
    try:
        _record(target, svg, title, argv)
        _svg_to_png(svg, png)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print('wrote {}'.format(png.relative_to(ROOT)))
    print('![]({})'.format(png.relative_to(ROOT).as_posix()))


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def _unique_path(dst: Path) -> Path:
    stamp = datetime.now()
    while True:
        png = dst / '{}.png'.format(stamp.strftime('%y%m%d-%H%M%S'))
        if not png.exists():
            return png
        stamp += timedelta(seconds=1)


def _record(target: Path, svg: Path, title: str, argv: str) -> None:
    """
    Run the scenario script and capture everything it prints through rich.
    """
    # argparse / click / typer / cyclopts wrap their help text to the terminal
    # width; pin it, so that the recorded image is stable.
    os.environ.setdefault('COLUMNS', '80')

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

    # the scenario registers its commands into the module level `cli` singleton.
    # give it a fresh one, so that what the wrapper script has registered (e.g.
    # the `main` function of this tool) does not appear in the output.
    origin_cli = argsense.cli
    argsense.cli = CommandLineInterface()

    origin_argv = sys.argv
    origin_stdout = sys.stdout
    origin_stderr = sys.stderr
    sys.argv = [str(target), *argv.split()]
    sys.stdout = _ConsoleStream(console)
    sys.stderr = sys.stdout
    try:
        runpy.run_path(str(target), run_name='__main__')
    except SystemExit:
        # `-h` handlers (argparse, click, ...) exit the process; that is the
        # expected way for them to end, so it must not abort the recording.
        pass
    finally:
        sys.stdout.flush()
        sys.argv = origin_argv
        sys.stdout = origin_stdout
        sys.stderr = origin_stderr
        argsense.cli = origin_cli
        R.console = _ORIGIN_CONSOLE

    console.save_svg(str(svg), title=title or 'argsense')
    _use_local_font(svg)


class _ConsoleStream:
    """
    Forward plain `print()` output to the recording console.

    rich only records what is rendered through a `Console`, so whatever a
    scenario (or the function it runs) writes to `sys.stdout` has to be
    redirected into the console to show up in the image.
    """

    encoding = 'utf-8'

    def __init__(self, console: Console) -> None:
        self._console = console
        self._buffer = ''

    def write(self, text: str) -> int:
        self._buffer += text
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            self._emit(line)
        return len(text)

    def flush(self) -> None:
        if self._buffer:
            line, self._buffer = self._buffer, ''
            self._emit(line)

    def isatty(self) -> bool:
        return False

    def _emit(self, line: str) -> None:
        # third party writers (neoprint, click, ...) may colorize their output
        # with ANSI escapes; decode them into rich text instead of forwarding
        # the raw escape sequences.
        self._console.print(
            Text.from_ansi(line), highlight=False, soft_wrap=True
        )


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
