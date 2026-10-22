"""
What a launcher is told to start, and how that travels inside an `.exe`.

A tiny binary carries no room for a config file: the thing gets copied to a
desktop and double-clicked, and anything sitting next to it would be left
behind. So the config is appended after the last PE section, where the loader
never looks -- the same trick self-extracting archives use. Copying the file
copies the config.

Layout, from the end of the file backwards:

    [ payload ][ u32 payload length ][ "ARGSNCHR" ]

The payload is `key=value` lines, LF separated. Windows paths cannot contain
a newline, so no escaping is needed -- and the stub parses it with `split`
calls instead of a json parser.
"""

import typing as tp
from dataclasses import dataclass

# the separator for `args`: a unit separator, which no sane command line
# argument contains, so the list survives the round trip.
ARGS_SEP = '\x1f'


@dataclass
class LaunchConfig:
    """
    One launcher's settings.

    `python` is the interpreter to start. `script` is a file to hand it, or
    `module` a dotted module to run with `-m`; exactly one of the two is set.
    `cwd` is the directory to run in, and `port` is 0 for "pick a free one at
    run time".
    """

    python: str
    script: str
    cwd: str
    args: tp.Tuple[str, ...] = ()
    name: str = ''
    module: str = ''
    log: str = ''
    icon: str = ''
    port: int = 0
    window_size: tp.Optional[tp.Tuple[int, int]] = None
    window_title: str = ''
    show_console: bool = False

    def to_text(self) -> str:
        lines = [
            'name={}'.format(self.name),
            'python={}'.format(self.python),
            'script={}'.format(self.script),
            'module={}'.format(self.module),
            'cwd={}'.format(self.cwd),
            'args={}'.format(ARGS_SEP.join(self.args)),
            'log={}'.format(self.log),
            'icon={}'.format(self.icon),
            'port={}'.format(self.port),
            'window_size={}'.format(
                LaunchConfig.size_tuple_to_str(self.window_size)
            ),
            'window_title={}'.format(self.window_title),
            'show_console={}'.format('1' if self.show_console else '0'),
        ]
        return '\n'.join(lines)

    @classmethod
    def from_text(cls, text: str) -> 'LaunchConfig':
        data = {}
        for line in text.split('\n'):
            if not line:
                continue
            key, _, value = line.partition('=')
            data[key] = value
        args = data.get('args', '')
        return cls(
            python=data['python'],
            script=data['script'],
            cwd=data['cwd'],
            args=tuple(args.split(ARGS_SEP)) if args else (),
            name=data.get('name', ''),
            module=data.get('module', ''),
            log=data.get('log', ''),
            icon=data.get('icon', ''),
            port=int(data.get('port', '0')),
            window_size=data.get('window_size', None)
            and LaunchConfig.size_str_to_tuple(data['window_size']),
            window_title=data.get('window_title', ''),
            show_console=data.get('show_console', '0') == '1',
        )

    @staticmethod
    def size_str_to_tuple(size: str):
        w, _, h = size.partition('x')
        return (int(w), int(h))

    @staticmethod
    def size_tuple_to_str(size: tp.Optional[tp.Tuple[int, int]]):
        return '{}x{}'.format(*size) if size else ''
