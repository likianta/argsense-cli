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
from argsense.parser import Argv
from argsense.parser import FuncInfo
from argsense.renderer.tui import ArgsenseTuiApp
from argsense.renderer.tui import CliRunRequest
from argsense.renderer.tui import collect_initial_values
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


def main(name: str, age: int):
    """
    General types demo.

    params:
        name: Your name.
        age: Your age.
    """
    print(name, age)


def func_info_of(func) -> t.Any:
    cli = CommandLineInterface()
    cli.add_cmd(func)
    cli.resolve_doc_references()
    return cli.commands[id(func)]


def build_app(inline: bool = False) -> ArgsenseTuiApp:
    return ArgsenseTuiApp(func_info_of(install), inline=inline)


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
            'exit uses the error (danger) style',
            app.query_one('#exit', Button).variant,
            'error',
        )
        check(
            'the log panel exists',
            isinstance(app.query_one('#log'), RichLog),
            True,
        )
        run = app.query_one('#run', Button)
        run_exit = app.query_one('#run-exit', Button)
        exit_ = app.query_one('#exit', Button)
        check(
            'run < run-and-exit < exit',
            run.region.x < run_exit.region.x < exit_.region.x,
            True,
        )
        check(
            'one character gap: run -> run-and-exit',
            run_exit.region.x - (run.region.x + run.size.width),
            1,
        )
        check(
            'one character gap: run-and-exit -> exit',
            exit_.region.x - (run_exit.region.x + run_exit.size.width),
            1,
        )
        check(
            'exit wraps its content (narrower than run)',
            exit_.size.width < run.size.width,
            True,
        )


async def test_button_layout() -> None:
    print('[2] the run buttons split the space, exit wraps')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        run = app.query_one('#run', Button)
        run_exit = app.query_one('#run-exit', Button)
        exit_ = app.query_one('#exit', Button)
        actions = app.query_one('#actions')
        check(
            'run and run-and-exit are equal',
            run.size.width,
            run_exit.size.width,
        )
        check(
            'the row is exactly: run + gap + run-exit + gap + exit',
            run.size.width * 2 + exit_.size.width + 2,
            actions.size.width,
        )


async def test_log_height() -> None:
    print('[3] the log panel height')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        log = app.query_one('#log')
        check(
            'non-inline: stretches to the bottom of the window',
            log.region.bottom,
            app.screen.region.height,
        )

    app = build_app(inline=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        log = app.query_one('#log')
        # 5 lines of content + 2 border rows.
        check('inline: fixed to 5 inner lines', log.region.height, 7)


async def test_run() -> None:
    print('[4] fill the form and press Run')
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
    print('[5] toggle the switch, then press Run and exit')
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
        check('the function is NOT run inside the tui', len(CALLS), 0)
    check('the app exited', app.is_running, False)
    request = app.return_value
    check('a cli run was requested', isinstance(request, CliRunRequest), True)
    assert isinstance(request, CliRunRequest)
    check(
        'the tokens mirror the form',
        request.tokens,
        ('--appid', 'Bob', '--no-use-exist', '--count', '1'),
    )


async def test_exit_button() -> None:
    print('[6] press Exit -> quits without running')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click('#param-appid')
        await pilot.press(*'Alice')
        await pilot.pause()
        await pilot.click('#exit')
        await pilot.pause()
        check('the function was not called', len(CALLS), 0)
    check('the app exited', app.is_running, False)
    check('exit returns nothing', app.return_value, None)


async def test_errors() -> None:
    print('[7] error reporting')
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
    print('[8] narrow terminal')
    app = build_app()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.resize_terminal(46, 20)
        await pilot.pause()
        run = app.query_one('#run', Button)
        run_exit = app.query_one('#run-exit', Button)
        exit_ = app.query_one('#exit', Button)
        check('buttons survive a narrow terminal', run.size.width > 0, True)
        check('run buttons stay equal', run.size.width, run_exit.size.width)
        check(
            'the gaps survive',
            run_exit.region.x - (run.region.x + run.size.width),
            1,
        )
        check('exit stays wrapped', exit_.size.width < run.size.width, True)


def test_argv_prefill() -> None:
    print('[9] the command line prefills the form')
    func_info = func_info_of(main)
    argv = Argv(('python',), ('main.py',), ('Alice', '22'))
    initial = collect_initial_values(func_info, argv)
    check(
        'values are mapped onto the params',
        initial,
        {'name': 'Alice', 'age': '22'},
    )

    # a command line that cannot be parsed simply yields nothing.
    bad = collect_initial_values(
        func_info, Argv(('python',), ('main.py',), ('--nope',))
    )
    check('unparsable argv -> no prefill', bad, {})


async def test_argv_prefill_in_form() -> None:
    print('[10] the prefilled values show up in the widgets')
    func_info = func_info_of(main)
    initial = collect_initial_values(
        func_info, Argv(('python',), ('main.py',), ('Alice', '22'))
    )
    app = ArgsenseTuiApp(func_info, initial=initial)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        check(
            'name input is prefilled',
            app.query_one('#param-name', Input).value,
            'Alice',
        )
        check(
            'age input is prefilled',
            app.query_one('#param-age', Input).value,
            '22',
        )


def test_multi_command_is_rejected() -> None:
    print('[11] multi-command is rejected before the app starts')

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
    print('[12] tui.run(...) resolves the entrance and opens the form')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original = renderer.run_form

    def fake_run_form(
        func_info: FuncInfo,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
    ) -> t.Any:
        captured['name'] = func_info.name
        captured['inline'] = inline
        captured['argv'] = argv
        captured['has_runner'] = callable(cli_runner)
        return 'stub-result'

    renderer.run_form = fake_run_form  # type: ignore
    original_argv = sys.argv
    try:
        sys.argv = ['prog', 'Alice', '22']
        result = TuiInterface().run(install, inline=True)
    finally:
        renderer.run_form = original
        sys.argv = original_argv

    check('delegates to the form renderer', captured.get('name'), 'install')
    check('passes the inline flag', captured.get('inline'), True)
    check(
        'passes the command line for prefill',
        captured['argv'].args,
        ('Alice', '22'),
    )
    check('passes a cli runner', captured.get('has_runner'), True)
    check('returns the form result', result, 'stub-result')


def test_run_and_exit_goes_through_cli() -> None:
    print('[13] "Run and exit" is dispatched to the cli path')
    import argsense.renderer.tui as renderer

    original = renderer.run_form

    def fake_run_form(
        func_info: FuncInfo,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
    ) -> t.Any:
        # pretend the user filled the form and pressed "Run and exit".
        assert cli_runner is not None
        return cli_runner(('Zoe',))

    renderer.run_form = fake_run_form  # type: ignore
    original_argv = sys.argv
    CALLS.clear()
    try:
        sys.argv = ['prog']
        with redirect_stdout(io.StringIO()):
            CommandLineInterface().run(install, mode='tui')
    finally:
        renderer.run_form = original
        sys.argv = original_argv

    check('the cli path executed the function', CALLS[0], ('Zoe', '', True, 1))


def test_mode_tokens() -> None:
    print('[14] the mode tokens on the command line')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original_form = renderer.run_form

    def fake_run_form(
        func_info: FuncInfo,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
    ) -> t.Any:
        captured['name'] = func_info.name
        captured['inline'] = inline
        captured['argv'] = argv
        captured['has_runner'] = callable(cli_runner)
        return 'stub-result'

    renderer.run_form = fake_run_form  # type: ignore
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
        sys.argv = ['prog', 'Zoe', '22']
        CommandLineInterface().run(install, mode='tui')
        check(
            'the tui receives the positional args for prefill',
            captured['argv'].args,
            ('Zoe', '22'),
        )

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


async def run_all() -> None:
    await test_structure()
    await test_button_layout()
    await test_log_height()
    await test_run()
    await test_flag_and_run_exit()
    await test_exit_button()
    await test_errors()
    await test_narrow_terminal()
    test_argv_prefill()
    await test_argv_prefill_in_form()
    test_multi_command_is_rejected()
    test_run_delegates_to_the_form()
    test_run_and_exit_goes_through_cli()
    test_mode_tokens()

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    asyncio.run(run_all())
