@namespace("Promethium")

from Promethium import List


# CPython's `bytearray` — a mutable, growable byte sequence, unlike
# Promethium's own `bytes` (a fixed-size native `Byte[]`, no `+`
# operator, no `bytes(n)` zero-fill constructor — see `struct.py`'s
# notes). Named `PyByteArray` rather than `ByteArray` on the established
# precedent of Cocoa/Toffee short-name collisions (`Queue`→`PyQueue`,
# `Date`→`PyDate`) — not confirmed to collide, but not worth a wasted
# rebuild to find out.
#
# Indexed access/mutation is backed by a plain `List[int]` (each element
# 0-255) — Promethium's own array-backed list, the same substrate
# `Deque`/`Counter`/etc. already use. `to_bytes()` is the part that used
# to be impossible: converting a *runtime-determined-length* `List[int]`
# into a real `bytes` value needs allocating a `bytes` buffer of that
# exact size, and the only previously-confirmed way to build a `bytes`
# value was a compile-time-sized literal. `RemObjects.Elements.RTL.Binary`
# — a genuine cross-platform growable byte buffer (backed per-target by
# `MemoryStream`/`NSMutableData`/`ByteArrayOutputStream`, found while
# looking for a `bytearray` substrate) turns out to solve exactly this:
# `Binary()` starts empty, `.Write(someBytes)` appends, and `.ToArray()`
# hands back a `bytes`-compatible native array of the exact accumulated
# length. Confirmed with a standalone probe before writing this file:
# `Binary().Write(...)` three times then `.ToArray()` round-tripped
# correctly and `.Length` matched the real accumulated count, both on
# Echoes. This corrects `struct.py`'s/`hashlib.py`'s "no dynamically-
# sized `bytes` allocation exists" note — it exists, it just isn't a
# `bytes`-literal-shaped API.
#
# `to_bytes()` writes one byte at a time (O(n) native calls) rather than
# batching runs into single `Write` calls — correct, not fast, matching
# `Deque`'s own documented "O(n) appendleft, real ring-buffer is future
# work" trade-off.


class PyByteArray:
    _entries: List[int]

    def __init__(self):
        self._entries = List[int]()

    def __init__(self, data: bytes):
        self._entries = List[int]()
        i: int = 0
        while i < data.Length:
            self._entries.append(data[i])
            i += 1

    def __init__(self, size: int):
        self._entries = List[int]()
        i: int = 0
        while i < size:
            self._entries.append(0)
            i += 1

    def __len__(self) -> int:
        return self._entries.__len__()

    def __getitem__(self, index: int) -> int:
        return self._entries[index]

    def __setitem__(self, index: int, value: int):
        self._entries[index] = value

    def append(self, value: int):
        self._entries.append(value)

    def extend(self, data: bytes):
        i: int = 0
        while i < data.Length:
            self._entries.append(data[i])
            i += 1

    def pop(self) -> int:
        return self._entries.pop()

    def clear(self):
        self._entries.clear()

    def copy(self) -> PyByteArray:
        result: PyByteArray = PyByteArray()
        i: int = 0
        while i < self._entries.__len__():
            result.append(self._entries[i])
            i += 1
        return result

    def to_bytes(self) -> bytes:
        buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
        i: int = 0
        while i < self._entries.__len__():
            one: bytes = b"\x00"
            one[0] = self._entries[i]
            buf.Write(one)
            i += 1
        return buf.ToArray()
