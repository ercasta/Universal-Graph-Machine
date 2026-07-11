"""
Goal-directed answering — the engine works BACKWARD in production (decision-attrgraph-rehost
Phase B; decision-cwa-default). `ask_goal` demands only the question's goal through the ISA machine
(`GoalSolver`), reasoning ON DEMAND, rather than the forward `ask` which reads a graph that a
prior forward pass materialized. These tests pin:

  1. PARITY — `ask_goal` gives the same yes/no answers as forward `run_rules` + `ask`, on the real
     graded + NAC bank (defeasible defeat included).
  2. GOAL-DIRECTION — answering ONE question materializes strictly fewer facts than the forward
     closure (`solve_all`): the whole point of working backward (the DIRECTION-PRESERVATION
     invariant), which a forward-saturating solver would violate.
  3. CWA-DEFAULT + per-predicate OWA opt-in — an underivable goal is a DEFEASIBLE `no` (best of
     current knowledge); `unknown` only when its concept is declared OPEN (`open_preds`), where
     absence != false and the ask-user evidence-gatherer fires.
"""
import ugm as h
from ugm import derived_triples


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
YESNO = [
    "is alice served express", "is bob served regular", "is bob served express",
    "is alice served regular", "is carol offered alternative",
]
def test_ask_goal_matches_forward_ask_on_the_defeasible_graded_bank():
    kb_fwd, rules = h.load_corpus(ICE_CREAM)
    h.run_rules(kb_fwd, rules)
    forward = [h.ask(kb_fwd, q) for q in YESNO]

    kb_goal, rules_g = h.load_corpus(ICE_CREAM)          # NOT run_rules'd — ask_goal reasons on demand
    backward = [h.ask_goal(kb_goal, q, rules_g) for q in YESNO]   # CWA-default (matches forward `ask`)

    assert backward == forward
    assert backward[0] == ["yes"]                         # alice -> express (graded)
    assert backward[2] == ["no"]                          # bob NOT express (NAC-completed defeat)
    assert backward[3] == ["no"]                          # alice NOT regular (NAC-completed defeat)


# RETIRED (Phase 6.1): `test_ask_goal_is_goal_directed_materializes_less_than_the_full_closure` —
# it pinned GoalSolver's demand-driven selectivity (materialize only the goal's chain). Decided
# negation is inherently FORWARD (aggressive completion + defeat), so `ask_goal` now materializes via
# the forward firmware (`decide.solve`) like any other bank; the selectivity property was GoalSolver's
# and is deliberately gone. The remaining ask tests pin the ANSWERS, which is what matters.


def test_cwa_default_no_vs_owa_optin_unknown():
    # `is bob served express` is underivable. CWA-DEFAULT (decision-cwa-default): a defeasible `no`
    # (act on the best of current knowledge). OWA opt-in (`served` declared open): `unknown` —
    # absence != false, for the predicates where CWA is unsafe.
    kb1, rules1 = h.load_corpus(ICE_CREAM)
    assert h.ask_goal(kb1, "is bob served express", rules1) == ["no"]                       # CWA default

    kb2, rules2 = h.load_corpus(ICE_CREAM)
    assert h.ask_goal(kb2, "is bob served express", rules2,
                      open_preds=frozenset({"served"})) == ["unknown"]                       # OWA opt-in

    # a derivable goal is `yes` regardless of open/closed (positive knowledge is decisive either way).
    kb3, rules3 = h.load_corpus(ICE_CREAM)
    assert h.ask_goal(kb3, "is alice served express", rules3, open_preds=frozenset({"served"})) == ["yes"]


# The thief elimination WITH `cleared is closed world`. Under DEMAND-DRIVEN NEGATION (firmware v3) the
# `cleared is closed world` marker is VESTIGIAL for reasoning — the `is not cleared` clause is a NAC
# decided on demand by negation-as-failure (nested negative demand -> positive closure -> absence).
THIEF_CW = """
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


def test_closed_world_elimination_via_demand_driven_naf():
    # Closed-world elimination on the firmware, DEMAND-DRIVEN: `thief when suspect and not cleared`. To
    # decide `thief(cy)`, bind cy from `suspect(cy)`, demand the positive `cleared(cy)` to closure (it
    # comes back empty), absence decides `not cleared` -> `thief(cy)`. bo/ada ARE cleared (library ->
    # innocent -> cleared; alibi -> cleared), so their NAC fails. No `is_not` is materialized.
    kb, rules = h.load_corpus(THIEF_CW)
    answers = [h.ask_goal(kb, q, rules)
               for q in ("is cy thief", "is ada thief", "is bo thief", "who is thief")]
    assert answers == [["yes"], ["no"], ["no"], ["cy is thief"]]


ASK_USER_KB = """
    alice is a person
    ?p is friendly when ?p likes bob
"""


def test_ask_user_gathers_evidence_for_an_open_predicate_and_persists():
    # `likes` is declared OPEN (the OWA opt-in) -> an underivable goal is UNKNOWN, so the engine
    # gathers evidence for exactly that open fact, folds it in (monotone), and downstream reasoning
    # then derives. (decision-cwa-default: gathering happens only for open predicates.)
    kb, rules = h.load_corpus(ASK_USER_KB)
    assert h.ask_goal(kb, "is alice likes bob", rules, open_preds=frozenset({"likes"})) == ["unknown"]

    asked = []

    def ask_user(s, p, o):
        asked.append((s, p, o))
        return (s, p, o) == ("alice", "likes", "bob")     # confirm this open fact, else None/False

    kb2, rules2 = h.load_corpus(ASK_USER_KB)
    assert h.ask_goal(kb2, "is alice likes bob", rules2, open_preds=frozenset({"likes"}),
                      ask_user=ask_user) == ["yes"]
    assert asked == [("alice", "likes", "bob")]           # asked ONLY the open thing the goal needs
    # the acquired fact PERSISTS -> `friendly` now derives without asking again
    assert h.ask_goal(kb2, "is alice friendly", rules2) == ["yes"]


def test_ask_user_is_never_consulted_for_a_cwa_default_predicate():
    # A CWA-default predicate is decided `no` on the best of current knowledge -> never gathers.
    kb, rules = h.load_corpus(ASK_USER_KB)

    def boom(s, p, o):
        raise AssertionError("ask_user must not be consulted for a CWA-default predicate")

    assert h.ask_goal(kb, "is alice likes bob", rules, ask_user=boom) == ["no"]


# RETIRED (Phase 6.1): `test_expand_rules_goal_form_keeps_closed_world_negation_as_a_nac` pinned the
# `decided_negation=False` NAF path (keep `is not P` a NAC for GoalSolver to complete). That path is the
# old negation-as-failure model; the vision is DECIDED-NEGATION-ONLY, so it is retired along with
# GoalSolver. `test_closed_world_elimination_via_decided_negation` above pins the decided form's answers.


# ---- GATED coref-following: GoalSolver carries selective coreference WHEN THE BANK DECLARES IT
# (decision-labelless-substrate; user directive 2026-07-07). Whether the engine FOLLOWS `same_as` as
# identity is DATA, not a hardcoded engine policy: a bank that carries the `same_as` propagation rules
# (`same_as_rules(...)` — the declaration "compose across coref links") turns following ON, and the
# engine evaluates it via the fast union-find (dropping the now-subsumed rules). A bank WITHOUT them
# (recognition / graded) is coref-BLIND — each node is its own identity. These pin BOTH the declared
# case (linked mentions compose, unlinked stay distinct — selectivity) AND the blind case (no rules =>
# no composition even when linked), so the POLICY lives in the bank, matching the forward rewriter.

_RESPECT = h.Rule(
    key="respect",
    lhs=[h.Pat("?p", "is_a", "teacher"), h.Pat("?p", "is_a", "mortal")],
    rhs=[h.Pat("?p", "is_a", "respected")],
)


def _two_mentions(link: bool):
    """Two `paul` mentions: one is_a teacher, one is_a mortal. `link` wires them `same_as`."""
    g = h.Graph()
    p1, teacher = g.add_node("paul"), g.add_node("teacher")
    g.add_relation(p1, "is_a", teacher)
    p2, mortal = g.add_node("paul"), g.add_node("mortal")
    g.add_relation(p2, "is_a", mortal)
    if link:
        g.add_relation(p1, "same_as", p2)
    return g


_COREF_BANK = [_RESPECT] + h.same_as_rules(["is_a"]) + h.UNIVERSAL_RULES   # DECLARES coref-following


def _respected(fg) -> bool:
    """Did `paul is_a respected` derive on any mention? (read the forward-materialized graph)."""
    return any(fg.has_key(r, "is_a") and fg.name(o) == "respected"
               for p in fg.nodes_named("paul") for r in fg.out(p) for o in fg.out(r))


# Coref-following is DATA (the `same_as_rules` in the bank), not a hardcoded engine policy — on the
# forward firmware (`run_rules`) exactly as it was on the retired GoalSolver. These pin the declared
# case (linked mentions compose, unlinked stay distinct — selectivity) AND the blind case.

def test_coref_composes_across_same_as_linked_mentions():
    # respected needs is_a teacher AND is_a mortal — facts on DIFFERENT mentions. The bank DECLARES
    # coref (`same_as_rules`), so propagation composes them across the link.
    fg = _two_mentions(link=True)
    h.run_rules(fg, _COREF_BANK)
    assert _respected(fg) is True


def test_coref_keeps_unlinked_same_named_mentions_distinct():
    # Coref DECLARED but the two `paul`s are NOT linked — DISTINCT witnesses (label-less default): no
    # single paul is both teacher AND mortal, so respected does NOT derive. Selectivity: follow LINKS,
    # not names.
    fg = _two_mentions(link=False)
    h.run_rules(fg, _COREF_BANK)
    assert _respected(fg) is False


def test_coref_blind_without_the_propagation_rules():
    # The GATE: the SAME linked graph, but a bank WITHOUT `same_as_rules`, is coref-BLIND — no
    # propagation, so the two mentions stay distinct and respected does not derive. Following is DATA.
    fg = _two_mentions(link=True)
    h.run_rules(fg, [_RESPECT] + h.UNIVERSAL_RULES)
    assert _respected(fg) is False





