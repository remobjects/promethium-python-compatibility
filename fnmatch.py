@namespace("fnmatch")

# A small, opt-in subset of Python's fnmatch module: just the pattern
# matcher itself (`fnmatch(name, pattern)`), not `fnmatch.filter`/`glob`
# (which need filesystem listing — out of scope; see the README's Build
# notes). The predicate itself doesn't touch the filesystem at all, so
# it's in scope the same way `csv`/`configparser` are: pure text
# processing over an already-provided string.
#
# Supports `*` (any run of characters, including none) and `?` (exactly
# one character) via the standard iterative two-pointer/backtrack
# algorithm (no recursion, no regex engine). `[seq]`/`[!seq]` character
# classes are **not** attempted — CPython translates the whole pattern to
# a regex internally to support those; that's a meaningfully bigger step
# than plain `*`/`?` matching and wasn't attempted here.


def fnmatch(name: str, pattern: str) -> bool:
    nameLength: int = _length(name)
    patternLength: int = _length(pattern)
    i: int = 0
    j: int = 0
    starIndex: int = -1
    matchIndex: int = 0
    while i < nameLength:
        if j < patternLength and (_charAt(pattern, j) == "?" or _charAt(pattern, j) == _charAt(name, i)):
            i += 1
            j += 1
        elif j < patternLength and _charAt(pattern, j) == "*":
            starIndex = j
            matchIndex = i
            j += 1
        elif starIndex >= 0:
            j = starIndex + 1
            matchIndex += 1
            i = matchIndex
        else:
            return False
    while j < patternLength and _charAt(pattern, j) == "*":
        j += 1
    return j == patternLength


def _length(value: str) -> int:
    if defined("COOPER") or defined("TOFFEE"):
        return value.length()
    else:
        return value.Length


def _charAt(value: str, index: int) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Substring(index, 1)
    elif defined("COOPER"):
        return value.substring(index, index + 1)
    else:
        return value.substringWithRange(NSMakeRange(index, 1))
