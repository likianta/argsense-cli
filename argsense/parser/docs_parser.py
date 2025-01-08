import re
import typing as t
from textwrap import dedent

if __name__ == '__main__':
    from .func_parser import FuncInfo


class T:
    # noinspection PyTypedDict
    DocsInfo = t.TypedDict('DocsInfo', {
        'desc'  : str,
        'args'  : t.Dict[
            # e.g.
            #   {
            #       'aaa': {
            #           'cname': 'aaa',
            #           'cshort': '-a',
            #           'desc': 'the description of aaa.'
            #       }, ...
            #   }
            str, t.TypedDict('ArgInfo', {
                'cname' : str,
                'cshort': str,
                'desc'  : str,
            })
        ],
        'kwargs': t.Dict[
            # e.g.
            #   {
            #       'bbb': {
            #           'cname': '--bbb',
            #           'cshort': '-b',
            #           'desc': 'the description of bbb.'
            #       }, ...
            #   }
            str, t.TypedDict('OptInfo', {
                'cname' : str,
                'cshort': str,
                'desc'  : str,
            })
        ]
    })


def parse_docstring(doc: str, funsig: 'FuncInfo') -> T.DocsInfo:
    """
    doc: /docs/how-to-parse-docstring.md
    params:
        funsig: function signature.
    """
    from ..converter import name_2_cname
    
    out: T.DocsInfo = {
        'desc'  : '',
        'args'  : {},
        'kwargs': {},
    }
    
    if '\n' not in doc:
        '''
        example:
            def foo(...):
                """ blabla. """
        '''
        out['desc'] = doc.strip()
        return out
    
    doc = dedent(doc).strip()
    doc = re.sub(r' - *\n +', ' ', doc)
    
    flag = 'INIT'
    temp_str: str = ''
    temp_dict: t.Optional[dict] = None
    
    def accumulate_lines(line: str) -> None:
        nonlocal temp_str
        if line.endswith(' -'):
            temp_str += line[:-2]
        else:
            temp_str += line + '\n'
            
    def add_extra_param(line: str) -> None:
        add_param(line[4:])
    
    def add_param(line: str) -> None:
        nonlocal temp_str, temp_dict
        
        # print(line, ':v')
        m = re.match(r' {4}(\*?)(\w+)(?: \((-\w\d*)\))?:(?: (.*))?', line)
        #                  ~~~~1~~~~2      ~~~~~~~3         ~~~4
        has_asterisk = bool(m.group(1))
        param_name = m.group(2)
        param_short = m.group(3) or ''
        leading_text = m.group(4) or ''
        
        if has_asterisk:
            assert param_short == ''
            temp_dict = out['args']['*'] = {
                'cname' : funsig.args['*']['cname'],
                'cshort': '',
                'desc'  : '',
            }
        else:
            if param_name in funsig.args:
                temp_dict = out['args'][param_name] = {
                    'cname' : funsig.args[param_name]['cname'],
                    'cshort': param_short,
                    'desc'  : '',
                }
            elif param_name in funsig.kwargs:
                temp_dict = out['kwargs'][param_name] = {
                    'cname' : funsig.kwargs[param_name]['cname'],
                    'cshort': param_short,
                    'desc'  : '',
                }
            else:
                if funsig.has_var_kwargs:
                    temp_dict = out['kwargs'][param_name] = {
                        'cname' : name_2_cname(param_name, 'opt'),
                        'cshort': param_short,
                        'desc'  : '',
                    }
                else:
                    raise Exception(
                        'docstring parsing failed: "{}" is not in the '
                        'signature of function `{}`.'.format(
                            param_name, funsig.name
                        )
                    )
        
        assert temp_str == ''
        accumulate_lines(leading_text)
    
    def finalize_desc() -> None:
        nonlocal temp_str
        out['desc'] = temp_str.strip()
        temp_str = ''
    
    def finalize_param_desc() -> None:
        nonlocal temp_str, temp_dict
        assert temp_dict
        temp_dict['desc'] = temp_str.strip()
        temp_dict = None
        temp_str = ''
    
    def is_extra_param_field(line: str) -> bool:
        """
        example:
              | def foo(...):
              |     '''
              |     params:
              |         aaa: the description text.
              |         bbb (-b): the description text.
              |         **kwargs:
            * |             ccc: the description text.
            * |             ddd (-d): the description text.
              |     '''
        """
        return bool(re.match(r' {8}\w+(?: \(-\w\))?:', line))
    
    def is_new_field(line: str) -> bool:
        if line.startswith(' '):
            return False
        if line.endswith(':'):
            return True
        return False
    
    def is_param_field(line: str) -> int:
        """
        diagram:
              | def foo(...):
              |     '''
              |     params:
            * |         aaa: the description text.
            * |         *args: the description text.
            * |         **kwargs:
              |             aaa: the description text.
              |     '''
        """
        if bool(re.match(r' {4}\w+(?: \(-\w\))?:', line)):
            return 1
        elif bool(re.match(r' {4}\*\w+:.*', line)):
            return 2
        elif bool(re.match(r' {4}\*\*\w+: *', line)):
            return 3
        else:
            return 0
    
    def is_params_field(line: str) -> bool:
        return line.lower() in (
            'params:',  # recommended
            'args:', 'kwargs:', 'opts:', 'options:',
        )
    
    for i, line in enumerate(doc.splitlines()):
        if flag == 'INIT':
            if line:
                if is_new_field(line):
                    if line.lower() in ('argsense:', 'help:'):
                        flag = 'STANDALONE_DESC'
                    elif is_params_field(line):
                        flag = 'PARAMS'
                    else:
                        assert not temp_str
                        flag = 'DESC_DONE'
                else:
                    assert not temp_str
                    accumulate_lines(line)
                    flag = 'TOP_DESC'
            else:
                assert not temp_str
        
        elif flag == 'DESC_DONE':
            if is_params_field(line):
                flag = 'PARAMS'
        
        elif flag == 'EXTRA_PARAM_DESC':
            if not line.startswith(' '):
                finalize_param_desc()
                flag = 'OVER'
                break
            elif is_param_field(line):
                finalize_param_desc()
                add_param(line)
                flag = 'PARAM_DESC'
            elif is_extra_param_field(line):
                finalize_param_desc()
                add_extra_param(line)
            else:
                assert line == '' or line.startswith(' ' * 12)
                accumulate_lines(line[12:])
            
        elif flag == 'EXTRA_PARAMS':
            if line:
                if not line.startswith(' '):
                    finalize_param_desc()
                    flag = 'OVER'
                    break
                elif is_param_field(line):
                    finalize_param_desc()
                    add_param(line)
                    flag = 'PARAM_DESC'
                else:
                    assert line.startswith(' ' * 8)
                    assert is_extra_param_field(line)
                    add_extra_param(line)
                    flag = 'EXTRA_PARAM_DESC'
        
        elif flag == 'PARAM_DESC':
            if not line.startswith(' '):
                finalize_param_desc()
                flag = 'OVER'
                break
            elif x := is_param_field(line):
                finalize_param_desc()
                if x == 1 or x == 2:
                    add_param(line)
                else:
                    flag = 'EXTRA_PARAMS'
            else:
                assert line == '' or line.startswith(' ' * 8)
                accumulate_lines(line[8:])
        
        elif flag == 'PARAMS':
            if line:
                if not line.startswith(' '):
                    finalize_param_desc()
                    flag = 'OVER'
                    break
                else:
                    assert line.startswith('    ')
                    if x := is_param_field(line):
                        if x == 1 or x == 2:
                            add_param(line)
                            flag = 'PARAM_DESC'
                        else:
                            flag = 'EXTRA_PARAMS'
                    else:
                        raise Exception(i, line)
        
        elif flag == 'STANDALONE_DESC':
            if not line.startswith(' '):
                finalize_desc()
                flag = 'DESC_DONE'
            else:
                assert line == '' or line.startswith(' ' * 4)
                accumulate_lines(line[4:])
        
        elif flag == 'TOP_DESC':
            if is_new_field(line):
                finalize_desc()
                if is_params_field(line):
                    flag = 'PARAMS'
                else:
                    flag = 'DESC_DONE'
            else:
                accumulate_lines(line)
    
    # print(flag, ':v1')
    if flag in ('TOP_DESC', 'STANDALONE_DESC'):
        finalize_desc()
    elif flag in ('PARAM_DESC', 'EXTRA_PARAM_DESC'):
        finalize_param_desc()
    else:
        assert flag in ('DESC_DONE', 'OVER'), flag
    
    return out
