@namespace("gettext")

from Promethium import List

# `gettext` was originally filed under "Locale & text data — needs real
# Unicode/locale data tables", the same bucket as `unicodedata`/`locale`.
# That was wrong: `gettext`'s actual job — parsing a compiled `.mo` message
# catalog and looking up a translated string by its original — needs no
# Unicode category tables, no locale-aware collation, no platform locale
# data at all. It's pure binary file parsing, the same category `wave.py`/
# `zipfile.py`/`tarfile.py` already proved tractable, over a well-documented,
# stable format (GNU gettext's `.mo` binary layout, unchanged for decades).
#
# `Translations.load(data: bytes)` parses a real `.mo` file: an 8-entry
# little-endian header (magic `0x950412de`, revision, string count, and
# offsets to the original/translated string tables — the hash table that
# follows is real but never read, the same "safe to skip, not needed for
# correctness" call CPython's own `gettext.GNUTranslations` makes), then
# each original/translated string pair. Plural entries store their
# `msgid`/`msgid_plural` as one NUL-separated blob and their per-plural-form
# translations as another — parsed by finding the NUL byte at the raw byte
# level *before* decoding to `str`, sidestepping any need to search for an
# embedded NUL character inside a Promethium string (untested, avoided on
# purpose) — split first, decode each piece separately.
#
# `ngettext`'s plural-form selection is a real, documented scope cut: CPython
# parses an arbitrary C-style boolean expression out of the catalog's
# `Plural-Forms` header (some languages need 3-6 forms with real logic —
# Polish, Arabic, etc.). This only implements the single most common rule
# in practice — `nplurals=2; plural=(n != 1)` (English, German, and most
# Germanic/Romance languages) — singular for `n == 1`, plural otherwise, no
# expression parser. `Translations.load` never even reads the `Plural-Forms`
# header string for this reason; a catalog needing a different rule will
# still parse and look up plural entries correctly, just always select
# between form 0 and form 1 by the `n == 1` rule regardless of what that
# catalog's own header actually specifies.
#
# `gettext(msgid)` falls back to returning `msgid` unchanged when not found
# in the catalog, matching CPython's own `NullTranslations`/`GNUTranslations`
# fallback behavior exactly (never raises for a missing key).
#
# Verified against a real `.mo` file compiled by GNU `msgfmt` from a small
# German catalog (a plain entry, and a `%d apple`/`%d apples` plural entry)
# and cross-checked against live CPython's own `gettext.translation(...)`
# output: `gettext("Hello")` → `"Hallo"`, `gettext("Goodbye")` →
# `"Auf Wiedersehen"`, `ngettext("%d apple", "%d apples", 1)` →
# `"%d Apfel"`, `ngettext("%d apple", "%d apples", 5)` → `"%d Aepfel"` —
# all matching CPython's output on the identical file, byte-for-byte.


def _findNull(data: bytes, start: int, length: int) -> int:
    i: int = start
    end: int = start + length
    while i < end:
        if data[i] == 0:
            return i
        i += 1
    return -1


def _decodeRange(data: bytes, start: int, length: int) -> str:
    return codecs.decode(marshal._extractBytes(data, start, length))


class Translations:
    _msgKeys: List[str]
    _isPlural: List[bool]
    _forms0: List[str]
    _forms1: List[str]

    def __init__(self):
        self._msgKeys = List[str]()
        self._isPlural = List[bool]()
        self._forms0 = List[str]()
        self._forms1 = List[str]()

    def _find(self, key: str) -> int:
        i: int = 0
        while i < len(self._msgKeys):
            if self._msgKeys.__getitem__(i) == key:
                return i
            i += 1
        return -1

    def gettext(self, msgid: str) -> str:
        idx: int = self._find(msgid)
        if idx < 0:
            return msgid
        return self._forms0.__getitem__(idx)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        idx: int = self._find(singular)
        if idx < 0 or not self._isPlural.__getitem__(idx):
            if n == 1:
                return singular
            else:
                return plural
        if n == 1:
            return self._forms0.__getitem__(idx)
        else:
            return self._forms1.__getitem__(idx)


def load(data: bytes) -> Translations:
    result: Translations = Translations()

    magic: int = struct.unpack_uint32_le(marshal._extractBytes(data, 0, 4))
    # -1794895138 is 0x950412DE's signed-32-bit bit pattern (the real GNU
    # .mo magic number's top bit is set, and Promethium's int is signed
    # 32-bit — struct.unpack_uint32_le already returns the same negative
    # value for this magic, so the literal here has to match that, not
    # the unsigned hex value, the same representational point
    # struct.py's own header comment makes about uint32 round-tripping).
    if magic != -1794895138:
        raise ValueError("gettext.load: not a little-endian .mo file (unsupported magic number)")

    count: int = struct.unpack_uint32_le(marshal._extractBytes(data, 8, 4))
    origTableOffset: int = struct.unpack_uint32_le(marshal._extractBytes(data, 12, 4))
    transTableOffset: int = struct.unpack_uint32_le(marshal._extractBytes(data, 16, 4))

    i: int = 0
    while i < count:
        origEntryPos: int = origTableOffset + i * 8
        origLen: int = struct.unpack_uint32_le(marshal._extractBytes(data, origEntryPos, 4))
        origOff: int = struct.unpack_uint32_le(marshal._extractBytes(data, origEntryPos + 4, 4))

        transEntryPos: int = transTableOffset + i * 8
        transLen: int = struct.unpack_uint32_le(marshal._extractBytes(data, transEntryPos, 4))
        transOff: int = struct.unpack_uint32_le(marshal._extractBytes(data, transEntryPos + 4, 4))

        nullPos: int = _findNull(data, origOff, origLen)
        if nullPos < 0:
            key: str = _decodeRange(data, origOff, origLen)
            if key != "":
                result._msgKeys.append(key)
                result._isPlural.append(False)
                form0: str = _decodeRange(data, transOff, transLen)
                result._forms0.append(form0)
                result._forms1.append("")
        else:
            singularLen: int = nullPos - origOff
            key: str = _decodeRange(data, origOff, singularLen)
            result._msgKeys.append(key)
            result._isPlural.append(True)

            transNullPos: int = _findNull(data, transOff, transLen)
            if transNullPos < 0:
                form0: str = _decodeRange(data, transOff, transLen)
                result._forms0.append(form0)
                result._forms1.append(form0)
            else:
                form0Len: int = transNullPos - transOff
                form0: str = _decodeRange(data, transOff, form0Len)
                form1Start: int = transNullPos + 1
                form1Len: int = (transOff + transLen) - form1Start
                form1: str = _decodeRange(data, form1Start, form1Len)
                result._forms0.append(form0)
                result._forms1.append(form1)

        i += 1

    return result
