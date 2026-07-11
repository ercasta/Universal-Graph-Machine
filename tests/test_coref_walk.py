"""
Coref as a serialized cursor — CHECK-BEFORE-COMMIT (docs/coref_as_rules_design.md). A `<coref>`
token walks the pair chain over a name's mentions ONE at a time; for each pair it waits on the
`settle` barrier (so the endpoints' sort closures are current), checks a disqualifying clash, and
COMMITS the link only if there is no clash. Coref is purely ADDITIVE (never links-then-retracts),
so the whole walk runs in ONE `run()` driven by rule firing + the engine's fixpoint-then-service
cycle — no Python loop, no cascade, no retraction.
"""
import ugm as h
from ugm import coref_walk as cw
from ugm import run_bank
from ugm.cnl.universal import same_as_rules, UNIVERSAL_RULES


def _walk(g, name, preds):
    """Assemble and run the full one-pass check-before-commit walk over `name`: cursor rules +
    propagation + is_a transitivity, provenance ON, the settle barrier as a tool. No Python loop,
    no retraction. Uses `run_bank` DIRECTLY (not `run_rules`, which stratifies rules into layers
    run to fixpoint one at a time) — `resolve_coref` (coref_walk.py) also calls `run_bank` on the
    whole rule list in one pass, and stratifying this particular bank changes the firing order
    enough to flip WHICH of two symmetric compatible links the greedy walk keeps (still exactly
    one, still consistent — see test_transitive_clash_keeps_a_consistent_partition — but this
    test fixture must match production's actual call shape to pin the real behavior)."""
    cw.materialize_cursor(g, name)
    rules = cw.CURSOR_RULES + cw.clash_rules(g) + same_as_rules(preds) + UNIVERSAL_RULES
    run_bank(g, rules, tools=cw.SETTLE_TOOLS, provenance=True)


def _pairs(g):
    return list(g.nodes_named(cw.PAIR))


def _settled(g, p):
    return any(g.name(r) == cw.SETTLED for r in g.out(p))


def _cursor(g, tok):
    return next((o for r, o in g.relations_from(tok) if g.name(r) == cw.CURSOR), None)


def _has(g, s, p, o):
    """True if the edge  s --[p]--> o  exists, matched by NODE ID (the mentions share a name,
    so `match` by name can't tell them apart)."""
    return any(g.name(r) == p and o in g.out(r) for r in g.out(s))


def _pair_ab(g, p):
    a = next(o for rr, o in g.relations_from(p) if g.name(rr) == cw.PA)
    b = next(o for rr, o in g.relations_from(p) if g.name(rr) == cw.PB)
    return (a, b)


def test_materialize_builds_a_linear_pair_chain():
    g = h.Graph()
    for _ in range(3):
        g.add_node("paul")
    tok = cw.materialize_cursor(g, "paul")
    assert tok is not None
    pairs = _pairs(g)
    assert len(pairs) == 3                       # C(3,2)
    # every pair has distinct endpoints, all a mention of paul
    mentions = set(g.nodes_named("paul"))
    for p in pairs:
        a, b = _pair_ab(g, p)
        assert a in mentions and b in mentions and a != b
    # the three pairs cover the three unordered combinations
    combos = {frozenset(_pair_ab(g, p)) for p in pairs}
    assert len(combos) == 3


def test_cursor_visits_every_pair_in_one_run_no_loop():
    g = h.Graph()
    for _ in range(3):
        g.add_node("paul")
    tok = cw.materialize_cursor(g, "paul")

    run_bank(g, cw.CURSOR_WALK_STUB, tools=cw.SETTLE_TOOLS, provenance=True)

    # every pair got settled — the walk reached all of them via emergent rule+tool firing
    assert all(_settled(g, p) for p in _pairs(g))
    # the cursor came to rest on the last pair of the chain (no `pnext` to advance past)
    last = _cursor(g, tok)
    assert last is not None
    assert not any(g.name(r) == cw.PNEXT for r in g.out(last))


def test_single_mention_no_cursor():
    g = h.Graph()
    g.add_node("solo")
    assert cw.materialize_cursor(g, "solo") is None


def test_compatible_pair_committed_and_composes_facts():
    # A consistent pair: no clash -> COMMIT the link, and its facts COMPOSE (same_as propagation),
    # all in one run() — probe/barrier/checked/commit/advance + propagation, no retraction.
    g = h.Graph()
    pa = g.add_node("paul")
    pb = g.add_node("paul")
    g.add_relation(pa, "likes", g.add_node("chess"))
    g.add_relation(pb, "is_a", g.add_node("student"))

    _walk(g, "paul", ["likes", "is_a"])

    assert _has(g, pa, "same_as", pb) or _has(g, pb, "same_as", pa)   # committed
    assert not h.is_rejected(g, pa, pb)
    chess = g.nodes_named("chess")[0]
    student = g.nodes_named("student")[0]
    assert _has(g, pb, "likes", chess)               # paul_b inherited paul_a's `likes chess`
    assert _has(g, pa, "is_a", student)              # paul_a inherited paul_b's `is_a student`


def test_two_pauls_stay_separate_no_retraction():
    # Two pauls in disjoint categories: the clash between the endpoints is caught BEFORE any link
    # is committed, so `not_same_as` is recorded and the mentions stay separate — purely additive,
    # no cascade. One run(), no cascade_retract.
    g = h.Graph()
    p1, p2 = g.add_node("paul"), g.add_node("paul")
    g.add_relation(p1, "is_a", g.add_node("teacher"))
    g.add_relation(p2, "is_a", g.add_node("student"))
    g.add_relation(g.nodes_named("teacher")[0], "disjoint_from", g.nodes_named("student")[0])

    _walk(g, "paul", ["is_a"])

    assert len(g.nodes_named("paul")) == 2               # never merged
    assert not _has(g, p1, "same_as", p2)                # never linked (clash caught pre-commit)
    assert not _has(g, p2, "same_as", p1)
    assert h.is_consistent(g)                            # no contradiction was ever produced
    assert h.is_rejected(g, p1, p2)                      # rejection recorded

    def cats(n):
        return sorted(g.name(o) for r, o in g.relations_from(n) if g.name(r) == "is_a")
    assert cats(p1) == ["teacher"] and cats(p2) == ["student"]   # each keeps only its own


def test_transitive_clash_keeps_a_consistent_partition():
    # Three mentions: a(solid), b(no sort), c(liquid), solid disjoint liquid. b is compatible with
    # EITHER a or c, but not both (that would make a~b~c solid+liquid). The greedy walk keeps
    # exactly ONE of {a=b, b=c} — WHICH one depends on the (hash-randomized) mention order, the
    # same non-determinism the original `coref_on_demand` has. The order-ROBUST guarantee: the
    # result is consistent, a≠c always (direct clash), and the transitive clash is caught (never
    # both compatible links kept). This exercises transitive-awareness: whichever link is kept
    # first, its propagation extends b's sorts so the second is rejected at its pair's barrier.
    g = h.Graph()
    a, b, c = g.add_node("m"), g.add_node("m"), g.add_node("m")
    g.add_relation(a, "is_a", g.add_node("solid"))
    g.add_relation(c, "is_a", g.add_node("liquid"))
    g.add_relation(g.nodes_named("solid")[0], "disjoint_from", g.nodes_named("liquid")[0])

    _walk(g, "m", ["is_a"])

    assert h.is_consistent(g)                                     # no contradiction ever produced
    assert h.is_rejected(g, a, c)                                 # a≠c (direct clash), order-independent
    ab = _has(g, a, "same_as", b) or _has(g, b, "same_as", a)
    bc = _has(g, b, "same_as", c) or _has(g, c, "same_as", b)
    assert ab != bc                                              # EXACTLY one kept (transitive clash caught)
    # ... and the compatible link NOT kept is the one recorded rejected
    assert h.is_rejected(g, b, c) if ab else h.is_rejected(g, a, b)
