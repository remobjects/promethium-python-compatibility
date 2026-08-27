@namespace("queue")

from Promethium import ValueError
from collections import Deque

# A small, opt-in subset of Python's queue module: `PyQueue`/`PyLifoQueue`,
# both thin wrappers over the already-shipped `collections.Deque`. No real
# concurrency: this language slice has no threading primitives (the same
# reason `asyncio`/generators are excluded), so `put`/`get` never actually
# block — they just raise `Promethium.ValueError` on overflow/underflow
# instead of CPython's queue-specific `queue.Full`/`queue.Empty`
# exceptions (this project has no custom exception types beyond reusing
# `ValueError`, same convention `graphlib.py` documents for its own
# cycle-detection error). `put_nowait`/`get_nowait` are aliases for
# `put`/`get` for the same reason — there's no blocking variant to be the
# non-blocking alternative *to*.
#
# `maxsize` uses `-1` as the "unbounded" sentinel, the same concrete
# stand-in for CPython's `None`/`0` this project already uses elsewhere
# (`Deque.maxlen`, `bisect.py`'s `hi`).


class PyQueue[T]:
    _entries: Deque[T]
    maxsize: int

    def __init__(self):
        self._entries = Deque[T]()
        self.maxsize = -1

    def __init__(self, maxsize: int):
        self._entries = Deque[T]()
        self.maxsize = maxsize

    def qsize(self) -> int:
        return len(self._entries)

    def empty(self) -> bool:
        return len(self._entries) == 0

    def full(self) -> bool:
        return self.maxsize >= 0 and len(self._entries) >= self.maxsize

    def put(self, item: T):
        if self.full():
            raise ValueError("queue.PyQueue.put: queue is full")
        self._entries.append(item)

    def put_nowait(self, item: T):
        self.put(item)

    def get(self) -> T:
        if self.empty():
            raise ValueError("queue.PyQueue.get: queue is empty")
        return self._entries.popleft()

    def get_nowait(self) -> T:
        return self.get()


class PyLifoQueue[T]:
    _entries: Deque[T]
    maxsize: int

    def __init__(self):
        self._entries = Deque[T]()
        self.maxsize = -1

    def __init__(self, maxsize: int):
        self._entries = Deque[T]()
        self.maxsize = maxsize

    def qsize(self) -> int:
        return len(self._entries)

    def empty(self) -> bool:
        return len(self._entries) == 0

    def full(self) -> bool:
        return self.maxsize >= 0 and len(self._entries) >= self.maxsize

    def put(self, item: T):
        if self.full():
            raise ValueError("queue.PyLifoQueue.put: queue is full")
        self._entries.append(item)

    def put_nowait(self, item: T):
        self.put(item)

    def get(self) -> T:
        if self.empty():
            raise ValueError("queue.PyLifoQueue.get: queue is empty")
        return self._entries.pop()

    def get_nowait(self) -> T:
        return self.get()
