@namespace("difflib")

from Promethium import List

# A small, opt-in subset of Python's difflib module: `ratio(a, b)` and
# `get_close_matches(word, possibilities, n, cutoff)`, built on the real
# Ratcliff-Obershelp matching-blocks algorithm CPython's own
# `SequenceMatcher` uses — not a simpler LCS approximation, which would
# give a *different* number for many input pairs and break this project's
# standing bar of runtime-verifying against CPython's own output. The one
# simplification: CPython's `SequenceMatcher` has an "autojunk" heuristic
# that treats very common characters specially in long sequences; that's
# not replicated here (irrelevant for the short strings this is meant
# for), so results could diverge from CPython's on long, junk-heavy input.
#
# `_find_longest_match` is a plain O(n·m) scan rather than CPython's
# junk-aware hashing — fine for a compatibility shim operating on
# reasonably short strings, not a performance-critical diff engine.
# `get_matching_blocks` is the standard recursive divide-around-the-best-
# match approach, implemented with an explicit `List`-backed stack instead
# of actual recursion (no generic self-recursion concern here since
# nothing here is generic, but a stack was just as simple to write).


def _findLongestMatch(a: str, b: str, aLo: int, aHi: int, bLo: int, bHi: int) -> tuple[int, int, int]:
    bestI: int = aLo
    bestJ: int = bLo
    bestSize: int = 0
    i: int = aLo
    while i < aHi:
        j: int = bLo
        while j < bHi:
            size: int = 0
            while i + size < aHi and j + size < bHi and _strutil.charAt(a, i + size) == _strutil.charAt(b, j + size):
                size += 1
            if size > bestSize:
                bestI = i
                bestJ = j
                bestSize = size
            j += 1
        i += 1
    return (bestI, bestJ, bestSize)


def _matchingBlockSum(a: str, b: str) -> int:
    total: int = 0
    stack: List[tuple[int, int, int, int]] = List[tuple[int, int, int, int]]()
    stack.append((0, _strutil.length(a), 0, _strutil.length(b)))
    while len(stack) > 0:
        region: tuple[int, int, int, int] = stack.__getitem__(len(stack) - 1)
        stack.pop(len(stack) - 1)
        aLo: int = region[0]
        aHi: int = region[1]
        bLo: int = region[2]
        bHi: int = region[3]
        found: tuple[int, int, int] = _findLongestMatch(a, b, aLo, aHi, bLo, bHi)
        i: int = found[0]
        j: int = found[1]
        k: int = found[2]
        if k > 0:
            total += k
            if aLo < i and bLo < j:
                stack.append((aLo, i, bLo, j))
            if i + k < aHi and j + k < bHi:
                stack.append((i + k, aHi, j + k, bHi))
    return total


def ratio(a: str, b: str) -> float:
    totalLength: int = _strutil.length(a) + _strutil.length(b)
    if totalLength == 0:
        return 1.0
    matched: int = _matchingBlockSum(a, b)
    return (2.0 * matched) / totalLength


def get_close_matches(word: str, possibilities: List[str], n: int, cutoff: float) -> List[str]:
    scored: List[tuple[float, str]] = List[tuple[float, str]]()
    index: int = 0
    while index < len(possibilities):
        candidate: str = possibilities.__getitem__(index)
        score: float = ratio(word, candidate)
        if score >= cutoff:
            position: int = 0
            while position < len(scored) and scored.__getitem__(position)[0] >= score:
                position += 1
            scored.insert(position, (score, candidate))
        index += 1
    result: List[str] = List[str]()
    limit: int = n
    if limit > len(scored):
        limit = len(scored)
    index = 0
    while index < limit:
        result.append(scored.__getitem__(index)[1])
        index += 1
    return result
