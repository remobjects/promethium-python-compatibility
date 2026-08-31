@namespace("abc")

# CPython's `abc` module has two moving parts: `ABCMeta` (a metaclass that
# enforces, at *instantiation* time, that every method marked
# `@abstractmethod` got overridden — raising `TypeError` otherwise) and
# the `@abstractmethod` decorator itself. Decorators are not supported in
# Promethium user code (see the stdlib survey's "No decorators" finding —
# same wall `functools.wraps`/`dataclasses`/`contextlib` hit), so there is
# no way to port `@abstractmethod`'s actual enforcement behavior. This was
# originally filed under "confirmed unblocked by dynamic/Reflection" on
# the assumption Reflection could substitute for the decorator — it
# can't: `@abstractmethod` doesn't need to *inspect* anything at
# instantiation time, it needs a decorator to exist as a language
# feature, and nothing found this pass changes that.
#
# What already works today, with zero library support beyond one small
# gap, is the idiom Python itself used for "abstract" methods for years
# before `abc` existed: give the base method a body that raises
# `NotImplementedError`. The gap: `NotImplementedError` is a CPython
# *builtin*, not part of the real `abc` module, and Promethium has no
# built-in exception hierarchy at all beyond `Promethium.ValueError`/
# `Promethium.KeyError` (both plain `Exception` subclasses with no
# `__init__` override of their own — see `PromethiumBaseLibrary/
# Exceptions.py`). `class Shape: def area(self): raise
# NotImplementedError(...)` fails to compile ("Unknown identifier
# 'NotImplementedError'") without it. Defining it here, in `abc`, is a
# pragmatic bend of scope — it's the one place in the standard library
# whose entire reason for existing is this idiom — rather than adding a
# new builtin-exceptions module nobody asked for.
#
#   class Shape:
#       def area(self) -> float:
#           raise NotImplementedError("Shape.area must be overridden")
#
# `ABC` is nothing more than a documented, empty marker base class
# matching `abc.ABC`'s name and spelling, useful only for signaling
# intent at the class-declaration site (`class Shape(ABC):`) — it does
# **not**, and cannot, enforce anything at instantiation time the way
# CPython's `ABCMeta` does. Compiles clean and is safe to inherit from on
# every target since it has no members at all, but callers should not
# expect `TypeError` at instantiation for an unoverridden method the way
# CPython gives them — only the `raise NotImplementedError` idiom itself
# provides any enforcement here, and only when the method is actually
# called, not when the object is created.
#
# Verified: a `Shape(ABC)` base with `area()` raising `NotImplementedError`,
# and a `Circle(Shape)` subclass overriding it, both compile and run
# correctly — `Circle(2.0).area()` returns the overridden computation, not
# the exception.


class ABC:
    pass


class NotImplementedError(Exception):
    pass
