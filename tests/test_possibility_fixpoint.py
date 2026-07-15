"""
Possibilistic layer — the banded FIXPOINT driver (docs/possibilistic.md S7.6): forward-chain a whole
rule bank to a fixpoint, banded and environment-sound. `ugm.possibility.run_banded`.
"""
from ugm.attrgraph import AttrGraph
from ugm.possibility import run_banded, possibility, CERTAIN
from ugm.cnl.uncertainty import load_uncertain, ask


def test_chain_propagates_the_band_to_a_fixpoint():
    """A 3-rule chain `male → manly → brave → hero` off a fork (0.6) carries the band all the way — the
    driver reaches the transitive conclusion automatically (no hand-application per rule)."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")                            # fork: x is male (0.6)
    rules = [
        ([("?p", "is", "male")],  [], ("?p", "is", "manly")),
        ([("?p", "is", "manly")], [], ("?p", "is", "brave")),
        ([("?p", "is", "brave")], [], ("?p", "is", "hero")),
    ]
    run_banded(g, rules, theta=0.5)
    assert possibility(g, "is", "x", "hero") == 0.6                  # min carried through the whole chain
    assert ask(g, "is x hero") == "likely"


def test_fixpoint_is_idempotent():
    """Re-running the bank emits NOTHING new — the driver has reached a fixpoint (termination guard)."""
    g = AttrGraph()
    load_uncertain(g, "x is likely male")
    rules = [([("?p", "is", "male")], [], ("?p", "is", "manly")),
             ([("?p", "is", "manly")], [], ("?p", "is", "brave"))]
    assert run_banded(g, rules, theta=0.5) > 0                       # first run derives
    assert run_banded(g, rules, theta=0.5) == 0                     # second run: fixpoint, no new emissions


def test_certain_chain_stays_ink():
    """An all-ink chain reaches its conclusion at CERTAIN and writes ink (crisp behaviour preserved)."""
    g = AttrGraph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("surgeon"))   # ink
    rules = [([("?p", "is_a", "surgeon")], [], ("?p", "is", "doctor")),
             ([("?p", "is", "doctor")],   [], ("?p", "is", "professional"))]
    run_banded(g, rules, theta=0.5)
    assert possibility(g, "is", "x", "professional") == CERTAIN
    assert ask(g, "is x professional") == "certain"


def test_fixpoint_stays_environment_sound():
    """A chain that would combine two exclusive forks never fires — the fixpoint inherits ATMS soundness
    from head-environment propagation. `manly` (fork A) + `short` (fork B) is impossible."""
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")
    rules = [
        ([("?p", "is", "male")], [], ("?p", "is", "manly")),                       # fork A → manly
        ([("?p", "is", "manly"), ("?p", "is", "short")], [], ("?p", "is", "puzzling")),  # A ∧ B: impossible
        ([("?p", "is", "manly"), ("?p", "is", "tall")], [], ("?p", "is", "ok")),   # A ∧ A: fine
    ]
    run_banded(g, rules, theta=0.9)
    assert ask(g, "is x manly") == "likely"                          # 0.5
    assert ask(g, "is x ok") == "likely"                             # 0.5, sound chain
    assert ask(g, "is x puzzling") == "assumed-no"                  # impossible world → never derived
