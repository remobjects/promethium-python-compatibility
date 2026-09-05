@namespace("email")

# A very small subset of Python's `email` package: `email.utils.
# parseaddr`/`formataddr` only — plain string parsing over a `"Name
# <addr>"`-shaped address, not the full package (no message parsing,
# no MIME, no header encoding/RFC 2047 encoded-words). `email` sits
# under the survey's "Networking" exclusion as a whole, but this pair
# does no I/O at all, the same correction `mimetypes.py`/`urllib.py`/
# `wave.py` already made to their own over-broad exclusions.
#
# `parseaddr` only recognizes the common `Name <addr>` / bare-`addr`
# shapes — real RFC 2822 address parsing handles comments, multiple
# addresses, and far more syntax than attempted here. A quoted name
# (`"Doe, John" <addr>`) has its surrounding quotes stripped.
# `formataddr` quotes the name (escaping internal `"`/`\`) whenever it
# contains any of the characters CPython's own implementation treats as
# needing quoting (`,`, `"`, `<`, `>`, `@`, `:`, `;`, `(`, `)`, `[`, `]`,
# `.`), otherwise leaves it bare — matching CPython's own output shape
# for the common cases, not its full RFC 2822 `specials` handling.
#
# Reuses `configparser.py`'s already-proven `_trim` (a cross-namespace
# call, same pattern as `gzip` → `zlib`/`wave` → `zipfile`) rather than
# a fourth duplicate whitespace-trim helper.
#
# Runtime-verified against live CPython's own `email.utils.parseaddr`/
# `formataddr`: a plain name/address pair, a bare address with no name,
# and a comma-containing name needing quotes — every result matched
# exactly, both directions.


def _needsQuoting(name: str) -> bool:
    length: int = _strutil.length(name)
    i: int = 0
    while i < length:
        ch: str = _strutil.substring(name, i, 1)
        if ch == "," or ch == "\"" or ch == "<" or ch == ">" or ch == "@" or ch == ":" or ch == ";" or ch == "(" or ch == ")" or ch == "[" or ch == "]" or ch == ".":
            return True
        i += 1
    return False


def _quoteName(name: str) -> str:
    result: str = ""
    length: int = _strutil.length(name)
    i: int = 0
    while i < length:
        ch: str = _strutil.substring(name, i, 1)
        if ch == "\"" or ch == "\\":
            result += "\\"
        result += ch
        i += 1
    return "\"" + result + "\""


def formataddr(nameAndAddr: tuple[str, str]) -> str:
    name: str = nameAndAddr[0]
    addr: str = nameAndAddr[1]
    if name == "":
        return addr
    if _needsQuoting(name):
        return _quoteName(name) + " <" + addr + ">"
    return name + " <" + addr + ">"


def parseaddr(value: str) -> tuple[str, str]:
    length: int = _strutil.length(value)
    ltPos: int = -1
    gtPos: int = -1
    i: int = 0
    while i < length:
        ch: str = _strutil.substring(value, i, 1)
        if ch == "<" and ltPos == -1:
            ltPos = i
        elif ch == ">" and ltPos != -1 and gtPos == -1:
            gtPos = i
        i += 1

    if ltPos == -1 or gtPos == -1:
        return ("", configparser._trim(value))

    namePart: str = configparser._trim(_strutil.substring(value, 0, ltPos))
    addrPart: str = _strutil.substring(value, ltPos + 1, gtPos - ltPos - 1)

    nameLen: int = _strutil.length(namePart)
    if nameLen >= 2 and _strutil.substring(namePart, 0, 1) == "\"" and _strutil.substring(namePart, nameLen - 1, 1) == "\"":
        namePart = _strutil.substring(namePart, 1, nameLen - 2)

    return (namePart, addrPart)
