@namespace("html")

# A small, opt-in subset of Python's html module: `escape`/`unescape` for
# the five entities CPython's own `html.escape` produces (`&amp;`, `&lt;`,
# `&gt;`, `&quot;`, `&#x27;`) plus `unescape`'s common aliases for the
# apostrophe (`&#39;`, `&apos;`) — not the full HTML5 named-character-
# reference table (2000+ entries) or numeric character references
# (`&#NNN;`/`&#xHHH;` for arbitrary code points), which would need an
# int-codepoint-to-`str` conversion this codebase has never established
# (a different question from the confirmed `int`→`str` *decimal* text
# conversion `"" + value` gives — see `string.py`'s notes).
#
# Built on the already-confirmed per-target `.Replace`/`.replace`/
# `.stringByReplacingOccurrencesOfString` (see `string.py`'s notes) — all
# three replace *every* occurrence by default, so no manual loop is
# needed. Order matters: `escape` replaces `&` first (so the `&` it
# introduces via `&lt;`/`&gt;`/etc. isn't re-escaped); `unescape` replaces
# `&amp;` last (so `&amp;lt;` — an already-escaped literal `&lt;` — comes
# back as `&lt;` text, not `<`).


def _replace(value: str, oldValue: str, newValue: str) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return value.Replace(oldValue, newValue)
    elif defined("COOPER"):
        return value.replace(oldValue, newValue)
    else:
        return value.stringByReplacingOccurrencesOfString(oldValue, withString=newValue)


def escape(value: str) -> str:
    result: str = value
    result = _replace(result, "&", "&amp;")
    result = _replace(result, "<", "&lt;")
    result = _replace(result, ">", "&gt;")
    result = _replace(result, "\"", "&quot;")
    result = _replace(result, "'", "&#x27;")
    return result


def unescape(value: str) -> str:
    result: str = value
    result = _replace(result, "&quot;", "\"")
    result = _replace(result, "&#x27;", "'")
    result = _replace(result, "&#39;", "'")
    result = _replace(result, "&apos;", "'")
    result = _replace(result, "&lt;", "<")
    result = _replace(result, "&gt;", ">")
    result = _replace(result, "&amp;", "&")
    return result
