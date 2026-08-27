@namespace("binascii")

# A small, opt-in subset of Python's binascii module: `hexlify`/`unhexlify`,
# built directly on `RemObjects.Elements.RTL.Convert`'s already-implemented
# `ToHexString`/`HexStringToByteArray` — no new algorithm needed, the same
# story as `base64.py` reusing `Convert`'s base64 codec.
#
# Same deliberate signature deviation as `base64.py`, for the same reason:
# CPython's `hexlify(bytes) -> bytes` returns ASCII hex digits as *bytes*,
# which callers almost always immediately `.decode('ascii')` anyway — this
# returns `str` directly, with the matching shortcut on `unhexlify`'s
# input. `RemObjects.Elements.RTL.Convert` is always fully qualified, same
# reasoning as `base64.py`/`time.py` (a bare `Convert`/`DateTime` risks
# inconsistent per-target resolution, and `Convert` plausibly collides
# with the platform BCL's own `System.Convert`).
#
# `Convert.ToHexString` produces UPPERCASE hex digits; CPython's own
# `hexlify` produces lowercase — confirmed by direct runtime comparison,
# not assumed. `hexlify` lowercases the result to match (same native
# per-target `.ToLower()`/`.toLowerCase()`/`.lowercaseString` idiom
# `string.py`'s `_lower` already uses).
#
# `crc32` is the one function here that's a real algorithm, not a
# `Convert` passthrough — pure bit arithmetic, no native call, the
# standard reflected bit-by-bit CRC-32 (polynomial `0xEDB88320`, the same
# one CPython's `binascii.crc32`/`zlib.crc32` both use). Promethium's
# `int` is signed 32-bit, so two things needed care: (1) `0xFFFFFFFF`
# (the algorithm's initial/final all-ones value) is spelled `-1` — the
# same bit pattern, unambiguous regardless of signedness; (2) the
# algorithm's per-bit right-shift must be *logical* (zero-fill), but
# Promethium's `>>` on a negative value is arithmetic (sign-extending,
# confirmed by the same reasoning `struct.py`'s unpack functions already
# rely on) — `_logicalShiftRight1` corrects for this by masking off bit
# 31 after the shift, which is the only bit an arithmetic and a logical
# single-bit right-shift can ever disagree on. The returned checksum is
# CPython's own unsigned result's *bit pattern*, reinterpreted as signed
# — for inputs whose CRC is `>= 0x80000000`, this reads back as the
# equivalent negative `int`, the same representational limit `struct.py`
# already documents for `unpack_uint32_*`, not a bug in the algorithm
# itself.


def _lower(value: str) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.ToLower()
    elif defined("COOPER"):
        return value.toLowerCase()
    else:
        return value.lowercaseString


def hexlify(data: bytes) -> str:
    return _lower(RemObjects.Elements.RTL.Convert.ToHexString(data))


def unhexlify(data: str) -> bytes:
    return RemObjects.Elements.RTL.Convert.HexStringToByteArray(data)


def _logicalShiftRight1(value: int) -> int:
    return (value >> 1) & 0x7FFFFFFF


def crc32(data: bytes) -> int:
    crc: int = -1
    byteIndex: int = 0
    while byteIndex < data.Length:
        crc = crc ^ data[byteIndex]
        bitIndex: int = 0
        while bitIndex < 8:
            lsbSet: bool = (crc & 1) != 0
            crc = _logicalShiftRight1(crc)
            if lsbSet:
                crc = crc ^ -306674912
            bitIndex += 1
        byteIndex += 1
    return crc ^ -1
