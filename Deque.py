@namespace("collections")

from Promethium import List


# Deque, backed by a single Promethium List. `append`/`pop` at the list's
# own end are List's normal operations; `appendleft`/`popleft`/`extendleft`
# use List's `insert(0, ...)`/`pop(0)`, which are O(n) — a real deque needs
# its own ring-buffer/native structure for O(1) at both ends, which is
# future work. This is correct, not fast.
#
# `copy()` returns Deque[T] — that needed a Promethium compiler fix for
# generic self-reference (see the note in Counter.py), which has since
# landed.
#
# `maxlen` uses `-1` as the "unbounded" sentinel, the same concrete stand-in
# for CPython's `None` default this project already uses elsewhere (see
# `bisect.py`'s `hi` parameter). When bounded, `append`/`appendleft` each
# evict from the *opposite* end as needed, matching CPython's per-append
# eviction exactly (not a single bulk trim at the end) — `extend`/
# `extendleft` are implemented by looping over `append`/`appendleft`, so
# they inherit the same per-item eviction for free.


class Deque[T]:
    _entries: List[T]
    maxlen: int

    def __init__(self):
        self._entries = List[T]()
        self.maxlen = -1

    def __init__(self, values: List[T]):
        self._entries = values.copy()
        self.maxlen = -1

    def __init__(self, maxlen: int):
        self._entries = List[T]()
        self.maxlen = maxlen

    def __init__(self, values: List[T], maxlen: int):
        self._entries = List[T]()
        self.maxlen = maxlen
        self.extend(values)

    def __len__(self) -> int:
        return len(self._entries)

    def __getitem__(self, index: int) -> T:
        return self._entries.__getitem__(index)

    def append(self, value: T):
        self._entries.append(value)
        if self.maxlen >= 0:
            while len(self._entries) > self.maxlen:
                self._entries.pop(0)

    def appendleft(self, value: T):
        self._entries.insert(0, value)
        if self.maxlen >= 0:
            while len(self._entries) > self.maxlen:
                self._entries.pop(len(self._entries) - 1)

    def pop(self) -> T:
        index: int = len(self._entries) - 1
        value: T = self._entries.__getitem__(index)
        self._entries.pop(index)
        return value

    def popleft(self) -> T:
        value: T = self._entries.__getitem__(0)
        self._entries.pop(0)
        return value

    def extend(self, values: List[T]):
        index: int = 0
        while index < len(values):
            self.append(values.__getitem__(index))
            index += 1

    def extendleft(self, values: List[T]):
        index: int = 0
        while index < len(values):
            self.appendleft(values.__getitem__(index))
            index += 1

    def clear(self):
        self._entries.clear()

    def count(self, value: T) -> int:
        result: int = 0
        index: int = 0
        while index < len(self._entries):
            candidate: T = self._entries.__getitem__(index)
            matched: bool = False
            if defined("TOFFEE"):
                matched = candidate.isEqual(value)
            else:
                matched = candidate.Equals(value)
            if matched:
                result += 1
            index += 1
        return result

    def __contains__(self, value: T) -> bool:
        return self.count(value) > 0

    def Contains(self, value: T) -> bool:
        return self.count(value) > 0

    def rotate(self, n: int = 1):
        total: int = len(self._entries)
        if total == 0:
            return
        steps: int = n % total
        if steps < 0:
            steps += total
        index: int = 0
        while index < steps:
            last: int = len(self._entries) - 1
            value: T = self._entries.__getitem__(last)
            self._entries.pop(last)
            self._entries.insert(0, value)
            index += 1

    def copy(self) -> Deque[T]:
        return Deque[T](self._entries, self.maxlen)
