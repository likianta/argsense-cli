import sys


class OrigSysArgvInfo:
    """ wrapper for `sys.org_argv`. """
    
    def __init__(self) -> None:
        self._argv = sys.orig_argv
        self._is_package_mode = self._argv[1] == '-m'
        self.main_args = (
            self._argv[3:] if self._is_package_mode else self._argv[2:]
        )
        self.exec_path = self._argv[0]
        self.target = self._argv[2] if self._is_package_mode else self._argv[1]
        self.command = ''
        for x in self.main_args:
            if not x.startswith('-'):
                self.command = x  # FIXME: not reliable
                break
        

argv_info = OrigSysArgvInfo()
