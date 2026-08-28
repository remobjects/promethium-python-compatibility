@namespace("hmac")

# HMAC-MD5 and HMAC-SHA256, built on `hashlib`'s hand-rolled MD5/SHA-256.
# HMAC needs to hash `(key XOR pad) || message` and then `(key XOR pad)
# || innerDigest` — two concatenations of byte buffers we can't
# physically build (no `bytes` concatenation operator, no dynamic
# allocation — see `struct.py`'s notes). `hashlib._md5Core`/
# `_sha256Core(prefix, prefixLen, suffix, suffixLen)` were added
# specifically to make this possible: each hashes the logical
# concatenation of two buffers without ever materializing one.
#
# Both MD5 and SHA-256 have a 64-byte block size, so both variants share
# the same key-normalization shape (RFC 2104): zero-padded to 64 bytes if
# the key is shorter, or hashed down (to 16 bytes for MD5, 32 for
# SHA-256) then zero-padded if longer. `_keyBlockMd5`/`_keyBlockSha256`
# are near-identical, kept separate rather than parameterized over which
# hash to call — named-function-as-a-value only works as a lambda here,
# not a plain function reference (see the Cocoa/Toffee short-name/
# function-ref notes), so passing `hashlib.md5`/`hashlib.sha256` in isn't
# a safe option worth risking on a per-target basis.
#
# Runtime-verified against Python's own `hmac.new(key, msg,
# hashlib.md5).hexdigest()` / `hmac.new(key, msg,
# hashlib.sha256).hexdigest()` for a short key/short message, a key
# longer than the 64-byte block size (forcing the hash-down path), and
# the empty-key/empty-message case.

from Promethium import List

def _zeroBlock64() -> bytes:
    return b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def _keyBlockMd5(key: bytes) -> bytes:
    block: bytes = _zeroBlock64()
    keyLen: int = key.Length
    if keyLen > 64:
        hashed: bytes = hashlib.md5(key)
        i: int = 0
        while i < hashed.Length:
            block[i] = hashed[i]
            i += 1
    else:
        i: int = 0
        while i < keyLen:
            block[i] = key[i]
            i += 1
    return block


def hmac_md5(key: bytes, message: bytes) -> bytes:
    keyBlock: bytes = _keyBlockMd5(key)
    ipadBlock: bytes = _zeroBlock64()
    opadBlock: bytes = _zeroBlock64()
    i: int = 0
    while i < 64:
        ipadBlock[i] = keyBlock[i] ^ 0x36
        opadBlock[i] = keyBlock[i] ^ 0x5C
        i += 1

    innerHash: bytes = hashlib._md5Core(ipadBlock, 64, message, message.Length)
    outerHash: bytes = hashlib._md5Core(opadBlock, 64, innerHash, 16)
    return outerHash


def hmac_md5_hexdigest(key: bytes, message: bytes) -> str:
    return binascii.hexlify(hmac_md5(key, message))


def _keyBlockSha256(key: bytes) -> bytes:
    block: bytes = _zeroBlock64()
    keyLen: int = key.Length
    if keyLen > 64:
        hashed: bytes = hashlib.sha256(key)
        i: int = 0
        while i < hashed.Length:
            block[i] = hashed[i]
            i += 1
    else:
        i: int = 0
        while i < keyLen:
            block[i] = key[i]
            i += 1
    return block


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    keyBlock: bytes = _keyBlockSha256(key)
    ipadBlock: bytes = _zeroBlock64()
    opadBlock: bytes = _zeroBlock64()
    i: int = 0
    while i < 64:
        ipadBlock[i] = keyBlock[i] ^ 0x36
        opadBlock[i] = keyBlock[i] ^ 0x5C
        i += 1

    innerHash: bytes = hashlib._sha256Core(ipadBlock, 64, message, message.Length)
    outerHash: bytes = hashlib._sha256Core(opadBlock, 64, innerHash, 32)
    return outerHash


def hmac_sha256_hexdigest(key: bytes, message: bytes) -> str:
    return binascii.hexlify(hmac_sha256(key, message))


def _keyBlockSha1(key: bytes) -> bytes:
    block: bytes = _zeroBlock64()
    keyLen: int = key.Length
    if keyLen > 64:
        hashed: bytes = hashlib.sha1(key)
        i: int = 0
        while i < hashed.Length:
            block[i] = hashed[i]
            i += 1
    else:
        i: int = 0
        while i < keyLen:
            block[i] = key[i]
            i += 1
    return block


def hmac_sha1(key: bytes, message: bytes) -> bytes:
    keyBlock: bytes = _keyBlockSha1(key)
    ipadBlock: bytes = _zeroBlock64()
    opadBlock: bytes = _zeroBlock64()
    i: int = 0
    while i < 64:
        ipadBlock[i] = keyBlock[i] ^ 0x36
        opadBlock[i] = keyBlock[i] ^ 0x5C
        i += 1

    innerHash: bytes = hashlib._sha1Core(ipadBlock, 64, message, message.Length)
    outerHash: bytes = hashlib._sha1Core(opadBlock, 64, innerHash, 20)
    return outerHash


def hmac_sha1_hexdigest(key: bytes, message: bytes) -> str:
    return binascii.hexlify(hmac_sha1(key, message))
