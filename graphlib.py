@namespace("graphlib")

from Promethium import List, ValueError

# A small, opt-in subset of Python's graphlib module: just
# `TopologicalSorter.static_order()`, the most commonly used entry point.
# The incremental `prepare()`/`get_ready()`/`done()` protocol isn't
# attempted — `static_order()` covers the common case (compute a full
# dependency order up front) without needing to model in-progress state
# across calls.
#
# `add(node, predecessors)` takes a `List[T]` of predecessors rather than
# CPython's `*predecessors` (no `*args` support in this language slice).
# On a cycle, this raises `ValueError` rather than CPython's `CycleError`
# (no custom exception types have been established in this project beyond
# reusing `Promethium.ValueError`).
#
# Node lookup is a linear `.Equals`/`.isEqual` scan exactly like
# `Counter._index_of` — the same reason: unconstrained generic `T` has no
# `==`. `static_order()` itself is plain iterative Kahn's algorithm over
# index arrays, so it has no generic self-recursion to worry about (see the
# note in `itertools.py`) — there's no recursion here at all.


class TopologicalSorter[T]:
    _nodes: List[T]
    _predecessors: List[List[int]]

    def __init__(self):
        self._nodes = List[T]()
        self._predecessors = List[List[int]]()

    def _indexOf(self, node: T) -> int:
        index: int = 0
        while index < len(self._nodes):
            candidate: T = self._nodes.__getitem__(index)
            if defined("TOFFEE"):
                if candidate.isEqual(node):
                    return index
            else:
                if candidate.Equals(node):
                    return index
            index += 1
        return -1

    def _ensureNode(self, node: T) -> int:
        index: int = self._indexOf(node)
        if index >= 0:
            return index
        self._nodes.append(node)
        self._predecessors.append(List[int]())
        return len(self._nodes) - 1

    def add(self, node: T):
        self._ensureNode(node)

    def add(self, node: T, predecessors: List[T]):
        nodeIndex: int = self._ensureNode(node)
        preds: List[int] = self._predecessors.__getitem__(nodeIndex)
        index: int = 0
        while index < len(predecessors):
            predIndex: int = self._ensureNode(predecessors.__getitem__(index))
            preds.append(predIndex)
            index += 1

    def static_order(self) -> List[T]:
        n: int = len(self._nodes)

        inDegree: List[int] = List[int]()
        index: int = 0
        while index < n:
            inDegree.append(len(self._predecessors.__getitem__(index)))
            index += 1

        successors: List[List[int]] = List[List[int]]()
        index = 0
        while index < n:
            successors.append(List[int]())
            index += 1

        index = 0
        while index < n:
            preds: List[int] = self._predecessors.__getitem__(index)
            predIndex: int = 0
            while predIndex < len(preds):
                p: int = preds.__getitem__(predIndex)
                successors.__getitem__(p).append(index)
                predIndex += 1
            index += 1

        queue: List[int] = List[int]()
        index = 0
        while index < n:
            if inDegree.__getitem__(index) == 0:
                queue.append(index)
            index += 1

        result: List[T] = List[T]()
        processed: int = 0
        while len(queue) > 0:
            current: int = queue.__getitem__(0)
            queue.pop(0)
            result.append(self._nodes.__getitem__(current))
            processed += 1
            succs: List[int] = successors.__getitem__(current)
            succIndex: int = 0
            while succIndex < len(succs):
                s: int = succs.__getitem__(succIndex)
                newDegree: int = inDegree.__getitem__(s) - 1
                inDegree.pop(s)
                inDegree.insert(s, newDegree)
                if newDegree == 0:
                    queue.append(s)
                succIndex += 1

        if processed < n:
            raise ValueError("nodes are in a cycle")
        return result
