"""
Riddles — small logic puzzles as an INTEGRATION probe over the whole stack at once
(reasoning + question-answering + explanation), and the forcing-function for the negation work
(firmware v3, demand-driven NAF). Unlike ProofWriter (which loads a formal theory), a riddle is
authored as a domain and SOLVED by elimination: the answer is the entity for which a closed-world
property CANNOT be derived — so it exercises DEMAND-DRIVEN NEGATION-AS-FAILURE end to end (`chain_sip`
deciding a NAC by nested negative demand, absence-decides), then answers with the real `ask_goal`
surface and explains from the in-graph provenance a demand-with-RECORD pass minted.

First riddle — "the thief":
  - suspects ada, bo, cy; exactly one is the thief.
  - bo was in the library; anyone in the library is innocent; an innocent suspect is cleared.
  - ada has an alibi; anyone with an alibi is cleared.
  - the thief is the suspect who is NOT cleared.
Solving it needs (a) multi-step deduction (in library -> innocent -> cleared), (b) closed-world
elimination BY DEMAND (to decide `thief(cy)`, demand the positive `cleared(cy)` to closure; it comes
back empty, so `not cleared` holds — NOTHING is materialized for the negative), (c) a wh-answer
(who is the thief -> cy), and (d) a why-trace grounding `cy is thief` on the given suspect premise.

AUTHORED ENTIRELY IN CNL. The whole riddle — facts, the (now-vestigial) `cleared is closed world`
declaration, the producer rules, AND the consumer (`?x is thief when ?x is a suspect and ?x is not
cleared`) — is one corpus loaded by `load_corpus`. The consumer's `is not cleared` clause is a NAC,
decided ON DEMAND by negation-as-failure — NO closed-world upgrade to a positive `is_not` match, NO
generated completion rule (the retired forward `decide.solve` apparatus, firmware v3). The
suspects-to-decide are DISCOVERED by the positive residual (`?x is a suspect`), not hand-listed.

WHAT THESE RIDDLES SURFACE:
  CONFIRMED working, composed in one problem, all in CNL:
   - multi-step deduction feeds a closed-world decision on demand (`in library -> innocent -> cleared`,
     then `not cleared` decided by the empty demand closure);
   - wh-answer + yes/no-answer + why-trace all compose over a DERIVED predicate (`who is thief`);
   - the elimination is HONEST: `cleared(cy)` is an ASSUMED_NO with a renderable "where I looked", not
     a materialized negative — the agent-not-theorem-prover reading.
  GAP the riddles still pin (the "what to build next" signal):
   - NO CONSTRUCTIVE DISJUNCTION / EXHAUSTION. These riddles are framed so the answer is "the one we
     cannot clear" — which NAF gives directly. A puzzle whose answer must be derived POSITIVELY by
     ruling out alternatives ("not red and not blue, so GREEN holds the prize"), or that needs
     "EXACTLY ONE holds", is NOT expressible: NAF gives the negative, not existence-from-exhaustion,
     and there is no "exactly one" quantifier yet. The deferred indefinite-existentials / uniqueness
     axis — the boundary to keep riddles clear of until it is built.
"""
import ugm as h
from ugm import provenance as prov
from ugm.cnl.authoring import load_corpus
from ugm.cnl.forms import SURFACE_TAGS
from ugm.cnl.query import ask_goal


def _clean(g: h.Graph) -> None:
    """Drop the RECOGNITION-time provenance (form-firing justifications + proves/uses) and the
    surface token chain, so the base facts read as `(given)` leaves and an explanation shows only
    REASONING (the batch loaders keep this scaffolding; the interactive Session strips it via
    `_strip_surface`). Cosmetic-but-important: it is what makes a why-trace legible. Reasoning has
    not run yet, so nothing depends on these nodes; the CWA marker (`closes <closed_world>`) and
    the recognized facts/rules survive."""
    for n in [n for n in g.nodes()
              if prov.is_justification(g.name(n)) or g.predicate(n) in prov.PROVENANCE_PREDS]:
        g.remove_node(n)
    for nm in ("next", "first", "<sentence>", *SURFACE_TAGS):
        for n in list(g.nodes_named(nm)):
            g.remove_node(n)
    g.gc_disconnected()


# The thief — authored ENTIRELY in CNL. `cleared is closed world` is the CWA declaration; the
# consumer's `is not cleared` reflects to a decided negation (positive `is_not` match + a seeded
# `<decide>`), so there is no hand-built rule and no explicit suspects list.
THIEF_RIDDLE = dict(
    name="the thief",
    corpus="""
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
    """,
    question="who is thief",
    answer=["cy is thief"],
)


# The broken vase — a second, independent riddle: a different query surface (yes/no + why-not),
# a different subject kind (pet), single-step deduction. Confirms the CNL decide-consumer path is
# not a one-off.
VASE_RIDDLE = dict(
    name="the broken vase",
    corpus="""
        rex is a pet
        sam is a pet
        tia is a pet
        rex in yard
        sam in yard

        cleared is closed world

        ?x is cleared when ?x in yard

        ?x is culprit when ?x is a pet and ?x is not cleared
    """,
    question="who is culprit",
    answer=["tia is culprit"],
)


def _solve(riddle: dict):
    """Author the riddle in CNL, returning (graph, rules). Reasoning is DEMAND-DRIVEN (firmware v3) at
    QUERY time — each `ask_goal` demands just its goal, deciding the closed-world `is not cleared` clause
    on demand by negation-as-failure (nested negative demand -> positive closure -> absence decides).
    Nothing is materialized up front; `_clean` only strips recognition scaffolding."""
    g, rules = load_corpus(riddle["corpus"])
    _clean(g)
    return g, rules


def _holds(g, name, pred, obj):
    """Does any mention of `name` carry `--pred--> (a node named obj)`? (node-agnostic under additive
    coref — a derived fact may land on the same_as-class canonical mention)."""
    return any(g.has_key(r, pred) and any(g.name(o) == obj for o in g.out(r))
               for n in g.nodes_named(name) for r in g.out(n))


def test_thief_riddle_solved_by_elimination():
    g, rules = _solve(THIEF_RIDDLE)
    ask_goal(g, "who is thief", rules)                # demand-drive the elimination into the graph
    # the deduction chain ran on demand: bo cleared via library->innocent->cleared; ada via alibi
    assert _holds(g, "bo", "is", "cleared")
    assert _holds(g, "ada", "is", "cleared")
    # cy could NOT be cleared -> `not cleared(cy)` holds by ABSENCE (NAF); NOTHING is materialized for
    # the negative — there is no `is_not` fact (the whole point vs. forward completion).
    assert not _holds(g, "cy", "is", "cleared")
    assert not any(t[1] == "is_not" for t in h.derived_triples(g))
    assert _holds(g, "cy", "is", "thief")             # ... so cy is the thief


def test_thief_riddle_answers_the_question():
    g, rules = _solve(THIEF_RIDDLE)
    assert ask_goal(g, THIEF_RIDDLE["question"], rules) == THIEF_RIDDLE["answer"]   # cy is thief
    # and it is the UNIQUE answer (no other suspect is the thief)
    assert ask_goal(g, "is ada thief", rules) == ["no (assumed)"]
    assert ask_goal(g, "is cy thief", rules) == ["yes"]


def test_thief_riddle_explains_the_answer():
    g, rules = _solve(THIEF_RIDDLE)
    text = "\n".join(ask_goal(g, "why cy is thief", rules))
    # the trace names the (CNL-authored) thief rule and grounds `cy is thief` on the given suspect
    # premise. Under NAF there is NO `is_not`/`complete` step — the elimination is the ABSENCE of a
    # `cleared(cy)` derivation, not a materialized negative.
    assert "cy is thief" in text and "rule.?x.is.thief" in text
    assert "is_not" not in text and "complete" not in text


def test_thief_riddle_cy_is_not_cleared_is_an_assumed_no():
    # The elimination as the demand-driven firmware sees it: CHECK `cleared(cy)` -> ASSUMED_NO (closed-
    # world default, and the positive was not derivable), with a renderable "where I looked". No
    # negative is materialized; the verdict is computed from the (empty) demand closure.
    g, rules = _solve(THIEF_RIDDLE)
    rg = h.AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    status = h.check(g, ("is", "cy", "cleared"), rules=rg)
    assert status == h.ASSUMED_NO
    assert h.collapse(status) == "no"
    assert any("cy is cleared" in ln for ln in h.explain_check(status, rg))   # the demand it explored


def test_vase_riddle_yesno_and_why_not():
    # A second, independent riddle: yes/no answers over a derived predicate + a why-not.
    g, rules = _solve(VASE_RIDDLE)
    assert ask_goal(g, VASE_RIDDLE["question"], rules) == VASE_RIDDLE["answer"]
    assert ask_goal(g, "is tia culprit", rules) == ["yes"]
    assert ask_goal(g, "is rex culprit", rules) == ["no (assumed)"]
    # "rex is NOT the culprit" bottoms out at a real derivation: rex was cleared (in the yard).
    assert ask_goal(g, "is rex cleared", rules) == ["yes"]
    why = "\n".join(ask_goal(g, "why tia is culprit", rules))
    assert "tia is culprit" in why and "is_not" not in why   # elimination by absence, no materialized negative


def test_riddles_author_entirely_in_cnl():
    # The point of handoff step 1: no hand-built decide-consumer, no Python seeding — the consumer is a
    # real CNL rule (`?x is thief when ...`). Under DEMAND-DRIVEN NEGATION (firmware v3) its closed-world
    # `is not cleared` clause stays a NAC, decided on demand — NO upgrade to a positive `is_not` match,
    # NO generated completion rule (the retired forward apparatus).
    _g, rules = _solve(THIEF_RIDDLE)
    thief = next(r for r in rules if r.key == "rule.?x.is.thief")
    assert ("?x", "is", "cleared") in {p.tokens() for p in thief.nac}        # the clause stays a NAC
    assert not any(p.p == "is_not" for p in thief.lhs)                       # NOT upgraded to a positive
    assert not any(r.key.startswith("decide.complete") for r in rules)      # NO completion rule
