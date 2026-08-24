@namespace("collections")

from Promethium import List


# OrderedDict: a mapping that remembers insertion order, backed by a single
# Promethium List of (key, value) tuples for the same reasons Counter is
# (see Counter.py): Dictionary.update(Dictionary) throws at runtime on its
# own generic self-reference, and bracket assignment does not route to a
# native setter for consumers outside Dictionary's defining file. Order is
# therefore just list order, with no separate bookkeeping needed.
#
# `move_to_end`/`popitem` cover the common ordering operations. `copy()`
# returns OrderedDict[Key, Value] — that needed a Promethium compiler fix
# for generic self-reference (see the note in Counter.py), which has since
# landed.


class OrderedDict[Key, Value]:
    _entries: List[tuple[Key, Value]]

    def __init__(self):
        self._entries = List[tuple[Key, Value]]()

    def __init__(self, values: List[tuple[Key, Value]]):
        self._entries = List[tuple[Key, Value]]()
        index: int = 0
        while index < len(values):
            entry: tuple[Key, Value] = values.__getitem__(index)
            self[entry[0]] = entry[1]
            index += 1

    def _index_of(self, key: Key) -> int:
        index: int = 0
        while index < len(self._entries):
            candidate: Key = self._entries.__getitem__(index)[0]
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

    def __contains__(self, key: Key) -> bool:
        return self._index_of(key) >= 0

    def Contains(self, key: Key) -> bool:
        return self._index_of(key) >= 0

    def __getitem__(self, key: Key) -> Value:
        index: int = self._index_of(key)
        return self._entries.__getitem__(index)[1]

    def __setitem__(self, key: Key, value: Value):
        index: int = self._index_of(key)
        if index < 0:
            self._entries.append((key, value))
        else:
            self._entries[index] = (key, value)

    def get(self, key: Key, default: Value = None) -> Value:
        index: int = self._index_of(key)
        if index < 0:
            return default
        return self._entries.__getitem__(index)[1]

    def keys(self) -> List[Key]:
        result: List[Key] = List[Key]()
        index: int = 0
        while index < len(self._entries):
            result.append(self._entries.__getitem__(index)[0])
            index += 1
        return result

    def values(self) -> List[Value]:
        result: List[Value] = List[Value]()
        index: int = 0
        while index < len(self._entries):
            result.append(self._entries.__getitem__(index)[1])
            index += 1
        return result

    def items(self) -> List[tuple[Key, Value]]:
        return self._entries.copy()

    def pop(self, key: Key, default: Value = None) -> Value:
        index: int = self._index_of(key)
        if index < 0:
            return default
        value: Value = self._entries.__getitem__(index)[1]
        self._entries.pop(index)
        return value

    def popitem(self, last: bool = True) -> tuple[Key, Value]:
        index: int = len(self._entries) - 1
        if not last:
            index = 0
        entry: tuple[Key, Value] = self._entries.__getitem__(index)
        self._entries.pop(index)
        return entry

    def move_to_end(self, key: Key, last: bool = True):
        index: int = self._index_of(key)
        if index < 0:
            return
        entry: tuple[Key, Value] = self._entries.__getitem__(index)
        self._entries.pop(index)
        if last:
            self._entries.append(entry)
        else:
            self._entries.insert(0, entry)

    def clear(self):
        self._entries.clear()

    def copy(self) -> OrderedDict[Key, Value]:
        return OrderedDict[Key, Value](self.items())
