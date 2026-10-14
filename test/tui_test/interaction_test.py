"""
Headless interaction test for the argsense TUI.

It drives the form without a real terminal, using textual's `Pilot`.

Usage (run from the project root):
    python test/tui_test/interaction_test.py
"""

import asyncio
import typing as t
from pathlib import Path

from argsense.cli import CommandLineInterface
from argsense.renderer.tui import ArgsenseTuiApp
from argsense.tui import TuiInterface
from textual.widgets import Button
from textual.widgets import Input
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


def status_of(app: ArgsenseTuiApp) -> str:
    return str(app.query_one('#status', Static).content)


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
        check('status reports success', 'done' in status_of(app), True)

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
        message = status_of(app)
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
            'not compatible' in status_of(app).lower(),
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

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    asyncio.run(main())
