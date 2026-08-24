@namespace("shlex")

from Promethium import List

# A small, opt-in subset of Python's shlex module: just `split(s)`,
# CPython's POSIX-mode tokenizer — splits on whitespace, honors single and
# double quotes (contents kept literally inside `'...'`, backslash-escapes
# for `"` and `\` honored inside `"..."`), and a bare backslash outside
# any quotes escapes the next character. `shlex.shlex` (the full stateful
# lexer class, with comment handling, punctuation tokens, `wordchars`
# customization, etc.) isn't attempted — just the common `split()` case.
#
# Built on the same manual-character-scan technique as `csv.py`/
# `configparser.py` (no `.Split`, no regex).


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


def split(value: str) -> List[str]:
    result: List[str] = List[str]()
    length: int = _length(value)
    index: int = 0
    current: str = ""
    inToken: bool = False
    inSingle: bool = False
    inDouble: bool = False
    while index < length:
        ch: str = _charAt(value, index)
        if inSingle:
            if ch == "'":
                inSingle = False
            else:
                current += ch
        elif inDouble:
            if ch == "\"":
                inDouble = False
            elif ch == "\\" and index + 1 < length and (_charAt(value, index + 1) == "\"" or _charAt(value, index + 1) == "\\"):
                current += _charAt(value, index + 1)
                index += 1
            else:
                current += ch
        else:
            if ch == "'":
                inSingle = True
                inToken = True
            elif ch == "\"":
                inDouble = True
                inToken = True
            elif ch == "\\" and index + 1 < length:
                current += _charAt(value, index + 1)
                index += 1
                inToken = True
            elif ch == " " or ch == "\t" or ch == "\n":
                if inToken:
                    result.append(current)
                    current = ""
                    inToken = False
            else:
                current += ch
                inToken = True
        index += 1
    if inToken:
        result.append(current)
    return result
