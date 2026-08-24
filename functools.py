@namespace("functools")

from Promethium import List, ValueError

# A small, opt-in subset of Python's functools module. `reduce` is the only
# function attempted: `partial`/`lru_cache`/`wraps`/`cmp_to_key` all need
# either decorators or storing+re-dispatching an arbitrary callable's
# signature, neither of which is attempted anywhere in this codebase.
#
# `func` is deliberately untyped, matching `DefaultDict`'s factory field —
# there's no confirmed way to type a callable/predicate parameter in this
# codebase (see the note in `itertools.py`). Two-argument `.Invoke(a, b)`
# works on Echoes/Island/Cooper but not Toffee: an untyped parameter erases
# to Objective-C `id` there, whose block-invocation surface doesn't expose
# a matching 2-parameter `invoke` (confirmed: "No overloaded method 'invoke'
# with 2 parameters on type 'id'"). This is the same dynamic-block-
# invocation limitation `DefaultDict.__getitem__` already documents for its
# own (0-argument) factory, handled the same way: raise on Toffee instead
# of silently misbehaving.


def reduce(func, values: List[int], initial: int) -> int:
    if defined("TOFFEE"):
        raise ValueError("functools.reduce cannot invoke its callable on Toffee yet")
    else:
        accumulator: int = initial
        index: int = 0
        while index < len(values):
            accumulator = func.Invoke(accumulator, values.__getitem__(index))
            index += 1
        return accumulator