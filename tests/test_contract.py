"""
Behavioral CONTRACT suite — representation-INDEPENDENT tests that pin what the system DOES, not
how it is built, so parts of the engine can be SWAPPED later against a fixed spec (the HRG /
clingo-calculator / SLM-front-end / Joern-extractor swaps discussed in docs/vision_agentic.md).

THE DISCIPLINE (the whole point — read before adding a case):
  - Arrange and assert ONLY through the PUBLIC surface: CNL in (`load_corpus` / `Session.submit`),
    answers out (`ask` / `.answer` / `.new_facts` / `.facts()`). Every assertion is a STRING or a
    recognition boolean.
  - NEVER touch internals: no `Graph` traversal (`_has`, `g.out`, node scans), no `Rule.lhs`/`.key`,
    no journal node names, no provenance node shapes, no exact confidence numbers. Those are the
    MECHANISM. A future engine (HRG-backed, clingo-delegated, a different matcher, an SLM front-end)
    would have entirely different internals but must keep EVERY assertion in this file green.
  - Where behavior is a ranking rather than an exact value (the graded layer), assert the RANKING,
    not the number — the number is implementation, the order is contract.

CONTRAST: tests/test_new_core.py, test_riddles.py, test_code_frames.py etc. are IMPLEMENTATION
regression tests — they assert on lhs token-tuples, node names, `_has(...)`, journal internals.
Those are the right tool for defending the CURRENT engine and the wrong tool for a swap net,
precisely because they are coupled to the representation. This file is the swap net; keep the two
kinds separate and do not let internals leak in here.

FUTURE: when a second engine exists, lift each scenario's (corpus, question, expected) triples into
a fixture parametrized over a thin engine adapter, and run the SAME cases against both. Today there
is one engine, so the scenarios are plain functions and the "adapter" is just the public API. Do
NOT build the adapter indirection before the second engine is real (YAGNI, per the vision's own
"don't build machinery before the risk is").
"""
import ugm as h


# ===========================================================================
# Scenario 1 — graded + defeasible routing (the matcher + graded + NAC seams)
# ===========================================================================
# Exercises: gradable embedding from an adverb, a NAC-gated default that a derived fact defeats,
# and multi-clause relational rules. Any engine must route the three customers the same way.

ICE_CREAM = """
    urgent is gradable
    vanilla is in_stock
    chocolate is in_stock
    alice is a customer
    alice wants vanilla
    alice is very urgent
    bob is a customer
    bob wants chocolate
    carol is a customer
    carol wants strawberry
    ?c is urgent when ?c is a customer and ?c is very urgent
    ?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock
    ?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent
    ?c offered alternative when ?c is a customer and ?c wants ?f and ?f is not in_stock
"""


def test_contract_graded_defeasible_routing():
    kb, rules = h.load_corpus(ICE_CREAM)
    h.run_rules(kb, rules)

    # each customer is routed to exactly the right outcome...
    assert h.ask(kb, "is alice served express") == ["yes"]        # graded urgency -> express
    assert h.ask(kb, "is bob served regular") == ["yes"]          # calm + in stock -> regular
    assert h.ask(kb, "is carol offered alternative") == ["yes"]   # out of stock -> alternative

    # ...and the NAC-gated default REALLY defeats: the derived `is urgent` keeps bob off express
    # and alice off regular (soundness of the closed-world guard, not just presence of an answer).
    assert h.ask(kb, "is bob served express") == ["no"]
    assert h.ask(kb, "is alice served regular") == ["no"]

    # a wh-question over the same derived predicate
    assert sorted(h.ask(kb, "who served express")) == ["alice served express"]


# ===========================================================================
# Scenario 2 — closed-world elimination (the negation / defeasibility seam)
# ===========================================================================
# The "thief" riddle solved by elimination: cy cannot be cleared, so the closed-world negative is
# completed and cy is the thief. This is the seam a clingo calculator might one day back; the
# contract is the ANSWER and that the explanation bottoms out at the elimination, not the mechanism.

THIEF = """
    ada is a suspect
    bo is a suspect
    cy is a suspect
    bo in library
    ada is alibied
    cleared is closed world
    ?x is innocent when ?x in library
    ?x is cleared when ?x is innocent
    ?x is cleared when ?x is alibied
    ?x is thief when ?x is a suspect and ?x is not cleared
"""


def test_contract_closed_world_elimination():
    # Engine swap (the whole point of this suite): the closed-world elimination runs DEMAND-DRIVEN
    # (firmware v3 — the `is not cleared` clause is a NAC decided on demand by negation-as-failure; NO
    # aggressive `is_not` completion, NO retraction / fact-edge cut), with `why` read from the in-graph
    # provenance the demand pass MINTs. Same public contract as the retired forward `decide.solve` path.
    kb, rules = h.load_corpus(THIEF)

    # solved by elimination, and UNIQUELY — one demand-driven `ask_goal` per question.
    assert h.ask_goal(kb, "who is thief", rules) == ["cy is thief"]
    assert h.ask_goal(kb, "is cy thief", rules) == ["yes"]
    assert h.ask_goal(kb, "is ada thief", rules) == ["no (assumed)"]
    assert h.ask_goal(kb, "is bo thief", rules) == ["no (assumed)"]

    # the explanation grounds `cy is thief` on the given suspect premise. Under demand-driven NAF the
    # trace has NO `is_not`/completion step — the elimination is the ABSENCE of a `cleared(cy)`
    # derivation, not a materialized negative. Reload fresh so the `why` demand DERIVES thief(cy) WITH
    # provenance (the prior queries derived it without) — `explain` reads the in-graph proves/uses support.
    kb2, rules2 = h.load_corpus(THIEF)
    why = "\n".join(h.ask_goal(kb2, "why cy is thief", rules2))
    assert "cy is thief" in why and "rule.?x.is.thief" in why
    assert "is_not" not in why and "complete" not in why


# ===========================================================================
# Scenario 3 — compositional code hazard (the extraction + composition seam)
# ===========================================================================
# The Stage-1 queryset-mutation-during-iteration hazard, authored ENTIRELY through the CNL surface
# via the interactive `Session` (definite `the` merges each mention to one node, standing in for a
# real extractor's stable ids). The hazard is DERIVED by composing two mechanism rules. This is the
# behavior a Joern-fed engine must reproduce; the contract is the yes/no answer, not how the frames
# are stored.
#
# NB: this scenario uses `Session.submit` line-by-line rather than `load_corpus`, because the
# declared-relation catalog (`iterate is a relation`) is currently applied only on the SEQUENTIAL
# path — the batch loaders do not sequence declaration-before-use (a known NL-front-end gap, see
# docs/handoff_redesign.md). `Session.submit` is equally a public, representation-independent surface.

def _hazard_session(mutation_target):
    s = h.Session()
    for line in (
        "the is a definite",
        "iterate is a relation", "mutate is a relation",
        "consume is a relation", "contain is a relation",
        "the loop is a iteration",
        "the loop iterate the queryset",
        "the deletion is a mutation",
        f"the deletion mutate the {mutation_target}",
        "the loop contain the deletion",
        "?loop consume ?c when ?loop is a iteration and ?loop iterate ?c",
        "?m is unsafe when ?m is a mutation and ?m mutate ?c "
        "and ?loop contain ?m and ?loop consume ?c",
    ):
        s.submit(line)
    return s




