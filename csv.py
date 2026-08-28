@namespace("csv")

from Promethium import List
from collections import OrderedDict

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


# `DictReader`/`DictWriter`-equivalent, one row at a time (same row-at-a-
# time scope as `parse_line`/`write_row` above, not a file-bound object).
# Missing trailing fields read as `""` (matching CPython's own `restval`
# default of `None`, adapted to a concrete `str` the way this project
# elsewhere stands in for CPython's `None` defaults); a header key with
# no matching value in the row to write is skipped and written as `""`.


def parse_line_dict(header: List[str], line: str) -> OrderedDict[str, str]:
    values: List[str] = parse_line(line)
    result: OrderedDict[str, str] = OrderedDict[str, str]()
    valueCount: int = values.__len__()
    i: int = 0
    n: int = header.__len__()
    while i < n:
        if i < valueCount:
            result[header[i]] = values[i]
        else:
            result[header[i]] = ""
        i += 1
    return result


def write_row_dict(header: List[str], row: OrderedDict[str, str]) -> str:
    values: List[str] = List[str]()
    i: int = 0
    n: int = header.__len__()
    while i < n:
        key: str = header[i]
        if key in row:
            values.append(row[key])
        else:
            values.append("")
        i += 1
    return write_row(values)