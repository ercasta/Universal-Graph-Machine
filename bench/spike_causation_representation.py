"""Spike: does a UNIFORM proposition representation dissolve the causation composition gaps + order bug?

THE QUESTION (design discussion 2026-07-23; composition_architecture.md §GAPS). Propositional causation
`that A causes that B` currently reifies each proposition into a content-keyed HANDLE (`prop:X:Y:Z` with
DUPLICATED `subj`/`pred`/`obj` edges) joined by a `causes` edge, plus three bridge rules (reify / MP /
dereify). That handle is a SECOND representation of a proposition, unreconciled with the substrate's
NATIVE one - the relation node in the S-P-O path (the node the band/scope already hang on). The claim is
that this duality is the root of two separate-looking problems:

  (a) the LINK-FIRST ORDER BUG - stating the link before its antecedent mints a THIRD co-named node
      (the handle's `subj lion`, interned by NAME, with no `denotes` link to the grammar fold's entity),
      so the reify join misses it;
  (b) the causation o {hedge, negation} COMPOSITION GAPS - the crisp handle does not carry the
      antecedent proposition's band/negation across the reification boundary.

THE ALTERNATIVE TESTED HERE. For a GROUND `that A causes that B`, lower it to a RULE `B <= A` - the
substrate's native conditional, which lives INSIDE the one evaluation (`chain_sip` over rules under a
policy). No handle, no duplicated edges, no bridge. Prediction: it composes for FREE (exactly as
`conditional o {hedge, negation}` already do in the audit) and is order-independent (rules re-evaluate
every ask). This isolates whether the HANDLE was carrying its weight or was the whole problem.

HONEST TRADEOFF this also measures: the handle makes the LINK a first-class queryable fact ("does A
cause B?") and lets links chain through DERIVED intermediate propositions. The rule lowering keeps
chaining (rules chain natively) but the link is no longer a fact you can ask about. Both halves reported.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ugm as h                                                          # noqa: E402
from ugm.attrgraph import AttrGraph                                      # noqa: E402
from ugm.cnl import cause_surface, grammar_intake as gi                 # noqa: E402
from ugm.cnl.query import _reify_rules, ask_goal                        # noqa: E402
from ugm.policy import BANDED, FirmwarePolicy                           # noqa: E402
from ugm.production_rule import Pat, Rule                               # noqa: E402
from ugm import rule_control                                            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR = (ROOT / "corpus" / "loudon_grammar.cnl").read_text(encoding="utf-8")
ADJ = "safe is a adj\nhungry is a adj\ndangerous is a adj\n"
BP = FirmwarePolicy(uncertainty=BANDED)


def _kb():
    kb = AttrGraph()
    gi.declare_grammar(kb, GRAMMAR + ADJ, open_class="noun")
    return kb, []


# --- the ALTERNATIVE: lower a ground `that A causes that B` to a rule B <= A ------------------------

def _hedges(kb) -> dict:
    banks = kb.registers.get("grammar")
    return dict(banks.grammar.hedge_bands) if banks is not None else {}


def ingest_cause_as_rule(kb, rules, line: str) -> None:
    """Instead of `intake`'s handle bridge, lower a ground propositional cause to a plain RULE `B <= A`
    and append it to the rule list - the substrate's native conditional, evaluated by `chain_sip`.
    The hedge lexicon is threaded so a hedged antecedent strips to its clean triple (the band lives on
    the fork the fact route pens; the ground rule's premise then matches it banded)."""
    pc = cause_surface.parse_cause(line, _hedges(kb))
    assert pc is not None, line
    (a_s, a_p, a_o), (b_s, b_p, b_o) = pc
    rules.append(Rule(key=f"cause::{a_s}.{a_p}.{a_o}=>{b_s}.{b_p}.{b_o}",
                      lhs=[Pat(a_s, a_p, a_o)], rhs=[Pat(b_s, b_p, b_o)]))


def ask(kb, rules, s, p, o, *, policy=None):
    active = rule_control.active_rules(kb, rules)
    return ask_goal(kb, ("yesno", s, p, o), active, policy=policy)


# ---------------------------------------------------------------------------
# The cases - each run under BOTH representations and BOTH statement orders
# ---------------------------------------------------------------------------

def scenario_negation(order: str, mode: str):
    """`that lion has no mane causes that lion is safe` + `the lion has no mane`; ask `is lion safe`."""
    kb, rules = _kb()
    link = "that lion has no mane causes that lion is safe"
    fact = "the lion has no mane"
    steps = [link, fact] if order == "link-first" else [fact, link]
    for s in steps:
        if s == link and mode == "rule":
            ingest_cause_as_rule(kb, rules, s)
        else:
            h.ingest(kb, rules, s)
    return ask(kb, rules, "lion", "is", "safe")


def scenario_hedge(order: str, mode: str):
    """`that lion generally is hungry causes that lion is dangerous` + `lion generally is hungry`;
    ask `is lion dangerous` BANDED."""
    kb, rules = _kb()
    link = "that lion generally is hungry causes that lion is dangerous"
    fact = "lion generally is hungry"
    steps = [link, fact] if order == "link-first" else [fact, link]
    for s in steps:
        if s == link and mode == "rule":
            ingest_cause_as_rule(kb, rules, s)
        else:
            h.ingest(kb, rules, s)
    return ask(kb, rules, "lion", "is", "dangerous", policy=BP)


def scenario_chain(mode: str):
    """CHAINING through a DERIVED intermediate: A->B->C, only A asserted; ask C.
    `door1 is open` ; that door1 is open causes that cat is scared ; that cat is scared causes that dog
    is alert ; ask `is dog alert`."""
    kb, rules = _kb()
    h.ingest(kb, rules, "open is a adj")
    h.ingest(kb, rules, "scared is a adj")
    h.ingest(kb, rules, "alert is a adj")
    h.ingest(kb, rules, "door1 is open")
    for link in ("that door1 is open causes that cat is scared",
                 "that cat is scared causes that dog is alert"):
        if mode == "rule":
            ingest_cause_as_rule(kb, rules, link)
        else:
            h.ingest(kb, rules, link)
    return ask(kb, rules, "dog", "is", "alert")


def scenario_link_as_fact(mode: str):
    """Can you ASK about the link itself - `does A cause B`? Only the handle representation makes the
    link a queryable fact. Measured as `causes` between the two propositions' handles."""
    kb, rules = _kb()
    link = "that door1 is open causes that cat is scared"
    if mode == "rule":
        ingest_cause_as_rule(kb, rules, link)
    else:
        h.ingest(kb, rules, "door1 is open")
        h.ingest(kb, rules, link)
    # the handle representation names the propositions `prop:door1:is:open` / `prop:cat:is:scared`
    ha = cause_surface.handle_name(("door1", "is", "open"))
    hb = cause_surface.handle_name(("cat", "is", "scared"))
    return ask(kb, rules, ha, "causes", hb)


def _mark(ans, want) -> str:
    ok = (ans == want) if want != "band" else (bool(ans) and ans != ["yes"]
                                               and not ans[0].startswith("no"))
    return f"[{'+' if ok else 'X'}] {str(ans):20}"


def main() -> None:
    print("=" * 92)
    print("CAUSATION REPRESENTATION SPIKE - content-keyed HANDLE vs native RULE (B <= A)")
    print("=" * 92)

    print("\n-- causation o NEGATION  (want ['yes']) " + "-" * 50)
    for order in ("antecedent-first", "link-first"):
        hb = scenario_negation(order, "handle")
        rl = scenario_negation(order, "rule")
        print(f"  {order:17}  HANDLE {_mark(hb, ['yes'])}   RULE {_mark(rl, ['yes'])}")

    print("\n-- causation o HEDGE     (want a band word, e.g. ['likely']) " + "-" * 30)
    for order in ("antecedent-first", "link-first"):
        hb = scenario_hedge(order, "handle")
        rl = scenario_hedge(order, "rule")
        print(f"  {order:17}  HANDLE {_mark(hb, 'band')}   RULE {_mark(rl, 'band')}")

    print("\n-- CHAINING through a derived intermediate  (want ['yes']) " + "-" * 32)
    print(f"  A->B->C, only A asserted  HANDLE {_mark(scenario_chain('handle'), ['yes'])}   "
          f"RULE {_mark(scenario_chain('rule'), ['yes'])}")

    print("\n-- THE TRADEOFF: is the LINK a queryable fact?  `does A cause B` (want ['yes']) " + "-" * 12)
    print(f"  ask the causes-link       HANDLE {_mark(scenario_link_as_fact('handle'), ['yes'])}   "
          f"RULE {_mark(scenario_link_as_fact('rule'), ['yes'])}")

    print("\n" + "=" * 92)
    print("READ: RULE '+' on the composition/order cells where HANDLE is 'X' => the handle DUALITY was the")
    print("problem, not the composition axis. A HANDLE '+' on the link-as-fact cell where RULE is 'X' => the")
    print("cost of dropping the handle (the link stops being a queryable proposition).")


if __name__ == "__main__":
    main()
