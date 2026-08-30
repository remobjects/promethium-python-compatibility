@namespace("asyncio")

from Promethium import ValueError

# A curated corner of `asyncio`, not the module — this project's own
# scope statement excludes filesystem/process APIs, and a real event
# loop with I/O multiplexing (`asyncio`'s actual reason for existing) is
# squarely in that territory. What's here corrects a different, narrower
# "blocked" assumption: whether Python's `async def`/`await` *syntax*
# works in Promethium at all.
#
# It does — this was taken straight from `PROMETHIUM_IMPLEMENTATION_PLAN
# .md`'s exclusion list ("...generators... are outside the initial
# slice") the same way `yield` was, and turned out just as wrong. Direct
# test: `async def addAsync(a: int, b: int) -> int: return a + b` compiles
# clean across all 15 targets, and calling it immediately returns a real
# `System.Threading.Tasks.Task<int>` on Echoes (confirmed by printing the
# value's type name before ever touching it) — genuine Task-based async,
# the same mechanism C#/Oxygene use, not a stub. `await` correctly works
# *inside* another `async def` (`await addAsync(2, 3)` inside a second
# `async def computeAsync() -> int:` chain resolved to `5` at runtime) —
# but, matching Python's own rule, `await` is rejected outside an `async
# def` ("await is only allowed inside async def").
#
# That last rule is the actual gap this module exists to bridge: Python
# code (and this library's own callers) routinely wants to call an async
# function and block for its result from *ordinary*, non-async code —
# the same role CPython's `asyncio.run(coro())` plays. `run_int`/`run_str`
# /`run_float`/`run_bool` do exactly that, reading the already-completed-
# or-still-running task's result (a genuine synchronous blocking wait, not
# a busy-loop). They're separate concrete functions, not overloads of one
# `run`, and not a single generic `run[T]` — a generic version was tried
# and abandoned: `task`'s own type is necessarily untyped/`dynamic` (no
# confirmed way to spell "a Task of statically-unknown T" as a parameter
# type), so a generic `run[T](task) -> T`'s `T` never appears in any
# parameter, only the return position — the exact same "Generic parameter
# T for this method call could not fully be resolved" gap `itertools.py`'s
# abandoned `starmap` already documents.
#
# The member used to read the result is genuinely per-target, discovered
# by testing and reading the RTL source, not assumed: Echoes/Island's
# task is a real .NET `System.Threading.Tasks.Task<T>`, read via
# `.Result`. Cooper's task is `RemObjects.Elements.System.
# TaskCompletionSourceTask<T>` (confirmed by printing the value's runtime
# class name) — a *different*, Elements-internal class, not a raw Java
# `Future`. It does **not** expose a dynamically-accessible `.Result`
# property at all — first attempt crashed with `DynamicInvokeException:
# No element with this name: Result`, and a guessed `.get()` (matching
# `java.util.concurrent.Future`) crashed too (`No element with this name:
# get`) — neither guess was right. Reading `com.remobjects.elements.rtl/
# Source/Task.pas` directly settled it: the Oxygene source declares
# `property &Result: T read getResult` — Oxygene's `&` just escapes
# `Result` as an identifier (a reserved implicit-return-value keyword
# there), and the property compiles down to a real Java method literally
# named `getResult()`. Calling `.getResult()` explicitly (not `.Result`,
# which is how the *source* spells it but not how the compiled Java
# class exposes it to dynamic dispatch) is what actually works. Toffee
# raises a clear `ValueError` instead of misbehaving — an untyped
# parameter erases to Objective-C `id` there, which doesn't expose any of
# these spellings.
#
# Deviates from CPython's `asyncio.run(coro())` on purpose: CPython's
# coroutine objects are lazy (nothing runs until the event loop drives
# them); calling a Promethium `async def` function starts it running
# immediately and returns an already-in-flight task, so `run_int(...)` is
# a blocking wait on a task already underway, not the start of a lazy
# computation — a real semantic difference worth knowing, not just a
# naming one.
#
# Runtime-verified on both Echoes and Cooper with the same cross-assembly
# shape: `run_int(computeAsync())` — where `computeAsync` itself `await`s
# a nested `async def addAsync(2, 3)`, both defined in a separate consumer
# project, not this library — returns `5` on both, correctly resolving a
# two-level async chain through a synchronous caller compiled against
# this library as a dependency. Not yet tested on Island or Toffee
# (Toffee raises by design; Island's task is presumably `.Result`-shaped
# like Echoes but unconfirmed).


def run_int(task) -> int:
    if defined("ECHOES") or defined("ISLAND"):
        return task.Result
    elif defined("COOPER"):
        return task.getResult()
    else:
        raise ValueError("asyncio.run_int cannot read the task result on Toffee yet")


def run_str(task) -> str:
    if defined("ECHOES") or defined("ISLAND"):
        return task.Result
    elif defined("COOPER"):
        return task.getResult()
    else:
        raise ValueError("asyncio.run_str cannot read the task result on Toffee yet")


def run_float(task) -> float:
    if defined("ECHOES") or defined("ISLAND"):
        return task.Result
    elif defined("COOPER"):
        return task.getResult()
    else:
        raise ValueError("asyncio.run_float cannot read the task result on Toffee yet")


def run_bool(task) -> bool:
    if defined("ECHOES") or defined("ISLAND"):
        return task.Result
    elif defined("COOPER"):
        return task.getResult()
    else:
        raise ValueError("asyncio.run_bool cannot read the task result on Toffee yet")
