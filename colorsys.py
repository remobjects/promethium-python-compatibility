@namespace("colorsys")

# A small, opt-in subset of Python's colorsys module: rgb_to_hsv/
# hsv_to_rgb and rgb_to_hls/hls_to_rgb, a direct port of CPython's own
# Lib/colorsys.py algorithm.
#
# CPython's `hsv_to_rgb`/`hls_to_rgb` compute `i = int(h*6.0)` to pick a
# "sector" of the hue wheel — a float-to-int cast with no confirmed working
# syntax anywhere in this codebase (see `math.py`'s notes). Sidestepped
# entirely by keeping the sector index as a `float` throughout
# (`math.floor(h * 6.0)`) and comparing it against float literals
# (`0.0`, `1.0`, ...) instead of switching on an `int` — safe because the
# sector value is always an exact small integer (0–5) even in floating
# point, so there's no precision risk in the comparison.


def _max3(a: float, b: float, c: float) -> float:
    result: float = a
    if b > result:
        result = b
    if c > result:
        result = c
    return result


def _min3(a: float, b: float, c: float) -> float:
    result: float = a
    if b < result:
        result = b
    if c < result:
        result = c
    return result


def rgb_to_hsv(r: float, g: float, b: float) -> tuple[float, float, float]:
    maxc: float = _max3(r, g, b)
    minc: float = _min3(r, g, b)
    v: float = maxc
    if minc == maxc:
        return (0.0, 0.0, v)
    rangec: float = maxc - minc
    s: float = rangec / maxc
    rc: float = (maxc - r) / rangec
    gc: float = (maxc - g) / rangec
    bc: float = (maxc - b) / rangec
    h: float = 0.0
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0
    return (h, s, v)


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    if s == 0.0:
        return (v, v, v)
    hueSector: float = math.floor(h * 6.0)
    f: float = (h * 6.0) - hueSector
    p: float = v * (1.0 - s)
    q: float = v * (1.0 - s * f)
    t: float = v * (1.0 - s * (1.0 - f))
    sector: float = hueSector % 6.0
    if sector == 0.0:
        return (v, t, p)
    if sector == 1.0:
        return (q, v, p)
    if sector == 2.0:
        return (p, v, t)
    if sector == 3.0:
        return (p, q, v)
    if sector == 4.0:
        return (t, p, v)
    return (v, p, q)


def rgb_to_hls(r: float, g: float, b: float) -> tuple[float, float, float]:
    maxc: float = _max3(r, g, b)
    minc: float = _min3(r, g, b)
    sumc: float = maxc + minc
    rangec: float = maxc - minc
    lightness: float = sumc / 2.0
    if minc == maxc:
        return (0.0, lightness, 0.0)
    saturation: float = 0.0
    if lightness <= 0.5:
        saturation = rangec / sumc
    else:
        saturation = rangec / (2.0 - sumc)
    rc: float = (maxc - r) / rangec
    gc: float = (maxc - g) / rangec
    bc: float = (maxc - b) / rangec
    h: float = 0.0
    if r == maxc:
        h = bc - gc
    elif g == maxc:
        h = 2.0 + rc - bc
    else:
        h = 4.0 + gc - rc
    h = (h / 6.0) % 1.0
    return (h, lightness, saturation)


def _hueToChannel(m1: float, m2: float, hue: float) -> float:
    normalizedHue: float = hue % 1.0
    oneSixth: float = 1.0 / 6.0
    twoThird: float = 2.0 / 3.0
    if normalizedHue < oneSixth:
        return m1 + (m2 - m1) * normalizedHue * 6.0
    if normalizedHue < 0.5:
        return m2
    if normalizedHue < twoThird:
        return m1 + (m2 - m1) * (twoThird - normalizedHue) * 6.0
    return m1


def hls_to_rgb(h: float, lightness: float, s: float) -> tuple[float, float, float]:
    if s == 0.0:
        return (lightness, lightness, lightness)
    m2: float = 0.0
    if lightness <= 0.5:
        m2 = lightness * (1.0 + s)
    else:
        m2 = lightness + s - (lightness * s)
    m1: float = 2.0 * lightness - m2
    oneThird: float = 1.0 / 3.0
    return (
        _hueToChannel(m1, m2, h + oneThird),
        _hueToChannel(m1, m2, h),
        _hueToChannel(m1, m2, h - oneThird),
    )
