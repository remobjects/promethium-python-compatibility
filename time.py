@namespace("time")

# A small, opt-in subset of Python's time module: just `time()`, reading
# the real wall clock — the piece `datetime.py` explicitly deferred
# ("`now()`/`today()` are NOT attempted: reading the actual wall clock
# needs the same kind of per-target native-call research `math.py`'s
# functions and `random.py`'s RNG needed, which hasn't been done for
# time"). Turns out no per-target branching is needed here at all: the
# bare `DateTime` identifier in scope resolves to RTL2's own
# `RemObjects.Elements.RTL.DateTime`, not the platform-native BCL type —
# it's already a genuine cross-platform abstraction (backed by
# `java.util.Calendar` on Cooper, `NSDate` on Toffee, `System.DateTime`
# on Echoes, `RemObjects.Elements.System.DateTime` on Island internally),
# with its own `UtcNow`/`ToUnixTimeSeconds()` doing the per-target work
# this module would otherwise have needed to do by hand.


def time() -> float:
    seconds: int = RemObjects.Elements.RTL.DateTime.UtcNow.ToUnixTimeSeconds()
    return seconds + 0.0
