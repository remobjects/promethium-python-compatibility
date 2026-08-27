# Promethium Python Compatibility

This library provides optional, source-level compatibility modules for
Promethium projects that are being ported from Python. Nothing is enabled by
default: a project opts in by referencing this library and importing the
required module.

## `math`

Declares `@namespace("math")`, so consumers use the normal Python-shaped
`import math` spelling rather than the project implementation namespace —
though as with `heapq`/`bisect` below, `from math import sqrt` doesn't
actually work (function imports only bind types in Promethium); add `math`
to the consuming project's `DefaultUses` and call functions bare instead,
or call fully qualified as `math.sqrt(...)`.

Where a function can be implemented with pure Promethium arithmetic, it is,
with no native call and no per-target branching at all: `fabs`, `isnan`
(the two original functions), plus `isinf`, `isfinite`, `copysign`, `fmod`
(just Promethium's own `%` operator — already confirmed working for floats
by `operator.py`'s `mod`), `degrees`, `radians`, `gcd`, `factorial`.
`isinf`/`isfinite` are themselves built from `isnan` with the same kind of
NaN-arithmetic trick as the original `isnan` (`inf - inf` is NaN; nothing
else subtracted from itself is), rather than a native
`Double.IsInfinity`-equivalent per target.

Everything else — roots, logs, trig, powers — genuinely needs a native
call, since each of the four backends spells its math library differently.
Confirmed working (compiled clean across all fifteen targets and
runtime-verified against CPython's own output on Echoes): `sqrt`, `hypot`
(built from `sqrt`), `pow`, `exp`, `log`, `log2`, `log10`, `floor`, `ceil`,
`trunc`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`. Each branches
on `defined("ECHOES"|"ISLAND"|"COOPER")` to call, respectively,
`System.Math.*`, `RemObjects.Elements.System.Math.*`, or bare `Math.*`
(java.lang.Math, lowercase methods, no import needed) — the same
fully-qualified-native-call pattern `PromethiumBaseLibrary`'s own
`Builtins.py` already uses for `print`
(`RemObjects.Elements.System.writeLn(value)`). Toffee uses `rtl.*`
(`rtl.sqrt`, `rtl.floor`, etc.) rather than the bare global C functions of
the same name (`sqrt(...)` also exists in Toffee mode) — calling a bare
`sqrt(...)` from *inside this module's own function named `sqrt`* would
recurse into itself instead of reaching the C library. `log2` has no
`System.Math.Log2` pre-.NET 6 and no confirmed `rtl`/Cooper equivalent, so
Echoes/Cooper/Toffee all compute it as `log(value) / log(2.0)`; only Island
has a native `Log2`. `trunc` has no direct Cooper equivalent either, so it
branches to `Math.ceil`/`Math.floor` there based on the value's sign.

`int(...)`/`float(...)` casts are avoided entirely — there's no
confirmed-working cast syntax in this codebase yet, so every function
above either returns a native call's `float` result directly or stays in
`int` arithmetic throughout (`gcd`, `factorial`, and the additions below).

Also added, all pure `int`/`float` arithmetic with no native call:
`comb(n, k)`, `perm(n, k)` (the standard incremental-multiply/divide
identities, exact at every step — no intermediate rounding), `prod`
(`int`/`float` overloads, like `sum`), `dist(p, q)` (2D points only, via
`sqrt`), and `isqrt(n)` — integer square root via pure-integer Newton's
method (no float involved at all, sidestepping the float→int cast
question entirely rather than computing `floor(sqrt(float(n)))` and
needing to cast the result back).

## `operator`

A target-neutral subset of Python's `operator` API: integer and
floating-point arithmetic, primitive ordering comparisons, integer/float/
boolean equality, boolean negation/truth, `abs`, bitwise ops (`and_`, `or_`,
`xor`, `invert`, `lshift`, `rshift`), floor division, and a handful of
sequence operations over `Promethium.List` (`getitem`, `setitem`, `concat`,
`contains`, `countOf`, `indexOf`). Runtime-verified against CPython's own
`operator` module output for every function.

`floordiv` hand-rolls CPython's floor-toward-negative-infinity semantics
(`/` and `%` are assumed to truncate toward zero, like C/C#/Java, since
Promethium's `//` operator is unconfirmed to exist or match CPython's
rounding) — verified correct for both-positive, both-negative, and
mixed-sign operands.

`contains`/`countOf` are built on `List.count()` rather than `List.index()`
deliberately: Toffee's `indexOfObject:` returns Cocoa's `NSNotFound`
sentinel (not `-1`) when an item is missing, so a portable "not found"
check can't just test `index() >= 0`. `indexOf` instead does its own linear
scan with `.Equals`/`.isEqual` — the same technique `collections`' classes
already use for their own lookups (see `Counter.py`'s `_index_of`) — and
raises `ValueError` on a miss, matching CPython's `list.index()`.
`setitem` is a thin wrapper over `List.__setitem__` — see the note on
`List`'s bracket-write indexer below.

## `collections`

One class per file (`Counter.py`, `OrderedDict.py`, `ChainMap.py`,
`Deque.py`, `DefaultDict.py`), each declaring `@namespace("collections")` so
`from collections import X` works for each. All are plain Promethium classes
(not `@mapped`) backed by `Promethium.List`/`Dictionary`, so they need a
reference to `PromethiumBaseLibrary` in addition to this project.

Bracket syntax (`x[key]`, `x[key] = value`) works correctly for all of
these — `__getitem__`/`__setitem__` lower to a real indexer, including
compound assignment (`counts[key] += 1`) and auto-vivify-on-read
(`DefaultDict`). This required a compiler fix for `@mapped` types (see
`Counter`'s note below); it was already working for plain classes before
that fix. One real limit remains: bracket syntax does **not** dispatch
through a *subclass's* override of `__getitem__`/`__setitem__` — confirmed
with an isolated repro (a subclass overriding `__setitem__` to count writes
never saw its override invoked via `sub[i] = v`, only the base class's
version ran). That's why `UserDict`/`UserList`/`UserString` are still not
attempted; see below. Same-class dispatch (a method calling `self[key]` on
its own class) works fine and is used throughout.

Two other Python operators needed the same kind of treatment as the
indexer, and only one of them has it so far:

- **`in`** now works (`key in counts`) — every class here defines a native
  `Contains(...)` method (not just Python's `__contains__`) because the `in`
  operator lowers to a call to a member literally named `Contains`, not to
  `__contains__`. Both are kept: `Contains` for the operator, `__contains__`
  for explicit/Python-style calls and internal use.
- **`len()`** now works too (`len(counts)`) — not because `len` gained
  special dunder support, but because `LenOverloads.py` declares more
  overloads of the *ordinary* `len` function under `@namespace("Promethium")`
  (not `"collections"`), which extends the same overload set
  `PromethiumBaseLibrary`'s own `Builtins.py` declares its `List`/
  `Dictionary`/`Set`/`str` overloads under. Overload resolution combines
  same-named functions across assemblies within one open namespace, so this
  needed no compiler change at all — just declaring `len` again, elsewhere,
  in the right namespace. `.__len__()` still works directly too.
- **`+`/`-`/`&`/`|`** do *not* route to `__add__`/`__sub__`/`__and__`/
  `__or__` — confirmed by testing `a + b` on two `Counter`s, which fails to
  compile even though `__add__` is defined and callable explicitly
  (`a.__add__(b)`). Unlike `in`, there's no known native-operator name to
  define instead (nothing like `Contains` for `in`) — this would need
  either compiler support for lowering these operators to the dunders (like
  the indexer got) or a discovered convention this session didn't find.
  `Counter.__add__`/`__sub__`/`__and__`/`__or__` are implemented and correct
  (verified), just not reachable via `+`/`-`/`&`/`|` syntax yet.
- **`for x in counter:`** does not work at all yet — direct iteration needs
  `GetEnumerator`/`IEnumerable` (or the equivalent per target), not Python's
  `__iter__`; none of the classes here implement it. This fails at compile
  time with a clear message, not a runtime surprise. `for x in
  counter.keys():` works today since `.keys()` returns a real `List`, which
  is already enumerable.

### `Counter`

A multiset. Backed by a single `List` of `(key, count)` tuples, not a
`Dictionary`. Two independent `Dictionary` issues motivated this, both still
present: `Dictionary.update(Dictionary)` itself throws at runtime
(`OxygeneBinderException: No methods called "get"`) because its `values:
Dictionary[Key, Value]` parameter is a generic class referencing its own
enclosing type — the same generic-self-reference limitation noted below, but
here it compiles and fails at runtime instead of failing to compile, because
`Dictionary` is `@mapped` and falls back to dynamic dispatch against the
erased native dictionary; and — separately — a bracket-syntax indexer on a
`@mapped` class like `Dictionary` itself did not work until a compiler fix
landed for exactly that combination (`@mapped` classes couldn't declare
`__getitem__`/`__setitem__` as indexers at all, confirmed with a minimal
isolated repro independent of generics). `Counter` sidesteps both by using
only `List`'s already-proven `append`/`pop(index)`/`insert(index, value)`/
`__getitem__`, doing a linear scan for lookups (fine for the small/moderate
key counts `Counter` is meant for) and using `.Equals(...)` rather than `==`
for key comparison (an unconstrained generic `T` has no known `==` operator
at compile time, but every type has `Equals` — except under Toffee, where
generics erase to Objective-C `id`, which has no `Equals` either, so key
comparison branches on `defined("TOFFEE")` to use `.isEqual(...)` there
instead). Key order for tied counts is therefore just list order —
first-insertion order, matching CPython's dict/Counter guarantee — with no
separate ordering structure needed. The same `List`-of-tuples design, and the
same `.Equals`/`.isEqual` branch, is reused in `OrderedDict`, `DefaultDict`,
and (via a shared `_list_contains` helper) `ChainMap`/`Deque`.

Supported: construction from an iterable (`Counter[str](words)`) or from
another `Counter` (`Counter[str](other)`); `get`, `keys`, `items`;
`update`/`subtract` from an iterable or another `Counter`; `most_common()` /
`most_common(n)`; `elements()`; `total()`; `pop`; `clear`; `copy()`;
`__add__`/`__sub__`/`__and__`/`__or__` (CPython semantics: `+`/`-` keep only
positive resulting counts, `&`/`|` are min/max — reachable today only via
explicit calls like `a.__add__(b)`, not `a + b`; see the operator note
above). Missing-key lookups return `0` instead of raising, matching CPython.

### `OrderedDict`

A mapping that remembers insertion order — same `List`-of-`(key, value)`-
tuples design as `Counter`, which gets ordering for free with no separate
bookkeeping. Supported: construction from an iterable of pairs; `get`,
`keys`, `values`, `items`; `pop`; `popitem(last=True)`;
`move_to_end(key, last=True)`; `clear`; `copy()`.

### `ChainMap`

Groups several `Dictionary` mappings and searches them in order, first match
wins. Unlike `Counter`/`OrderedDict`, this one does wrap `Dictionary`
directly — but only ever calls `get`/`__contains__`/`keys` on the wrapped
mappings, never `update`, so it never hits the `Dictionary.update` bug above.
Supported: construction from a `List` of `Dictionary` mappings (most-local
first); `maps()`; `get`, `keys`; `__getitem__` raises `KeyError` on a
completely missing key, matching CPython; `clear()` clears only the first
(most-local) map, also matching CPython; `new_child(m=None)`/`parents()`.

`__setitem__` (CPython writes a missing key to `self.maps[0]`) is **not**
implemented, and can't be with `Dictionary` as it stands today: `Dictionary`
declares neither `__getitem__` nor `__setitem__` itself, so it has no
indexer property to write through even now that the `@mapped`-indexer bug
is fixed — that fix only helps a class that declares the methods itself.
There's still no working way to set a single key on a `Dictionary` from
outside its own file (no external bracket write, and
`Dictionary.update(Dictionary)` throws at runtime — see `Counter`'s note
above). Fixing this would mean adding `__getitem__`/`__setitem__` to
`Dictionary` in `PromethiumBaseLibrary` itself.

### `Deque`

Backed by a single `List`. `append`/`pop` at the list's own end are List's
normal operations; `appendleft`/`popleft`/`extendleft` use `insert(0, ...)`/
`pop(0)`, which are O(n) — a real deque needs its own ring-buffer/native
structure for O(1) at both ends, which is future work. This is correct, not
fast. Supported: `append`/`appendleft`/`pop`/`popleft`/`extend`/`extendleft`/
`clear`/`count`/`rotate(n)`/`copy()`/`__contains__` (and `Contains`, for
`in`); `maxlen` (a public field, read directly as `dq.maxlen` — bounded
construction via `Deque[T](maxlen)` or `Deque[T](values, maxlen)`, `-1`
meaning unbounded, the same concrete stand-in for CPython's `None` this
project uses elsewhere for a `hi`/`default`-style parameter, e.g.
`bisect.py`'s `hi`). `append`/`appendleft` each evict from the *opposite*
end once `maxlen` is exceeded, matching CPython's per-append eviction
exactly rather than a single bulk trim; `extend`/`extendleft` loop over
`append`/`appendleft` so they inherit the same behavior automatically.
Runtime-verified character-for-character against CPython's own `deque`
output for both eviction directions and for bounded construction from an
existing list.

### Generic self-reference: fixed

Promethium used to be unable to resolve a generic class's own name
(parameterized or bare) from within its own body at all, which blocked
`Counter`-to-`Counter` ops, `OrderedDict.copy()`, `Deque.copy()`, and
`ChainMap.new_child()`/`.parents()` — any method taking or returning an
instance of its own generic class. That's fixed now (verified with an
isolated repro — a generic class calling and returning its own type from
two different methods, both compiling and running correctly — before
relying on it in the classes above), so all of those are implemented.

### Deliberately not attempted: `namedtuple`, `UserDict`/`UserList`/`UserString`

`namedtuple` dynamically creates a *new type* at runtime from its arguments
(`namedtuple('Point', ['x', 'y'])`); Promethium is statically compiled and
has no runtime type-generation facility to hook into. This isn't a
workaround-able bug like the ones above — it's a different language feature
entirely. (The original design note already called this: better expressed
by native tuples, records, or a future Promethium data-class feature.)

`UserDict`/`UserList`/`UserString` exist in Python so that *your subclass*
can override `__setitem__`/etc. and have `x[i] = y` pick it up. Confirmed
with an isolated repro that this still doesn't work: a subclass overriding
`__setitem__` to count writes never had its override invoked via bracket
assignment on a subclass instance — only the base class's indexer ran (see
the note in the intro above). A `UserList` subclass would compile but
silently not behave like Python's — which is worse than not shipping it.

### `DefaultDict`

Backed by the same `List`-of-tuples design as `Counter`/`OrderedDict`, plus
a stored zero-argument factory invoked on a missing key
(`DefaultDict[str, List[int]](lambda: List[int]())`, matching Python's
`defaultdict(list)`). The factory is stored as a plain, implicitly-typed
field from an untyped constructor parameter (`self._factory = factory`, no
type annotation — an annotated field declaration does not work here, only
a bare `self.x = value` assignment infers one) and invoked with `.Invoke()`.
Verified: each key gets its own independent instance from the factory (two
different keys' `List[int]()` values don't alias each other), and compound
assignment through the indexer works (`dd["missing"] += 1` auto-vivifies via
`__getitem__`, then writes back via `__setitem__`).

This compiles for every target, including Toffee, but does not work on
Toffee at runtime: there, the factory value erases to a dynamic Objective-C
`id`, and invoking it dynamically returns void with no way to recover a
typed result (confirmed: `self._factory.invoke()` compiles but its result
can't be assigned to `Value`, and there's no accessible cast from `id` to a
generic `Value` either). This is unrelated to the `@mapped`-indexer issue
above — it's about dynamic block invocation losing static return-type
information, not about indexers. Rather than exclude `DefaultDict.py` from
Toffee at the project-file level (source files here are compiled for every
target uniformly — see Build notes below), the limitation is handled inside
`__getitem__` itself: on `defined("TOFFEE")`, a missing key raises a clear
`ValueError` explaining the factory can't be invoked there, instead of
silently misbehaving; every other target takes the normal auto-vivify path
in the `else` branch.

## `bytearray`

`PyByteArray` (in `Promethium`, alongside `bytes` itself, not under any
module namespace — a builtin in CPython too — named `Py`-prefixed on the
same established Cocoa/Toffee short-name-collision precedent as
`PyQueue`/`PyDate`, not a confirmed collision). A mutable, growable byte
sequence, unlike Promethium's own `bytes` (a fixed-size native `Byte[]`
with no `+` operator and no `bytes(n)` zero-fill constructor — see
`struct.py`'s notes). Indexed access/mutation (`__getitem__`/
`__setitem__`, `append`/`extend`/`pop`/`clear`/`copy`) is backed by a
plain `List[int]`, the same substrate `Deque`/`Counter`/etc. use; `len()`
works via the same `LenOverloads.py` overload-set mechanism they use too.

`to_bytes()` — converting the list back into a real `bytes` value of its
exact runtime length — used to be the genuinely-impossible part: the only
previously-confirmed way to build a `bytes` value was a compile-time-
sized literal (`struct.py`'s "declare a same-length literal, then assign
into its indices" idiom), which can't work when the length isn't known
until runtime. **This is now solved**: `RemObjects.Elements.RTL.Binary` —
found while looking for a `bytearray` substrate, not previously exercised
in this project — is a genuine cross-platform *growable* byte buffer
(backed per-target by `MemoryStream`/`NSMutableData`/
`ByteArrayOutputStream`): `Binary()` starts empty, `.Write(someBytes)`
appends, `.ToArray()` hands back a `bytes`-compatible native array sized
to exactly what was written. Confirmed with a standalone probe before
building `PyByteArray` on it — three separate `.Write()` calls followed
by `.ToArray()` round-tripped the right bytes in the right order, and
`.Length` matched the real accumulated count. This corrects `struct.py`'s
and `hashlib.py`'s "no dynamically-sized `bytes` allocation exists" note
— dynamic allocation exists, it just isn't a `bytes`-literal-shaped API;
worth reaching for on any future module that needs to build a
variable-length `bytes` result (a `zlib`/compression output buffer, for
instance).

`to_bytes()` writes one byte at a time (O(n) native `Write` calls) rather
than batching contiguous runs into fewer calls — correct, not fast,
matching `Deque`'s own documented "O(n) appendleft, real ring-buffer is
future work" trade-off.

Runtime-verified against CPython's own `bytearray` for every operation
above (`append`, indexed read/write, `extend`, `pop`, `len`, the
`bytearray(n)` zero-fill constructor, `bytearray(existing_bytes)`, and
`copy()`'s independence from the original) — every result matched
exactly.

## `itertools`

An eager subset of Python's `itertools`: every function returns a
fully-materialized `List` instead of a lazy iterator, the same choice
`PromethiumBaseLibrary`'s own `range()` already makes (Promethium generators
are outside the initial language slice). Runtime-verified against CPython's
own output: `chain` (2- and 3-argument overloads — no `*args` support),
`repeat(value, times)`, `islice`, `compress`, `accumulate` (`int`/`float`
overloads, like `sum()`), `product`, `permutations`, `combinations`,
`combinations_with_replacement`, `zip_longest`.

Infinite generators (`count`, `cycle`, no-`times` `repeat`) have no eager
equivalent and aren't attempted. Predicate-taking functions (`takewhile`,
`dropwhile`, `filterfalse`, `starmap`) aren't attempted either: there's no
confirmed, tested way to type a callable/predicate parameter in this
codebase yet (`DefaultDict`'s untyped, `.Invoke()`-only factory field is the
only precedent, and it isn't enough to build a generic predicate parameter
on).

`zip_longest` takes two fill values instead of CPython's single shared
`fillvalue`: with independently-typed sequences (`T` and `U`), one value
can't satisfy both slots' types statically. Both fill parameters default to
`None`, matching `DefaultDict.get`'s already-proven generic-default pattern.

`permutations`/`combinations`/`combinations_with_replacement` are built in
two phases — compute over plain `List[int]` index arrays first, then map
indices to `T` values — because of a real compiler limitation found while
writing them: **a generic function that calls itself recursively fails to
compile** ("Generic parameter T for this method call could not fully be
resolved"), even though every call-site type is already concrete. This is
distinct from the (now-fixed) generic-class-self-reference issue in
`Counter.py` — that was a class referencing its own type in a method
signature; this is a function recursing by name, and remains unfixed. The
workaround: keep the actual recursion in a private, non-generic helper
(operating on `List[int]`/`List[bool]`, no type parameter at all), and have
the public generic function call that helper once, non-recursively.

## `string`

Just the character-class constants (`ascii_lowercase`, `ascii_uppercase`,
`ascii_letters`, `digits`, `hexdigits`, `octdigits`, `punctuation`,
`whitespace`, `printable`), exposed as zero-argument functions rather than
Python-style module attributes (`string.digits` becomes `digits()`).
Runtime-verified character-for-character against CPython's own values,
except `whitespace`/`printable`, which omit `\x0b`/`\x0c` (vertical
tab/form feed) — no confirmed-working way to spell those escapes in a
Promethium string literal was tried, so they're left out rather than
guessed at; `whitespace()` has 4 characters where CPython's has 6, and
`printable()` is shorter by the same 2.

Two real findings shaped the zero-argument-function design, both worth
knowing for any future module:

- **A top-level `name: str = "..."` module constant compiles fine, but
  isn't consumable either way**: a bare reference to it doesn't resolve via
  `DefaultUses` the way a bare *function* call does (functions from
  `heapq`/`bisect`/`math`/`operator`/`itertools` all resolve bare at the
  consumer level; a top-level `str` constant declared the same way did
  not), and...
- **...the namespace name `string` itself collides with the native
  `String` type**: `string.digits` fails with "Case for identifier
  'string' does not match original case 'String'" then "No static member
  'digits' on type 'String'" — `string` resolves case-insensitively to the
  platform's `String` type instead of this module's namespace. Any future
  module should avoid namespace names that collide case-insensitively with
  a built-in type name.

Both problems disappear with zero-argument functions: consumers add
`string` to `DefaultUses` and call `digits()`/`punctuation()`/etc. bare,
exactly like every other module in this project — never writing `string.`
at all.

Also adds `split(value, sep=None)` — the compiler team's own call on the
"`String.Split`'s overload set is confusing" compiler-gaps finding: not a
Promethium parser gap, just a genuinely ambiguous native overload set (a
bare string argument suggests one overload, a `Char[]` argument suggests a
*different* one, and neither call lands cleanly), so it's a plain
BaseLibrary-level implementation instead of trying to force native
resolution. Same manual character-scan idiom as `capwords`. Matches
CPython's `str.split()` exactly: omitting `sep` splits on whitespace runs
and discards empty/leading/trailing tokens; a non-empty `sep` splits on
that literal substring and keeps empty tokens between consecutive
separators (`"a,,b".split(",") == ["a", "", "b"]`). An empty `sep` would be
a `ValueError` in CPython; this project has no exception-raising
convention anywhere else, so it degrades to returning `[value]` unchanged
instead. Runtime-verified against CPython for whitespace splitting,
multi-character separators, and the empty-string/empty-separator edge
case.

Also adds `capwords(value)` — CPython's own split-and-capitalize algorithm,
built on private per-target-branched helpers (`_upper`/`_lower`/`_length`/
`_substring`) that call native string methods directly (`.ToUpper()`/
`.toUpperCase()`/`.uppercaseString`, etc.) exactly the way `math.py` calls
native math functions. This corrects an earlier wrong assumption in this
file: native string manipulation is **not** actually blocked — it was
simply untested. Direct probing (three rounds of throwaway per-target
compile experiments) confirmed `.ToUpper`/`.ToLower`/`.Trim`/`.Replace`/
`.Contains`/`.IndexOf`/`.Substring`/`.Length` all compile clean on every
target via `defined("ECHOES"|"ISLAND"|"COOPER")` branching, the same shape
as `math.py`'s native calls. `.Split` is the one method that didn't resolve
cleanly on a first attempt (ambiguity between at least two different
overloads) — `capwords` sidesteps it entirely with a manual character
scan (`_substring`/`_length` in a loop) rather than chasing the exact
`Split` signature. Runtime-verified against CPython's own `capwords`
output, including the empty-string and multiple-consecutive-spaces edge
cases. `Template` is still not attempted — it needs meaningfully more
string-parsing machinery than a single split-and-capitalize pass.

A related, separately-confirmed finding: `int`/`float` → `str` conversion
needs **no** native call or per-target branching at all — `"" + intValue`
and `"" + floatValue` (plain string concatenation, value on the right)
compile clean on every target and produce the expected text at runtime.
This is a different mechanism from the method calls above (the `+`
operator's own implicit conversion, not a method call on the value), and
retroactively unblocked real `__str__` methods on `fractions.Fraction`,
`decimal.DecimalValue`, and `cmath.ComplexValue` (see those sections).

## `statistics`

A small, opt-in subset of Python's `statistics` module: `mean`, `median`,
`median_low`, `median_high`, `mode`, `variance`, `pvariance`, `stdev`,
`pstdev`, `harmonic_mean`, `geometric_mean` (the latter via `math.log`/
`math.exp`, fully qualified). Unlike `median`, `median_low`/`median_high`
return the *same type as the input* (`int` stays `int`), matching CPython
exactly — no float-promotion ambiguity to route around since neither one
ever needs to average two elements together. Overloaded for `int`/
`float` like `heapq`/`bisect` (ordering and arithmetic aren't available on
unconstrained generic `T`), except `mode`, which is fully generic — it's
built directly on `collections.Counter[T]` (`Counter[T](data).most_common(1)`)
and only needs `T` to support equality, which `Counter` already provides.
Runtime-verified against CPython's own output for every function, including
both the even- and odd-length cases of `median`.

`median` always returns `float`, unlike CPython's version (which returns
the *middle element's own type* for odd-length input, only promoting to
`float` for the even-length average) — a Promethium function can't return
one type or another based on a runtime-only condition, so this always
returns `float`; the numeric value still matches CPython exactly in every
case, only the static type differs for odd-length `int` input.

Calls `Promethium.sorted(...)` and `math.sqrt(...)` fully qualified rather
than bare, the same workaround `heapq.py` needed for calling a concrete
function from another namespace (bare calls to those don't reliably
resolve via ambient `DefaultUses`).

## `copy`

`copy(values)` (shallow) and `deepcopy(values)` (one level deep, for
`List[List[T]]` only) — the smallest possible slice of Python's `copy`
module that's generically implementable without reflection over arbitrary
types (a fully generic `deepcopy` recursing into arbitrary user-defined
objects isn't attempted, same reasoning as `namedtuple`'s exclusion from
`collections`). Runtime-verified: mutating a shallow copy leaves the
original untouched, and mutating a deep copy's *inner* list also leaves the
original's inner list untouched (the property a plain `copy()` on a
`List[List[T]]` wouldn't have, since a shallow copy of a list of lists still
shares the inner lists by reference).

`deepcopy` intentionally has **no** flat `List[T]` overload alongside the
`List[List[T]]` one — flat and nested "deep" copies would be different
methods needing to agree on how to bind `T` for the same `List[List[int]]`
argument (does `T` mean `int` or `List[int]`?), and the compiler refuses to
guess, failing with "Ambiguous call to overloaded method 'deepcopy'"
(confirmed by writing the flat overload first and hitting this on every
call with a nested list). For a flat list, "deep" and "shallow" copy are
the same operation anyway (nothing nested to alias) — call `copy()`
directly.

Writing this module's demo also reconfirmed and *sharpened* an existing
finding (at the time): `List`'s bracket-write indexer was read-only not
just "on at least one target" (as `heapq.py` originally found on Toffee)
but **on Echoes too** — `shallow[0] = 99` on a plain `Promethium.List[int]`
failed there with "Default indexer ... is read-only". That was correct
compiler behavior, not a bug: `PromethiumBaseLibrary.List` only declared
`__getitem__`, never `__setitem__`, at the time. **`List` has since gained
a real `__setitem__`**, so bracket-write (`someList[i] = value`, including
compound assignment like `someList[i] += 1`) now works directly, and every
module in this project that used to route around it with
`pop(index)` + `insert(index, value)` (`Counter.__setitem__`,
`OrderedDict.__setitem__`, `DefaultDict.__setitem__`, `heapq.py`'s sift
functions, `itertools.py`'s permutation bookkeeping,
`random.py`'s `shuffle`, `operator.setitem`) has been simplified back to
plain bracket assignment. Re-verified with the same regression cases each
of those already had, all still passing.

## `functools`

Just `reduce` — `partial`/`lru_cache`/`wraps`/`cmp_to_key` all need either
decorators or storing and re-dispatching an arbitrary callable's signature,
neither attempted anywhere in this codebase. `reduce`'s `func` parameter is
deliberately untyped, matching `DefaultDict`'s factory field (there's no
confirmed way to type a callable parameter here — see `itertools.py`'s
notes), and is invoked with `func.Invoke(accumulator, item)`.

Two-argument `.Invoke(a, b)` works on Echoes/Island/Cooper but not Toffee:
an untyped parameter erases to Objective-C `id` there, which doesn't expose
a matching 2-parameter `invoke` ("No overloaded method 'invoke' with 2
parameters on type 'id'"). Handled the same way `DefaultDict.__getitem__`
handles its own Toffee limitation: `defined("TOFFEE")` raises a clear error
instead of failing to compile or misbehaving silently.

Runtime-verified with a **lambda** argument (`reduce(lambda a, b: a + b,
values, 0)`). A plain named function passed by reference does **not**
work as a callable argument — `reduce(myFunc, ...)` fails even when
fully-qualified, because the compiler insists on *calling* a named function
rather than treating its name as a value ("Parenthesis required for call").
Always pass a lambda literal to any function-parameter-taking API in this
project, including multi-parameter ones (`lambda a, b: ...` is confirmed
working, not just the zero-parameter form `DefaultDict`'s factory uses).

## `random`

Exposes a single class, `RandomGenerator` (constructed as
`RandomGenerator(seed)`) — deliberately not named plain `Random`, and
deliberately not CPython's free-function-plus-implicit-global-state shape.
Both deviations were forced, not stylistic:

- **`class Random:` fails to compile on every Toffee target**: "The public
  type 'Random' has a duplicate with the same short name in reference
  'Elements', which is not allowed on Cocoa" — Cocoa's flat type registry
  rejects two types sharing a short name even across different namespaces,
  unlike Echoes/Island/Cooper. Renaming to `RandomGenerator` fixed it.
- **CPython's implicit global default instance has no safe equivalent
  here**: native per-target RNGs turned up real uncertainty on every
  leg — Echoes' `System.Random` needs an instance (whether Python-style
  parens instantiate a *native* type at all, stored in a variable, is
  unconfirmed anywhere in this codebase or the wider Elements tree — the
  only related precedent is a native type constructed inline inside a bare
  `raise` expression); Island's native `Random` only exposes a raw
  `Cardinal`, no ranged/double helpers; Cooper's `Math.random()` can't be
  seeded; and Toffee's candidates (`arc4random_uniform`, `rtl.random`) are
  only confirmed from Oxygene-compiled code, never a Promethium `.py` file.
  Rather than gamble on several unconfirmed behaviors at once (including
  whether a *module-level* mutable field even works, which is separately
  unconfirmed — see `string.py`'s notes on module-level constants), this
  implements its own small, fully portable linear congruential generator in
  pure Promethium arithmetic — no native call and no per-target branching
  anywhere — storing its state in an ordinary *instance* field
  (`RandomGenerator._state`), the same proven kind of per-instance mutable
  state `Counter._entries` already relies on.

This is a deliberately low-quality generator next to CPython's Mersenne
Twister: `random()` has 6 significant decimal digits of resolution, not a
full 53-bit mantissa — fine for shuffling/sampling, not for anything
statistically sensitive. Runtime-verified: same seed reproduces an
identical sequence; `randint(a, b)` stays in `[a, b]` across 1000 trials;
`shuffle` preserves length and the sum of elements (a permutation, not a
resample); `choice` returns an in-range element; `uniform(a, b)` stays in
range. `choice`/`shuffle` are overloaded for `int`/`float`/`str`, like
`heapq`/`bisect`.

Also exposes `next32()`, returning the raw internal LCG step as-is — added
for `uuid.py`, which needs full-range 32-bit words: `randint`'s own
`b - a + 1` span computation overflows `Int32` for the full `Int32` range
itself, so it can't produce one safely.

## `fractions`

Just `Fraction`: construction from a numerator/denominator pair (reduced to
lowest terms with a positive denominator via `math.gcd`, fully qualified —
same reasoning as `statistics.py`'s calls to `math.sqrt`) or from a single
integer; `__add__`/`__sub__`/`__mul__`/`__truediv__`/`__neg__`/`__abs__`/
`__pow__` (integer exponent, positive or negative — a negative exponent
inverts numerator/denominator)/`__eq__`/`__lt__`/`__le__`/`__float__`/
`__str__`. `__pow__` loops rather than recursing (though recursion would
likely be fine here too — `Fraction` isn't generic, so it wouldn't hit the
generic-function self-recursion limitation `itertools.py` documents; the
loop was just simpler to reason about directly). Like `Counter`'s
arithmetic dunders, these
are reachable only via explicit calls (`a.__add__(b)`), not `+`/`-`/`==`/
`<` operator syntax — Promethium doesn't lower those operators to dunder
methods on a class any more than it does for `Counter`. Runtime-verified
against CPython's own `fractions.Fraction` output for every operation,
including automatic reduction (`Fraction(4, 8)` stores as `1/2`).

`__str__` is built on plain string concatenation (`"" + self.numerator +
"/" + self.denominator`) — `int`→`str` conversion turned out to need no
native call or per-target branching at all: `"" + intValue` compiles clean
on every target and produces the expected text at runtime. (An earlier
version of this file claimed the opposite — see `string.py`'s notes above
for the correction and how it was found.) `__float__`
forces true floating-point division (`(self.numerator * 1.0) /
self.denominator`) rather than `self.numerator / self.denominator`
directly: both operands would otherwise be `int`, and this codebase
consistently assumes `int / int` truncates like C/C#/Java (see `operator.
py`'s `floordiv`) — multiplying by `1.0` first forces the division itself
to run in floating point.

## `graphlib`

Just `TopologicalSorter.static_order()` — the incremental `prepare()`/
`get_ready()`/`done()` protocol isn't attempted, since `static_order()`
covers the common case (a full dependency order computed up front) without
needing to model in-progress state across calls. `add(node, predecessors)`
takes a `List[T]` of predecessors rather than CPython's `*predecessors`
(no `*args` in this language slice); a cycle raises `Promethium.ValueError`
rather than CPython's `CycleError` (no custom exception types have been
established in this project). Node lookup is a linear `.Equals`/`.isEqual`
scan, exactly like `Counter._index_of`. Runtime-verified: a small diamond-
shaped dependency graph produces a valid order, and a genuine cycle raises
(caught via `try`/`except ValueError`, confirmed working here — the first
`try`/`except` used anywhere in this project).

## `decimal`

A fixed-point `DecimalValue` (unscaled `int` + `scale`, value =
`unscaled / 10^scale`) — not CPython's arbitrary-precision,
context-configurable `Decimal`, but exact base-10 arithmetic within `int`'s
range, the property `decimal` is normally reached for (avoiding float's
binary-fraction rounding). `__add__`/`__sub__`/`__mul__`/`__eq__`/`__lt__`/
`__le__`/`__float__`/`__str__`, explicit-call-only like `Fraction`/
`Counter`. `__str__` zero-pads the fractional part out to exactly `scale`
digits (`0.05`, not `0.5`) via a small `_digitCount` helper — pure integer
arithmetic, no native call, following the `int`→`str` concatenation
finding documented in `string.py`'s section above. Runtime-verified
against CPython's own `Decimal` output for mixed-scale arithmetic (`19.99
+ 5.005` correctly produces the 3-decimal `24.995`, not a 2-decimal
truncation) and for `__str__`, including the zero-padding and negative-
value cases.

Deliberately **not** named `Decimal`: .NET's own `System.Decimal` is a
prominent built-in value type, and `random.py`'s `class Random:` already
confirmed that a Promethium class sharing a short name with a native type
risks at least a Toffee-only compile failure. Named `DecimalValue`
preemptively rather than spending a build cycle rediscovering the same
problem.

## `cmath`

Promethium has no native complex-number type at all — the grammar
explicitly rejects complex literals ("Elements has no cross-platform
complex-number type") — so this defines its own `ComplexValue` class rather
than hooking a native one, the same way `fractions.py`/`decimal.py` define
their own numeric types. Deliberately not named `Complex`: .NET's
`System.Numerics.Complex` is a real, plausible collision by the same
mechanism `random.py`'s `Random` and `decimal.py`'s `Decimal` already hit.

`ComplexValue` supports `__add__`/`__sub__`/`__mul__`/`__truediv__`/
`__neg__`/`__eq__`/`__abs__`/`conjugate`/`__str__` (all explicit-call-only,
as usual — `__str__` matches CPython's `(3+4j)`/`(3-4j)`/`4j` shapes, via
plain `float`→`str` concatenation); module-level `phase`, `polar`, `rect`,
`sqrt`, `exp`, `log` build directly on `math.py`'s already-verified
`sin`/`cos`/`exp`/`log`/`atan2` (fully qualified — same reasoning as
`statistics.py`'s calls to `math.sqrt`). Runtime-verified against
CPython's own `complex`/`cmath` output for every operation, including
`sqrt` of a negative real number producing a correct pure-imaginary
result, and `__str__`'s three distinct formatting shapes.

## `datetime`

Mostly date arithmetic — `PyDate`/`PyTimeDelta`. Proleptic-Gregorian day
arithmetic (the same algorithm CPython's own pure-Python reference
implementation uses) is pure integer math, so this needs no native call
at all. Not named `Date`/`DateTime`/`TimeDelta`: the first two collide
with native BCL/platform types by the mechanism `random.py`'s `Random`
and `decimal.py`'s `Decimal` already confirmed breaks Toffee builds.

Every value is stored and compared through a single day ordinal (day 1 =
January 1, year 1, matching CPython's `date.toordinal()` convention
exactly — including `weekday()`'s Monday-is-0 result), so `__add__`/
`__sub__`/comparisons are just integer arithmetic on that ordinal. No
`@classmethod` in this language slice, so CPython's `date.fromordinal(...)`
becomes the module-level `dateFromOrdinal(...)`. Runtime-verified against
CPython's own `date`/`timedelta` output, including a leap-day (`Feb 29
2024`) rollover into March.

`today() -> PyDate` reads the real wall clock (UTC) — originally cut,
"reading the real wall clock needs the same kind of per-target native-
call research `math.py`/`random.py` needed, not yet done for time." That
research is done now (see `time.py`): a bare `DateTime` identifier
resolves inconsistently per target (sometimes the platform-native BCL
type, sometimes nothing), so `today()` calls the fully-qualified
`RemObjects.Elements.RTL.DateTime.UtcNow` explicitly and reads its
`Year`/`Month`/`Day` — RTL2's `DateTime` is already a genuine cross-
platform abstraction, so no `defined("ECHOES")`-style branching was
needed here at all. Runtime-verified against
`datetime.datetime.utcnow().date()`'s year/month/day/weekday, same day.
Still no `now()` (date *and* time-of-day together) — that needs an hour/
minute/second-carrying type this module doesn't have yet.

## `calendar`

`isleap`, `leapdays`, `weekday`, `monthrange`, `month_name(index)`,
`day_name(index)` — built directly on `datetime.PyDate`'s already-verified
ordinal/weekday arithmetic (`weekday(...)` is a one-line call into
`PyDate`) rather than reimplementing it. `month_name`/`day_name` are
CPython module-level *subscriptable* lists (`calendar.month_name[1]`);
here they're parameterized functions instead (`month_name(1)`), the same
convention `string.py` established for its character-class constants.
Runtime-verified against CPython's own `calendar` output for every
function, including a leap-February `monthrange`.

## `ipaddress`

Just `IPv4Value`, constructed from four `int` octets — deliberately not
from a dotted-quad string (`.split('.')` hits the same unconfirmed
native-string gap as `re`/`csv`). Also deliberately **not** packed into a
single 32-bit `int` the way CPython's `IPv4Address` stores it internally:
Promethium's `int` is a *signed* 32-bit `Int32`, and a packed address only
needs 24 more bits to overflow it — `192.168.1.1` alone would already wrap
to a negative number, corrupting both its value and its ordering under
`<`. Storing all four octets separately sidesteps the overflow entirely;
`__lt__`/`__le__` compare lexicographically over `a, b, c, d`, matching
CPython's actual address ordering. `is_private`/`is_loopback`/
`is_multicast` are plain octet-range checks. Runtime-verified against
CPython's own `IPv4Address` output for every predicate and for ordering.

## `colorsys`

`rgb_to_hsv`/`hsv_to_rgb`/`rgb_to_hls`/`hls_to_rgb`, a direct port of
CPython's own algorithm. CPython's version computes `i = int(h*6.0)` to
pick a "sector" of the hue wheel — a float-to-int cast with no confirmed
working syntax in this codebase (see `math.py`'s notes). Sidestepped by
keeping the sector index as a `float` throughout (`math.floor(h * 6.0)`)
and comparing it against float literals (`0.0`, `1.0`, ...) instead of
switching on an `int` — safe because the sector value is always an exact
small integer (0–5) even in floating point. Runtime-verified against
CPython's own `colorsys` output (within float rounding) for a full
RGB→HSV→RGB and RGB→HLS→RGB round trip.

## `uuid`

Just `uuid4(rng)`, and only as raw components — no canonical hyphenated
hex string (`int`-to-`str` formatting needs a native per-platform call
this codebase has never established, same as `fractions.py`'s `__str__`
note) and no single packed 128-bit value (`int` is a signed 32-bit
`Int32` — the overflow problem `ipaddress.py` avoids for a 32-bit address
applies twice as hard to 128 bits). `UUID4Value` instead stores the value
as four 32-bit words (`w0`..`w3`), generated via a new `RandomGenerator.
next32()` method (the existing `randint` can't safely cover a full 32-bit
span — `b - a + 1` for the whole `Int32` range overflows `Int32` itself).

The version (`0100`) and variant (`10xx`) bits are set with `&`/`|`/`>>`,
already-proven bitwise ops — masking after a right-shift extracts the
correct bits regardless of whether the shift is arithmetic or logical on a
negative `int`, so `int`'s signedness doesn't affect correctness here.
Runtime-verified: generated values report version `4` and variant bits
`2` (binary `10`, the RFC 4122 variant), two draws from the same generator
differ, and reconstructing a `UUID4Value` from another's own components
compares equal. Randomness quality matches `random.py`'s own generator (a
small LCG, not cryptographically secure) — fine for non-adversarial unique
IDs, not for anything security-sensitive.

## `textwrap`

Just `wrap(text, width)`/`fill(text, width)` — a greedy word-wrap over
whitespace-delimited words, found with the same manual scan `string.py`'s
`capwords` uses (no `.Split`, no regex). `TextWrapper`'s many options
(indent, tab expansion, hyphen breaking) aren't attempted. A word longer
than `width` gets its own line rather than being sliced — a deliberate
simplification of CPython's default `break_long_words=True`. Runtime-
verified against CPython's own `wrap`/`fill` output.

## `csv`

`parse_line(line)`/`write_row(fields)` — one row at a time, not a
`reader`/`writer` bound to a file handle (this project's own scope
excludes filesystem APIs; see Build notes below). Handles CPython's
default `excel` dialect: comma-separated fields, double-quoted fields
(needed when a field contains a comma), and `""` as an escaped quote
inside a quoted field. No custom delimiter/quote character, no embedded
newlines inside a quoted field, no other `Dialect` options. Built on the
same manual-character-scan technique as `string.py`'s `capwords`/
`textwrap.py`'s word-finder. Runtime-verified against CPython's own `csv`
module for both directions — parsing a quoted-comma-and-escaped-quote line
and writing a row back out byte-for-byte the same way.

## `configparser`

`parse(lines)` reads INI-style text — already split into lines, since this
project excludes filesystem APIs and there's no file handle to read from
directly — into an `OrderedDict[str, OrderedDict[str, str]]` (section name
→ ordered key/value map), reusing `collections.OrderedDict` rather than
inventing another ordered-mapping type. Supports `[section]` headers,
both `key = value` and `key: value` separators (like CPython), `#`/`;`
comment lines, and blank-line skipping. Not attempted: interpolation
(`%(x)s`), the `DEFAULT`-section fallback, multi-line values, or writing
config back out. Uses a hand-rolled `_indexOfChar` rather than native
`.IndexOf`, deliberately: Toffee's equivalent
(`rangeOfString(...).location`) returns Cocoa's `NSNotFound` sentinel
instead of `-1` when missing, the same class of problem `operator.py`'s
`indexOf` already avoids for `List` — a manual scan sidesteps the
question entirely. Runtime-verified against CPython's own `ConfigParser`
output for a two-section config with both separator styles and a comment
line.

## `difflib`

`ratio(a, b)` and `get_close_matches(word, possibilities, n, cutoff)`,
built on the real Ratcliff-Obershelp matching-blocks algorithm CPython's
own `SequenceMatcher` uses — not a simpler LCS approximation, which would
give a *different* number for many input pairs and break this project's
standing bar of runtime-verifying against CPython's own output.
`_findLongestMatch` is a plain O(n·m) scan rather than CPython's
junk-aware hashing (fine for short strings, not a performance-critical
diff engine); `get_matching_blocks`'s usual recursive divide-around-the-
best-match approach is implemented with an explicit `List`-backed stack
instead of real recursion. CPython's "autojunk" heuristic for very common
characters in long sequences isn't replicated — irrelevant for the short
strings this is meant for, but long junk-heavy input could diverge from
CPython's exact number. Runtime-verified bit-for-bit against CPython's own
`SequenceMatcher.ratio()` (`0.6153846153846154` for `"kitten"`/`"sitting"`,
matching exactly) and `get_close_matches`' output and ranking order.

A local variable literally named `match` failed to compile ("Unknown
identifier 'match', did you mean 'System.Text.RegularExpressions.Match'?")
— the same shadowing-by-a-native-identifier problem `random.py`'s `Random`
class and `decimal.py`'s `Decimal` class already hit, but for a local
variable rather than a type declaration. Renamed to `found`.

## `fnmatch`

Just the pattern matcher itself, `fnmatch(name, pattern)` — not
`fnmatch.filter`/`glob` (which need filesystem listing, out of scope; see
Build notes below). The predicate doesn't touch the filesystem at all, so
it's in scope the same way `csv`/`configparser` are: pure text processing
over an already-provided string. Supports `*`/`?` via the standard
iterative two-pointer/backtrack algorithm (no recursion, no regex engine).
`[seq]`/`[!seq]` character classes aren't attempted — CPython translates
the whole pattern to a regex internally to support those, a meaningfully
bigger step than plain `*`/`?` matching. Runtime-verified against
CPython's own `fnmatch.fnmatch` output, including a `?`-only pattern and a
non-matching case.

## `shlex`

Just `split(value)` — CPython's POSIX-mode tokenizer: splits on
whitespace, honors single quotes (contents kept literally) and double
quotes (with `\"`/`\\` escapes honored inside), and a bare backslash
outside any quotes escapes the next character. The full stateful
`shlex.shlex` lexer class (comments, punctuation tokens, `wordchars`
customization) isn't attempted. Built on the same manual-character-scan
technique as `csv.py`/`configparser.py`. Runtime-verified against
CPython's own `shlex.split` output for plain splitting, both quote styles,
a backslash escape, and repeated/leading whitespace.

## `html`

`escape`/`unescape` for the five entities CPython's own `html.escape`
produces (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&#x27;`) plus `unescape`'s
common apostrophe aliases (`&#39;`, `&apos;`) — not the full HTML5
named-character-reference table or numeric character references
(`&#NNN;`/`&#xHHH;`), which would need an int-codepoint-to-`str`
conversion this codebase has never established (different from the
confirmed decimal `int`→`str` conversion — see `string.py`'s notes). Built
entirely on the already-confirmed native `.Replace`/`.replace`/
`.stringByReplacingOccurrencesOfString` (all three replace every
occurrence by default, no manual loop needed). Order matters: `escape`
replaces `&` first so the `&` it introduces isn't re-escaped; `unescape`
replaces `&amp;` last so an already-escaped literal like `&amp;lt;` comes
back as literal `&lt;` text, not `<`. Runtime-verified byte-for-byte
against CPython's own `html.escape` output, and a full escape/unescape
round trip.

## `xml`

`parse(text) -> XmlTreeNode`, in the shape of `xml.etree.ElementTree`
(`.tag`, `.attrib`, `.text`, `.findall(tag)`), not that module's actual
namespace. **Not** a hand-rolled parser (an earlier version of this file
was, before this was found) — internally backed by `RemObjects.Elements.
RTL.XmlDocument`, a real, cross-platform parser that already ships with
the Elements RTL (`RTL2/Source/RemObjects.Elements.RTL/XmlDocument.pas`/
`XmlParser.pas`/`XmlTokenizer.pas`), giving real namespace/CDATA/comment/
entity handling for free instead of this project's own scoped-down
approximations. `.text` concatenates *all* nested text recursively
(`XmlElement.Value`'s own semantics), not just the text immediately
following the start tag the way CPython's `ElementTree.text` does — a
deliberate, simpler difference, not an attempt at exact `.tail`-less
mixed-content parity.

Getting here needed two real fixes, neither of them "just call the API":

- **A reference-wiring fix.** This RTL2 checkout builds its own
  `Elements.dll`/`.fx`/`.jar` under `RTL2/Bin/<target>/...`, distinct from
  the "Elements" reference this project already had bare (no `HintPath`)
  in every per-target `ItemGroup` — which resolved ambiently to a
  *different*, older `Elements.dll` that doesn't contain this RTL at all
  (confirmed: calling `RemObjects.Elements.RTL.XmlDocument` failed with
  "Unknown identifier" until an explicit `HintPath` was added to each
  `Reference Include="Elements"`/`"libElements"`/`"elements"` block,
  pointing at the matching RTL2 build output per target — see this
  project's `.elements` file for the exact paths). Any consumer of the
  compiled `Promethium.PythonCompatibility` assembly needs the *same*
  `Elements` `HintPath` wired in too, or the two won't agree on which
  physical assembly "Elements" is.
- **Toffee's `for x in someRtlSequence:` erases `x` to a dynamic `id`**,
  the same generics-erasure behavior already documented for `DefaultDict`'s
  factory — every property access on the loop variable fails ("No member
  'LocalName' on type 'id'", and the lowercase Cocoa spelling doesn't help
  either; the member is inaccessible on `id` entirely). Fixed by
  re-declaring the loop variable with an explicit type annotation as the
  first statement inside the loop body (`child: RemObjects.Elements.RTL.
  XmlElement = rawChild`), which recovers the static type.

Not named `XmlElement`: that's `System.Xml.XmlElement`, a real collision
by the same mechanism as `Random`/`Decimal`/`Complex`. `XmlNode` (the next
guess) *also* collided on Cocoa, so this took two renames to land on
`XmlTreeNode`.

Runtime-verified against CPython's own `ElementTree.fromstring` output:
tag names, `findall`, attribute values, entity-decoded text content,
self-closing elements, nested elements, and a leading XML declaration —
same test cases the earlier hand-rolled version passed, now backed by a
real parser instead of an approximation.

## `re`

`compile`/`match`/`search`/`fullmatch`/`findall`/`finditer`/`sub`/`split`/
`escape`, plus a `Pattern` class (from `compile`) and a `Match` class (what
every match-returning function/method returns). Backed by
`RemObjects.Elements.RTL.Regex`, a portable regex engine added to RTL2 as a
side task alongside this module (`RTL2/Source/RemObjects.Elements.RTL/
Regex.pas`) — literals, `.`, character classes (`[abc]`, `[^abc]`, ranges),
anchors `^`/`$`, quantifiers `* + ? {m} {m,} {m,n}` (greedy and lazy),
alternation `|`, capturing/non-capturing groups `(...)`/`(?:...)`, and
escapes `\d \D \w \W \s \S \b \B`. No backreferences, lookahead/lookbehind,
named groups, Unicode property classes, or case-insensitive/multiline/
dotall flags — the engine doesn't support them, so there's no `flags`
parameter here.

Two real gaps needed working around, not just calling the API:

- **`Regex`'s constructor is a *named* constructor**
  (`constructor withPattern(...)`), and Promethium has no calling
  convention that can invoke one — bare positional, `=`-style, and
  `:`-style keyword args were all tried; the `:` form is a hard Promethium
  syntax error, not just a label mismatch. Fixed by adding a plain
  `class method FromPattern(aPattern): not nullable Regex;` factory to
  `Regex.pas` itself (mirroring `XmlDocument.FromString`, which Promethium
  already calls fine), rather than trying to change how Promethium calls
  constructors.
- **`Regex.Match`/`IsMatch` always search anywhere in the string** — there
  is no "only try this exact start position" primitive in the engine.
  Python's `match()` (anchored to the start) and `fullmatch()` (the whole
  string) need stronger anchoring than that, so `Pattern` actually compiles
  *three* engines from one source pattern: the raw pattern for
  `search`/`findall`/`finditer`/`sub`/`split`, `^(?:pattern)` for `match`,
  and `^(?:pattern)$` for `fullmatch`. Wrapping in a non-capturing group
  keeps capture-group numbers identical across all three.

Other deliberate deviations from CPython, all forced by fixed function
return types (a Promethium function can't return "a list of strings, or a
list of tuples, depending on the pattern" the way CPython's `findall`
does):

- `findall` always returns whole-match strings (`List[str]`), never group
  tuples — use `finditer` plus `Match.group(n)` to reach capture groups.
- `finditer` returns an eagerly-built `List[Match]`, not a lazy iterator —
  the same stand-in this project already uses everywhere else a CPython
  generator would otherwise be needed (see `csv`/`difflib`).
- `Match.start()`/`end()`/`span()` only ever cover the whole match (group
  0): `RegexMatch` exposes an `Index` for the overall match and each
  group's matched *text*, but never a per-group start/end offset, so a
  capture group's own position isn't computable from what the engine
  returns.
- `sub`'s replacement string accepts Python-style backreferences (`\1`,
  `\g<12>`) and is translated to the engine's own `$1`/`$12` syntax before
  being handed to `Regex.Replace`; a literal `$` in the replacement is
  escaped to `$$` first so it survives that translation unchanged.
- `escape` matches CPython 3.7+'s exact special-character set
  (`()[]{}?*+-|^$\.&~#` plus whitespace) rather than just the characters
  this engine treats as special, since its job is safe embedding of
  arbitrary text into a pattern string — CPython's contract, not this
  engine's.

Runtime-verified against live CPython 3.12's `re` module: `search`/`match`/
`fullmatch` anchoring (including the "matches somewhere but not at the
required position" negative cases), `findall`, multi-group `search` with
`group(1)`/`group(2)`, `sub` with both a literal replacement and a
`\1`/`\2`-backreference swap, `split`, and `escape` — all outputs matched
byte-for-byte.

## `json`

`loads(text) -> JsonValueNode`/`dumps(value) -> str`, a hand-written
recursive-descent parser/serializer (not `re`-based — JSON's grammar is
closed and doesn't benefit from a general regex engine) over
`JsonValueNode`: a tagged-union class with one field per JSON kind
(`is_null`/`is_bool`/`is_int`/`is_float`/`is_string`/`is_array`/
`is_object`, and matching `as_*()` accessors), plus module-level factories
(`json_null()`, `json_bool(v)`, `json_int(v)`, `json_float(v)`,
`json_string(v)`, `json_array(v)`, `json_object(v)`).

Not named `JsonValue`: that collided on Cocoa with something in the
referenced `Elements` assembly, the same "duplicate short name" issue as
`Random`/`Decimal`/`XmlElement` elsewhere in this project. The next guess,
`JsonNode`, *also* collided — same two-renames-needed story as `xml.py`'s
`XmlTreeNode`. `JsonValueNode` was the one that stuck.

This is the module that put this session's "reflection and dynamic typing
are blocked" finding to the test — and deliberately doesn't use `dynamic`
at all. `typing.Any`/`dynamic` are confirmed working now (see the stdlib
survey), but JSON's value space is closed (always exactly six kinds), so
a plain tagged-union class sidesteps needing runtime dynamism here
entirely — a better fit than reaching for `dynamic` just because it's
newly available.

CPython's `json` folds a parsed number into `int` or `float` depending on
whether the source text had a `.`/exponent; this keeps that same split
(`is_int()` vs `is_float()`) rather than collapsing every number into
`float`, so `dumps(loads("3"))` round-trips as `"3"`, not `"3.0"`.

Two real native-call gaps surfaced getting this working, both worth
knowing for any future module:

- **Python's own `float(x)`/`int(x)` conversions are not callable from
  Promethium at all** — not for numeric widening (`float(someInt)` fails
  "Unknown identifier 'float'") and not for string parsing (`float(
  "1.5")` fails differently per target, sometimes resolving to an
  unrelated native RTL function with an incompatible signature). Fixed
  with real per-target native calls for string→number parsing
  (`Double.Parse`/`Int32.Parse` on Echoes/Island, `Double.parseDouble`/
  `Integer.parseInt` on Cooper, `.doubleValue`/`.intValue` on Toffee), and
  plain arithmetic promotion (`someInt + 0.0`) instead of a cast for
  int→float widening.
- **Native float→string formatting drops the decimal point for a
  whole-number float** — `3.0` stringifies as `"3"`, not `"3.0"`, on at
  least one target. `_dumpFloat` appends `.0` when the native-formatted
  text has no `.`/`e`/`E` in it, so a float round-trips as a float instead
  of silently becoming indistinguishable from an int.

Not supported, documented rather than silently wrong: `\uXXXX` escape
sequences in string literals raise `ValueError` (no confirmed portable
way to turn a parsed code point back into a character was tried across
all four targets); `dumps` never escapes non-ASCII (CPython's
`ensure_ascii=True` default) — output is UTF-8 text with non-ASCII passed
through unchanged.

Runtime-verified against live CPython 3.12's `json` module: nested
objects/arrays, all six value kinds, negative numbers, exponent notation,
string escapes (`\n`/`\t`/`\"`), empty array/object, and whitespace
tolerance around tokens — all outputs matched byte-for-byte.

## `pprint`

`pformat(value) -> str`/`pprint(value)`, multi-line indented formatting
over `json.JsonValueNode` — the same scope decision `json.py` made and for
the same reason: Promethium has no single value that can hold an
arbitrary object outside `typing.Any`/`dynamic` (confirmed working now,
see the stdlib survey), but reaching for that here would trade a closed,
well-understood value space for open-ended per-target reflection with no
real payoff. `JsonValueNode` is already this project's closest thing to
"a generic value," and pretty-printing loaded JSON/config data is the
most common real reason to reach for `pprint` in the first place.

Output is **JSON syntax** (`null`/`true`/`false`, double-quoted strings),
not CPython's Python-literal `pprint` syntax (`None`/`True`/`False`,
single-quoted strings) — a deliberate deviation, not an oversight: there's
no arbitrary Python object here to `repr()`, only `JsonValueNode` trees,
so JSON's own syntax is the more honest fit. In practice this makes
`pformat`/`pprint` a multi-line, indented counterpart to `json.dumps` —
verified byte-for-byte identical in shape to CPython's own
`json.dumps(value, indent=2)` on the same data (nested objects/arrays,
mixed value kinds, empty array/object).

## `tomllib`

`loads(text) -> JsonValueNode` (always an object at the root) — a
TOML parser reusing `json.py`'s tagged-union value tree rather than a
second one, since TOML and JSON describe the same value universe minus
JSON's `null`. Python 3.11+ ships `tomllib` in the real stdlib; this
follows the same `loads`-only shape (no `dump`/`dumps` — TOML writing
wasn't attempted).

Supported: comments, bare and basic-quoted table/key names, dotted paths
in both table headers (`[a.b.c]`) and key/value assignments (`a.b.c =
1`), `[table]` headers, `[[array.of.tables]]` headers, inline tables,
arrays (including ones spanning multiple lines with trailing commas and
comments), basic strings (same escapes as `json.py`), literal strings
(`'...'`, no escape processing), integers and floats including `_` digit
separators (`1_000_000`), and booleans.

Not supported, documented rather than silently wrong: multi-line strings
(`"""…"""`/`'''…'''`), dates/times (TOML has native date/time literals
with no equivalent in this project's closed value set — everything here
is null/bool/int/float/string/array/object), hex/octal/binary integer
literals, and `inf`/`nan` float literals. Any of these in the source
raises `ValueError`.

Runtime-verified against live CPython 3.12's `tomllib`: nested table
headers, array-of-tables, inline tables, arrays, dotted key/value paths,
comments, underscore-separated numbers, and mixed value kinds — output
matched `json.dumps` on the same parsed structure byte-for-byte, in both
directions (a full multi-section document, and a standalone dotted-key
case).

## `time`

Just `time() -> float` — Unix epoch seconds, reading the real wall clock.
Closes a gap `datetime.py` explicitly flagged early on ("reading the
actual wall clock needs the same kind of per-target native-call research
`math.py`'s functions and `random.py`'s RNG needed, which hasn't been
done for time") now that that research has matured. The real surprise:
no per-target `defined("ECHOES")`-branching was needed at all —
`RemObjects.Elements.RTL.DateTime` (RTL2's own date/time class, reached
via its fully-qualified name; a *bare* `DateTime` resolves
inconsistently per target and shouldn't be relied on) is already a
genuine cross-platform abstraction with its own `UtcNow`/
`ToUnixTimeSeconds()`, backed internally by `java.util.Calendar` on
Cooper, `NSDate` on Toffee, and the platform's native `DateTime` on
Echoes/Island — the per-target work this module would otherwise have
needed to do by hand was already done, inside RTL2. Runtime-verified
against live CPython's `time.time()` — same Unix second.

## `queue`

`PyQueue[T]`/`PyLifoQueue[T]`, thin wrappers over the already-shipped
`collections.Deque`. Not named `Queue`/`LifoQueue`: `Queue` collides with
a native BCL type by the same mechanism `Random`/`Decimal`/`DateTime`
already confirmed elsewhere in this project — same `Py`-prefix convention
`datetime.py`'s `PyDate`/`PyTimeDelta` already established for exactly
this situation.

No real concurrency: this language slice has no threading primitives
(the same reason `asyncio`/generators are excluded), so `put`/`get` never
actually block — they raise `Promethium.ValueError` on overflow/underflow
instead of CPython's queue-specific `queue.Full`/`queue.Empty` exceptions
(no custom exception types beyond reusing `ValueError`, same convention
`graphlib.py` documents). `put_nowait`/`get_nowait` are aliases for
`put`/`get`, since there's no blocking variant to be the non-blocking
alternative *to*. `maxsize` uses `-1` as the "unbounded" sentinel, same
concrete stand-in for CPython's default this project uses elsewhere
(`Deque.maxlen`, `bisect.py`'s `hi`).

Finding this module's real bug needed isolating it first: a *fresh*
generic class (`PyQueue[T]`, not previously used anywhere) failed to
resolve from a separate consumer project — both bare and fully
namespace-qualified — even though the compiled assembly genuinely
contained it (confirmed via `strings`). Root cause: **a generic class
needs an explicit `from <namespace> import <ClassName>` to resolve
cross-project at all** — bare `DefaultUses` resolution, which works fine
for non-generic classes and free functions, doesn't work for generic
ones. This was already this project's established practice for `Counter`/
`OrderedDict`/`DefaultDict`/`Deque` (always explicitly imported) without
ever being diagnosed as load-bearing rather than just tidy — now it is.

Runtime-verified: FIFO order (`PyQueue`), LIFO order (`PyLifoQueue`), and
`full()` on a bounded queue — all matched expected CPython `queue`
semantics.

## `base64`

`b64encode(data: bytes) -> str`/`b64decode(data: str) -> bytes`, built
directly on `RemObjects.Elements.RTL.Convert`'s already-implemented
`ToBase64String`/`Base64StringToByteArray` (a hand-rolled codec, no
native crypto library dependency) — no new algorithm needed at all, the
same way `re.py` needed none once RTL2 had a regex engine.

The real story here is what this module corrects: the survey's "no
bytes/binary-data type — blocked" finding was wrong the same way native
string manipulation, `re`, and reflection/dynamic typing were — assumed
blocked because untested, not because it's actually unavailable. `bytes`
is a real, already-implemented Promethium v1 language feature: `b'...'`
literals and the `bytes` type annotation both lower directly to the
target's native `Byte[]` array. A native byte array's length is its
`.Length` property (not `len(...)`, which has no `bytes` overload).

Signature deviates from CPython on purpose: CPython's `b64encode(bytes)
-> bytes` returns the base64 alphabet as ASCII *bytes*, which callers
almost always immediately `.decode('ascii')` into a `str` anyway — this
returns `str` directly and skips that redundant step, with the matching
shortcut on `b64decode`'s input.

`RemObjects.Elements.RTL.Convert` is always fully qualified: a bare
`Convert` risks the same inconsistent per-target resolution `time.py` hit
with a bare `DateTime`, and plausibly collides with the platform's own
BCL `System.Convert`, which has same-named `ToBase64String`/
`FromBase64String` methods of its own.

Runtime-verified against live CPython's `base64.b64encode`/`b64decode`:
encoded text and every decoded byte matched exactly.

## `binascii`

`hexlify(data: bytes) -> str`/`unhexlify(data: str) -> bytes`, built
directly on `RemObjects.Elements.RTL.Convert`'s `ToHexString`/
`HexStringToByteArray` — same story as `base64.py`: no new algorithm
needed, RTL2 already had it. Same deliberate `str`-not-`bytes` signature
deviation as `base64.py`, for the same reason (CPython's own `hexlify`
returns ASCII bytes that callers almost always immediately decode to
`str` anyway).

One real discrepancy caught by runtime comparison, not assumed:
`Convert.ToHexString` produces **uppercase** hex digits, while CPython's
`binascii.hexlify` produces lowercase — `hexlify` lowercases the result
to match, using the same native per-target `.ToLower()`/`.toLowerCase()`/
`.lowercaseString` idiom `string.py`'s `_lower` already established.
`unhexlify` accepts the lowercased text back fine (RTL2's parser isn't
case-sensitive on input).

Runtime-verified against live CPython's `binascii.hexlify`/`unhexlify`:
hex text and every decoded byte matched exactly.

Also `crc32(data: bytes) -> int` — the one function here that's a real
algorithm, not a `Convert` passthrough: the standard reflected bit-by-bit
CRC-32 (polynomial `0xEDB88320`, the same one CPython's `binascii.crc32`/
`zlib.crc32` both use), pure bit arithmetic, no native call, same
category as `struct.py`. Two things needed care for Promethium's signed
32-bit `int`: `0xFFFFFFFF` (the algorithm's initial/final all-ones value)
is spelled `-1` (same bit pattern, unambiguous regardless of signedness);
and the algorithm's per-bit right-shift must be *logical* (zero-fill),
but Promethium's `>>` on a negative value is arithmetic (sign-extending)
— corrected with a small `_logicalShiftRight1` helper that masks off bit
31 after the shift, the only bit an arithmetic and a logical single-bit
right-shift can ever disagree on. Returns the same bit pattern CPython's
unsigned result has, reinterpreted as signed — inputs whose CRC is `>=
0x80000000` read back as the equivalent negative `int`, same
representational limit `struct.py` already documents for
`unpack_uint32_*`. Runtime-verified against live CPython's
`binascii.crc32` across several inputs (empty, ASCII text, and raw bytes
including a value that exercises the negative-representation case) —
matched exactly, bit pattern for bit pattern.

## `codecs`

`encode(s, encoding="utf-8") -> bytes`/`decode(data, encoding="utf-8") ->
str`, UTF-8 only, built on `RemObjects.Elements.RTL.Encoding.UTF8`'s
already-implemented `GetBytes`/`GetString` — no new native call needed,
same story as `base64.py`/`binascii.py` reusing `Convert`. Closes the
loop on this session's "bytes/binary-data isn't blocked" correction:
`base64`/`binascii` convert between `bytes` and a textual representation
of those bytes; this is the piece that gets from an ordinary `str` to
`bytes` (UTF-8) and back. Only `"utf-8"` is accepted — CPython's `codecs`
supports dozens of encodings via a registry; any other name here raises
`Promethium.ValueError`.

Runtime-verified round-tripping real multi-byte UTF-8 (`café`'s `é`,
`[0xC3, 0xA9]`) byte-for-byte against CPython. Finding this needed
working around a **separate, genuine bug** first: a Promethium `.py`
source file mishandles non-ASCII characters typed *directly* into a
string literal — `"café"` written literally in source silently becomes
`caf?` by runtime, even though the source file's own bytes on disk are
valid UTF-8 (confirmed by inspecting them directly — not an editor/save
encoding problem, something in how the compiler reads non-ASCII source
text). Not a bug in this module, `bytes`, or RTL2's `Encoding` — a
`bytes` literal built from `\xNN` hex escapes (`b"caf\xc3\xa9"`) round-
trips through `decode`/`encode` perfectly; only literal non-ASCII
characters typed directly into Promethium source are affected. Worth
knowing for any future module that wants non-ASCII text in its own test
cases or literals.

## `struct`

`pack_uint8`/`unpack_uint8`, `pack_uint16_le`/`_be` +
`unpack_uint16_le`/`_be`, `pack_uint32_le`/`_be` + `unpack_uint32_le`/
`_be` — fixed-width integer packing, both byte orders. CPython's actual
API is a single `pack(fmt, *values)`/`unpack(fmt, data)` pair driven by a
format string and variadic arguments; that's not reproducible here since
`*args`/`**kwargs` are outside this language slice entirely. Named
per-width, per-byte-order functions instead, matching this project's
established "one CPython generic function becomes several concrete ones"
pattern (`heapq`/`bisect`/`statistics`'s int/float/str overloads).

Pure bit arithmetic — no native call of any kind, same as `datetime.py`'s
proleptic-Gregorian day math. Building a `bytes` value of a specific size
needed its own small discovery: `bytes` concatenation (`b"\x01" +
b"\x02"`) doesn't compile ("cannot find operator to evaluate `<array
literal>` + `<array literal>`"), but a fixed-size `bytes` literal's
individual elements *can* be assigned after construction (`data: bytes =
b"\x00\x00"; data[0] = 1`) — confirmed working and used throughout as the
allocation idiom.

Named `uint8`/`uint16`/`uint32` (CPython's `B`/`H`/`I` format codes), but
Promethium's `int` is signed 32-bit — unpacking 4 bytes whose top bit is
set produces the same bit pattern a signed 32-bit `int` would have, which
reads back negative rather than as a value `>= 0x80000000`. A
representational limit, not a bug (same class of thing `ipaddress.py`/
`uuid.py` already document) — `pack_*`/`unpack_*` are exact inverses of
each other regardless, round-tripping any 32-bit bit pattern losslessly
even when the signed *meaning* differs from what a real `uint32` would
say.

No float packing (`f`/`d` format codes) in this pass — needs a native
bit-reinterpretation call not attempted here, a scope cut not an
oversight.

Runtime-verified against live CPython's `struct.pack`/`unpack`: `uint8`,
`uint16` both byte orders, `uint32` both byte orders — every byte and
every round-tripped value matched exactly.

## `hashlib`

`md5(data: bytes) -> bytes` (16-byte digest) / `md5_hexdigest(data:
bytes) -> str`, and `sha256(data: bytes) -> bytes` (32-byte digest) /
`sha256_hexdigest(data: bytes) -> str`. Full hand-rolled implementations
of RFC 1321 (MD5) and FIPS 180-4 (SHA-256) — no cross-platform hash
primitive was found anywhere in RTL2 (only a Toffee-only `CC_SHA1`
TLS-certificate-fingerprint helper, not reusable), the same situation
`re.py` was in before RTL2 got a regex engine as a side task. This is
that side task done in pure Promethium instead: no native call anywhere
in the file, only bit arithmetic, same category as `struct.py`/
`binascii.py`'s `crc32`.

Both algorithms needed the same two Promethium-specific problems solved:

- **No dynamically-sized `bytes` allocation exists** (`bytes(n)` isn't a
  valid constructor — see `struct.py`'s notes). Both hashes need to work
  over a *padded* message whose length depends on the input, which would
  ordinarily need a runtime-allocated padded buffer. Sidestepped with a
  virtual-byte function per algorithm (`_virtualByte` for MD5,
  `_sha256VirtualByte` for SHA-256— separate because SHA-256 packs bytes
  **big-endian** and appends its bit-length field big-endian, the mirror
  image of MD5's little-endian): computes what byte *would* be at any
  position of the conceptually-padded message (the real input, the
  single `0x80` marker, zero padding, or the trailing 8-byte bit-length
  field) without ever materializing the padded buffer — only the
  original `data` and a fixed-size digest buffer are ever actually
  allocated. Each takes a `prefix`/`suffix` buffer pair rather than a
  single buffer, so `md5()`/`sha256()` can hash the *logical*
  concatenation of two buffers without ever materializing a combined
  one — `md5(data)`/`sha256(data)` are just `_md5Core(data, data.Length,
  data, 0)`/`_sha256Core(data, data.Length, data, 0)` (an unused
  zero-length suffix); this exists so `hmac.py` can build `(key XOR pad)
  || message` without a `bytes` concatenation operator, which still
  doesn't exist.
- **Promethium's `int` is signed 32-bit with an arithmetic `>>`**, but
  both algorithms need a logical right shift (MD5's left-rotate is half
  of one; SHA-256 uses both a rotate and a plain logical shift directly).
  `_logicalShiftRight` generalizes the single-bit trick `crc32` already
  established (`(value >> 1) & 0x7FFFFFFF` is unconditionally correct for
  one bit, since that's the only bit an arithmetic and logical shift-by-1
  can ever disagree on) by simply repeating it; `_rotr32` (SHA-256's
  right-rotate) is just `_rotl32(value, 32 - amount)`. Bitwise NOT is
  `value ^ -1`. 32-bit addition wraps silently on overflow — confirmed
  directly (`2147483647 + 1` produces `-2147483648`, no exception) —
  exactly the modular arithmetic both compression functions need.

Both only support inputs whose *bit* length fits in 32 bits (message
length under ~268MB) — a curated-scope limit, not a correctness gap for
realistic input sizes.

`md5`/`md5_hexdigest` runtime-verified against all seven of RFC 1321's
own official MD5 test vectors; `sha256`/`sha256_hexdigest` against four
of NIST's own SHA-256 test vectors (including two multi-block messages).
Both cross-checked against live CPython's `hashlib.md5`/`hashlib.sha256`
on the same inputs — every digest matched exactly (SHA-256 matched on
the first attempt; MD5 needed one real bug found and fixed:
`_sTable()`'s construction interleaved all four 4-shift groups on each of
four outer loop passes instead of repeating each group four times before
moving to the next — a loop-nesting mistake, not a bit-arithmetic one).

## `hmac`

`hmac_md5(key: bytes, message: bytes) -> bytes` / `hmac_md5_hexdigest`,
and `hmac_sha256(key: bytes, message: bytes) -> bytes` /
`hmac_sha256_hexdigest`, built entirely on `hashlib`'s hand-rolled MD5/
SHA-256 via their `_md5Core`/`_sha256Core` two-buffer primitives. RFC
2104's algorithm: `H((K' XOR opad) || H((K' XOR ipad) || message))`,
where `K'` is the key zero-padded to the hash's 64-byte block size (both
MD5 and SHA-256 share that block size), or hashed down (to 16 bytes for
MD5, 32 for SHA-256) then zero-padded, if the key is longer than 64
bytes. `_keyBlockMd5`/`_keyBlockSha256` are near-identical but kept
separate rather than parameterized over which hash to call — a
named-function-as-value only works as a lambda here, not a plain
function reference, so passing `hashlib.md5`/`hashlib.sha256` in wasn't
a safe bet to make per-target.

Runtime-verified against cases drawn from RFC 2202's official HMAC test
vectors — a short key/message, the empty key and empty message, a short
key ("Jefe") with a longer message, and (the case that actually exercises
the hash-down path) an 80-byte key with a plain-text message — for both
HMAC-MD5 and HMAC-SHA256, cross-checked against live CPython's
`hmac.new(key, msg, hashlib.md5 / hashlib.sha256).hexdigest()`; every
digest matched exactly. Also re-verified `hashlib.md5`/`hashlib.sha256`
themselves still produce correct digests after being generalized into
two-buffer cores — the refactor changed no observable behavior for the
single-buffer case.

## `heapq`

A binary min-heap, stored directly in a `Promethium.List` — an array-backed
heap over an existing list, exactly like CPython's own `Lib/heapq.py`, not a
separate class.

Every function here is overloaded for `int`/`float`/`str` rather than
generic over `T`, for the same reason `PromethiumBaseLibrary`'s own
`sorted()`/`min()`/`max()` are (see `Counter`'s note above): unconstrained
generic `T` has no `<` operator in Promethium, and there's no established,
tested `[T: IComparable]`-style constraint pattern to fall back on either
(confirmed: the parser supports generic type-parameter bounds, but nothing
in `PromethiumBaseLibrary` or this project uses them — adopting that now
would mean pioneering an untested compiler path, not following precedent).

Two Promethium quirks surfaced while writing this module, one of them
since fixed:

- **`List`'s bracket-write indexer wasn't reliably usable at the time**:
  one target rejected direct heap-slot writes with "Default indexer on
  type ... is read-only", because `PromethiumBaseLibrary.List` didn't
  declare `__setitem__` yet. This module originally worked around it with
  a small `_set(...)` helper doing `pop(index)` + `insert(index, value)`,
  used far more heavily here than in `Counter.py`/`OrderedDict.py`/
  `DefaultDict.py` since a single heap sift can overwrite many slots.
  **`List` has since gained a real `__setitem__`**, so this now uses plain
  `heap[position] = value` directly — the `_set` helper is gone, and every
  sift function was re-verified against the same test cases it already
  had.
- **A concrete (non-generic) function like `sorted(values: List[int])`
  isn't reachable as a bare call from another module via `DefaultUses`
  alone** — unlike `len`, which resolves ambiently everywhere in this
  project. `from Promethium import sorted` doesn't work either (`from X
  import name` only binds *types* — confirmed by the compiler then reading
  `sorted` as a type, not a function, and failing with "Unknown type"
  instead). The only combination that compiled was calling it fully
  qualified as `Promethium.sorted(values)`, which is what `nsmallest`/
  `nlargest` do internally.

That last point also shapes how *consumers* of `heapq`/`bisect` need to
import them: `from heapq import heappush` does **not** work, for the same
reason (`heappush` is a function, not a type). Add `heapq`/`bisect` to the
consuming project's `DefaultUses` instead (e.g. `<DefaultUses>Promethium;
Promethium.PythonCompatibility;heapq;bisect</DefaultUses>`) and call them as
bare names — verified working end-to-end this way in a scratch consumer
project, alongside `from collections import ...`'s already-working
type-import style for the classes above.

Supported, and runtime-verified against CPython's own output for every
function: `heappush`, `heappop`, `heapreplace`, `heappushpop`, `heapify`,
`nsmallest(n, values)`, `nlargest(n, values)`.

## `bisect`

Binary search / sorted-insertion helpers over a `Promethium.List`, also
overloaded for `int`/`float`/`str` only, for the same reason as `heapq`
above.

Python's `bisect_left(a, x, lo=0, hi=None)` has no direct equivalent for
`hi=None` here — `hi` is a plain `int` parameter, and Promethium has no
nullable-int default to spell "unspecified" with — so `-1` is used as the
"search to the end of the list" sentinel instead, the same kind of concrete
stand-in `DefaultDict`'s `get`/`pop` already use for CPython's `None`
defaults elsewhere in this project.

Supported, and runtime-verified against CPython's own output: `bisect_left`,
`bisect_right`, `bisect` (alias for `bisect_right`, matching CPython),
`insort_left`, `insort_right`, `insort` (alias for `insort_right`).

## `unittest`

A curated core, not the full framework: `TestCase` with `assertEqual`/
`assertNotEqual` (overloaded for `int`/`float`/`str`/`bool`, same
per-type-overload convention `heapq.py`/`bisect.py` use) plus
`assertTrue`/`assertFalse`, each *recording* a pass/fail rather than
raising — `passed`/`failed` counters, a `failures: List[str]` of
messages, and `summary() -> str`. Deliberately not exception-based, the
same "concrete stand-in, not exact parity" choice as `struct.py`'s
no-`*args` deviation.

`assertEqual`/`assertNotEqual` don't have a single `dynamic`-typed
overload covering every type, unlike `json.py`'s tagged-union approach —
equality between two `dynamic` values was never confirmed to lower
correctly (only *arithmetic* operators on `dynamic` were exercised, and
even those needed explicit class-level field annotations to avoid a real
multi-target bug — see the dynamic-typing notes), so this sticks to
known-safe per-type overloads instead of risking it.

Deliberately out of scope: `unittest.main()`'s auto-discovery — scanning
a `TestCase` subclass for `test_*`-prefixed methods and invoking each via
reflection. RTL2's `Reflection` namespace exists but has never been
exercised end-to-end in this project; getting method discovery *and*
dynamic invocation *and* per-test exception isolation all working across
15 targets is a much bigger lift than the assertion core, and tests here
are driven by hand instead — instantiate a `TestCase`, call its `assert*`
methods directly, check `summary()`/`failed`.

Writing this also confirmed a new instance of the `float(x)`/`int(x)`
conversion gap (see that memory note): `str(x)` isn't callable either,
same "Unknown identifier" failure on every target. Fixed the same way
`json.py`'s `_dumpFloat` already had to: string concatenation's `+`
stringifies a numeric/bool operand automatically once a string is
already on one side (`"expected " + expected` needs no wrapper at all;
only a bare leading numeric, as in `summary()`, needs the `"" + value`
empty-literal-prefix trick).

Runtime-verified: a passing case and a failing case for each of
`assertEqual`/`assertNotEqual`/`assertTrue`/`assertFalse` (eight checks
total, spanning `int`/`str` for the equality assertions) produced the
expected `5 passed, 5 failed` summary, correct `passed`/`failed` counts,
and the expected five failure messages verbatim.

## Build notes

Each module lives in its own top-level `.py` file at the project root and
carries its own `@namespace(...)` directive, all compiled into the single
`Promethium.PythonCompatibility` assembly. Multiple files sharing (or not
sharing) the same `@namespace` value compile together fine as long as each
file is itself free of errors — an earlier, incorrect diagnosis blamed a
"two files with @namespace" compiler limit for a failure that turned out to
be an unrelated real error whose diagnostics cascaded across files. Every
`.py` source file (`math.py`, `operator.py`, `Counter.py`, `OrderedDict.py`,
`ChainMap.py`, `Deque.py`, `DefaultDict.py`, `LenOverloads.py`, `heapq.py`,
`bisect.py`, `itertools.py`, `string.py`, `statistics.py`, `copy.py`,
`functools.py`, `random.py`, `fractions.py`, `graphlib.py`, `decimal.py`,
`cmath.py`, `datetime.py`, `calendar.py`, `ipaddress.py`, `colorsys.py`,
`uuid.py`, `textwrap.py`, `csv.py`, `configparser.py`, `difflib.py`,
`fnmatch.py`, `shlex.py`, `html.py`, `xml.py`, `re.py`, `json.py`,
`pprint.py`, `tomllib.py`, `time.py`, `queue.py`, `base64.py`,
`binascii.py`, `codecs.py`, `struct.py`, `hashlib.py`, `hmac.py`,
`PyByteArray.py`, `unittest.py`) is a single global
`<Compile Include="..." />` item compiled
for every target — including `DefaultDict.py`, whose Toffee-specific
limitation is handled inside the source itself (see its section above)
rather than by excluding the file from a target in the project. Per-target
`<ItemGroup Condition="...">` blocks in
`PromethiumPythonCompatibility.elements` exist only for actual build
references (`<Reference Include="Promethium">` and platform references),
never for source files.

All fifteen target configurations build clean from an empty cache:
`Echoes.Full`/`Echoes.Core`/`Echoes.Standard`, `Cooper`, all seven `Island.*`
targets, and all four `Toffee.*` targets, each with its own `<Reference
Include="Promethium">` pointing at the matching `PromethiumBaseLibrary`
build output (`.dll` for Echoes, `.jar` for Cooper, `.fx` for Island/Toffee).

Every target's `<Reference Include="Elements">` (`"libElements"` on
Toffee, `"elements"` on Cooper) now carries an explicit `HintPath` into
this checkout's `RTL2/Bin/<target>/...` build output, rather than
resolving ambiently. This matters beyond style: the ambient resolution
points at a *different*, older `Elements.dll` that doesn't contain
`RemObjects.Elements.RTL`'s real classes (`XmlDocument` and friends —
see `xml.py`'s notes) at all, so pinning the `HintPath` is what makes
that RTL actually reachable. `Toffee.macOS` — which previously had no
`libElements` reference at all, since there was no `libElements.fx`
shipped for plain macOS in the *ambient* reference paths — now has one,
because RTL2's own build output does ship a `Toffee/macOS/libElements.fx`.
Any project consuming the compiled `Promethium.PythonCompatibility`
assembly needs the exact same `HintPath` for its own `Elements` reference,
or the two won't agree on which physical assembly "Elements" is.

`DefaultUses` must include `Promethium` (needed for bare builtins like
`len(...)`, which none of `Counter.py`/`OrderedDict.py`/`ChainMap.py`/
`Deque.py`/`DefaultDict.py` import) and must *not* include
`RemObjects.Elements.RTL` — some environments expose an
`RemObjects.Elements.RTL.List`/`.Dictionary` that silently wins unqualified
`List`/`Dictionary` resolution over `Promethium.List`/`.Dictionary` when both
are ambiently open, which is why each of those files also imports `List`
(and `ChainMap.py` also `Dictionary`) explicitly rather than relying on
`DefaultUses` alone.

RTL2's own `Elements.RTL.Island.Android.elements` builds only the
`x86_64` ABI in its `Debug` configuration (`Release` builds all five —
`arm64-v8a;armeabi;armeabi-v7a;x86;x86_64` — but `armeabi` fails outright
against a modern Android SDK, "Unsupported architecture ('armeabi') for
Android 35", so `Release` isn't a usable workaround). This project's
`Island.Android` reference points at `arm64-v8a`, so a plain `Debug`
rebuild of RTL2 silently leaves that specific `.fx` stale — every *other*
target rebuilds fine, and the only symptom is `Regex`/whatever the new
type is showing up as "Unknown type" on `Island.Android` alone. Confirmed
via each target's intermediate build folder (`Debug/<Target>/`): 14 of 15
targets produced their final `.dll`/`.fx`/`.a`/`.lib`/`.jar`, and
`Island.Android`'s folder had nothing past `Caches/ResolveReferences.cache`
— i.e. it never got past reference resolution. Fixed by temporarily adding
`arm64-v8a` to that one project file's `Debug` `<Architecture>` list,
rebuilding, then reverting the project file (the architecture list itself
wasn't meant to change — only that one rebuild needed to happen). Any
future RTL2 change that needs to reach `Island.Android` in this project
should rebuild RTL2 the same way (or use this same temporary-widen-then-
revert trick), not assume `--configuration:Debug` alone covers it.

This milestone intentionally excludes platform bindings, filesystem or process
APIs, automatic built-in overrides, and modules with complex Python runtime
semantics. Future modules should remain individually importable and preserve
that explicit opt-in boundary.
