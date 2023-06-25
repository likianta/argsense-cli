import typing as t
from os.path import normpath
from sys import platform

from ...parser.args_parser import ParamType
from ...parser.func_parser import FuncInfo
from ...parser.func_parser import T as T0

try:
    import PySimpleGUI as psg  # noqa
except (ImportError, ModuleNotFoundError):
    
    class FakeTyping:
        
        def __bool__(self) -> bool:
            return False
        
        def __getattr__(self, k) -> t.Any:
            return self
            
    psg = FakeTyping()
    
else:
    psg.theme('SandyBeach')
    psg.set_options(
        icon=open(normpath(f'{__file__}/../launcher.png'), 'rb').read(),
        font=('Helvetica', 13) if platform == 'darwin' else None,
    )


class T:
    ArgsInfo = T0.ArgsInfo
    FuncsInfo = t.Union[t.Tuple[FuncInfo, ...], t.List[FuncInfo]]
    KwArgsInfo = T0.KwArgsInfo
    ParamName = T0.ParamName
    
    Layout = t.List[t.List[psg.Element]]
    Row = t.List[psg.Element]


def run(funcs_info: T.FuncsInfo) -> t.Any:
    if psg is None:
        raise RuntimeError('PySimpleGUI is not installed')
    
    layout = [
        [
            _create_tab_group(funcs_info),
        ],
        [
            psg.Button('copy command'),
            psg.Button('run'),
        ],
    ]
    
    win = psg.Window('Argsense GUI', layout)
    while True:
        evt, val = win.read()
        print(evt, val, ':lv')
        if evt in (psg.WIN_CLOSED, 'Exit', None):
            break
    win.close()


def _add_row(*items: psg.Element) -> T.Row:
    return list(items)


def _create_tab_group(funcs_info: T.FuncsInfo) -> psg.TabGroup:
    layout = []
    for info in funcs_info:
        layout.append([
            psg.Tab(info.name, [
                [
                    psg.Text(info.name),
                ],
                [
                    psg.Text(info.desc),
                ],
                [
                    psg.Frame(
                        'arguments',
                        _build_args_panel(info.args)
                    )
                ],
                [
                    psg.Frame(
                        'keyword arguments',
                        _build_kwargs_panel(info.local_kwargs)
                    )
                ]
            ])
        ])
    return psg.TabGroup(layout)


def _build_args_panel(args_info: T.ArgsInfo) -> T.Layout:
    layout = []
    for name, info in args_info.items():
        for item in _get_arg_entry(name, info):
            layout.append(_add_row(item))
    return layout


def _build_kwargs_panel(kwargs_info: T.KwArgsInfo) -> T.Layout:
    layout = []
    for name, info in kwargs_info.items():
        for item in _get_kwarg_entry(name, info):
            layout.append(_add_row(item))
    return layout


def _get_arg_entry(name: T.ParamName, info: dict) -> t.Iterable[psg.Element]:
    name = name + ' ({})'.format(info['ctype'].name)
    
    assert info['ctype'] not in (ParamType.DICT, ParamType.LIST), \
        ('unsupported type', info)
    assert info['ctype'] not in (ParamType.FLAG, ParamType.NONE), \
        ('unexpected type', info)
    
    if info['ctype'] == ParamType.BOOL:
        yield psg.Checkbox(name)
        if info['desc']:
            yield psg.Text(info['desc'], text_color='grey')
    
    else:
        yield psg.Text(name)
        if info['desc']:
            yield psg.Text(info['desc'], text_color='grey')
        yield psg.InputText()


def _get_kwarg_entry(name: T.ParamName, info: dict) -> t.Iterable[psg.Element]:
    name = name + ' ({})'.format(info['ctype'].name)
    
    assert info['ctype'] not in (ParamType.DICT, ParamType.LIST), \
        ('unsupported type', info)
    assert info['ctype'] not in (ParamType.BOOL, ParamType.NONE), \
        ('unexpected type', info)
    
    if info['ctype'] == ParamType.FLAG:
        yield psg.Checkbox(name, default=bool(info['default']))
        if info['desc']:
            yield psg.Text(info['desc'], text_color='grey')
    
    else:
        yield psg.Text(name)
        if info['desc']:
            yield psg.Text(info['desc'], text_color='grey')
        yield psg.InputText(default_text=str(info['default']))
