from . import launcher
from .cli import CommandLineInterface


def create_launcher(
    script: str,
    result: str = '',
    kind: str = 'auto',
    title: str = '',
    size: str = '',
    icon: str = '',
    port: int = 0,
    show_console: bool = False,
    add_to_desktop_shortcut: bool = True,
) -> None:
    """
    Wrap a script in a launcher that can be double-clicked.

    Args:
        script (-s): The path of the ".py" file to start.
        result (-t):
            Where to write the launcher.

            If left empty, it goes next to the script and takes the script's -
            name. Given just ".exe" or ".lnk", it does the same, with that -
            suffix. Given a path ending in ".exe" or ".lnk", it is created or -
            overwritten exactly there. Given a directory, it becomes -
            `<directory>/<script name>.<kind>`, and that directory has to -
            exist already.
        kind (-k):
            'exe' or 'lnk'. 'auto', the default, follows the suffix of -
            `result` when there is one. Otherwise it prefers 'exe' when an -
            icon was given, and when the two binaries are in place; without -
            either, it falls back to 'lnk'.

            Naming a kind that contradicts the suffix of `result` is an error.
        title: The text in the window's title bar.
        size (-z): The window size, written as "980x820".
        icon (-i): A ".png" or ".ico" file. Both for launcher and window.
        port (-p):
            The port to serve on. The default, 0, picks a free one, which is -
            what you want when two launchers may run at once.
        show_console (-c): Keep a console window open, for debugging.
        add_to_desktop_shortcut (-d):
            Also leave a shortcut on the desktop, unless `result` already -
            points there. This is on by default, so pass `-D` to turn it off.
    """
    for path in launcher.create(
        script,
        result=result,
        kind=kind,
        window_title=title,
        window_size=size,
        window_icon=icon,
        port=port,
        show_console=show_console,
        add_to_desktop_shortcut=add_to_desktop_shortcut,
    ):
        print(path)


if __name__ == '__main__':
    # python -m argsense -h
    # python -m argsense create_launcher -h
    CommandLineInterface().run((create_launcher,))
