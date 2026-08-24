@namespace("uuid")

from random import RandomGenerator

# A small, opt-in subset of Python's uuid module: just `uuid4()`, and only
# as raw components — no canonical hyphenated hex string. `int`-to-`str`
# formatting needs a native per-platform call this codebase has never
# established (see `fractions.py`'s identical `__str__` note), and a
# 128-bit value can't be stored as a single Promethium `int` at all
# (`int` is a *signed* 32-bit `Int32` — the same overflow problem
# `ipaddress.py` avoids for a 32-bit address applies twice as hard here).
#
# `UUID4Value` instead stores the 128 bits as four 32-bit words (`w0`..
# `w3`, most-significant first), generated via `RandomGenerator.next32()`
# (added to `random.py` alongside this module — the existing `randint`
# can't safely cover a full 32-bit span: `b - a + 1` for the full `Int32`
# range itself overflows `Int32`). The version (`0100`) and variant
# (`10xx`) bits are set via `&`/`|`/`>>`, already proven bitwise ops (see
# `operator.py`/`ipaddress.py`) — masking after a right-shift extracts the
# correct bits regardless of whether the shift is arithmetic or logical on
# a negative `int`, so the signedness of `int` doesn't affect correctness
# here despite these being "random bits", not a numeric magnitude.
#
# This is randomness quality equivalent to `random.py`'s own generator
# (a small LCG, not cryptographically secure) — good enough for
# non-adversarial unique-ID needs, not for anything security-sensitive.


class UUID4Value:
    w0: int
    w1: int
    w2: int
    w3: int

    def __init__(self, w0: int, w1: int, w2: int, w3: int):
        self.w0 = w0
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3

    def __eq__(self, other: UUID4Value) -> bool:
        return self.w0 == other.w0 and self.w1 == other.w1 and self.w2 == other.w2 and self.w3 == other.w3

    def version(self) -> int:
        return (self.w1 >> 12) & 15

    def variant_bits(self) -> int:
        return (self.w2 >> 30) & 3


def uuid4(rng: RandomGenerator) -> UUID4Value:
    w0: int = rng.next32()

    randomW1: int = rng.next32()
    timeMid: int = (randomW1 >> 16) & 65535
    timeHiRandom: int = randomW1 & 4095
    timeHiAndVersion: int = timeHiRandom | 16384
    w1: int = (timeMid << 16) | timeHiAndVersion

    randomW2: int = rng.next32()
    clockSeqRandom: int = (randomW2 >> 24) & 63
    clockSeqHiAndReserved: int = clockSeqRandom | 128
    clockSeqLow: int = (randomW2 >> 16) & 255
    nodeHigh16: int = randomW2 & 65535
    w2: int = (clockSeqHiAndReserved << 24) | (clockSeqLow << 16) | nodeHigh16

    w3: int = rng.next32()

    return UUID4Value(w0, w1, w2, w3)
