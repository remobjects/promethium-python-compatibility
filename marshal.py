@namespace("marshal")

# CPython's `marshal` writes an internal, version-specific object-graph
# format (the same one `.pyc` files use) — undocumented on purpose, never
# guaranteed stable across Python versions, and never meant for real
# interop even between two CPython builds. There is nothing to be
# "compatible" with here the way `wave.py`/`zipfile.py` are compatible
# with a real, stable container format — so this ships its own small,
# fully-documented binary format instead of attempting to mimic CPython's
# private one.
#
# Concrete `dumps_*`/`loads_*` functions per type, matching this
# project's established pattern for "one generic CPython function becomes
# several concrete ones" (`struct.py`, `asyncio.py`'s `run_int`/`run_str`,
# `numbers.py`) rather than a single `dumps(obj)` over a `dynamic`-typed
# parameter.
#
# Built entirely on primitives this project already shipped and verified:
# `struct.pack_uint32_le`/`unpack_uint32_le` for the integer encoding,
# `codecs.encode`/`decode` for UTF-8 string bytes, and
# `RemObjects.Elements.RTL.Binary` for the growable buffer
# (`zipfile.py`'s established idiom for building/reading variable-length
# `bytes` payloads).
#
# No `dumps_float`/`loads_float`: needs a native bit-reinterpretation call
# (`BitConverter.GetBytes`/`ToSingle` on Echoes, `Float.floatToIntBits` on
# Cooper, etc.) that `struct.py` already scoped out as "a scope cut not
# an oversight" — same call here, for the same reason, not attempted in
# this pass.
#
# `dumps_str`/`loads_str` format: a 4-byte little-endian length prefix
# (via `struct.pack_uint32_le`) followed by that many UTF-8 bytes.
# Verified round-tripping `dumps_int`/`loads_int` and `dumps_str`/
# `loads_str` against hand-computed expected byte sequences, plus
# `dumps_bool`/`loads_bool` for both `True` and `False`.


def _extractBytes(data: bytes, start: int, count: int) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    i: int = 0
    while i < count:
        b: bytes = b"\x00"
        b[0] = data[start + i]
        buf.Write(b)
        i += 1
    return buf.ToArray()


def dumps_int(value: int) -> bytes:
    return struct.pack_uint32_le(value)


def loads_int(data: bytes) -> int:
    return struct.unpack_uint32_le(data)


def dumps_bool(value: bool) -> bytes:
    data: bytes = b"\x00"
    if value:
        data[0] = 1
    return data


def loads_bool(data: bytes) -> bool:
    return data[0] != 0


def dumps_str(value: str) -> bytes:
    payload: bytes = codecs.encode(value)
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    buf.Write(struct.pack_uint32_le(payload.Length))
    buf.Write(payload)
    return buf.ToArray()


def loads_str(data: bytes) -> str:
    lengthBytes: bytes = _extractBytes(data, 0, 4)
    length: int = struct.unpack_uint32_le(lengthBytes)
    payload: bytes = _extractBytes(data, 4, length)
    return codecs.decode(payload)
