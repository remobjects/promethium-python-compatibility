@namespace("textwrap")

from Promethium import List

# A small, opt-in subset of Python's textwrap module: `wrap`/`fill`, a
# greedy word-wrap over whitespace-delimited words. Built on the same
# per-target-branched native string primitives `string.py`'s `capwords`
# established (`_upper`/`_length`/`_substring` — reimplemented here rather
# than imported, to keep this module's only dependency on `string.py` at
# the source-pattern level, not a hard reference); no `.Split` (its exact
# overload was never resolved — see `string.py`'s notes) and no regex
# (`re` isn't attempted anywhere in this project) — words are found with a
# manual whitespace scan, the same technique `capwords` already uses.
#
# `textwrap.TextWrapper`'s many options (indent, tab expansion, hyphen
# breaking, etc.) aren't attempted — just the common `wrap(text, width)`/
# `fill(text, width)` case, breaking only at existing whitespace (never
# splitting a word longer than `width`, matching CPython's default
# `break_long_words=True` only loosely — a single very long word is placed
# on its own line rather than being sliced, a deliberate simplification).


def _words(text: str) -> List[str]:
    result: List[str] = List[str]()
    length: int = _strutil.length(text)
    wordStart: int = 0
    index: int = 0
    while index <= length:
        atBoundary: bool = False
        if index == length:
            atBoundary = True
        elif _strutil.substring(text, index, 1) == " ":
            atBoundary = True
        if atBoundary:
            if index > wordStart:
                result.append(_strutil.substring(text, wordStart, index - wordStart))
            wordStart = index + 1
        index += 1
    return result


def wrap(text: str, width: int) -> List[str]:
    words: List[str] = _words(text)
    lines: List[str] = List[str]()
    current: str = ""
    index: int = 0
    while index < len(words):
        word: str = words.__getitem__(index)
        if _strutil.length(current) == 0:
            current = word
        elif _strutil.length(current) + 1 + _strutil.length(word) <= width:
            current = current + " " + word
        else:
            lines.append(current)
            current = word
        index += 1
    if _strutil.length(current) > 0:
        lines.append(current)
    return lines


def fill(text: str, width: int) -> str:
    lines: List[str] = wrap(text, width)
    result: str = ""
    index: int = 0
    while index < len(lines):
        if index > 0:
            result += "\n"
        result += lines.__getitem__(index)
        index += 1
    return result
