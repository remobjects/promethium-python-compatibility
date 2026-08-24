@namespace("math")

from Promethium import ValueError, List

# The module namespace is intentionally explicit: consumers use the normal
# Python-shaped `import math` spelling rather than the project implementation
# namespace.
#
# Where a function can be implemented with pure Promethium arithmetic
# (fabs/isnan/isinf/isfinite/degrees/radians/copysign/gcd/factorial/fmod),
# it is, exactly like the original fabs/isnan — no per-target branching
# needed, and no dependency on any native math library existing or being
# spelled consistently across targets.
#
# Everything else (roots, logs, trig, powers) genuinely needs a native call:
# Elements compiles this same source to four very different backends, and
# each spells its math library differently. Confirmed call surfaces:
#   - Echoes:  System.Math.Sqrt/.Floor/.Ceiling/.Truncate/.Pow/.Log/.Log10/
#              .Exp/.Sin/.Cos/.Tan/.Asin/.Acos/.Atan/.Atan2 (RTL2's own
#              Math.pas maps identically; no Log2 pre-.NET6, use Log(x, 2)).
#   - Island:  RemObjects.Elements.System.Math with the same Sqrt/Floor/
#              Ceiling/Truncate/Pow/Log/Log2/Log10/Exp/Sin/Cos/Tan/Asin/
#              Acos/Atan/Atan2 names (IslandRTL's own Math unit).
#   - Cooper:  Math.sqrt/.floor/.ceil/.pow/.log/.log10/.exp/.sin/.cos/.tan/
#              .asin/.acos/.atan/.atan2 (java.lang.Math, lowercase methods,
#              no explicit import needed).
#   - Toffee:  rtl.sqrt/.floor/.ceil/.pow/.log/.log10/.exp/.sin/.cos/.tan/
#              .asin/.acos/.atan/.atan2 — the `rtl.`-qualified spelling is
#              used deliberately instead of the bare global C functions
#              (`sqrt(...)` etc., which also exist in Toffee mode): a bare
#              call to `sqrt` from *inside a function this module itself
#              defines and also names `sqrt`* would resolve to itself
#              (infinite recursion) rather than the C library function.
# `System.Math.Sqrt(value)`-style fully-qualified native calls follow the
# same pattern already proven in PromethiumBaseLibrary's own Builtins.py,
# whose `print` calls `RemObjects.Elements.System.writeLn(value)` directly.
#
# `int(...)`/`float(...)` casts are avoided entirely here — there's no
# confirmed-working cast syntax in this codebase yet, so every function
# below either returns float directly from a native call or works with
# int arithmetic throughout (gcd, factorial).


def fabs(value: float) -> float:
    if value == 0.0:
        return 0.0
    if value < 0.0:
        return -value
    return value


def isnan(value: float) -> bool:
    return value != value


def isinf(value: float) -> bool:
    if isnan(value):
        return False
    difference: float = value - value
    return isnan(difference)


def isfinite(value: float) -> bool:
    return not isnan(value) and not isinf(value)


def copysign(magnitude: float, sign: float) -> float:
    result: float = fabs(magnitude)
    if sign < 0.0:
        return -result
    return result


def fmod(x: float, y: float) -> float:
    return x % y


def degrees(value: float) -> float:
    return value * (180.0 / 3.141592653589793)


def radians(value: float) -> float:
    return value * (3.141592653589793 / 180.0)


def gcd(a: int, b: int) -> int:
    x: int = a
    if x < 0:
        x = -x
    y: int = b
    if y < 0:
        y = -y
    while y != 0:
        remainder: int = x % y
        x = y
        y = remainder
    return x


def factorial(n: int) -> int:
    if n < 0:
        raise ValueError("factorial() not defined for negative values")
    result: int = 1
    value: int = 2
    while value <= n:
        result *= value
        value += 1
    return result


def sqrt(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Sqrt(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Sqrt(value)
    elif defined("COOPER"):
        return Math.sqrt(value)
    else:
        return rtl.sqrt(value)


def hypot(x: float, y: float) -> float:
    return sqrt(x * x + y * y)


def floor(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Floor(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Floor(value)
    elif defined("COOPER"):
        return Math.floor(value)
    else:
        return rtl.floor(value)


def ceil(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Ceiling(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Ceiling(value)
    elif defined("COOPER"):
        return Math.ceil(value)
    else:
        return rtl.ceil(value)


def trunc(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Truncate(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Truncate(value)
    elif defined("COOPER"):
        if value < 0.0:
            return Math.ceil(value)
        else:
            return Math.floor(value)
    else:
        return rtl.trunc(value)


def pow(base: float, exponent: float) -> float:
    if defined("ECHOES"):
        return System.Math.Pow(base, exponent)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Pow(base, exponent)
    elif defined("COOPER"):
        return Math.pow(base, exponent)
    else:
        return rtl.pow(base, exponent)


def exp(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Exp(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Exp(value)
    elif defined("COOPER"):
        return Math.exp(value)
    else:
        return rtl.exp(value)


def log(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Log(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Log(value)
    elif defined("COOPER"):
        return Math.log(value)
    else:
        return rtl.log(value)


def log10(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Log10(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Log10(value)
    elif defined("COOPER"):
        return Math.log10(value)
    else:
        return rtl.log10(value)


def log2(value: float) -> float:
    if defined("ISLAND"):
        return RemObjects.Elements.System.Math.Log2(value)
    else:
        return log(value) / log(2.0)


def sin(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Sin(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Sin(value)
    elif defined("COOPER"):
        return Math.sin(value)
    else:
        return rtl.sin(value)


def cos(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Cos(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Cos(value)
    elif defined("COOPER"):
        return Math.cos(value)
    else:
        return rtl.cos(value)


def tan(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Tan(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Tan(value)
    elif defined("COOPER"):
        return Math.tan(value)
    else:
        return rtl.tan(value)


def asin(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Asin(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Asin(value)
    elif defined("COOPER"):
        return Math.asin(value)
    else:
        return rtl.asin(value)


def acos(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Acos(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Acos(value)
    elif defined("COOPER"):
        return Math.acos(value)
    else:
        return rtl.acos(value)


def atan(value: float) -> float:
    if defined("ECHOES"):
        return System.Math.Atan(value)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Atan(value)
    elif defined("COOPER"):
        return Math.atan(value)
    else:
        return rtl.atan(value)


def atan2(y: float, x: float) -> float:
    if defined("ECHOES"):
        return System.Math.Atan2(y, x)
    elif defined("ISLAND"):
        return RemObjects.Elements.System.Math.Atan2(y, x)
    elif defined("COOPER"):
        return Math.atan2(y, x)
    else:
        return rtl.atan2(y, x)


def isqrt(n: int) -> int:
    if n < 0:
        raise ValueError("isqrt() argument must be nonnegative")
    if n == 0:
        return 0
    x: int = n
    y: int = (x + 1) / 2
    while y < x:
        x = y
        y = (x + n / x) / 2
    return x


def comb(n: int, k: int) -> int:
    if k < 0 or n < 0:
        raise ValueError("comb() arguments must be non-negative")
    if k > n:
        return 0
    if k > n - k:
        k = n - k
    result: int = 1
    index: int = 0
    while index < k:
        result = result * (n - index) / (index + 1)
        index += 1
    return result


def perm(n: int, k: int) -> int:
    if k < 0 or n < 0:
        raise ValueError("perm() arguments must be non-negative")
    if k > n:
        return 0
    result: int = 1
    index: int = 0
    while index < k:
        result *= (n - index)
        index += 1
    return result


def prod(values: List[int]) -> int:
    result: int = 1
    index: int = 0
    while index < len(values):
        result *= values.__getitem__(index)
        index += 1
    return result

def prod(values: List[float]) -> float:
    result: float = 1.0
    index: int = 0
    while index < len(values):
        result *= values.__getitem__(index)
        index += 1
    return result


def dist(p: tuple[float, float], q: tuple[float, float]) -> float:
    dx: float = p[0] - q[0]
    dy: float = p[1] - q[1]
    return sqrt(dx * dx + dy * dy)
