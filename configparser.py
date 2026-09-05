@namespace("configparser")

from Promethium import List
from collections import OrderedDict

# A small, opt-in subset of Python's configparser module: `parse(lines)`
# reads INI-style text (already split into lines — this project excludes
# filesystem APIs, so there's no file handle to read from directly) into
# an `OrderedDict[str, OrderedDict[str, str]]` (section name -> ordered
# key/value map), reusing `collections.OrderedDict` rather than inventing
# another ordered-mapping type. Supports `[section]` headers, `key = value`
# and `key: value` (both separators, like CPython), `#`/`;` comment lines,
# and blank-line skipping. Not attempted: interpolation (`%(x)s`),
# `DEFAULT` section fallback, multi-line values, or writing config back
# out.
#
# Built on the same manual-character-scan primitives `string.py`'s
# `capwords` established, plus a hand-rolled `_indexOfChar` rather than a
# native `.IndexOf` — deliberately, since Toffee's equivalent
# (`rangeOfString(...).location`) returns Cocoa's `NSNotFound` sentinel
# instead of `-1` when the character is missing (the same class of problem
# `operator.py`'s `indexOf` already avoids for `List`), and a manual scan
# sidesteps the question entirely rather than branching around it per
# target.


def _trim(value: str) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Trim()
    elif defined("COOPER"):
        return value.trim()
    else:
        return value.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceCharacterSet)


def _indexOfChar(value: str, ch: str) -> int:
    length: int = _strutil.length(value)
    index: int = 0
    while index < length:
        if _strutil.substring(value, index, 1) == ch:
            return index
        index += 1
    return -1


def parse(lines: List[str]) -> OrderedDict[str, OrderedDict[str, str]]:
    result: OrderedDict[str, OrderedDict[str, str]] = OrderedDict[str, OrderedDict[str, str]]()
    currentSection: str = ""
    currentMap: OrderedDict[str, str] = OrderedDict[str, str]()
    hasSection: bool = False
    lineIndex: int = 0
    while lineIndex < len(lines):
        line: str = _trim(lines.__getitem__(lineIndex))
        lineIndex += 1
        if _strutil.length(line) == 0:
            continue
        first: str = _strutil.substring(line, 0, 1)
        if first == "#" or first == ";":
            continue
        if first == "[":
            if hasSection:
                result[currentSection] = currentMap
            closeIndex: int = _indexOfChar(line, "]")
            if closeIndex > 0:
                currentSection = _strutil.substring(line, 1, closeIndex - 1)
            else:
                currentSection = _strutil.substring(line, 1, _strutil.length(line) - 1)
            currentMap = OrderedDict[str, str]()
            hasSection = True
            continue
        sepIndex: int = _indexOfChar(line, "=")
        if sepIndex < 0:
            sepIndex = _indexOfChar(line, ":")
        if sepIndex < 0:
            continue
        key: str = _trim(_strutil.substring(line, 0, sepIndex))
        value: str = _trim(_strutil.substring(line, sepIndex + 1, _strutil.length(line) - sepIndex - 1))
        currentMap[key] = value
    if hasSection:
        result[currentSection] = currentMap
    return result
