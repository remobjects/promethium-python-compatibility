@namespace("inspect")

from Promethium import ValueError

# A tiny, curated corner of `inspect`: `get_type_name(obj) -> str`, the
# equivalent of CPython's `type(obj).__name__`. Not a real port of the
# module — CPython's `inspect` is built around introspecting CPython's
# own bytecode/frame objects (`getsource`, `getframeinfo`, parameter
# `Signature` details), none of which has an analog once compiled to a
# different backend. What carries over is the much narrower, genuinely
# useful question: given a `dynamic`-held value, what's its real runtime
# type?
#
# Built on the reflection/dynamic-typing correction confirmed earlier
# this session — `typing.Any` really does lower to a genuine `dynamic`
# type, late-bound and validated at call time. The *obvious* way to ask
# for a value's type — `RemObjects.Elements.RTL.Reflection.Type.
# TypeOf(obj)`, a static method call with a `dynamic` argument — turned
# out to be a **new, real compiler bug**, not a naming mistake: even
# fully qualified, and even through an explicit `from ... import Type as
# ReflectionType` alias, calling `ReflectionType.TypeOf(obj)` crashed at
# runtime on Echoes with `RemObjects.Elements.Dynamic.
# OxygeneBinderException: No methods called "TypeOf" defined on
# "System.Type"` — the dynamic call site resolved to the *wrong* type
# (the ambient BCL `System.Type`, which shares a short name) despite the
# source unambiguously specifying `RemObjects.Elements.RTL.Reflection.
# Type` every way this project knows how to say it. The alias doesn't
# help because this is a *runtime* dynamic-dispatch bug, not a
# compile-time name-resolution one.
#
# The working alternative: an *instance* method call on the dynamic
# object itself (`obj.GetType()` on Echoes/Island) rather than a static
# method call taking the object as an argument — the same shape of
# dynamic dispatch `functools.reduce`'s `.Invoke()` already uses
# successfully, not the shape that crashed here. Per-target, discovered
# by testing: Echoes/Island use `.GetType().Name` (a real .NET
# `System.Type.Name`); Cooper's `.getClass()` — a zero-argument instance
# call, nothing dynamic passed *into* it — still crashes with the exact
# same `ClassCastException`-in-`DynamicHelpers.FindBestMatch` signature
# already seen for dynamic dispatch on generator values and async task
# objects, strongly suggesting one systemic Cooper dynamic-dispatch
# fragility rather than three unrelated bugs; not yet reported as a
# formal repro. Toffee not attempted (an untyped parameter erases to
# `id` there, the same limitation this project hits repeatedly).
#
# Runtime-verified on Echoes: `get_type_name(Point(3, 4))` → `"Point"`,
# `get_type_name(5)` → `"Int32"`, `get_type_name("hello")` → `"String"` —
# a user-defined class and two built-ins, all correct.


def get_type_name(obj) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return obj.GetType().Name
    else:
        raise ValueError("inspect.get_type_name is only confirmed working on Echoes/Island so far — Cooper hits a dynamic-dispatch crash, Toffee erases the parameter to id")
