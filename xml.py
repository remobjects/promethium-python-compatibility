@namespace("xml")

from Promethium import List
from collections import OrderedDict

# A small, opt-in subset of Python's xml module (the shape of
# `xml.etree.ElementTree`, not its actual namespace): `parse(text) ->
# XmlTreeNode`. Internally backed by `RemObjects.Elements.RTL.XmlDocument`
# — a real, hand-written, cross-platform XML parser that already ships
# with the Elements RTL (`RTL2/Source/RemObjects.Elements.RTL/
# XmlDocument.pas`/`XmlParser.pas`/`XmlTokenizer.pas`), rather than the
# hand-rolled character-scanning parser this file used at first. Reusing
# it gets real namespace/CDATA/comment/entity handling for free instead of
# this project's own scoped-down approximations.
#
# Getting here needed two things beyond just importing something:
#
# 1. **A reference-wiring fix, not a language feature.** `RemObjects.
#    Elements.RTL` (this RTL2 checkout) builds its own `Elements.dll`/
#    `.fx`/`.jar` under `RTL2/Bin/<target>/...`, distinct from the
#    "Elements" reference this project already had bare (no `HintPath`) in
#    every per-target `ItemGroup` — which resolves ambiently to a
#    *different*, older `Elements.dll` build that doesn't contain this RTL
#    at all. Adding an explicit `HintPath` to each `Reference
#    Include="Elements"`/`"libElements"`/`"elements"` block, pointing at
#    the matching RTL2 build output per target, is what actually brings
#    `RemObjects.Elements.RTL.XmlDocument` into scope — see this project's
#    `.elements` file for the exact paths. Any consumer of this compiled
#    `Promethium.PythonCompatibility` assembly (like the scratch demo used
#    to verify this) needs the *same* `Elements` HintPath wired in too, or
#    the two won't agree on which physical assembly "Elements" is.
# 2. **Toffee's `for x in someRtlSequence:` erases `x` to a dynamic `id`**,
#    the same generics-erasure behavior documented elsewhere in this
#    project (see `DefaultDict`'s factory notes) — losing every property
#    on the real type (`x.LocalName` fails with "No member 'LocalName' on
#    type 'id'", and even the lowercase Cocoa spelling doesn't help; the
#    member is inaccessible on `id` entirely, not just misnamed).
#    Re-declaring the loop variable with an explicit type annotation as
#    the very first statement inside the loop body (`child:
#    RemObjects.Elements.RTL.XmlElement = rawChild`) recovers the static
#    type and fixes it — cheaper than avoiding the `for`/`in` loop shape
#    entirely.
#
# `.text` is the *simpler* semantic of the two documented in the earlier
# hand-rolled version's design notes: `XmlElement.Value` (what this now
# calls) concatenates *all* nested text recursively, not just the text
# immediately following the start tag the way CPython's `ElementTree.text`
# does. A deliberate, documented difference rather than an attempt to
# reproduce `.tail`-less mixed-content semantics exactly.


class XmlTreeNode:
    tag: str
    attrib: OrderedDict[str, str]
    text: str
    children: List[XmlTreeNode]

    def __init__(self, tag: str):
        self.tag = tag
        self.attrib = OrderedDict[str, str]()
        self.text = ""
        self.children = List[XmlTreeNode]()

    def findall(self, tag: str) -> List[XmlTreeNode]:
        result: List[XmlTreeNode] = List[XmlTreeNode]()
        index: int = 0
        while index < len(self.children):
            child: XmlTreeNode = self.children.__getitem__(index)
            if child.tag == tag:
                result.append(child)
            index += 1
        return result


def parse(text: str) -> XmlTreeNode:
    doc: RemObjects.Elements.RTL.XmlDocument = RemObjects.Elements.RTL.XmlDocument.FromString(text)
    return _convert(doc.Root)


def _convert(source: RemObjects.Elements.RTL.XmlElement) -> XmlTreeNode:
    node: XmlTreeNode = XmlTreeNode(source.LocalName)
    for rawAttr in source.Attributes:
        attr: RemObjects.Elements.RTL.XmlAttribute = rawAttr
        node.attrib[attr.LocalName] = attr.Value
    value: str = source.Value
    if value is not None:
        node.text = value
    for rawChild in source.Elements:
        child: RemObjects.Elements.RTL.XmlElement = rawChild
        node.children.append(_convert(child))
    return node
