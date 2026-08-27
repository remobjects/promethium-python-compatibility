@namespace("Promethium")

from collections import Counter, OrderedDict, ChainMap, Deque, DefaultDict


# The built-in `len()` only has overloads for PromethiumBaseLibrary's own
# List/Dictionary/Set/str (declared in Builtins.py, in this same "Promethium"
# namespace). Overload resolution combines same-named functions across
# assemblies within one open namespace, so declaring more `len` overloads
# here — in "Promethium", not "collections" — extends that same overload
# set: `len(counts)` now works directly for every class in this library,
# instead of requiring `.__len__()`.


def len[T](value: Counter[T]) -> int:
    return value.__len__()


def len[Key, Value](value: OrderedDict[Key, Value]) -> int:
    return value.__len__()


def len[Key, Value](value: ChainMap[Key, Value]) -> int:
    return value.__len__()


def len[T](value: Deque[T]) -> int:
    return value.__len__()


def len[Key, Value](value: DefaultDict[Key, Value]) -> int:
    return value.__len__()


def len(value: PyByteArray) -> int:
    return value.__len__()
