import os
from pathlib import Path


# DELETE: not used
def desktop_dir() -> str:
    """The desktop, following a redirect to onedrive when there is one."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer'
            r'\User Shell Folders',
        )
        value, _ = winreg.QueryValueEx(key, 'Desktop')
        return os.path.expandvars(value)
    except Exception:
        return str(Path.home() / 'Desktop')


_LOCAL_APPDATA = os.environ.get('LOCALAPPDATA', '').replace('\\', '/')
APPDATA = (
    '{}/argsense'.format(_LOCAL_APPDATA)
    if _LOCAL_APPDATA
    else os.path.expanduser('~/.argsense').replace('\\', '/')
)

DESKTOP = os.path.expanduser('~/Desktop').replace('\\', '/')

PKG_ROOT = os.path.normpath('{}/../../'.format(__file__)).replace('\\', '/')
assert PKG_ROOT.endswith('argsense')

ASSETS = '{}/launcher/assets'.format(PKG_ROOT)

RCEDIT = '{}/rcedit.exe'.format(ASSETS)
STUB = '{}/stub.exe'.format(ASSETS)
ICON = '{}/launcher.png'.format(ASSETS)
