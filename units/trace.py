"""THE TRACE NETWORK — provenance as a parallel, forward-built value (`substrate_inversion.md` §16.6, §20).

**§8's backward walk is WRONG, by this document's own §15.2.** It said `why` is a walk backward along the
wires. It is not, for three independent reasons, and each alone is fatal:

* a wire says what COULD have fed a unit, never what DID — the LHS decides, and a unit that woke and
  correctly wrote nothing is the case the cell-network spike found load-bearing;
* refire keeps only the LAST output, so the values the walk would read are not the ones that fired;
* §6b's late wiring means the topology at explanation time is not the topology at derivation time — so a
  backward walk can explain a derivation that never happened.

The replacement is the one §16.6 reasoned to: **a parallel, FORWARD-BUILT, APPEND-ONLY network over FIRING
EVENTS — one unit, many firings — carried on its OWN wire.** Same lesson as `Unit.derived` and
`last_firing`: *a derivation is a fact about a RUN*, so it is recorded when the run happens.

**THE TWO ACCRETIONS RUN IN OPPOSITE DIRECTIONS, AND THAT IS THE DESIGN, NOT AN INCONSISTENCY.**

    OBJECT wire — SUBSET output (§16). A rule emits only what it derived, so a non-firing unit is a real
                  gate and silence is a semantic act.
    TRACE  wire — APPEND-ONLY. A firing cites the firings that produced its premises, so the record must
                  carry forward. History does not gate; it accumulates.

Which is exactly why they must be SEPARATE WIRES. §16.6 states the constraint and this module obeys it:
**the trace must never accrete into the object value**, or §6a's exact-NAF-over-the-wire starts seeing
provenance facts and `Absent` begins answering questions about the derivation instead of about the world.
That is mechanically checkable — `Net.trace_leaks()` — and it is checked, in the same spirit as the
no-import rule: this is precisely the kind of thing that is right on paper and wrong in the build.

**THE FORM IS AN OPAQUE HANDLE** (§16.6). A firing names its unit through a minted node and nothing else.
The template's shape, its LHS, its form — none of it is reachable from the trace. Leak any of it and
`form_inventory.md` §4d's L0 escapes through the back door, which is the failure the constraint exists to
prevent.

**LIFETIME COLLAPSES INTO UNIT LIFETIME** (§16.6, and it turns §10.3's two questions into one). Keep the
last firing per unit, plus any firing still reachable from a kept one, plus a small supersession stub so
*"why did you change your mind?"* survives one generation. `prune` is that rule, applied at the unit, so
the bound travels with the value instead of being a property of a collector.
"""
from __future__ import annotations

from .reify import OF_O, OF_P, OF_S, handle_key, reify
from .value import EMPTY, Fact, Node, Subgraph, mint
from .vocab import role

# -- the vocabulary. Every trace predicate is bracketed, and `is_trace` is the leak check ---------------

# ROLE NODES, resolved through the form set once (§22.5). The trace vocabulary is roles like any other —
# which is the point: `is_trace` stays an identity test, and a unit reading firing events needs no new
# construct. Holding these as strings was a real defect for exactly one release: `prune` compared `f.p`
# (a node) against a string constant, silently kept nothing, and `why` degraded to None.
FIRED_BY = role("<fired_by>")    # firing  -> the unit's OPAQUE handle
CONCLUDED = role("<concluded>")  # firing  -> a conclusion handle
FROM = role("<from>")            # firing  -> a conclusion handle it CONSUMED as a premise
RETRACTED = role("<retracted>")  # firing  -> unit handle. The stub: "this no longer holds"

# ⭐ THE DESCRIPTION VOCABULARY IS `reify`'s, SHARED WITH THE OBJECT WIRE (§22.9) — corrected 2026-07-26.
# It used to be a private `<subject>/<predicate>/<object>`, and that split is what made degree
# inheritance unexpressible as a rule: a premise's band hung off a REIFY handle while a firing's `<from>`
# pointed at a TRACE handle, and the two denoted the same fact without being joinable.
#
# THE CORRECTION IS TO THE GUARD, NOT A WORKAROUND. Saying WHICH FACT a handle denotes is CONTENT; only
# *"firing F concluded c"* and *"F came from c'"* are provenance. So the leak check narrows to the FIRING
# vocabulary, and the description is shared. §16.6's constraint is unchanged in force — §6a's `Absent`
# must never see a derivation fact — it was simply drawn one predicate too wide.
SUBJECT, PREDICATE, OBJECT = OF_S, OF_P, OF_O           # kept as names; same nodes now

# §27: the assembler's own decisions are provenance too — *how the NETWORK came about* is the same kind
# of thing as how a conclusion came about — so they join this set and inherit §26.1's stratification.
from .journal import JOURNAL_PREDICATES                                            # noqa: E402
FIRING_PREDICATES = frozenset({FIRED_BY, CONCLUDED, FROM, RETRACTED}) | JOURNAL_PREDICATES
TRACE_PREDICATES = FIRING_PREDICATES | {OF_S, OF_P, OF_O}


def is_trace(f: Fact) -> bool:
    """**The LEAK test, and it is the FIRING vocabulary only** (§22.9). A description of which fact a
    handle denotes is content and may travel on the object wire; a derivation fact may not."""
    return f.p in FIRING_PREDICATES


# -- describing a conclusion ---------------------------------------------------------------------------

def describe(handle: Node, f: Fact) -> tuple:
    """The three facts that say *"`handle` is the conclusion `f`"*.

    Note all THREE slots are **the same node objects** the conclusion holds — identity inherited into the
    trace, not re-minted (§5). Since §22.5 the role is a node too, so the `<predicate>` slot needs no
    special construct: `value.sym`, and the name-equality carve-out it forced, are retired."""
    return (Fact(handle, OF_S, f.s), Fact(handle, OF_P, f.p), Fact(handle, OF_O, f.o))


def handle_index(trace: Subgraph) -> dict:
    """`(s, p, o) -> handle`, built ONCE for a value. `handle_of` is a linear scan, and calling it per
    premise made trace construction O(n^2) in the size of the value — measured, and it was the dominant
    cost on a wide net before this existed (§25.1)."""
    idx: dict = {}
    for t in trace.by_pred(OF_P):
        h = t.s
        s = next((x.o for x in trace.by_pred(OF_S) if x.s == h), None)
        o = next((x.o for x in trace.by_pred(OF_O) if x.s == h), None)
        if s is not None and o is not None:
            idx.setdefault((s, t.o, o), h)
    return idx


def handle_of(trace: Subgraph, f: Fact) -> Node | None:
    """Which conclusion handle in `trace` describes `f`? — the join that lets a consumer cite the firing
    that produced a premise it consumed. Bounded local enumeration over the value on ITS OWN wire, which
    is what §1 permits and what `Subgraph.by_pred` is for."""
    for t in trace.by_pred(PREDICATE):
        if t.o == f.p:                              # role identity, not a name (§22.5 retires `sym`)
            h = t.s
            if Fact(h, SUBJECT, f.s) in trace and Fact(h, OBJECT, f.o) in trace:
                return h
    return None


def conclusion(trace: Subgraph, handle: Node) -> Fact | None:
    """The inverse of `describe`."""
    s = p = o = None
    for t in trace.by_pred(SUBJECT):
        if t.s == handle:
            s = t.o
    for t in trace.by_pred(PREDICATE):
        if t.s == handle:
            p = t.o
    for t in trace.by_pred(OBJECT):
        if t.s == handle:
            o = t.o
    return Fact(s, p, o) if s is not None and p is not None and o is not None else None


# -- building one unit's contribution ------------------------------------------------------------------

def firing_facts(uhandle: Node, firings: tuple, introduced, incoming: Subgraph) -> tuple:
    """The trace facts for one run: one FIRING EVENT per derivation, plus one per fact the unit
    INTRODUCES of its own (a given's axiom, a branch's hypothesis).

    Introduced facts get a firing with **no `<from>`** — which is §2's in-degree-0 story arriving in the
    trace unchanged: *"you told me"* is not a special case in `why`, it is a firing with no premises.

    A premise whose handle is not in `incoming` is cited by **nothing at all** rather than by a fabricated
    stub. That is deliberate: an unciteable premise is a real hole in the record, and it should be visible
    as a short explanation rather than papered over with a placeholder that reads like provenance."""
    out = []
    idx = handle_index(incoming)
    for g, premises in firings:
        f_node = mint("firing")
        c_node = handle_key(g)                  # content-derived (§25.3): the SAME node the object wire
        out.append(Fact(f_node, FIRED_BY, uhandle))
        out.append(Fact(f_node, CONCLUDED, c_node))
        out.extend(describe(c_node, g))
        cited = set()
        for prem in premises:
            h = idx.get((prem.s, prem.p, prem.o))
            if h is not None and h not in cited:
                cited.add(h)
                out.append(Fact(f_node, FROM, h))
    for g in introduced:
        f_node = mint("firing")
        c_node = handle_key(g)                  # uses, so a band and a firing can name one thing
        out.append(Fact(f_node, FIRED_BY, uhandle))
        out.append(Fact(f_node, CONCLUDED, c_node))
        out.extend(describe(c_node, g))
    return tuple(out)


def supersession_stub(uhandle: Node, previous: Subgraph, still_holds) -> tuple:
    """*"Why did you change your mind?"* — kept for ONE generation, then dropped (§16.6: *a small stub*).

    A firing this unit previously owned whose conclusion it no longer derives is re-emitted marked
    `<retracted>`, carrying its conclusion description so the reader knows WHAT was withdrawn. Nothing
    cascades and nothing is undone — the conclusion is simply not in the output any more (§7). This is the
    record of that, not a mechanism for it."""
    out = []
    holds = frozenset(still_holds)
    for t in previous.by_pred(FIRED_BY):
        if t.o != uhandle:
            continue
        f_node = t.s
        if Fact(f_node, RETRACTED, uhandle) in previous:
            continue                                    # already a stub — one generation only
        for c in previous.by_pred(CONCLUDED):
            if c.s != f_node:
                continue
            fact = conclusion(previous, c.o)
            if fact is not None and fact not in holds:
                out.append(Fact(f_node, FIRED_BY, uhandle))
                out.append(Fact(f_node, RETRACTED, uhandle))
                out.append(Fact(f_node, CONCLUDED, c.o))
                out.extend(describe(c.o, fact))
    return tuple(out)


# -- garbage collection: trace lifetime IS unit lifetime -----------------------------------------------

def prune(trace: Subgraph, live: Subgraph) -> Subgraph:
    """Keep the firings that explain the facts CURRENTLY on the object wire, plus everything they cite,
    plus the supersession stubs (§16.6).

    Reachability from the current output is the whole rule, and it is what collapses §10.3's two lifetime
    questions into one: a firing nobody's live conclusion depends on is not history, it is litter."""
    roots = set()
    idx = handle_index(trace)
    for f in live:
        h = idx.get((f.s, f.p, f.o))
        if h is not None:
            roots.add(h)
    for t in trace.by_pred(RETRACTED):
        for c in trace.by_pred(CONCLUDED):
            if c.s == t.s:
                roots.add(c.o)

    owner = {c.o: c.s for c in trace.by_pred(CONCLUDED)}      # conclusion handle -> its firing
    keep_f, frontier = set(), [owner[h] for h in roots if h in owner]
    while frontier:
        f_node = frontier.pop()
        if f_node in keep_f:
            continue
        keep_f.add(f_node)
        for t in trace.by_pred(FROM):
            if t.s == f_node:
                up = owner.get(t.o)
                if up is not None and up not in keep_f:
                    frontier.append(up)

    keep_c = {c.o for c in trace.by_pred(CONCLUDED) if c.s in keep_f}
    kept = []
    for f in trace:
        if f.p in (FIRED_BY, CONCLUDED, FROM, RETRACTED):
            if f.s in keep_f:
                kept.append(f)
        elif f.s in keep_c:
            kept.append(f)
    return Subgraph(kept)


# -- reading it ----------------------------------------------------------------------------------------

def explain(trace: Subgraph, f: Fact, depth: int = 8) -> dict | None:
    """`why P?` — a walk over the TRACE VALUE, never over the wires.

    The distinction is the whole point of this module: this reads what actually fired, at the time it
    fired, and it is unaffected by wires added since. §16.6 places `why P?` as a SINK ON TRACE WIRES, which
    is where the object and trace networks meet; this function is that sink's reader. Returns
    `{"fact", "unit", "because": [...]}` — `because == []` is a GIVEN (in-degree 0, *"you told me"*)."""
    h = handle_of(trace, f)
    if h is None:
        return None
    owner = {c.o: c.s for c in trace.by_pred(CONCLUDED)}
    f_node = owner.get(h)
    if f_node is None:
        return None
    unit = next((t.o for t in trace.by_pred(FIRED_BY) if t.s == f_node), None)
    node = {"fact": f, "unit": unit, "because": []}
    if depth > 0:
        prems = [conclusion(trace, t.o) for t in trace.by_pred(FROM) if t.s == f_node]
        # SORTED, and this is not cosmetic. The premises live in a frozenset, so an unsorted walk makes an
        # explanation's SHAPE depend on the hash seed — the same class of defect as
        # [[perf-hash-seed-sensitivity]], and found the same way: a probe that passed and then did not.
        # An explanation a user reads twice must read the same twice.
        for prem in sorted((p for p in prems if p is not None), key=repr):
            sub = explain(trace, prem, depth - 1)
            node["because"].append(sub or {"fact": prem, "unit": None, "because": []})
    return node


def render(node: dict | None, indent: int = 0) -> str:
    """The explanation as text. `(given)` is not a special case in the data — it is what no `<from>`
    looks like, which is §2's in-degree taxonomy showing through the trace."""
    if node is None:
        return "(no record)"
    pad = "  " * indent
    who = node["unit"].name if node["unit"] is not None else "?"
    line = f"{pad}{node['fact']}  [{who}]" + ("" if node["because"] else "  (given)")
    return "\n".join([line] + [render(b, indent + 1) for b in node["because"]])


__all__ = ["FIRED_BY", "CONCLUDED", "FROM", "SUBJECT", "PREDICATE", "OBJECT", "RETRACTED",
           "TRACE_PREDICATES", "is_trace", "describe", "handle_of", "conclusion", "firing_facts",
           "supersession_stub", "prune", "explain", "render", "EMPTY"]
