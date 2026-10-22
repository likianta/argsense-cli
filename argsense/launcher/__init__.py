"""
Build a desktop launcher (a `.exe` or a `.lnk`) out of a script.

The entry point is `python -m argsense create_launcher`; see
`.trae/specs/gui-desktop-launcher` for the design notes.
"""

from .config import LaunchConfig
from .creator import check_requirements
from .creator import create_launcher
from .exe import make_exe
from .lnk import make_lnk
from .path import ASSETS
from .path import DESKTOP
from .path import PKG_ROOT
