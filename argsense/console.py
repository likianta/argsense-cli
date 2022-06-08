from rich import get_console

from . import config

__all__ = ['console']

console = get_console()

if config.WARNING_IF_RUNNING_ON_PYCHARM_CONSOLE \
        and console.color_system is None:
    # this may be happend when running in pycharm console.
    # i've tried this [link][1] but sadly it seems pycharm has removed its
    # support. so just remind me to tick the checkbox of "emulate output in
    # terminal" in pycharm configurations.
    # [1]: https://github.com/Textualize/rich/issues/206
    print('[argsense]/console.py:13  >>  warning: argsense cli does not '
          'perform well in pycharm console. \n'
          'you may tick the checkbox of '
          '"emulate output in terminal" in pycharm configurations to demolish '
          'this warning.')
    #   otherwise let developer turn off in config.
