@namespace("base64")

# A small, opt-in subset of Python's base64 module: `b64encode`/`b64decode`,
# built directly on `RemObjects.Elements.RTL.Convert`'s already-implemented
# `ToBase64String`/`Base64StringToByteArray` — a hand-rolled, no-native-
# crypto-dependency codec that RTL2 ships today. No new algorithm needed
# here at all, the same way `re.py` needed none once RTL2 had a regex
# engine.
#
# Signature deviates from CPython on purpose: CPython's `b64encode(bytes)
# -> bytes` returns the base64 alphabet as ASCII *bytes*, which callers
# almost always immediately `.decode('ascii')` into a `str` anyway — this
# skips that redundant step and returns `str` directly. `b64decode(str) ->
# bytes` takes the equivalent shortcut on input. `bytes` itself is a real
# Promethium v1 language feature (`b'...'` literals, the `bytes` type
# annotation both lower to the target's native `Byte[]`), not something
# this module had to establish.
#
# `RemObjects.Elements.RTL.Convert` is always fully qualified: a bare
# `Convert` risks the same kind of inconsistent per-target resolution
# `time.py` hit with a bare `DateTime` (and `Convert` specifically also
# plausibly collides with the platform's own BCL `System.Convert`, which
# has same-named `ToBase64String`/`FromBase64String` methods of its own).


def b64encode(data: bytes) -> str:
    return RemObjects.Elements.RTL.Convert.ToBase64String(data)


def b64decode(data: str) -> bytes:
    return RemObjects.Elements.RTL.Convert.Base64StringToByteArray(data)
