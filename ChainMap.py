@namespace("collections")

from Promethium import List, Dictionary, KeyError


# ChainMap groups several Dictionary mappings and searches them in order,
# first match wins, matching CPython's semantics. It only ever calls
# get/__contains__/keys on the wrapped mappings — never their `update`
# method, which is the one Dictionary operation known to throw at runtime
# on its own generic self-reference (see the note in Counter.py).
#
# `new_child`/`parents` return ChainMap[Key, Value] — that needed a
# Promethium compiler fix for generic self-reference (see the note in
# Counter.py), which has since landed.
#
# `__setitem__` (CPython writes a missing key to `self.maps[0]`) is not
# implemented: `Dictionary` declares neither `__getitem__` nor `__setitem__`
# itself, so it has no indexer property to write through even now that the
# @mapped-indexer bug is fixed — that fix only applies to a class that
# declares the methods itself. Setting a single key on a `Dictionary` from
# outside its own file still has no working path (no external bracket
# write, and `Dictionary.update(Dictionary)` throws at runtime — see above).


class ChainMap[Key, Value]:
    _maps: List[Dictionary[Key, Value]]

    def __init__(self):
        self._maps = List[Dictionary[Key, Value]]()
        self._maps.append(Dictionary[Key, Value]())

    def __init__(self, maps: List[Dictionary[Key, Value]]):
        self._maps = maps.copy()

    def maps(self) -> List[Dictionary[Key, Value]]:
        return self._maps.copy()

    def __len__(self) -> int:
        return len(self.keys())

    def __contains__(self, key: Key) -> bool:
        index: int = 0
        while index < len(self._maps):
            if self._maps.__getitem__(index).__contains__(key):
                return True
            index += 1
        return False

    def Contains(self, key: Key) -> bool:
        return self.__contains__(key)

    def __getitem__(self, key: Key) -> Value:
        index: int = 0
        while index < len(self._maps):
            candidate: Dictionary[Key, Value] = self._maps.__getitem__(index)
            if candidate.__contains__(key):
                return candidate.get(key)
            index += 1
        raise KeyError(key)

    def get(self, key: Key, default: Value = None) -> Value:
        index: int = 0
        while index < len(self._maps):
            candidate: Dictionary[Key, Value] = self._maps.__getitem__(index)
            if candidate.__contains__(key):
                return candidate.get(key)
            index += 1
        return default

    def keys(self) -> List[Key]:
        result: List[Key] = List[Key]()
        mapIndex: int = 0
        while mapIndex < len(self._maps):
            candidateKeys: List[Key] = self._maps.__getitem__(mapIndex).keys()
            keyIndex: int = 0
            while keyIndex < len(candidateKeys):
                key: Key = candidateKeys.__getitem__(keyIndex)
                if not _list_contains(result, key):
                    result.append(key)
                keyIndex += 1
            mapIndex += 1
        return result

    def clear(self):
        self._maps.__getitem__(0).clear()

    def new_child(self, m: Dictionary[Key, Value] = None) -> ChainMap[Key, Value]:
        newMap: Dictionary[Key, Value] = m
        if newMap is None:
            newMap = Dictionary[Key, Value]()
        combined: List[Dictionary[Key, Value]] = List[Dictionary[Key, Value]]()
        combined.append(newMap)
        index: int = 0
        while index < len(self._maps):
            combined.append(self._maps.__getitem__(index))
            index += 1
        return ChainMap[Key, Value](combined)

    def parents(self) -> ChainMap[Key, Value]:
        combined: List[Dictionary[Key, Value]] = List[Dictionary[Key, Value]]()
        index: int = 1
        while index < len(self._maps):
            combined.append(self._maps.__getitem__(index))
            index += 1
        return ChainMap[Key, Value](combined)


def _list_contains[T](values: List[T], value: T) -> bool:
    index: int = 0
    while index < len(values):
        candidate: T = values.__getitem__(index)
        if defined("TOFFEE"):
            if candidate.isEqual(value):
                return True
        else:
            if candidate.Equals(value):
                return True
        index += 1
    return False
