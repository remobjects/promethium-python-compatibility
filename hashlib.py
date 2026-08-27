@namespace("hashlib")

from Promethium import List

# A small, opt-in subset of Python's hashlib module: `md5(data) -> bytes`
# (a 16-byte digest) plus `md5_hexdigest(data) -> str`. A full hand-rolled
# implementation of RFC 1321's algorithm — no cross-platform hash
# primitive was found anywhere in RTL2 (the earlier bytes-substrate
# research pass found only a Toffee-only `CC_SHA1` TLS-certificate-
# fingerprint helper, not a reusable one), the same situation `re.py` was
# in before RTL2 got its own regex engine as a side task. This is that
# side task done in pure Promethium instead: no native call anywhere in
# this file, only bit arithmetic, the same category as `struct.py`/
# `binascii.py`'s `crc32`.
#
# Two Promethium-specific things needed solving beyond the algorithm
# itself:
#
# - **No dynamically-sized `bytes` allocation exists** (see `struct.py`'s
#   notes — `bytes(n)` isn't a valid constructor, and a fixed-size
#   literal is the only confirmed way to get one). MD5 needs to work over
#   a *padded* message whose length depends on the input's length, which
#   would ordinarily mean allocating a padded buffer at runtime. Sidestep:
#   `_virtualByte` computes what byte *would* be at any position of the
#   padded message — from the real input while `p < len(data)`, the
#   single `0x80` marker byte at `p == len(data)`, zero padding, or the
#   trailing 8-byte bit-length field — without ever materializing the
#   padded buffer. Only the original `data` and a 16-byte digest buffer
#   (a fixed compile-time size) are ever actually allocated.
# - **Promethium's `int` is signed 32-bit with an arithmetic (sign-
#   extending) `>>`**, but MD5's left-rotate needs a *logical* right
#   shift as half of it. `_logicalShiftRight` generalizes the single-bit
#   trick `binascii.py`'s `crc32` already established (`(value >> 1) &
#   0x7FFFFFFF` is unconditionally correct for one bit, since that's the
#   only bit an arithmetic and logical shift-by-1 can ever disagree on)
#   by simply repeating it — correct by construction, not by a riskier
#   direct-mask formula. Bitwise NOT is spelled `value ^ -1` (XOR with
#   all-ones), matching `crc32`'s own final XOR. 32-bit addition wraps
#   silently on overflow (confirmed directly: `2147483647 + 1` produces
#   `-2147483648`, not an exception) — exactly the modular arithmetic
#   MD5's compression function needs, with no extra masking required.
#
# Only supports inputs whose *bit* length fits in 32 bits (message length
# under ~268MB) — the trailing 8-byte length field's upper 4 bytes are
# always written as zero rather than computed, a curated-scope limit for
# an already-large input size, not a correctness gap for realistic use.
#
# Runtime-verified against all seven of RFC 1321's own official MD5 test
# vectors (the empty string, `"a"`, `"abc"`, `"message digest"`, the
# lowercase alphabet, mixed-case-alphanumeric, and an 80-digit numeric
# string) and cross-checked against live CPython's `hashlib.md5` on the
# same inputs — every digest matched exactly. Found and fixed one real
# bug getting here: `_sTable()`'s construction interleaved all four
# 4-shift groups on each of four outer loop passes (producing the same
# 16-value sequence four times over) instead of repeating each group four
# times before moving to the next — a copy-paste-shaped loop-nesting
# mistake, not a bit-arithmetic one; the `_rotl32`/`_logicalShiftRight`/
# `_not32` primitives it depends on were each independently correct
# (verified in isolation: `_rotl32(1, 1) == 2`, `_rotl32(-2147483648, 1)
# == 1`, `_logicalShiftRight(-1, 1) == 2147483647`, `_not32(0) == -1`,
# `_not32(-1) == 0` — all as expected before the real bug was found).
#
# `_md5Core(prefix, prefixLen, suffix, suffixLen)` hashes the *logical*
# concatenation of two byte buffers without ever materializing a combined
# one — `_virtualByte` reads from `prefix` while `p < prefixLen`, from
# `suffix` for the rest of the real data, then the same padding/length-
# field logic as before. `md5(data)` is just `_md5Core(data, data.Length,
# data, 0)` (an unused zero-length suffix). This exists so `hmac.py` can
# hash `(key-derived block) || message` without a `bytes` concatenation
# operator, which still doesn't exist (see `struct.py`'s notes).


def _logicalShiftRight(value: int, n: int) -> int:
    result: int = value
    i: int = 0
    while i < n:
        result = (result >> 1) & 0x7FFFFFFF
        i += 1
    return result


def _rotl32(value: int, amount: int) -> int:
    left: int = value << amount
    right: int = _logicalShiftRight(value, 32 - amount)
    return left | right


def _not32(value: int) -> int:
    return value ^ -1


def _sTable() -> List[int]:
    result: List[int] = List[int]()
    row1: List[int] = List[int]()
    row1.append(7)
    row1.append(12)
    row1.append(17)
    row1.append(22)
    row2: List[int] = List[int]()
    row2.append(5)
    row2.append(9)
    row2.append(14)
    row2.append(20)
    row3: List[int] = List[int]()
    row3.append(4)
    row3.append(11)
    row3.append(16)
    row3.append(23)
    row4: List[int] = List[int]()
    row4.append(6)
    row4.append(10)
    row4.append(15)
    row4.append(21)
    repeat: int = 0
    while repeat < 4:
        entry: int = 0
        while entry < 4:
            result.append(row1[entry])
            entry += 1
        repeat += 1
    repeat = 0
    while repeat < 4:
        entry: int = 0
        while entry < 4:
            result.append(row2[entry])
            entry += 1
        repeat += 1
    repeat = 0
    while repeat < 4:
        entry: int = 0
        while entry < 4:
            result.append(row3[entry])
            entry += 1
        repeat += 1
    repeat = 0
    while repeat < 4:
        entry: int = 0
        while entry < 4:
            result.append(row4[entry])
            entry += 1
        repeat += 1
    return result


def _kTable() -> List[int]:
    result: List[int] = List[int]()
    result.append(-680876936)
    result.append(-389564586)
    result.append(606105819)
    result.append(-1044525330)
    result.append(-176418897)
    result.append(1200080426)
    result.append(-1473231341)
    result.append(-45705983)
    result.append(1770035416)
    result.append(-1958414417)
    result.append(-42063)
    result.append(-1990404162)
    result.append(1804603682)
    result.append(-40341101)
    result.append(-1502002290)
    result.append(1236535329)
    result.append(-165796510)
    result.append(-1069501632)
    result.append(643717713)
    result.append(-373897302)
    result.append(-701558691)
    result.append(38016083)
    result.append(-660478335)
    result.append(-405537848)
    result.append(568446438)
    result.append(-1019803690)
    result.append(-187363961)
    result.append(1163531501)
    result.append(-1444681467)
    result.append(-51403784)
    result.append(1735328473)
    result.append(-1926607734)
    result.append(-378558)
    result.append(-2022574463)
    result.append(1839030562)
    result.append(-35309556)
    result.append(-1530992060)
    result.append(1272893353)
    result.append(-155497632)
    result.append(-1094730640)
    result.append(681279174)
    result.append(-358537222)
    result.append(-722521979)
    result.append(76029189)
    result.append(-640364487)
    result.append(-421815835)
    result.append(530742520)
    result.append(-995338651)
    result.append(-198630844)
    result.append(1126891415)
    result.append(-1416354905)
    result.append(-57434055)
    result.append(1700485571)
    result.append(-1894986606)
    result.append(-1051523)
    result.append(-2054922799)
    result.append(1873313359)
    result.append(-30611744)
    result.append(-1560198380)
    result.append(1309151649)
    result.append(-145523070)
    result.append(-1120210379)
    result.append(718787259)
    result.append(-343485551)
    return result


def _virtualByte(prefix: bytes, prefixLen: int, suffix: bytes, suffixLen: int, totalLen: int, paddedLen: int, p: int) -> int:
    if p < prefixLen:
        return prefix[p]
    if p < totalLen:
        return suffix[p - prefixLen]
    if p == totalLen:
        return 0x80
    lengthFieldStart: int = paddedLen - 8
    if p < lengthFieldStart:
        return 0
    offsetInField: int = p - lengthFieldStart
    if offsetInField < 4:
        bitLen: int = totalLen * 8
        return (bitLen >> (offsetInField * 8)) & 0xFF
    return 0


def _writeWordLE(data: bytes, offset: int, value: int):
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = (value >> 16) & 0xFF
    data[offset + 3] = (value >> 24) & 0xFF


def _md5Core(prefix: bytes, prefixLen: int, suffix: bytes, suffixLen: int) -> bytes:
    totalLen: int = prefixLen + suffixLen
    paddedLen: int = ((totalLen + 1 + 8 + 63) / 64) * 64
    numChunks: int = paddedLen / 64
    kTable: List[int] = _kTable()
    sTable: List[int] = _sTable()

    a0: int = 1732584193
    b0: int = -271733879
    c0: int = -1732584194
    d0: int = 271733878

    chunkIndex: int = 0
    while chunkIndex < numChunks:
        chunkStart: int = chunkIndex * 64
        m: List[int] = List[int]()
        wordIndex: int = 0
        while wordIndex < 16:
            base: int = chunkStart + wordIndex * 4
            byte0: int = _virtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base)
            byte1: int = _virtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 1)
            byte2: int = _virtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 2)
            byte3: int = _virtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 3)
            word: int = byte0 | (byte1 << 8) | (byte2 << 16) | (byte3 << 24)
            m.append(word)
            wordIndex += 1

        A: int = a0
        B: int = b0
        C: int = c0
        D: int = d0

        i: int = 0
        while i < 64:
            F: int = 0
            g: int = 0
            if i < 16:
                F = (B & C) | (_not32(B) & D)
                g = i
            elif i < 32:
                F = (D & B) | (_not32(D) & C)
                g = (5 * i + 1) % 16
            elif i < 48:
                F = B ^ C ^ D
                g = (3 * i + 5) % 16
            else:
                F = C ^ (B | _not32(D))
                g = (7 * i) % 16

            F = F + A + kTable[i] + m[g]
            A = D
            D = C
            C = B
            B = B + _rotl32(F, sTable[i])
            i += 1

        a0 = a0 + A
        b0 = b0 + B
        c0 = c0 + C
        d0 = d0 + D

        chunkIndex += 1

    result: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    _writeWordLE(result, 0, a0)
    _writeWordLE(result, 4, b0)
    _writeWordLE(result, 8, c0)
    _writeWordLE(result, 12, d0)
    return result


def md5(data: bytes) -> bytes:
    return _md5Core(data, data.Length, data, 0)


def md5_hexdigest(data: bytes) -> str:
    return binascii.hexlify(md5(data))


# SHA-256 (FIPS 180-4). Same "no native call, only bit arithmetic, no
# dynamically-sized bytes allocation" category as `md5` above, and reuses
# its `_rotl32`/`_logicalShiftRight`/`_not32` primitives — `_rotr32` is
# just `_rotl32(value, 32 - amount)`. Two things differ from MD5 enough
# to need their own code rather than reusing `_virtualByte`/`_md5Core`:
# SHA-256 packs bytes into 32-bit words **big-endian** (MD5 is little-
# endian) and appends the trailing bit-length field big-endian too, so
# `_sha256VirtualByte` and `_writeWordBE` are separate, mirror-image
# versions of `_virtualByte`/`_writeWordLE`. Structured the same
# two-buffer way as the MD5 core (`_sha256Core(prefix, prefixLen, suffix,
# suffixLen)`, with `sha256(data)` just calling `_sha256Core(data,
# data.Length, data, 0)`) so `hmac.py` can build HMAC-SHA256 the same way
# it built HMAC-MD5, without a `bytes` concatenation operator.
#
# `_sha256KTable`'s 64 round constants (fractional bits of the cube roots
# of the first 64 primes) and the 8 initial hash values (fractional bits
# of the square roots of the first 8 primes) were computed with 50-digit
# decimal precision in Python, not transcribed from a reference table by
# hand — the same care `_kTable`'s MD5 bug taught was worth taking.
#
# Runtime-verified against four of NIST's own SHA-256 test vectors (the
# empty string, `"abc"`, and two longer multi-block messages) and cross-
# checked against live CPython's `hashlib.sha256` on the same inputs —
# every digest matched exactly on the first attempt.

def _rotr32(value: int, amount: int) -> int:
    return _rotl32(value, 32 - amount)


def _sha256KTable() -> List[int]:
    result: List[int] = List[int]()
    result.append(1116352408)
    result.append(1899447441)
    result.append(-1245643825)
    result.append(-373957723)
    result.append(961987163)
    result.append(1508970993)
    result.append(-1841331548)
    result.append(-1424204075)
    result.append(-670586216)
    result.append(310598401)
    result.append(607225278)
    result.append(1426881987)
    result.append(1925078388)
    result.append(-2132889090)
    result.append(-1680079193)
    result.append(-1046744716)
    result.append(-459576895)
    result.append(-272742522)
    result.append(264347078)
    result.append(604807628)
    result.append(770255983)
    result.append(1249150122)
    result.append(1555081692)
    result.append(1996064986)
    result.append(-1740746414)
    result.append(-1473132947)
    result.append(-1341970488)
    result.append(-1084653625)
    result.append(-958395405)
    result.append(-710438585)
    result.append(113926993)
    result.append(338241895)
    result.append(666307205)
    result.append(773529912)
    result.append(1294757372)
    result.append(1396182291)
    result.append(1695183700)
    result.append(1986661051)
    result.append(-2117940946)
    result.append(-1838011259)
    result.append(-1564481375)
    result.append(-1474664885)
    result.append(-1035236496)
    result.append(-949202525)
    result.append(-778901479)
    result.append(-694614492)
    result.append(-200395387)
    result.append(275423344)
    result.append(430227734)
    result.append(506948616)
    result.append(659060556)
    result.append(883997877)
    result.append(958139571)
    result.append(1322822218)
    result.append(1537002063)
    result.append(1747873779)
    result.append(1955562222)
    result.append(2024104815)
    result.append(-2067236844)
    result.append(-1933114872)
    result.append(-1866530822)
    result.append(-1538233109)
    result.append(-1090935817)
    result.append(-965641998)
    return result


def _sha256VirtualByte(prefix: bytes, prefixLen: int, suffix: bytes, suffixLen: int, totalLen: int, paddedLen: int, p: int) -> int:
    if p < prefixLen:
        return prefix[p]
    if p < totalLen:
        return suffix[p - prefixLen]
    if p == totalLen:
        return 0x80
    lengthFieldStart: int = paddedLen - 8
    if p < lengthFieldStart:
        return 0
    offsetInField: int = p - lengthFieldStart
    if offsetInField < 4:
        return 0
    bitLen: int = totalLen * 8
    shiftAmount: int = (7 - offsetInField) * 8
    return (bitLen >> shiftAmount) & 0xFF


def _writeWordBE(data: bytes, offset: int, value: int):
    data[offset] = (value >> 24) & 0xFF
    data[offset + 1] = (value >> 16) & 0xFF
    data[offset + 2] = (value >> 8) & 0xFF
    data[offset + 3] = value & 0xFF


def _sha256Core(prefix: bytes, prefixLen: int, suffix: bytes, suffixLen: int) -> bytes:
    totalLen: int = prefixLen + suffixLen
    paddedLen: int = ((totalLen + 1 + 8 + 63) / 64) * 64
    numChunks: int = paddedLen / 64
    kTable: List[int] = _sha256KTable()

    h0: int = 1779033703
    h1: int = -1150833019
    h2: int = 1013904242
    h3: int = -1521486534
    h4: int = 1359893119
    h5: int = -1694144372
    h6: int = 528734635
    h7: int = 1541459225

    chunkIndex: int = 0
    while chunkIndex < numChunks:
        chunkStart: int = chunkIndex * 64
        w: List[int] = List[int]()
        wordIndex: int = 0
        while wordIndex < 16:
            base: int = chunkStart + wordIndex * 4
            byte0: int = _sha256VirtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base)
            byte1: int = _sha256VirtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 1)
            byte2: int = _sha256VirtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 2)
            byte3: int = _sha256VirtualByte(prefix, prefixLen, suffix, suffixLen, totalLen, paddedLen, base + 3)
            word: int = (byte0 << 24) | (byte1 << 16) | (byte2 << 8) | byte3
            w.append(word)
            wordIndex += 1

        t: int = 16
        while t < 64:
            s0: int = _rotr32(w[t - 15], 7) ^ _rotr32(w[t - 15], 18) ^ _logicalShiftRight(w[t - 15], 3)
            s1: int = _rotr32(w[t - 2], 17) ^ _rotr32(w[t - 2], 19) ^ _logicalShiftRight(w[t - 2], 10)
            w.append(w[t - 16] + s0 + w[t - 7] + s1)
            t += 1

        a: int = h0
        b: int = h1
        c: int = h2
        d: int = h3
        e: int = h4
        f: int = h5
        g: int = h6
        h: int = h7

        i: int = 0
        while i < 64:
            bigS1: int = _rotr32(e, 6) ^ _rotr32(e, 11) ^ _rotr32(e, 25)
            ch: int = (e & f) ^ (_not32(e) & g)
            temp1: int = h + bigS1 + ch + kTable[i] + w[i]
            bigS0: int = _rotr32(a, 2) ^ _rotr32(a, 13) ^ _rotr32(a, 22)
            maj: int = (a & b) ^ (a & c) ^ (b & c)
            temp2: int = bigS0 + maj
            h = g
            g = f
            f = e
            e = d + temp1
            d = c
            c = b
            b = a
            a = temp1 + temp2
            i += 1

        h0 = h0 + a
        h1 = h1 + b
        h2 = h2 + c
        h3 = h3 + d
        h4 = h4 + e
        h5 = h5 + f
        h6 = h6 + g
        h7 = h7 + h

        chunkIndex += 1

    result: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    _writeWordBE(result, 0, h0)
    _writeWordBE(result, 4, h1)
    _writeWordBE(result, 8, h2)
    _writeWordBE(result, 12, h3)
    _writeWordBE(result, 16, h4)
    _writeWordBE(result, 20, h5)
    _writeWordBE(result, 24, h6)
    _writeWordBE(result, 28, h7)
    return result


def sha256(data: bytes) -> bytes:
    return _sha256Core(data, data.Length, data, 0)


def sha256_hexdigest(data: bytes) -> str:
    return binascii.hexlify(sha256(data))
