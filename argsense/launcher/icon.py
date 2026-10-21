"""
Turn the caller's picture into an icon windows can actually use.

A `.ico` holds one image per size, and windows picks a different one per
place: 16px in a title bar, 32 in the taskbar, 48+ in explorer's views. Saving
a single 256px frame makes the small ones blurry, so every size is written.
"""

import typing as tp
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 128, 256)


def to_ico(file_i: tp.Union[str, Path], file_o: tp.Union[str, Path]) -> Path:
    """
    Write `file_i` (png, or an ico that is already fine) as a multi-size ico.

    A `.ico` input is returned as is: it already carries whatever sizes its
    author chose, and re-encoding it would only lose them.
    """
    source = Path(file_i)
    target = Path(file_o)
    if source.suffix.lower() == '.ico':
        return source

    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            'converting an icon needs pillow: pip install pillow'
        ) from None

    image = Image.open(source).convert('RGBA')
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format='ICO', sizes=[(x, x) for x in SIZES])
    return target
