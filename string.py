@namespace("string")

from Promethium import List

# A small, opt-in subset of Python's string module: just the character-class
# constants, exposed as zero-argument functions rather than Python-style
# module attributes (`string.digits` becomes `digits()`), for two confirmed
# reasons:
#
# - A top-level `name: str = "..."` module-level constant compiles fine on
#   its own, but is unreachable from a consumer both ways: a bare `digits`
#   doesn't resolve via `DefaultUses` the way a bare *function* call does
#   (confirmed: `heapq`/`bisect`/`math`/`operator`/`itertools`'s functions
#   all resolve bare via `DefaultUses` at the consumer level; a `str`-typed
#   top-level constant declared the same way in this same namespace did
#   not), and the fully-qualified form (`string.digits`) fails too — see
#   the next point.
# - The namespace name `string` itself collides with the native `String`
#   type: `string.digits` fails to compile with "Case for identifier
#   'string' does not match original case 'String'" followed by "No static
#   member 'digits' on type 'String'" — the compiler resolves `string`
#   case-insensitively to the platform's own `String` type instead of this
#   module's namespace. Zero-argument functions sidestep this too, since
#   consumers never need to write `string.` at all: add `string` to
#   `DefaultUses` and call `digits()`, `punctuation()`, etc. bare, the same
#   pattern already established for every other module in this project.
#
# `capwords` (below) needed confirming that native string methods are
# callable from Promethium at all — they are: `.ToUpper`/`.ToLower`/`.Trim`/
# `.Substring`/`.Length`/`.Replace`/`.Contains` all compile clean on every
# target via the same `defined("ECHOES"|"ISLAND"|"COOPER")`-branching
# pattern `math.py` uses for native calls (Cooper's spellings are the
# lowercase Java ones; Toffee's are the Foundation/NSString ones). `Split`
# is the one exception found so far: neither a bare string argument nor a
# `Char[]` argument matched a single confirmed overload cleanly on a first
# attempt, so `capwords` deliberately avoids it, splitting words with a
# manual character scan (`_substring`/`_length` only) instead. `Template`
# is still not attempted — it needs far more string-parsing machinery than
# `capwords`' single split-and-capitalize pass.


def _upper(value: str) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.ToUpper()
    elif defined("COOPER"):
        return value.toUpperCase()
    else:
        return value.uppercaseString


def _capitalizeWord(word: str) -> str:
    if _strutil.length(word) == 0:
        return word
    first: str = _upper(_strutil.substring(word, 0, 1))
    rest: str = _strutil.lower(_strutil.substring(word, 1, _strutil.length(word) - 1))
    return first + rest


def capwords(value: str) -> str:
    result: str = ""
    wordStart: int = 0
    length: int = _strutil.length(value)
    index: int = 0
    while index <= length:
        atBoundary: bool = False
        if index == length:
            atBoundary = True
        elif _strutil.substring(value, index, 1) == " ":
            atBoundary = True
        if atBoundary:
            if index > wordStart:
                word: str = _strutil.substring(value, wordStart, index - wordStart)
                if _strutil.length(result) > 0:
                    result += " "
                result += _capitalizeWord(word)
            wordStart = index + 1
        index += 1
    return result


def _isAsciiWhitespace(ch: str) -> bool:
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r" or ch == "\v" or ch == "\f"


def _startsWithAt(value: str, valueLength: int, needle: str, needleLength: int, index: int) -> bool:
    if needleLength == 0 or index + needleLength > valueLength:
        return False
    return _strutil.substring(value, index, needleLength) == needle


# `str.split`, standing in for native `String.Split` — the one native string
# method that turned out to have no single confirmed overload from
# Promethium (bare string argument and `Char[]` argument each matched a
# *different* unwanted overload; see the "String.Split's overload set"
# compiler-gaps entry in the stdlib survey). The compiler team's own call:
# not a Promethium parser gap, just a genuinely confusing overload set not
# worth distorting native resolution for — so this is a plain BaseLibrary-
# level implementation instead, the same manual character-scan idiom
# `capwords` already uses.
#
# `sep: str = None` mirrors Python's own `str.split(sep=None)` signature:
# omitting `sep` (or passing `None`) splits on runs of whitespace and
# discards leading/trailing/empty tokens, matching CPython's `"  a  b  "
# .split()` behavior exactly. Passing a non-empty `sep` splits on that
# literal substring and *keeps* empty tokens between consecutive
# separators (`"a,,b".split(",") == ["a", "", "b"]`), also matching
# CPython. An empty `sep` is a `ValueError` in CPython; this has no
# exception-raising convention established anywhere else in this project,
# so it degrades to returning `[value]` unchanged instead.
def split(value: str, sep: str = None) -> List[str]:
    result: List[str] = List[str]()
    length: int = _strutil.length(value)
    if sep is None:
        tokenStart: int = -1
        index: int = 0
        while index <= length:
            atSeparator: bool = index == length or _isAsciiWhitespace(_strutil.substring(value, index, 1))
            if atSeparator:
                if tokenStart >= 0:
                    result.append(_strutil.substring(value, tokenStart, index - tokenStart))
                    tokenStart = -1
            elif tokenStart < 0:
                tokenStart = index
            index += 1
        return result
    sepLength: int = _strutil.length(sep)
    if sepLength == 0:
        result.append(value)
        return result
    tokenStart: int = 0
    index: int = 0
    while index <= length - sepLength:
        if _startsWithAt(value, length, sep, sepLength, index):
            result.append(_strutil.substring(value, tokenStart, index - tokenStart))
            index += sepLength
            tokenStart = index
        else:
            index += 1
    result.append(_strutil.substring(value, tokenStart, length - tokenStart))
    return result


def ascii_lowercase() -> str:
    return "abcdefghijklmnopqrstuvwxyz"


def ascii_uppercase() -> str:
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def ascii_letters() -> str:
    return ascii_lowercase() + ascii_uppercase()


def digits() -> str:
    return "0123456789"


def hexdigits() -> str:
    return "0123456789abcdefABCDEF"


def octdigits() -> str:
    return "01234567"


def punctuation() -> str:
    return "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"


def whitespace() -> str:
    return " \t\n\r"


def printable() -> str:
    return digits() + ascii_letters() + punctuation() + whitespace()
