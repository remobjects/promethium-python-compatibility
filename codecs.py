@namespace("codecs")

from Promethium import ValueError

# A small, opt-in subset of Python's codecs module: `encode`/`decode`,
# UTF-8 only, built on `RemObjects.Elements.RTL.Encoding.UTF8`'s already-
# implemented `GetBytes`/`GetString` (per-target-branched inside RTL2
# itself — no new native call needed here, same story as `base64.py`/
# `binascii.py` reusing `Convert`). Closes the loop on this session's
# "bytes/binary-data isn't actually blocked" correction: `base64`/
# `binascii` convert between `bytes` and a *textual* representation of
# those bytes; this module is the missing piece that gets from an
# ordinary `str` to `bytes` (its UTF-8 encoding) and back.
#
# Only `"utf-8"` is accepted as the `encoding` argument — CPython's
# `codecs` supports dozens of encodings via a lookup registry; RTL2's
# `Encoding` class has several as class properties (`ASCII`, `UTF16LE`/
# `BE`, `UTF32LE`/`BE`) but only UTF-8 was wired up here, since it's the
# overwhelmingly common case and every other encoding would need its own
# confirmed-working call path. Any other encoding name raises
# `Promethium.ValueError` rather than being silently misencoded.
#
# `encode`/`decode` themselves are correct — round-tripped real
# multi-byte UTF-8 (`café`'s `é`, `[0xC3, 0xA9]`) byte-for-byte against
# CPython. What's genuinely broken, found while verifying this: **a
# Promethium `.py` source file mishandles non-ASCII characters typed
# directly into a string literal** — `"café"` written literally in source
# compiles and runs, but the accented character silently becomes `?` at
# some point before the string reaches runtime (confirmed: the source
# file's bytes are valid UTF-8 on disk, so this isn't an editor/encoding-
# of-the-file-itself problem — it's specific to how the compiler reads
# non-ASCII source text). Not a bug in this module or in `bytes`/RTL2's
# `Encoding` — a `bytes` literal built from `\xNN` hex escapes
# (`b"caf\xc3\xa9"`) round-trips through `decode`/`encode` perfectly;
# only *literal* non-ASCII characters typed directly into Promethium
# source are affected. Worth knowing for any future module whose test
# cases or literals might otherwise want non-ASCII text written directly.


def encode(s: str, encoding: str = "utf-8") -> bytes:
    if encoding != "utf-8" and encoding != "UTF-8":
        raise ValueError("codecs.encode: only 'utf-8' is supported")
    return RemObjects.Elements.RTL.Encoding.UTF8.GetBytes(s)


def decode(data: bytes, encoding: str = "utf-8") -> str:
    if encoding != "utf-8" and encoding != "UTF-8":
        raise ValueError("codecs.decode: only 'utf-8' is supported")
    return RemObjects.Elements.RTL.Encoding.UTF8.GetString(data)
