@namespace("csv")

from Promethium import List

# A small, opt-in subset of Python's csv module: `parse_line`/`write_row`
# for one row at a time — not a `reader`/`writer` object bound to a file
# handle (this project's own scope statement excludes filesystem APIs;
# see the README's "Build notes"). Handles the common cases: comma-
# separated fields, double-quoted fields (needed when a field itself
# contains a comma), and `""` as an escaped quote inside a quoted field —
# CPython's default `excel` dialect's escaping rule. Does not support a
# custom delimiter/quote character, embedded newlines inside a quoted
# field, or any of the other `Dialect` options.
#
# Built on the same manual-character-scan technique `string.py`'s
# `capwords` and `textwrap.py`'s `_words` already use (no `.Split`, no
# regex — see `string.py`'s notes on why).


def _length(value: str) -> int:
    if defined("COOPER") or defined("TOFFEE"):
        return value.length()
    else:
        return value.Length


def _substring(value: str, start: int, count: int) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Substring(start, count)
    elif defined("COOPER"):
        return value.substring(start, start + count)
    else:
        return value.substringWithRange(NSMakeRange(start, count))


def parse_line(line: str) -> List[str]:
    fields: List[str] = List[str]()
    length: int = _length(line)
    index: int = 0
    field: str = ""
    inQuotes: bool = False
    while index < length:
        ch: str = _substring(line, index, 1)
        if inQuotes:
            if ch == "\"":
                if index + 1 < length and _substring(line, index + 1, 1) == "\"":
                    field += "\""
                    index += 1
                else:
                    inQuotes = False
            else:
                field += ch
        else:
            if ch == "\"":
                inQuotes = True
            elif ch == ",":
                fields.append(field)
                field = ""
            else:
                field += ch
        index += 1
    fields.append(field)
    return fields


def _fieldNeedsQuoting(field: str) -> bool:
    length: int = _length(field)
    index: int = 0
    while index < length:
        ch: str = _substring(field, index, 1)
        if ch == "," or ch == "\"" or ch == "\n" or ch == "\r":
            return True
        index += 1
    return False


def _quoteField(field: str) -> str:
    result: str = ""
    length: int = _length(field)
    index: int = 0
    while index < length:
        ch: str = _substring(field, index, 1)
        if ch == "\"":
            result += "\"\""
        else:
            result += ch
        index += 1
    return "\"" + result + "\""


def write_row(fields: List[str]) -> str:
    result: str = ""
    index: int = 0
    while index < len(fields):
        if index > 0:
            result += ","
        field: str = fields.__getitem__(index)
        if _fieldNeedsQuoting(field):
            result += _quoteField(field)
        else:
            result += field
        index += 1
    return result