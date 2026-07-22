"""FACTS-AS-TRUTH-BEARERS SPIKE (primitive ② / causation C3) — where is the wall, and how wide?

WHY THIS EXISTS. `form_inventory.md` §9.3 names TWO fundamental primitives: ① scope generalization
(built) and ② facts-as-truth-bearers. ② is causation's propositional COMPLETION (C3): "A holds and A
causes B ⇒ B holds", where A and B are whole PROPOSITIONS, not entities+conditions (that is C1, native).
`spike_binder.py::probe_C3` recorded it as a flat GAP with two hard stops — "the rule grammar requires
every clause to be exactly S-P-O (so `?b holds` is unwritable), and there is no dereify operator."

This spike RE-PROBES that verdict at the machine layer, because this arc's method is: probe first, the
wall is usually narrower than the summary. And it is. The realization under test is the classic
REIFICATION BRIDGE, expressed as DECLARED DATA (honouring "domain logic ONLY in banks", "causation is
not privileged"):

    a proposition P = "s p o" gets a HANDLE entity h carrying `h subj s`, `h pred p`, `h obj o`;
    reify:   `?h truth yes when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?s ?p ?o`
    MP:      `?b truth yes when ?a truth yes and ?a causes ?b`          (pure S-P-O over handles)
    dereify: `?s ?p ?o when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?h truth yes`

If those three declared rules worked, C3 would be declared-data, not engine — like the rest of the arc.

VERDICTS: NATIVE (works now) / GAP (needs an engine mechanism). Read the output as: which of the three
bridge rules already work, and what the ONE missing mechanism is.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm import assemble_facts, derived_triples, run_bank                # noqa: E402
from ugm.attrgraph import AttrGraph                                      # noqa: E402
from ugm.check import POSITIVE, check                                    # noqa: E402
from ugm.cnl.machine_rules import load_machine_rules                     # noqa: E402
from ugm.machine import Machine                                          # noqa: E402

NATIVE, GAP = "NATIVE", "GAP"


def _facts(facts):
    g = AttrGraph()
    triples = [tuple(f.split()) if isinstance(f, str) else f for f in facts]
    if triples:
        Machine().run(g, assemble_facts(triples))
    return g


def _forward(facts, rules_text):
    """Build a KB, run the bank FORWARD, return the derived triple set."""
    g = _facts(facts)
    rules = []
    for rt in rules_text:
        rules += load_machine_rules(rt)
    run_bank(g, rules)
    return g, set(derived_triples(g))


REIFY = "?h truth yes when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?s ?p ?o"
MP = "?b truth yes when ?a truth yes and ?a causes ?b"
DEREIFY = "?s ?p ?o when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?h truth yes"

# The two named propositions of the running example, hand-reified into handles.
HANDLES = [
    "ha subj door1", "ha pred is", "ha obj open",      # A = (door1 is open)
    "hb subj cat", "hb pred flees", "hb obj yes",       # B = (cat flees yes)
    "ha causes hb",                                      # the PROPOSITIONAL causal link
]


def probe_authoring():
    """Is a variable-predicate clause even authorable? The spike said clauses must be S-P-O. In fact a
    3-token `?s ?p ?o` authors fine (only the 2-token `?b holds` is rejected — arity, not predicate-var)."""
    ok3 = ok2 = None
    try:
        load_machine_rules(REIFY); ok3 = True
    except Exception:
        ok3 = False
    try:
        load_machine_rules("?b holds when ?a causes ?b"); ok2 = True
    except Exception:
        ok2 = False
    return (NATIVE if ok3 and not ok2 else GAP,
            f"3-token var-pred `?s ?p ?o` authorable={ok3}; 2-token `?b holds` authorable={ok2} "
            f"(the spike's 'clauses must be S-P-O' conflated arity with predicate-vars)")


def probe_dereify_forward():
    """DEREIFY — a variable-predicate HEAD with `?p` LHS-bound (`?h pred ?p`). The spike said 'no
    dereify operator'. It already works FORWARD: a true handle asserts its underlying edge."""
    _g, tr = _forward(
        ["ha subj cat", "ha pred flees", "ha obj yes", "ha truth yes"],
        [DEREIFY])
    got = ("cat", "flees", "yes") in tr
    return (NATIVE if got else GAP,
            f"dereify (var-pred HEAD, ?p LHS-bound) -> asserts (cat,flees,yes)={got}")


def probe_mp_over_handles():
    """PROPOSITIONAL MP itself — `?b truth yes when ?a truth yes and ?a causes ?b`. Pure S-P-O over
    handle entities; `causes` is an ordinary relation between them. Given A already true, B goes true."""
    _g, tr = _forward(["ha truth yes"] + HANDLES, [MP])
    got = ("hb", "truth", "yes") in tr
    return (NATIVE if got else GAP,
            f"MP: hb.truth from ha.truth & ha causes hb ={got} (propositional MP is S-P-O)")


def probe_reify_forward():
    """⭐ THE ONE WALL — REIFY: reading a fact THROUGH A BOUND PREDICATE VARIABLE. `?p` is LHS-bound by
    `?h pred ?p`, then used as the predicate of `?s ?p ?o`. The lowerer demands a GROUND predicate
    anchor and cannot lower a body pattern whose predicate is a variable, so the handle never learns its
    edge holds. This is the missing mechanism: match a fact through a bound predicate variable."""
    _g, tr = _forward(["door1 is open"] + HANDLES, [REIFY])
    got = ("ha", "truth", "yes") in tr
    return (NATIVE if got else GAP,
            f"reify: ha.truth from (door1 is open) via bound-pred read `?s ?p ?o` ={got} "
            f"(FAILS: body pattern with a variable predicate has 'no ground anchor')")


def probe_full_pipeline_forward():
    """The three bridge rules together, FORWARD. Fails at REIFY, so the consequent edge never lands —
    isolating that the whole declared-data route hinges on the single bound-predicate-read mechanism."""
    _g, tr = _forward(["door1 is open"] + HANDLES, [REIFY, MP, DEREIFY])
    got = ("cat", "flees", "yes") in tr
    return (GAP if not got else NATIVE,
            f"full declared bridge: (door1 is open) => (cat flees yes) ={got} "
            f"(blocked only at REIFY; dereify+MP are native)")


def probe_demand_reachability():
    """Even the pieces that fire FORWARD are unreachable on the DEMAND path (`check`/`ask_goal`): the
    head index (`apply.build_head_index`) catalogs rules by their CONCRETE head predicate, so a
    variable-predicate head indexes under the literal '?p', never under the demanded predicate. So a
    second facet of the same primitive: variable-predicate rules must be demand-reachable."""
    g = _facts(["ha subj cat", "ha pred flees", "ha obj yes", "ha truth yes"])
    for r in load_machine_rules(DEREIFY):
        from ugm.cnl.rule_graph import write_rule
        write_rule(g, r)
    v = check(g, ("flees", "cat", "yes"))
    return (GAP if v != POSITIVE else NATIVE,
            f"demand check(cat flees yes) with dereify rule -> {v} "
            f"(var-pred head not in the concrete head index; forward-only today)")


PROBES = [
    ("authoring: var-pred clause", probe_authoring),
    ("dereify FORWARD (var-pred head)", probe_dereify_forward),
    ("propositional MP over handles", probe_mp_over_handles),
    ("REIFY FORWARD (bound-pred read) — THE WALL", probe_reify_forward),
    ("full declared bridge FORWARD", probe_full_pipeline_forward),
    ("demand reachability of var-pred rules", probe_demand_reachability),
]


def main() -> None:
    print("=" * 78)
    print("FACTS-AS-TRUTH-BEARERS (C3) — reification bridge as declared data")
    print("=" * 78)
    for label, probe in PROBES:
        verdict, note = probe()
        print(f"  [{verdict:6}] {label}")
        print(f"           {note}")
    print("-" * 78)
    print("SUMMARY: dereify + propositional-MP are NATIVE; the ONE fundamental gap is READING A FACT")
    print("THROUGH A BOUND PREDICATE VARIABLE (reify), plus demand-reachability of var-pred rules.")
    print("Both are facets of ONE mechanism: predicate-variable matching, not causation-specific.")


if __name__ == "__main__":
    main()
