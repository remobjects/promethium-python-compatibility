@namespace("collections")

from Promethium import List


# A small, opt-in subset of Python's collections module.
#
# Import this module explicitly from Promethium code. It deliberately does not
# alter built-ins or provide target-specific behavior.
#
# Counter is backed by a single Promethium List of (key, count) tuples rather
# than a Dictionary. Two things ruled Dictionary out: bracket assignment
# (`d[key] = value`) does not route to a native setter for consumers outside
# Dictionary's own defining file (no `__setitem__` is declared, and mapped
# types don't expose their native indexer to external bracket syntax either),
# and `Dictionary.update(Dictionary)` itself throws at runtime
# (OxygeneBinderException: "No methods called 'get'") because its `values:
# Dictionary[Key, Value]` parameter is a generic class referencing its own
# enclosing type, which Promethium resolves dynamically against the erased
# native dictionary instead of statically against Dictionary's own methods.
# A List of tuples sidesteps both: lookups are a linear scan (fine for the
# small/moderate key counts Counter is meant for), and replacing an entry
# uses the already-proven `pop(index)` + `insert(index, value)` pair. Key
# order for tied counts is therefore also just list order: first-insertion
# order, matching CPython's dict/Counter guarantee, with no separate ordering
# structure needed.
#
# Counter-to-Counter operations (construct/update/subtract from another
# Counter, copy, +, -, &, |) were blocked for a while by a Promethium
# compiler limitation where a generic class could not resolve its own name
# from within its own body (not even unparameterized) — a method on
# Counter[T] could not take or return another Counter[T]/Counter. That is
# now fixed (verified with an isolated repro before relying on it here), so
# they're implemented below like any other method.


class Counter[T]:
    _entries: List[tuple[T, int]]

    def __init__(self):
        self._entries = List[tuple[T, int]]()

    def __init__(self, values: List[T]):
        self._entries = List[tuple[T, int]]()
        self.update(values)

    def __init__(self, values: Counter[T]):
        self._entries = List[tuple[T, int]]()
        self.update(values)

    def _index_of(self, key: T) -> int:
        index: int = 0
        while index < len(self._entries):
            candidate: T = self._entries.__getitem__(index)[0]
            if defined("TOFFEE"):
                if candidate.isEqual(key):
                    return index
            else:
                if candidate.Equals(key):
                    return index
            index += 1
        return -1

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: T) -> bool:
        return self._index_of(key) >= 0

    def Contains(self, key: T) -> bool:
        return self._index_of(key) >= 0

    def __getitem__(self, key: T) -> int:
        index: int = self._index_of(key)
        if index < 0:
            return 0
        return self._entries.__getitem__(index)[1]

    def __setitem__(self, key: T, value: int):
        index: int = self._index_of(key)
        if index < 0:
            self._entries.append((key, value))
        else:
            self._entries.pop(index)
            self._entries.insert(index, (key, value))

    def get(self, key: T, default: int = 0) -> int:
        index: int = self._index_of(key)
        if index < 0:
            return default
        return self._entries.__getitem__(index)[1]

    def keys(self) -> List[T]:
        result: List[T] = List[T]()
        index: int = 0
        while index < len(self._entries):
            result.append(self._entries.__getitem__(index)[0])
            index += 1
        return result

    def items(self) -> List[tuple[T, int]]:
        return self._entries.copy()

    def update(self, values: List[T]):
        index: int = 0
        while index < len(values):
            key: T = values.__getitem__(index)
            self[key] = self.get(key, 0) + 1
            index += 1

    def subtract(self, values: List[T]):
        index: int = 0
        while index < len(values):
            key: T = values.__getitem__(index)
            self[key] = self.get(key, 0) - 1
            index += 1

    def update(self, values: Counter[T]):
        otherItems: List[tuple[T, int]] = values.items()
        index: int = 0
        while index < len(otherItems):
            entry: tuple[T, int] = otherItems.__getitem__(index)
            self[entry[0]] = self.get(entry[0], 0) + entry[1]
            index += 1

    def subtract(self, values: Counter[T]):
        otherItems: List[tuple[T, int]] = values.items()
        index: int = 0
        while index < len(otherItems):
            entry: tuple[T, int] = otherItems.__getitem__(index)
            self[entry[0]] = self.get(entry[0], 0) - entry[1]
            index += 1

    def copy(self) -> Counter[T]:
        return Counter[T](self)

    def __add__(self, other: Counter[T]) -> Counter[T]:
        result: Counter[T] = Counter[T]()
        selfItems: List[tuple[T, int]] = self.items()
        index: int = 0
        while index < len(selfItems):
            entry: tuple[T, int] = selfItems.__getitem__(index)
            combined: int = entry[1] + other.get(entry[0], 0)
            if combined > 0:
                result[entry[0]] = combined
            index += 1
        otherKeys: List[T] = other.keys()
        index = 0
        while index < len(otherKeys):
            key: T = otherKeys.__getitem__(index)
            if not self.__contains__(key):
                combined: int = other.get(key, 0)
                if combined > 0:
                    result[key] = combined
            index += 1
        return result

    def __sub__(self, other: Counter[T]) -> Counter[T]:
        result: Counter[T] = Counter[T]()
        selfItems: List[tuple[T, int]] = self.items()
        index: int = 0
        while index < len(selfItems):
            entry: tuple[T, int] = selfItems.__getitem__(index)
            combined: int = entry[1] - other.get(entry[0], 0)
            if combined > 0:
                result[entry[0]] = combined
            index += 1
        return result

    def __and__(self, other: Counter[T]) -> Counter[T]:
        result: Counter[T] = Counter[T]()
        selfItems: List[tuple[T, int]] = self.items()
        index: int = 0
        while index < len(selfItems):
            entry: tuple[T, int] = selfItems.__getitem__(index)
            otherCount: int = other.get(entry[0], 0)
            minCount: int = entry[1]
            if otherCount < minCount:
                minCount = otherCount
            if minCount > 0:
                result[entry[0]] = minCount
            index += 1
        return result

    def __or__(self, other: Counter[T]) -> Counter[T]:
        result: Counter[T] = Counter[T]()
        selfItems: List[tuple[T, int]] = self.items()
        index: int = 0
        while index < len(selfItems):
            entry: tuple[T, int] = selfItems.__getitem__(index)
            otherCount: int = other.get(entry[0], 0)
            maxCount: int = entry[1]
            if otherCount > maxCount:
                maxCount = otherCount
            if maxCount > 0:
                result[entry[0]] = maxCount
            index += 1
        otherKeys: List[T] = other.keys()
        index = 0
        while index < len(otherKeys):
            key: T = otherKeys.__getitem__(index)
            if not self.__contains__(key):
                count: int = other.get(key, 0)
                if count > 0:
                    result[key] = count
            index += 1
        return result

    def total(self) -> int:
        result: int = 0
        index: int = 0
        while index < len(self._entries):
            result += self._entries.__getitem__(index)[1]
            index += 1
        return result

    def elements(self) -> List[T]:
        result: List[T] = List[T]()
        index: int = 0
        while index < len(self._entries):
            entry: tuple[T, int] = self._entries.__getitem__(index)
            copies: int = 0
            while copies < entry[1]:
                result.append(entry[0])
                copies += 1
            index += 1
        return result

    def most_common(self) -> List[tuple[T, int]]:
        result: List[tuple[T, int]] = List[tuple[T, int]]()
        index: int = 0
        while index < len(self._entries):
            entry: tuple[T, int] = self._entries.__getitem__(index)
            position: int = 0
            while position < len(result) and result.__getitem__(position)[1] >= entry[1]:
                position += 1
            result.insert(position, entry)
            index += 1
        return result

    def most_common(self, n: int) -> List[tuple[T, int]]:
        full: List[tuple[T, int]] = self.most_common()
        limit: int = n
        if limit > len(full):
            limit = len(full)
        if limit < 0:
            limit = 0
        result: List[tuple[T, int]] = List[tuple[T, int]]()
        index: int = 0
        while index < limit:
            result.append(full.__getitem__(index))
            index += 1
        return result

    def pop(self, key: T, default: int) -> int:
        index: int = self._index_of(key)
        if index < 0:
            return default
        value: int = self._entries.__getitem__(index)[1]
        self._entries.pop(index)
        return value

    def clear(self):
        self._entries.clear()