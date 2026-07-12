"""
Phase 8.3 — the discourse focus stack (docs/cnl_intake_design.md §3).

The working set of a long CNL session is a FOCUS: pointer nodes into the KB marking what the conversation
is currently about. Not last-N-turns (topics switch) — a `<focus>` STACK in the control layer, each frame
pointing at CENTER node(s) (the in-play entities). Decisions (ratified 2026-07-12):

  - POINTER-AT-CENTER, extent DERIVED. A frame names only its centers; the working-set EXTENT is the
    demand-closure reasoning reaches from them (§3), never a declared scope subgraph (that boundary is
    domain-dependent — the engine cannot own it without hardcoding domain logic). Same emergent principle
    as recognition / demand-driven negation.
  - IMPLICIT = WIDEN-ONLY. An ordinary utterance only adds its mentioned entities as centers of the TOP
    frame (`widen`); it never pushes a new frame. This sidesteps brittle implicit topic-switch detection.
  - EXPLICIT = the small control-CNL (`FOCUS_FORMS`, recognized — never string-sniffed, §D discipline):
    `focus on X` pushes, `forget that` drops, `back to X` re-enters. Reuse of the SUPPOSE scope idiom.
  - GC by REACHABILITY from focus roots: a dropped frame's center pointers are cut (control-layer op, NOT
    a fact deletion §5 — entities/facts persist, only the focus's pointer goes).

The stack is label-less structure: frames are `<focus>` nodes; `newer -[below]-> older` links them; the
TOP is the frame no other frame is stacked below-of (derived, not a mutable pointer). Content-blind — no
predicate/domain strings here (§D).
"""
from __future__ import annotations

from .production_rule import Pat, Rule

FOCUS = "<focus>"
CENTER = "center"
BELOW = "below"
FOCUS_OP = "<focus-op>"


# ---------------------------------------------------------------------------
# The stack (control-layer structure)
# ---------------------------------------------------------------------------

def _frames(kb) -> list[str]:
    return list(kb.nodes_named(FOCUS))


def _covered(kb) -> set[str]:
    """Frames that have another frame stacked above them (objects of a `below` edge)."""
    out: set[str] = set()
    for f in _frames(kb):
        for rel, obj in kb.relations_from(f):
            if kb.has_key(rel, BELOW):
                out.add(obj)
    return out


def top_frame(kb) -> str | None:
    """The current top of the focus stack — the frame nothing is stacked below-of — or None."""
    covered = _covered(kb)
    tops = [f for f in _frames(kb) if f not in covered]
    return tops[0] if tops else None


def _entity_node(kb, name: str) -> str:
    """The KB node for entity `name` (a real, non-control mention), minted if absent — a center is an
    entity in play, not a fresh scaffolding node."""
    for n in kb.nodes_named(name):
        if not (kb.is_control(n) or kb.is_inert(n)):
            return n
    return kb.add_node(name)


def _center_names(kb, frame: str) -> set[str]:
    return {kb.name(o) for rel, o in kb.relations_from(frame) if kb.has_key(rel, CENTER)}


def push_focus(kb, center_names=()) -> str:
    """Push a new focus frame (an EXPLICIT topic switch), optionally seeded with centers. Returns it."""
    old = top_frame(kb)
    frame = kb.add_node(FOCUS, control=True)
    if old is not None:
        kb.add_relation(frame, BELOW, old, control=True)
    for nm in center_names:
        kb.add_relation(frame, CENTER, _entity_node(kb, nm), control=True)
    return frame


def widen(kb, center_names) -> str:
    """IMPLICIT default: add `center_names` as centers of the TOP frame (creating a first frame if the
    stack is empty). Never pushes — a topic switch is explicit."""
    frame = top_frame(kb)
    if frame is None:
        return push_focus(kb, center_names)
    have = _center_names(kb, frame)
    for nm in center_names:
        if nm not in have:
            kb.add_relation(frame, CENTER, _entity_node(kb, nm), control=True)
    return frame


def top_centers(kb) -> list[str]:
    """The center entity NAMES of the top frame — the seed set (8.3b) and the anaphora referents (8.4)."""
    frame = top_frame(kb)
    return sorted(_center_names(kb, frame)) if frame is not None else []


def _drop_top(kb) -> None:
    frame = top_frame(kb)
    if frame is None:
        return
    for rel, _o in list(kb.relations_from(frame)):
        kb.remove_node(rel)                 # cut this frame's center/below rel nodes (control-layer op)
    kb.remove_node(frame)
    kb.gc_disconnected()                    # entities with other edges persist (§5); orphans swept


def drop_focus(kb) -> None:
    """`forget that` — pop the top frame. A control-layer op, NOT a fact deletion (§5): the entities stay,
    only the focus's pointer to them goes. The frame below becomes top."""
    _drop_top(kb)


def reenter_focus(kb, name: str) -> None:
    """`back to X` — return to the frame whose centers include `X` by popping the frames above it. (v1:
    pop-to-X; keeping intervening frames below a re-raised one is a later refinement.)"""
    guard = len(_frames(kb))
    while guard >= 0:
        frame = top_frame(kb)
        if frame is None or name in _center_names(kb, frame):
            return
        _drop_top(kb)
        guard -= 1


# ---------------------------------------------------------------------------
# The explicit focus control-CNL — recognized as FORMS, never string-sniffed (§D.2)
# ---------------------------------------------------------------------------

FOCUS_FORMS: list[Rule] = [
    # "focus on X"  -> push a frame centered on X
    Rule(key="focus.push",
         lhs=[Pat("?s", "first", "focus?"), Pat("focus?", "next", "on?"), Pat("on?", "next", "?x")],
         rhs=[Pat(FOCUS_OP + "?", "op", "push"), Pat(FOCUS_OP + "?", "target", "?x")]),
    # "forget that"  -> drop the top frame
    Rule(key="focus.drop",
         lhs=[Pat("?s", "first", "forget?"), Pat("forget?", "next", "that?")],
         rhs=[Pat(FOCUS_OP + "?", "op", "drop")]),
    # "back to X"  -> re-enter the frame centered on X
    Rule(key="focus.reenter",
         lhs=[Pat("?s", "first", "back?"), Pat("back?", "next", "to?"), Pat("to?", "next", "?x")],
         rhs=[Pat(FOCUS_OP + "?", "op", "reenter"), Pat(FOCUS_OP + "?", "target", "?x")]),
]


def _slot(graph, node: str, role: str) -> str | None:
    for rel, obj in graph.relations_from(node):
        if graph.has_key(rel, role):
            return graph.name(obj)
    return None


def recognize_focus_op(utterance: str) -> tuple[str, str | None] | None:
    """If `utterance` is an explicit focus move, its `(op, target|None)` — else None. Recognized by which
    FOCUS_FORM fires (in a scratch scope), NOT by a Python word list."""
    from .cnl.forms import tokenize
    from .lowering import run_bank
    from .world_model import Graph
    tmp = Graph()
    tokenize(tmp, utterance)
    run_bank(tmp, FOCUS_FORMS)
    for nid in tmp.nodes():
        if tmp.name(nid) == FOCUS_OP:
            return (_slot(tmp, nid, "op"), _slot(tmp, nid, "target"))
    return None


def apply_focus_op(kb, op: str, target: str | None) -> None:
    """Execute a recognized focus move on the live KB."""
    if op == "push":
        push_focus(kb, [target] if target else [])
    elif op == "drop":
        drop_focus(kb)
    elif op == "reenter" and target is not None:
        reenter_focus(kb, target)


# ---------------------------------------------------------------------------
# Content-blind: the entities an utterance is ABOUT (its content SUBJECTS)
# ---------------------------------------------------------------------------

def gc_utterance_scaffolding(kb, anchor: str) -> None:
    """Sweep ONE processed utterance's recognition scaffolding — its `<sentence>` anchor and `first`/`next`
    token chain — after routing. Surgical (only THIS anchor's chain, never a shared `next` structure like a
    reified itinerary): the fact CONTENT lives on the entity nodes (a relation between them), not the chain,
    so removing the chain is ANSWER-NEUTRAL; entity tokens survive (they keep their content relations and
    re-coref with future same-named mentions), while pure grammar-word tokens (`is`/`a`, no content relation)
    are swept by `gc_disconnected`. Accretion control (§3): the transcript's tokens don't pile up in the KB.
    (Focus-reachability GC of a persistent `<query>`/`<goal>` lands with streaming, 8.5.)"""
    seen: set[str] = set()
    frontier = [anchor]
    chain_rels: list[str] = []
    while frontier:
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        for rel, nxt in list(kb.relations_from(n)):
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                chain_rels.append(rel)
                frontier.append(nxt)
    for rel in chain_rels:
        kb.remove_node(rel)
    kb.remove_node(anchor)
    kb.gc_disconnected()


def utterance_subjects(kb, anchor: str) -> set[str]:
    """The names of the content entities this utterance PREDICATES ABOUT — a token that carries an
    outgoing content relation (subject of a fact). Content-blind: no predicate/domain vocabulary; the
    token chain (`first`/`next`) and control/inert flags are the only structure read. These are the
    centers an assertion implicitly widens the focus with (§3)."""
    seen: set[str] = set()
    frontier = [anchor]
    toks: list[str] = []
    while frontier:
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        for rel, nxt in kb.relations_from(n):
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                frontier.append(nxt)
                if not (kb.is_control(nxt) or kb.is_inert(nxt)):
                    toks.append(nxt)
    names: set[str] = set()
    for t in toks:
        for rel, _obj in kb.relations_from(t):
            if kb.is_control(rel) or kb.is_inert(rel):
                continue
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                continue
            names.add(kb.name(t))                 # t is the subject of a content relation
            break
    return names
