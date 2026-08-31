@namespace("numbers")

from fractions import Fraction
from decimal import DecimalValue
from cmath import ComplexValue

# CPython's `numbers` module is an ABC tower (Number > Complex > Real >
# Rational > Integral) meant for `isinstance(x, numbers.Real)`-style duck
# typing against values of unknown concrete type. Promethium is statically
# typed, so there is no dynamic value to `isinstance`-check against an ABC
# in the first place by the time one of these could be called — the
# caller already knows whether they have an `int`, a `float`, a `Fraction`,
# a `DecimalValue`, or a `ComplexValue`. What *is* useful to port is the
# classification matrix itself, as a set of concrete overload sets, one
# function per tier, so code that's generic over "a numeric value" for
# some purpose (formatting, validation) can still ask "is this tier X"
# without inventing its own copy of the table.
#
# The table below is not a guess — it's transcribed from live CPython
# 3.12 (`isinstance(v, numbers.X)` for `int`, `float`,
# `fractions.Fraction`, `decimal.Decimal`, `complex`). The one surprising
# entry: `decimal.Decimal` is NOT registered against any `numbers` ABC in
# real CPython (a long-standing, deliberate stdlib decision — Decimal
# predates full ABC registration and was never retrofitted), so
# `DecimalValue` here correctly returns `False` across the board, same as
# CPython's `Decimal`.
#
# Each function is overloaded per concrete type rather than written once
# over a `dynamic`/`typing.Any` parameter — consistent with this project's
# established pattern (see `asyncio.py`'s `run_int`/`run_str`/...) of
# preferring concrete overloads to dynamic dispatch, which has repeatedly
# surfaced real compiler bugs this pass (see
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`).
# These are plain statically-typed overloads, no dynamic dispatch at all,
# so none of that fragility applies here.


def is_complex(x: int) -> bool:
    return True

def is_complex(x: float) -> bool:
    return True

def is_complex(x: Fraction) -> bool:
    return True

def is_complex(x: DecimalValue) -> bool:
    return False

def is_complex(x: ComplexValue) -> bool:
    return True


def is_real(x: int) -> bool:
    return True

def is_real(x: float) -> bool:
    return True

def is_real(x: Fraction) -> bool:
    return True

def is_real(x: DecimalValue) -> bool:
    return False

def is_real(x: ComplexValue) -> bool:
    return False


def is_rational(x: int) -> bool:
    return True

def is_rational(x: float) -> bool:
    return False

def is_rational(x: Fraction) -> bool:
    return True

def is_rational(x: DecimalValue) -> bool:
    return False

def is_rational(x: ComplexValue) -> bool:
    return False


def is_integral(x: int) -> bool:
    return True

def is_integral(x: float) -> bool:
    return False

def is_integral(x: Fraction) -> bool:
    return False

def is_integral(x: DecimalValue) -> bool:
    return False

def is_integral(x: ComplexValue) -> bool:
    return False
