@namespace("re")

from Promethium import List

# Backed by RemObjects.Elements.RTL.Regex, a portable regex engine added to
# RTL2 as a side task in this same effort (see [[rtl2_regex_engine_added]]
# memory). Supports literals, `.`, character classes (`[abc]`, `[^abc]`,
# ranges), anchors `^`/`$`, quantifiers `* + ? {m} {m,} {m,n}` (greedy and
# lazy), alternation `|`, capturing/non-capturing groups `(...)`/`(?:...)`,
# and escapes `\d \D \w \W \s \S \b \B`. NOT supported (by the underlying
# engine, not a Promethium limitation): backreferences, lookahead/
# lookbehind, named groups, Unicode property classes, case-insensitive/
# multiline/dotall flags — there is no `flags` parameter here for that
# reason.
#
# `RemObjects.Elements.RTL.Regex`'s own constructor is a *named* constructor
# (`constructor withPattern(...)`), which Promethium has no calling
# convention for (bare positional, `=`, and `:` keyword-style call syntax
# were all tried and all failed — the `:` form is a hard Promethium syntax
# error, not just a label mismatch). Worked around by adding a plain
# `class method FromPattern(...)` factory to `Regex.pas` in RTL2 itself,
# mirroring `XmlDocument.FromString`.
#
# `Regex.Match`/`IsMatch` always search anywhere in the string (there is no
# "anchor to this start position only" primitive). Python's `match()` and
# `fullmatch()` need stronger anchoring than that, so `Pattern` compiles
# *three* separate engines from the same source pattern: the raw pattern
# for `search`/`findall`/`finditer`/`sub`/`split`, `^(?:pattern)` for
# `match`, and `^(?:pattern)$` for `fullmatch`. The non-capturing wrapper
# keeps capture-group numbering identical across all three.
#
# `Match.start()`/`end()`/`span()` only cover the whole match (group 0):
# `RegexMatch` only exposes an `Index` for the overall match plus each
# group's matched *text* (as `Groups`), not per-group start/end offsets, so
# there is no way to compute a capture group's own position.
#
# `findall` always returns whole-match strings (`List[str]`), never the
# "list of group tuples" shape CPython uses when the pattern has groups —
# a fixed function return type can't switch shape based on the pattern
# passed in. Use `finditer` plus `Match.group(n)` to get at capture groups.
#
# `finditer` returns a `List[Match]` rather than a lazy iterator, matching
# every other module in this project that stands in for a CPython generator
# with an eagerly-built `List` (see `csv`/`difflib`).
#
# `sub`'s replacement string accepts Python-style backreferences (`\1`,
# `\g<12>`) and translates them to the engine's own `$1`/`$12` syntax; a
# literal `$` in the replacement is escaped to `$$` so it survives that
# translation unchanged.
#
# `escape` matches CPython 3.7+'s own special-character set exactly
# (`()[]{}?*+-|^$\.&~#` plus whitespace), not just the subset this engine
# actually treats as special — the point of `escape` is safe embedding of
# arbitrary text into a pattern string, so it follows CPython's contract
# rather than this engine's.


def _isAsciiDigit(ch: str) -> bool:
    return (
        ch == "0" or ch == "1" or ch == "2" or ch == "3" or ch == "4"
        or ch == "5" or ch == "6" or ch == "7" or ch == "8" or ch == "9"
    )


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


def _convertReplacement(repl: str) -> str:
    result: str = ""
    length: int = _length(repl)
    i: int = 0
    while i < length:
        ch: str = _substring(repl, i, 1)
        if ch == "\\" and i + 1 < length:
            nextCh: str = _substring(repl, i + 1, 1)
            if _isAsciiDigit(nextCh):
                j: int = i + 1
                digits: str = ""
                while j < length and _isAsciiDigit(_substring(repl, j, 1)):
                    digits = digits + _substring(repl, j, 1)
                    j += 1
                result = result + "$" + digits
                i = j
            elif nextCh == "g" and i + 2 < length and _substring(repl, i + 2, 1) == "<":
                j: int = i + 3
                digits: str = ""
                while j < length and _substring(repl, j, 1) != ">":
                    digits = digits + _substring(repl, j, 1)
                    j += 1
                result = result + "$" + digits
                i = j + 1
            elif nextCh == "\\":
                result = result + "\\"
                i += 2
            else:
                result = result + nextCh
                i += 2
        elif ch == "$":
            result = result + "$$"
            i += 1
        else:
            result = result + ch
            i += 1
    return result


class Match:
    _value: str
    _index: int
    _groups: List[str]

    def __init__(self, source: RemObjects.Elements.RTL.RegexMatch):
        self._value = source.Value
        self._index = source.Index
        self._groups = List[str]()
        for rawGroup in source.Groups:
            group: str = rawGroup
            self._groups.append(group)

    def group(self, index: int = 0) -> str:
        return self._groups[index]

    def groups(self) -> List[str]:
        result: List[str] = List[str]()
        i: int = 1
        while i < len(self._groups):
            result.append(self._groups[i])
            i += 1
        return result

    def start(self) -> int:
        return self._index

    def end(self) -> int:
        return self._index + _length(self._value)

    def span(self) -> tuple[int, int]:
        return (self.start(), self.end())


class Pattern:
    pattern: str
    _searchEngine: RemObjects.Elements.RTL.Regex
    _matchEngine: RemObjects.Elements.RTL.Regex
    _fullEngine: RemObjects.Elements.RTL.Regex

    def __init__(self, pattern: str):
        self.pattern = pattern
        self._searchEngine = RemObjects.Elements.RTL.Regex.FromPattern(pattern)
        self._matchEngine = RemObjects.Elements.RTL.Regex.FromPattern("^(?:" + pattern + ")")
        self._fullEngine = RemObjects.Elements.RTL.Regex.FromPattern("^(?:" + pattern + ")$")

    def search(self, text: str) -> Match:
        raw: RemObjects.Elements.RTL.RegexMatch = self._searchEngine.Match(text)
        if raw is None:
            return None
        return Match(raw)

    def match(self, text: str) -> Match:
        raw: RemObjects.Elements.RTL.RegexMatch = self._matchEngine.Match(text)
        if raw is None:
            return None
        return Match(raw)

    def fullmatch(self, text: str) -> Match:
        raw: RemObjects.Elements.RTL.RegexMatch = self._fullEngine.Match(text)
        if raw is None:
            return None
        return Match(raw)

    def findall(self, text: str) -> List[str]:
        result: List[str] = List[str]()
        for rawMatch in self._searchEngine.Matches(text):
            m: RemObjects.Elements.RTL.RegexMatch = rawMatch
            result.append(m.Value)
        return result

    def finditer(self, text: str) -> List[Match]:
        result: List[Match] = List[Match]()
        for rawMatch in self._searchEngine.Matches(text):
            m: RemObjects.Elements.RTL.RegexMatch = rawMatch
            result.append(Match(m))
        return result

    def sub(self, repl: str, text: str, count: int = 0) -> str:
        if count == 0:
            return self._searchEngine.Replace(text, _convertReplacement(repl))
        result: str = ""
        remaining: str = text
        done: int = 0
        while done < count:
            raw: RemObjects.Elements.RTL.RegexMatch = self._searchEngine.Match(remaining)
            if raw is None:
                break
            m: RemObjects.Elements.RTL.RegexMatch = raw
            result = result + _substring(remaining, 0, m.Index) + Match(m).group(0)
            matched: str = m.Value
            tailStart: int = m.Index + _length(matched)
            remaining = _substring(remaining, tailStart, _length(remaining) - tailStart)
            done += 1
            if _length(matched) == 0:
                if _length(remaining) > 0:
                    result = result + _substring(remaining, 0, 1)
                    remaining = _substring(remaining, 1, _length(remaining) - 1)
                else:
                    break
        return result + remaining

    def split(self, text: str) -> List[str]:
        result: List[str] = List[str]()
        for rawPart in self._searchEngine.Split(text):
            part: str = rawPart
            result.append(part)
        return result


def compile(pattern: str) -> Pattern:
    return Pattern(pattern)


def match(pattern: str, text: str) -> Match:
    return Pattern(pattern).match(text)


def search(pattern: str, text: str) -> Match:
    return Pattern(pattern).search(text)


def fullmatch(pattern: str, text: str) -> Match:
    return Pattern(pattern).fullmatch(text)


def findall(pattern: str, text: str) -> List[str]:
    return Pattern(pattern).findall(text)


def finditer(pattern: str, text: str) -> List[Match]:
    return Pattern(pattern).finditer(text)


def sub(pattern: str, repl: str, text: str, count: int = 0) -> str:
    return Pattern(pattern).sub(repl, text, count)


def split(pattern: str, text: str) -> List[str]:
    return Pattern(pattern).split(text)


def escape(text: str) -> str:
    result: str = ""
    length: int = _length(text)
    i: int = 0
    while i < length:
        ch: str = _substring(text, i, 1)
        isSpecial: bool = (
            ch == "\\" or ch == "." or ch == "^" or ch == "$" or ch == "*"
            or ch == "+" or ch == "?" or ch == "{" or ch == "}" or ch == "["
            or ch == "]" or ch == "|" or ch == "(" or ch == ")" or ch == "-"
            or ch == "&" or ch == "~" or ch == "#" or ch == " " or ch == "\t"
            or ch == "\n" or ch == "\r" or ch == "\v" or ch == "\f"
        )
        if isSpecial:
            result = result + "\\" + ch
        else:
            result = result + ch
        i += 1
    return result
