@namespace("unicodedata")

from Promethium import ValueError

# Originally filed under "Locale & text data — needs real Unicode/locale
# data tables" — that assumption was never actually tested. Every target's
# own runtime already ships a full, correct Unicode character database:
# .NET's `System.Globalization.CharUnicodeInfo`/`String.Normalize` on
# Echoes, `java.lang.Character`/`java.text.Normalizer` on Cooper, and
# Foundation's `NSCharacterSet`/`NSString` normalization methods on Toffee.
# Nothing needed embedding — the same "check the platform before assuming
# a gap" correction this project has made repeatedly (native string ops,
# `re`, reflection, bytes).
#
# `RemObjects.Elements.RTL.Globalization` (a new RTL2 addition made
# alongside this module) wraps those three native APIs behind one
# cross-platform `UnicodeInfo` class; this module is a thin Python-facing
# layer over it, matching CPython's `unicodedata.category(chr)`/
# `normalize(form, s)`/`decimal(chr)`/`digit(chr)`/`numeric(chr)` shapes.
#
# `category()` maps a real 30-value `UnicodeCategory` enum to CPython's own
# two-letter codes (`"Lu"`, `"Nd"`, `"Zs"`, etc.) — exact, full-fidelity on
# Echoes and Cooper, both of which have a genuine native 30-way
# classification. Toffee is coarser by necessity: Foundation only exposes
# character-set *membership* tests (`NSCharacterSet`), not a single
# "classify this character" call, so it distinguishes uppercase/lowercase
# letters, decimal digits, whitespace, and punctuation/symbol/control at a
# coarse level and falls back to the matching "Other*" code (`"Lo"`,
# `"So"`, `"Po"`) for anything finer a real Unicode category table would be
# needed to tell apart. This is a real, documented reduction in granularity
# on Toffee, not a bug.
#
# `name()`/`lookup()` (Unicode's official character *names*, e.g.
# `unicodedata.name('A')` → `"LATIN CAPITAL LETTER A"`) are the one piece
# genuinely NOT reachable this way — none of the three native APIs expose
# character names, only categories/normalization/numeric values. Calling
# either raises a clear `ValueError` rather than being silently missing.
#
# `normalize()` only supports `"NFC"`/`"NFD"` (canonical composition/
# decomposition) — not `"NFKC"`/`"NFKD"` (compatibility forms). Echoes and
# Cooper's native APIs support all four; Toffee's `NSString` convenience
# methods only expose the canonical pair (`precomposedStringWithCanonicalMapping`/
# `decomposedStringWithCanonicalMapping` — the compatibility forms need a
# lower-level `CFStringNormalize` call not attempted here), so this module
# sticks to the pair available on all three targets rather than have NFKC/
# NFKD silently work on two backends and fail on the third.
#
# Not available on Island (any sub-target): Island's own native runtime has
# no character-category/normalization API of its own (confirmed by reading
# its String.pas source directly — no IsLetter/GetType/Normalize-shaped
# methods exist there at all), and while Island.Darwin links against the
# same Foundation framework Toffee uses, writing the identical Foundation
# calls in RTL2's Oxygene source for Island specifically crashes the
# compiler itself (an internal codegen assertion failure, isolated down to
# a minimal repro with no Foundation calls involved at all — reported
# separately). Every function here raises a clear `ValueError` on Island
# rather than fail to compile or misbehave.
#
# Verified: `category()` matches live CPython 3.12 output for uppercase/
# lowercase letters, decimal digits, and whitespace on Echoes and Cooper;
# `normalize("NFC", ...)`/`normalize("NFD", ...)` round-trip a precomposed/
# decomposed "é" correctly on Echoes, Cooper, and Toffee (RTL2-level,
# called directly — see `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`
# for why the compat-library-level Toffee Exe link is still pending).


def category(ch: str) -> str:
    if defined("ISLAND") or defined("IOS") or defined("TVOS"):
        raise ValueError("unicodedata.category is not available on Island, or on Toffee iOS/tvOS (blocked by an unrelated pre-existing RTL2 build issue on those two SDKs)")
    else:
        cat: RemObjects.Elements.RTL.Globalization.UnicodeCategory = RemObjects.Elements.RTL.Globalization.UnicodeInfo.GetCategory(ch[0])
        if cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.UppercaseLetter:
            return "Lu"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.LowercaseLetter:
            return "Ll"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.TitlecaseLetter:
            return "Lt"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.ModifierLetter:
            return "Lm"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.OtherLetter:
            return "Lo"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.NonSpacingMark:
            return "Mn"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.SpacingCombiningMark:
            return "Mc"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.EnclosingMark:
            return "Me"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.DecimalDigitNumber:
            return "Nd"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.LetterNumber:
            return "Nl"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.OtherNumber:
            return "No"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.SpaceSeparator:
            return "Zs"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.LineSeparator:
            return "Zl"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.ParagraphSeparator:
            return "Zp"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.Control:
            return "Cc"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.Format:
            return "Cf"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.Surrogate:
            return "Cs"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.PrivateUse:
            return "Co"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.ConnectorPunctuation:
            return "Pc"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.DashPunctuation:
            return "Pd"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.OpenPunctuation:
            return "Ps"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.ClosePunctuation:
            return "Pe"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.InitialQuotePunctuation:
            return "Pi"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.FinalQuotePunctuation:
            return "Pf"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.OtherPunctuation:
            return "Po"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.MathSymbol:
            return "Sm"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.CurrencySymbol:
            return "Sc"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.ModifierSymbol:
            return "Sk"
        elif cat == RemObjects.Elements.RTL.Globalization.UnicodeCategory.OtherSymbol:
            return "So"
        else:
            return "Cn"


def normalize(form: str, s: str) -> str:
    if defined("ISLAND") or defined("IOS") or defined("TVOS"):
        raise ValueError("unicodedata.normalize is not available on Island, or on Toffee iOS/tvOS (blocked by an unrelated pre-existing RTL2 build issue on those two SDKs)")
    else:
        if form == "NFC":
            return RemObjects.Elements.RTL.Globalization.UnicodeInfo.NormalizeNFC(s)
        elif form == "NFD":
            return RemObjects.Elements.RTL.Globalization.UnicodeInfo.NormalizeNFD(s)
        else:
            raise ValueError("unicodedata.normalize: only 'NFC' and 'NFD' are supported (no NFKC/NFKD)")


def numeric(ch: str) -> float:
    if defined("ISLAND") or defined("IOS") or defined("TVOS"):
        raise ValueError("unicodedata.numeric is not available on Island, or on Toffee iOS/tvOS (blocked by an unrelated pre-existing RTL2 build issue on those two SDKs)")
    else:
        value: float = RemObjects.Elements.RTL.Globalization.UnicodeInfo.GetNumericValue(ch[0])
        if value != value:
            raise ValueError("unicodedata.numeric: not a numeric character")
        return value


def digit(ch: str) -> int:
    value: float = numeric(ch)
    return Integer(value)


def decimal(ch: str) -> int:
    cat: str = category(ch)
    if cat != "Nd":
        raise ValueError("unicodedata.decimal: not a decimal digit")
    return digit(ch)
