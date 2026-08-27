@namespace("datetime")

# A small, opt-in subset of Python's datetime module: mostly date
# arithmetic (`PyDate`/`PyTimeDelta`), not wall-clock time. Proleptic-
# Gregorian day arithmetic (the same algorithm CPython's own pure-Python
# reference implementation uses) is pure integer math — no native call
# needed for any of this. `now()`/full wall-clock time-of-day were
# originally NOT attempted, deferred pending the native-call research
# `time.py` has since done — `today()` (just the date, UTC) is now
# implemented on top of that, reusing `RemObjects.Elements.RTL.DateTime`'s
# `UtcNow`/`Year`/`Month`/`Day` the same way `time.py`'s `time()` reuses
# its `ToUnixTimeSeconds()`. Still no `now()` (date *and* time together)
# — that needs an hour/minute/second-carrying type this module doesn't
# have yet, a further scope cut, not an oversight.
#
# Not named `Date`/`DateTime`/`TimeDelta`: `Date`/`DateTime` collide with
# native BCL/platform types by the same mechanism `random.py`'s `Random`
# and `decimal.py`'s `Decimal` already confirmed breaks Toffee builds.
# `PyDate`/`PyTimeDelta` sidestep it preemptively. There's also no
# `@classmethod` (no decorators in this language slice), so CPython's
# `date.fromordinal(...)` becomes the module-level function
# `dateFromOrdinal(...)` instead of an alternate constructor.
#
# Every value is stored and compared through a single day-ordinal (day 1 =
# January 1, year 1, matching CPython's own `date.toordinal()` convention
# exactly, including `weekday()`'s Monday=0 result), so `__add__`/`__sub__`/
# comparisons are all just integer arithmetic on that ordinal — dunders are
# explicit-call-only, as everywhere else in this project.


def _isLeap(year: int) -> bool:
    if year % 4 != 0:
        return False
    if year % 100 != 0:
        return True
    return year % 400 == 0


def _daysInMonth(year: int, month: int) -> int:
    if month == 2:
        if _isLeap(year):
            return 29
        return 28
    if month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    return 31


def _daysBeforeMonth(year: int, month: int) -> int:
    total: int = 0
    m: int = 1
    while m < month:
        total += _daysInMonth(year, m)
        m += 1
    return total


def _daysBeforeYear(year: int) -> int:
    y: int = year - 1
    return y * 365 + y / 4 - y / 100 + y / 400


def _ymdToOrdinal(year: int, month: int, day: int) -> int:
    return _daysBeforeYear(year) + _daysBeforeMonth(year, month) + day


def _ordinalToYmd(ordinal: int) -> tuple[int, int, int]:
    year: int = 1
    remaining: int = ordinal
    while True:
        daysInYear: int = 365
        if _isLeap(year):
            daysInYear = 366
        if remaining <= daysInYear:
            break
        remaining -= daysInYear
        year += 1
    month: int = 1
    while True:
        dim: int = _daysInMonth(year, month)
        if remaining <= dim:
            break
        remaining -= dim
        month += 1
    return (year, month, remaining)


class PyTimeDelta:
    days: int

    def __init__(self, days: int):
        self.days = days

    def __add__(self, other: PyTimeDelta) -> PyTimeDelta:
        return PyTimeDelta(self.days + other.days)

    def __sub__(self, other: PyTimeDelta) -> PyTimeDelta:
        return PyTimeDelta(self.days - other.days)

    def __neg__(self) -> PyTimeDelta:
        return PyTimeDelta(-self.days)

    def __eq__(self, other: PyTimeDelta) -> bool:
        return self.days == other.days

    def __lt__(self, other: PyTimeDelta) -> bool:
        return self.days < other.days

    def __le__(self, other: PyTimeDelta) -> bool:
        return self.days <= other.days


class PyDate:
    year: int
    month: int
    day: int

    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day

    def toordinal(self) -> int:
        return _ymdToOrdinal(self.year, self.month, self.day)

    def weekday(self) -> int:
        return (self.toordinal() - 1) % 7

    def isoweekday(self) -> int:
        return self.weekday() + 1

    def __add__(self, delta: PyTimeDelta) -> PyDate:
        return dateFromOrdinal(self.toordinal() + delta.days)

    def __sub__(self, delta: PyTimeDelta) -> PyDate:
        return dateFromOrdinal(self.toordinal() - delta.days)

    def __sub__(self, other: PyDate) -> PyTimeDelta:
        return PyTimeDelta(self.toordinal() - other.toordinal())

    def __eq__(self, other: PyDate) -> bool:
        return self.toordinal() == other.toordinal()

    def __lt__(self, other: PyDate) -> bool:
        return self.toordinal() < other.toordinal()

    def __le__(self, other: PyDate) -> bool:
        return self.toordinal() <= other.toordinal()


def dateFromOrdinal(ordinal: int) -> PyDate:
    parts: tuple[int, int, int] = _ordinalToYmd(ordinal)
    return PyDate(parts[0], parts[1], parts[2])


def today() -> PyDate:
    now: RemObjects.Elements.RTL.DateTime = RemObjects.Elements.RTL.DateTime.UtcNow
    return PyDate(now.Year, now.Month, now.Day)
