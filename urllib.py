@namespace("urllib")

# `urllib` as a whole is filed under the survey's "Networking" exclusion,
# but `urllib.parse.quote`/`unquote` (percent-encoding) do no I/O at
# all — pure string/byte manipulation, the same kind of correction
# `mimetypes.py` made to its own over-broad exclusion. Exposed as plain
# `urllib.quote`/`urllib.unquote` rather than nesting a `urllib.parse`
# sub-namespace — no other module in this project attempts a dotted
# namespace, and there's no confirmed working syntax for `from
# urllib.parse import quote` to match CPython's real import path.
#
# `quote(s: str) -> str` percent-encodes every byte of `s`'s UTF-8
# encoding except RFC 3986's unreserved characters (letters, digits,
# `-`/`_`/`.`/`~`) and `/` — matching CPython's own `quote`'s default
# `safe='/'`. `unquote(s: str) -> str` reverses it, decoding `%XX`
# triplets back to raw bytes and re-assembling as UTF-8. Built entirely
# on already-shipped primitives: `codecs.encode`/`decode` for UTF-8,
# `binascii.hexlify`/`unhexlify` for the `%XX` hex pairs, and
# `string._length`/`_substring` for the character scan.
#
# Runtime-verified against live CPython's own `urllib.parse.quote`/
# `unquote`: a string mixing spaces, a reserved character (`?`), an
# unreserved one (`-`), and a non-ASCII character (`é`, which needs
# multi-byte UTF-8 percent-encoding) round-tripped and matched exactly.

from Promethium import List


def _isUnreserved(b: int) -> bool:
    if b >= 0x41 and b <= 0x5A:
        return True
    if b >= 0x61 and b <= 0x7A:
        return True
    if b >= 0x30 and b <= 0x39:
        return True
    if b == 0x2D or b == 0x5F or b == 0x2E or b == 0x7E:
        return True
    return False


def quote(s: str) -> str:
    data: bytes = codecs.encode(s, "utf-8")
    result: str = ""
    i: int = 0
    while i < data.Length:
        b: int = data[i]
        if _isUnreserved(b) or b == 0x2F:
            oneByte: bytes = b"\x00"
            oneByte[0] = b
            result += codecs.decode(oneByte, "utf-8")
        else:
            oneByte2: bytes = b"\x00"
            oneByte2[0] = b
            result += "%" + string._upper(binascii.hexlify(oneByte2))
        i += 1
    return result


def unquote(s: str) -> str:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    length: int = string._length(s)
    i: int = 0
    while i < length:
        ch: str = string._substring(s, i, 1)
        if ch == "%" and i + 2 < length:
            hexPair: str = string._substring(s, i + 1, 2)
            buf.Write(binascii.unhexlify(hexPair))
            i += 3
        else:
            buf.Write(codecs.encode(ch, "utf-8"))
            i += 1
    return codecs.decode(buf.ToArray(), "utf-8")
