"""
Headless interaction test for the argsense TUI.

It drives the form without a real terminal, using textual's `Pilot`.

Usage (run from the project root):
    python test/tui_test/interaction_test.py
"""

import asyncio
import io
import sys
import typing as t
from contextlib import redirect_stdout
from pathlib import Path

from argsense.cli import CommandLineInterface
from argsense.renderer.tui import ArgsenseTuiApp
from argsense.tui import TuiInterface
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import RichLog
from textual.widgets import Static
from textual.widgets import Switch

CALLS: t.List[t.Tuple] = []
FAILURES: t.List[str] = []


def install(
    appid: str, version: str = '', use_exist: bool = True, count: int = 1
):
    """
    install an app.

    params:
        appid: the app id.
        version: the version to install.
        use_exist: reuse the already installed copy.
        count: how many times to retry.
    """
    print('installing {} {}'.format(appid, version or '(latest)'))
    CALLS.append((appid, version, use_exist, count))
    return 'ok:{}'.format(appid)


def build_app() -> ArgsenseTuiApp:
    cli = CommandLineInterface()
    cli.add_cmd(install)
    cli.resolve_doc_references()
    return ArgsenseTuiApp(cli.commands[id(install)])


def check(label: str, actual: t.Any, expected: t.Any) -> None:
    if actual == expected:
        print('   PASS  {:<44} {}'.format(label, actual))
    else:
        FAILURES.append(label)
        print('   FAIL  {:<44} {} != {}'.format(label, actual, expected))


def log_of(app: ArgsenseTuiApp) -> str:
    lines = app.query_one('#log', RichLog).lines
    return '\n'.join(strip.text for strip in lines)


# -----------------------------------------------------------------------------


async def test_structure() -> None:
    print('[1] form structure')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        check('inputs for non-flag params', len(app.query(Input)), 3)
        check('switch for the flag param', len(app.query(Switch)), 1)
        check(
            'desc is rendered', app.query_one('#desc', Static) is not None, True
        )
        check(
            'default value is prefilled',
            app.query_one('#param-count', Input).value,
            '1',
        )
        check(
            'no default -> left empty',
            app.query_one('#param-version', Input).value,
            '',
        )
        check(
            'description becomes the placeholder',
            app.query_one('#param-appid', Input).placeholder,
            'the app id.',
        )
        check(
            'run is the primary button',
            app.query_one('#run', Button).variant,
            'primary',
        )
        check(
            'run-and-exit uses the default style',
            app.query_one('#run-exit', Button).variant,
            'default',
        )
        check(
            'the log panel exists',
            isinstance(app.query_one('#log'), RichLog),
            True,
        )
        check(
            'Run sits on the left of Run and exit',
            app.query_one('#run', Button).region.x
            < app.query_one('#run-exit', Button).region.x,
            True,
        )
        check(
            'the two buttons resolve to different colours',
            app.query_one('#run', Button).styles.color
            != app.query_one('#run-exit', Button).styles.color,
            True,
        )


async def test_equal_button_width() -> None:
    print('[2] the two buttons split the horizontal space')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        run_width = app.query_one('#run', Button).size.width
        exit_width = app.query_one('#run-exit', Button).size.width
        check('equal widths', run_width, exit_width)
        check(
            'each takes exactly half of the action row',
            run_width * 2,
            app.query_one('#actions').size.width,
        )


async def test_run() -> None:
    print('[3] fill the form and press Run')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click('#param-appid')
        await pilot.press(*'Alice')
        await pilot.pause()
        check(
            'the typed value lands in the input',
            app.query_one('#param-appid', Input).value,
            'Alice',
        )

        await pilot.click('#run')
        await pilot.pause()
        check('the function was called once', len(CALLS), 1)
        check('args/kwargs are resolved', CALLS[0], ('Alice', '', True, 1))
        check('Run keeps the app open', app.is_running, True)

        content = log_of(app)
        check('captures the print output', 'installing Alice' in content, True)
        check('appends the done marker', 'done' in content, True)
        check(
            'the log panel sits below the buttons',
            app.query_one('#log').region.y > app.query_one('#run').region.y,
            True,
        )

        # let the button's "active" tint settle, and force a repaint, so that
        # the exported screenshot shows the settled state.
        await asyncio.sleep(0.4)
        app.screen.refresh(repaint=True, layout=True)
        await pilot.pause()
        svg = app.export_screenshot()
        path = Path('test/temp/tui_form.svg')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding='utf-8')
        print('   ....  screenshot exported -> {}'.format(path))


async def test_flag_and_run_exit() -> None:
    print('[4] toggle the switch, then press Run and exit')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click('#param-appid')
        await pilot.press(*'Bob')
        await pilot.click('#param-use_exist')
        await pilot.pause()
        check(
            'the switch was toggled off',
            app.query_one('#param-use_exist', Switch).value,
            False,
        )

        await pilot.click('#run-exit')
        await pilot.pause()
        check('the function was called once', len(CALLS), 1)
        check(
            'False is passed through as --no-use-exist',
            CALLS[0],
            ('Bob', '', False, 1),
        )
    check('the app exited', app.return_value, 'ok:Bob')


async def test_errors() -> None:
    print('[5] error reporting')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click('#run')
        await pilot.pause()
        check('missing required arg -> not called', len(CALLS), 0)
        message = log_of(app)
        check(
            'reports the missing argument',
            'insufficient' in message.lower(),
            True,
        )
        check('no raw markup leaks through', '[' not in message, True)

        await pilot.click('#param-appid')
        await pilot.press(*'Alice')

        count_input = app.query_one('#param-count', Input)
        count_input.value = ''
        await pilot.pause()
        await pilot.click('#param-count')
        await pilot.press(*'abc')
        await pilot.click('#run')
        await pilot.pause()
        check('bad number -> not called', len(CALLS), 0)
        check(
            'reports an incompatible type',
            'not compatible' in log_of(app).lower(),
            True,
        )

        # NOTE: a click on a button is ignored while its "active" animation is
        # still running (textual's `Button.active_effect_duration`, 0.25s).
        await asyncio.sleep(0.4)
        count_input.value = '2'
        await pilot.pause()
        await pilot.click('#run')
        await pilot.pause()
        check('calls after the form is fixed', len(CALLS), 1)
        check('the number is parsed as int', CALLS[0][3], 2)


async def test_narrow_terminal() -> None:
    print('[6] narrow terminal')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.resize_terminal(46, 20)
        await pilot.pause()
        width = app.query_one('#run', Button).size.width
        check('buttons survive a narrow terminal', width > 0, True)
        check(
            'buttons stay equal',
            width,
            app.query_one('#run-exit', Button).size.width,
        )
        check(
            'buttons re-split for the new width',
            width * 2,
            app.query_one('#actions').size.width,
        )


def test_multi_command_is_rejected() -> None:
    print('[7] multi-command is rejected before the app starts')

    def f1() -> None: ...

    def f2() -> None: ...

    interface = TuiInterface()
    try:
        interface.run((f1, f2))
    except RuntimeError as exc:
        check('raises RuntimeError', 'exactly one command' in str(exc), True)
    else:
        check('raises RuntimeError', 'nothing raised', 'RuntimeError')


def test_run_delegates_to_the_form() -> None:
    print('[8] tui.run(...) resolves the entrance and opens the form')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original = renderer.run_form

    def fake_run_form(func_info, inline: bool = False):
        captured['name'] = func_info.name
        captured['inline'] = inline
        return 'stub-result'

    renderer.run_form = fake_run_form
    try:
        result = TuiInterface().run(install, inline=True)
    finally:
        renderer.run_form = original

    check(
        'delegates to the form renderer',
        captured,
        {'name': 'install', 'inline': True},
    )
    check('returns the form result', result, 'stub-result')


def test_mode_tokens() -> None:
    print('[9] the mode tokens on the command line')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original_form = renderer.run_form

    def fake_run_form(func_info, inline: bool = False):
        captured['name'] = func_info.name
        captured['inline'] = inline
        return 'stub-result'

    renderer.run_form = fake_run_form
    original_argv = sys.argv
    try:
        sys.argv = ['prog', ':tui']
        CommandLineInterface().run(install, mode='cli')
        check(':tui overrides mode="cli"', captured.get('inline'), False)

        captured.clear()
        sys.argv = ['prog', ':itui']
        CommandLineInterface().run(install, mode='cli')
        check(':itui means an inline tui', captured.get('inline'), True)

        captured.clear()
        CALLS.clear()
        sys.argv = ['prog', ':cli', 'Zoe']
        with redirect_stdout(io.StringIO()):
            CommandLineInterface().run(install, mode='tui')
        check(':cli overrides mode="tui"', captured, {})
        check('  ... and the cli path ran', CALLS[0], ('Zoe', '', True, 1))

        try:
            sys.argv = ['prog']
            CommandLineInterface().run(install, mode='gui')
        except NotImplementedError as exc:
            check(
                'mode="gui" raises NotImplementedError', 'gui' in str(exc), True
            )
        else:
            check(
                'mode="gui" raises NotImplementedError',
                'nothing raised',
                'NotImplementedError',
            )
    finally:
        renderer.run_form = original_form
        sys.argv = original_argv


# -----------------------------------------------------------------------------


async def main() -> None:
    await test_structure()
    await test_equal_button_width()
    await test_run()
    await test_flag_and_run_exit()
    await test_errors()
    await test_narrow_terminal()
    test_multi_command_is_rejected()
    test_run_delegates_to_the_form()
    test_mode_tokens()

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    asyncio.run(main())
