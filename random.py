@namespace("random")

from Promethium import List

# A small, opt-in subset of Python's random module, shaped quite differently
# from CPython's: this exposes only the `RandomGenerator` class (construct
# your own `RandomGenerator(seed)`), not CPython's free functions backed by
# an implicit global default instance, and not named plain `Random` either.
# Three things pushed toward this design rather than a closer copy:
#
# - A class literally named `Random` fails to compile for Toffee targets:
#   "The public type 'Random' has a duplicate with the same short name in
#   reference 'Elements', which is not allowed on Cocoa" — Cocoa's
#   flat (non-namespaced) type registry doesn't tolerate two types sharing
#   a short name even across different namespaces, unlike Echoes/Island/
#   Cooper. Confirmed by compiling the natural `class Random:` first and
#   hitting this on every Toffee target. `RandomGenerator` avoids it.
# - Research into each target's native RNG turned up real per-platform
#   uncertainty on every leg: Echoes' `System.Random` needs an *instance*
#   (no confirmed static/bare call), which needs confirming that Python-
#   style parens (`System.Random()`) instantiate a *native*, non-Promethium
#   type — the only precedent found anywhere in this codebase or the wider
#   Elements tree is a bare `raise ApplicationException(...)` expression,
#   not a value assigned to a variable; Island's `RemObjects.Elements.
#   System.Random` only exposes a raw `Cardinal`, no `NextDouble`/ranged
#   `Next`; Cooper's `Math.random()` can't be seeded (would need
#   `java.util.Random`, untested anywhere); and Toffee's options
#   (`arc4random_uniform`, `rtl.random`) are only confirmed used from
#   Oxygene-compiled code, never from a Promethium `.py` file, and a
#   module-defined `random()` calling bare Toffee `random()` would hit the
#   same self-recursion trap `math.py`'s `sqrt` documents.
# - CPython's implicit global default state would need either a native
#   instance stored in a module-level field, or a mutable module-level
#   field of any kind — genuinely untested anywhere in this codebase (the
#   one related precedent, a top-level `str` constant in `string.py`,
#   compiles but isn't consumable at all — see that module's notes).
#
# Rather than gamble on several unconfirmed compiler behaviors at once, this
# implements its own tiny, fully portable linear congruential generator —
# pure Promethium integer arithmetic, no native call and no per-target
# branching anywhere, relying only on `int` multiplication/addition wrapping
# on overflow the way plain `int` arithmetic ordinarily does on every target
# Elements compiles to. Its own instance field (`_state`) is exactly the
# kind of per-*instance* mutable field already used throughout `collections`
# (e.g. `Counter._entries`) — a solidly proven pattern, unlike a *module*-
# level one. This is a deliberately low-quality generator compared to
# CPython's Mersenne Twister (`random()` has 6 significant decimal digits of
# resolution, not a full 53-bit mantissa) — good enough for shuffling and
# sampling, not for anything statistically sensitive.


class RandomGenerator:
    _state: int

    def __init__(self, seed: int):
        self._state = seed

    def _next(self) -> int:
        self._state = self._state * 1103515245 + 12345
        return self._state

    def seed(self, value: int):
        self._state = value

    def next32(self) -> int:
        return self._next()

    def random(self) -> float:
        raw: int = self._next()
        if raw < 0:
            raw = -raw
        return (raw % 1000000) / 1000000.0

    def randint(self, a: int, b: int) -> int:
        span: int = b - a + 1
        raw: int = self._next()
        if raw < 0:
            raw = -raw
        return a + (raw % span)

    def uniform(self, a: float, b: float) -> float:
        return a + self.random() * (b - a)

    def choice(self, values: List[int]) -> int:
        return values.__getitem__(self.randint(0, len(values) - 1))

    def choice(self, values: List[float]) -> float:
        return values.__getitem__(self.randint(0, len(values) - 1))

    def choice(self, values: List[str]) -> str:
        return values.__getitem__(self.randint(0, len(values) - 1))

    def shuffle(self, values: List[int]):
        index: int = len(values) - 1
        while index > 0:
            j: int = self.randint(0, index)
            a: int = values.__getitem__(index)
            b: int = values.__getitem__(j)
            values[index] = b
            values[j] = a
            index -= 1

    def shuffle(self, values: List[float]):
        index: int = len(values) - 1
        while index > 0:
            j: int = self.randint(0, index)
            a: float = values.__getitem__(index)
            b: float = values.__getitem__(j)
            values[index] = b
            values[j] = a
            index -= 1

    def shuffle(self, values: List[str]):
        index: int = len(values) - 1
        while index > 0:
            j: int = self.randint(0, index)
            a: str = values.__getitem__(index)
            b: str = values.__getitem__(j)
            values[index] = b
            values[j] = a
            index -= 1
