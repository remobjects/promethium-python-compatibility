@namespace("cmath")

# A small, opt-in subset of Python's cmath module. Promethium has no native
# complex-number type at all — the grammar explicitly rejects complex
# literals ("Elements has no cross-platform complex-number type") — so this
# defines its own `ComplexValue` class rather than hooking a native one, the
# same way `fractions.py`/`decimal.py` define their own numeric types.
#
# Deliberately not named `Complex`: .NET has `System.Numerics.Complex`, a
# real, plausible collision by the same mechanism `random.py`'s `Random`
# and `decimal.py`'s `Decimal` already hit. Named `ComplexValue`
# preemptively.
#
# All arithmetic reuses `math.py`'s already-verified `sqrt`/`sin`/`cos`/
# `exp`/`log`/`atan2`, called fully qualified (`math.sqrt(...)`) — bare
# calls to a concrete function from another namespace aren't reliably
# resolved via ambient `DefaultUses` (see `heapq.py`'s note on
# `Promethium.sorted`). Dunders are explicit-call-only, same as every other
# class in this project — Promethium doesn't lower operators to methods.


class ComplexValue:
    real: float
    imag: float

    def __init__(self, real: float, imag: float):
        self.real = real
        self.imag = imag

    def __add__(self, other: ComplexValue) -> ComplexValue:
        return ComplexValue(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other: ComplexValue) -> ComplexValue:
        return ComplexValue(self.real - other.real, self.imag - other.imag)

    def __mul__(self, other: ComplexValue) -> ComplexValue:
        return ComplexValue(
            self.real * other.real - self.imag * other.imag,
            self.real * other.imag + self.imag * other.real,
        )

    def __truediv__(self, other: ComplexValue) -> ComplexValue:
        denominator: float = other.real * other.real + other.imag * other.imag
        return ComplexValue(
            (self.real * other.real + self.imag * other.imag) / denominator,
            (self.imag * other.real - self.real * other.imag) / denominator,
        )

    def __neg__(self) -> ComplexValue:
        return ComplexValue(-self.real, -self.imag)

    def __eq__(self, other: ComplexValue) -> bool:
        return self.real == other.real and self.imag == other.imag

    def __abs__(self) -> float:
        return math.sqrt(self.real * self.real + self.imag * self.imag)

    def conjugate(self) -> ComplexValue:
        return ComplexValue(self.real, -self.imag)

    def __str__(self) -> str:
        if self.real == 0.0:
            return "" + self.imag + "j"
        if self.imag < 0.0:
            return "(" + self.real + "-" + (-self.imag) + "j)"
        return "(" + self.real + "+" + self.imag + "j)"


def phase(z: ComplexValue) -> float:
    return math.atan2(z.imag, z.real)


def polar(z: ComplexValue) -> tuple[float, float]:
    return (z.__abs__(), phase(z))


def rect(r: float, phi: float) -> ComplexValue:
    return ComplexValue(r * math.cos(phi), r * math.sin(phi))


def sqrt(z: ComplexValue) -> ComplexValue:
    magnitude: float = z.__abs__()
    realPart: float = math.sqrt((magnitude + z.real) / 2.0)
    imagPart: float = math.sqrt((magnitude - z.real) / 2.0)
    if z.imag < 0.0:
        imagPart = -imagPart
    return ComplexValue(realPart, imagPart)


def exp(z: ComplexValue) -> ComplexValue:
    factor: float = math.exp(z.real)
    return ComplexValue(factor * math.cos(z.imag), factor * math.sin(z.imag))


def log(z: ComplexValue) -> ComplexValue:
    return ComplexValue(math.log(z.__abs__()), phase(z))
