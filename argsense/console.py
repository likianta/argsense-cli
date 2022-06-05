from rich import get_console

__all__ = ['console']

console = get_console()

if console.color_system is None:
    # this may happend when running in pycharm on windows platform.
    # i've tried this [link][1] but sadly it seems pycharm has removed its
    # support. so just remind me to tick the checkbox of "emulate output in
    # terminal" in pycharm configurations.
    # [1]: https://github.com/Textualize/rich/issues/206
    print('[argsense]/console.py:13  >>  warning: argsense cli does not '
          'perform well in pycharm on windows platform.')
