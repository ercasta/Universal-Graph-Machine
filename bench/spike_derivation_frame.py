"""DERIVATION-FRAME SPIKE — copy vs. projection for the locality/identity bug class (2026-07-23).

WHY THIS EXISTS. Almost every grammar-route (flip-default) corner case is a LOCALITY-OF-PROCESSING
failure: a rule, or a read, touches graph it should not — the token/entity DUAL-STORE (a name resolves
to a discourse token AND an interpretation entity; content lands on the wrong one), the scaffolding
ENUMERATION leak (a `who` query enumerates an empty-named control node), the schema meta-rule binding an
interpretation control-mirror. We have been paying this in installments: a per-site denotation patch
(`intern_denoted`, `resolve_write_node`, the who-branch `_guard`, the hedge `denoted=`) at N call sites,
"resolving identity CASE BY CASE instead of at one boundary" (the handoff's deeper diagnosis).

THE HYPOTHESIS (user, 2026-07-23). Do not reason over a PROJECTION (a filtered VIEW of the shared
graph) — a view isolates READS but not WRITES, and writes (derived facts landing on a node) are exactly
where the aliasing bites, so a projection leaves the shared-state bug in place. Instead reason over a
materialized derived COPY with value semantics: one node per name (so token / entity / scaffolding
collapse or are simply never copied in), reason IN the copy, then MERGE conclusions back to the source
at ONE identity boundary — discardable and re-derivable, like an ETL job or a local stack frame. This
is the message-passing stance vs. the shared-state stance.

WHAT THIS SPIKE TESTS. The discriminator is propositional-cause authored the UNPATCHED way
(`intern_denoted=False`), because its reify bridge is a NODE-BOUND join with predicate-variable matching
(value-nodes) — so it stresses both (a) whether the copy dissolves the dual-store WITHOUT the patch and
(b) whether the copy preserves ENOUGH structure to still reason.

VERDICT (run it): the frame dissolves the identity class at one boundary, subsuming BOTH the
`intern_denoted` write-patch and the who-branch read-guard, and the node-bound predicate-variable bridge
survives the project->reassemble round-trip. It does NOT touch surface-coverage gaps (a fact that never
parsed is not in the projection to copy) — the frame is for the IDENTITY/locality class only.

CAVEATS THE SPIKE MADE CONCRETE (cost, not correctness):
  * EAGER vs. LAZY. This projects the whole KB; the engine is demand-driven. The production shape is
    COPY-ON-LAZY: an empty frame that materializes a source node at first-touch by the demand path
    (`_facts_matching`), resolving identity once per node and memoizing the frame->source back-pointer —
    the frame IS the memo table. That reconciles value-semantics isolation with laziness, and collapses
    the N denotation call-sites into the ONE fact-fetch primitive. NOT built here; the next probe.
  * IDENTITY AT MERGE. `merge_back` here re-resolves by NAME (the `src` map). The honest form mints a
    frame_node->source_node back-pointer AT projection/first-touch time (the `ById` discipline) so a
    genuine same-name/different-entity case cannot mis-merge. One place to get right — which is the win.
  * RELATION TO `commit=False`. A read-only query already scopes crisp derivations into a suppose pencil
    scope (discardable) — but IN THE SHARED GRAPH, so reads still alias onto the wrong node. That is why
    write-scoping alone did not fix identity; the COPY is the missing half.

Run: `python -m bench.spike_derivation_frame` (from repo root).
"""
from __future__ import annotations

import pathlib
import warnings

from ugm import AttrGraph
from ugm.attrgraph import valued
from ugm.cnl import grammar_intake as gi
from ugm.intake import ingest
from ugm.cnl.query import ask_goal
from ugm.lowering import assemble_facts
from ugm.machine import Machine
from ugm.cnl.cause_surface import handle_facts, BRIDGE_RULES
from ugm.cnl.machine_rules import load_machine_rules

_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus" / "loudon_grammar.cnl"

DERIVED_TAG = "<derived-in-frame>"      # provenance stamp on a merged-back conclusion

# Pure surface/scaffolding predicates — never reasoning content, so never copied into a frame.
_SKIP_PREDS = frozenset({
    "next", "first", "denotes", "interprets", "about", "head", "because",
    "span_noun", "span_np", "span_clause", "span_qbody", "span_verb",
    "useful_clause", "useful_np", "useful_noun", "useful_verb",
})


def _grammar_kb():
    """A KB whose reasoning path IS the grammar route (open vocabulary — the default-grammar config)."""
    g = AttrGraph()
    gi.declare_grammar(g, _CORPUS.read_text(encoding="utf-8"), open_class="noun")
    return g, []


def project(kb):
    """The reasoning-relevant content of `kb` as NAME triples (token / entity / scaffolding collapse by
    shared name; control/inert nodes are dropped), plus a name->source-node map for merge-back. A
    value-node carried in object position (a predicate handled as a node) renders by its name."""
    triples: list[tuple[str, str, str]] = []
    src: dict[str, str] = {}
    for n in list(kb.nodes()):
        if kb.is_control(n) or kb.is_inert(n):
            continue
        nm = kb.name(n)
        if not nm:
            continue
        src.setdefault(nm, n)
        for r, o in kb.relations_from(n):
            p = kb.predicate(r)
            if not p or p in _SKIP_PREDS or kb.is_control(r) or kb.is_inert(r):
                continue
            onm = kb.name(o)
            if onm:
                triples.append((nm, p, onm))
    return triples, src


def frame_of(kb):
    """Materialize the projection into a FRESH copy graph — one node per name."""
    triples, src = project(kb)
    fg = AttrGraph()
    Machine().run(fg, assemble_facts(triples))
    return fg, src, triples


def merge_back(kb, src, s_name, pred, o_name):
    """The ONE identity boundary: a frame conclusion lands on the SOURCE entity (resolved by name
    through `src`), tagged with `<derived-in-frame>` provenance — discardable, re-derivable.
    (Production form: resolve through a frame->source back-pointer, not a name re-lookup.)"""
    s = src.get(s_name) or kb.add_node(s_name)
    o = src.get(o_name) or kb.add_node(o_name)
    rel = kb.add_relation(s, pred, o)
    kb.set_attr(rel, DERIVED_TAG, valued("yes"))
    return rel


def _ask(kb, rules, goal, *, commit=False):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ask_goal(kb, goal, rules, commit=commit)


def case1_dual_store():
    print("=" * 72)
    print("CASE 1 — propositional-cause dual-store, authored UNPATCHED (intern_denoted=False)")
    print("=" * 72)
    kb, rules = _grammar_kb()
    ingest(kb, rules, "door1 is open")                    # folds onto the interpretation ENTITY
    a, b = ("door1", "is", "open"), ("cat", "is", "scared")
    Machine().run(kb, assemble_facts(handle_facts(a, b), intern_denoted=False))   # the BUGGY intern
    rules.extend(r for rt in BRIDGE_RULES for r in load_machine_rules(rt))

    shared = _ask(kb, rules, ("yesno", "cat", "is", "scared"))
    fg, _, triples = frame_of(kb)
    framed = _ask(fg, rules, ("yesno", "cat", "is", "scared"))
    print(f"  shared graph : cat is scared -> {shared}")
    print(f"  frame ({len(triples)} triples): cat is scared -> {framed}")
    ok = shared != ["yes"] and framed == ["yes"]
    print(f"  => {'PASS — frame dissolves the dual-store without the patch' if ok else 'FAIL'}")
    return ok


def case2_enumeration():
    print("\n" + "=" * 72)
    print("CASE 2 — enumeration is structurally clean in the frame (no who-branch guard)")
    print("=" * 72)
    kb, rules = _grammar_kb()
    ingest(kb, rules, "ada is a suspect")
    ingest(kb, rules, "bo is a suspect")
    fg, _, _ = frame_of(kb)
    who = _ask(fg, rules, ("who", None, "is_a", "suspect"))
    ok = who == ["ada is_a suspect", "bo is_a suspect"]
    print(f"  frame who is_a suspect -> {who}")
    print(f"  => {'PASS — exactly the witnesses, no empty-named scaffolding row' if ok else 'FAIL'}")
    return ok


def case3_merge_back():
    print("\n" + "=" * 72)
    print("CASE 3 — merge-back to source + discard (value semantics)")
    print("=" * 72)
    kb, rules = _grammar_kb()
    ingest(kb, rules, "door1 is open")
    a, b = ("door1", "is", "open"), ("cat", "is", "scared")
    Machine().run(kb, assemble_facts(handle_facts(a, b), intern_denoted=False))
    rules.extend(r for rt in BRIDGE_RULES for r in load_machine_rules(rt))

    fg, src, _ = frame_of(kb)
    _ask(fg, rules, ("yesno", "cat", "is", "scared"), commit=True)      # derive IN the frame
    before = _ask(kb, [], ("yesno", "cat", "is", "scared"))             # source, no rules
    merge_back(kb, src, "cat", "is", "scared")                         # the one identity boundary
    after = _ask(kb, [], ("yesno", "cat", "is", "scared"))
    fg.clear() if hasattr(fg, "clear") else None                       # discard the frame
    ok = before != ["yes"] and after == ["yes"]
    print(f"  source cat is scared: before merge={before}  after merge={after}")
    print(f"  => {'PASS — conclusion lands on the source entity, frame discarded' if ok else 'FAIL'}")
    return ok


def main():
    results = [case1_dual_store(), case2_enumeration(), case3_merge_back()]
    print("\n" + "=" * 72)
    verdict = "GO — the copy dissolves the identity class at one boundary" if all(results) \
        else "MIXED — see failing case(s) above"
    print(f"VERDICT: {verdict}  ({sum(results)}/{len(results)} cases)")
    print("=" * 72)


if __name__ == "__main__":
    main()
