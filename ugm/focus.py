"""
Phase 8.3 — the discourse focus stack (docs/cnl_intake_design.md §3; Axis B register lift,
docs/mechanism_policy_separation.md §8).

The working set of a long CNL session is a FOCUS: what the conversation is currently about. Not
last-N-turns (topics switch) — a STACK, each frame naming the in-play CENTER entities. Decisions
(ratified 2026-07-12):

  - POINTER-AT-CENTER, extent DERIVED. A frame names only its centers; the working-set EXTENT is the
    demand-closure reasoning reaches from them (§3), never a declared scope subgraph (that boundary is
    domain-dependent — the engine cannot own it without hardcoding domain logic). Same emergent principle
    as recognition / demand-driven negation.
  - IMPLICIT = WIDEN-ONLY. An ordinary utterance only adds its mentioned entities as centers of the TOP
    frame (`widen`); it never pushes a new frame. This sidesteps brittle implicit topic-switch detection.
  - EXPLICIT = the small control-CNL (`FOCUS_FORMS`, recognized — never string-sniffed, §D discipline):
    `focus on X` pushes, `forget that` drops, `back to X` re-enters. Reuse of the SUPPOSE scope idiom.

AXIS B (2026-07-14): the focus stack is EXECUTION/CONTROL state — pure attention bookkeeping that NO rule
reasons about (the extent is DERIVED on demand from the centers; nothing matches a focus frame). By the
discriminating test it is NOT a fact and NOT explanation, so it lives in the graph's CONTROL-REGISTER FILE
(`AttrGraph.registers["focus"]`), not as `<focus>`/`center`/`below` NODES in the data graph. The stack is
a plain Python list of frames, each frame an ordered list of center NAMES (focus is name-grained — the
discourse handle the SLM resolves anaphora to, and exactly what `top_centers` feeds `fscope`). This RETIRES
the `<focus>` control-node convention: focus never touches the node/edge store, so a `drop` is graph-neutral
by construction (the entities were never linked to focus — the old §5 "cut the pointer, keep the entity"
guarantee is now trivially true) and no focus node can ever leak into fact matching. Content-blind — no
predicate/domain strings here (§D).
"""
from __future__ import annotations

from .production_rule import Pat, Rule
from .vocabulary import SAME_AS, MENTION

FOCUS_OP = "<focus-op>"      # transient recognition marker (scratch graph only — see recognize_focus_op)


# ---------------------------------------------------------------------------
# The stack — a control REGISTER (Axis B), not `<focus>` graph nodes
# ---------------------------------------------------------------------------
#
# `kb.registers["focus"]` is the stack: a list of frames, each frame an ordered list of center NAMES.
# Frame `[-1]` is the TOP. The register is physically separate from the node/edge store, so matching /
# `nodes()` / `derived_triples` never see it (control state is not a fact).

def _stack(kb) -> list[list[str]]:
    return kb.registers.setdefault("focus", [])


def top_frame(kb) -> list[str] | None:
    """The current top frame (its list of center names), or None if the stack is empty."""
    st = _stack(kb)
    return st[-1] if st else None


def push_focus(kb, center_names=()) -> list[str]:
    """Push a new focus frame (an EXPLICIT topic switch), optionally seeded with centers. Returns it."""
    frame: list[str] = []
    _stack(kb).append(frame)
    for nm in center_names:
        if nm not in frame:
            frame.append(nm)
    return frame


def widen(kb, center_names) -> list[str]:
    """IMPLICIT default: add `center_names` as centers of the TOP frame (creating a first frame if the
    stack is empty), bumping recency on re-mention. Never pushes — a topic switch is explicit."""
    frame = top_frame(kb)
    if frame is None:
        return push_focus(kb, center_names)
    for nm in center_names:
        if nm not in frame:
            frame.append(nm)
    return frame


def top_centers(kb) -> list[str]:
    """The center entity NAMES of the top frame — the seed set (8.3b) and the anaphora referents (8.4)."""
    frame = top_frame(kb)
    return sorted(frame) if frame is not None else []


# ANAPHORA is a BOUNDARY concern, not the substrate's (decision 2026-07-12): resolving "she" -> "ada" is
# pragmatics the external SLM owns on the NL->CNL side, using the discourse state the substrate EXPOSES
# (`top_centers`). The substrate reasons over already-resolved CNL and never sees a pronoun. So there is no
# in-substrate salience ranking / pronoun resolver here — only the exposed centers. See `cnl_intake_design.md` §4.


def drop_focus(kb) -> None:
    """`forget that` — pop the top frame. Purely a register op: graph-NEUTRAL by construction (focus never
    linked to the entities, so nothing to cut, no §5 fact-deletion risk). The frame below becomes top."""
    st = _stack(kb)
    if st:
        st.pop()


def reenter_focus(kb, name: str) -> None:
    """`back to X` — return to the frame whose centers include `X` by popping the frames above it. (v1:
    pop-to-X; keeping intervening frames below a re-raised one is a later refinement.)"""
    st = _stack(kb)
    while st and name not in st[-1]:
        st.pop()


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
        for rel, obj in kb.relations_from(t):
            if kb.is_control(rel) or kb.is_inert(rel):
                continue
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                continue
            if kb.has_key(rel, SAME_AS):          # a coref link is not a domain fact ABOUT t — skip it,
                continue                          # else a TYPE ("suspect") coref'd across mentions would
            if kb.name(obj) == MENTION:           # the universal `is_a <mention>` coref handle is
                continue                          # infrastructure, not a fact ABOUT t (like same_as) —
            names.add(kb.name(t))                 # else EVERY token (incl. stopwords) leaks as a center
            break
    return names
