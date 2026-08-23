@namespace("math")

# The module namespace is intentionally explicit: consumers import `math`
# instead of the project's implementation namespace.


def fabs(value: float) -> float:
    if value == 0.0:
        return 0.0
    if value < 0.0:
        return -value
    return value


def isnan(value: float) -> bool:
    return value != value
