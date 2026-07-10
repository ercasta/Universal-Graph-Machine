"""
clingo as a SCOPED calculator — constructive disjunction / exactly-one (docs/vision_agentic.md §3).

This is the one thing the stratified, single-fixpoint engine genuinely cannot express: reasoning
BY CASES over a disjunction to force a POSITIVE conclusion. "Exactly one of {a,b,c} holds; not a;
not b; therefore c" is not closed-world elimination (CWA/`decide` would wrongly conclude `not c`
too, since c is unproven) — it is a choice + integrity constraint whose unique stable model entails
c. clingo does this natively; our engine has no head-disjunction and no model enumeration. So per
the vision, we do NOT put disjunction in the engine — we DELEGATE it to clingo behind the §8
materialized-`<call>` boundary (dispatch.py), scoped to the atoms a rule hands it.

THE OPAQUE DISCIPLINE (vision §1/§8) is honored strictly: the calculator NEVER parses the atom
node NAMES. It assigns each atom an anonymous index, hands clingo only `sel(0..k-1)`, and maps the
solution back onto the original nodes. clingo reasons over symbols with no meaning; the fold-back
lands on the real graph nodes. Names stay opaque labels the way the calculator boundary requires.

SOUNDNESS (why it folds back only sometimes): the winner is emitted only under CAUTIOUS entailment
— the atom selected in EVERY stable model. With all-but-one ruled out, one model remains and that
atom is forced (emit it). With two live options, two models disagree (emit nothing — genuinely
undetermined). Unsat (a contradiction, e.g. everything ruled out) also emits nothing. The calculator
never guesses; it forces only what the disjunction actually entails.

Swappability: clingo sits behind the `asp_solve` tool contract (`handler(graph, call_id) -> touched
ids`). The whole box could be replaced by any exactly-one solver without touching a rule or a fact —
which is exactly what tests/test_contract.py pins at the behavioral level.
"""
from __future__ import annotations

from .dispatch import CALL, TOOL, _ensure, call_arg, call_args
from .cnl.machine_rules import load_machine_rules
from .world_model import Graph

TOOL_NAME = "asp_solve"
YES = "<yes>"
ATOM = "atom"        # a member of the disjunction domain (exactly one holds)
OUT = "out"          # a domain member ruled out (its selection is forbidden)
PRED = "pred"        # the node whose NAME is the relation to stamp on the winner


def emit_exactly_one_call(graph: Graph, atoms: list[str], ruled_out: list[str],
                          pred: str) -> str:
    """Materialize an `asp_solve` `<call>`: exactly one of `atoms` satisfies `pred`, with each of
    `ruled_out` forbidden. `pred` is the node id whose name is the relation the winner receives.
    A driver/test helper — normally a rule materializes the call (the aggregation of atoms into one
    call from per-match rule firings is the next integration step; see docs/handoff_redesign.md)."""
    c = graph.add_node(CALL)
    graph.add_relation(c, TOOL, _ensure(graph, TOOL_NAME))
    graph.add_relation(c, PRED, pred)
    for a in atoms:
        graph.add_relation(c, ATOM, a)
    for r in ruled_out:
        graph.add_relation(c, OUT, r)
    return c


def asp_solve(graph: Graph, call_id: str) -> set[str]:
    """Service one `asp_solve` call: project its atoms/out-set to an exactly-one ASP program, solve
    with clingo, and stamp `winner --pred--> <yes>` iff the disjunction cautiously entails a unique
    winner. Returns the touched node ids so the engine re-seeds reasoning on the result."""
    import clingo

    atoms = call_args(graph, call_id, ATOM)
    pred_id = call_arg(graph, call_id, PRED)
    if not atoms or pred_id is None:
        return set()
    out = set(call_args(graph, call_id, OUT))
    index = {a: i for i, a in enumerate(atoms)}          # opaque: node id -> anonymous index

    program = "1 { " + "; ".join(f"sel({i})" for i in range(len(atoms))) + " } 1.\n"
    for a in out:
        if a in index:
            program += f":- sel({index[a]}).\n"          # a ruled-out member cannot be selected
    program += "#show sel/1.\n"

    ctl = clingo.Control(["--models=0"])                 # enumerate ALL stable models
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    models: list[frozenset[int]] = []
    ctl.solve(on_model=lambda m: models.append(
        frozenset(s.arguments[0].number for s in m.symbols(shown=True) if s.name == "sel")))

    if not models:
        return set()                                     # unsat: contradiction, nothing forced
    forced = set(models[0]).intersection(*models)        # cautious entailment: in EVERY model
    if len(forced) != 1:
        return set()                                     # ambiguous / undetermined -> emit nothing

    winner = atoms[next(iter(forced))]
    rel = graph.add_relation(winner, graph.name(pred_id), _ensure(graph, YES))
    return {winner, rel, graph.nodes_named(YES)[0]}


# The tool registry to pass as `run(..., tools=asp.TOOLS)`.
TOOLS: dict = {TOOL_NAME: asp_solve}


# --- rule-driven aggregation: RULES build the call from domain facts ----------
#
# So the calculator fires from ordinary reasoning, not a Python driver (`emit_exactly_one_call`). A
# DECISION is declared as facts: `?dec pred_of ?p` (the predicate exactly one member gets) and `?dec
# domain_of ?type` (the candidate type); candidates are `?d is_a ?type`; a ruled-out member is `?d
# ruled_out ?p`. These rules materialize ONE `asp_solve` call per decision and accrete every candidate
# as `atom` and every ruled-out member as `out`. Run with `run(g, DISJUNCTION_RULES, tools=TOOLS)`.
#
# MECHANISM NOTE: the call is materialized ONCE (a rule bound only to the decision, so it fires a
# single time), then the atom/out rules bind that existing call by a PLAIN variable via its `decision`
# link and accrete onto it. A fresh `<call>?` bound-literal token would mint a NEW node per firing (it
# does not aggregate), so the split — one materializer, then plain-variable accretors — is load-bearing.
#
# AUTHORING NOTE: the decision facts (`pred_of`/`domain_of`/`ruled_out`) are relational facts, so they
# CAN be declared in CNL — but a full natural-language "exactly one door holds the prize" surface, and
# same-name identity for the shared `?p`/`?type` nodes across facts, are gated on the two NL-front-end
# gaps (batch declaration-before-use; same-name merge) recorded in docs/handoff_redesign.md.
DISJUNCTION_RULES = load_machine_rules("""
    <call>? tool asp_solve and <call>? pred ?p and <call>? decision ?dec when ?dec pred_of ?p
    ?call atom ?d when ?call decision ?dec and ?dec domain_of ?type and ?d is_a ?type
    ?call out ?d when ?call decision ?dec and ?dec pred_of ?p and ?d ruled_out ?p
""")
