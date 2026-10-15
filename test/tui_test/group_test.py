"""
Headless test for the tui sidebar that `cli.run_group(...)` brings.

It drives the form without a real terminal, using textual's `Pilot`.

Usage (run from the project root):
    python test/tui_test/group_test.py
"""

import asyncio
import sys
import typing as t

from argsense.cli import CommandLineInterface
from argsense.cli import T
from argsense.parser import Argv
from argsense.parser import FuncInfo
from argsense.renderer.tui import ArgsenseTuiApp
from argsense.renderer.tui import GroupItem
from argsense.renderer.tui import resolve_initials
from textual.widgets import ListView
from textual.widgets import Tab
from textual.widgets import Tabs

SIZE = (100, 40)
#   a terminal big enough to show a small sidebar without scrolling.

SMALL_SIZE = (100, 30)
#   a terminal too small for the big fixtures below, so that they have to
#   scroll.

GroupStructure = t.List[t.Tuple[str, t.List[str]]]
FAILURES: t.List[str] = []


def install(appid: str, upgrade: bool = True) -> None:
    """
    install an app.

    params:
        appid: the app id.
        upgrade: upgrade if a newer version is available.
    """


def upgrade(appid: str) -> None:
    """
    upgrade an installed app.

    params:
        appid: the app id.
    """


def launch(appid: str) -> None:
    """
    run an installed app.

    params:
        appid: the app id.
    """


def doctor() -> None:
    """
    check the local environment.
    """


def echo(text: str) -> None:
    """
    print the text back.

    params:
        text: the text to echo.
    """


GROUPS: GroupStructure = [
    ('app', ['install', 'upgrade', 'launch']),
    ('debug', ['doctor', 'echo']),
]
#   the resolved group structure, which is what the tui takes.

GROUPS_ARG: T.CommandGroups = {
    'app': (install, upgrade, launch),
    'debug': (doctor, echo),
}
#   the argument that `cli.run_group(...)` takes.

COMMANDS = (install, upgrade, launch, doctor, echo)


def make_command(name: str) -> t.Any:
    """Build a command with the given name, for the bulky fixtures."""

    def command(alpha: str = 'x') -> None:
        pass

    command.__name__ = name
    command.__doc__ = '{0}.\n\nparams:\n    alpha: the alpha.'.format(name)
    return command


TASKS = [make_command('task-{0:02d}'.format(i)) for i in range(12)]
#   one group with more commands than the tab bar can show at once.

OTHERS = [make_command('other-{0}'.format(i)) for i in range(1, 11)]
#   more groups than the sidebar can show at once.

BIG_GROUPS: GroupStructure = [
    ('tasks', [x.__name__ for x in TASKS]),
    *[(x.__name__, [x.__name__]) for x in OTHERS],
]
BIG_COMMANDS = (*TASKS, *OTHERS)


# -----------------------------------------------------------------------------


def func_info_of(func: t.Any) -> FuncInfo:
    cli = CommandLineInterface()
    cli.add_cmd(func)
    cli.resolve_doc_references()
    return cli.commands[id(func)]


def build_app(
    groups: t.Optional[GroupStructure] = None,
    funcs: t.Sequence = COMMANDS,
    active: str = '',
    initials: t.Optional[dict] = None,
) -> ArgsenseTuiApp:
    func_infos = [func_info_of(x) for x in funcs]
    app = ArgsenseTuiApp(
        func_infos, initials=initials, groups=groups, active=active
    )
    # scrolling to a tab is animated by default; turning the animations off
    # makes the scroll land immediately, so that the checks below do not have
    # to wait for it.
    app.animation_level = 'none'
    return app


def check(label: str, actual: t.Any, expected: t.Any) -> None:
    if actual == expected:
        print('   PASS  {:<46} {}'.format(label, actual))
    else:
        FAILURES.append(label)
        print('   FAIL  {:<46} {} != {}'.format(label, actual, expected))


def group_items(app: ArgsenseTuiApp) -> t.List[GroupItem]:
    return list(app.query(GroupItem))


def visible_tabs(app: ArgsenseTuiApp) -> t.List[str]:
    """The ids of the tabs that the tab bar actually shows."""
    return [x.id or '' for x in app.query(Tab) if x.display]


def active_item(app: ArgsenseTuiApp) -> t.List[str]:
    return [x.id or '' for x in app.query(GroupItem) if x.has_class('-active')]


def is_visible_in(container: t.Any, widget: t.Any) -> bool:
    """Tell whether `widget` sits inside the region of `container`."""
    outer = container.region
    inner = widget.region
    return (
        outer.x <= inner.x
        and outer.y <= inner.y
        and inner.right <= outer.right
        and inner.bottom <= outer.bottom
    )


def painted(app: ArgsenseTuiApp) -> t.List[str]:
    """The characters that are actually painted on each screen row."""
    return [x.text for x in app.screen._compositor.render_strips()]  # noqa: SLF001


def is_centered(text: str, name: str) -> bool:
    """Tell whether `name` is painted in the middle of `text`."""
    start = text.index(name)
    return abs(start - (len(text) - start - len(name))) <= 1


# -----------------------------------------------------------------------------


async def test_sidebar_structure() -> None:
    print('[1] the sidebar is a list of big group buttons')
    app = build_app(GROUPS)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check('a sidebar is mounted', len(app.query('#sidebar')), 1)
        check(
            'and it is a list view',
            isinstance(app.query_one('#sidebar'), ListView),
            True,
        )
        check(
            'one item per group, in order',
            [x.group_name for x in group_items(app)],
            ['app', 'debug'],
        )
        check(
            'the items are identified by their group',
            [x.id for x in group_items(app)],
            ['group-app', 'group-debug'],
        )
        check(
            'each item is a three-line button',
            [x.outer_size.height for x in group_items(app)],
            [3, 3],
        )
        check(
            'the item spans the sidebar',
            [x.outer_size.width for x in group_items(app)],
            [21, 21],
        )
        check(
            'the buttons are stacked without a gap',
            [x.region.y for x in group_items(app)],
            [1, 4],
        )
        rows = painted(app)
        check(
            'and the name is painted in the middle',
            [
                is_centered(
                    rows[x.region.y + 1][x.region.x : x.region.right],
                    x.group_name,
                )
                for x in group_items(app)
            ],
            [True, True],
        )
        check(
            'the sidebar sits left of the form',
            app.query_one('#sidebar').region.x
            < app.query_one('#params').region.x,
            True,
        )
        check(
            'the tab bar and the form share the column right of the sidebar',
            (
                app.query_one(Tabs).parent is app.query_one('#main'),
                app.query_one('#params').parent is app.query_one('#main'),
            ),
            (True, True),
        )
        check(
            'that column is as tall as the sidebar',
            (
                app.query_one('#main').size.height,
                app.query_one('#sidebar').size.height,
            ),
            (18, 18),
        )
        check(
            'and the form gives the first two rows to the tab bar',
            (app.query_one(Tabs).region.y, app.query_one('#params').region.y),
            (1, 3),
        )
        check(
            'both live inside the panel above the run buttons',
            (
                app.query_one('#body').parent is app.query_one('#panel'),
                app.query_one('#panel').region.bottom
                < app.query_one('#actions').region.y,
            ),
            (True, True),
        )


async def test_only_the_active_group_is_listed() -> None:
    print("[2] the tab bar only shows the active group's commands")
    app = build_app(GROUPS)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check('the first command starts active', app.active, 'install')
        check(
            'its group is marked in the sidebar',
            active_item(app),
            ['group-app'],
        )
        check(
            'the tab bar lists that group only',
            visible_tabs(app),
            ['tab-install', 'tab-upgrade', 'tab-launch'],
        )
        check(
            'and the active tab is the one of the command',
            app.query_one(Tabs).active,
            'tab-install',
        )


async def test_clicking_a_group_switches_to_it() -> None:
    print('[3] clicking a group button opens that group')
    app = build_app(GROUPS)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        await pilot.click('#group-debug')
        await pilot.pause()
        check("the group's first command is opened", app.active, 'doctor')
        check('the sidebar follows', active_item(app), ['group-debug'])
        check(
            "the tab bar is replaced by that group's commands",
            visible_tabs(app),
            ['tab-doctor', 'tab-echo'],
        )
        check(
            'and the form shows it', app.query_one('#pane-doctor').display, True
        )
        check(
            'the group before it is hidden',
            app.query_one('#pane-install').display,
            False,
        )

        # clicking a group that is already open keeps its command.
        await pilot.click('#tab-echo')
        await pilot.pause()
        await pilot.click('#group-debug')
        await pilot.pause()
        check('clicking it again keeps the command', app.active, 'echo')


async def test_the_command_line_activates_the_group() -> None:
    print('[4] a command from the command line activates its group too')
    func_infos = [func_info_of(x) for x in COMMANDS]
    argv = Argv(launcher=('python',), target=('prog.py',), args=('echo',))
    initials, active = resolve_initials(func_infos, argv)
    check('the command line picked the command', active, 'echo')
    check('and prefilled it', initials['echo'], {})

    app = ArgsenseTuiApp(
        func_infos, initials=initials, active=active, groups=GROUPS
    )
    app.animation_level = 'none'
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check('the form opens on it', app.active, 'echo')
        check(
            "its group is the sidebar's active one",
            active_item(app),
            ['group-debug'],
        )
        check(
            "and the sidebar's cursor is on it",
            app.query_one(ListView).index,
            1,
        )
        check(
            'the tab bar shows that group, with the tab active',
            (visible_tabs(app), app.query_one(Tabs).active),
            (['tab-doctor', 'tab-echo'], 'tab-echo'),
        )
        check(
            'the form shows its pane',
            app.query_one('#panes').current,  # type: ignore
            'pane-echo',
        )


async def test_a_group_out_of_view_is_scrolled_to() -> None:
    print('[5] an out-of-view group button is scrolled into view')
    app = build_app(BIG_GROUPS, funcs=BIG_COMMANDS, active='other-10')
    async with app.run_test(size=SMALL_SIZE) as pilot:
        await pilot.pause()
        sidebar = app.query_one('#sidebar')
        item = app.query_one('#group-other-10', GroupItem)
        check(
            'the group is the active one', active_item(app), ['group-other-10']
        )
        check(
            'its item is the last one',
            [x.group_name for x in group_items(app)][-1],
            'other-10',
        )
        check('so the sidebar had to scroll', sidebar.scroll_offset.y > 0, True)
        check(
            'and the item is inside the view',
            is_visible_in(sidebar, item),
            True,
        )
        check(
            'while the first group is out of view',
            is_visible_in(sidebar, app.query_one('#group-tasks', GroupItem)),
            False,
        )


async def test_a_tab_out_of_view_is_scrolled_to() -> None:
    print('[6] an out-of-view tab is scrolled into view')
    app = build_app(BIG_GROUPS, funcs=BIG_COMMANDS, active='task-11')
    async with app.run_test(size=SMALL_SIZE) as pilot:
        await pilot.pause()
        tabs = app.query_one(Tabs)
        tab = app.query_one('#tab-task-11', Tab)
        check('the tab bar shows the group', len(visible_tabs(app)), 12)
        check('the tab is the active one', tabs.active, 'tab-task-11')
        check(
            'so the tab bar had to scroll',
            tabs.query_one('#tabs-scroll').scroll_offset.x > 0,
            True,
        )
        check('and the tab is inside its view', is_visible_in(tabs, tab), True)
        check(
            'while the first tab is out of view',
            is_visible_in(tabs, app.query_one('#tab-task-00', Tab)),
            False,
        )


async def test_ungrouped_leftovers() -> None:
    print('[7] commands that no group mentions land in "ungrouped"')
    app = build_app(
        [('app', ['install', 'upgrade'])],
        funcs=(install, upgrade, launch, doctor),
    )
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        check(
            'the extra group is appended',
            [x.group_name for x in group_items(app)],
            ['app', 'ungrouped'],
        )
        check(
            'and holds the leftover commands',
            app.members_of['ungrouped'],
            ['launch', 'doctor'],
        )


def test_run_group_opens_the_form() -> None:
    print('[8] cli.run_group(...) can open the form')
    import argsense.renderer as renderer
    import argsense.renderer.tui as tui_renderer

    captured: t.Dict[str, t.Any] = {}
    original_form = tui_renderer.run_form
    original_functions = renderer.render_functions

    def fake_run_form(
        func_infos: t.Sequence[FuncInfo],
        inline: bool = False,
        argv: t.Any = None,
        cli_runner: t.Optional[t.Callable] = None,
        groups: t.Optional[GroupStructure] = None,
    ) -> str:
        captured['names'] = [x.name for x in func_infos]
        captured['inline'] = inline
        captured['groups'] = groups
        captured['has_runner'] = callable(cli_runner)
        return 'stub-result'

    def fake_render_functions(
        argv: t.Any, funcs: t.Any, groups: t.Optional[GroupStructure] = None
    ) -> None:
        captured['cli_groups'] = groups

    tui_renderer.run_form = fake_run_form  # type: ignore
    renderer.render_functions = fake_render_functions  # type: ignore
    original_argv = sys.argv
    try:
        sys.argv = ['prog', ':tui']
        result = CommandLineInterface().run_group(GROUPS_ARG)
        check(
            'the mode token wins over the default',
            captured.get('groups'),
            GROUPS,
        )
        check(
            'the form gets every command',
            captured.get('names'),
            ['install', 'upgrade', 'launch', 'doctor', 'echo'],
        )
        check('the form is not inline', captured.get('inline'), False)
        check('a cli runner is passed', captured.get('has_runner'), True)
        check('and the result comes back', result, 'stub-result')

        captured.clear()
        sys.argv = ['prog', ':itui']
        CommandLineInterface().run_group(GROUPS_ARG)
        check(':itui asks for the inline form', captured.get('inline'), True)

        captured.clear()
        sys.argv = ['prog', ':tui', '-h']
        CommandLineInterface().run_group(GROUPS_ARG)
        check(
            'a help request keeps the sidebar shut', 'groups' in captured, False
        )
        check(
            'and asks for the cli group tree',
            captured.get('cli_groups'),
            GROUPS,
        )
    finally:
        tui_renderer.run_form = original_form
        renderer.render_functions = original_functions
        sys.argv = original_argv

    print('[9] and its help interface still shows the group tree')
    try:
        sys.argv = ['prog', '-h']
        CommandLineInterface().run_group(GROUPS_ARG)
    finally:
        sys.argv = original_argv
    check(
        'the tree renderer got the structure',
        captured.get('cli_groups'),
        GROUPS,
    )


# -----------------------------------------------------------------------------


async def run_all() -> None:
    await test_sidebar_structure()
    await test_only_the_active_group_is_listed()
    await test_clicking_a_group_switches_to_it()
    await test_the_command_line_activates_the_group()
    await test_a_group_out_of_view_is_scrolled_to()
    await test_a_tab_out_of_view_is_scrolled_to()
    await test_ungrouped_leftovers()
    test_run_group_opens_the_form()

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    asyncio.run(run_all())
