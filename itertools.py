@namespace("itertools")

from Promethium import List, ValueError


# A small subset of Python's itertools module. Most functions here return
# a fully-materialized `List` instead of a lazy iterator (the same eager
# choice PromethiumBaseLibrary's own `range()` makes) — this was originally
# because "Promethium generators are outside the initial language slice
# (per PROMETHIUM_IMPLEMENTATION_PLAN.md)", a claim taken from that doc
# without testing it, which turned out to be stale: a direct probe found
# real, genuinely lazy `yield`-based generator support (confirmed with an
# infinite generator that returned immediately and stopped cleanly after 5
# items via `break` — not eagerly buffered), and reading the actual
# Promethium parser source confirmed this is deliberate, purpose-built
# support (a real `yield` keyword token, `ParseYield`, `yield from`
# desugaring, `MethodFlags.Iterator`) plugged into the same shared
# iterator-lowering machinery Oxygene/C# use, with genuine per-backend
# codegen (`FixCooper`/`FixEchoes`/`FixNougat` for Toffee) — not an
# Echoes-only accident. `PROMETHIUM_V1_GRAMMAR.md`, a later and
# authoritative doc, confirms statement-form `yield`/`yield from` generators
# are in scope. `count`/`cycle` below are real generators on the strength of
# this — genuinely infinite, no `List` materialization at all. Every other
# function here stays eager; there was no reason to revisit them.
#
# **Was confirmed broken on Cooper and Toffee, now fixed upstream and
# re-verified.** A *consumer*'s use of a value drawn from a cross-assembly
# generator (a generator defined in one compiled library, like `count`/
# `cycle` here, consumed from a separate project — the normal way library
# code gets used) used to fail: on Cooper, using the value in an expression
# failed to compile with an empty inferred type, and passing it to a
# dynamic call like `print(x)` crashed at runtime with a
# `ClassCastException`; on Toffee (all four sub-targets), the same
# expression usage failed to compile with an `Int32`/`NSDecimalNumber`
# mismatch. Root cause: the parser was committing an unresolved `for`-loop
# item to `dynamic` instead of recovering `T` from the generator's
# `IEnumerable<T>`-shaped metadata, and Cooper's generated iterator classes
# were erasing their generic `Iterable<T>`/`Iterator<T>` signature across
# assembly boundaries. Fixed upstream and independently re-verified here:
# a full 15-target compile-only sweep of the original failing pattern shows
# zero errors (Toffee's compile-time symptom is gone), and a real two-jar
# Cooper build (`itertools.py` compiled separately from a consumer, exactly
# this cross-assembly shape) now runs `count(10, 5)`/`cycle(names)`
# correctly end to end, matching CPython exactly. `count`/`cycle` are fully
# usable on all four backends today.
#
# Predicate-taking functions (`takewhile`, `dropwhile`, `filterfalse`)
# *are* attempted, below, correcting this file's own earlier note that
# there was "no confirmed, tested way to type a callable/predicate
# parameter in this codebase" — `functools.reduce` already proved
# otherwise by the time this was revisited: an untyped `func` parameter
# (the compiler infers it as `dynamic`) plus `.Invoke(...)` works on
# Echoes/Island/Cooper, just not Toffee (an untyped parameter erases to
# Objective-C `id` there, whose block-invocation surface doesn't expose a
# matching `invoke` overload — confirmed, not assumed, by `functools.py`).
# Each predicate-taking function here follows `functools.reduce`'s exact
# pattern: raise a clear `ValueError` on Toffee instead of silently
# misbehaving, and use `.Invoke(...)` everywhere else.
#
# All three are typed for `int` specifically, not generic over `T`, for a
# newly-discovered reason beyond the Toffee limitation: combining a
# *generic* type parameter with an untyped/`dynamic` callable parameter
# that gets `.Invoke()`d produces a genuine runtime crash on Echoes —
# confirmed with an isolated probe (two near-identical functions, one
# generic over `T` and one concrete over `int`, otherwise byte-for-byte
# the same body): the concrete version ran correctly, the generic version
# compiled clean but threw `System.BadImageFormatException: An attempt
# was made to load a program with an incorrect format` at the very first
# call, every time. `functools.reduce` never hit this because it was
# never generic in the first place. Not yet reported as a formal repro to
# the compiler team.
#
# `starmap` was attempted and abandoned separately: its generic return
# type `V` only ever appears in the function's *return* position, never
# in a parameter, so the compiler can't infer it from a call site
# ("Generic parameter V for this method call could not fully be
# resolved") — and there's no confirmed syntax in this language slice for
# supplying generic type arguments explicitly at a *function* call site
# the way `List[int]()` supplies them for a *constructor* call
# (`starmap[int, int, int](...)` itself fails to parse: "Unknown
# identifier 'int'").
#
# `pairwise`/`batched` need no predicate at all, stay generic over `T`,
# and work on every target.
#
# Most functions here are fully generic over `T` — they only rearrange or
# copy elements, never compare or hash them, so they don't run into the
# "no `<`/`==` on unconstrained T" wall documented in `heapq.py`/`bisect.py`.
# Only `accumulate` needs arithmetic and is overloaded for `int`/`float`
# like `Builtins.py`'s own `sum()`.
#
# `permutations`/`combinations`/`combinations_with_replacement` compute
# purely over index arrays (`List[int]`) in a set of private, deliberately
# *non-generic* recursive helpers, then map the resulting index lists to `T`
# values in a separate, non-recursive pass. This two-phase split exists
# because of a real compiler limitation: a *generic* function calling
# itself recursively fails with "Generic parameter T for this method call
# could not fully be resolved" — confirmed by writing the natural one-phase
# generic-recursive version first and hitting that error on every recursive
# call site, then confirming the error disappears once the recursion is
# moved into non-generic helpers instead. This is a different limitation
# from the (now-fixed) generic-*class*-self-reference issue documented in
# `Counter.py` — that one was about a generic class referencing its own
# type in a method signature; this one is about a generic function calling
# itself by name, and remains unfixed as of this writing.
#
# `zip_longest` differs from CPython's signature: Python's single
# `fillvalue` (default `None`) can pad either side because Python is
# dynamically typed. With two independently-typed sequences (`T` and `U`),
# one shared fill value can't satisfy both slots' types statically, so this
# takes two fill values instead, one per side, matching `DefaultDict.get`'s
# already-proven `default: Value = None` pattern for a generic default.


def chain[T](a: List[T], b: List[T]) -> List[T]:
    result: List[T] = a.copy()
    result.extend(b)
    return result

def chain[T](a: List[T], b: List[T], c: List[T]) -> List[T]:
    result: List[T] = chain(a, b)
    result.extend(c)
    return result


def repeat[T](value: T, times: int) -> List[T]:
    result: List[T] = List[T]()
    count: int = 0
    while count < times:
        result.append(value)
        count += 1
    return result


def repeat[T](value: T):
    while True:
        yield value


def islice[T](values: List[T], stop: int) -> List[T]:
    return islice(values, 0, stop)

def islice[T](values: List[T], start: int, stop: int) -> List[T]:
    result: List[T] = List[T]()
    index: int = start
    limit: int = stop
    if limit > len(values):
        limit = len(values)
    while index < limit:
        result.append(values.__getitem__(index))
        index += 1
    return result


def compress[T](data: List[T], selectors: List[bool]) -> List[T]:
    result: List[T] = List[T]()
    limit: int = len(data)
    if len(selectors) < limit:
        limit = len(selectors)
    index: int = 0
    while index < limit:
        if selectors.__getitem__(index):
            result.append(data.__getitem__(index))
        index += 1
    return result


def accumulate(values: List[int]) -> List[int]:
    result: List[int] = List[int]()
    total: int = 0
    index: int = 0
    while index < len(values):
        total += values.__getitem__(index)
        result.append(total)
        index += 1
    return result

def accumulate(values: List[float]) -> List[float]:
    result: List[float] = List[float]()
    total: float = 0.0
    index: int = 0
    while index < len(values):
        total += values.__getitem__(index)
        result.append(total)
        index += 1
    return result


def product[T, U](a: List[T], b: List[U]) -> List[tuple[T, U]]:
    result: List[tuple[T, U]] = List[tuple[T, U]]()
    i: int = 0
    while i < len(a):
        left: T = a.__getitem__(i)
        j: int = 0
        while j < len(b):
            result.append((left, b.__getitem__(j)))
            j += 1
        i += 1
    return result


def _collectCombinations(n: int, r: int, start: int, current: List[int], result: List[List[int]]):
    if len(current) == r:
        result.append(current.copy())
        return
    index: int = start
    while index < n:
        current.append(index)
        _collectCombinations(n, r, index + 1, current, result)
        current.pop()
        index += 1

def _indexCombinations(n: int, r: int) -> List[List[int]]:
    result: List[List[int]] = List[List[int]]()
    if r < 0 or r > n:
        return result
    current: List[int] = List[int]()
    _collectCombinations(n, r, 0, current, result)
    return result


def _collectCombinationsWithReplacement(n: int, r: int, start: int, current: List[int], result: List[List[int]]):
    if len(current) == r:
        result.append(current.copy())
        return
    index: int = start
    while index < n:
        current.append(index)
        _collectCombinationsWithReplacement(n, r, index, current, result)
        current.pop()
        index += 1

def _indexCombinationsWithReplacement(n: int, r: int) -> List[List[int]]:
    result: List[List[int]] = List[List[int]]()
    if r < 0:
        return result
    if r > 0 and n == 0:
        return result
    current: List[int] = List[int]()
    _collectCombinationsWithReplacement(n, r, 0, current, result)
    return result


def _collectPermutations(n: int, r: int, used: List[bool], current: List[int], result: List[List[int]]):
    if len(current) == r:
        result.append(current.copy())
        return
    index: int = 0
    while index < n:
        if not used.__getitem__(index):
            used[index] = True
            current.append(index)
            _collectPermutations(n, r, used, current, result)
            current.pop()
            used[index] = False
        index += 1

def _indexPermutations(n: int, r: int) -> List[List[int]]:
    result: List[List[int]] = List[List[int]]()
    if r < 0 or r > n:
        return result
    used: List[bool] = List[bool]()
    index: int = 0
    while index < n:
        used.append(False)
        index += 1
    current: List[int] = List[int]()
    _collectPermutations(n, r, used, current, result)
    return result


def _materialize[T](values: List[T], indexSets: List[List[int]]) -> List[List[T]]:
    result: List[List[T]] = List[List[T]]()
    i: int = 0
    while i < len(indexSets):
        indices: List[int] = indexSets.__getitem__(i)
        combo: List[T] = List[T]()
        k: int = 0
        while k < len(indices):
            combo.append(values.__getitem__(indices.__getitem__(k)))
            k += 1
        result.append(combo)
        i += 1
    return result


def permutations[T](values: List[T]) -> List[List[T]]:
    return permutations(values, len(values))

def permutations[T](values: List[T], r: int) -> List[List[T]]:
    return _materialize(values, _indexPermutations(len(values), r))


def combinations[T](values: List[T], r: int) -> List[List[T]]:
    return _materialize(values, _indexCombinations(len(values), r))


def combinations_with_replacement[T](values: List[T], r: int) -> List[List[T]]:
    return _materialize(values, _indexCombinationsWithReplacement(len(values), r))


def zip_longest[T, U](a: List[T], b: List[U], fillA: T = None, fillB: U = None) -> List[tuple[T, U]]:
    result: List[tuple[T, U]] = List[tuple[T, U]]()
    length: int = len(a)
    if len(b) > length:
        length = len(b)
    index: int = 0
    while index < length:
        left: T = fillA
        if index < len(a):
            left = a.__getitem__(index)
        right: U = fillB
        if index < len(b):
            right = b.__getitem__(index)
        result.append((left, right))
        index += 1
    return result


def pairwise[T](values: List[T]) -> List[tuple[T, T]]:
    result: List[tuple[T, T]] = List[tuple[T, T]]()
    i: int = 0
    n: int = len(values)
    while i + 1 < n:
        result.append((values.__getitem__(i), values.__getitem__(i + 1)))
        i += 1
    return result


def batched[T](values: List[T], n: int) -> List[List[T]]:
    result: List[List[T]] = List[List[T]]()
    i: int = 0
    total: int = len(values)
    while i < total:
        batch: List[T] = List[T]()
        j: int = 0
        while j < n and i + j < total:
            batch.append(values.__getitem__(i + j))
            j += 1
        result.append(batch)
        i += n
    return result


def takewhile(pred, values: List[int]) -> List[int]:
    if defined("TOFFEE"):
        raise ValueError("itertools.takewhile cannot invoke its predicate on Toffee yet")
    else:
        result: List[int] = List[int]()
        i: int = 0
        n: int = len(values)
        while i < n:
            item: int = values.__getitem__(i)
            keep: bool = pred.Invoke(item)
            if not keep:
                break
            result.append(item)
            i += 1
        return result


def dropwhile(pred, values: List[int]) -> List[int]:
    if defined("TOFFEE"):
        raise ValueError("itertools.dropwhile cannot invoke its predicate on Toffee yet")
    else:
        result: List[int] = List[int]()
        i: int = 0
        n: int = len(values)
        dropping: bool = True
        while i < n:
            item: int = values.__getitem__(i)
            if dropping:
                keep: bool = pred.Invoke(item)
                if keep:
                    i += 1
                    continue
                dropping = False
            result.append(item)
            i += 1
        return result


def filterfalse(pred, values: List[int]) -> List[int]:
    if defined("TOFFEE"):
        raise ValueError("itertools.filterfalse cannot invoke its predicate on Toffee yet")
    else:
        result: List[int] = List[int]()
        i: int = 0
        n: int = len(values)
        while i < n:
            item: int = values.__getitem__(i)
            keep: bool = pred.Invoke(item)
            if not keep:
                result.append(item)
            i += 1
        return result


# Real generators, genuinely infinite — see this file's header for why
# these were previously skipped as "no eager equivalent" and why that
# turned out to be wrong. No predicate/callable parameter is involved in
# either, so neither hits the separate generic-type-parameter +
# `.Invoke()` crash `takewhile`/`dropwhile`/`filterfalse` above avoid by
# staying concrete — `cycle` is generic over `T` and was specifically
# verified not to hit that crash (it doesn't call `.Invoke()` on
# anything, so the two preconditions for that bug never both apply).

def count(start: int, step: int):
    n: int = start
    while True:
        yield n
        n += step


def cycle[T](values: List[T]):
    while True:
        i: int = 0
        n: int = len(values)
        while i < n:
            yield values.__getitem__(i)
            i += 1