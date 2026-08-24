@namespace("operator")

from Promethium import List, ValueError

# A small, opt-in subset of Python's operator module.
#
# Import this module explicitly from Promethium code. It deliberately does not
# alter built-ins or provide target-specific behavior.
#
# `floordiv` implements CPython's floor-toward-negative-infinity semantics by
# hand rather than Promethium's `//` operator (unconfirmed to exist/behave
# the same way here — no file in this codebase uses it), using only `/` and
# `%` (both already relied on elsewhere: see `mod` above and
# PromethiumBaseLibrary's own `range()`), which are assumed to truncate
# toward zero like C/C#/Java's integer division.
#
# `contains`/`concat`/`countOf`/`getitem`/`setitem`/`indexOf` operate on
# `List[T]` generically, but deliberately avoid `List.index()`: Toffee's
# underlying `indexOfObject:` returns Cocoa's `NSNotFound` sentinel (not
# `-1`) when the item is missing, so a portable "not found" check can't
# just compare `index() >= 0`. `contains`/`countOf` use the already-portable
# `List.count()` instead, and `indexOf` does its own linear scan with
# `.Equals`/`.isEqual` — the same pattern `collections`' classes already use
# for exactly this reason (see `Counter.py`'s `_index_of`). `setitem` is a
# thin wrapper over `List`'s own `__setitem__` (bracket assignment).


def add(left: int, right: int) -> int:
    return left + right


def add(left: float, right: float) -> float:
    return left + right


def sub(left: int, right: int) -> int:
    return left - right


def sub(left: float, right: float) -> float:
    return left - right


def mul(left: int, right: int) -> int:
    return left * right


def mul(left: float, right: float) -> float:
    return left * right


def truediv(left: float, right: float) -> float:
    return left / right


def mod(left: int, right: int) -> int:
    return left % right


def mod(left: float, right: float) -> float:
    return left % right


def neg(value: int) -> int:
    return -value


def neg(value: float) -> float:
    return -value


def pos(value: int) -> int:
    return +value


def pos(value: float) -> float:
    return +value


def eq(left: int, right: int) -> bool:
    return left == right


def eq(left: float, right: float) -> bool:
    return left == right


def eq(left: bool, right: bool) -> bool:
    return left == right


def ne(left: int, right: int) -> bool:
    return left != right


def ne(left: float, right: float) -> bool:
    return left != right


def ne(left: bool, right: bool) -> bool:
    return left != right


def lt(left: int, right: int) -> bool:
    return left < right


def lt(left: float, right: float) -> bool:
    return left < right


def le(left: int, right: int) -> bool:
    return left <= right


def le(left: float, right: float) -> bool:
    return left <= right


def gt(left: int, right: int) -> bool:
    return left > right


def gt(left: float, right: float) -> bool:
    return left > right


def ge(left: int, right: int) -> bool:
    return left >= right


def ge(left: float, right: float) -> bool:
    return left >= right


def not_(value: bool) -> bool:
    return not value


def truth(value: bool) -> bool:
    return value


def abs(value: int) -> int:
    if value < 0:
        return -value
    return value


def abs(value: float) -> float:
    if value < 0.0:
        return -value
    return value


def and_(left: int, right: int) -> int:
    return left & right


def and_(left: bool, right: bool) -> bool:
    return left and right


def or_(left: int, right: int) -> int:
    return left | right


def or_(left: bool, right: bool) -> bool:
    return left or right


def xor(left: int, right: int) -> int:
    return left ^ right


def xor(left: bool, right: bool) -> bool:
    return left != right


def invert(value: int) -> int:
    return ~value


def lshift(value: int, count: int) -> int:
    return value << count


def rshift(value: int, count: int) -> int:
    return value >> count


def floordiv(left: int, right: int) -> int:
    quotient: int = left / right
    remainder: int = left % right
    if remainder != 0 and (remainder < 0) != (right < 0):
        quotient -= 1
    return quotient


def getitem[T](container: List[T], index: int) -> T:
    return container.__getitem__(index)


def setitem[T](container: List[T], index: int, value: T):
    container[index] = value


def concat[T](a: List[T], b: List[T]) -> List[T]:
    result: List[T] = a.copy()
    result.extend(b)
    return result


def contains[T](container: List[T], item: T) -> bool:
    return container.count(item) > 0


def countOf[T](container: List[T], item: T) -> int:
    return container.count(item)


def indexOf[T](container: List[T], item: T) -> int:
    position: int = 0
    while position < len(container):
        candidate: T = container.__getitem__(position)
        if defined("TOFFEE"):
            if candidate.isEqual(item):
                return position
        else:
            if candidate.Equals(item):
                return position
        position += 1
    raise ValueError("sequence.index(x): x not in sequence")
