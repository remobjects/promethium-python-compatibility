@namespace("zipfile")

from Promethium import List, ValueError
from collections import OrderedDict

# The same "honest subset, not a placeholder" approach as `zlib.py`/
# `gzip.py`: real, standards-compliant ZIP archives (local file headers +
# central directory + end-of-central-directory record), but only ever
# writing and reading entries with compression method 0 ("stored",
# uncompressed) — no Huffman/LZ77, the same limitation `zlib.py` already
# documents, just one format layer up (ZIP's own stored-entry mode is a
# real, standard part of the format, used by real tools for content
# that's already compressed or where speed matters more than size).
#
# API deviates from CPython's class-based `zipfile.ZipFile` on purpose:
# `write_archive(names: List[str], contents: List[bytes]) -> bytes` /
# `read_archive(data: bytes) -> OrderedDict[str, bytes]` take/return
# plain lists instead — no `*args`/context managers/file-object streaming
# in this language slice, matching `struct.py`'s and `pbkdf2_hmac_sha256`'s
# established "concrete stand-in over exact parity" choices. Modification
# timestamps are always written as the DOS epoch (1980-01-01 00:00:00,
# the same deterministic-output choice `gzip.py` makes with `mtime=0`).
#
# `read_archive()` raises a clear `ValueError` on any entry whose
# compression method isn't 0 (stored) — the same honest-failure pattern
# `zlib.py`/`gzip.py` use for a real Huffman-coded stream — rather than
# silently returning garbage. It reads by following each central
# directory entry's own `localOffset`/filename/extra-field lengths to
# locate that entry's actual data, so it correctly reads archives written
# by real tools too (not just ones from `write_archive`), as long as
# every entry is stored.
#
# Exact byte layout (local file header, central directory header, and
# end-of-central-directory record field order/widths) was decoded field-
# by-field from a real archive produced by CPython's own `zipfile.
# ZipFile`/`struct.unpack`, not guessed from the spec — `version made
# by`/`external file attributes` are written as `0` here rather than
# mimicking CPython's own Unix-permission-encoded values, since neither
# affects whether a stored entry reads back correctly.
#
# Runtime-verified: (1) `write_archive()`'s two-entry output opens and
# reads back correctly with real CPython's `zipfile.ZipFile` — genuine
# interop, not just format compliance; (2) `read_archive()` correctly
# reads a real archive produced by CPython's own `zipfile.ZipFile` (with
# `ZIP_STORED`), recovering both entries' exact content; (3) this
# module's own `write_archive()` → `read_archive()` round-trips exactly.


def _writeU16LE(buf: RemObjects.Elements.RTL.Binary, value: int):
    b: bytes = b"\x00\x00"
    b[0] = value & 0xFF
    b[1] = (value >> 8) & 0xFF
    buf.Write(b)


def _writeU32LE(buf: RemObjects.Elements.RTL.Binary, value: int):
    b: bytes = b"\x00\x00\x00\x00"
    b[0] = value & 0xFF
    b[1] = (value >> 8) & 0xFF
    b[2] = (value >> 16) & 0xFF
    b[3] = (value >> 24) & 0xFF
    buf.Write(b)


def _readU16LE(data: bytes, pos: int) -> int:
    return data[pos] | (data[pos + 1] << 8)


def _readU32LE(data: bytes, pos: int) -> int:
    return data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16) | (data[pos + 3] << 24)


def write_archive(names: List[str], contents: List[bytes]) -> bytes:
    localBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    centralBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    count: int = names.__len__()

    i: int = 0
    while i < count:
        name: str = names[i]
        data: bytes = contents[i]
        nameBytes: bytes = codecs.encode(name, "utf-8")
        crc: int = binascii.crc32(data)
        size: int = data.Length
        localOffset: int = localBuf.Length

        localBuf.Write(b"\x50\x4b\x03\x04")
        _writeU16LE(localBuf, 20)
        _writeU16LE(localBuf, 0)
        _writeU16LE(localBuf, 0)
        _writeU16LE(localBuf, 0)
        _writeU16LE(localBuf, 0x21)
        _writeU32LE(localBuf, crc)
        _writeU32LE(localBuf, size)
        _writeU32LE(localBuf, size)
        _writeU16LE(localBuf, nameBytes.Length)
        _writeU16LE(localBuf, 0)
        localBuf.Write(nameBytes)
        localBuf.Write(data)

        centralBuf.Write(b"\x50\x4b\x01\x02")
        _writeU16LE(centralBuf, 20)
        _writeU16LE(centralBuf, 20)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0x21)
        _writeU32LE(centralBuf, crc)
        _writeU32LE(centralBuf, size)
        _writeU32LE(centralBuf, size)
        _writeU16LE(centralBuf, nameBytes.Length)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0)
        _writeU16LE(centralBuf, 0)
        _writeU32LE(centralBuf, 0)
        _writeU32LE(centralBuf, localOffset)
        centralBuf.Write(nameBytes)

        i += 1

    result: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    localBytes: bytes = localBuf.ToArray()
    result.Write(localBytes)

    centralDirBytes: bytes = centralBuf.ToArray()
    centralDirOffset: int = localBytes.Length
    result.Write(centralDirBytes)

    result.Write(b"\x50\x4b\x05\x06")
    _writeU16LE(result, 0)
    _writeU16LE(result, 0)
    _writeU16LE(result, count)
    _writeU16LE(result, count)
    _writeU32LE(result, centralDirBytes.Length)
    _writeU32LE(result, centralDirOffset)
    _writeU16LE(result, 0)

    return result.ToArray()


def read_archive(data: bytes) -> OrderedDict[str, bytes]:
    result: OrderedDict[str, bytes] = OrderedDict[str, bytes]()
    length: int = data.Length
    eocdPos: int = length - 22
    numEntries: int = _readU16LE(data, eocdPos + 10)
    cdOffset: int = _readU32LE(data, eocdPos + 16)

    pos: int = cdOffset
    i: int = 0
    while i < numEntries:
        method: int = _readU16LE(data, pos + 10)
        if method != 0:
            raise ValueError("zipfile.read_archive: only stored (uncompressed) entries are supported")

        uncompSize: int = _readU32LE(data, pos + 24)
        nameLen: int = _readU16LE(data, pos + 28)
        extraLen: int = _readU16LE(data, pos + 30)
        commentLen: int = _readU16LE(data, pos + 32)
        localOffset: int = _readU32LE(data, pos + 42)

        nameStart: int = pos + 46
        nameBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
        j: int = 0
        while j < nameLen:
            nameByte: bytes = b"\x00"
            nameByte[0] = data[nameStart + j]
            nameBuf.Write(nameByte)
            j += 1
        name: str = codecs.decode(nameBuf.ToArray(), "utf-8")

        localNameLen: int = _readU16LE(data, localOffset + 26)
        localExtraLen: int = _readU16LE(data, localOffset + 28)
        dataStart: int = localOffset + 30 + localNameLen + localExtraLen

        entryBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
        k: int = 0
        while k < uncompSize:
            dataByte: bytes = b"\x00"
            dataByte[0] = data[dataStart + k]
            entryBuf.Write(dataByte)
            k += 1
        result[name] = entryBuf.ToArray()

        pos = nameStart + nameLen + extraLen + commentLen
        i += 1

    return result
