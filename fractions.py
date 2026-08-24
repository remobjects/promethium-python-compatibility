@namespace("fractions")

from Promethium import ValueError

# A small, opt-in subset of Python's fractions module: just `Fraction`
# itself, always stored in lowest terms with a positive denominator (like
# CPython's), reusing `math.gcd` (fully qualified — bare calls to a
# concrete function from another namespace aren't reliably resolved via
# ambient `DefaultUses`, the same finding `heapq.py`/`statistics.py`
# document).


class Fraction:
    numerator: int
    denominator: int

    def __init__(self, numerator: int, denominator: int):
        if denominator == 0:
            raise ValueError("Fraction(n, 0)")
        sign: int = 1
        if denominator < 0:
            sign = -1
        n: int = numerator * sign
        d: int = denominator * sign
        divisor: int = math.gcd(n, d)
        if divisor == 0:
            divisor = 1
        self.numerator = n / divisor
        self.denominator = d / divisor

    def __init__(self, numerator: int):
        self.numerator = numerator
        self.denominator = 1

    def __add__(self, other: Fraction) -> Fraction:
        return Fraction(self.numerator * other.denominator + other.numerator * self.denominator, self.denominator * other.denominator)

    def __sub__(self, other: Fraction) -> Fraction:
        return Fraction(self.numerator * other.denominator - other.numerator * self.denominator, self.denominator * other.denominator)

    def __mul__(self, other: Fraction) -> Fraction:
        return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)

    def __truediv__(self, other: Fraction) -> Fraction:
        return Fraction(self.numerator * other.denominator, self.denominator * other.numerator)

    def __eq__(self, other: Fraction) -> bool:
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __lt__(self, other: Fraction) -> bool:
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other: Fraction) -> bool:
        return self.numerator * other.denominator <= other.numerator * self.denominator

    def __neg__(self) -> Fraction:
        return Fraction(-self.numerator, self.denominator)

    def __abs__(self) -> Fraction:
        if self.numerator < 0:
            return Fraction(-self.numerator, self.denominator)
        return Fraction(self.numerator, self.denominator)

    def __pow__(self, exponent: int) -> Fraction:
        exp: int = exponent
        negative: bool = False
        if exp < 0:
            negative = True
            exp = -exp
        resultNum: int = 1
        resultDen: int = 1
        index: int = 0
        while index < exp:
            resultNum *= self.numerator
            resultDen *= self.denominator
            index += 1
        if negative:
            return Fraction(resultDen, resultNum)
        return Fraction(resultNum, resultDen)

    def __float__(self) -> float:
        return (self.numerator * 1.0) / self.denominator

    def __str__(self) -> str:
        if self.denominator == 1:
            return "" + self.numerator
        return "" + self.numerator + "/" + self.denominator
