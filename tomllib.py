@namespace("tomllib")

from Promethium import List, ValueError
from collections import OrderedDict
from json import JsonValueNode

# A small, opt-in subset of Python 3.11+'s `tomllib` module: `loads(text)
# -> JsonValueNode` (always an object at the root), reusing `json.py`'s
# tagged-union value tree instead of inventing a second one — TOML and
# JSON describe the same value universe (null doesn't exist in TOML
# itself, but the other five kinds do), so there is no reason for a
# second `TomlValueNode` type to exist.
#
# Supported: comments (`# ...` to end of line), bare and basic-quoted
# (`"..."`) table/key names, dotted paths in both table headers
# (`[a.b.c]`) and key/value assignments (`a.b.c = 1`), `[table]` headers,
# `[[array.of.tables]]` headers, inline tables (`{a = 1, b = 2}`), arrays
# (including ones spanning multiple lines, with trailing commas and
# comments), basic strings with the same escapes `json.py` supports,
# literal strings (`'...'`, no escape processing), integers and floats
# (including `_` digit separators, e.g. `1_000_000`), and booleans.
#
# Not supported, documented rather than silently wrong: multi-line
# strings (`"""..."""`/`'''...'''`), dates/times (TOML has native
# date/time literals with no equivalent in this project's closed value
# set), hex/octal/binary integer literals (`0x..`/`0o..`/`0b..`), and
# `inf`/`nan` float literals. Any of these in the source raises
# `ValueError` rather than being silently misparsed.


def _isBareKeyChar(ch: str) -> bool:
    if _strutil.isDigit(ch):
        return True
    if ch == "_" or ch == "-":
        return True
    isUpper: bool = ch >= "A" and ch <= "Z"
    isLower: bool = ch >= "a" and ch <= "z"
    return isUpper or isLower


def _isInlineWhitespace(ch: str) -> bool:
    return ch == " " or ch == "\t"


def _isNewline(ch: str) -> bool:
    return ch == "\n" or ch == "\r"


def _skipInlineWhitespace(text: str, index: int, length: int) -> int:
    i: int = index
    while i < length and _isInlineWhitespace(_strutil.substring(text, i, 1)):
        i += 1
    return i


# Skips whitespace, newlines, and `#` comments — used between top-level
# statements and inside arrays, where TOML allows line breaks freely.
def _skipLayout(text: str, index: int, length: int) -> int:
    i: int = index
    while i < length:
        ch: str = _strutil.substring(text, i, 1)
        if _isInlineWhitespace(ch) or _isNewline(ch):
            i += 1
        elif ch == "#":
            while i < length and not _isNewline(_strutil.substring(text, i, 1)):
                i += 1
        else:
            break
    return i


def _expectChar(text: str, index: int, length: int, expected: str) -> int:
    if index >= length or _strutil.substring(text, index, 1) != expected:
        raise ValueError("tomllib.loads: expected '" + expected + "'")
    return index + 1


def _parseBasicString(text: str, index: int, length: int) -> tuple[str, int]:
    i: int = index + 1
    if i + 1 < length and _strutil.substring(text, i, 2) == "\"\"":
        raise ValueError("tomllib.loads: multi-line strings are not supported")
    result: str = ""
    while True:
        if i >= length:
            raise ValueError("tomllib.loads: unterminated string")
        ch: str = _strutil.substring(text, i, 1)
        if ch == "\"":
            return (result, i + 1)
        elif ch == "\\":
            if i + 1 >= length:
                raise ValueError("tomllib.loads: unterminated escape")
            escapeChar: str = _strutil.substring(text, i + 1, 1)
            if escapeChar == "\"":
                result = result + "\""
            elif escapeChar == "\\":
                result = result + "\\"
            elif escapeChar == "b":
                result = result + "\b"
            elif escapeChar == "f":
                result = result + "\f"
            elif escapeChar == "n":
                result = result + "\n"
            elif escapeChar == "r":
                result = result + "\r"
            elif escapeChar == "t":
                result = result + "\t"
            else:
                raise ValueError("tomllib.loads: invalid escape character")
            i += 2
        elif _isNewline(ch):
            raise ValueError("tomllib.loads: unterminated string")
        else:
            result = result + ch
            i += 1


def _parseLiteralString(text: str, index: int, length: int) -> tuple[str, int]:
    i: int = index + 1
    if i + 1 < length and _strutil.substring(text, i, 2) == "''":
        raise ValueError("tomllib.loads: multi-line strings are not supported")
    result: str = ""
    while True:
        if i >= length:
            raise ValueError("tomllib.loads: unterminated string")
        ch: str = _strutil.substring(text, i, 1)
        if ch == "'":
            return (result, i + 1)
        elif _isNewline(ch):
            raise ValueError("tomllib.loads: unterminated string")
        else:
            result = result + ch
            i += 1


def _parseBareOrQuotedKey(text: str, index: int, length: int) -> tuple[str, int]:
    if index >= length:
        raise ValueError("tomllib.loads: expected a key")
    ch: str = _strutil.substring(text, index, 1)
    if ch == "\"":
        return _parseBasicString(text, index, length)
    elif ch == "'":
        return _parseLiteralString(text, index, length)
    elif _isBareKeyChar(ch):
        start: int = index
        i: int = index
        while i < length and _isBareKeyChar(_strutil.substring(text, i, 1)):
            i += 1
        return (_strutil.substring(text, start, i - start), i)
    else:
        raise ValueError("tomllib.loads: invalid key")


def _parseKeyPath(text: str, index: int, length: int) -> tuple[List[str], int]:
    path: List[str] = List[str]()
    i: int = _skipInlineWhitespace(text, index, length)
    firstResult: tuple[str, int] = _parseBareOrQuotedKey(text, i, length)
    path.append(firstResult[0])
    i = _skipInlineWhitespace(text, firstResult[1], length)
    while i < length and _strutil.substring(text, i, 1) == ".":
        i = _skipInlineWhitespace(text, i + 1, length)
        segmentResult: tuple[str, int] = _parseBareOrQuotedKey(text, i, length)
        path.append(segmentResult[0])
        i = _skipInlineWhitespace(text, segmentResult[1], length)
    return (path, i)


def _removeUnderscores(text: str) -> str:
    result: str = ""
    length: int = _strutil.length(text)
    i: int = 0
    while i < length:
        ch: str = _strutil.substring(text, i, 1)
        if ch != "_":
            result = result + ch
        i += 1
    return result


def _parseNumberOrDate(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    start: int = index
    i: int = index
    if i < length and (_strutil.substring(text, i, 1) == "-" or _strutil.substring(text, i, 1) == "+"):
        i += 1
    while i < length and (_strutil.isDigit(_strutil.substring(text, i, 1)) or _strutil.substring(text, i, 1) == "_"):
        i += 1
    isFloat: bool = False
    if i < length and _strutil.substring(text, i, 1) == ".":
        isFloat = True
        i += 1
        while i < length and (_strutil.isDigit(_strutil.substring(text, i, 1)) or _strutil.substring(text, i, 1) == "_"):
            i += 1
    if i < length and (_strutil.substring(text, i, 1) == "e" or _strutil.substring(text, i, 1) == "E"):
        isFloat = True
        i += 1
        if i < length and (_strutil.substring(text, i, 1) == "+" or _strutil.substring(text, i, 1) == "-"):
            i += 1
        while i < length and _strutil.isDigit(_strutil.substring(text, i, 1)):
            i += 1
    numberText: str = _removeUnderscores(_strutil.substring(text, start, i - start))
    if isFloat:
        return (json.json_float(_strutil.parseFloatText(numberText)), i)
    else:
        return (json.json_int(_strutil.parseIntText(numberText)), i)


def _parseValue(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    i: int = _skipInlineWhitespace(text, index, length)
    if i >= length:
        raise ValueError("tomllib.loads: unexpected end of input")
    ch: str = _strutil.substring(text, i, 1)
    if ch == "\"":
        stringResult: tuple[str, int] = _parseBasicString(text, i, length)
        return (json.json_string(stringResult[0]), stringResult[1])
    elif ch == "'":
        stringResult2: tuple[str, int] = _parseLiteralString(text, i, length)
        return (json.json_string(stringResult2[0]), stringResult2[1])
    elif ch == "[":
        return _parseArray(text, i, length)
    elif ch == "{":
        return _parseInlineTable(text, i, length)
    elif i + 3 < length and _strutil.substring(text, i, 4) == "true":
        return (json.json_bool(True), i + 4)
    elif i + 4 < length and _strutil.substring(text, i, 5) == "false":
        return (json.json_bool(False), i + 5)
    elif ch == "-" or ch == "+" or _strutil.isDigit(ch):
        return _parseNumberOrDate(text, i, length)
    else:
        raise ValueError("tomllib.loads: unexpected value")


def _parseArray(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    items: List[JsonValueNode] = List[JsonValueNode]()
    i: int = _skipLayout(text, index + 1, length)
    if i < length and _strutil.substring(text, i, 1) == "]":
        return (json.json_array(items), i + 1)
    while True:
        itemResult: tuple[JsonValueNode, int] = _parseValue(text, i, length)
        items.append(itemResult[0])
        i = _skipLayout(text, itemResult[1], length)
        if i >= length:
            raise ValueError("tomllib.loads: unterminated array")
        ch: str = _strutil.substring(text, i, 1)
        if ch == ",":
            i = _skipLayout(text, i + 1, length)
            if i < length and _strutil.substring(text, i, 1) == "]":
                return (json.json_array(items), i + 1)
        elif ch == "]":
            return (json.json_array(items), i + 1)
        else:
            raise ValueError("tomllib.loads: expected ',' or ']' in array")


def _parseInlineTable(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    entries: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
    i: int = _skipInlineWhitespace(text, index + 1, length)
    if i < length and _strutil.substring(text, i, 1) == "}":
        return (json.json_object(entries), i + 1)
    while True:
        keyPathResult: tuple[List[str], int] = _parseKeyPath(text, i, length)
        i = _expectChar(text, keyPathResult[1], length, "=")
        valueResult: tuple[JsonValueNode, int] = _parseValue(text, i, length)
        _setNestedKey(entries, keyPathResult[0], valueResult[0])
        i = _skipInlineWhitespace(text, valueResult[1], length)
        if i >= length:
            raise ValueError("tomllib.loads: unterminated inline table")
        ch: str = _strutil.substring(text, i, 1)
        if ch == ",":
            i = _skipInlineWhitespace(text, i + 1, length)
        elif ch == "}":
            return (json.json_object(entries), i + 1)
        else:
            raise ValueError("tomllib.loads: expected ',' or '}' in inline table")


def _setNestedKey(table: OrderedDict[str, JsonValueNode], path: List[str], value: JsonValueNode):
    current: OrderedDict[str, JsonValueNode] = table
    i: int = 0
    while i < len(path) - 1:
        segment: str = path[i]
        if segment in current:
            existing: JsonValueNode = current[segment]
            if not existing.is_object():
                raise ValueError("tomllib.loads: key '" + segment + "' is not a table")
            current = existing.as_object()
        else:
            newTable: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
            current[segment] = json.json_object(newTable)
            current = newTable
        i += 1
    lastSegment: str = path[len(path) - 1]
    if lastSegment in current:
        raise ValueError("tomllib.loads: duplicate key '" + lastSegment + "'")
    current[lastSegment] = value


def _navigateCreateTable(root: OrderedDict[str, JsonValueNode], path: List[str], isArrayTable: bool) -> OrderedDict[str, JsonValueNode]:
    current: OrderedDict[str, JsonValueNode] = root
    i: int = 0
    while i < len(path) - 1:
        segment: str = path[i]
        if segment in current:
            existing: JsonValueNode = current[segment]
            if existing.is_object():
                current = existing.as_object()
            elif existing.is_array():
                items: List[JsonValueNode] = existing.as_array()
                current = items[len(items) - 1].as_object()
            else:
                raise ValueError("tomllib.loads: key '" + segment + "' is not a table")
        else:
            newTable: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
            current[segment] = json.json_object(newTable)
            current = newTable
        i += 1
    lastSegment: str = path[len(path) - 1]
    if isArrayTable:
        newEntry: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
        if lastSegment in current:
            existing2: JsonValueNode = current[lastSegment]
            if not existing2.is_array():
                raise ValueError("tomllib.loads: key '" + lastSegment + "' is not an array of tables")
            existing2.as_array().append(json.json_object(newEntry))
        else:
            entries: List[JsonValueNode] = List[JsonValueNode]()
            entries.append(json.json_object(newEntry))
            current[lastSegment] = json.json_array(entries)
        return newEntry
    else:
        if lastSegment in current:
            existing3: JsonValueNode = current[lastSegment]
            if not existing3.is_object():
                raise ValueError("tomllib.loads: key '" + lastSegment + "' is not a table")
            return existing3.as_object()
        else:
            newTable2: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
            current[lastSegment] = json.json_object(newTable2)
            return newTable2


def loads(text: str) -> JsonValueNode:
    length: int = _strutil.length(text)
    root: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
    currentTable: OrderedDict[str, JsonValueNode] = root
    i: int = _skipLayout(text, 0, length)
    while i < length:
        ch: str = _strutil.substring(text, i, 1)
        if ch == "[":
            isArrayTable: bool = False
            j: int = i + 1
            if j < length and _strutil.substring(text, j, 1) == "[":
                isArrayTable = True
                j += 1
            keyPathResult: tuple[List[str], int] = _parseKeyPath(text, j, length)
            j = _expectChar(text, keyPathResult[1], length, "]")
            if isArrayTable:
                j = _expectChar(text, j, length, "]")
            currentTable = _navigateCreateTable(root, keyPathResult[0], isArrayTable)
            i = _skipLayout(text, j, length)
        else:
            keyPathResult2: tuple[List[str], int] = _parseKeyPath(text, i, length)
            j2: int = _expectChar(text, keyPathResult2[1], length, "=")
            valueResult: tuple[JsonValueNode, int] = _parseValue(text, j2, length)
            _setNestedKey(currentTable, keyPathResult2[0], valueResult[0])
            i = _skipLayout(text, valueResult[1], length)
    return json.json_object(root)
