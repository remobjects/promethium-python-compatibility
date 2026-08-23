# Promethium Python Compatibility

This library provides optional, source-level compatibility modules for
Promethium projects that are being ported from Python. Nothing is enabled by
default: a project opts in by referencing this library and importing the
required module.

The `math` module declares `@namespace("math")`, so consumers use the normal
Python-shaped `import math` spelling rather than the project implementation
namespace. Its initial portable surface is `fabs` and `isnan`.

## `operator`

A small, target-neutral subset of Python's `operator` API: integer and
floating-point arithmetic, primitive ordering comparisons, integer/float/
boolean equality, and boolean negation. It uses only Promethium language
operators, so the same source can be built for Echoes, Cooper, Island, and
Toffee.

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
`in`).

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

## Build notes

Each module lives in its own top-level `.py` file at the project root and
carries its own `@namespace(...)` directive, all compiled into the single
`Promethium.PythonCompatibility` assembly. Multiple files sharing (or not
sharing) the same `@namespace` value compile together fine as long as each
file is itself free of errors — an earlier, incorrect diagnosis blamed a
"two files with @namespace" compiler limit for a failure that turned out to
be an unrelated real error whose diagnostics cascaded across files. Every
`.py` source file (`math.py`, `operator.py`, `Counter.py`, `OrderedDict.py`,
`ChainMap.py`, `Deque.py`, `DefaultDict.py`, `LenOverloads.py`) is a single
global `<Compile Include="..." />` item compiled for every target — including
`DefaultDict.py`, whose Toffee-specific limitation is handled inside the
source itself (see its section above) rather than by excluding the file from
a target in the project. Per-target `<ItemGroup Condition="...">` blocks in
`PromethiumPythonCompatibility.elements` exist only for actual build
references (`<Reference Include="Promethium">` and platform references),
never for source files.

All fifteen target configurations build clean from an empty cache:
`Echoes.Full`/`Echoes.Core`/`Echoes.Standard`, `Cooper`, all seven `Island.*`
targets, and all four `Toffee.*` targets, each with its own `<Reference
Include="Promethium">` pointing at the matching `PromethiumBaseLibrary`
build output (`.dll` for Echoes, `.jar` for Cooper, `.fx` for Island/Toffee).
`Toffee.macOS` intentionally has no `libElements` reference — unlike
`Toffee.iOS`/`tvOS`/`watchOS`, there is no `libElements.fx` shipped for
plain macOS in the reference paths, and `PromethiumBaseLibrary` itself
builds for that exact target without one.

`DefaultUses` must include `Promethium` (needed for bare builtins like
`len(...)`, which none of `Counter.py`/`OrderedDict.py`/`ChainMap.py`/
`Deque.py`/`DefaultDict.py` import) and must *not* include
`RemObjects.Elements.RTL` — some environments expose an
`RemObjects.Elements.RTL.List`/`.Dictionary` that silently wins unqualified
`List`/`Dictionary` resolution over `Promethium.List`/`.Dictionary` when both
are ambiently open, which is why each of those files also imports `List`
(and `ChainMap.py` also `Dictionary`) explicitly rather than relying on
`DefaultUses` alone.

This milestone intentionally excludes platform bindings, filesystem or process
APIs, automatic built-in overrides, and modules with complex Python runtime
semantics. Future modules should remain individually importable and preserve
that explicit opt-in boundary.
