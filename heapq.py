@namespace("heapq")

from Promethium import List


# A small, opt-in subset of Python's heapq module: a binary min-heap stored
# directly in a Promethium List, exactly like CPython's own array-backed
# implementation.
#
# Unconstrained generic T has no `<` operator in Promethium (confirmed: no
# file in PromethiumBaseLibrary or this project compares two generic-typed
# values, and PromethiumBaseLibrary's own sorted()/min()/max() in
# Builtins.py are hand-overloaded for List[int]/List[float]/List[str] rather
# than generic, for exactly this reason). This module follows that same
# precedent: every function is overloaded for int, float, and str rather
# than generic over T.
#
# The sift algorithms are a direct port of CPython's Lib/heapq.py, using
# `>> 1` for the parent-index halving (confirmed supported: the Promethium
# grammar lists shift operators as supported, unlike floor division `//`,
# which no other file in this codebase uses).


def heappush(heap: List[int], item: int):
    heap.append(item)
    _siftdown(heap, 0, len(heap) - 1)

def heappush(heap: List[float], item: float):
    heap.append(item)
    _siftdown(heap, 0, len(heap) - 1)

def heappush(heap: List[str], item: str):
    heap.append(item)
    _siftdown(heap, 0, len(heap) - 1)


def heappop(heap: List[int]) -> int:
    lastItem: int = heap.pop()
    if len(heap) == 0:
        return lastItem
    returnItem: int = heap.__getitem__(0)
    heap.__setitem__(0, lastItem)
    _siftup(heap, 0)
    return returnItem

def heappop(heap: List[float]) -> float:
    lastItem: float = heap.pop()
    if len(heap) == 0:
        return lastItem
    returnItem: float = heap.__getitem__(0)
    heap.__setitem__(0, lastItem)
    _siftup(heap, 0)
    return returnItem

def heappop(heap: List[str]) -> str:
    lastItem: str = heap.pop()
    if len(heap) == 0:
        return lastItem
    returnItem: str = heap.__getitem__(0)
    heap.__setitem__(0, lastItem)
    _siftup(heap, 0)
    return returnItem


def heapreplace(heap: List[int], item: int) -> int:
    returnItem: int = heap.__getitem__(0)
    heap.__setitem__(0, item)
    _siftup(heap, 0)
    return returnItem

def heapreplace(heap: List[float], item: float) -> float:
    returnItem: float = heap.__getitem__(0)
    heap.__setitem__(0, item)
    _siftup(heap, 0)
    return returnItem

def heapreplace(heap: List[str], item: str) -> str:
    returnItem: str = heap.__getitem__(0)
    heap.__setitem__(0, item)
    _siftup(heap, 0)
    return returnItem


def heappushpop(heap: List[int], item: int) -> int:
    result: int = item
    if len(heap) > 0 and heap.__getitem__(0) < result:
        result = heap.__getitem__(0)
        heap.__setitem__(0, item)
        _siftup(heap, 0)
    return result

def heappushpop(heap: List[float], item: float) -> float:
    result: float = item
    if len(heap) > 0 and heap.__getitem__(0) < result:
        result = heap.__getitem__(0)
        heap.__setitem__(0, item)
        _siftup(heap, 0)
    return result

def heappushpop(heap: List[str], item: str) -> str:
    result: str = item
    if len(heap) > 0 and heap.__getitem__(0) < result:
        result = heap.__getitem__(0)
        heap.__setitem__(0, item)
        _siftup(heap, 0)
    return result


def heapify(heap: List[int]):
    index: int = (len(heap) >> 1) - 1
    while index >= 0:
        _siftup(heap, index)
        index -= 1

def heapify(heap: List[float]):
    index: int = (len(heap) >> 1) - 1
    while index >= 0:
        _siftup(heap, index)
        index -= 1

def heapify(heap: List[str]):
    index: int = (len(heap) >> 1) - 1
    while index >= 0:
        _siftup(heap, index)
        index -= 1


def nsmallest(n: int, values: List[int]) -> List[int]:
    ordered: List[int] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[int] = List[int]()
    index: int = 0
    while index < limit:
        result.append(ordered.__getitem__(index))
        index += 1
    return result

def nsmallest(n: int, values: List[float]) -> List[float]:
    ordered: List[float] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[float] = List[float]()
    index: int = 0
    while index < limit:
        result.append(ordered.__getitem__(index))
        index += 1
    return result

def nsmallest(n: int, values: List[str]) -> List[str]:
    ordered: List[str] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[str] = List[str]()
    index: int = 0
    while index < limit:
        result.append(ordered.__getitem__(index))
        index += 1
    return result


def nlargest(n: int, values: List[int]) -> List[int]:
    ordered: List[int] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[int] = List[int]()
    index: int = len(ordered) - 1
    count: int = 0
    while count < limit:
        result.append(ordered.__getitem__(index))
        index -= 1
        count += 1
    return result

def nlargest(n: int, values: List[float]) -> List[float]:
    ordered: List[float] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[float] = List[float]()
    index: int = len(ordered) - 1
    count: int = 0
    while count < limit:
        result.append(ordered.__getitem__(index))
        index -= 1
        count += 1
    return result

def nlargest(n: int, values: List[str]) -> List[str]:
    ordered: List[str] = sorted(values)
    limit: int = _clamp(n, len(ordered))
    result: List[str] = List[str]()
    index: int = len(ordered) - 1
    count: int = 0
    while count < limit:
        result.append(ordered.__getitem__(index))
        index -= 1
        count += 1
    return result


def _clamp(n: int, count: int) -> int:
    limit: int = n
    if limit > count:
        limit = count
    if limit < 0:
        limit = 0
    return limit


def _siftdown(heap: List[int], startpos: int, pos: int):
    newItem: int = heap.__getitem__(pos)
    position: int = pos
    while position > startpos:
        parentpos: int = (position - 1) >> 1
        parent: int = heap.__getitem__(parentpos)
        if newItem < parent:
            heap.__setitem__(position, parent)
            position = parentpos
        else:
            break
    heap.__setitem__(position, newItem)

def _siftdown(heap: List[float], startpos: int, pos: int):
    newItem: float = heap.__getitem__(pos)
    position: int = pos
    while position > startpos:
        parentpos: int = (position - 1) >> 1
        parent: float = heap.__getitem__(parentpos)
        if newItem < parent:
            heap.__setitem__(position, parent)
            position = parentpos
        else:
            break
    heap.__setitem__(position, newItem)

def _siftdown(heap: List[str], startpos: int, pos: int):
    newItem: str = heap.__getitem__(pos)
    position: int = pos
    while position > startpos:
        parentpos: int = (position - 1) >> 1
        parent: str = heap.__getitem__(parentpos)
        if newItem < parent:
            heap.__setitem__(position, parent)
            position = parentpos
        else:
            break
    heap.__setitem__(position, newItem)


def _siftup(heap: List[int], pos: int):
    endpos: int = len(heap)
    startpos: int = pos
    newItem: int = heap.__getitem__(pos)
    position: int = pos
    childpos: int = 2 * position + 1
    while childpos < endpos:
        rightpos: int = childpos + 1
        if rightpos < endpos and not (heap.__getitem__(childpos) < heap.__getitem__(rightpos)):
            childpos = rightpos
        heap.__setitem__(position, heap.__getitem__(childpos))
        position = childpos
        childpos = 2 * position + 1
    heap.__setitem__(position, newItem)
    _siftdown(heap, startpos, position)

def _siftup(heap: List[float], pos: int):
    endpos: int = len(heap)
    startpos: int = pos
    newItem: float = heap.__getitem__(pos)
    position: int = pos
    childpos: int = 2 * position + 1
    while childpos < endpos:
        rightpos: int = childpos + 1
        if rightpos < endpos and not (heap.__getitem__(childpos) < heap.__getitem__(rightpos)):
            childpos = rightpos
        heap.__setitem__(position, heap.__getitem__(childpos))
        position = childpos
        childpos = 2 * position + 1
    heap.__setitem__(position, newItem)
    _siftdown(heap, startpos, position)

def _siftup(heap: List[str], pos: int):
    endpos: int = len(heap)
    startpos: int = pos
    newItem: str = heap.__getitem__(pos)
    position: int = pos
    childpos: int = 2 * position + 1
    while childpos < endpos:
        rightpos: int = childpos + 1
        if rightpos < endpos and not (heap.__getitem__(childpos) < heap.__getitem__(rightpos)):
            childpos = rightpos
        heap.__setitem__(position, heap.__getitem__(childpos))
        position = childpos
        childpos = 2 * position + 1
    heap.__setitem__(position, newItem)
    _siftdown(heap, startpos, position)
