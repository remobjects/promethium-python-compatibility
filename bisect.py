@namespace("bisect")

from Promethium import List


# A small, opt-in subset of Python's bisect module. Like heapq.py, this
# follows PromethiumBaseLibrary's own sorted()/min()/max() precedent of
# hand-overloading for int/float/str rather than generic T, since
# unconstrained generic T has no `<` operator in Promethium.
#
# `hi` has no direct equivalent of Python's `hi=None` default (the parameter
# is a plain `int`, and Promethium has no `Optional[int]`/nullable-int
# default here), so `-1` is used as the "unspecified, search to the end of
# the list" sentinel instead — matching this project's existing pattern of
# picking a concrete sentinel where CPython uses `None` (see `DefaultDict`'s
# `get`/`pop` defaults).


def bisect_left(a: List[int], x: int, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if a.__getitem__(mid) < x:
            low = mid + 1
        else:
            high = mid
    return low

def bisect_left(a: List[float], x: float, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if a.__getitem__(mid) < x:
            low = mid + 1
        else:
            high = mid
    return low

def bisect_left(a: List[str], x: str, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if a.__getitem__(mid) < x:
            low = mid + 1
        else:
            high = mid
    return low


def bisect_right(a: List[int], x: int, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if x < a.__getitem__(mid):
            high = mid
        else:
            low = mid + 1
    return low

def bisect_right(a: List[float], x: float, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if x < a.__getitem__(mid):
            high = mid
        else:
            low = mid + 1
    return low

def bisect_right(a: List[str], x: str, lo: int = 0, hi: int = -1) -> int:
    high: int = hi
    if high < 0:
        high = len(a)
    low: int = lo
    while low < high:
        mid: int = (low + high) >> 1
        if x < a.__getitem__(mid):
            high = mid
        else:
            low = mid + 1
    return low


def bisect(a: List[int], x: int, lo: int = 0, hi: int = -1) -> int:
    return bisect_right(a, x, lo, hi)

def bisect(a: List[float], x: float, lo: int = 0, hi: int = -1) -> int:
    return bisect_right(a, x, lo, hi)

def bisect(a: List[str], x: str, lo: int = 0, hi: int = -1) -> int:
    return bisect_right(a, x, lo, hi)


def insort_left(a: List[int], x: int, lo: int = 0, hi: int = -1):
    a.insert(bisect_left(a, x, lo, hi), x)

def insort_left(a: List[float], x: float, lo: int = 0, hi: int = -1):
    a.insert(bisect_left(a, x, lo, hi), x)

def insort_left(a: List[str], x: str, lo: int = 0, hi: int = -1):
    a.insert(bisect_left(a, x, lo, hi), x)


def insort_right(a: List[int], x: int, lo: int = 0, hi: int = -1):
    a.insert(bisect_right(a, x, lo, hi), x)

def insort_right(a: List[float], x: float, lo: int = 0, hi: int = -1):
    a.insert(bisect_right(a, x, lo, hi), x)

def insort_right(a: List[str], x: str, lo: int = 0, hi: int = -1):
    a.insert(bisect_right(a, x, lo, hi), x)


def insort(a: List[int], x: int, lo: int = 0, hi: int = -1):
    insort_right(a, x, lo, hi)

def insort(a: List[float], x: float, lo: int = 0, hi: int = -1):
    insort_right(a, x, lo, hi)

def insort(a: List[str], x: str, lo: int = 0, hi: int = -1):
    insort_right(a, x, lo, hi)
