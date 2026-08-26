@namespace("pprint")

from Promethium import List
from collections import OrderedDict
from json import JsonValueNode

# A small, opt-in subset of Python's pprint module: multi-line indented
# formatting over `json.JsonValueNode` rather than CPython's "any Python
# object" — the same scope decision `json.py` made, for the same reason:
# Promethium has no single statically-typed value that can hold an
# arbitrary object outside `typing.Any`/`dynamic` (now confirmed working,
# see the stdlib survey), but reaching for that here would trade a closed,
# well-understood value space for open-ended per-target reflection with
# no real payoff — `JsonValueNode` is already this project's closest thing
# to "a generic value," and pretty-printing loaded JSON/config data is the
# most common real reason to reach for `pprint` in the first place.
#
# Output is JSON syntax (`null`/`true`/`false`, double-quoted keys and
# strings), not CPython's Python-literal `pprint` syntax (`None`/`True`/
# `False`, single-quoted strings) — this is `json.dumps(value, indent=2)`-
# shaped output, not a `repr()`-shaped one. A deliberate deviation, not an
# oversight: there is no arbitrary Python object here to `repr()` in the
# first place, only `JsonValueNode` trees, so JSON's own syntax is the
# more honest fit than pretending to Python-literal output for data that
# was never a live Python object.
#
# Leaf values (`null`/bool/int/float/string) are formatted by calling
# `json.dumps` on them directly rather than reimplementing that logic —
# only the multi-line indentation for arrays/objects is new here.


def _indent(level: int, width: int) -> str:
    result: str = ""
    total: int = level * width
    i: int = 0
    while i < total:
        result = result + " "
        i += 1
    return result


def _formatArray(items: List[JsonValueNode], width: int, level: int) -> str:
    if len(items) == 0:
        return "[]"
    result: str = "[\n"
    i: int = 0
    while i < len(items):
        result = result + _indent(level + 1, width) + _formatValue(items[i], width, level + 1)
        if i < len(items) - 1:
            result = result + ","
        result = result + "\n"
        i += 1
    return result + _indent(level, width) + "]"


def _formatObject(entries: OrderedDict[str, JsonValueNode], width: int, level: int) -> str:
    pairs: List[tuple[str, JsonValueNode]] = entries.items()
    if len(pairs) == 0:
        return "{}"
    result: str = "{\n"
    i: int = 0
    while i < len(pairs):
        pair: tuple[str, JsonValueNode] = pairs.__getitem__(i)
        result = result + _indent(level + 1, width) + json.dumps(json.json_string(pair[0])) + ": " + _formatValue(pair[1], width, level + 1)
        if i < len(pairs) - 1:
            result = result + ","
        result = result + "\n"
        i += 1
    return result + _indent(level, width) + "}"


def _formatValue(value: JsonValueNode, width: int, level: int) -> str:
    if value.is_array():
        return _formatArray(value.as_array(), width, level)
    elif value.is_object():
        return _formatObject(value.as_object(), width, level)
    else:
        return json.dumps(value)


def pformat(value: JsonValueNode, indent: int = 2) -> str:
    return _formatValue(value, indent, 0)


def pprint(value: JsonValueNode, indent: int = 2):
    print(pformat(value, indent))
