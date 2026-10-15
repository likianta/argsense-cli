"""
Regenerate every screenshot that the README shows.

The scene definitions live in `sidework/readme_scenes.py`. There are three kinds
of figures:

- `script`: run a scenario script with a help request and record its help
  interface, e.g. `test/depsland_mock.py -h`.
- `console`: run a console scene: a simulated shell session, or a bare help
  interface. The scene owns the printing (see `readme_scenes.py`).
- `tui`: drive a textual form headlessly with `Pilot`, export its layout to an
  svg, and rasterize it like the console ones.

Every figure is written to `docs/images/<name>.png`, using a stable name, so
refreshing never leaves an orphan image behind.

Usage (run from the project root):
    python sidework/readme_screenshots.py               # refresh everything
    python sidework/readme_screenshots.py tui-overview  # refresh one figure
    python sidework/readme_screenshots.py a,b,c         # refresh several
"""

from __future__ import annotations

import asyncio
import os
import re
import runpy
import shutil
import sys
import tempfile
import typing as t
from dataclasses import dataclass
from pathlib import Path

import argsense
from rich.console import Console

import argsense.renderer.rich.render as R
from argsense import cli
from argsense.cli import CommandLineInterface

import screenshot_console_output as shot
from readme_scenes import CONSOLE_SCENES
from readme_scenes import TUI_SCENES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


@dataclass
class Figure:
    name: str
    kind: str
    #   'script' | 'console' | 'tui' | 'manual'
    scene: str = ''
    script: str = ''
    argv: str = ''
    title: str = 'argsense'


# the order follows the README, and a name is the image file's stem.
FIGURES: t.List[Figure] = [
    # -- the screenshots at the top of the README -------------------------------
    Figure(
        '261015-140133', 'script', script='test/depsland_mock.py', argv='-h'
    ),
    Figure(
        '261015-140405',
        'script',
        script='test/depsland_mock.py',
        argv='runx -h',
    ),
    Figure('tui-overview', 'tui', scene='overview', title='argsense'),
    # -- comparison with other libraries ----------------------------------------
    Figure('261015-140453', 'console', scene='hello'),
    Figure('261015-140601', 'console', scene='long_desc_argsense'),
    Figure('261015-140603', 'console', scene='long_desc_argparse'),
    Figure('261015-140605', 'console', scene='long_desc_click'),
    Figure('261015-140607', 'console', scene='long_desc_typer'),
    Figure('261015-140609', 'console', scene='long_desc_cyclopts'),
    Figure(
        '261015-132007', 'script', script='test/command_group.py', argv='-h'
    ),
    Figure('261015-140455', 'console', scene='param_types'),
    Figure('261015-140459', 'console', scene='varargs_compare'),
    # -- quick start ------------------------------------------------------------
    Figure('261015-140457', 'console', scene='quick_start'),
    # -- in-depth reading -------------------------------------------------------
    # an ide screenshot; it is taken by hand, not by this tool.
    Figure('241219-101538', 'manual'),
    Figure('261015-140529', 'console', scene='docstring_wrap'),
    Figure('261015-140531', 'console', scene='docstring_fields'),
    Figure('261015-140532', 'console', scene='supported_types'),
    Figure('261015-140534', 'console', scene='varargs_indepth'),
    # -- the tui chapter --------------------------------------------------------
    Figure('tui-widgets', 'tui', scene='widgets'),
    Figure('tui-compact-layout', 'tui', scene='compact'),
    Figure('tui-log', 'tui', scene='log'),
]


def main(names: str = '') -> None:
    """
    Refresh the README screenshots.

    params:
        names: A comma separated list of the figure names to refresh. When it
            is empty, every figure is refreshed.
    """
    wanted = [x.strip() for x in names.split(',') if x.strip()]
    unknown = [x for x in wanted if x not in {f.name for f in FIGURES}]
    if unknown:
        raise ValueError('unknown figure(s): {}'.format(', '.join(unknown)))

    figures = [f for f in FIGURES if not wanted or f.name in wanted]
    dst = ROOT / 'docs' / 'images'

    for figure in figures:
        if figure.kind == 'manual':
            print('skip {} (it is taken by hand)'.format(figure.name))
            continue

        png = dst / '{}.png'.format(figure.name)
        staging = Path(tempfile.mkdtemp(prefix='argsense-shot-'))
        svg = staging / '{}.svg'.format(figure.name)
        try:
            if figure.kind == 'tui':
                _record_tui(figure, svg)
            else:
                _record_console(figure, svg)
            shot._svg_to_png(svg, png)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        print('wrote {}'.format(png.relative_to(ROOT)))


# ------------------------------------------------------------------------------
# console


def _record_console(figure: Figure, svg: Path) -> None:
    # argparse / click / typer / cyclopts wrap their help text to the terminal
    # width; pin it, so that the recorded image is stable.
    os.environ.setdefault('COLUMNS', '80')

    console = Console(
        width=shot.WIDTH,
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

    # a fresh interface per figure: a scenario script registers its commands
    # into the module level `cli` singleton, and we don't want one script's
    # commands to leak into the next figure - nor the `main` function of this
    # tool to appear in the recorded help interface.
    origin_cli = argsense.cli
    argsense.cli = CommandLineInterface()

    origin_argv = sys.argv
    origin_stdout = sys.stdout
    origin_stderr = sys.stderr
    # `_ConsoleStream` forwards whatever a scene writes to `sys.stdout` (plain
    # `print()`, neoprint, click, ...) into the recording console.
    sys.stdout = shot._ConsoleStream(console)
    sys.stderr = sys.stdout
    try:
        if figure.kind == 'script':
            target = ROOT / figure.script
            sys.argv = [str(target), *figure.argv.split()]
            runpy.run_path(str(target), run_name='__main__')
        else:
            CONSOLE_SCENES[figure.scene]()
    except SystemExit:
        # `-h` handlers (argparse, click, typer, ...) exit the process; that is
        # the expected way for them to end, so it must not abort the recording.
        pass
    finally:
        sys.stdout.flush()
        sys.argv = origin_argv
        sys.stdout = origin_stdout
        sys.stderr = origin_stderr
        argsense.cli = origin_cli
        R.console = shot._ORIGIN_CONSOLE

    console.save_svg(str(svg), title=figure.title)
    shot._use_local_font(svg)


# ------------------------------------------------------------------------------
# tui


def _record_tui(figure: Figure, svg: Path) -> None:
    scene = TUI_SCENES[figure.scene]

    interface = CommandLineInterface()
    for func in scene.commands:
        interface.add_cmd(func)
    interface.resolve_doc_references()
    func_infos = [interface.commands[id(x)] for x in scene.commands]

    # a scene names its functions the python way; the form knows them by their
    # command name (the converted, dashed one).
    initials = {
        interface.commands[id(x)].name: scene.initials[getattr(x, '__name__')]
        for x in scene.commands
        if getattr(x, '__name__') in scene.initials
    }

    from argsense.renderer.tui import ArgsenseTuiApp

    app = ArgsenseTuiApp(func_infos, initials=initials, groups=scene.groups)
    app.animation_level = 'none'

    async def run() -> str:
        async with app.run_test(size=scene.size) as pilot:
            await pilot.pause()
            if scene.prepare is not None:
                await scene.prepare(app, pilot)
                await pilot.pause()
            return app.export_screenshot()

    svg.write_text(asyncio.run(run()), encoding='utf-8')
    _use_local_font_tui(svg)


def _use_local_font_tui(svg: Path) -> None:
    """
    Point the exported svg at a locally installed font, the same way the
    console images do - textual also references a font by name, and falls back
    to whatever the browser picks when it is missing.
    """
    text = svg.read_text(encoding='utf-8')
    svg.write_text(
        re.sub(r'font-family: [^;]+;', _FONT_DECL, text), encoding='utf-8'
    )


_FONT_DECL = "font-family: '{}', monospace;".format(shot.FONT)


if __name__ == '__main__':
    cli.run(main)
