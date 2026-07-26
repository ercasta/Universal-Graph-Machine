"""THE ASSEMBLY JOURNAL — the assembler's decisions as DATA (§27).

§8 says a dynamically-wired system **cannot be statically checked, so the trace is the only thing there is
to inspect** — and then left the assembler, the part that does the dynamic wiring, entirely outside the
trace. §22.1 named the fix (*the assembler's decisions become events on the trace wire*) and §26 supplied
the missing half by making trace-consuming units assemblable.

**What this closes, and it is the failure mode that matters for intake** (measured, §27.1): a form can be
accepted, become a well-formed template, and **never be wired — silently**. `wellformed()` stays clean and
the budget is untouched. That is [[book-corpus-experiment]]'s *"partial intake systematically drops
exceptions"* one layer lower: the parse succeeded and the assembler quietly declined. Its mirror (§24.7's
spurious instance that can never fire) was equally silent. Both are now facts.

**OBSERVABLE, NOT WRITABLE** (§20.4, §22.1). The journal is a RECORD. Nothing here lets a unit wire
anything, and §8's line is untouched: units still never touch wiring. A unit may *read* why a wire exists
exactly as it may read why a conclusion holds.

**These are PROVENANCE, not content** (§23.2's test: *"which fact a handle denotes"* is content, *"how it
came about"* is provenance). *How the NETWORK came about* is the same kind of thing as how a conclusion
came about, so journal predicates join `FIRING_PREDICATES` — which means §26.1's stratification guard
covers them for free, and an ordinary unit still cannot see them.
"""
from __future__ import annotations

from .value import Fact, Node, Subgraph
from .vocab import role

SPAWNED = role("<spawned>")       # instance handle -> the template it instantiates
WIRE_FROM = role("<wire_from>")   # wire -> producer handle
WIRE_TO = role("<wire_to>")       # wire -> consumer handle
WIRE_KIND = role("<wire_kind>")   # wire -> <object> | <trace>
DECLINED = role("<declined>")     # wire -> why it was refused
UNUSED = role("<unused>")         # template -> <never_wired>

OBJECT_WIRE = role("<object>")
TRACE_WIRE = role("<trace>")
NEVER_WIRED = role("<never_wired>")

# Reasons. Each is a decision the assembler already makes and, until now, made invisibly.
CYCLE = role("<would_cycle>")
BYPASS = role("<would_bypass>")
SEEN = role("<nothing_new>")
STRATIFIED = role("<stratified>")
SHAPE = role("<no_shape_match>")  # THE COMPUTED INDEX refused it (§28): the producer emits the predicate
#                                   the template reads and no fact of it could satisfy any ATOM. §24.7's
#                                   dead instance, now a recorded refusal instead of a spawned unit.

JOURNAL_PREDICATES = frozenset({SPAWNED, WIRE_FROM, WIRE_TO, WIRE_KIND, DECLINED, UNUSED})

_B = 1 << 32


def template_node(name: str) -> Node:
    """A stable node for a template. Derived from the template's position in the LIBRARY, which is the
    assembler's own namespace — not from discourse, so no name-luck reaches the data graph (§21.2)."""
    return Node(-(_B * 7 + (abs(hash(name)) % _B)), name)


def wire_node(producer: Node, consumer: Node, kind: Node) -> Node:
    """A wire's identity is a function of its endpoints — **keyed, not minted**, or re-running the
    assembler would emit a different journal every pass and the fixpoint would die (§22.8's standing rule,
    reaching a fourth construct)."""
    z = lambda n: (n.nid << 1) if n.nid >= 0 else ((-n.nid << 1) | 1)   # noqa: E731
    return Node(-(((z(producer) * _B + z(consumer)) * _B + z(kind)) + 3), "w")


def spawned(inst_handle: Node, template: str) -> tuple:
    return (Fact(inst_handle, SPAWNED, template_node(template)),)


def wired(producer: Node, consumer: Node, trace: bool = False) -> tuple:
    kind = TRACE_WIRE if trace else OBJECT_WIRE
    w = wire_node(producer, consumer, kind)
    return (Fact(w, WIRE_FROM, producer), Fact(w, WIRE_TO, consumer), Fact(w, WIRE_KIND, kind))


def declined(producer: Node, consumer: Node, reason: Node, trace: bool = False) -> tuple:
    """**A REFUSAL IS A FACT.** The assembler already refuses cycles, bypasses and already-consumed
    projections; none of it was recorded, so *"what did you not consider?"* had no answer at all."""
    kind = TRACE_WIRE if trace else OBJECT_WIRE
    w = wire_node(producer, consumer, kind)
    return (Fact(w, WIRE_FROM, producer), Fact(w, WIRE_TO, consumer), Fact(w, DECLINED, reason))


def unused(template: str) -> tuple:
    """A template that was accepted and never instantiated — the silent intake failure (§27.1)."""
    return (Fact(template_node(template), UNUSED, NEVER_WIRED),)


def orphans(net) -> Subgraph:
    """Every template with no instances, as facts. Computed on demand rather than tracked, because it is
    a property of the whole library and only meaningful once assembly has quiesced."""
    return Subgraph(f for t, insts in net.instances.items() if not insts for f in unused(t))


__all__ = ["SPAWNED", "WIRE_FROM", "WIRE_TO", "WIRE_KIND", "DECLINED", "UNUSED",
           "OBJECT_WIRE", "TRACE_WIRE", "NEVER_WIRED", "CYCLE", "BYPASS", "SEEN", "STRATIFIED", "SHAPE",
           "JOURNAL_PREDICATES", "template_node", "wire_node",
           "spawned", "wired", "declined", "unused", "orphans"]
