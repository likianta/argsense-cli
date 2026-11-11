"""Regression test: numbers in scientific notation must parse as numbers.

run: python test/scientific_notation_number.py
"""
from argsense.converter import cval_2_val
from argsense.parser.args_parser import ParamType


def check(actual, expected):
    assert actual == expected, 'expected {!r}, got {!r}'.format(
        expected, actual
    )
    assert type(actual) is type(expected), 'expected type {}, got {}'.format(
        type(expected).__name__, type(actual).__name__
    )


# typed (NUMBER) params accept scientific notation.
check(cval_2_val('1e5', ParamType.NUMBER), 100000.0)
check(cval_2_val('2.5e-3', ParamType.NUMBER), 0.0025)
check(cval_2_val('-1E+3', ParamType.NUMBER), -1000.0)
# untyped (ANY) params auto-convert it too, instead of keeping a string.
check(cval_2_val('1e5', ParamType.ANY), 100000.0)
# pre-existing forms keep working.
check(cval_2_val('42', ParamType.NUMBER), 42)
check(cval_2_val('2.5', ParamType.NUMBER), 2.5)
check(cval_2_val('-3', ParamType.NUMBER), -3)
check(cval_2_val('0x1F', ParamType.NUMBER), 31)
check(cval_2_val('0b101', ParamType.NUMBER), 5)

print('ok: scientific notation parses as numbers')
