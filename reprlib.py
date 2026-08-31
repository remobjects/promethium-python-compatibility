@namespace("reprlib")

from Promethium import List

# A small, curated slice of CPython's `reprlib`: `repr_str`/`repr_list_int`/
# `repr_list_str`, matching the *behavior* of `reprlib.repr(x)` for those
# three concrete shapes, not a generic `repr(obj)` that works over any
# value — the same concrete-overload choice this project already made for
# `numbers.py`/`asyncio.py`, avoiding a `dynamic`-typed single entry point
# (and the fragility that shape of API has repeatedly hit this pass; see
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`).
#
# CPython's defaults (`reprlib.aRepr.maxstring == 30`,
# `reprlib.aRepr.maxlist == 6`) are hardcoded rather than exposed as
# configurable fields — nobody in practice changes them, and a
# configurable global mutable default isn't worth the surface area here.
#
# `repr_str`'s truncation was reverse-engineered from live CPython 3.12
# output, not guessed: `reprlib.repr('a'*50)` is `"'aaaaaaaaaaaa...`
# `aaaaaaaaaaaaa'"` — exactly 30 characters including the quotes, 12
# characters kept from the front and 13 from the back. CPython's own
# source (`Lib/reprlib.py`) computes this as `i = (maxstring-3)//2`,
# `j = maxstring-3-i` (13 and 14 for maxstring=30), then re-slices an
# already-quoted intermediate string — which nets out to keeping `i-1`
# raw characters from the front and `j-1` from the back once the quoting
# step is worked through algebraically. Verified byte-for-byte against
# the CPython output above.
#
# `repr_list_int`/`repr_list_str`'s truncation is simpler and confirmed
# directly from CPython's `_repr_iterable`: always take the first
# `maxlist` (6) elements, and append a trailing `"..."` marker only if
# the original had more than 6 — a list of exactly 6 elements is never
# truncated (`reprlib.repr(list(range(6)))` has no `...`, `range(7)`
# does).


def repr_str(s: str) -> str:
    maxstring: int = 30
    n: int = string._length(s)
    if n <= maxstring:
        return "'" + s + "'"
    i: int = (maxstring - 3) // 2
    j: int = maxstring - 3 - i
    head: str = string._substring(s, 0, i - 1)
    tail: str = string._substring(s, n - (j - 1), j - 1)
    return "'" + head + "..." + tail + "'"


def repr_list_int(values: List[int]) -> str:
    maxlist: int = 6
    n: int = len(values)
    result: str = "["
    count: int = n
    if count > maxlist:
        count = maxlist
    i: int = 0
    while i < count:
        if i > 0:
            result = result + ", "
        result = result + ("" + values.__getitem__(i))
        i += 1
    if n > maxlist:
        result = result + ", ...]"
    else:
        result = result + "]"
    return result


def repr_list_str(values: List[str]) -> str:
    maxlist: int = 6
    n: int = len(values)
    result: str = "["
    count: int = n
    if count > maxlist:
        count = maxlist
    i: int = 0
    while i < count:
        if i > 0:
            result = result + ", "
        result = result + repr_str(values.__getitem__(i))
        i += 1
    if n > maxlist:
        result = result + ", ...]"
    else:
        result = result + "]"
    return result
