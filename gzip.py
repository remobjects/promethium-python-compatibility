@namespace("gzip")

# Real gzip (RFC 1952) container format, sharing `zlib.py`'s DEFLATE-
# stored-blocks approach entirely: gzip wraps the exact same
# uncompressed DEFLATE stream `zlib._deflateStored` already produces —
# just with different outer framing (a 10-byte header instead of zlib's
# 2-byte one) and a CRC-32 + uncompressed-size trailer instead of an
# Adler-32 one. Built directly on `zlib._deflateStored`/`zlib.
# _inflateStored` (a `gzip` → `zlib` cross-namespace call, same pattern
# `hashlib.pbkdf2_hmac_sha256`'s `hashlib` → `hmac` call already
# established) and `binascii.crc32`.
#
# `mtime` is always written as 0 (matches CPython's own `gzip.GzipFile`
# when `mtime=0` is passed explicitly) rather than real wall-clock time —
# deterministic output, and mtime has no effect on decompression
# correctness either way. `OS` is written as `0xFF` ("unknown"), also
# matching CPython's own default.
#
# `decompress()` inherits the same limitation as `zlib.py`'s
# `decompress()`: it only understands the stored-block DEFLATE stream
# `compress()` produces, raising a clear `ValueError` (via `zlib.
# decompress`'s underlying `_inflateStored`) on a real Huffman-coded
# stream rather than misbehaving silently; it also doesn't validate the
# trailing CRC-32/ISIZE against the decompressed output.
#
# Runtime-verified: `compress()`'s output is byte-for-byte identical to
# CPython's own `gzip.GzipFile(fileobj=..., mode='wb', mtime=0,
# compresslevel=0)` output for a short input (single DEFLATE block, no
# chunk-boundary ambiguity — see `zlib.py`'s notes on why multi-block
# outputs can validly differ there); CPython's own `gzip.decompress()`
# correctly reads this module's output back to the original bytes;
# this module's own `compress()` → `decompress()` round-trips exactly.

def compress(data: bytes) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    header: bytes = b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff"
    buf.Write(header)
    buf.Write(zlib._deflateStored(data))

    crc: int = binascii.crc32(data)
    crcBytes: bytes = b"\x00\x00\x00\x00"
    crcBytes[0] = crc & 0xFF
    crcBytes[1] = (crc >> 8) & 0xFF
    crcBytes[2] = (crc >> 16) & 0xFF
    crcBytes[3] = (crc >> 24) & 0xFF
    buf.Write(crcBytes)

    size: int = data.Length
    sizeBytes: bytes = b"\x00\x00\x00\x00"
    sizeBytes[0] = size & 0xFF
    sizeBytes[1] = (size >> 8) & 0xFF
    sizeBytes[2] = (size >> 16) & 0xFF
    sizeBytes[3] = (size >> 24) & 0xFF
    buf.Write(sizeBytes)

    return buf.ToArray()


def decompress(data: bytes) -> bytes:
    return zlib._inflateStored(data, 10)
