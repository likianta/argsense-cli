"""
if user both imports `pyside6` and `textual`, there will be an ImportError says:
    "ImportError: Package 'textual.widgets' has no class '__wrapped__'".
this because `textual.widgets` uses a lazy loading mechanism, while `pyside6`
has a modified import mechanism, that inspects `__wrapped__` attribute from
`textual.widgets` module, the module blames strongly so ImportError is raised.

reproduced code:
    # save the two lines in "test.py" and run.
    from PySide6.QtWidgets import QApplication, QWidget
    from textual.widgets import Button
ps: if you exchange the order of the two lines, the error will disappear.
"""


def fake_run(*_, **__) -> None:
    raise ImportError(
        'textual package is not usable in pyside6 environment.',
        f'see details in docstring at "{__file__}"'
    )
