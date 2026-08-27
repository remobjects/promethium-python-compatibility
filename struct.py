@namespace("struct")

# A small, opt-in subset of Python's struct module: fixed-width integer
# packing/unpacking, both byte orders. CPython's actual API is a single
# `pack(fmt, *values)`/`unpack(fmt, data)` pair driven by a format string
# and variadic arguments — not reproducible here, since `*args`/`**kwargs`
# are outside this language slice entirely (per
# `PROMETHIUM_IMPLEMENTATION_PLAN.md`). Per-width, per-byte-order named
# functions instead, matching this project's established pattern for
# "CPython's one generic function becomes several concrete ones"
# (`heapq`/`bisect`/`statistics`'s int/float/str overloads).
#
# Pure bit arithmetic — no native call of any kind, the same as
# `datetime.py`'s proleptic-Gregorian day math. Building a `bytes` value
# of a specific size needed its own small discovery: `bytes` concatenation
# (`b"\x01" + b"\x02"`) doesn't compile ("cannot find operator to
# evaluate <array literal> + <array literal>"), but a fixed-size `bytes`
# literal's individual elements *can* be assigned after construction
# (`data: bytes = b"\x00\x00"; data[0] = 1`) — confirmed working and used
# throughout below as the allocation idiom.
#
# Named `uint8`/`uint16`/`uint32` (CPython's `B`/`H`/`I` format codes),
# but Promethium's `int` is signed 32-bit (see
# `promethium_int32_packing_overflow` precedent from this same project) —
# unpacking 4 bytes whose top bit is set produces the *same bit pattern*
# a signed 32-bit `int` would have, which reads back negative rather than
# as a value `>= 0x80000000`. This is a representational limit, not a
# bug: nothing here claims to represent the full unsigned 32-bit range.
# `pack_*`/`unpack_*` are exact inverses of each other regardless — round-
# tripping any 32-bit bit pattern through both is lossless even though
# the signed *meaning* of the round value may differ from what a real
# `uint32` would say.
#
# No float packing (`f`/`d` format codes) in this pass — that needs a
# native bit-reinterpretation call (`BitConverter.GetBytes`/`ToSingle` on
# Echoes, `Float.floatToIntBits`/`intBitsToFloat` on Cooper, similar on
# Toffee) that wasn't attempted here, a scope cut not an oversight.


def pack_uint8(value: int) -> bytes:
    data: bytes = b"\x00"
    data[0] = value & 0xFF
    return data


def unpack_uint8(data: bytes) -> int:
    return data[0]


def pack_uint16_le(value: int) -> bytes:
    data: bytes = b"\x00\x00"
    data[0] = value & 0xFF
    data[1] = (value >> 8) & 0xFF
    return data


def pack_uint16_be(value: int) -> bytes:
    data: bytes = b"\x00\x00"
    data[0] = (value >> 8) & 0xFF
    data[1] = value & 0xFF
    return data


def unpack_uint16_le(data: bytes) -> int:
    return data[0] | (data[1] << 8)


def unpack_uint16_be(data: bytes) -> int:
    return (data[0] << 8) | data[1]


def pack_uint32_le(value: int) -> bytes:
    data: bytes = b"\x00\x00\x00\x00"
    data[0] = value & 0xFF
    data[1] = (value >> 8) & 0xFF
    data[2] = (value >> 16) & 0xFF
    data[3] = (value >> 24) & 0xFF
    return data


def pack_uint32_be(value: int) -> bytes:
    data: bytes = b"\x00\x00\x00\x00"
    data[0] = (value >> 24) & 0xFF
    data[1] = (value >> 16) & 0xFF
    data[2] = (value >> 8) & 0xFF
    data[3] = value & 0xFF
    return data


def unpack_uint32_le(data: bytes) -> int:
    return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)


def unpack_uint32_be(data: bytes) -> int:
    return (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
