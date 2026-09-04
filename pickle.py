@namespace("pickle")

from Promethium import List

# CPython draws a real distinction between `marshal` (an internal,
# version-specific format the docs explicitly warn against using for
# anything but `.pyc` files / cross-process trust boundaries you control)
# and `pickle` (the general-purpose serializer users actually reach for,
# including for collections — `pickle.dumps([1, 2, 3])` is completely
# ordinary code; `marshal.dumps([1, 2, 3])` is not something real code is
# meant to do). This module reflects that same split: `dumps_int`/
# `dumps_bool`/`dumps_str` are thin wrappers straight through to
# `marshal.py`'s identical functions (same format, no reason to
# duplicate the bytes) — the actual value pickle adds here is
# `dumps_list_int`/`loads_list_int`, since serializing a collection is
# the thing people use `pickle` for far more than the scalar case.
#
# `dumps_list_int` format: `struct.pack_uint32_le(count)` followed by
# `count` 4-byte little-endian integers, no per-item type tag — a flat
# `List[int]` only, no heterogeneous or nested collections.
#
# `dumps_object`/`loads_object` — added after revisiting the "no
# object-graph walker" scope cut above. Uses
# `RemObjects.Elements.RTL.Reflection` (`Type.TypeOf`, `.Fields`/
# `.MethodFields`, `Field.GetValue`/`SetValue`, `Type.Instantiate`) to
# serialize an arbitrary object's `int`/`str`/`bool` fields (not `float`
# — see below) by name, and reconstruct a new instance of the same type
# from those bytes elsewhere. Works on **Echoes, Island, and Cooper** —
# the earlier assumption that this
# needed "exactly the `dynamic`-typed single entry point this project has
# been avoiding" turned out to be imprecise: the actual crash (see
# `promethium_reflection_static_dynamic_bug_and_cooper_pattern.md`) only
# triggers on Cooper when the *caller's own value* has static type
# `dynamic`/`typing.Any` at the call site — an ordinary call like
# `pickle.dumps_object(myPoint)` where `myPoint: Point` never hits it,
# since `Point` widening to the `object`-typed parameter is a normal,
# non-dynamic reference conversion. A caller that genuinely holds the
# value as `typing.Any` needs one extra step first: assign it to an
# `object`-typed local (`casted: object = anyValue`) before passing it in
# — that local assignment is what changes the argument's static type away
# from `dynamic`, and this is now the confirmed, verified workaround (not
# a guess) for the cross-assembly-dynamic-argument bug.
#
# **Toffee now works too.** `RemObjects.Elements.RTL.Reflection.Type.
# Get_Fields` used to be `raise new NotImplementedException("Reflection
# for Fields is not implemented yet for Cocoa")` in RTL2's own source — a
# real gap in RTL2 itself, not a Promethium compiler bug. That's fixed
# upstream now (`class_copyIvarList`/`ivar_getName`/`ivar_getTypeEncoding`
# — real Objective-C ivar introspection, migrated into this project's
# RTL2 checkout and verified with a real Toffee executable: field
# enumeration, get/set by name, and a parameterless-constructor
# `Instantiate()` round-trip all confirmed correct). Getting a genuinely
# fresh build to actually *link* took real work: Toffee static-library
# linking on this host doesn't reliably use whichever `libElements.a` is
# referenced via `HintPath`/`ProjectReference` — `lld` was still pulling
# in the toolchain's separate *ambient* reference copy regardless,
# confirmed directly by `strings`-searching the built binary for should-
# be-gone text from the old, unfixed code. Not a Promethium or RTL2
# defect — a `lld` quirk on this host, per the person who actually
# maintains this toolchain.
#
# No `float` field support: unlike `int`/`str`/`bool` (whose "is this
# object of type X" check is a plain `Type.Name` string compare —
# `"Int32"` on Echoes/Island, `"Integer"` on Cooper for the int case;
# `"String"`/`"Boolean"` match on both), reading a `float` back out of its
# boxed `object` form needs a native bit-reinterpretation call that
# `marshal.py` already scoped out for the same reason — not attempted
# here either, for consistency. A `float` field raises a clear `ValueError`
# naming the field, not a silent wrong value.
#
# `loads_object(data, template)` takes a `template: object` — an
# already-constructed, throwaway instance of the target type
# (`pickle.loads_object(data, Point())`) — rather than a type-name
# string, and reconstructs from that type. This isn't a stylistic choice:
# `RemObjects.Elements.RTL.Reflection.Type.GetType(name: string)` (which
# looks up a type from its name alone) only searches the calling
# assembly plus the platform's own base library — since `loads_object`
# runs inside this compiled library, it could never find a type defined
# in whatever *consumer* project calls it, no matter how the name was
# spelled (confirmed: `Activator.CreateInstance` threw
# `ArgumentNullException` because `GetType` silently returned `null` for
# a real, correctly-named consumer-defined class). Requiring a live
# `template` object instead sidesteps that entirely — `Type.TypeOf
# (template)` always carries full assembly binding, since it comes from
# an actual object reference, not a name string. `dumps_object` still
# writes the type's `FullName` into the data, used only as a sanity
# check on load (`loads_object` raises `ValueError` if `template`'s type
# doesn't match what was pickled) — not for lookup.
#
# `Type.Instantiate()` reconstructs a new, blank instance of the pickled
# type (`template`'s type, not `template` itself) — this requires the
# target class to have a parameterless constructor (`Type.Instantiate`
# calls exactly that, per-target: `Activator.CreateInstance`/
# `getDeclaredConstructor().newInstance()`/`mapped.Instantiate()`), a
# real, documented requirement any class being round-tripped through
# `dumps_object`/`loads_object` must satisfy — not a limitation unique to
# this project (most reflection-based serializers, in any language, need
# the same).
#
# `copyreg` still has nothing to register against here and stays
# unshipped: its purpose is letting a *specific class* override how it
# gets pickled, but `dumps_object`/`loads_object` use one fixed,
# reflection-driven strategy for every object — there is no per-class
# hook in that design for `copyreg` to plug into.
#
# Verified: `dumps_list_int([1, 2, 3])` / `loads_list_int(...)` round-
# trips exactly; `dumps_int`/`dumps_bool`/`dumps_str` produce byte-for-
# byte identical output to the equivalent `marshal.py` call (they're the
# same call); `dumps_object`/`loads_object` round-trip a plain class with
# `int`/`str`/`bool` fields correctly on both Echoes (`dotnet exec`) and
# Cooper (a real two-jar JVM build/run, not taken on faith) — re-dumping
# the reconstructed instance produces byte-identical output to the
# original.


def dumps_int(value: int) -> bytes:
    return marshal.dumps_int(value)


def loads_int(data: bytes) -> int:
    return marshal.loads_int(data)


def dumps_bool(value: bool) -> bytes:
    return marshal.dumps_bool(value)


def loads_bool(data: bytes) -> bool:
    return marshal.loads_bool(data)


def dumps_str(value: str) -> bytes:
    return marshal.dumps_str(value)


def loads_str(data: bytes) -> str:
    return marshal.loads_str(data)


def dumps_list_int(values: List[int]) -> bytes:
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    count: int = len(values)
    buf.Write(struct.pack_uint32_le(count))
    i: int = 0
    while i < count:
        buf.Write(struct.pack_uint32_le(values.__getitem__(i)))
        i += 1
    return buf.ToArray()


def loads_list_int(data: bytes) -> List[int]:
    result: List[int] = List[int]()
    count: int = struct.unpack_uint32_le(marshal._extractBytes(data, 0, 4))
    pos: int = 4
    i: int = 0
    while i < count:
        result.append(struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4)))
        pos += 4
        i += 1
    return result


def _fieldsOf(reflType: RemObjects.Elements.RTL.Reflection.Type) -> RemObjects.Elements.RTL.ImmutableList[RemObjects.Elements.RTL.Reflection.Field]:
    if defined("COOPER"):
        return reflType.MethodFields
    else:
        return reflType.Fields


def _getFieldValue(fld: RemObjects.Elements.RTL.Reflection.Field, obj: object) -> object:
    if defined("COOPER"):
        return fld.GetValue(obj, None)
    else:
        return fld.GetValue(obj)


def _setFieldValue(fld: RemObjects.Elements.RTL.Reflection.Field, instance: object, value: object):
    if defined("COOPER"):
        fld.SetValue(instance, None, value)
    else:
        fld.SetValue(instance, value)


def dumps_object(obj: object) -> bytes:
    reflType: RemObjects.Elements.RTL.Reflection.Type = RemObjects.Elements.RTL.Reflection.Type.TypeOf(obj)
    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()

    typeNameBytes: bytes = codecs.encode(reflType.FullName)
    buf.Write(struct.pack_uint32_le(typeNameBytes.Length))
    buf.Write(typeNameBytes)

    fields: RemObjects.Elements.RTL.ImmutableList[RemObjects.Elements.RTL.Reflection.Field] = _fieldsOf(reflType)
    buf.Write(struct.pack_uint32_le(fields.Count))

    fi: int = 0
    while fi < fields.Count:
        fld: RemObjects.Elements.RTL.Reflection.Field = fields.__getitem__(fi)
        nameBytes: bytes = codecs.encode(fld.Name)
        buf.Write(struct.pack_uint32_le(nameBytes.Length))
        buf.Write(nameBytes)

        val: object = _getFieldValue(fld, obj)
        valTypeName: str = RemObjects.Elements.RTL.Reflection.Type.TypeOf(val).Name

        if valTypeName == "Int32" or valTypeName == "Integer":
            buf.Write(b"\x00")
            buf.Write(struct.pack_uint32_le(Integer(val)))
        elif valTypeName == "String" or valTypeName == "NSCFString" or valTypeName == "NSTaggedPointerString" or valTypeName == "__NSCFConstantString":
            buf.Write(b"\x01")
            strVal: str = ""
            if defined("TOFFEE"):
                strVal = val.description
            else:
                strVal = val.ToString()
            strBytes: bytes = codecs.encode(strVal)
            buf.Write(struct.pack_uint32_le(strBytes.Length))
            buf.Write(strBytes)
        elif valTypeName == "Boolean" or valTypeName == "__NSCFBoolean":
            buf.Write(b"\x02")
            boolByte: bytes = b"\x00"
            if Boolean(val):
                boolByte[0] = 1
            buf.Write(boolByte)
        elif valTypeName == "Double" or valTypeName == "Single":
            raise ValueError("pickle.dumps_object: field '" + fld.Name + "' is a float, which isn't supported yet (needs a native bit-reinterpretation call, same scope cut as marshal.py)")
        else:
            raise ValueError("pickle.dumps_object: field '" + fld.Name + "' has unsupported type '" + valTypeName + "'")
        fi += 1

    return buf.ToArray()


def loads_object(data: bytes, template: object) -> object:
    pos: int = 0
    typeNameLen: int = struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4))
    pos += 4
    typeName: str = codecs.decode(marshal._extractBytes(data, pos, typeNameLen))
    pos += typeNameLen

    reflType: RemObjects.Elements.RTL.Reflection.Type = RemObjects.Elements.RTL.Reflection.Type.TypeOf(template)
    if reflType.FullName != typeName:
        raise ValueError("pickle.loads_object: data was pickled from type '" + typeName + "' but template is a '" + reflType.FullName + "'")
    newInstance: object = reflType.Instantiate()
    fields: RemObjects.Elements.RTL.ImmutableList[RemObjects.Elements.RTL.Reflection.Field] = _fieldsOf(reflType)

    fieldCount: int = struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4))
    pos += 4

    fi: int = 0
    while fi < fieldCount:
        nameLen: int = struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4))
        pos += 4
        fieldName: str = codecs.decode(marshal._extractBytes(data, pos, nameLen))
        pos += nameLen

        tag: int = data[pos]
        pos += 1

        val: object
        if tag == 0:
            intVal: int = struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4))
            pos += 4
            val = intVal
        elif tag == 1:
            strLen: int = struct.unpack_uint32_le(marshal._extractBytes(data, pos, 4))
            pos += 4
            strVal: str = codecs.decode(marshal._extractBytes(data, pos, strLen))
            pos += strLen
            val = strVal
        elif tag == 2:
            boolVal: bool = data[pos] != 0
            pos += 1
            val = boolVal
        else:
            raise ValueError("pickle.loads_object: unknown field type tag for field '" + fieldName + "'")

        targetField: RemObjects.Elements.RTL.Reflection.Field = None
        fj: int = 0
        while fj < fields.Count:
            candidate: RemObjects.Elements.RTL.Reflection.Field = fields.__getitem__(fj)
            if candidate.Name == fieldName:
                targetField = candidate
                break
            fj += 1
        if targetField == None:
            raise ValueError("pickle.loads_object: type '" + typeName + "' has no field named '" + fieldName + "'")
        _setFieldValue(targetField, newInstance, val)

        fi += 1

    return newInstance
