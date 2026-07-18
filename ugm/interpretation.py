"""
The SURFACE / INTERPRETATION split — denotation as a defeasible, discardable commitment.

Design: `docs/design/surface_interpretation.md`. Produced by the grammar arc
(`docs/design/homoiconic_grammar.md` §11) but substrate-level: it governs coreference, revision,
and how the substrate is layered.

    The nodes representing the SENTENCE are never touched. They are the permanent, monotone record
    of what was said. Every JUDGEMENT about what it MEANS lives in a SCOPE holding COPIES, with
    provenance back to the surface.

SURFACE (observation, immutable): tokens, the `first`/`next` chains, and parse spans
(`cat`/`begin`/`end`).

INTERPRETATION (inference, scoped, discardable): entities, `denotes`, every slot (`head`, `subj`,
`pred`, …), every folded fact, coreference, subkind minting.

THE MEMBERSHIP RULE — and the finding that cost a bug: the line is NOT "which node it hangs on".
Slot edges are written ONTO surface span nodes and are still interpretation. The line is
**structure vs denotation**. Leaving slot edges out of the scope let a second interpretation
silently inherit the first one's decisions while appearing to work.

WHY THE MERGE MAY STAY DESTRUCTIVE. Inside the scope, coreference folds mentions to ONE node — the
fast representation, no `same_as` clique, no representative-pointer hop, i.e. exactly today's cost.
That is legal because reversal is never needed: an interpretation is not repaired, it is DISCARDED
and re-derived from a surface that never moved. This is what makes defeasible coreference
affordable and why the 2026-07-13 interning decision does not have to be reopened — interning
stays and stays destructive; only its STATUS changes, from irreversible reader policy to a
defeasible commitment carrying provenance.
"""
from __future__ import annotations

from .production_rule import Pat, Rule
from .lowering import run_bank
from .vocabulary import neg_pred

SCOPE = "<interpretation>"
DENOTES = "denotes"          # surface token -> the entity it is TAKEN to denote (the judgement)
INTERPRETS = "interprets"    # entity -> every surface mention it was derived from (provenance)
MEMBER = "member"
CONTRADICTION = "<contradiction>"

#: The relations a minted entity's identity consists of (`ByDesc`'s defining relations).
DEFINING: tuple[str, ...] = ("is_a", "is")

#: Predicates that are SURFACE structure. Everything else a fold writes is interpretation.
SURFACE_PREDS: frozenset[str] = frozenset({"cat", "begin", "end", "next", "first", "is_eos"})


def _slot(g, n, key):
    return next((o for r, o in g.relations_from(n) if g.has_key(r, key)), None)


# ---------------------------------------------------------------------------
# Opening a scope: the coreference judgement, as copies
# ---------------------------------------------------------------------------

def open_scope(g) -> str:
    """A fresh interpretation scope node."""
    return g.add_node(SCOPE, control=True)


def interpret_mentions(g, scope: str) -> dict[str, str]:
    """THE COREFERENCE JUDGEMENT, as a scoped copy rather than a destructive fold of the surface.

    One entity node per distinct mention NAME, with `interprets` provenance to every surface token
    it was derived from and `denotes` from each token to it. The surface tokens keep their identity
    and their chain — nothing about the sentence is touched.

    This is where `intern_mentions` differs: it folds the surface mentions together and DELETES the
    victims, which is why that decision can never be revised."""
    lex_heads: dict[str, list[str]] = {}
    for p in list(g.nodes()):
        if not any(g.has_key(r, "cat") for r, _o in g.relations_from(p)):
            continue
        beg, end = _slot(g, p, "begin"), _slot(g, p, "end")
        if beg is None or end is None:
            continue
        nxt = next((o for r, o in g.relations_from(beg) if g.has_key(r, "next")), None)
        if nxt == end:                              # a one-token span denotes its token
            lex_heads.setdefault(g.name(beg), []).append(beg)
    ents: dict[str, str] = {}
    for nm, dups in sorted(lex_heads.items()):
        toks = list(dict.fromkeys(dups))            # a token may head spans of several categories
        e = g.add_node(nm)
        g.add_relation(scope, MEMBER, e, control=True)
        for t in toks:
            g.add_relation(e, INTERPRETS, t, control=True)
            g.add_relation(t, DENOTES, e, control=True)
        ents[nm] = e
    return ents


HEAD_BRIDGE: list[Rule] = [
    # The bridge from surface to interpretation: a one-token span's `head` is the ENTITY its token
    # is taken to denote, not the token. Every slot downstream therefore carries entities, and the
    # whole fold writes into the scope without knowing it.
    Rule(key="interp.lexhead",
         lhs=[Pat("?p", "cat", "?c"), Pat("?p", "begin", "?t"), Pat("?p", "end", "?u"),
              Pat("?t", "next", "?u"), Pat("?t", DENOTES, "?e")],
         rhs=[Pat("?p", "head", "?e")]),
]


def close_scope(g, scope: str, before: set) -> int:
    """The scope IS everything this interpretation created — the delta against a pre-interpretation
    snapshot.

    Taking the delta needs no per-category bookkeeping and cannot miss a node, which matters:
    marking membership with a RULE silently marked nothing, because `Pat(scope_id, MEMBER, "?e")`
    reads its subject as a NAME and interned a node named `n417` instead. A scope node has no name
    to be addressed by; addressing one from inside a rule would need `ByDesc`."""
    n = 0
    for node in g.nodes():
        if node not in before and node != scope and not g.is_inert(node):
            g.add_relation(scope, MEMBER, node, control=True)
            n += 1
    return n


def scope_members(g, scope: str) -> set[str]:
    return {o for r, o in g.relations_from(scope) if g.has_key(r, MEMBER)}


def discard_scope(g, scope: str, interp_preds) -> int:
    """Throw the interpretation away. Legal precisely because it is scoped: the surface record is
    untouched, so nothing is lost that cannot be re-derived.

    `interp_preds` must name every DENOTATION predicate the fold wrote — the slots. Leaving them
    behind leaves surface spans holding stale heads that point at deleted entities, and the next
    interpretation silently inherits this one's decisions."""
    gone = 0
    for m in scope_members(g, scope):
        if m in g.nodes():
            g.remove_node(m)
            gone += 1
    preds = set(interp_preds) | {DENOTES, "head"}
    for t in list(g.nodes()):
        for r, _o in list(g.relations_from(t)):
            if g.predicate(r) in preds and r in g.nodes():
                g.remove_node(r)
                gone += 1
    return gone


# ---------------------------------------------------------------------------
# Contradiction — a DERIVED marker, not a checker (consistency_design.md §0)
# ---------------------------------------------------------------------------

def contradiction_bank(predicates) -> list[Rule]:
    """`X p Y` and `X not-p Y` on ONE entity derives a `<contradiction>` marker.

    Monotone and PARACONSISTENT: it marks itself and does not explode the KB. This is a local
    stand-in for `consistency_design.md`'s universal conflict lint, which is still a SKETCH — the
    marker convention is designed there, but nothing derives it yet."""
    return [Rule(key=f"contra.{w}",
                 lhs=[Pat("?e", w, "?x"), Pat("?e", neg_pred(w), "?x")],
                 rhs=[Pat(f"{CONTRADICTION}?", "about", "?e"),
                      Pat(f"{CONTRADICTION}?", "because", "?x")])
            for w in sorted(predicates)]


def contradictions(g) -> list[tuple[str, str]]:
    """Every `(about, because)` a contradiction marker names."""
    out = []
    for n in g.nodes():
        if g.name(n) != CONTRADICTION:
            continue
        about, because = _slot(g, n, "about"), _slot(g, n, "because")
        if about is not None:
            out.append((about, because))
    return out


def culprits(g, entity: str) -> list[str]:
    """The surface mentions `entity` was interpreted FROM.

    More than one means a coreference JUDGEMENT is in the contradiction's support — which is the
    thing to ASK about, not to guess. Culprit selection is a SELECTION problem, and this project's
    answer to selection problems is consistently the same: do not select, ask."""
    return [o for r, o in g.relations_from(entity) if g.has_key(r, INTERPRETS)]


# ---------------------------------------------------------------------------
# Reading a nameless entity back: description, not name
# ---------------------------------------------------------------------------

def describe(g, n: str, defining: tuple[str, ...] = DEFINING) -> str:
    """A node's name, or — for a minted entity — its defining DESCRIPTION."""
    nm = g.name(n)
    if nm:
        return nm
    parts = sorted({f"{g.predicate(r)} {g.name(o)}" for r, o in g.relations_from(n)
                    if g.predicate(r) in defining and g.name(o)})
    return f"<{' & '.join(parts)}>" if parts else "<anon>"


def intern_described(g, defining: tuple[str, ...] = DEFINING) -> int:
    """Coalesce NAMELESS entities that share a description — the description-keyed counterpart of
    `intern_mentions`, which is name-keyed and therefore structurally blind to them.

    Keyed on the DEFINING relations only, not on everything the node has since acquired: two
    mentions of the same subkind must intern even when each has learned different facts. Hash-keyed
    on the description, so it is O(k) — NOT the pairwise clique that similarity matching would need.

    REQUIRED for correctness, not tidiness: an RHS-only `?e` is VALUE INVENTION, minted fresh on
    every bank run, so an accumulating KB re-mints the same subkind on every re-run."""
    from .cnl.forms import _fold_node
    groups: dict[frozenset, list[str]] = {}
    for n in list(g.nodes()):
        if g.name(n) or g.is_control(n) or g.is_inert(n):
            continue
        desc = frozenset((g.predicate(r), g.name(o)) for r, o in g.relations_from(n)
                         if g.predicate(r) in defining and g.name(o))
        if desc:
            groups.setdefault(desc, []).append(n)
    folded = 0
    for members in groups.values():
        for victim in members[1:]:
            _fold_node(g, members[0], victim)
            folded += 1
    return folded


# ---------------------------------------------------------------------------
# The interpretation pass
# ---------------------------------------------------------------------------

def interpret(g, banks, scope: str) -> set[str]:
    """Run ONE interpretation over the standing surface. Returns the scope's members.

    `banks` is a `cnl.grammar.GrammarBanks`. Assumes `parse` has already written the surface."""
    before = set(g.nodes())
    interpret_mentions(g, scope)
    run_bank(g, HEAD_BRIDGE + banks.slots,
             control_preds=banks.slot_preds | {"head", DENOTES})
    run_bank(g, banks.asserts)
    run_bank(g, contradiction_bank(set(banks.grammar.lexicon)))
    close_scope(g, scope, before)
    return scope_members(g, scope)


def scope_facts(g, scope: str) -> list[tuple[str, str, str]]:
    """The facts this interpretation commits to, rendered by name or description."""
    members = scope_members(g, scope)
    out = []
    for s in members:
        for r, o in g.relations_from(s):
            p = g.predicate(r)
            if g.is_control(r) or g.is_inert(r) or not p:
                continue
            if p in SURFACE_PREDS or p in ("head", "about", "because"):
                continue
            if o in members or g.name(o):
                out.append((describe(g, s), p, describe(g, o)))
    return sorted(set(out))
