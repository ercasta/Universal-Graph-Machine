"""
Riddles — small logic puzzles as an INTEGRATION probe over the whole stack at once
(reasoning + question-answering + explanation), and the forcing-function for the negation
work (`decide.py`). Unlike ProofWriter (which loads a formal theory), a riddle is authored as
a domain and SOLVED by elimination: the answer is the entity for which a closed-world property
CANNOT be derived — so it exercises `decide.complete` (materialize the explicit negative) end
to end, then answers with the real `ask` surface and explains with the real `explain` traversal.

First riddle — "the thief":
  - suspects ada, bo, cy; exactly one is the thief.
  - bo was in the library; anyone in the library is innocent; an innocent suspect is cleared.
  - ada has an alibi; anyone with an alibi is cleared.
  - the thief is the suspect who is NOT cleared.
Solving it needs (a) multi-step deduction (in library -> innocent -> cleared), (b) closed-world
elimination (cy is cleared by nothing, so `cy is_not cleared` is COMPLETED), (c) a wh-answer
(who is the thief -> cy), and (d) a why-trace bottoming out at the completion.

AUTHORED ENTIRELY IN CNL (handoff step 1, DONE). The whole riddle — facts, the per-predicate
CWA declaration (`cleared is closed world`), the producer rules, AND the decide-consumer
(`?x is thief when ?x is a suspect and ?x is not cleared`) — is one corpus loaded by
`load_corpus`. The consumer's closed-world `is not cleared` clause is no longer a NAC: the
reflection (`authoring.expand_rules`) UPGRADES it into a positive `?x is_not cleared` match and
emits a companion `<decide>` demand rule that seeds the decision from the positive residual
(`?x is a suspect`) — so the suspects-to-decide are DISCOVERED, not hand-listed. `decide.solve`
interleaves the monotone deduction with `complete`/`recheck` to a combined fixpoint. Nothing is
hand-built; the two former gaps are triangulated below.

WHAT THESE RIDDLES SURFACE (the point of running them now — triangulated over both):
  CONFIRMED working, composed for the first time in one problem, all in CNL:
   - multi-step forward deduction feeds a closed-world decision (`in library -> innocent ->
     cleared`, then the residual is completed);
   - completion + wh-answer + yes/no-answer + why-trace all compose (the `explain` traversal
     renders the completion `<- complete` as the elimination step);
   - the real `ask` surface answers over a DERIVED predicate (`who is thief`, `is rex culprit`).
   - [CLOSED, was gap #1] THE GRAMMAR AUTHORS THE DECIDE-CONSUMER. A closed-world `is not P`
     clause reflects to a positive `is_not` match + a `<decide>` demand, so the whole riddle is
     CNL — no hand-built consumer rule, no Python `seed_decide`/`declare_closed_world` per tuple.
  GAP the riddles still pin (the "what to build next" signal):
   - NO CONSTRUCTIVE DISJUNCTION / EXHAUSTION. These riddles are framed so the answer is "the
     one we cannot clear" — which completion gives directly. A puzzle whose answer must be
     derived POSITIVELY by ruling out alternatives ("not red and not blue, so GREEN holds the
     prize"), or that needs "EXACTLY ONE holds", is NOT expressible: decide gives the negative,
     not existence-from-exhaustion, and there is no "exactly one" quantifier yet. This is the
     deferred indefinite-existentials / uniqueness axis — the boundary to keep riddles clear of
     until it is built.
"""
import ugm as h
from ugm import decide, provenance as prov
from ugm.cnl.authoring import load_corpus
from ugm import solve_all
from ugm.cnl.forms import SURFACE_TAGS
from ugm.cnl.query import ask
from ugm.cnl.surface import explain


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
    """Author the riddle in CNL and solve it on the BACKWARD ISA engine, returning (graph, [], rules).

    `load_corpus(..., decided_negation=False)` keeps the closed-world `is not P` a plain NAC; `solve_all`
    (the goal-directed engine forward-driven) materializes the closure — deducing forward AND completing
    the closed-world negative on demand (`_complete_negative`), with NO aggressive over-assertion and NO
    retraction. `provenance=True` MINTs the in-graph proves/uses support (incl. a `complete.REL` J for a
    completed negative) so the real `explain` traversal renders the elimination step. The retired forward
    `decide.solve` did the same at the answer level via aggressive-completion + retract (decision-attrgraph-rehost)."""
    g, rules = load_corpus(riddle["corpus"], decided_negation=False)
    _clean(g)
    solve_all(g, rules, provenance=True)
    return g, [], rules


def test_thief_riddle_solved_by_elimination():
    g, journal, rules = _solve(THIEF_RIDDLE)
    # node-agnostic: the backward engine (node-level identity) materializes a derived fact on the
    # same_as-class canonical mention, so check ANY mention of the entity (additive coref, no merge).
    def pos(name, prop): return any(decide.positive_holds(g, n, prop) for n in g.nodes_named(name))
    def neg(name, prop): return any(decide.negative_holds(g, n, prop) for n in g.nodes_named(name))
    # the deduction chain ran: bo cleared via library->innocent->cleared; ada cleared via alibi
    assert pos("bo", "cleared")
    assert pos("ada", "cleared")
    # cy could not be cleared -> the negative was COMPLETED (the elimination step)
    assert neg("cy", "cleared")


def test_thief_riddle_answers_the_question():
    g, journal, rules = _solve(THIEF_RIDDLE)
    answer = ask(g, THIEF_RIDDLE["question"], journal=journal, rules=rules)
    assert answer == THIEF_RIDDLE["answer"]           # cy is thief
    # and it is the UNIQUE answer (no other suspect is the thief)
    assert ask(g, "is ada thief", journal=journal, rules=rules) == ["no"]
    assert ask(g, "is cy thief", journal=journal, rules=rules) == ["yes"]


def test_thief_riddle_explains_the_answer():
    g, journal, rules = _solve(THIEF_RIDDLE)
    why = ask(g, "why cy is thief", journal=journal, rules=rules)
    text = "\n".join(why)
    # the trace names the (CNL-authored) thief rule, the given suspect premise, and bottoms out at
    # the completion of the closed-world negative (the "we could not clear cy" step).
    assert "cy is thief" in text and "rule.?x.is.thief" in text
    assert "cy is_not cleared" in text
    assert "complete" in text                          # <j:complete> — the elimination is explained


def test_thief_riddle_why_cy_not_cleared_is_a_completion():
    # Directly ask the engine to explain the decided negative: it is a completion (no positive
    # premises — it holds by the ABSENCE of a derivation), which is exactly closed-world negation.
    g, journal, rules = _solve(THIEF_RIDDLE)
    trace = explain(g, journal, rules, "cy", "is_not", "cleared")
    assert trace and "cy is_not cleared" in trace[0] and "complete" in trace[0]


def test_vase_riddle_yesno_and_why_not():
    # A second, independent riddle: yes/no answers over a derived predicate + a why-not.
    g, journal, rules = _solve(VASE_RIDDLE)
    assert ask(g, VASE_RIDDLE["question"], journal=journal, rules=rules) == VASE_RIDDLE["answer"]
    assert ask(g, "is tia culprit", journal=journal, rules=rules) == ["yes"]
    assert ask(g, "is rex culprit", journal=journal, rules=rules) == ["no"]
    # "rex is NOT the culprit" bottoms out at a real derivation: rex was cleared (in the yard).
    assert ask(g, "is rex cleared", journal=journal, rules=rules) == ["yes"]
    why = "\n".join(ask(g, "why tia is culprit", journal=journal, rules=rules))
    assert "tia is_not cleared" in why and "complete" in why


def test_riddles_author_entirely_in_cnl():
    # The point of handoff step 1: no hand-built decide-consumer, no Python seeding. The consumer is a
    # real CNL rule (`?x is thief when ...`). On the BACKWARD engine (decided_negation=False) its
    # closed-world `is not cleared` stays a plain NAC that the engine COMPLETES on demand — no generated
    # aggressive-completion rule, no <decide> token (the demand-completion subsumes them).
    _g, _journal, rules = _solve(THIEF_RIDDLE)
    thief = next(r for r in rules if r.key == "rule.?x.is.thief")
    assert ("?x", "is", "cleared") in {p.tokens() for p in thief.nac}       # the closed-world NAC is KEPT
    assert not any(r.key.startswith("decide.complete") for r in rules)      # no aggressive completion rule
