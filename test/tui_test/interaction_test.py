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
from argsense.renderer.tui import collect_rows
from argsense.renderer.tui import plan_layout
from argsense.renderer.tui import resolve_initials
from argsense.renderer.tui import TripleSwitch
from argsense.tui import TuiInterface
from textual.containers import VerticalScroll
from textual.content import Content
from textual.widgets import Button
from textual.widgets import ContentSwitcher
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import RichLog
from textual.widgets import Static
from textual.widgets import Switch
from textual.widgets import Tab
from textual.widgets import Tabs

SIZE = (100, 40)
#   a terminal big enough to show a small form without scrolling.

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


def uninstall(appid: str, version: t.Optional[str] = None) -> None:
    """
    uninstall an app.

    params:
        appid: the app id.
        version: the version to uninstall.
    """
    print('uninstalling {} {}'.format(appid, version or '(latest)'))
    CALLS.append(('uninstall', appid, version))


def main(name: str, age: int):
    """
    General types demo.

    params:
        name: Your name.
        age: Your age.
    """
    print(name, age)


def bare(alpha: str) -> None:
    """
    a command whose parameter has no description.
    """


def many_params(
    project_name: str,
    version: str = '0.1.0',
    author: str = '',
    email: str = '',
    description: str = '',
    license: str = 'MIT',
    homepage: str = '',
    keywords: str = '',
    package_dir: str = '.',
    output_dir: str = 'dist',
    jobs: int = 4,
    timeout: int = 60,
    retries: int = 2,
    build_wheel: bool = True,
    build_sdist: bool = True,
    verbose: bool = False,
) -> None:
    """
    a command with a lot of parameters.

    params:
        project_name: The project name.
        version: The project version.
    """
    print('configure {} v{}'.format(project_name, version))


def mixed(a: str, b: bool, c: bool, d: str, e: bool) -> None:
    """
    only neighbours may share a row.

    params:
        a: some text.
        b: a flag.
        c: another flag.
        d: some text.
        e: a third flag.
    """


def numbers(name: str, count: int = 1, rate: float = 1.0, limit: int = 5):
    """
    numbers do not need a whole row.

    params:
        name: the name.
        count: how many.
        rate: how fast.
        limit: how far.
    """


def preview(
    port: int, show: t.Optional[bool] = None, live: bool = False
) -> None:
    """
    a `bool | None` parameter gets a triple switch.

    params:
        port: the port to watch.
        show: draw a preview.
        live: keep watching.
    """
    print(locals())
    CALLS.append((port, show, live))


# `bool | None` asks for python 3.10, but argsense has to know the spelling.
def cache(url: str, reload: bool | None = True) -> None:  # type: ignore
    """
    the PEP 604 spelling of the same thing.

    params:
        url: where to fetch.
        reload: use the cached copy.
    """
    print(locals())
    CALLS.append((url, reload))


def func_info_of(func) -> FuncInfo:
    cli = CommandLineInterface()
    cli.add_cmd(func)
    cli.resolve_doc_references()
    return cli.commands[id(func)]


def build_app(
    func=install, inline: bool = False, extra: t.Sequence = ()
) -> ArgsenseTuiApp:
    func_infos = [func_info_of(func), *(func_info_of(x) for x in extra)]
    return ArgsenseTuiApp(func_infos, inline=inline)


def check(label: str, actual: t.Any, expected: t.Any) -> None:
    if actual == expected:
        print('   PASS  {:<44} {}'.format(label, actual))
    else:
        FAILURES.append(label)
        print('   FAIL  {:<44} {} != {}'.format(label, actual, expected))


def log_of(app: ArgsenseTuiApp) -> str:
    lines = app.query_one('#log', RichLog).lines
    return '\n'.join(strip.text for strip in lines)


def rendered_label(app: ArgsenseTuiApp, command: str, param: str) -> Content:
    """The painted content of a parameter's name label."""
    label = app.query_one('#label-{}-{}'.format(command, param), Label)
    return t.cast('Content', label.render())


# -----------------------------------------------------------------------------


async def test_structure() -> None:
    print('[1] form structure')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check('inputs for non-flag params', len(app.query(Input)), 3)
        check('switch for the flag param', len(app.query(Switch)), 1)
        check(
            'desc is rendered', app.query_one('.desc', Static) is not None, True
        )
        check(
            'default value is prefilled',
            app.query_one('#param-install-count', Input).value,
            '1',
        )
        check(
            'an empty-string default prefills :empty',
            app.query_one('#param-install-version', Input).value,
            ':empty',
        )
        check(
            'description becomes the placeholder',
            app.query_one('#param-install-appid', Input).placeholder,
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
        check('a single command shows no tabs', len(app.query(Tab)), 0)
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


async def test_layout_order() -> None:
    print('[2] the window is: params / buttons / log')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        params = app.query_one('#params', VerticalScroll)
        actions = app.query_one('#actions')
        log = app.query_one('#log', RichLog)
        check(
            'params is a scroll view', isinstance(params, VerticalScroll), True
        )
        check(
            'params sits above the buttons',
            params.region.bottom <= actions.region.y,
            True,
        )
        check(
            'the buttons sit above the log',
            actions.region.bottom <= log.region.y,
            True,
        )


async def test_button_layout() -> None:
    print('[3] the run buttons split the space, exit wraps')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
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
    print('[4] the log panel height')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        log = app.query_one('#log')
        check(
            'non-inline: reaches the bottom of the window',
            log.region.bottom,
            app.screen.region.height,
        )
        check(
            'non-inline: 40% of the window (2 rows less than it used to be)',
            log.region.height,
            15,
        )

    app = build_app(inline=True)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        log = app.query_one('#log')
        # 5 lines of content + 2 border rows.
        check('inline: fixed to 5 inner lines', log.region.height, 7)


async def test_run() -> None:
    print('[5] fill the form and press Run')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press(*'Alice')
        await pilot.pause()
        check(
            'the typed value lands in the input',
            app.query_one('#param-install-appid', Input).value,
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
    print('[6] toggle the switch, then press Run and exit')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press(*'Bob')
        await pilot.click('#param-install-use_exist')
        await pilot.pause()
        check(
            'the switch was toggled off',
            app.query_one('#param-install-use_exist', Switch).value,
            False,
        )

        await pilot.click('#run-exit')
        await pilot.pause()
        check('the function is NOT run inside the tui', len(CALLS), 0)
    check('the app exited', app.is_running, False)
    request = app.return_value
    check('a cli run was requested', isinstance(request, CliRunRequest), True)
    assert isinstance(request, CliRunRequest)
    check('the request names the command', request.command, 'install')
    check(
        'the tokens mirror the form',
        request.tokens,
        (
            '--appid',
            'Bob',
            '--version',
            ':empty',
            '--no-use-exist',
            '--count',
            '1',
        ),
    )


async def test_exit_button() -> None:
    print('[7] press Exit -> quits without running')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press(*'Alice')
        await pilot.pause()
        await pilot.click('#exit')
        await pilot.pause()
        check('the function was not called', len(CALLS), 0)
    check('the app exited', app.is_running, False)
    check('exit returns nothing', app.return_value, None)


async def test_errors() -> None:
    print('[8] error reporting')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
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

        await pilot.click('#param-install-appid')
        await pilot.press(*'Alice')

        count_input = app.query_one('#param-install-count', Input)
        count_input.value = ''
        await pilot.pause()
        await pilot.click('#param-install-count')
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
    print('[9] narrow terminal')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
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


async def test_multi_command_tabs() -> None:
    print('[10] several commands are switched by tabs')
    CALLS.clear()
    app = build_app(extra=(uninstall,))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        tabs = app.query_one('#tabs', Tabs)
        check('one tab per command', len(app.query(Tab)), 2)
        check('the tabs are shown', tabs.size.height > 0, True)
        check('the first command is active', app.active, 'install')
        check(
            'its pane is the visible one',
            app.query_one('#panes', ContentSwitcher).current,
            'pane-install',
        )
        check('both commands are mounted', len(app.query(Input)), 3 + 2)

        # switch to the second command.
        tabs.active = 'tab-uninstall'
        await pilot.pause()
        check('the active command follows the tab', app.active, 'uninstall')
        check(
            'the switcher follows the tab',
            app.query_one('#panes', ContentSwitcher).current,
            'pane-uninstall',
        )
        check(
            'the old pane is hidden',
            app.query_one('#pane-install').styles.display,
            'none',
        )
        check(
            'the new pane is shown',
            app.query_one('#pane-uninstall').styles.display,
            'block',
        )

        # run the second command.
        await pilot.click('#param-uninstall-appid')
        await pilot.press(*'Zoe')
        await pilot.click('#run')
        await pilot.pause()
        check('the second command ran', CALLS[0], ('uninstall', 'Zoe', None))
        check(
            'its output goes to the shared log',
            'uninstalling Zoe' in log_of(app),
            True,
        )


async def test_multi_command_run_and_exit() -> None:
    print('[11] "Run and exit" carries the active command')
    app = build_app(extra=(uninstall,))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        app.query_one('#tabs', Tabs).active = 'tab-uninstall'
        await pilot.pause()
        await pilot.click('#param-uninstall-appid')
        await pilot.press(*'Zoe')
        await pilot.click('#run-exit')
        await pilot.pause()
    request = app.return_value
    assert isinstance(request, CliRunRequest)
    check('the request names the active command', request.command, 'uninstall')
    check(
        'the tokens come from that pane',
        request.tokens,
        ('--appid', 'Zoe', '--version', ':none'),
    )


async def test_many_params_scroll() -> None:
    print('[12] a long form scrolls, the log keeps its minimum height')
    app = build_app(many_params)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        params = app.query_one('#params', VerticalScroll)
        log = app.query_one('#log', RichLog)
        check(
            'the parameter list is taller than the viewport',
            params.max_scroll_y > 0,
            True,
        )
        check(
            'the viewport cannot show everything',
            params.virtual_size.height > params.size.height,
            True,
        )
        check(
            'the log panel keeps >= 5 inner lines', log.region.height >= 7, True
        )
        check(
            'the log reaches the bottom',
            log.region.bottom,
            app.screen.region.height,
        )

        # scroll to the last row.
        params.scroll_end(animate=False)
        await pilot.pause()
        check('scrolling reaches the end', params.scroll_y, params.max_scroll_y)


def test_argv_prefill() -> None:
    print('[13] the command line prefills the form')
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


def test_argv_prefill_multi_command() -> None:
    print('[14] the command line picks the tab and prefills it')
    func_infos = [func_info_of(install), func_info_of(uninstall)]
    argv = Argv(('python',), ('demo.py',), ('uninstall', 'Zoe', '1.0'))
    initials, active = resolve_initials(func_infos, argv)
    check('the named command becomes active', active, 'uninstall')
    check(
        'its values are prefilled',
        initials['uninstall'],
        {'appid': 'Zoe', 'version': '1.0'},
    )
    check('the untouched command has no values', initials['install'], {})


async def test_argv_prefill_in_form() -> None:
    print('[15] the prefilled values show up in the widgets')
    func_info = func_info_of(main)
    initial = collect_initial_values(
        func_info, Argv(('python',), ('main.py',), ('Alice', '22'))
    )
    app = ArgsenseTuiApp([func_info], initials={'main': initial})
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check(
            'name input is prefilled',
            app.query_one('#param-main-name', Input).value,
            'Alice',
        )
        check(
            'age input is prefilled',
            app.query_one('#param-main-age', Input).value,
            '22',
        )


def test_single_command_is_still_enforced() -> None:
    print('[16] resolve_single_command still rejects several commands')

    def f1() -> None: ...

    def f2() -> None: ...

    interface = TuiInterface()
    try:
        interface._interface.resolve_single_command(  # noqa: SLF001
            (f1, f2), sys._getframe(0)
        )
    except RuntimeError as exc:
        check('raises RuntimeError', 'exactly one command' in str(exc), True)
    else:
        check('raises RuntimeError', 'nothing raised', 'RuntimeError')


def test_run_delegates_to_the_form() -> None:
    print('[17] tui.run(...) resolves the entrance and opens the form')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original = renderer.run_form

    def fake_run_form(
        func_infos,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
        groups: t.Optional[t.List] = None,
    ) -> t.Any:
        captured['names'] = [x.name for x in func_infos]
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

    check('delegates to the form renderer', captured.get('names'), ['install'])
    check('passes the inline flag', captured.get('inline'), True)
    check(
        'passes the command line for prefill',
        captured['argv'].args,
        ('Alice', '22'),
    )
    check('passes a cli runner', captured.get('has_runner'), True)
    check('returns the form result', result, 'stub-result')


def test_run_and_exit_goes_through_cli() -> None:
    print('[18] "Run and exit" is dispatched to the cli path')
    import argsense.renderer.tui as renderer

    original = renderer.run_form

    def fake_run_form(
        func_infos,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
        groups: t.Optional[t.List] = None,
    ) -> t.Any:
        # pretend the user filled the form and pressed "Run and exit".
        assert cli_runner is not None
        return cli_runner(CliRunRequest('install', ('Zoe',)))

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
    print('[19] the mode tokens on the command line')
    import argsense.renderer.tui as renderer

    captured: t.Dict[str, t.Any] = {}
    original_form = renderer.run_form

    def fake_run_form(
        func_infos,
        inline: bool = False,
        argv: t.Optional[Argv] = None,
        cli_runner: t.Optional[t.Callable] = None,
        groups: t.Optional[t.List] = None,
    ) -> t.Any:
        captured['names'] = [x.name for x in func_infos]
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

        # `mode='gui'` goes to the gui renderer. That renderer is patched at
        # the dispatch point rather than imported, so that this test does not
        # pull streamlit in -- importing it mid-run disturbs the driver below.
        original_run_gui = CommandLineInterface.run_gui
        gui_seen: t.Dict[str, t.Any] = {}

        def fake_run_gui(self, entrance, caller_frame, **kwargs):
            gui_seen['entrance'] = entrance
            return 'gui-stub'

        CommandLineInterface.run_gui = fake_run_gui  # type: ignore
        try:
            sys.argv = ['prog']
            result = CommandLineInterface().run(install, mode='gui')
            check(
                'mode="gui" goes to the gui renderer',
                gui_seen.get('entrance'),
                install,
            )
            check('  ... and its result comes back', result, 'gui-stub')
        finally:
            CommandLineInterface.run_gui = original_run_gui
    finally:
        renderer.run_form = original_form
        sys.argv = original_argv


async def test_initial_tab_and_prefill() -> None:
    print('[20] the command line opens the right tab, prefilled')
    func_infos = [func_info_of(install), func_info_of(uninstall)]
    initials, active = resolve_initials(
        func_infos,
        Argv(('python',), ('demo.py',), ('uninstall', '--appid', 'alpha')),
    )
    app = ArgsenseTuiApp(func_infos, initials=initials, active=active)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check(
            'the named tab is active',
            app.query_one('#tabs', Tabs).active,
            'tab-uninstall',
        )
        check('the app follows it', app.active, 'uninstall')
        check(
            'the matching pane is shown',
            app.query_one('#panes', ContentSwitcher).current,
            'pane-uninstall',
        )
        check(
            'its argument is prefilled',
            app.query_one('#param-uninstall-appid', Input).value,
            'alpha',
        )


async def test_tooltips() -> None:
    print('[21] parameters with a description get a help tooltip')
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        appid = app.query_one('#param-install-appid', Input)
        check('the input has a tooltip', appid.tooltip is not None, True)
        text = str(appid.tooltip)
        check('it shows the description', 'the app id.' in text, True)
        check('it shows the type', 'type: TEXT' in text, True)
        check('a required param has no default line', 'default:' in text, False)

        count = app.query_one('#param-install-count', Input)
        check(
            'a defaulted param shows its default',
            'default: 1' in str(count.tooltip),
            True,
        )

        flag = app.query_one('#param-install-use_exist', Switch)
        check('flags get a tooltip too', flag.tooltip is not None, True)
        check(
            'the flag tooltip shows its type and default',
            'type: FLAG' in str(flag.tooltip)
            and 'default: :true' in str(flag.tooltip),
            True,
        )

    app = build_app(bare)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check(
            'no description -> no tooltip',
            app.query_one('#param-bare-alpha', Input).tooltip,
            None,
        )


async def test_enter_runs_when_ready() -> None:
    print('[22] Enter runs the command once the form is complete')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press('enter')
        await pilot.pause()
        check('an incomplete form ignores Enter', len(CALLS), 0)
        check('and writes nothing to the log', log_of(app), '')

        await pilot.press(*'Alice')
        await pilot.press('enter')
        await pilot.pause()
        check('a complete form runs on Enter', len(CALLS), 1)
        check(
            'with the values filled in the form',
            CALLS[0],
            ('Alice', '', True, 1),
        )


async def test_enter_needs_every_required_param() -> None:
    print('[23] Enter waits until every required parameter is filled')
    app = build_app(main)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-main-name')
        await pilot.press(*'Alice')
        await pilot.press('enter')
        await pilot.pause()
        check('a missing required param blocks Enter', log_of(app), '')

        await pilot.press('tab')
        await pilot.press(*'22')
        await pilot.press('enter')
        await pilot.pause()
        check('once filled, Enter runs it', 'Alice 22' in log_of(app), True)


async def test_enter_without_input_focus() -> None:
    print('[24] Enter also works when no input is focused')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press(*'Alice')
        app.query_one('#params', VerticalScroll).focus()
        await pilot.pause()
        await pilot.press('enter')
        await pilot.pause()
        check('the app-level binding runs the command', len(CALLS), 1)


def test_help_request_skips_the_form() -> None:
    print('[25] -h shows the help interface instead of the form')
    import argsense.renderer as renderer
    import argsense.renderer.tui as tui_renderer

    calls: t.Dict[str, t.Any] = {'form': 0, 'params': [], 'functions': 0}
    original_form = tui_renderer.run_form
    original_params = renderer.render_function_parameters
    original_functions = renderer.render_functions

    def fake_form(*args: t.Any, **kwargs: t.Any) -> str:
        calls['form'] += 1
        return 'form'

    def fake_params(argv: Argv, func_info: FuncInfo, **kwargs: t.Any) -> None:
        calls['params'].append(func_info.name)

    def fake_functions(*args: t.Any, **kwargs: t.Any) -> None:
        calls['functions'] += 1

    tui_renderer.run_form = fake_form  # type: ignore
    renderer.render_function_parameters = fake_params  # type: ignore
    renderer.render_functions = fake_functions  # type: ignore
    original_argv = sys.argv
    try:
        # a single command: `-h` renders that command's help.
        sys.argv = ['prog', '-h']
        CommandLineInterface().run(install, mode='tui')
        check('the form is not started', calls['form'], 0)
        check('the command help is rendered', calls['params'], ['install'])

        # a group of commands: `-h` renders the command list.
        interface = CommandLineInterface()
        interface.add_cmd(install)
        interface.add_cmd(uninstall)
        calls['functions'] = 0
        sys.argv = ['prog', '-h']
        interface.run(mode='tui')
        check('the form is still not started', calls['form'], 0)
        check('the command list is rendered', calls['functions'], 1)

        # ... and `<command> -h` renders the help of that command.
        calls['params'] = []
        sys.argv = ['prog', 'uninstall', '-h']
        interface.run(mode='tui')
        check('the form is not started either', calls['form'], 0)
        check(
            'the named command help is rendered', calls['params'], ['uninstall']
        )
    finally:
        tui_renderer.run_form = original_form
        renderer.render_function_parameters = original_params
        renderer.render_functions = original_functions
        sys.argv = original_argv


async def test_default_prefill() -> None:
    print('[26] a signature default prefills the input box')
    app = build_app(extra=(uninstall,))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check(
            "'' prefills :empty",
            app.query_one('#param-install-version', Input).value,
            ':empty',
        )
        check(
            'None prefills :none',
            app.query_one('#param-uninstall-version', Input).value,
            ':none',
        )
        check(
            'a non-empty default is shown as-is',
            app.query_one('#param-install-count', Input).value,
            '1',
        )
        check(
            'a required param stays empty',
            app.query_one('#param-install-appid', Input).value,
            '',
        )


async def test_cleared_input_is_reported() -> None:
    print('[27] clearing an input is reported instead of using the default')
    CALLS.clear()
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click('#param-install-appid')
        await pilot.press(*'Alice')

        version = app.query_one('#param-install-version', Input)
        version.value = ''
        await pilot.pause()
        await pilot.click('#run')
        await pilot.pause()
        check('an empty-string default -> no run', len(CALLS), 0)
        check(
            'the :empty hint is shown',
            "version miss input, to pass 'empty' value, use :empty"
            in log_of(app),
            True,
        )

        version.value = ':empty'
        count = app.query_one('#param-install-count', Input)
        count.value = ''
        await pilot.pause()
        await asyncio.sleep(0.4)
        await pilot.click('#run')
        await pilot.pause()
        check('a non-empty default -> no run', len(CALLS), 0)
        check(
            'it says the param is not filled',
            'count is not filled' in log_of(app),
            True,
        )

        count.value = '2'
        await pilot.pause()
        await asyncio.sleep(0.4)
        await pilot.click('#run')
        await pilot.pause()
        check('the form runs once fixed', CALLS[0], ('Alice', '', True, 2))

    CALLS.clear()
    app = build_app(extra=(uninstall,))
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        app.query_one('#tabs', Tabs).active = 'tab-uninstall'
        await pilot.pause()
        await pilot.click('#param-uninstall-appid')
        await pilot.press(*'Zoe')
        app.query_one('#param-uninstall-version', Input).value = ''
        await pilot.pause()
        await pilot.click('#run')
        await pilot.pause()
        check('a None default -> no run', len(CALLS), 0)
        check(
            'the :none hint is shown',
            "version miss input, to pass 'empty' value, use :none"
            in log_of(app),
            True,
        )


async def test_required_marker() -> None:
    print("[28] a required parameter is marked with a red '*'")
    app = build_app()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        rendered = rendered_label(app, 'install', 'appid')
        check('the marker precedes the name', rendered.plain, '* appid')
        check('only the marker is styled', len(rendered.spans), 1)
        span = rendered.spans[0]
        check('the marker is red', 'red' in str(span.style), True)
        check(
            'the span covers exactly the "*"',
            rendered.plain[span.start : span.end],
            '*',
        )

        other = rendered_label(app, 'install', 'version')
        check('an optional param has no marker', other.plain, 'version')
        check('and carries no style', len(other.spans), 0)


def group_names(rows: t.Sequence, width: int) -> t.List[t.List[str]]:
    """The parameter names of each planned row."""
    return [[name for name, _ in group] for group in plan_layout(rows, width)]


def test_plan_layout() -> None:
    print('[29] the layout planner only groups neighbours')
    info = func_info_of(mixed)
    plan = plan_layout(collect_rows(info), 200)
    check(
        'b and c share a row, the rest do not',
        [[name for name, _ in group] for group in plan],
        [['a'], ['b', 'c'], ['d'], ['e']],
    )

    rows = collect_rows(func_info_of(numbers))
    check(
        'a wide terminal fits the whole run',
        group_names(rows, 200),
        [['name'], ['count', 'rate', 'limit']],
    )
    check(
        'a half-empty line wraps',
        group_names(rows, 60),
        [['name'], ['count', 'rate'], ['limit']],
    )
    check(
        'a single column stacks them',
        group_names(rows, 1),
        [['name'], ['count'], ['rate'], ['limit']],
    )


async def test_compact_layout() -> None:
    print('[30] small widgets are laid out side by side')
    app = build_app(mixed)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check('five params take four rows', len(app.query('.row')), 4)
        b = app.query_one('#param-mixed-b', Switch)
        c = app.query_one('#param-mixed-c', Switch)
        d = app.query_one('#param-mixed-d', Input)
        check('b and c share a row', b.parent is c.parent, True)
        check('d does not join them', d.parent is not c.parent, True)
        check(
            'e gets a row of its own',
            app.query_one('#param-mixed-e', Switch).parent is not d.parent,
            True,
        )
        check(
            'so five params cost twelve lines, not fifteen',
            [row.size.height for row in app.query('.row')],
            [3, 3, 3, 3],
        )


async def test_compact_numbers() -> None:
    print('[31] a number gets a narrow input, a text fills the row')
    app = build_app(numbers)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        count = app.query_one('#param-numbers-count', Input)
        check(
            'the number input has room for 8 characters',
            count.content_region.width,
            8,
        )
        check(
            'its box is 12 wide (the border and the padding take 4)',
            count.outer_size.width,
            12,
        )
        check(
            'its default is still readable',
            app.query_one('#param-numbers-rate', Input).value,
            '1.0',
        )
        check(
            'the text input takes what is left',
            app.query_one('#param-numbers-name', Input).outer_size.width > 60,
            True,
        )
        check(
            'every small widget leaves the same gap after it',
            [
                app.query_one('#label-numbers-rate').region.x
                - app.query_one('#param-numbers-count').region.right,
                app.query_one('#label-numbers-limit').region.x
                - app.query_one('#param-numbers-rate').region.right,
            ],
            [3, 3],
        )
        check(
            'the names after the first one only take their text',
            [
                app.query_one('#label-numbers-rate').outer_size.width,
                app.query_one('#label-numbers-limit').outer_size.width,
            ],
            [len('rate') + 1, len('limit') + 1],
        )


async def test_triple_switch() -> None:
    print('[32] a `bool | None` parameter gets a triple switch')
    info = func_info_of(preview)
    check(
        'Optional[bool] is marked as an optional flag',
        (info.args1['show']['plain_type'], info.args1['show']['ctype'].name),
        ('optional-flag', 'FLAG'),
    )
    check(
        'bool | None is marked the same way',
        func_info_of(cache).args1['reload']['plain_type'],
        'optional-flag',
    )
    check(
        'a plain bool keeps its ordinary flag',
        func_info_of(preview).args1['live']['plain_type'],
        'flag',
    )

    app = build_app(preview)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        show = app.query_one('#param-preview-show', TripleSwitch)
        live = app.query_one('#param-preview-live', Switch)
        check('one triple switch', len(app.query(TripleSwitch)), 1)
        check('one plain switch', len(app.query(Switch)), 1)
        check('it starts on None', show.value, None)
        check('the plain switch starts off', live.value, False)
        check('they share a row', show.parent is live.parent, True)
        check('its box is 12 wide', show.outer_size.width, 12)
        check('the plain switch is 10 wide', live.outer_size.width, 10)

        cells = show.content_region
        row = cells.y - show.region.y
        knob_colors = []
        for offset, expected, class_ in (
            (3, False, '-off'),
            (5, None, '-none'),
            (7, True, '-on'),
        ):
            await pilot.click(show, offset=(offset, row))
            await pilot.pause()
            check(
                'clicking a third picks {!r}'.format(expected),
                show.value,
                expected,
            )
            check(
                '{!r} is highlighted as {}'.format(expected, class_),
                [x for x in ('-off', '-none', '-on') if show.has_class(x)],
                [class_],
            )
            knob_style = show.get_component_rich_style('triple-switch--slider')
            assert knob_style.color is not None
            knob_colors.append(knob_style.color.triplet)
        check('the three states get three colors', len(set(knob_colors)), 3)

        # the knob slides from state to state, as the stock `Switch` does.
        await pilot.click(show, offset=(3, row))  # True -> False
        positions = set()
        for _ in range(5):
            await asyncio.sleep(0.04)
            positions.add(round(show._slider_position, 3))
        check('the knob passes through the middle', len(positions) > 1, True)
        await pilot.wait_for_scheduled_animations()
        check('and it lands on False', show._slider_position, 0.0)

        show.focus()
        await pilot.pause()
        await pilot.press('space')
        await pilot.pause()
        check('space slides it forward', show.value, None)

        await pilot.click(show, offset=(7, row))
        await pilot.pause()
        check('True travels as --show', '--show' in app.collect_tokens(), True)
        await pilot.click(show, offset=(3, row))
        await pilot.pause()
        check(
            'False travels as --no-show',
            '--no-show' in app.collect_tokens(),
            True,
        )
        await pilot.click(show, offset=(5, row))
        await pilot.pause()
        check(
            'None has no token, so the default applies',
            set(app.collect_tokens()) & {'--show', '--no-show'},
            set(),
        )

        CALLS.clear()
        await pilot.click('#param-preview-port')
        await pilot.press(*'8080')
        await pilot.click(show, offset=(7, row))
        await pilot.pause()
        await pilot.click('#run')
        await pilot.pause()
        check('Run hands True to the function', CALLS[0], (8080, True, False))
        await pilot.click(show, offset=(5, row))
        await pilot.pause()
        await pilot.click('#run')
        await pilot.pause()
        check('Run hands None to the function', CALLS[1], (8080, None, False))


# -----------------------------------------------------------------------------


async def run_all() -> None:
    await test_structure()
    await test_layout_order()
    await test_button_layout()
    await test_log_height()
    await test_run()
    await test_flag_and_run_exit()
    await test_exit_button()
    await test_errors()
    await test_narrow_terminal()
    await test_multi_command_tabs()
    await test_multi_command_run_and_exit()
    await test_many_params_scroll()
    test_argv_prefill()
    test_argv_prefill_multi_command()
    await test_argv_prefill_in_form()
    test_single_command_is_still_enforced()
    test_run_delegates_to_the_form()
    test_run_and_exit_goes_through_cli()
    test_mode_tokens()
    await test_initial_tab_and_prefill()
    await test_tooltips()
    await test_enter_runs_when_ready()
    await test_enter_needs_every_required_param()
    await test_enter_without_input_focus()
    test_help_request_skips_the_form()
    await test_default_prefill()
    await test_cleared_input_is_reported()
    await test_required_marker()
    test_plan_layout()
    await test_compact_layout()
    await test_compact_numbers()
    await test_triple_switch()

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    asyncio.run(run_all())
