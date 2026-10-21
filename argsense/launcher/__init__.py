"""
Build a desktop launcher (a `.exe` or a `.lnk`) out of a script.

The entry point is `python -m argsense create_launcher`; see
`.trae/specs/gui-desktop-launcher` for the design notes.
"""

from .api import create

__all__ = ('create',)
