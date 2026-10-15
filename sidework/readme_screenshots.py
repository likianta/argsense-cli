"""
Regenerate every screenshot that the README shows.

The scene definitions live in `sidework/readme_scenes.py`, and the recording
engine in `sidework/figure_recorder.py`. There are three kinds of figures:

- `script`: run a scenario script with a help request and record its help
  interface, e.g. `test/depsland_mock.py -h`.
- `console`: run a console scene: a simulated shell session, or a bare help
  interface. The scene owns the printing (see `readme_scenes.py`).
- `tui`: drive a textual form headlessly with `Pilot`, then take a screenshot.

Every figure is written to `docs/images/<name>.png`, using a stable name, so
refreshing never leaves an orphan image behind.

Usage (run from the project root):
    python sidework/readme_screenshots.py               # refresh everything
    python sidework/readme_screenshots.py tui-overview  # refresh one figure
    python sidework/readme_screenshots.py a,b,c         # refresh several
"""

from __future__ import annotations

import shutil
import tempfile
import typing as t
from dataclasses import dataclass
from pathlib import Path

from argsense import cli
from sidework import figure_recorder as fr
from sidework.readme_scenes import CONSOLE_SCENES
from sidework.readme_scenes import TUI_SCENES

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
            _record(figure, svg)
            fr.rasterize(svg, png)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        print('wrote {}'.format(png.relative_to(ROOT)))


def _record(figure: Figure, svg: Path) -> None:
    if figure.kind == 'script':
        fr.record_script(ROOT / figure.script, figure.argv, svg)
    elif figure.kind == 'console':
        fr.record_console(CONSOLE_SCENES[figure.scene], svg)
    else:
        assert figure.kind == 'tui'
        scene = TUI_SCENES[figure.scene]
        fr.record_tui(
            scene.commands,
            svg,
            groups=scene.groups,
            initials=scene.initials,
            size=scene.size,
            prepare=scene.prepare,
        )


if __name__ == '__main__':
    cli.run(main)
