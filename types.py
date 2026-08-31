@namespace("types")

from Promethium import List, ValueError

# CPython's `types` module is mostly runtime-type objects for isinstance
# checks against things a statically-typed language never has loose
# handles on in the first place (`FunctionType`, `ModuleType`,
# `GeneratorType`, `new_class`/`resolve_bases` for metaclass machinery).
# None of that has a meaningful analog here. The one genuinely useful,
# commonly-reached-for piece is `SimpleNamespace` — a plain mutable
# attribute bag, often used as a cheap stand-in for a dataclass or as a
# return value bundling a few named results.
#
# A faithful port would back it with a single `name -> value` mapping of
# heterogeneous value types, but that needs exactly the two things this
# project has already found broken: `Dictionary` has no working external
# mutation path (`Dictionary.update(Dictionary)` throws at runtime, and it
# declares no `__setitem__` of its own — see the note in `ChainMap.py`),
# and a single heterogeneous value slot would need `dynamic`/`typing.Any`
# storage, which is the same shape of thing behind this pass's static-
# method-plus-dynamic-argument bug (see
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`).
#
# So this `SimpleNamespace` is backed by four parallel name/value `List`
# pairs, one per supported concrete type (int/str/float/bool) — `List`
# mutation (`append`, `__setitem__`) is solid, unlike `Dictionary`'s.
# Lookup is a linear scan, fine for the small attribute counts this is
# meant for. The one real deviation from CPython: insertion order is
# preserved *within* each type group, not across all of them combined —
# `ns.set_int("a", 1); ns.set_str("b", "x"); ns.set_int("c", 2)` prints
# `a`/`c` before `b`, not in call order, since each type has its own list.


class SimpleNamespace:
    _int_names: List[str]
    _int_values: List[int]
    _str_names: List[str]
    _str_values: List[str]
    _float_names: List[str]
    _float_values: List[float]
    _bool_names: List[str]
    _bool_values: List[bool]

    def __init__(self):
        self._int_names = List[str]()
        self._int_values = List[int]()
        self._str_names = List[str]()
        self._str_values = List[str]()
        self._float_names = List[str]()
        self._float_values = List[float]()
        self._bool_names = List[str]()
        self._bool_values = List[bool]()

    def _find(self, names: List[str], name: str) -> int:
        i: int = 0
        while i < len(names):
            if names.__getitem__(i) == name:
                return i
            i += 1
        return -1

    def set_int(self, name: str, value: int):
        idx: int = self._find(self._int_names, name)
        if idx >= 0:
            self._int_values.__setitem__(idx, value)
        else:
            self._int_names.append(name)
            self._int_values.append(value)

    def get_int(self, name: str) -> int:
        idx: int = self._find(self._int_names, name)
        if idx < 0:
            raise ValueError("SimpleNamespace has no int attribute '" + name + "'")
        return self._int_values.__getitem__(idx)

    def has_int(self, name: str) -> bool:
        return self._find(self._int_names, name) >= 0

    def set_str(self, name: str, value: str):
        idx: int = self._find(self._str_names, name)
        if idx >= 0:
            self._str_values.__setitem__(idx, value)
        else:
            self._str_names.append(name)
            self._str_values.append(value)

    def get_str(self, name: str) -> str:
        idx: int = self._find(self._str_names, name)
        if idx < 0:
            raise ValueError("SimpleNamespace has no str attribute '" + name + "'")
        return self._str_values.__getitem__(idx)

    def has_str(self, name: str) -> bool:
        return self._find(self._str_names, name) >= 0

    def set_float(self, name: str, value: float):
        idx: int = self._find(self._float_names, name)
        if idx >= 0:
            self._float_values.__setitem__(idx, value)
        else:
            self._float_names.append(name)
            self._float_values.append(value)

    def get_float(self, name: str) -> float:
        idx: int = self._find(self._float_names, name)
        if idx < 0:
            raise ValueError("SimpleNamespace has no float attribute '" + name + "'")
        return self._float_values.__getitem__(idx)

    def has_float(self, name: str) -> bool:
        return self._find(self._float_names, name) >= 0

    def set_bool(self, name: str, value: bool):
        idx: int = self._find(self._bool_names, name)
        if idx >= 0:
            self._bool_values.__setitem__(idx, value)
        else:
            self._bool_names.append(name)
            self._bool_values.append(value)

    def get_bool(self, name: str) -> bool:
        idx: int = self._find(self._bool_names, name)
        if idx < 0:
            raise ValueError("SimpleNamespace has no bool attribute '" + name + "'")
        return self._bool_values.__getitem__(idx)

    def has_bool(self, name: str) -> bool:
        return self._find(self._bool_names, name) >= 0

    def __str__(self) -> str:
        result: str = "namespace("
        first: bool = True
        i: int = 0
        while i < len(self._int_names):
            if not first:
                result = result + ", "
            result = result + self._int_names.__getitem__(i) + "=" + ("" + self._int_values.__getitem__(i))
            first = False
            i += 1
        i = 0
        while i < len(self._str_names):
            if not first:
                result = result + ", "
            result = result + self._str_names.__getitem__(i) + "='" + self._str_values.__getitem__(i) + "'"
            first = False
            i += 1
        i = 0
        while i < len(self._float_names):
            if not first:
                result = result + ", "
            result = result + self._float_names.__getitem__(i) + "=" + ("" + self._float_values.__getitem__(i))
            first = False
            i += 1
        i = 0
        while i < len(self._bool_names):
            if not first:
                result = result + ", "
            boolText: str = "False"
            if self._bool_values.__getitem__(i):
                boolText = "True"
            result = result + self._bool_names.__getitem__(i) + "=" + boolText
            first = False
            i += 1
        return result + ")"
