"""
What python has to do for a launcher that no launcher can do for it.

Starting a program is the easy half; the half that decides whether a desktop
user trusts the thing is what happens when the program *dies* before its
window exists. That is invisible without a console, so it is handled here:
an optional log file to read afterwards, and a dialog saying what went wrong.
"""

import os
import sys
import traceback
import typing as tp
from datetime import datetime
from pathlib import Path


class _Tee:
    """Write to the real stream and to the log, tolerating a missing one."""

    def __init__(self, primary: tp.Any, secondary: tp.TextIO) -> None:
        self._primary = primary
        self._secondary = secondary

    def write(self, text: str) -> int:
        try:
            if self._primary is not None:
                self._primary.write(text)
        except Exception:
            pass
        self._secondary.write(text)
        return len(text)

    def flush(self) -> None:
        try:
            if self._primary is not None:
                self._primary.flush()
        except Exception:
            pass
        self._secondary.flush()

    def isatty(self) -> bool:
        return False


_log: tp.Optional[tp.TextIO] = None
_log_path = ''

# the exit code that says "the user has already been told what went wrong".
# the stub leaves this one alone, so a failed start produces one dialog
# rather than two.
EXIT_REPORTED = 3


def setup(file: str = '') -> None:
    """
    Route a fatal error to a dialog, and keep stdout usable.

    `file` is where the log goes; an empty one means "keep no log", and the
    streams are then pointed at the null device. Sending them *somewhere* is
    not cosmetic: under a windowed interpreter they are `None` to begin with,
    and uvicorn's logging setup asks `sys.stdout.isatty()` while the server is
    being configured, so with no stdout at all the app dies before its window
    ever appears. Tying stdout to the log has a second use: the command output
    the log panel shows is then also kept on disk.
    """
    global _log, _log_path
    _log_path = file

    if file:
        path = Path(file)
        path.parent.mkdir(parents=True, exist_ok=True)
        _log = path.open('a', encoding='utf-8', buffering=1)
        _log.write(
            '\n--- {} ---\n'.format(datetime.now().isoformat(' ', 'seconds'))
        )
        _log.write('python : {}\n'.format(sys.executable))
        _log.write('argv   : {}\n'.format(' '.join(sys.argv)))
        _log.flush()
    else:
        _log = open(os.devnull, 'w', encoding='utf-8')

    sys.stdout = _Tee(sys.stdout, _log)
    sys.stderr = _Tee(sys.stderr, _log)
    sys.excepthook = _excepthook


def log(text: str) -> None:
    if _log is not None:
        _log.write(text)
        _log.flush()


def alert(message: str, title: str = 'argsense') -> None:
    """Say something out loud when there is no console to say it in."""
    if os.name != 'nt':
        stream = sys.__stderr__ or sys.stderr
        if stream is not None:
            stream.write('{}: {}\n'.format(title, message))
        return

    import ctypes

    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)


def _excepthook(
    type_: tp.Type[BaseException], value: BaseException, tb: tp.Any
) -> None:
    log(''.join(traceback.format_exception(type_, value, tb)))
    where = 'Log: {}'.format(_log_path) if _log_path else 'No log was kept.'
    alert(
        'The app failed to start.\n\n{}: {}\n\n{}'.format(
            type_.__name__, value, where
        )
    )
    # leave without letting the exception print itself again, and with the
    # code the stub recognises as "already reported".
    os._exit(EXIT_REPORTED)
