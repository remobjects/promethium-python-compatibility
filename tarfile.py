@namespace("tarfile")

from Promethium import List, ValueError
from collections import OrderedDict

# Unlike `zlib`/`gzip`/`zipfile`, this is a *complete* implementation, not
# an honestly-scoped subset: the POSIX ustar TAR format has no
# compression concept at all — it's just fixed 512-byte header blocks
# followed by raw file data padded to a 512-byte boundary, terminated by
# a zero-filled block. Nothing here needed a "stored-only" carve-out the
# way `zlib.py`'s DEFLATE support did.
#
# API deviates from CPython's class-based `tarfile.TarFile` the same way
# `zipfile.py` deviates from `zipfile.ZipFile`: `write_archive(names:
# List[str], contents: List[bytes]) -> bytes` / `read_archive(data:
# bytes) -> OrderedDict[str, bytes]` take/return plain lists — no
# `*args`/context managers/file-object streaming in this language slice.
# Every entry is written as a regular file (typeflag `'0'`), mode
# `0o644`, uid/gid/devmajor/devminor `0`, empty uname/gname, and mtime
# `0` (the same deterministic-output choice `gzip.py`/`zipfile.py` make).
# Filenames longer than 100 bytes aren't supported (the classic ustar
# `name` field has no room for more — real tar implementations use a GNU
# or POSIX extension header for long names, not attempted here) and raise
# a clear `ValueError` rather than silently truncating.
#
# Header field layout (name/mode/uid/gid/size/mtime/chksum/typeflag/
# linkname/magic/version/uname/gname/devmajor/devminor/prefix, each
# field's exact byte offset and width, and the checksum algorithm — sum
# of all header bytes with the checksum field itself treated as 8 ASCII
# spaces during the sum, stored as 6 octal digits + NUL + space) was
# decoded field-by-field from a real archive CPython's own `tarfile`
# module produced, not guessed from the spec. `write_archive()` does not
# pad the overall output to a full 10240-byte "record" the way GNU tar's
# default blocking factor does — confirmed unnecessary by testing
# directly: real CPython's `tarfile.open()` reads an unpadded archive
# (header + data + just the two end-of-archive zero blocks) correctly,
# it doesn't require the file to reach a full record boundary.
# `read_archive()` does not validate the header checksum against a
# recomputed one — a curated-scope limitation, not a correctness gap for
# well-formed input — and stops as soon as it encounters a zero-filled
# block where a header was expected, the same lenient-reader behavior
# real tar tools use rather than requiring exactly two trailing zero
# blocks.
#
# Runtime-verified genuine two-way interop, both directions independently
# confirmed: (1) a two-entry archive from this module's `write_archive()`
# opens and reads back correctly with real CPython's `tarfile.open()`
# (`getnames()`, `extractfile().read()` both correct for both entries);
# (2) this module's `read_archive()` correctly reads a two-entry archive
# real CPython's `tarfile` produced; (3) this module's own
# `write_archive()` → `read_archive()` round-trips exactly.


def _octalDigit(d: int) -> str:
    if d == 0:
        return "0"
    elif d == 1:
        return "1"
    elif d == 2:
        return "2"
    elif d == 3:
        return "3"
    elif d == 4:
        return "4"
    elif d == 5:
        return "5"
    elif d == 6:
        return "6"
    else:
        return "7"


def _octalString(value: int, digitCount: int) -> str:
    result: str = ""
    v: int = value
    i: int = 0
    while i < digitCount:
        digit: int = v % 8
        result = _octalDigit(digit) + result
        v = v / 8
        i += 1
    return result


def _writeOctalField(buf: RemObjects.Elements.RTL.Binary, value: int, digitCount: int):
    s: str = _octalString(value, digitCount)
    sBytes: bytes = codecs.encode(s, "utf-8")
    buf.Write(sBytes)
    buf.Write(b"\x00")


def _writeZeros(buf: RemObjects.Elements.RTL.Binary, count: int):
    i: int = 0
    while i < count:
        buf.Write(b"\x00")
        i += 1


def _buildHeader(name: str, size: int) -> bytes:
    nameBytes: bytes = codecs.encode(name, "utf-8")
    nameLen: int = nameBytes.Length
    if nameLen > 100:
        raise ValueError("tarfile.write_archive: filename longer than 100 bytes is not supported")

    pre: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    pre.Write(nameBytes)
    _writeZeros(pre, 100 - nameLen)

    _writeOctalField(pre, 420, 7)
    _writeOctalField(pre, 0, 7)
    _writeOctalField(pre, 0, 7)
    _writeOctalField(pre, size, 11)
    _writeOctalField(pre, 0, 11)

    j: int = 0
    while j < 8:
        pre.Write(b"\x20")
        j += 1

    pre.Write(b"0")

    _writeZeros(pre, 100)

    pre.Write(codecs.encode("ustar", "utf-8"))
    pre.Write(b"\x00")
    pre.Write(codecs.encode("00", "utf-8"))

    _writeZeros(pre, 32)
    _writeZeros(pre, 32)

    _writeOctalField(pre, 0, 7)
    _writeOctalField(pre, 0, 7)

    _writeZeros(pre, 155)
    _writeZeros(pre, 12)

    headerBytes: bytes = pre.ToArray()

    checksum: int = 0
    r: int = 0
    while r < 512:
        checksum = checksum + headerBytes[r]
        r += 1

    checksumBytes: bytes = codecs.encode(_octalString(checksum, 6), "utf-8")
    s: int = 0
    while s < 6:
        headerBytes[148 + s] = checksumBytes[s]
        s += 1
    headerBytes[154] = 0
    headerBytes[155] = 0x20

    return headerBytes


def write_archive(names: List[str], contents: List[bytes]) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    count: int = names.__len__()

    i: int = 0
    while i < count:
        name: str = names[i]
        data: bytes = contents[i]
        buf.Write(_buildHeader(name, data.Length))
        buf.Write(data)
        padLen: int = (512 - (data.Length % 512)) % 512
        _writeZeros(buf, padLen)
        i += 1

    _writeZeros(buf, 1024)

    return buf.ToArray()


def _readOctalField(data: bytes, start: int, length: int) -> int:
    value: int = 0
    i: int = 0
    while i < length:
        b: int = data[start + i]
        if b >= 0x30 and b <= 0x37:
            value = value * 8 + (b - 0x30)
        i += 1
    return value


def read_archive(data: bytes) -> OrderedDict[str, bytes]:
    result: OrderedDict[str, bytes] = OrderedDict[str, bytes]()
    length: int = data.Length
    pos: int = 0

    while pos + 512 <= length:
        if data[pos] == 0:
            break

        nameBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
        i: int = 0
        while i < 100:
            b: int = data[pos + i]
            if b == 0:
                break
            oneByte: bytes = b"\x00"
            oneByte[0] = b
            nameBuf.Write(oneByte)
            i += 1
        name: str = codecs.decode(nameBuf.ToArray(), "utf-8")

        size: int = _readOctalField(data, pos + 124, 11)

        dataStart: int = pos + 512
        entryBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
        j: int = 0
        while j < size:
            dataByte: bytes = b"\x00"
            dataByte[0] = data[dataStart + j]
            entryBuf.Write(dataByte)
            j += 1
        result[name] = entryBuf.ToArray()

        padLen: int = (512 - (size % 512)) % 512
        pos = dataStart + size + padLen

    return result
