@namespace("decimal")

# A small, opt-in subset of Python's decimal module: a fixed-point
# `DecimalValue` (unscaled integer + scale, value = unscaled / 10^scale) —
# not CPython's arbitrary-precision, context-configurable `Decimal`, but
# exact base-10 arithmetic within the range of Promethium's `int`, which is
# the useful property `decimal` is normally reached for (avoiding float's
# binary-fraction rounding, e.g. for money).
#
# Deliberately not named `Decimal`: .NET's own `System.Decimal` is a
# prominent built-in value type, and `class Random:` already confirmed
# (see `random.py`) that a Promethium class sharing a short name with a
# native type risks — at minimum — a Toffee-only compile failure. Named
# `DecimalValue` preemptively rather than spending a build cycle finding
# out the same way `Random` did.
#
# Arithmetic dunders are explicit-call-only (`a.__add__(b)`, not `a + b`),
# same as `Counter`/`Fraction` — Promethium doesn't lower operators to
# dunder methods on a class. No `__str__`: converting `int` to `str` needs
# a native per-platform call that hasn't been established anywhere in this
# codebase yet (see `fractions.py`'s identical note).


class DecimalValue:
    unscaled: int
    scale: int

    def __init__(self, unscaled: int, scale: int):
        self.unscaled = unscaled
        self.scale = scale

    def __init__(self, value: int):
        self.unscaled = value
        self.scale = 0

    def __add__(self, other: DecimalValue) -> DecimalValue:
        if self.scale == other.scale:
            return DecimalValue(self.unscaled + other.unscaled, self.scale)
        if self.scale > other.scale:
            factor: int = _pow10(self.scale - other.scale)
            return DecimalValue(self.unscaled + other.unscaled * factor, self.scale)
        factor: int = _pow10(other.scale - self.scale)
        return DecimalValue(self.unscaled * factor + other.unscaled, other.scale)

    def __neg__(self) -> DecimalValue:
        return DecimalValue(-self.unscaled, self.scale)

    def __sub__(self, other: DecimalValue) -> DecimalValue:
        return self.__add__(other.__neg__())

    def __mul__(self, other: DecimalValue) -> DecimalValue:
        return DecimalValue(self.unscaled * other.unscaled, self.scale + other.scale)

    def __eq__(self, other: DecimalValue) -> bool:
        difference: DecimalValue = self.__sub__(other)
        return difference.unscaled == 0

    def __lt__(self, other: DecimalValue) -> bool:
        difference: DecimalValue = self.__sub__(other)
        return difference.unscaled < 0

    def __le__(self, other: DecimalValue) -> bool:
        difference: DecimalValue = self.__sub__(other)
        return difference.unscaled <= 0

    def __float__(self) -> float:
        return (self.unscaled * 1.0) / _pow10(self.scale)

    def __str__(self) -> str:
        if self.scale == 0:
            return "" + self.unscaled
        negative: bool = self.unscaled < 0
        magnitude: int = self.unscaled
        if negative:
            magnitude = -magnitude
        divisor: int = _pow10(self.scale)
        wholePart: int = magnitude / divisor
        fracPart: int = magnitude % divisor
        padded: str = "" + fracPart
        digitCount: int = _digitCount(fracPart)
        while digitCount < self.scale:
            padded = "0" + padded
            digitCount += 1
        result: str = "" + wholePart + "." + padded
        if negative:
            result = "-" + result
        return result


def _digitCount(n: int) -> int:
    if n == 0:
        return 1
    count: int = 0
    value: int = n
    while value > 0:
        value /= 10
        count += 1
    return count


def _pow10(n: int) -> int:
    result: int = 1
    index: int = 0
    while index < n:
        result *= 10
        index += 1
    return result
