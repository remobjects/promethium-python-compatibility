@namespace("json")

from Promethium import List, ValueError
from collections import OrderedDict

# A small, opt-in subset of Python's json module: `loads`/`dumps` over a
# `JsonValueNode` tagged-union tree, instead of CPython's approach of mapping
# JSON directly onto native `dict`/`list`/`str`/`int`/`float`/`bool`/`None`.
# Promethium has no way to hold "any Python object" in a single statically-
# typed variable outside `typing.Any`/`dynamic` (see the stdlib survey's
# now-corrected "no reflection/dynamic typing" finding) — but JSON's own
# value space is closed (six kinds, always the same six), so a plain
# tagged-union class sidesteps needing `dynamic` at all here. `JsonValueNode`
# has one field per possible kind and a `_kind` discriminator; `is_null()`/
# `is_bool()`/`is_int()`/`is_float()`/`is_string()`/`is_array()`/
# `is_object()` and matching `as_*()` accessors are the public surface.
#
# CPython's json module folds JSON numbers into a single `int` or `float`
# depending on whether the source text had a `.`/exponent — this keeps
# that same distinction (`is_int()` vs `is_float()`) rather than losing it
# by storing every number as `float`, so `dumps(loads("3"))` round-trips
# as `"3"`, not `"3.0"`.
#
# Recursive-descent parser over `_length`/`_substring` (the same per-
# target-branched idiom `configparser.py`/`csv.py` use), not regex — a
# closed, well-known grammar with no benefit from `re`'s general engine.
# Malformed input raises `Promethium.ValueError`, matching this project's
# established convention (`fractions.py`, `math.py`, `graphlib.py`) rather
# than a custom `JSONDecodeError` type.
#
# Not supported (documented gaps, not silent wrongness): `\uXXXX` escape
# sequences in string literals raise `ValueError` rather than being
# decoded — no confirmed portable way to turn a parsed code point back
# into a character was tried across all four targets, so this was left
# out rather than guessed at. `dumps` never escapes non-ASCII characters
# (CPython's `ensure_ascii=True` default) — output is UTF-8 text with
# non-ASCII passed through unchanged, ASCII-only output was not attempted.
#
# Two things found while getting this to compile/verify, worth knowing
# for any future module:
# - `JsonValue` (the obvious name) and `JsonNode` (the next guess) both
#   collided on Cocoa with something already in the referenced `Elements`
#   assembly — same class of "duplicate short name" issue as `Random`/
#   `Decimal`/`XmlElement` elsewhere in this project. `JsonValueNode`
#   (compound enough to be unique) was the one that stuck.
# - Python's own `float(x)`/`int(x)` builtin conversions are not callable
#   from Promethium at all — neither for numeric widening (`float(someInt)`
#   fails "Unknown identifier 'float'") nor for string parsing
#   (`float("1.5")` fails differently per target, sometimes resolving to
#   an unrelated native RTL function with an incompatible signature).
#   String→number parsing uses real per-target native calls instead
#   (`Double.Parse`/`Int32.Parse` on Echoes/Island, `Double.parseDouble`/
#   `Integer.parseInt` on Cooper, `.doubleValue`/`.intValue` on Toffee);
#   int→float widening uses `someInt + 0.0` instead of a cast, since
#   ordinary arithmetic promotion works where an explicit cast call does
#   not.
#
# Also found at runtime, not just compile time: native float→string
# formatting drops the decimal point for a whole-number float (`3.0`
# stringifies as `"3"`, not `"3.0"`) — `_dumpFloat` appends `.0` when the
# native-formatted text has no `.`/`e`/`E` in it, so `dumps(loads("3.0"))`
# round-trips correctly instead of silently becoming indistinguishable
# from an int.


def _isWhitespace(ch: str) -> bool:
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r"


class JsonValueNode:
    _kind: int
    _boolValue: bool
    _intValue: int
    _floatValue: float
    _stringValue: str
    _arrayValue: List[JsonValueNode]
    _objectValue: OrderedDict[str, JsonValueNode]

    def __init__(self):
        self._kind = 0
        self._boolValue = False
        self._intValue = 0
        self._floatValue = 0.0
        self._stringValue = ""
        self._arrayValue = List[JsonValueNode]()
        self._objectValue = OrderedDict[str, JsonValueNode]()

    def is_null(self) -> bool:
        return self._kind == 0

    def is_bool(self) -> bool:
        return self._kind == 1

    def is_int(self) -> bool:
        return self._kind == 2

    def is_float(self) -> bool:
        return self._kind == 3

    def is_string(self) -> bool:
        return self._kind == 4

    def is_array(self) -> bool:
        return self._kind == 5

    def is_object(self) -> bool:
        return self._kind == 6

    def as_bool(self) -> bool:
        return self._boolValue

    def as_int(self) -> int:
        return self._intValue

    def as_float(self) -> float:
        if self._kind == 2:
            return self._intValue + 0.0
        return self._floatValue

    def as_string(self) -> str:
        return self._stringValue

    def as_array(self) -> List[JsonValueNode]:
        return self._arrayValue

    def as_object(self) -> OrderedDict[str, JsonValueNode]:
        return self._objectValue


def json_null() -> JsonValueNode:
    return JsonValueNode()


def json_bool(value: bool) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 1
    v._boolValue = value
    return v


def json_int(value: int) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 2
    v._intValue = value
    return v


def json_float(value: float) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 3
    v._floatValue = value
    return v


def json_string(value: str) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 4
    v._stringValue = value
    return v


def json_array(value: List[JsonValueNode]) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 5
    v._arrayValue = value
    return v


def json_object(value: OrderedDict[str, JsonValueNode]) -> JsonValueNode:
    v: JsonValueNode = JsonValueNode()
    v._kind = 6
    v._objectValue = value
    return v


def _skipWhitespace(text: str, index: int, length: int) -> int:
    i: int = index
    while i < length and _isWhitespace(_strutil.substring(text, i, 1)):
        i += 1
    return i


def _expectLiteral(text: str, index: int, length: int, literal: str):
    literalLength: int = _strutil.length(literal)
    if index + literalLength > length or _strutil.substring(text, index, literalLength) != literal:
        raise ValueError("json.loads: invalid literal")


def _parseString(text: str, index: int, length: int) -> tuple[str, int]:
    i: int = index + 1
    result: str = ""
    while True:
        if i >= length:
            raise ValueError("json.loads: unterminated string")
        ch: str = _strutil.substring(text, i, 1)
        if ch == "\"":
            return (result, i + 1)
        elif ch == "\\":
            if i + 1 >= length:
                raise ValueError("json.loads: unterminated escape")
            escapeChar: str = _strutil.substring(text, i + 1, 1)
            if escapeChar == "\"":
                result = result + "\""
            elif escapeChar == "\\":
                result = result + "\\"
            elif escapeChar == "/":
                result = result + "/"
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
            elif escapeChar == "u":
                raise ValueError("json.loads: \\u escape sequences are not supported")
            else:
                raise ValueError("json.loads: invalid escape character")
            i += 2
        else:
            result = result + ch
            i += 1


def _parseNumber(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    start: int = index
    i: int = index
    if i < length and _strutil.substring(text, i, 1) == "-":
        i += 1
    while i < length and _strutil.isDigit(_strutil.substring(text, i, 1)):
        i += 1
    isFloat: bool = False
    if i < length and _strutil.substring(text, i, 1) == ".":
        isFloat = True
        i += 1
        while i < length and _strutil.isDigit(_strutil.substring(text, i, 1)):
            i += 1
    if i < length and (_strutil.substring(text, i, 1) == "e" or _strutil.substring(text, i, 1) == "E"):
        isFloat = True
        i += 1
        if i < length and (_strutil.substring(text, i, 1) == "+" or _strutil.substring(text, i, 1) == "-"):
            i += 1
        while i < length and _strutil.isDigit(_strutil.substring(text, i, 1)):
            i += 1
    numberText: str = _strutil.substring(text, start, i - start)
    if isFloat:
        return (json_float(_strutil.parseFloatText(numberText)), i)
    else:
        return (json_int(_strutil.parseIntText(numberText)), i)


def _parseArray(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    items: List[JsonValueNode] = List[JsonValueNode]()
    i: int = _skipWhitespace(text, index + 1, length)
    if i < length and _strutil.substring(text, i, 1) == "]":
        return (json_array(items), i + 1)
    while True:
        itemResult: tuple[JsonValueNode, int] = _parseValue(text, i, length)
        items.append(itemResult[0])
        i = _skipWhitespace(text, itemResult[1], length)
        if i >= length:
            raise ValueError("json.loads: unterminated array")
        ch: str = _strutil.substring(text, i, 1)
        if ch == ",":
            i = _skipWhitespace(text, i + 1, length)
        elif ch == "]":
            return (json_array(items), i + 1)
        else:
            raise ValueError("json.loads: expected ',' or ']' in array")


def _parseObject(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    entries: OrderedDict[str, JsonValueNode] = OrderedDict[str, JsonValueNode]()
    i: int = _skipWhitespace(text, index + 1, length)
    if i < length and _strutil.substring(text, i, 1) == "}":
        return (json_object(entries), i + 1)
    while True:
        i = _skipWhitespace(text, i, length)
        if i >= length or _strutil.substring(text, i, 1) != "\"":
            raise ValueError("json.loads: expected string key in object")
        keyResult: tuple[str, int] = _parseString(text, i, length)
        i = _skipWhitespace(text, keyResult[1], length)
        if i >= length or _strutil.substring(text, i, 1) != ":":
            raise ValueError("json.loads: expected ':' after object key")
        i = _skipWhitespace(text, i + 1, length)
        valueResult: tuple[JsonValueNode, int] = _parseValue(text, i, length)
        entries[keyResult[0]] = valueResult[0]
        i = _skipWhitespace(text, valueResult[1], length)
        if i >= length:
            raise ValueError("json.loads: unterminated object")
        ch: str = _strutil.substring(text, i, 1)
        if ch == ",":
            i = _skipWhitespace(text, i + 1, length)
        elif ch == "}":
            return (json_object(entries), i + 1)
        else:
            raise ValueError("json.loads: expected ',' or '}' in object")


def _parseValue(text: str, index: int, length: int) -> tuple[JsonValueNode, int]:
    i: int = _skipWhitespace(text, index, length)
    if i >= length:
        raise ValueError("json.loads: unexpected end of input")
    ch: str = _strutil.substring(text, i, 1)
    if ch == "{":
        return _parseObject(text, i, length)
    elif ch == "[":
        return _parseArray(text, i, length)
    elif ch == "\"":
        stringResult: tuple[str, int] = _parseString(text, i, length)
        return (json_string(stringResult[0]), stringResult[1])
    elif ch == "t":
        _expectLiteral(text, i, length, "true")
        return (json_bool(True), i + 4)
    elif ch == "f":
        _expectLiteral(text, i, length, "false")
        return (json_bool(False), i + 5)
    elif ch == "n":
        _expectLiteral(text, i, length, "null")
        return (json_null(), i + 4)
    elif ch == "-" or _strutil.isDigit(ch):
        return _parseNumber(text, i, length)
    else:
        raise ValueError("json.loads: unexpected character")


def loads(text: str) -> JsonValueNode:
    length: int = _strutil.length(text)
    result: tuple[JsonValueNode, int] = _parseValue(text, 0, length)
    trailing: int = _skipWhitespace(text, result[1], length)
    if trailing != length:
        raise ValueError("json.loads: unexpected trailing content")
    return result[0]


def _dumpFloat(value: float) -> str:
    text: str = "" + value
    length: int = _strutil.length(text)
    i: int = 0
    hasDecimalMarker: bool = False
    while i < length:
        ch: str = _strutil.substring(text, i, 1)
        if ch == "." or ch == "e" or ch == "E":
            hasDecimalMarker = True
        i += 1
    if hasDecimalMarker:
        return text
    return text + ".0"


def _dumpString(value: str) -> str:
    result: str = "\""
    length: int = _strutil.length(value)
    i: int = 0
    while i < length:
        ch: str = _strutil.substring(value, i, 1)
        if ch == "\"":
            result = result + "\\\""
        elif ch == "\\":
            result = result + "\\\\"
        elif ch == "\n":
            result = result + "\\n"
        elif ch == "\r":
            result = result + "\\r"
        elif ch == "\t":
            result = result + "\\t"
        else:
            result = result + ch
        i += 1
    return result + "\""


def _dumpArray(items: List[JsonValueNode]) -> str:
    result: str = "["
    i: int = 0
    while i < len(items):
        if i > 0:
            result = result + ","
        result = result + dumps(items.__getitem__(i))
        i += 1
    return result + "]"


def _dumpObject(entries: OrderedDict[str, JsonValueNode]) -> str:
    result: str = "{"
    pairs: List[tuple[str, JsonValueNode]] = entries.items()
    i: int = 0
    while i < len(pairs):
        if i > 0:
            result = result + ","
        pair: tuple[str, JsonValueNode] = pairs.__getitem__(i)
        result = result + _dumpString(pair[0]) + ":" + dumps(pair[1])
        i += 1
    return result + "}"


def dumps(value: JsonValueNode) -> str:
    if value.is_null():
        return "null"
    elif value.is_bool():
        if value.as_bool():
            return "true"
        else:
            return "false"
    elif value.is_int():
        return "" + value.as_int()
    elif value.is_float():
        return _dumpFloat(value.as_float())
    elif value.is_string():
        return _dumpString(value.as_string())
    elif value.is_array():
        return _dumpArray(value.as_array())
    else:
        return _dumpObject(value.as_object())
