"""
INTERPOSE / RESTORE — reversible retraction on the ISA forward driver (implementation_plan.md
Phase 0.5; isa-reference.md "Reserved: INTERPOSE / RESTORE"). The ISA-native replacement for the
forward `rewriter`'s `rewire cut`: hiding a fact is a REVERSIBLE interposition (splice a fresh
control `<retracted>` marker into the 2-hop path) rather than an irreversible edge deletion, so §5
reframes from "no opcode mutates a fact edge" to "the sole fact-edge op preserves its pre-image".

Coverage: (1) the opcode identity `INTERPOSE ∘ RESTORE = id`; (2) the `rewire`-triple lowers to one
INTERPOSE; (3) the CASCADE meta-rule matches inert `<j:…>` provenance under run_bank's per-rule
inert-visibility; (4) run_bank's retraction hides the derived fact and its dependents.
"""
import ugm as h
from ugm import retraction as ret
from ugm.cnl.authoring import run_rules
from ugm.attrgraph import AttrGraph
from ugm.machine import Machine, INTERPOSE, RESTORE, State
from ugm.lowering import lower_rewire, rule_touches_provenance, Unlowerable


def _has(g, s, r, o):
    sn, on = g.nodes_named(s), g.nodes_named(o)
    return bool(sn and on and any(g.has_key(rel, r) and on[0] in g.out(rel)
                                  for rel in g.out(sn[0])))


# --- 1. opcode identity ---------------------------------------------------------------------

def test_interpose_then_restore_is_identity():
    g = AttrGraph()
    s, rel, o = g.add_node("s"), g.add_node("is_a"), g.add_node("o")
    g.add_edge(s, rel); g.add_edge(rel, o)
    before = set(g.edges())
    m = Machine()
    st = State({"rel": rel, "obj": o})
    st2 = m.apply(g, [INTERPOSE(rel="rel", obj="obj", marker_name="<retracted>", out="mk")], st)
    # obliviousness is structural: rel no longer reaches o directly (marker spliced in)
    assert o not in g.succ(rel)
    marker = st2.regs["mk"]
    assert g.is_control(marker) and o in g.succ(marker) and marker in g.succ(rel)
    # the exact inverse reconstructs the original edge set
    m.apply(g, [RESTORE(rel="rel", marker="mk", obj="obj")], st2)
    assert before <= set(g.edges()) and o in g.succ(rel)


def test_interpose_works_on_a_control_edge_too():
    # a retractable walker shortcut is CONTROL-stamped; interposition is reversible, so it is safe
    # on any live edge (not just facts) — the opcode requires only that the edge exists.
    g = AttrGraph()
    rel = g.add_node("is_a", control=True); o = g.add_node("o")
    g.add_edge(rel, o)
    Machine().apply(g, [INTERPOSE(rel="r", obj="o", marker_name="<retracted>")],
                    State({"r": rel, "o": o}))
    assert o not in g.succ(rel)


# --- 2. rewire -> INTERPOSE lowering --------------------------------------------------------

def test_interpose_rule_rewire_lowers_to_one_interpose():
    ops = lower_rewire(ret.INTERPOSE_RULE)
    assert len(ops) == 1 and isinstance(ops[0], INTERPOSE)
    assert ops[0].marker_name == ret.RETRACTED


def test_a_non_interposition_rewire_stays_unlowerable():
    bare_cut = h.Rule(key="cut", lhs=[h.Pat("?x", "r?", "b")], rhs=[],
                      rewire=[("cut", "?x", "b")])
    try:
        lower_rewire(bare_cut)
        assert False, "a bare cut is not the reversible interposition shape"
    except Unlowerable:
        pass


# --- 3. per-rule provenance-awareness (the meta CASCADE match) ------------------------------

def test_cascade_is_provenance_aware_but_interpose_is_not():
    # CASCADE names proves/uses -> its match must see inert <j:> nodes; INTERPOSE names only
    # <retract>/targets (not provenance) -> it keeps the fact-only (inert-blind) view.
    assert rule_touches_provenance(ret.CASCADE_RULE) is True
    assert rule_touches_provenance(ret.INTERPOSE_RULE) is False


# --- 4. run_bank retraction hides the derived fact and its dependents -------------------------

def _derived_chain():
    g = h.Graph()
    g.add_relation(g.add_node("a"), "is_a", g.add_node("b"))
    b = g.nodes_named("b")[0]; g.add_relation(b, "is_a", g.add_node("c"))
    run_rules(g, h.load_rules("?x is_a ?z when ?x is_a ?y and ?y is_a ?z"), provenance=True)
    return g


def test_runbank_retraction_hides_the_derived_fact_and_its_dependents():
    g = _derived_chain()
    assert _has(g, "a", "is_a", "c")                  # the derived shortcut is present
    rel = next(r for r in g.out(g.nodes_named("b")[0])
               if g.has_key(r, "is_a") and g.nodes_named("c")[0] in g.out(r))
    ret.seed_retract(g, rel)
    run_rules(g, ret.RETRACT_RULES, provenance=False)
    assert not _has(g, "b", "is_a", "c") and not _has(g, "a", "is_a", "c")
