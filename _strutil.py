@namespace("_strutil")

# Shared native-string primitives used across many modules (configparser,
# csv, difflib, fnmatch, json, re, string, textwrap, tomllib, binascii, and
# others) — previously each module defined its own byte-identical private
# copy of these. Consolidated here for two reasons: the duplication itself,
# and because Toffee compiles top-level module functions to flat,
# non-namespaced global symbols (see
# elements-bug-toffee-cross-module-function-name-collision.md) — nine
# separate modules each defining their own `_length` produced a genuine
# `lld: duplicate symbol: _length` linker error the moment more than one
# ended up in the same Toffee link, which is effectively always once any
# real program references this library.


def length(value: str) -> int:
    if defined("COOPER") or defined("TOFFEE"):
        return value.length()
    else:
        return value.Length


def substring(value: str, start: int, count: int) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Substring(start, count)
    elif defined("COOPER"):
        return value.substring(start, start + count)
    else:
        return value.substringWithRange(NSMakeRange(start, count))


def charAt(value: str, index: int) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Substring(index, 1)
    elif defined("COOPER"):
        return value.substring(index, index + 1)
    else:
        return value.substringWithRange(NSMakeRange(index, 1))


def isDigit(ch: str) -> bool:
    return (
        ch == "0" or ch == "1" or ch == "2" or ch == "3" or ch == "4"
        or ch == "5" or ch == "6" or ch == "7" or ch == "8" or ch == "9"
    )


def lower(value: str) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.ToLower()
    elif defined("COOPER"):
        return value.toLowerCase()
    else:
        return value.lowercaseString


def parseIntText(value: str) -> int:
    if defined("ECHOES") or defined("ISLAND"):
        return Int32.Parse(value)
    elif defined("COOPER"):
        return Integer.parseInt(value)
    else:
        return value.intValue


def parseFloatText(value: str) -> float:
    if defined("ECHOES") or defined("ISLAND"):
        return Double.Parse(value)
    elif defined("COOPER"):
        return Double.parseDouble(value)
    else:
        return value.doubleValue
