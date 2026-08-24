@namespace("calendar")

from Promethium import List
from datetime import PyDate

# A small, opt-in subset of Python's calendar module, built directly on
# `datetime.PyDate`'s already-verified ordinal/weekday arithmetic rather
# than reimplementing it — `weekday(...)` is a one-line call into `PyDate`.
#
# `month_name`/`day_name` are CPython module-level *subscriptable* lists
# (`calendar.month_name[1]`); here they're parameterized functions instead
# (`month_name(1)`), matching the same convention `string.py` already
# established for its character-class constants (no consumable top-level
# module constant in Promethium — see that module's notes).


def isleap(year: int) -> bool:
    if year % 4 != 0:
        return False
    if year % 100 != 0:
        return True
    return year % 400 == 0


def leapdays(y1: int, y2: int) -> int:
    a: int = y1 - 1
    b: int = y2 - 1
    return (b / 4 - a / 4) - (b / 100 - a / 100) + (b / 400 - a / 400)


def weekday(year: int, month: int, day: int) -> int:
    return PyDate(year, month, day).weekday()


def _daysInMonth(year: int, month: int) -> int:
    if month == 2:
        if isleap(year):
            return 29
        return 28
    if month == 4 or month == 6 or month == 9 or month == 11:
        return 30
    return 31


def monthrange(year: int, month: int) -> tuple[int, int]:
    return (weekday(year, month, 1), _daysInMonth(year, month))


def month_name(index: int) -> str:
    names: List[str] = List[str]()
    names.append("")
    names.append("January")
    names.append("February")
    names.append("March")
    names.append("April")
    names.append("May")
    names.append("June")
    names.append("July")
    names.append("August")
    names.append("September")
    names.append("October")
    names.append("November")
    names.append("December")
    return names.__getitem__(index)


def day_name(index: int) -> str:
    names: List[str] = List[str]()
    names.append("Monday")
    names.append("Tuesday")
    names.append("Wednesday")
    names.append("Thursday")
    names.append("Friday")
    names.append("Saturday")
    names.append("Sunday")
    return names.__getitem__(index)
