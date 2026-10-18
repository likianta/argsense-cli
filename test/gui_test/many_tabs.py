"""
A group with more tabs than fit on one line.

`depsland`'s `__main__.py` looks like this: a bare `cli.run()` over a module of
a dozen-odd public functions, so the form gets one tab per command -- and the
tabs together are wider than the card. The point of this script is the tab
bar, not the commands, so they all do the same nothing.

Run it (from the project root) and open the address it prints:

    python test/gui_test/many_tabs.py

The window is the narrow one here (a single group, so there is no sidebar to
make it wide), which is the worst case for the tab bar. What to look at:

- the tab bar must stay inside the card -- no tab spilling past its edge and
  no horizontal scrollbar on the page;
- the bar itself scrolls sideways instead, and the underline still sits under
  the active tab after a switch;
- the tab you pick from the far end scrolls itself into view.
"""

from argsense import cli


def about() -> None:
    """Show the version and the home page."""


def self_location() -> None:
    """Print where this app is installed."""


def welcome(confirm_close: bool = False) -> None:
    """Print the welcome banner.

    params:
        confirm_close: Ask before closing the window.
    """


def init(target: str = '.', app_name: str = '') -> None:
    """Create a project in `target`.

    params:
        target: The directory to create it in.
        app_name: The name to give it.
    """


def build(version: str = '', keep_build: bool = False) -> None:
    """Build the project into a wheel.

    params:
        version: The version to stamp on it.
        keep_build: Keep the intermediate files.
    """


def publish(version: str = '', token: str = '') -> None:
    """Upload the wheel to the index.

    params:
        version: The version to upload.
        token: The index token.
    """


def install(appid: str, upgrade: bool = True, reinstall: bool = False) -> None:
    """Install an app.

    params:
        appid: The app to install.
        upgrade: Upgrade it if it is already there.
        reinstall: Remove it first, even if it is up to date.
    """


def upgrade(appid: str) -> None:
    """Upgrade an app to the latest version.

    params:
        appid: The app to upgrade.
    """


def uninstall(appid: str, version: str = '') -> None:
    """Remove an app.

    params:
        appid: The app to remove.
        version: The version to remove (all of them by default).
    """


def run(appid: str, args: str = '') -> None:
    """Run an installed app.

    params:
        appid: The app to run.
        args: Extra arguments for it.
    """


def runx(exe: str, args: str = '') -> None:
    """Run an executable in an isolated environment.

    params:
        exe: The executable to run.
        args: Extra arguments for it.
    """


def list_apps(pattern: str = '') -> None:
    """List the installed apps.

    params:
        pattern: Only show the ones matching it.
    """


def show(appid: str, version: str = '') -> None:
    """Show an app's details.

    params:
        appid: The app to show.
        version: The version to show.
    """


def view_manifest(manifest: str = '.') -> None:
    """Print a manifest as JSON.

    params:
        manifest: The manifest file, or a directory holding one.
    """


def show_packages(name: str = '', size: bool = False) -> None:
    """List the packages an app depends on.

    params:
        name: Only show the packages matching it.
        size: Show how much room each one takes.
    """


def get_package_size(name: str, deep: bool = False) -> None:
    """Measure the room a package takes on disk.

    params:
        name: The package to measure.
        deep: Walk its dependencies too.
    """


def open_readme(appid: str) -> None:
    """Open an app's readme in the browser.

    params:
        appid: The app whose readme to open.
    """


if __name__ == '__main__':
    cli.run(mode='gui')
