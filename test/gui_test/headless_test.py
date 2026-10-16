"""
Headless test for the argsense GUI.

It builds the form without a browser and without a streamlit runtime -- a
canary component tree can be built at any time (the runtime is what registers
it, and there is simply none here), so the specs, the rows, the sizes and the
run path can all be checked from an ordinary script.

Usage (run from the project root):
    python test/gui_test/headless_test.py
"""

import io
import sys
import typing as t
from contextlib import redirect_stdout

from argsense.cli import _MODE_TOKENS
from argsense.cli import DEFAULT_GUI_PORT
from argsense.cli import CommandLineInterface
from argsense.renderer.gui import SKIP
from argsense.renderer.gui import GuiScene
from argsense.renderer.gui import param_field
from argsense.renderer.gui import plan_rows
from argsense.renderer.gui import read_param
from argsense.renderer.gui import resolve_groups
from argsense.renderer.gui import row_slots
from argsense.renderer.gui import spec_of
from argsense.renderer.gui import value_of
from argsense.renderer.gui.fields import LONG
from argsense.renderer.gui.fields import SHORT
from argsense.renderer.gui.fields import VARIABLE
from argsense.renderer.gui.fields import WIDTH_CLASS_OF_KIND
from argsense.renderer.gui.fields import double_index_of
from argsense.renderer.gui.fields import triple_index_of
from argsense.renderer.gui.layout import QUARTERS_PER_ROW
from argsense.renderer.gui.layout import chrome_height
from argsense.renderer.gui.layout import estimate_window_size
from argsense.renderer.gui.layout import log_panel_height
from argsense.renderer.gui.layout import param_rows_height
from argsense.renderer.gui.layout import screen_size_in_css_px
from argsense.renderer.gui.spec import FLAG
from argsense.renderer.gui.spec import MAYBE_NUMBER
from argsense.renderer.gui.spec import NUMBER
from argsense.renderer.gui.spec import TEXT
from argsense.renderer.gui.spec import TRIPLE
from argsense.renderer.gui.spec import Param
from argsense.renderer.gui.spec import kind_of
from argsense.renderer.gui.spec import short_flag_of

CALLS: t.List[t.Tuple] = []
FAILURES: t.List[str] = []


# -----------------------------------------------------------------------------
# the commands under test (the ones of the showcase, plus a raising one)


def build(
    project: str,
    version: str = '0.1.0',
    jobs: int = 4,
    retries: int = 2,
    rate: float = 1.0,
    timeout: float = 60.0,
    wheel: bool = True,
    sdist: bool = False,
    clean: bool = False,
    verbose: bool = False,
) -> None:
    """
    Build a project.

    params:
        project: The project name.
        version: The version to stamp on the artifacts.
        jobs: How many steps to run in parallel.
        retries: How many times to retry a failed step.
        rate: The compression level.
        timeout: The per step timeout, in seconds.
        wheel: Build a wheel.
        sdist: Build a source distribution.
        clean: Empty the output directory first.
        verbose (-v): Print every command that is run.
    """
    CALLS.append(('build', locals()))


def serve(
    port: int,
    host: str = '127.0.0.1',
    reload: t.Optional[bool] = None,
    workers: int = 1,
    daemon: bool = False,
) -> None:
    """
    Start the development server.

    params:
        port: The port to listen on.
        host: The interface to bind to.
        reload: Restart when a source file changes.
        workers: How many worker processes to spawn.
        daemon: Detach from the terminal.
    """
    CALLS.append(('serve', locals()))


def fetch(
    url: str,
    # the pep 604 spelling of `Optional[bool]`, which needs python 3.10+.
    cache: bool | None = True,  # type: ignore
    timeout: t.Optional[float] = None,
    retries: t.Optional[int] = None,
    token: t.Optional[str] = None,
) -> None:
    """
    Fetch a URL.

    params:
        url: The address to fetch.
        cache: Use the cached response.
        timeout: The network timeout, in seconds.
        retries: How many times to retry on a failure.
        token: The bearer token to send, if any.
    """
    CALLS.append(('fetch', locals()))


def doctor(verbose: bool = False) -> None:
    """
    Check the local environment.

    params:
        verbose (-v): Show every check that was made.
    """
    CALLS.append(('doctor', locals()))


def version() -> None:
    """Show the version of this demo."""
    CALLS.append(('version', {}))


def explode() -> None:
    """Raise, so that Run's error path can be looked at."""
    raise ValueError('boom')


# -----------------------------------------------------------------------------


def check(label: str, actual: t.Any, expected: t.Any) -> None:
    if actual == expected:
        print('   PASS  {:<44} {}'.format(label, actual))
    else:
        FAILURES.append(label)
        print('   FAIL  {:<44} {} != {}'.format(label, actual, expected))


def func_infos_of(*funcs: t.Any) -> t.List[t.Any]:
    """Register the functions and hand back their `FuncInfo`, in order."""
    interface = CommandLineInterface('gui-test')
    for func in funcs:
        interface.add_cmd(func)
    return list(interface.commands.values())


def specs_of(*funcs: t.Any) -> t.Dict[str, t.Any]:
    return {x.name: x for x in map(spec_of, func_infos_of(*funcs))}


def params_of(command: t.Any) -> t.Dict[str, Param]:
    return {param.name: param for param in command.params}


# -----------------------------------------------------------------------------


def test_spec() -> None:
    print('[1] spec: kind / required / label / short flag')
    specs = specs_of(build, serve, fetch, doctor, version)

    bp = params_of(specs['build'])
    kinds = {name: param.kind for name, param in bp.items()}
    check('str -> text', kinds['project'], TEXT)
    check('int -> number', kinds['jobs'], NUMBER)
    check('float -> number', kinds['rate'], NUMBER)
    check('bool -> flag', kinds['wheel'], FLAG)
    check(
        'a parameter without a default is required',
        bp['project'].required,
        True,
    )
    check('a parameter with one is optional', bp['version'].required, False)
    check('a required one drops its default', bp['project'].default, None)
    check('the short flag is read off the cname', bp['verbose'].short, '-v')
    check(
        'the label carries the short flag',
        bp['verbose'].label,
        'verbose :gray[(-v)]',
    )
    check(
        'the label marks a required one', bp['project'].label, 'project :red[*]'
    )
    check('an int seed is its default', bp['jobs'].seed, 4)
    check('a float seed is its default', bp['rate'].seed, 1.0)

    sp = params_of(specs['serve'])
    check('Optional[bool] -> triple', sp['reload'].kind, TRIPLE)
    check('a required int is a number box', sp['port'].kind, NUMBER)
    check('a required port seeds at a zero of its type', sp['port'].seed, 0)
    check(
        'a parameter with no default and no setter is required',
        sp['port'].required,
        True,
    )

    fp = params_of(specs['fetch'])
    check('bool | None -> triple', fp['cache'].kind, TRIPLE)
    check(
        'Optional[float] = None -> maybe-number',
        fp['timeout'].kind,
        MAYBE_NUMBER,
    )
    check(
        'Optional[int] = None -> maybe-number', fp['retries'].kind, MAYBE_NUMBER
    )
    check('Optional[str] = None -> text', fp['token'].kind, TEXT)
    check('an absent-able one is not required', fp['timeout'].required, False)

    check('a command with no parameter has none', specs['version'].params, [])
    check(
        'the description comes from the docstring',
        specs['version'].desc,
        'Show the version of this demo.',
    )
    check('the function comes along', specs['build'].func, build)


def test_helpers() -> None:
    print('[2] the small helpers')
    check(
        'kind_of: a required int is a number box',
        kind_of('int', required=True, default=None),
        NUMBER,
    )
    check(
        'kind_of: an absent-able int is a text box',
        kind_of('int', required=False, default=None),
        MAYBE_NUMBER,
    )
    check(
        'kind_of: a defaulted int is a number box',
        kind_of('int', required=False, default=3),
        NUMBER,
    )
    check(
        'kind_of: an unknown type falls back to text',
        kind_of('weird', required=True, default=None),
        TEXT,
    )

    check('short flag: taken off a pair', short_flag_of('--verbose, -v'), '-v')
    check(
        'short flag: none when there is only a long one',
        short_flag_of('--jobs'),
        '',
    )
    check('short flag: none when the cname is empty', short_flag_of(''), '')

    check('double index: False', double_index_of(False), 0)
    check('double index: True', double_index_of(True), 1)
    check('triple index: False', triple_index_of(False), 0)
    check('triple index: None', triple_index_of(None), 1)
    check('triple index: True', triple_index_of(True), 2)

    check('value_of: a plain int', value_of('42'), 42)
    check('value_of: a hex int', value_of('0x1F'), 31)
    check('value_of: a binary int', value_of('0b1101'), 13)
    check('value_of: an octal int', value_of('0o755'), 493)
    check('value_of: a grouped int', value_of('1_000'), 1000)
    check('value_of: a leading zero still reads as int', value_of('08'), 8)
    check('value_of: a float', value_of('3.14'), 3.14)
    check('value_of: an exponent', value_of('1e3'), 1000.0)
    check('value_of: a word is left alone', value_of('abc'), 'abc')
    check('value_of: :true', value_of(':true'), True)
    check('value_of: :TRUE is case-insensitive', value_of(':TRUE'), True)
    check('value_of: :false', value_of(':false'), False)
    check('value_of: :none', value_of(':none'), None)
    check('value_of: :null', value_of(':null'), None)
    check(
        'value_of: an unknown colon word is left alone',
        value_of(':other'),
        ':other',
    )


def test_plan_rows() -> None:
    print('[3] packing the rows')
    params = specs_of(build, serve, fetch)['build'].params

    rows = plan_rows(params)
    check('row count', len(rows), 4)
    check('row sizes', [len(row) for row in rows], [1, 1, 4, 4])
    check(
        'the first row is the text input',
        [p.name for p in rows[0]],
        ['project'],
    )
    check(
        'four numbers share a row',
        [p.name for p in rows[2]],
        ['jobs', 'retries', 'rate', 'timeout'],
    )
    check(
        'four flags share a row',
        [p.name for p in rows[3]],
        ['wheel', 'sdist', 'clean', 'verbose'],
    )

    serve_rows = plan_rows(specs_of(serve)['serve'].params)
    check(
        'a text input ends the run before it',
        [len(row) for row in serve_rows],
        [1, 1, 3],
    )

    fetch_rows = plan_rows(specs_of(fetch)['fetch'].params)
    check(
        'a text input ends the run after it',
        [len(row) for row in fetch_rows],
        [1, 3, 1],
    )


def test_row_slots() -> None:
    print('[3b] sharing a row out in quarters')
    classes = {
        'text': TEXT,
        'number': NUMBER,
        'maybe': MAYBE_NUMBER,
        'flag': FLAG,
        'triple': TRIPLE,
    }
    check('text -> long', WIDTH_CLASS_OF_KIND[TEXT], LONG)
    check('number -> variable', WIDTH_CLASS_OF_KIND[NUMBER], VARIABLE)
    check(
        'maybe-number -> variable', WIDTH_CLASS_OF_KIND[MAYBE_NUMBER], VARIABLE
    )
    check('flag -> short', WIDTH_CLASS_OF_KIND[FLAG], SHORT)
    check('triple -> short', WIDTH_CLASS_OF_KIND[TRIPLE], SHORT)

    def row(*names: str) -> t.List[Param]:
        return [
            Param('p{}'.format(i), classes[name], '', None, '', False, '')
            for i, name in enumerate(names)
        ]

    def slots(*names: str) -> t.Tuple[t.List[int], int]:
        return row_slots(row(*names))

    check(
        'four numbers: 1:1:1:1',
        slots('number', 'number', 'number', 'number'),
        ([1, 1, 1, 1], 0),
    )
    check(
        'one number, two switches: 2:1:1',
        slots('number', 'flag', 'flag'),
        ([2, 1, 1], 0),
    )
    check(
        'two numbers, two switches: 1:1:1:1',
        slots('number', 'number', 'flag', 'flag'),
        ([1, 1, 1, 1], 0),
    )
    check('two numbers: 2:2', slots('number', 'number'), ([2, 2], 0))
    check(
        'two numbers, one switch: 1:1:1 and a spare',
        slots('number', 'number', 'flag'),
        ([1, 1, 1], 1),
    )
    check(
        'the order does not matter',
        slots('flag', 'number', 'flag'),
        ([1, 2, 1], 0),
    )
    check(
        'the spare sits at the end',
        slots('flag', 'number', 'number'),
        ([1, 1, 1], 1),
    )
    check('one number alone takes the line', slots('number'), ([4], 0))
    check('one switch alone takes a quarter', slots('flag'), ([1], 3))
    check(
        'four switches fill the line',
        slots('flag', 'triple', 'flag', 'triple'),
        ([1, 1, 1, 1], 0),
    )
    check(
        'three switches leave a spare',
        slots('flag', 'flag', 'triple'),
        ([1, 1, 1], 1),
    )
    check(
        'a maybe-number counts as a number', slots('maybe', 'flag'), ([3, 1], 0)
    )
    check(
        'three numbers leave a spare',
        slots('number', 'number', 'number'),
        ([1, 1, 1], 1),
    )
    check('a lone text input takes the line', slots('text'), ([4], 0))
    check(
        'every rule fills or spares exactly four quarters',
        all(
            sum(s) + spare == QUARTERS_PER_ROW
            for s, spare in (
                slots('number', 'number', 'number', 'number'),
                slots('number', 'flag', 'flag'),
                slots('flag', 'flag', 'triple'),
                slots('number'),
                slots('flag'),
            )
        ),
        True,
    )


def test_resolve_groups() -> None:
    print('[4] resolving the groups')
    commands = [
        spec_of(x) for x in func_infos_of(build, serve, fetch, doctor, version)
    ]

    flat = resolve_groups(None, commands)
    check(
        'no groups -> one flat group', [name for name, _ in flat], ['commands']
    )
    check(
        'flat holds every command',
        [c.name for c in flat[0][1]],
        ['build', 'serve', 'fetch', 'doctor', 'version'],
    )

    structure = [
        ('app', ['build', 'serve']),
        ('net', ['fetch']),
        ('debug', ['doctor', 'version']),
    ]
    grouped = resolve_groups(structure, commands)
    check(
        'the groups come through',
        [name for name, _ in grouped],
        ['app', 'net', 'debug'],
    )
    check(
        'their members too',
        [[c.name for c in m] for _, m in grouped],
        [['build', 'serve'], ['fetch'], ['doctor', 'version']],
    )

    leftovers = resolve_groups([('app', ['build'])], commands)
    check(
        'commands no group mentions are collected',
        [name for name, _ in leftovers],
        ['app', 'ungrouped'],
    )
    check(
        'in their own order',
        [c.name for c in leftovers[1][1]],
        ['serve', 'fetch', 'doctor', 'version'],
    )

    dropped = resolve_groups(
        [('app', ['build']), ('ghost', ['missing'])], commands
    )
    check(
        'a group with no member is dropped',
        [name for name, _ in dropped],
        ['app', 'ungrouped'],
    )


def test_layout() -> None:
    print('[5] the sizes')
    check('a row is four quarters wide', QUARTERS_PER_ROW, 4)
    check('one row is 60', param_rows_height(1), 60)
    check('two rows add one gap', param_rows_height(2), 136)
    check('four rows', param_rows_height(4), 288)
    check('six rows', param_rows_height(6), 440)
    check('a tall form gets the tall log panel', log_panel_height(4), 300)
    check('a short form gets the short one', log_panel_height(3), 200)
    check('the chrome around the rows', chrome_height(300), 618)
    check('the chrome with the short panel', chrome_height(200), 518)

    _, screen_height = screen_size_in_css_px()
    max_height = round(screen_height * 0.9)
    wide = estimate_window_size(4, wide=True, extra_height=618)
    check('wide window: width', wide[0], 980)
    check('wide window: height', wide[1], min(max(600, 906), max_height))
    narrow = estimate_window_size(6, wide=False, extra_height=618)
    check('narrow window: width', narrow[0], 700)
    check('narrow window: height', narrow[1], min(max(600, 1058), max_height))
    tiny = estimate_window_size(0, wide=False, extra_height=518)
    check('a tiny form never goes below the floor', tiny[1], 600)


def test_scene() -> None:
    print('[6] the scene')
    commands = [
        spec_of(x) for x in func_infos_of(build, serve, fetch, doctor, version)
    ]
    structure = [
        ('app', ['build', 'serve']),
        ('net', ['fetch']),
        ('debug', ['doctor', 'version']),
    ]
    scene = GuiScene(resolve_groups(structure, commands))

    check('several groups -> a wide window', scene.wide, True)
    check('the tallest command decides the rows', scene.max_param_rows, 4)
    check('a tall form -> the tall log panel', scene.log_height, 300)
    check('the window width', scene.window_size[0], 980)
    check('the first group is on show', scene.state.group.get(), 'app')
    check(
        'every command is known',
        [c.name for c in scene.commands],
        ['build', 'serve', 'fetch', 'doctor', 'version'],
    )
    check('the group of each command', scene.group_of['fetch'], 'net')

    scene.setup_ui('gui-test')
    check(
        'one field group per command',
        sorted(scene.fields),
        ['build', 'doctor', 'fetch', 'serve', 'version'],
    )
    check('build has ten widgets', len(scene.fields['build']), 10)
    check('version has none', len(scene.fields['version']), 0)
    check(
        'tabs only for a group with several commands',
        sorted(scene.tabs),
        ['app', 'debug'],
    )
    check('the log panel is kept', scene.logger is not None, True)
    shown = scene.command_at('app')
    check(
        'the picked tab is the first command',
        shown.name if shown else None,
        'build',
    )

    flat = GuiScene(resolve_groups(None, commands))
    check('one group -> a narrow window', flat.wide, False)
    check('the same rows as the wide form', flat.max_param_rows, 4)
    check('the window width', flat.window_size[0], 700)
    check('no tab bar for a group of one command', flat.tabs, {})


def test_read_param() -> None:
    print('[7] reading a widget back')
    empty = set()

    text = Param('name', TEXT, 'str', None, '', True, '')
    check(
        'an empty text box means skip',
        read_param(text, param_field(text), touched=empty, key='x'),
        SKIP,
    )
    filled = param_field(text)
    filled.value.set('zoe')
    check(
        'a filled text box means its content',
        read_param(text, filled, touched=empty, key='x'),
        'zoe',
    )

    maybe = Param('timeout', MAYBE_NUMBER, 'int', None, '', False, '')
    blank = param_field(maybe)
    blank.value.set('   ')
    check(
        'a blank absent-able box means skip',
        read_param(maybe, blank, touched=empty, key='x'),
        SKIP,
    )
    number = param_field(maybe)
    number.value.set('30')
    check(
        'a filled one is read as a value',
        read_param(maybe, number, touched=empty, key='x'),
        30,
    )

    flag = Param('verbose', FLAG, 'flag', False, '', False, '')
    check(
        'a two-mark switch: left is False',
        read_param(flag, param_field(flag), touched=empty, key='x'),
        False,
    )
    on = param_field(flag)
    on.index.set(1)
    check(
        'a two-mark switch: right is True',
        read_param(flag, on, touched=empty, key='x'),
        True,
    )

    triple = Param('reload', TRIPLE, 'optional-flag', None, '', False, '')
    for index, expected in ((0, False), (1, None), (2, True)):
        field = param_field(triple)
        field.index.set(index)
        check(
            'a three-mark switch at {}'.format(index),
            read_param(triple, field, touched=empty, key='x'),
            expected,
        )

    box = Param('jobs', NUMBER, 'int', 4, '', False, '')
    check(
        'an untouched number box keeps its default',
        read_param(box, param_field(box), touched=empty, key='x'),
        4,
    )
    required = Param('port', NUMBER, 'int', None, '', True, '')
    check(
        'an untouched required box means skip',
        read_param(required, param_field(required), touched=empty, key='x'),
        SKIP,
    )
    edited = param_field(box)
    edited.value.set(8)
    check(
        'an edited number box is read',
        read_param(box, edited, touched={'x'}, key='x'),
        8,
    )


def test_collect_and_run() -> None:
    print('[8] collecting the form and running the command')
    commands = [
        spec_of(x) for x in func_infos_of(build, doctor, version, explode)
    ]
    structure = [
        ('build', ['build']),
        ('doctor', ['doctor']),
        ('version', ['version']),
        ('boom', ['explode']),
    ]
    scene = GuiScene(resolve_groups(structure, commands))
    scene.setup_ui('gui-test')

    build_cmd = scene.members['build'][0]
    kwargs, errors = scene.collect(build_cmd)
    check(
        'a missing required text blocks the run',
        errors,
        ['project is required'],
    )
    check(
        'the defaults are filled in',
        kwargs,
        {
            'version': '0.1.0',
            'jobs': 4,
            'retries': 2,
            'rate': 1.0,
            'timeout': 60.0,
            'wheel': True,
            'sdist': False,
            'clean': False,
            'verbose': False,
        },
    )

    fields = scene.fields['build']
    fields['project'].value.set('my-project')
    jobs = next(p for p in build_cmd.params if p.name == 'jobs')
    # what the browser patches in, and the change it reports for a number box
    fields['jobs'].value.set(8)
    scene.touched.add(scene.key_of(build_cmd, jobs))
    fields['verbose'].index.set(1)
    kwargs, errors = scene.collect(build_cmd)
    check('a filled form has no error', errors, [])
    check('the text is handed over', kwargs['project'], 'my-project')
    check('an edited number wins over the default', kwargs['jobs'], 8)
    check('a switch is handed over as a bool', kwargs['verbose'], True)

    CALLS.clear()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        scene.run_command()
    out = buffer.getvalue()
    check('Run calls the command on show', CALLS[-1][0], 'build')
    check('Run hands the form over', CALLS[-1][1]['project'], 'my-project')
    check(
        'Run echoes the call', out.splitlines()[0].startswith('$ build '), True
    )
    check('Run reports the end', out.strip().endswith(': done'), True)

    scene.state.group.set('version')
    CALLS.clear()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        scene.run_command()
    check('another group runs its own command', CALLS[-1][0], 'version')
    check(
        'a command with no argument echoes bare',
        buffer.getvalue().splitlines()[0].startswith('$ version'),
        True,
    )

    scene.state.group.set('boom')
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        scene.run_command()
    check(
        'an exception is reported, not raised',
        ': ValueError: boom' in buffer.getvalue(),
        True,
    )


def test_fetch_absences() -> None:
    print('[9] the absent-able parameters of a form')
    scene = GuiScene(
        resolve_groups(None, [spec_of(x) for x in func_infos_of(fetch)])
    )
    scene.setup_ui('gui-test')
    command = scene.members['commands'][0]

    kwargs, errors = scene.collect(command)
    check('the required url blocks the run', errors, ['url is required'])
    check('absent-able boxes are left out', sorted(kwargs), ['cache'])
    check('a triple switch starts at its default', kwargs['cache'], True)

    fields = scene.fields['fetch']
    fields['url'].value.set('https://example.com')
    fields['cache'].index.set(1)
    fields['timeout'].value.set('30')
    kwargs, errors = scene.collect(command)
    check('a filled form has no error', errors, [])
    check('the url is handed over', kwargs['url'], 'https://example.com')
    check('the middle mark is None', kwargs['cache'], None)
    check('a filled absent-able box is handed over', kwargs['timeout'], 30)
    check('a blank one is still left out', 'retries' in kwargs, False)
    check('and so is a blank text one', 'token' in kwargs, False)


def test_cli_wiring() -> None:
    print('[10] the cli wiring')
    check(
        "':gui' -> gui, a browser tab",
        _MODE_TOKENS.get(':gui'),
        ('gui', {'window': False}),
    )
    check(
        "':guiw' -> gui, a native window",
        _MODE_TOKENS.get(':guiw'),
        ('gui', {'window': True}),
    )
    check(
        "':tui' -> tui, full screen",
        _MODE_TOKENS.get(':tui'),
        ('tui', {'inline': False}),
    )
    check(
        "':itui' -> tui, inline",
        _MODE_TOKENS.get(':itui'),
        ('tui', {'inline': True}),
    )
    check('the default port', DEFAULT_GUI_PORT, 2026)

    import argsense
    import argsense.renderer.gui as gui_renderer

    check('the gui interface is exported', hasattr(argsense, 'gui'), True)
    check('and its class', hasattr(argsense, 'GuiInterface'), True)

    captured: t.Dict[str, t.Any] = {}
    original_form = gui_renderer.run_form

    def fake_run_form(func_infos: t.Any, **kwargs: t.Any) -> str:
        captured['names'] = [x.name for x in func_infos]
        captured['groups'] = kwargs.get('groups')
        return 'gui-stub'

    gui_renderer.run_form = fake_run_form  # type: ignore
    original_argv = sys.argv
    try:
        sys.argv = ['prog', ':gui']
        result = CommandLineInterface().run_group(
            {'app': (build, serve)}, mode='cli'
        )
        check(
            ':gui overrides mode="cli"',
            captured.get('names'),
            ['build', 'serve'],
        )
        check(
            'the group structure goes to the form',
            [n for n, _ in captured['groups']],
            ['app'],
        )
        check("the result is the form's", result, 'gui-stub')
    finally:
        gui_renderer.run_form = original_form
        sys.argv = original_argv


# -----------------------------------------------------------------------------


def run_all() -> None:
    test_spec()
    test_helpers()
    test_plan_rows()
    test_row_slots()
    test_resolve_groups()
    test_layout()
    test_scene()
    test_read_param()
    test_collect_and_run()
    test_fetch_absences()
    test_cli_wiring()

    print()
    if FAILURES:
        print('{} check(s) FAILED:'.format(len(FAILURES)))
        for name in FAILURES:
            print('  - {}'.format(name))
        raise SystemExit(1)
    print('all checks passed')


if __name__ == '__main__':
    run_all()
