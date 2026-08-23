@namespace("operator")

# A small, opt-in subset of Python's operator module.
#
# Import this module explicitly from Promethium code. It deliberately does not
# alter built-ins or provide target-specific behavior.


def add(left: int, right: int) -> int:
    return left + right


def add(left: float, right: float) -> float:
    return left + right


def sub(left: int, right: int) -> int:
    return left - right


def sub(left: float, right: float) -> float:
    return left - right


def mul(left: int, right: int) -> int:
    return left * right


def mul(left: float, right: float) -> float:
    return left * right


def truediv(left: float, right: float) -> float:
    return left / right


def mod(left: int, right: int) -> int:
    return left % right


def mod(left: float, right: float) -> float:
    return left % right


def neg(value: int) -> int:
    return -value


def neg(value: float) -> float:
    return -value


def pos(value: int) -> int:
    return +value


def pos(value: float) -> float:
    return +value


def eq(left: int, right: int) -> bool:
    return left == right


def eq(left: float, right: float) -> bool:
    return left == right


def eq(left: bool, right: bool) -> bool:
    return left == right


def ne(left: int, right: int) -> bool:
    return left != right


def ne(left: float, right: float) -> bool:
    return left != right


def ne(left: bool, right: bool) -> bool:
    return left != right


def lt(left: int, right: int) -> bool:
    return left < right


def lt(left: float, right: float) -> bool:
    return left < right


def le(left: int, right: int) -> bool:
    return left <= right


def le(left: float, right: float) -> bool:
    return left <= right


def gt(left: int, right: int) -> bool:
    return left > right


def gt(left: float, right: float) -> bool:
    return left > right


def ge(left: int, right: int) -> bool:
    return left >= right


def ge(left: float, right: float) -> bool:
    return left >= right


def not_(value: bool) -> bool:
    return not value
