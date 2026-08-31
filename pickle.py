@namespace("pickle")

from Promethium import List

# CPython draws a real distinction between `marshal` (an internal,
# version-specific format the docs explicitly warn against using for
# anything but `.pyc` files / cross-process trust boundaries you control)
# and `pickle` (the general-purpose serializer users actually reach for,
# including for collections — `pickle.dumps([1, 2, 3])` is completely
# ordinary code; `marshal.dumps([1, 2, 3])` is not something real code is
# meant to do). This module reflects that same split: `dumps_int`/
# `dumps_bool`/`dumps_str` are thin wrappers straight through to
# `marshal.py`'s identical functions (same format, no reason to
# duplicate the bytes) — the actual value pickle adds here is
# `dumps_list_int`/`loads_list_int`, since serializing a collection is
# the thing people use `pickle` for far more than the scalar case.
#
# `dumps_list_int` format: `struct.pack_uint32_le(count)` followed by
# `count` 4-byte little-endian integers, no per-item type tag — this
# module doesn't attempt heterogeneous or nested pickling the way real
# CPython `pickle` (which walks an arbitrary object graph via `__reduce__`)
# does; only a flat `List[int]` is supported. That, and no custom-class
# support at all, are the real scope cuts from CPython's actual `pickle`
# — a full object-graph walker needs exactly the `dynamic`-typed single
# entry point this project has been avoiding all pass (see
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`), so
# it wasn't attempted; `copyreg` (which exists purely to let custom
# classes plug into that object-graph walk) has nothing to register
# against here and was correctly left unshipped for that reason.
#
# Verified: `dumps_list_int([1, 2, 3])` / `loads_list_int(...)` round-
# trips exactly; `dumps_int`/`dumps_bool`/`dumps_str` produce byte-for-
# byte identical output to the equivalent `marshal.py` call (they're the
# same call).


def dumps_int(value: int) -> bytes:
    return marshal.dumps_int(value)


def loads_int(data: bytes) -> int:
    return marshal.loads_int(data)


def dumps_bool(value: bool) -> bytes:
    return marshal.dumps_bool(value)


def loads_bool(data: bytes) -> bool:
    return marshal.loads_bool(data)


def dumps_str(value: str) -> bytes:
    return marshal.dumps_str(value)


def loads_str(data: bytes) -> str:
    return marshal.loads_str(data)


def dumps_list_int(values: List[int]) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    count: int = len(values)
    buf.Write(struct.pack_uint32_le(count))
    i: int = 0
    while i < count:
        buf.Write(struct.pack_uint32_le(values.__getitem__(i)))
        i += 1
    return buf.ToArray()


def loads_list_int(data: bytes) -> List[int]:
    result: List[int] = List[int]()
    count: int = struct.unpack_uint32_le(marshal._extractBytes(data, 0, 4))
    pos: int = 4
    i: int = 0
    while i < count:
        result.append(struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4)))
        pos += 4
        i += 1
    return result
