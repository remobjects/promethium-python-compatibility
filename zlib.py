@namespace("zlib")

from Promethium import ValueError

# A genuinely honest subset of Python's `zlib`: real, standards-compliant
# zlib/DEFLATE (RFC 1950/1951) container format, but only ever emitting
# and reading DEFLATE's *stored* (BTYPE=00, uncompressed) block type —
# no Huffman coding, no LZ77 back-references. This was previously written
# off entirely in the survey ("needs a real compression algorithm"), and
# actual compression (BTYPE=01/10) genuinely does — but the *stored*
# block type is a simple, well-defined container format that needs none
# of that: a 2-byte zlib header, one or more blocks each holding raw
# bytes verbatim behind a tiny length header, and a trailing Adler-32
# checksum. `compress()` here produces exactly what CPython's own
# `zlib.compress(data, 0)` (level 0 = no compression) produces — verified
# directly, not assumed — so this is real interop, not an approximation:
# output from this module decompresses correctly with real Python's
# `zlib.decompress`, and output from `zlib.compress(data, 0)` decompresses
# correctly with this module's `decompress()`.
#
# `decompress()` only understands stored blocks — given a real compressed
# (Huffman-coded) stream, it raises a clear `ValueError` explaining the
# limitation rather than silently misbehaving, the same honest-failure
# choice `DefaultDict.py` makes for its own Toffee limitation.
# `decompress()` also does not validate the trailing Adler-32 checksum
# against the decompressed output — a curated-scope limitation, not a
# correctness gap for well-formed input.
#
# Built entirely on already-shipped infrastructure: `RemObjects.Elements.
# RTL.Binary` (`Write`/`ToArray`) for the variable-length output neither
# `compress` nor `decompress` can size in advance — the same tool
# `PyByteArray.py`/`hashlib.pbkdf2_hmac_sha256` already use for exactly
# this reason.
#
# Runtime-verified: (1) `compress()`'s output byte-for-byte matches real
# CPython's `zlib.compress(data, 0)` for a short single-block input — for
# a large (80,000-byte) input needing multiple blocks, the two outputs
# differ in *where* they split (CPython's own zlib doesn't always chunk
# at the maximum 65535 bytes — an internal buffering detail, not part of
# the format), but both are exactly 80016 bytes and both are valid: (2)
# real CPython's `zlib.decompress()` correctly decompresses this module's
# multi-block output back to the original 80,000 bytes — genuine interop,
# confirmed directly, not assumed from format compliance; (3) this
# module's own `compress()` → `decompress()` round-trips back to the
# original bytes for both inputs; (4) `adler32()` matches CPython's
# `zlib.adler32()` exactly (compared as signed-int32 bit patterns, same
# convention `binascii.crc32` already established, since Promethium's
# `int` is signed 32-bit and CPython's checksum functions return
# unsigned).


def adler32(data: bytes) -> int:
    a: int = 1
    b: int = 0
    i: int = 0
    length: int = data.Length
    while i < length:
        a = (a + data[i]) % 65521
        b = (b + a) % 65521
        i += 1
    return (b << 16) | a


def _deflateStored(data: bytes) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    length: int = data.Length
    if length == 0:
        emptyBlock: bytes = b"\x01\x00\x00\xff\xff"
        buf.Write(emptyBlock)
        return buf.ToArray()

    offset: int = 0
    while offset < length:
        remaining: int = length - offset
        chunkLen: int = 65535
        if remaining < 65535:
            chunkLen = remaining
        isFinal: bool = (offset + chunkLen) >= length

        blockHeader: bytes = b"\x00"
        if isFinal:
            blockHeader[0] = 1
        buf.Write(blockHeader)

        nlen: int = (chunkLen ^ -1) & 0xFFFF
        lenBytes: bytes = b"\x00\x00\x00\x00"
        lenBytes[0] = chunkLen & 0xFF
        lenBytes[1] = (chunkLen >> 8) & 0xFF
        lenBytes[2] = nlen & 0xFF
        lenBytes[3] = (nlen >> 8) & 0xFF
        buf.Write(lenBytes)

        i: int = 0
        while i < chunkLen:
            one: bytes = b"\x00"
            one[0] = data[offset + i]
            buf.Write(one)
            i += 1

        offset += chunkLen

    return buf.ToArray()


def compress(data: bytes) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    zlibHeader: bytes = b"\x78\x01"
    buf.Write(zlibHeader)
    buf.Write(_deflateStored(data))

    checksum: int = adler32(data)
    checksumBytes: bytes = b"\x00\x00\x00\x00"
    checksumBytes[0] = (checksum >> 24) & 0xFF
    checksumBytes[1] = (checksum >> 16) & 0xFF
    checksumBytes[2] = (checksum >> 8) & 0xFF
    checksumBytes[3] = checksum & 0xFF
    buf.Write(checksumBytes)

    return buf.ToArray()


def _inflateStored(data: bytes, startPos: int) -> bytes:
    outputBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    pos: int = startPos
    isFinal: bool = False
    while not isFinal:
        blockHeader: int = data[pos]
        isFinal = (blockHeader & 1) != 0
        btype: int = (blockHeader >> 1) & 3
        if btype != 0:
            raise ValueError("zlib.decompress: only stored (uncompressed) DEFLATE blocks are supported")
        pos += 1

        lenLow: int = data[pos]
        lenHigh: int = data[pos + 1]
        chunkLen: int = lenLow | (lenHigh << 8)
        pos += 4

        i: int = 0
        while i < chunkLen:
            one: bytes = b"\x00"
            one[0] = data[pos + i]
            outputBuf.Write(one)
            i += 1
        pos += chunkLen

    return outputBuf.ToArray()


def decompress(data: bytes) -> bytes:
    return _inflateStored(data, 2)
