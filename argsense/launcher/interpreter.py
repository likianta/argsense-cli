import os
import shutil
import struct
import sys


def get_interpreter_path(show_console: bool):
    if show_console:
        return sys.executable
    else:
        pythonw = get_pythonw()
        assert is_real_pythonw(pythonw)
        return pythonw


def get_pythonw():
    file = os.path.normpath('{}/../pythonw.exe'.format(sys.executable))
    assert os.path.exists(file)
    return file


def is_real_pythonw(pythonw):
    return _pe_subsystem(pythonw) == 2


def fix_pythonw():
    fake_pythonw = '{}/pythonw.exe'.format(os.path.dirname(sys.executable))
    real_pythonw = '{}/pythonw.exe'.format(
        os.path.dirname(getattr(sys, '_base_executable'))
    )
    assert is_real_pythonw(real_pythonw)
    shutil.copy2(real_pythonw, fake_pythonw)


def _pe_subsystem(file: str) -> int:
    with open(file, 'rb') as f:
        dos_header = f.read(0x40)
        pe_offset = struct.unpack_from('<I', dos_header, 0x3C)[0]
        f.seek(pe_offset + 24 + 68)
        return struct.unpack('<H', f.read(2))[0]
