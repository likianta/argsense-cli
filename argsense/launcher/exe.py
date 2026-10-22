"""
Make the `.exe` form: the stub, a payload, and a face.

The stub is copied rather than linked to, because the file is meant to be
moved to a desktop and double-clicked there.
"""

import shutil
import struct
import subprocess

from .config import LaunchConfig
from .path import RCEDIT
from .path import STUB


def make_exe(config: LaunchConfig, file_o: str) -> str:
    shutil.copy2(STUB, file_o)
    # the icon goes on before the payload: rcedit rebuilds the resource section,
    # and in doing so throws away anything appended after the last section --
    # which is exactly where the payload lives.
    if config.icon:
        _rcedit(file_o, '--set-icon', config.icon)
    _append_payload(file_o, config)
    return file_o


def _append_payload(file_exe: str, config: LaunchConfig) -> None:
    Payload().append_payload(file_exe, config)


def _rcedit(file_exe: str, *args: str) -> None:
    result = subprocess.run(
        (RCEDIT, file_exe, *args), capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            'rcedit failed ({}): {} {}'.format(
                result.returncode, result.stdout.strip(), result.stderr.strip()
            )
        )


class Payload:
    MAGIC = b'ARGSENSE'
    FOOTER = len(MAGIC) + 4

    def append_payload(self, file_exe: str, config: LaunchConfig) -> None:
        """
        Write `config` after the last PE section, replacing any earlier one.
        """
        with open(file_exe, 'rb') as f:
            data = f.read()
        data = self.strip_payload(data)
        payload = config.to_text().encode('utf-8')
        with open(file_exe, 'wb') as f:
            f.write(
                data + payload + struct.pack('<I', len(payload)) + self.MAGIC
            )

    def strip_payload(self, data: bytes) -> bytes:
        try:
            payload = self._payload_of(data)
        except ValueError:
            return data
        return data[: len(data) - self.FOOTER - len(payload)]

    def _payload_of(self, data: bytes) -> bytes:
        if len(data) < self.FOOTER or not data.endswith(self.MAGIC):
            raise ValueError('no launcher payload in this file')
        length = struct.unpack_from('<I', data, len(data) - self.FOOTER)[0]
        start = len(data) - self.FOOTER - length
        if start < 0:
            raise ValueError('the launcher payload is truncated')
        return data[start : len(data) - self.FOOTER]
