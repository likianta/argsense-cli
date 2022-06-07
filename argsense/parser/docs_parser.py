import re
import typing as t
from enum import Enum
from enum import auto
from textwrap import dedent

from ..converter import name_2_cname

__all__ = ['parse_docstring']


class T:
    _ParamName = str
    _CliName = str  # e.g. 'ARGUMENT', '--option'
    _CliName2 = str  # e.g. '--option,-o'
    _Desc = str  # the description
    
    # noinspection PyTypedDict
    DocsInfo = t.TypedDict('DocsInfo', {
        'desc'  : _Desc,  # noqa
        'args'  : t.Dict[_ParamName, t.TypedDict('ArgInfo', {
            'cname': _CliName,
            'desc' : _Desc,
        })],
        'kwargs': t.Dict[_ParamName, t.TypedDict('OptInfo', {
            'cname': _CliName2,
            'desc' : _Desc,
        })]
    })


def parse_docstring(docstring: str) -> T.DocsInfo:
    """
    example:
        def foo(aaa: str, is_bbb: bool, ccc: int = 1, is_ddd: bool = False):
            '''
            do something.
            
            args:
                aaa: the description text.
                is_bbb: the description text.
                    the second line.
                    the third -
                    line.
            
            kwargs:
                ccc: the description text.
                is_ddd (-d): the description text.
            '''
        it will return:
            {
                'desc': 'do something.',
                'args': {
                    'aaa': {
                        'cname': 'AAA',
                        'desc': 'the description text.',
                    },
                    'is_bbb': {
                        'cname': 'IS-BBB',
                        'desc': 'the description text.\nthe second line.\n'
                                'the third line.',
                    },
                },
                'kwargs': {
                    'ccc': {
                        'cname': '--ccc',
                        'desc': 'the description text.',
                    },
                    'is_ddd': {
                        'cname': '--is-ddd,-d',
                        'desc': 'the description text.',
                    }
                }
            }
    """
    result: T.DocsInfo = {
        'desc'  : '',
        'args'  : {},
        'kwargs': {},
    }
    
    # sanitize docstring
    if len(docstring) >= 2 and (docstring[0] == ' ' and docstring[1] != ' '):
        docstring = '   ' + docstring
    docstring = dedent(docstring).strip()
    
    class Scope(Enum):
        ROOT = 'desc'
        ARGS = 'args'
        KWARGS = 'kwargs'
        OTHER = auto()
    
    # walk through lines
    scope = Scope.ROOT
    args_pending_line_pattern = re.compile(r'^([\w]+): ?(.*)')
    #   example: 'apple: the description text.'
    #             ~~~~1  ~~~~~~~~~~~~~~~~~~~~2
    kwargs_pending_line_pattern = re.compile(
        r'^([\w-]+)(?: \(([-,\w]+)\))?: ?(.*)')
    #   example: 'aaa_bbb (-ab): the description text.'
    #             ~~~~~~1  ~~2   ~~~~~~~~~~~~~~~~~~~~3
    last_key = ''
    
    for line in docstring.splitlines():
        line = line.rstrip()
        if not line:
            continue
        
        # determine scope
        if line.lower().startswith(('args:', 'arguments:')):
            scope = Scope.ARGS
            continue
        elif line.lower().startswith(('kwargs:', 'opt:', 'opts:', 'options:')):
            scope = Scope.KWARGS
            continue
        else:
            if scope == Scope.ROOT:
                pass
            elif scope == Scope.OTHER:
                continue
            elif not line.startswith('    '):
                scope = Scope.OTHER
                continue
        
        if scope == Scope.ROOT:
            result['desc'] = _feed_line(line, result['desc'])
        elif scope in (Scope.ARGS, Scope.KWARGS):
            node = result[scope.value]  # noqa
            line = line[4:]  # dedent 4 spaces
            
            pattern = args_pending_line_pattern if scope == Scope.ARGS \
                else kwargs_pending_line_pattern
            if m := pattern.match(line):
                if scope == Scope.ARGS:
                    name = m.group(1)
                    cname = name_2_cname(name, style='arg')
                    leading_text = m.group(2)
                else:
                    name = m.group(1)
                    long_option = name_2_cname(name, style='opt')
                    short_option = m.group(2) or ''
                    cname = f'{long_option},{short_option}'.rstrip(',')
                    leading_text = m.group(3)
                
                node[name] = {'cname': cname, 'desc': leading_text}
                last_key = name
                continue
            else:
                line = line[4:]
                node[last_key]['desc'] = _feed_line(
                    line, node[last_key]['desc']
                )
    
    return result


def _feed_line(line: str, refer: str = ''):
    # note: param `line` has been stripped.
    if not refer:
        return line
    if refer.endswith(' -'):
        return refer[:-1] + line
    else:
        return refer + '\n' + line
