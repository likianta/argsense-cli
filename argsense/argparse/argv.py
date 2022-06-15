from __future__ import annotations

import typing as t
from enum import Enum, auto
from dataclasses import dataclass


# noinspection PyArgumentList
class ParamType(Enum):
    TEXT = auto()
    NUMBER = auto()
    FLAG = auto()
    ANY = auto()


class T:
    ProgType = t.Literal['script', 'module', 'exe']
    
    _KwArgName = str
    _OptionName = str
    _ParamName = str
    ParamType = ParamType  # i.e. Enum
    
    ParamsInfo = t.TypedDict('ParamsInfo', {
        'args'  : t.Dict[_ParamName, ParamType],
        'kwargs': t.Dict[_KwArgName, ParamType],
        'index' : t.Dict[_OptionName, _KwArgName],
    })


class Argv:
    argv_seq: list[str]
    argv_str: str  # DELETE
    pointer: int  # DELETE
    
    prog_head: str
    _prog_type: T.ProgType
    
    def __init__(self, argv: list[str]):
        self.argv_seq = argv.copy()
        self.argv_str = ' '.join(argv)
        self.pointer = -1
        self._current_token = Token.START
        
        argv_str = ' '.join(argv)
        if argv_str.endswith('.exe'):
            self._prog_type = 'exe'
            self.prog_head = ' '.join(argv)
        elif ' -m ' in argv_str:
            self._prog_type = 'module'
            self.prog_head = ' '.join(argv[:2])
        else:
            self._prog_type = 'script'
            self.prog_head = ' '.join(argv[:1])
    
    def get_args(self, front_matter: T.ParamsInfo) -> t.Iterator[Arg]:
        ctx = Context()
        
        args: list[str]
        if self._prog_type == 'script':
            args = self.argv_seq[1:]
        elif self._prog_type == 'module':
            args = self.argv_seq[2:]
        else:
            args = []
        
        '''
        code of conduct:
            + forwardly using `continue`.
            + forwardly using `if` instead of `elif`.
        '''
        
        for i, arg in enumerate(args):
            if ctx.token in (Token.START, Token.READY):
                if arg.startswith('-'):
                    param_name: str
                    param_type: ParamType
                    
                    if arg.startswith('--'):
                        if arg.startswith('--not-'):
                            option_name = arg.replace('--not-', '--', 1)
                            param_name = front_matter['index'][option_name]
                            param_type = front_matter['kwargs'][param_name]
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                            yield Arg(i, param_name, Token.OPTION_NAME)
                            yield Arg(i, False, Token.OPTION_VALUE)
                            ctx.update(Token.READY)
                            continue
                        else:
                            option_name = arg
                            param_name = front_matter['index'][option_name]
                            param_type = front_matter['kwargs'][param_name]
                            if param_type == ParamType.FLAG:
                                yield Arg(i, param_name, Token.OPTION_NAME)
                                yield Arg(i, True, Token.OPTION_VALUE)
                                ctx.update(Token.READY)
                                continue
                    else:
                        assert arg.count('-') == 1
                        if arg[1:].isupper():
                            option_name = arg.lower()
                            param_name = front_matter['index'][option_name]
                            param_type = front_matter['kwargs'][param_name]
                            assert param_type in (ParamType.FLAG, ParamType.ANY)
                            yield Arg(i, param_name, Token.OPTION_NAME)
                            yield Arg(i, False, Token.OPTION_VALUE)
                            ctx.update(Token.READY)
                            continue
                        else:
                            option_name = arg
                            param_name = front_matter['index'][option_name]
                            param_type = front_matter['kwargs'][param_name]
                            if param_type == ParamType.FLAG:
                                yield Arg(i, param_name, Token.OPTION_NAME)
                                yield Arg(i, True, Token.OPTION_VALUE)
                                ctx.update(Token.READY)
                                continue
                                
                    yield Arg(i, param_name, Token.OPTION_NAME)
                    ctx.update(Token.OPTION_NAME)
                    ctx.stash_param_info(param_name, param_type)
                    continue
            
            # if ctx.token == Token.START:
            #     if mode == 'group'


@dataclass
class Arg:
    pos: int
    arg: t.Any
    token: Token


# noinspection PyArgumentList
class Token(Enum):
    HEAD = auto()
    START = auto()
    READY = auto()
    OPTION_NAME = auto()
    OPTION_VALUE = auto()


class Context:
    last_last_token: Token = None
    last_token: Token = None
    token: Token = None
    
    param_name: str
    param_type: T.ParamType
    
    last_last_arg: str = None
    last_arg: str = None
    arg: str = None
    
    def __init__(self):
        self.token = Token.START
    
    def update(self, token: Token):
        self.last_last_token = self.last_token
        self.last_token = self.token
        self.token = token
    
    def stash_param_info(self, name: str, type_: T.ParamType):
        self.param_name = name
        self.param_type = type_
