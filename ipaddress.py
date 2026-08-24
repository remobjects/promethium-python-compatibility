@namespace("ipaddress")

# A small, opt-in subset of Python's ipaddress module: just `IPv4Value`,
# constructed from four `int` octets — deliberately **not** from a
# dotted-quad string (`"192.168.1.1"`): parsing that needs `.split('.')`,
# the same unconfirmed native-string-method gap blocking `re`/`csv`/
# `textwrap` etc.
#
# Also deliberately **not** packed into a single 32-bit `int` the way
# CPython's `IPv4Address` stores it internally: Promethium's `int` maps to
# a *signed* 32-bit `Int32` (see `PROMETHIUM_IMPLEMENTATION_PLAN.md`), and
# a packed IPv4 value only needs 24 more bits to overflow that — any
# address with a first octet ≥ 128 (`192.168.1.1` included) would already
# overflow into a negative number, breaking both its numeric value and its
# ordering under `<`. Storing all four octets separately avoids the
# overflow entirely and keeps comparison correct (lexicographic over
# `a, b, c, d`, matching CPython's actual ordering for IPv4 addresses).


class IPv4Value:
    a: int
    b: int
    c: int
    d: int

    def __init__(self, a: int, b: int, c: int, d: int):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def octet(self, index: int) -> int:
        if index == 0:
            return self.a
        if index == 1:
            return self.b
        if index == 2:
            return self.c
        return self.d

    def __eq__(self, other: IPv4Value) -> bool:
        return self.a == other.a and self.b == other.b and self.c == other.c and self.d == other.d

    def __lt__(self, other: IPv4Value) -> bool:
        if self.a != other.a:
            return self.a < other.a
        if self.b != other.b:
            return self.b < other.b
        if self.c != other.c:
            return self.c < other.c
        return self.d < other.d

    def __le__(self, other: IPv4Value) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def is_loopback(self) -> bool:
        return self.a == 127

    def is_private(self) -> bool:
        if self.a == 10:
            return True
        if self.a == 127:
            return True
        if self.a == 172 and self.b >= 16 and self.b <= 31:
            return True
        if self.a == 192 and self.b == 168:
            return True
        return False

    def is_multicast(self) -> bool:
        return self.a >= 224 and self.a <= 239
