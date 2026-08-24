@namespace("copy")

from Promethium import List

# A small, opt-in subset of Python's copy module, scoped to what this
# project can support generically: `List[T]`/`List[List[T]]`. A fully
# generic `copy.deepcopy` (recursing into arbitrary user-defined objects)
# would need reflection over arbitrary types, which isn't attempted here —
# same reasoning as `namedtuple`'s exclusion in `collections`.
#
# `deepcopy` only has a `List[List[T]]` overload, not a flat `List[T]` one:
# for a flat list, "deep" and "shallow" copy are the same operation (there's
# nothing nested to alias), so a flat overload would just duplicate `copy`
# — and worse, having both compiles but makes `deepcopy(aListOfLists)`
# genuinely ambiguous (confirmed: the compiler can't tell whether `T` in the
# flat overload should bind to the *inner* list type or the *outer* one,
# and refuses to guess). Call `copy()` directly on a flat list instead.


def copy[T](values: List[T]) -> List[T]:
    return values.copy()


def deepcopy[T](values: List[List[T]]) -> List[List[T]]:
    result: List[List[T]] = List[List[T]]()
    index: int = 0
    while index < len(values):
        result.append(values.__getitem__(index).copy())
        index += 1
    return result
