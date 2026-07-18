"""
Conformance suite for RECALL — associative candidate introduction (ugm/recall.py).

Hand-written instruction sequences, no rules and no compiler, in the pinning style of
test_isa_machine.py. The point of RECALL is that the substrate ALREADY holds sparse embeddings:
a node's graded attribute bundle IS its vector, so these tests build "concepts" by asserting
ordinary graded predicates and never touch an external table.
"""
import pytest

from ugm import AttrGraph, SET, RECALL, TEST, run_program, Machine, near, cosine
from ugm.attrgraph import graded, valued
from ugm.machine import T_PROD


def _emotions() -> tuple[AttrGraph, dict[str, str]]:
    """A tiny affect neighbourhood. `furious` and `angry` share most dimensions; `calm` shares
    only the bare `emotion` dimension; `rock` shares nothing at all."""
    g = AttrGraph()
    ids = {
        "angry": g.add_node({"name": valued("angry"),
                             "emotion": graded(1.0), "negative": graded(0.9),
                             "aroused": graded(0.8)}),
        "furious": g.add_node({"name": valued("furious"),
                               "emotion": graded(1.0), "negative": graded(1.0),
                               "aroused": graded(1.0)}),
        "calm": g.add_node({"name": valued("calm"),
                            "emotion": graded(1.0)}),
        "rock": g.add_node({"name": valued("rock"),
                            "mineral": graded(1.0)}),
    }
    return g, ids


# ---------------------------------------------------------------------------
# The similarity primitive
# ---------------------------------------------------------------------------

def test_embedding_is_the_graded_bundle():
    # No side-car vector store: the dimensions ARE the asserted predicates.
    g, ids = _emotions()
    assert g.get_embedding(ids["angry"]) == {"emotion": 1.0, "negative": 0.9, "aroused": 0.8}


def test_near_ranks_by_similarity_and_explains_itself():
    g, ids = _emotions()
    hits = near(g, ids["angry"])
    assert [h.nid for h in hits] == [ids["furious"], ids["calm"]]   # rock shares no dimension
    assert hits[0].score > hits[1].score
    # The explanation is in the rules' own vocabulary, strongest contribution first.
    assert hits[0].shared == ("emotion", "negative", "aroused")
    assert hits[1].shared == ("emotion",)


def test_disjoint_concepts_are_not_recalled_at_all():
    g, ids = _emotions()
    assert ids["rock"] not in {h.nid for h in near(g, ids["angry"])}
    assert cosine(g.get_embedding(ids["angry"]), g.get_embedding(ids["rock"])) == 0.0


def test_probe_never_recalls_itself():
    g, ids = _emotions()
    assert ids["angry"] not in {h.nid for h in near(g, ids["angry"])}


def test_unembedded_probe_recalls_nothing():
    # An unembedded node is not "similar to everything" — it is simply not recallable.
    g, _ = _emotions()
    bare = g.add_node({"name": valued("nothing-in-particular")})
    assert near(g, bare) == []


def test_threshold_and_top_k():
    g, ids = _emotions()
    assert [h.nid for h in near(g, ids["angry"], top_k=1)] == [ids["furious"]]
    assert [h.nid for h in near(g, ids["angry"], threshold=0.9)] == [ids["furious"]]
    assert near(g, ids["angry"], threshold=1.01) == []


def test_scaffolding_is_not_a_concept():
    # Control and provenance-inert nodes carry graded keys too; neither is recallable.
    g, ids = _emotions()
    ctrl = g.add_node({"emotion": graded(1.0), "negative": graded(0.9)})
    g.set_control(ctrl)
    inert = g.add_node({"emotion": graded(1.0), "negative": graded(0.9)})
    g.set_inert(inert)
    recalled = {h.nid for h in near(g, ids["angry"])}
    assert ctrl not in recalled and inert not in recalled


def test_recall_is_deterministic_across_equivalent_graphs():
    a, ids_a = _emotions()
    b, ids_b = _emotions()
    assert [ (h.score, h.shared) for h in near(a, ids_a["angry"]) ] == \
           [ (h.score, h.shared) for h in near(b, ids_b["angry"]) ]


# ---------------------------------------------------------------------------
# The opcode
# ---------------------------------------------------------------------------

def test_recall_binds_candidates_best_first():
    g, ids = _emotions()
    states = run_program(g, [SET("p", ids["angry"]), RECALL("x", "p")])
    assert [s.regs["x"] for s in states] == [ids["furious"], ids["calm"]]


def test_recall_folds_similarity_into_score():
    # The similarity arrives as a DEGREE, so an associatively-reached state is already banded.
    g, ids = _emotions()
    states = run_program(g, [SET("p", ids["angry"]), RECALL("x", "p")])
    assert 0.0 < states[1].score < states[0].score < 1.0


def test_recall_score_composes_by_the_machine_tnorm():
    g, ids = _emotions()
    prog = [SET("p", ids["angry"]), RECALL("x", "p", top_k=1)]
    godel = run_program(g, prog)
    product = Machine(tnorm=T_PROD).run(g, prog)
    # Starting score is 1.0, so both t-norms agree on a single hop; the point is that RECALL
    # goes through the t-norm at all rather than overwriting the score.
    assert godel[0].score == pytest.approx(product[0].score)


def test_recall_composes_with_ordinary_filters():
    # RECALL only PROPOSES: downstream ops verify, exactly as with any SEED-introduced candidate.
    g, ids = _emotions()
    states = run_program(g, [SET("p", ids["angry"]), RECALL("x", "p"),
                             TEST("x", "aroused")])
    assert [s.regs["x"] for s in states] == [ids["furious"]]


def test_recall_writes_nothing():
    g, ids = _emotions()
    before = (len(g), sorted(g.edges()), g.version)
    run_program(g, [SET("p", ids["angry"]), RECALL("x", "p")])
    assert (len(g), sorted(g.edges()), g.version) == before


def test_recall_is_never_an_automatic_fallback():
    """The contract the probe bought (bench/recall_autofire.py): a demand MISS must not escalate to
    recall on its own. Measured on the THIEF bank, auto-fire flipped `cy is thief` to `no (assumed)`
    — on a TRUE similarity (fellow suspects), so no threshold rescues it. Pinned here as a
    structural guarantee: the demand chain must not reach the recall primitive."""
    import inspect
    from ugm import chain
    src = inspect.getsource(chain)
    assert "near(" not in src and "recall" not in src, (
        "the demand chain reached the recall primitive — a miss must stay a miss (NAF), and "
        "recall must be invoked explicitly by a program, never as a rescue")


def test_recall_after_an_effect_is_a_program_error():
    # It forks the state stream like SEED, so it is a MATCHING op: match-then-apply must hold.
    from ugm import EMIT, ProgramError
    g, ids = _emotions()
    with pytest.raises(ProgramError):
        run_program(g, [SET("p", ids["angry"]),
                        EMIT("p", "seen", 1.0),
                        RECALL("x", "p")])
