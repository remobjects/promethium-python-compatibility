@namespace("locale")

from Promethium import ValueError

# Same correction as `unicodedata`'s: assumed blocked because it needs
# "real locale data tables," never actually tested. Every target's own
# runtime already ships full locale-aware number/currency formatting and
# collation, built on top of `RemObjects.Elements.RTL.Culture`
# (a new RTL2 addition made alongside this module): `System.Globalization.
# CultureInfo` on Echoes, `java.util.Locale`/`NumberFormat`/
# `DecimalFormatSymbols`/`Collator` on Cooper, `NSLocale`/`NSNumberFormatter`
# on Toffee.
#
# API deviates from CPython's `locale.setlocale`/global-state model on
# purpose: CPython's `locale` module mutates process-wide global state
# (`setlocale`) that every subsequent `locale.format_string`/`strcoll`
# call implicitly reads — there's no clean equivalent to "the current
# process locale" here, and a mutable global wouldn't be thread-safe
# across this project's targets anyway. `LocaleInfo(name)` is an explicit,
# instantiable object instead (`LocaleInfo("de-DE")`), matching this
# project's established "concrete object over ambient global state"
# choices elsewhere (`random.RandomGenerator` over CPython's global
# `random.seed`, noted in that module's own README section). Named
# `LocaleInfo`, not `Locale` — RTL2 already has its own `Locale` class
# (`Locale.pas`, timezone/locale plumbing unrelated to this), and a
# same-name class in this project's namespace hit the identical "duplicate
# short name" build error `Random`/`Decimal`/`XmlElement` already ran into
# elsewhere in this project.
#
# `LocaleInfo` stores only the locale name (a plain `str`) and builds a
# fresh `RemObjects.Elements.RTL.Culture` inside each method
# rather than caching one in a typed field — deliberately, not for
# performance: a class-level field typed as the RTL2 `Culture` class would
# reference that type *unconditionally*, breaking compilation on any
# target whose reference doesn't have it yet (Island always; occasionally
# a Toffee sub-target too, if its own RTL2 build is stale for unrelated
# reasons — this project depends on whichever `Elements` reference the
# consuming project resolves, and can't control how current every target's
# copy is). Keeping the RTL2 type reference confined inside each already-
# `if defined("ISLAND")`-guarded method body avoids that entirely.
#
# `decimal_point()`/`thousands_sep()` cover CPython's `localeconv()`
# dict's two most commonly used keys; the rest of `localeconv()`'s ~14
# fields (currency formatting grouping rules, positive/negative sign
# placement, etc.) aren't exposed individually — `format_currency()`
# below covers the actual currency-formatting use case directly instead,
# rather than exposing raw formatting *rules* for a caller to apply by
# hand.
#
# Not available on Island (any sub-target) — same two reasons as
# `unicodedata`: Island's own runtime has no locale API of its own, and
# Island.Darwin's Foundation-based path (identical code to Toffee's, which
# works) crashes the compiler itself when compiled for Island specifically
# (see `unicodedata.py`'s header and
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`).
#
# Verified: `LocaleInfo("de-DE").format_number(1234567.89, 2)` →
# `"1.234.567,89"`, `.decimal_point()` → `","`, `.thousands_sep()` →
# `"."`, `.format_currency(1234567.89)` → `"1.234.567,89 €"` — matching
# Java's/.NET's own locale data exactly, on both Echoes and Cooper;
# `LocaleInfo("en-US").strcoll("apple", "Banana")` → `-1`
# (case-insensitive, alphabetically first) on both.


class LocaleInfo:
    _name: str

    def __init__(self, name: str):
        self._name = name

    def decimal_point(self) -> str:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.DecimalSeparator

    def thousands_sep(self) -> str:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.GroupSeparator

    def format_number(self, value: float, fraction_digits: int) -> str:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.FormatNumber(value, fraction_digits)

    def format_currency(self, value: float) -> str:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.FormatCurrency(value)

    def strcoll(self, a: str, b: str) -> int:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.Compare(a, b, False)

    def strcoll_ignorecase(self, a: str, b: str) -> int:
        if defined("ISLAND"):
            raise ValueError("locale.LocaleInfo is not available on Island")
        else:
            culture: RemObjects.Elements.RTL.Culture = RemObjects.Elements.RTL.Culture(self._name)
            return culture.Compare(a, b, True)
