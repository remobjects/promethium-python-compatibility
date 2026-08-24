@namespace("collections")

from Promethium import List, ValueError


# DefaultDict: a mapping like OrderedDict, but a missing key auto-vivifies
# using a stored zero-argument factory instead of raising — e.g.
# DefaultDict(list) so `d[key].append(x)` works without checking first.
#
# The factory is stored as a plain, implicitly-typed field from an untyped
# constructor parameter (`self._factory = factory`, no annotation) and
# invoked with `.Invoke()`. This works on Echoes, Cooper, and Island, where
# enough type information survives for the call to return a real Value.
#
# It does not work on Toffee: there, the factory value erases to a dynamic
# Objective-C `id`, and invoking it dynamically returns void with no way to
# recover a typed result (confirmed empirically: `self._factory.invoke()`
# compiles but its result cannot be assigned to Value, and there is no
# accessible cast from `id` to a generic Value either). This is unrelated to
# the separate @mapped-indexer issue that blocked Counter/OrderedDict/
# ChainMap/Deque earlier — this one is about dynamic block invocation
# losing static return-type information, not about indexers.
#
# This file still compiles for every target, including Toffee, so `from
# collections import DefaultDict` always resolves and everything except
# auto-vivification works there too (construction, get/set/pop/keys/etc. on
# keys that are already present). Only reaching for the factory on a
# missing key raises on Toffee specifically, at the point of use, instead
# of either failing to compile or silently returning a wrong value.


class DefaultDict[Key, Value]:
    _entries: List[tuple[Key, Value]]

    def __init__(self, factory):
        self._factory = factory
        self._entries = List[tuple[Key, Value]]()

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
        if index >= 0:
            return self._entries.__getitem__(index)[1]
        if defined("TOFFEE"):
            raise ValueError("DefaultDict cannot invoke its factory on Toffee yet; set the key explicitly instead of relying on auto-vivification")
        else:
            value: Value = self._factory.Invoke()
            self[key] = value
            return value

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

    def clear(self):
        self._entries.clear()