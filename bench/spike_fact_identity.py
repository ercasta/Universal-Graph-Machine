"""Spike: STEP 1 of the unified-representation arc (docs/design/unified_representation.md §4) — does a
TARGETED, denotes-based reconciliation of a proposition's participant REFERENCES to their discourse
referent close the causation link-first order bug WITHOUT the brute same-name union (which would be the
seam the north star forbids)?

THE PROBLEM (probed 2026-07-23; see docs/design/composition_architecture.md §GAPS + the causation cells
in test_epistemic_closure.py). `that A causes that B` reifies each proposition to a content-keyed HANDLE
(`prop:X:Y:Z`) whose `subj`/`obj` edges point at NAME-interned participant nodes. When the LINK is stated
BEFORE its antecedent, those participant nodes are minted as ORPHANS (canon class == {itself}, no `denotes`
edge to the grammar fold's later-created entity), so the reify bridge `?h subj ?s … ?s ?p ?o` — a NODE-bound
join that unions only via the `denotes` canonical class (`chain._canon_class`, the derivation-frame boundary)
— cannot see the asserted fact. Measured: 3 co-named `lion` nodes, join misses, answer `no (assumed)`.

WHAT WAS ESTABLISHED BEFORE THIS SPIKE (scratch probes):
  * reconciling the SUBJECT endpoint alone is NOT enough (the OBJECT `mane` is split too);
  * brute-unioning EVERY same-named node via `denotes` DOES flip link-first to `yes` — but that is
    name-based coref, which breaks the same-name disambiguation the substrate protects
    ([[node-identity-is-not-a-semantic-proxy]]). So it proves SUFFICIENCY, not the shippable shape.

THE MECHANISM UNDER TEST (the shippable shape). Reconcile ONLY a proposition's participant references
(the nodes a `prop:` handle's `subj`/`obj` edges target), each to the UNAMBIGUOUS discourse referent of its
name — the same-named nodes that are NOT themselves reference-endpoints and that form ONE `denotes` canonical
class. If the referent is AMBIGUOUS (two disjoint same-name classes), REFUSE (leave it to coref judgment) —
so disambiguation is preserved by construction, not by luck. This is `id(F) = (canon(subj), pred, canon(obj))`
reached by completing the `denotes` graph the fetch already reads, using the SANCTIONED boundary relation —
no new partition, no name-union.

In production this reconciliation is REACTIVE (fired when the antecedent assertion arrives / at ask time via
the existing reconsider + reactive-core machinery), not a batch pass; here it is a standalone function applied
post-ingest to isolate the IDENTITY mechanism from the firing schedule.

GO / NO-GO:
  CASE 1 (the fix)  — link-first negation + hedge close (`yes` / banded) after TARGETED reconciliation.
  CASE 2 (no-regress) — antecedent-first still holds; the link stays a QUERYABLE fact ("does A cause B").
  CASE 3 (the guard) — reconciliation REFUSES an ambiguous referent (two disjoint same-name classes),
                       and touches ONLY handle reference-endpoints (never merges two discourse entities).

OWED AT THE BUILD (not this scratch spike — derivation_frame.md says so): the comparative partial-order +
skolem same-name NON-regression is a SUITE-level gate (`test_comparative`, `test_world`,
`test_facts_as_truth_bearers`), plus test_epistemic_closure.py's causation cells flipping REFUSED->PASS
link-first, plus differential forward==demand parity.

PRODUCTION NOTE (SHIPPED 2026-07-23, increment 1). The mechanism is now `ugm/fact_identity.py`, fired
REACTIVELY at the committed-ask gate (`cnl.query.ask_goal`). It evolved in one way from this spike's
standalone function: production ADDS parallel `subj`/`obj` handle edges to the entity (rather than drawing
`denotes`), because the derived consequent must also MATERIALIZE onto the in-scope entity — the `ById`-write
path does not follow `denotes`, so the denotes-only form answered `yes` but left the conclusion out of the
interpretation scope (a LEAK the epistemic-closure gate caught). Because production reconciles at ask time,
this spike's `reconcile=False` "before" rows are now SHADOWED (they get reconciled anyway), so the CASE 1
before/after marks are cosmetic — the spike is kept as the design record; the gate is `test_epistemic_closure.py`.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ugm as h                                                          # noqa: E402
from ugm.attrgraph import AttrGraph                                      # noqa: E402
from ugm.chain import _canon_class                                       # noqa: E402
from ugm.cnl import grammar_intake as gi                                 # noqa: E402
from ugm.cnl.query import ask_goal                                       # noqa: E402
from ugm.policy import BANDED, FirmwarePolicy                            # noqa: E402
from ugm import rule_control                                             # noqa: E402
from ugm.vocabulary import DENOTES                                       # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR = (ROOT / "corpus" / "loudon_grammar.cnl").read_text(encoding="utf-8")
ADJ = "safe is a adj\nhungry is a adj\ndangerous is a adj\n"
BP = FirmwarePolicy(uncertainty=BANDED)


def _kb() -> tuple[AttrGraph, list]:
    kb = AttrGraph()
    gi.declare_grammar(kb, GRAMMAR + ADJ, open_class="noun")
    return kb, []


def _ask(kb, rules, s, p, o, *, policy=None):
    return ask_goal(kb, ("yesno", s, p, o), rule_control.active_rules(kb, rules), policy=policy)


# --- the mechanism under test -----------------------------------------------------------------------

def _prop_handles(kb: AttrGraph) -> list[str]:
    return [n for n in kb.nodes() if str(kb.name(n) or "").startswith("prop:")]


def _reference_endpoints(kb: AttrGraph) -> set[str]:
    """The participant-reference nodes: the targets of every `prop:` handle's `subj`/`obj` edge."""
    refs: set[str] = set()
    for hnode in _prop_handles(kb):
        for rel, obj in kb.relations_from(hnode):
            if kb.has_key(rel, "subj") or kb.has_key(rel, "obj"):
                refs.add(obj)
    return refs


def _merge_classes(classes: list[frozenset[str]]) -> list[set[str]]:
    """Union-find over canonical classes by node-id overlap -> connected components."""
    comps: list[set[str]] = []
    for c in classes:
        hits = [k for k in comps if k & c]
        if not hits:
            comps.append(set(c))
        else:
            first = hits[0]
            first |= c
            for extra in hits[1:]:
                first |= extra
                comps.remove(extra)
    return comps


def reconcile_proposition_refs(kb: AttrGraph) -> list[tuple[str, str]]:
    """TARGETED identity reconciliation (the shippable shape). For each proposition participant reference,
    draw a `denotes` edge to the UNAMBIGUOUS discourse referent of its name — refuse if ambiguous. Returns
    the (endpoint, referent) pairs actually reconciled (for the spike's assertions)."""
    refs = _reference_endpoints(kb)
    drawn: list[tuple[str, str]] = []
    for ep in refs:
        name = kb.name(ep)
        # discourse referents = same-named nodes that are NOT themselves reference-endpoints
        referents = [n for n in kb.nodes()
                     if kb.name(n) == name and n != ep and n not in refs]
        if not referents:
            continue
        classes = _merge_classes([frozenset(_canon_class(kb, r)) for r in referents])
        if len(classes) != 1:
            continue                                    # AMBIGUOUS referent -> refuse (guard)
        target_class = classes[0]
        if ep in target_class:
            continue                                    # already unioned
        # `_canon_class` is ONE-HOP (node + direct denotes neighbours, no transitive closure), so the
        # reference must denote EVERY member of the referent's class to read the fact-carrying node
        # (the entity) directly. Drawing to all members = the reference genuinely denotes that referent.
        for target in sorted(target_class):
            kb.add_relation(ep, DENOTES, target)
            drawn.append((ep, target))
    return drawn


# --- scenarios --------------------------------------------------------------------------------------

def scenario(link: str, fact: str, order: str, *, reconcile: bool, policy=None):
    kb, rules = _kb()
    steps = [link, fact] if order == "link-first" else [fact, link]
    for s in steps:
        h.ingest(kb, rules, s)
    if reconcile:
        reconcile_proposition_refs(kb)
    return kb, rules


NEG = ("that lion has no mane causes that lion is safe", "the lion has no mane", "lion", "is", "safe")
HED = ("that lion generally is hungry causes that lion is dangerous", "lion generally is hungry",
       "lion", "is", "dangerous")


def _ok_yes(ans):  return ans == ["yes"]
def _ok_band(ans): return bool(ans) and ans != ["yes"] and not ans[0].startswith("no")
def _mark(ok):     return "[+]" if ok else "[X]"


def main() -> None:
    print("=" * 96)
    print("FACT-IDENTITY SPIKE — targeted denotes-reconciliation of proposition references (unified-rep §4)")
    print("=" * 96)

    # CASE 1 — the fix: link-first closes AFTER targeted reconciliation (and was broken before).
    print("\n-- CASE 1: link-first, BEFORE vs AFTER targeted reconciliation " + "-" * 32)
    link, fact, s, p, o = NEG
    kb0, r0 = scenario(link, fact, "link-first", reconcile=False)
    kb1, r1 = scenario(link, fact, "link-first", reconcile=True)
    a0, a1 = _ask(kb0, r0, s, p, o), _ask(kb1, r1, s, p, o)
    print(f"  negation  before {_mark(not _ok_yes(a0))} {str(a0):18}  ->  after {_mark(_ok_yes(a1))} {a1}")
    link, fact, s, p, o = HED
    kb0, r0 = scenario(link, fact, "link-first", reconcile=False, policy=BP)
    kb1, r1 = scenario(link, fact, "link-first", reconcile=True, policy=BP)
    a0, a1 = _ask(kb0, r0, s, p, o, policy=BP), _ask(kb1, r1, s, p, o, policy=BP)
    print(f"  hedge     before {_mark(not _ok_band(a0))} {str(a0):18}  ->  after {_mark(_ok_band(a1))} {a1}")

    # CASE 2 — no-regression: antecedent-first still holds; reconciliation is a no-op there.
    print("\n-- CASE 2: antecedent-first still holds (reconciliation must not break it) " + "-" * 20)
    link, fact, s, p, o = NEG
    kb, r = scenario(link, fact, "antecedent-first", reconcile=True)
    a = _ask(kb, r, s, p, o)
    print(f"  negation  antecedent-first + reconcile {_mark(_ok_yes(a))} {a}")

    # CASE 3 — anti-seam: reconciliation is TARGETED (draws only FROM handle reference-endpoints),
    # NOT the brute same-name union. This is the property that keeps it off the seam; the AMBIGUOUS-
    # referent disambiguation non-regression (comparative + skolem same-name) is a SUITE-level gate
    # owed at the build (derivation_frame.md), not faithfully constructible in a bare declare+ingest KB
    # (name-interning already collapses same-name discourse nodes into one referent here).
    print("\n-- CASE 3: anti-seam — reconciliation draws ONLY from handle reference-endpoints " + "-" * 12)
    kb, r = scenario(NEG[0], NEG[1], "link-first", reconcile=False)
    endpoints = _reference_endpoints(kb)
    drawn = reconcile_proposition_refs(kb)
    from_refs_only = all(ep in endpoints for ep, _ in drawn)
    touched_names = sorted({kb.name(ep) for ep, _ in drawn})
    print(f"  drew {len(drawn)} denotes edge(s); every source is a proposition reference-endpoint "
          f"{_mark(from_refs_only)}")
    print(f"  names reconciled = {touched_names} (the proposition's participants only, not every 'lion')")

    print("\n" + "=" * 96)
    print("READ: CASE 1 both '+' after / '+' before-is-broken => targeted reconciliation CLOSES link-first")
    print("without brute name-union. CASE 2 '+' => no regression. CASE 3 '+' => targeted, not brute (anti-")
    print("seam). GO iff all '+'. Suite-level disambiguation + comparative non-regression owed at build.")


if __name__ == "__main__":
    main()
