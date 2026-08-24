@namespace("statistics")

from Promethium import List
from collections import Counter

# A small, opt-in subset of Python's statistics module, overloaded for
# `int`/`float` like `PromethiumBaseLibrary`'s own `sorted()`/`min()`/
# `max()` (see the note in `heapq.py`) — `median`/`variance`/`stdev` need
# ordering/arithmetic that unconstrained generic T doesn't have.
#
# `median` always returns `float`, unlike CPython's `statistics.median`
# (which returns the middle element's own type for odd-length input, and
# only promotes to `float` for the even-length average) — a Promethium
# function can't return one type or another depending on a runtime-only
# condition, so this always returns `float`, matching every case's numeric
# *value* even where CPython would give back an `int`.
#
# `sorted(...)`/`sqrt(...)` are called fully qualified (`Promethium.sorted`,
# `math.sqrt`) rather than bare, following the same pattern `heapq.py`
# established for calling a concrete (non-generic) function from another
# namespace — bare calls to those aren't reliably resolved via ambient
# `DefaultUses` opening the way `len(...)` is.
#
# `mode` is generic — it just needs `T` to support equality (via
# `collections.Counter`, not needing anything of its own beyond that), not
# ordering.


def mean(data: List[int]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += data.__getitem__(index)
        index += 1
    return total / len(data)

def mean(data: List[float]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += data.__getitem__(index)
        index += 1
    return total / len(data)


def median(data: List[int]) -> float:
    ordered: List[int] = Promethium.sorted(data)
    count: int = len(ordered)
    middle: int = count / 2
    if count % 2 == 1:
        return ordered.__getitem__(middle)
    lower: int = ordered.__getitem__(middle - 1)
    upper: int = ordered.__getitem__(middle)
    return (lower + upper) / 2.0

def median(data: List[float]) -> float:
    ordered: List[float] = Promethium.sorted(data)
    count: int = len(ordered)
    middle: int = count / 2
    if count % 2 == 1:
        return ordered.__getitem__(middle)
    lower: float = ordered.__getitem__(middle - 1)
    upper: float = ordered.__getitem__(middle)
    return (lower + upper) / 2.0


def median_low(data: List[int]) -> int:
    ordered: List[int] = Promethium.sorted(data)
    count: int = len(ordered)
    middle: int = count / 2
    if count % 2 == 1:
        return ordered.__getitem__(middle)
    return ordered.__getitem__(middle - 1)

def median_low(data: List[float]) -> float:
    ordered: List[float] = Promethium.sorted(data)
    count: int = len(ordered)
    middle: int = count / 2
    if count % 2 == 1:
        return ordered.__getitem__(middle)
    return ordered.__getitem__(middle - 1)


def median_high(data: List[int]) -> int:
    ordered: List[int] = Promethium.sorted(data)
    middle: int = len(ordered) / 2
    return ordered.__getitem__(middle)

def median_high(data: List[float]) -> float:
    ordered: List[float] = Promethium.sorted(data)
    middle: int = len(ordered) / 2
    return ordered.__getitem__(middle)


def harmonic_mean(data: List[int]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += 1.0 / data.__getitem__(index)
        index += 1
    return len(data) / total

def harmonic_mean(data: List[float]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += 1.0 / data.__getitem__(index)
        index += 1
    return len(data) / total


def geometric_mean(data: List[int]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += math.log(data.__getitem__(index))
        index += 1
    return math.exp(total / len(data))

def geometric_mean(data: List[float]) -> float:
    total: float = 0.0
    index: int = 0
    while index < len(data):
        total += math.log(data.__getitem__(index))
        index += 1
    return math.exp(total / len(data))


def mode[T](data: List[T]) -> T:
    counts: Counter[T] = Counter[T](data)
    top: List[tuple[T, int]] = counts.most_common(1)
    return top.__getitem__(0)[0]


def pvariance(data: List[int]) -> float:
    average: float = mean(data)
    total: float = 0.0
    index: int = 0
    while index < len(data):
        difference: float = data.__getitem__(index) - average
        total += difference * difference
        index += 1
    return total / len(data)

def pvariance(data: List[float]) -> float:
    average: float = mean(data)
    total: float = 0.0
    index: int = 0
    while index < len(data):
        difference: float = data.__getitem__(index) - average
        total += difference * difference
        index += 1
    return total / len(data)


def variance(data: List[int]) -> float:
    average: float = mean(data)
    total: float = 0.0
    index: int = 0
    while index < len(data):
        difference: float = data.__getitem__(index) - average
        total += difference * difference
        index += 1
    return total / (len(data) - 1.0)

def variance(data: List[float]) -> float:
    average: float = mean(data)
    total: float = 0.0
    index: int = 0
    while index < len(data):
        difference: float = data.__getitem__(index) - average
        total += difference * difference
        index += 1
    return total / (len(data) - 1.0)


def pstdev(data: List[int]) -> float:
    return math.sqrt(pvariance(data))

def pstdev(data: List[float]) -> float:
    return math.sqrt(pvariance(data))


def stdev(data: List[int]) -> float:
    return math.sqrt(variance(data))

def stdev(data: List[float]) -> float:
    return math.sqrt(variance(data))
