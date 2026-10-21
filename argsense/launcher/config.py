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

import struct
import typing as tp
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

MAGIC = b'ARGSNCHR'
FOOTER = len(MAGIC) + 4
# the separator for `args`: a unit separator, which no sane command line
# argument contains, so the list survives the round trip.
ARGS_SEP = '\x1f'


@dataclass
class LaunchConfig:
    """
    One launcher's settings.

    `python` is the interpreter to start, `script` the file to hand it, `cwd`
    the directory to run in. `port` is 0 for "pick a free one at run time".
    """

    python: str
    script: str
    cwd: str
    args: tp.Tuple[str, ...] = ()
    name: str = ''
    log: str = ''
    icon: str = ''
    port: int = 0
    window_size: str = ''
    window_title: str = ''
    show_console: bool = False

    def to_text(self) -> str:
        lines = [
            'name={}'.format(self.name),
            'python={}'.format(self.python),
            'script={}'.format(self.script),
            'cwd={}'.format(self.cwd),
            'args={}'.format(ARGS_SEP.join(self.args)),
            'log={}'.format(self.log),
            'icon={}'.format(self.icon),
            'port={}'.format(self.port),
            'window_size={}'.format(self.window_size),
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
            log=data.get('log', ''),
            icon=data.get('icon', ''),
            port=int(data.get('port', '0')),
            window_size=data.get('window_size', ''),
            window_title=data.get('window_title', ''),
            show_console=data.get('show_console', '0') == '1',
        )


@dataclass
class Built:
    """What `build` produced, so the caller can print or test it."""

    path: Path
    config: LaunchConfig
    extra: tp.Dict[str, Path] = field(default_factory=dict)


def append_payload(file_exe: tp.Union[str, Path], config: LaunchConfig) -> None:
    """Write `config` after the last PE section, replacing any earlier one."""
    path = Path(file_exe)
    data = path.read_bytes()
    data = _strip_payload(data)
    payload = config.to_text().encode('utf-8')
    path.write_bytes(data + payload + struct.pack('<I', len(payload)) + MAGIC)


def read_payload(file_exe: tp.Union[str, Path]) -> LaunchConfig:
    path = Path(file_exe)
    return LaunchConfig.from_text(
        _payload_of(path.read_bytes()).decode('utf-8')
    )


def has_payload(file_exe: tp.Union[str, Path]) -> bool:
    try:
        _payload_of(Path(file_exe).read_bytes())
    except ValueError:
        return False
    return True


def _payload_of(data: bytes) -> bytes:
    if len(data) < FOOTER or not data.endswith(MAGIC):
        raise ValueError('no launcher payload in this file')
    length = struct.unpack_from('<I', data, len(data) - FOOTER)[0]
    start = len(data) - FOOTER - length
    if start < 0:
        raise ValueError('the launcher payload is truncated')
    return data[start : len(data) - FOOTER]


def _strip_payload(data: bytes) -> bytes:
    try:
        payload = _payload_of(data)
    except ValueError:
        return data
    return data[: len(data) - FOOTER - len(payload)]
