"""
Turn the caller's picture into an icon windows can actually use.

A `.ico` holds one image per size, and windows picks a different one per
place: 16px in a title bar, 32 in the taskbar, 48+ in explorer's views. Saving
a single 256px frame makes the small ones blurry, so every size is written.
"""


def png_to_ico(file_i: str, file_o: str) -> str:
    """
    Write `file_i` (png, or an ico that is already fine) as a multi-size ico.

    A `.ico` input is returned as is: it already carries whatever sizes its
    author chose, and re-encoding it would only lose them.
    """
    try:
        from PIL import Image
    except ImportError as e:
        raise Exception(
            'converting an icon needs pillow: `pip install pillow`'
        ) from e

    img = Image.open(file_i).convert('RGBA')
    img.save(
        file_o,
        format='ICO',
        sizes=[(x, x) for x in (16, 24, 32, 48, 64, 128, 256)],
    )
    return file_o
