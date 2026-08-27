@namespace("unittest")

from Promethium import List


# A curated core of CPython's `unittest`: `TestCase` with typed
# `assertEqual`/`assertTrue`/`assertFalse`/`assertNotEqual`, each
# recording a pass/fail rather than raising (no exception-based test
# framework here — matches this project's existing "concrete stand-in,
# not exact parity" pattern, e.g. `struct.py`'s no-`*args` deviation).
# `assertEqual`/`assertNotEqual` are overloaded per type (`int`/`float`/
# `str`/`bool`) rather than one `dynamic`-typed version — equality
# between two `dynamic` values was never confirmed to lower correctly
# (only arithmetic operators on `dynamic` were exercised, and *those* hit
# a real multi-target bug before class-level field annotations fixed it —
# see the dynamic-typing notes), so this sticks to the same per-type
# overload convention `heapq.py`/`bisect.py` already use rather than risk
# it.
#
# Deliberately out of scope: `unittest.main()`'s auto-discovery (scanning
# a `TestCase` subclass for `test_*`-prefixed methods and invoking each
# via reflection) — RTL2's `Reflection` namespace exists but has never
# been exercised end-to-end in this project, and getting method discovery
# *and* dynamic invocation *and* per-test exception isolation all working
# across 15 targets is a much bigger lift than the assertion core itself.
# Tests are driven by hand here: instantiate a `TestCase`, call its
# `assert*` methods directly, then check `summary()`/`failed`.
#
# Runtime-verified: a passing case and a failing case for each of
# `assertEqual`/`assertNotEqual`/`assertTrue`/`assertFalse` (eight checks
# total) all produced the expected pass/fail counts and the expected
# `summary()` string.


class TestCase:
    passed: int
    failed: int
    failures: List[str]

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = List[str]()

    def _recordPass(self):
        self.passed += 1

    def _recordFail(self, message: str):
        self.failed += 1
        self.failures.append(message)

    def assertEqual(self, actual: int, expected: int):
        if actual == expected:
            self._recordPass()
        else:
            self._recordFail("assertEqual failed: expected " + expected + ", got " + actual)

    def assertEqual(self, actual: float, expected: float):
        if actual == expected:
            self._recordPass()
        else:
            self._recordFail("assertEqual failed: expected " + expected + ", got " + actual)

    def assertEqual(self, actual: str, expected: str):
        if actual == expected:
            self._recordPass()
        else:
            self._recordFail("assertEqual failed: expected " + expected + ", got " + actual)

    def assertEqual(self, actual: bool, expected: bool):
        if actual == expected:
            self._recordPass()
        else:
            self._recordFail("assertEqual failed: expected " + expected + ", got " + actual)

    def assertNotEqual(self, actual: int, expected: int):
        if actual != expected:
            self._recordPass()
        else:
            self._recordFail("assertNotEqual failed: both were " + actual)

    def assertNotEqual(self, actual: float, expected: float):
        if actual != expected:
            self._recordPass()
        else:
            self._recordFail("assertNotEqual failed: both were " + actual)

    def assertNotEqual(self, actual: str, expected: str):
        if actual != expected:
            self._recordPass()
        else:
            self._recordFail("assertNotEqual failed: both were " + actual)

    def assertTrue(self, value: bool):
        if value:
            self._recordPass()
        else:
            self._recordFail("assertTrue failed: value was False")

    def assertFalse(self, value: bool):
        if not value:
            self._recordPass()
        else:
            self._recordFail("assertFalse failed: value was True")

    def summary(self) -> str:
        return "" + self.passed + " passed, " + self.failed + " failed"
