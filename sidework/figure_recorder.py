"""
The engine behind the screenshot tooling.

It records the kinds of figures the documents use:

- a console figure: either a *scene* (a callable that draws on the recording
  console) or a *scenario script* run with a help request. The scene owns the
  printing, so it can play a shell session, render a help interface, or draw
  whatever else the document needs.
- a tui figure: a textual form driven headlessly with `Pilot`.

A figure is written as an svg first and then rasterized to a png with a
headless Chrome / Edge. The svg is only an intermediate - the scene
definitions and the rasterizer live in this package too (see
`screenshot_console_output.py`).

The callers keep their own figure lists:
`sidework/readme_screenshots.py` for the README, and
`docs/advertisement/build-images.py` for the advertisement materials.
"""

from __future__ import annotations

import asyncio
import os
import re
import runpy
import sys
import typing as t
from pathlib import Path

import argsense
from rich.console import Console

import argsense.renderer.rich.render as R
from argsense.cli import CommandLineInterface

from sidework import screenshot_console_output as shot

WIDTH = 120
#   the default recording width, which the README screenshots use. A wider
#   console keeps the parameters panel from stacking its rows.

FONT_DECL = "font-family: '{}', monospace;".format(shot.FONT)
#   replaces whatever font the svg asks for, so that the rasterized image uses
#   the locally installed monospace font instead of a CDN one.


def rasterize(svg: Path, png: Path) -> None:
    """Turn the recorded svg into the png that the documents embed."""
    shot._svg_to_png(svg, png)


def record_script(
    script: Path, argv: str, svg: Path, width: int = WIDTH
) -> None:
    """
    Record a scenario script that is run with a help request, e.g.
    `test/depsland_mock.py runx -h`.

    params:
        argv: the extra words to append after the script path.
    """

    def scene() -> None:
        origin_argv = sys.argv
        sys.argv = [str(script), *argv.split()]
        try:
            runpy.run_path(str(script), run_name='__main__')
        except SystemExit:
            # `-h` handlers (argparse, click, typer, ...) exit the process;
            # that is the expected way for them to end, so it must not abort
            # the recording.
            pass
        finally:
            sys.argv = origin_argv

    record_console(scene, svg, width=width)


def record_console(
    scene: t.Callable[[], None],
    svg: Path,
    width: int = WIDTH,
    title: str = 'argsense',
) -> None:
    """Record a console scene (see the module docstring)."""
    # argparse / click / typer / cyclopts wrap their help text to the terminal
    # width; pin it, so that the recorded image is stable.
    os.environ.setdefault('COLUMNS', '80')

    console = Console(
        width=width,
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

    # a fresh interface per figure: a scenario script (or a scene) registers
    # its commands into the module level `cli` singleton, and we don't want
    # one figure's commands to leak into the next one - nor the `main`
    # function of the caller to appear in the recorded help interface.
    origin_cli = argsense.cli
    argsense.cli = CommandLineInterface()

    origin_stdout = sys.stdout
    origin_stderr = sys.stderr
    # rich only records what is rendered through a `Console`, so whatever a
    # scene writes to `sys.stdout` (plain `print()`, neoprint, click, ...) has
    # to be redirected into the console to show up in the image.
    sys.stdout = shot._ConsoleStream(console)
    sys.stderr = sys.stdout
    try:
        scene()
    except SystemExit:
        pass
    finally:
        sys.stdout.flush()
        sys.stdout = origin_stdout
        sys.stderr = origin_stderr
        argsense.cli = origin_cli
        R.console = shot._ORIGIN_CONSOLE

    console.save_svg(str(svg), title=title)
    shot._use_local_font(svg)


def record_tui(
    commands: t.Sequence[t.Callable],
    svg: Path,
    groups: t.Optional[t.List[t.Tuple[str, t.List[str]]]] = None,
    initials: t.Optional[t.Dict[str, t.Dict[str, t.Any]]] = None,
    size: t.Tuple[int, int] = (110, 40),
    prepare: t.Optional[t.Callable[..., t.Any]] = None,
) -> None:
    """
    Record a textual form.

    params:
        commands: the functions to list in the form.
        groups: the group structure (as `cli.run_group(...)` builds it). When
            it is given, the groups are shown in a sidebar instead of the tab
            bar.
        initials: the form values to prefill, keyed by the *python* name of a
            command (the form knows it by its converted, dashed command name).
        prepare: an optional `async def prepare(app, pilot)` that fills the
            form (or presses a button) before the screenshot is taken.
    """
    interface = CommandLineInterface()
    for func in commands:
        interface.add_cmd(func)
    interface.resolve_doc_references()
    func_infos = [interface.commands[id(x)] for x in commands]

    form_initials = {
        interface.commands[id(x)].name: initials[getattr(x, '__name__')]
        for x in commands
        if initials and getattr(x, '__name__') in initials
    }

    from argsense.renderer.tui import ArgsenseTuiApp

    app = ArgsenseTuiApp(func_infos, initials=form_initials, groups=groups)
    app.animation_level = 'none'

    async def run() -> str:
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            if prepare is not None:
                await prepare(app, pilot)
                await pilot.pause()
            return app.export_screenshot()

    svg.write_text(asyncio.run(run()), encoding='utf-8')
    # textual references its font by name too, and falls back to whatever the
    # browser picks when it is missing.
    text = svg.read_text(encoding='utf-8')
    svg.write_text(re.sub(r'font-family: [^;]+;', FONT_DECL, text), 'utf-8')
