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
from ugm import decide
from ugm import derived_triples, solve_all


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


def test_ask_goal_is_goal_directed_materializes_less_than_the_full_closure():
    # answering one question pulls only its chain; the forward closure derives strictly more.
    kb_one, rules = h.load_corpus(ICE_CREAM)
    base = len(derived_triples(kb_one))
    h.ask_goal(kb_one, "is alice served express", rules)
    one_goal_new = len(derived_triples(kb_one)) - base

    kb_all, rules2 = h.load_corpus(ICE_CREAM)
    base_all = len(derived_triples(kb_all))
    solve_all(kb_all, rules2)
    full_new = len(derived_triples(kb_all)) - base_all

    assert one_goal_new >= 1                              # it did derive alice's answer
    assert one_goal_new < full_new                        # ...but strictly less than the whole closure


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


# The thief elimination WITH `cleared is closed world` — today this drives decide.solve's
# aggressive-completion + RETRACTION (deletion). Goal-directed, it is subsumed by demand-completion.
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


def test_closed_world_elimination_goal_directed_without_decide_retraction():
    # Forward: decide.solve (aggressive completion defeated by RETRACT/interpose — DELETES).
    kb_fwd, rules_fwd = h.load_corpus(THIEF_CW)
    decide.solve(kb_fwd, rules_fwd)
    forward = [h.ask(kb_fwd, q) for q in ("is cy thief", "is ada thief", "is bo thief", "who is thief")]

    # Backward: closed-world `is not P` kept as a NAC (decided_negation=False) -> GoalSolver's
    # demand-completion. Under CWA-DEFAULT the underivable `thief` goals answer `no` without any
    # `closed` set (closed-world is the default now). NO retraction anywhere.
    kb, _ = h.load_corpus(THIEF_CW)
    goal_rules = h.expand_rules(kb, decided_negation=False)
    backward = [h.ask_goal(kb, q, goal_rules)
                for q in ("is cy thief", "is ada thief", "is bo thief", "who is thief")]

    assert backward == forward
    assert backward == [["yes"], ["no"], ["no"], ["cy is thief"]]
    assert h.closed_predicates(kb) == frozenset({"cleared"})   # the reasoning-side CWA DATA is intact


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


def test_expand_rules_goal_form_keeps_closed_world_negation_as_a_nac():
    # decided_negation=False leaves the closed-world `is not cleared` a NAC (no aggressive
    # `decide.complete.*` rule, no positive is_not upgrade) — the form GoalSolver completes.
    kb, _ = h.load_corpus(THIEF_CW)
    goal_rules = h.expand_rules(kb, decided_negation=False)
    assert not any(r.key.startswith("decide.complete") for r in goal_rules)
    thief = next(r for r in goal_rules if r.rhs and r.rhs[0].tokens()[1:] == ("is", "thief"))
    assert [p.tokens() for p in thief.nac] == [("?x", "is", "cleared")]   # stayed a NAC


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


def test_goalsolver_composes_across_same_as_linked_mentions():
    # respected needs is_a teacher AND is_a mortal — facts on DIFFERENT mentions. The bank DECLARES
    # coref (`same_as_rules`), so the solver follows the class (via the union-find fast path) and
    # composes them — matching the forward ISA engine, which reaches the same answer via propagation.
    from ugm import Goal, GoalSolver
    fg = _two_mentions(link=True)
    h.run_rules(fg, _COREF_BANK)                          # forward: same_as propagation
    fwd = any(fg.has_key(r, "is_a") and fg.name(o) == "respected"
              for p in fg.nodes_named("paul") for r in fg.out(p) for o in fg.out(r))
    backward = bool(GoalSolver(_two_mentions(link=True), _COREF_BANK)
                    .solve(Goal("is_a", "paul", "respected")))
    assert fwd is True and backward is True              # both compose across the link, agreeing


def test_goalsolver_keeps_unlinked_same_named_mentions_distinct():
    # Coref DECLARED (`same_as_rules` in the bank) but the two `paul`s are NOT linked — so they are
    # DISTINCT witnesses (label-less default): no single paul is both teacher AND mortal, so respected
    # does NOT derive. Selectivity holds even with following ON — it follows LINKS, not names.
    from ugm import Goal, GoalSolver
    ans = GoalSolver(_two_mentions(link=False), _COREF_BANK).solve(Goal("is_a", "paul", "respected"))
    assert ans == set()                                  # not composed — distinct entities


def test_goalsolver_is_coref_blind_without_the_propagation_rules():
    # The GATE: the SAME linked graph, but a bank WITHOUT `same_as_rules`, is coref-BLIND — the engine
    # does NOT follow the link, so the two mentions stay distinct and respected does not derive. Coref-
    # following is DATA (the rules), not a hardcoded engine policy. (This is what makes recognition /
    # the graded surface-chain pass structural — they carry no propagation rules.)
    from ugm import Goal, GoalSolver
    ans = GoalSolver(_two_mentions(link=True),
                     [_RESPECT] + h.UNIVERSAL_RULES).solve(Goal("is_a", "paul", "respected"))
    assert ans == set()                                  # linked, but not declared -> not composed





