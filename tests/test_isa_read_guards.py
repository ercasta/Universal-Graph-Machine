"""
Firmware §3/§5 — the fact-read guard as compiler-emitted attribute TESTs, and focus as the
register-pointed MEMBER live-set op (docs/attic/firmware_over_isa_design.md).

Three layers pinned here:
  1. MARKER LOCKSTEP: control/inert live BOTH as the legacy flags and as ordinary marker attributes
     (`<control>`/`<inert>`), dual-written at every mint/set chokepoint — the §3 de-privileging
     enabler. The two representations may never diverge.
  2. The machine primitives: `TEST(..., absent=True)` (the fact-read attribute guard, A5) and
     `MEMBER(regs, live)` (register-pointed live-set restriction, A5) — small, dumb, reusable.
  3. The demand read (`chain._facts_matching_isa`) is a SELF-CONTAINED program built from them —
     its walk-parity is asserted call-by-call by `chain._CROSSCHECK` in the differential suites;
     here we pin the register-pointed focus mechanism end-to-end.
"""
import ugm as h
from ugm import AttrGraph, Pat, Rule, chain_sip, derived_triples
from ugm import chain
from ugm.attrgraph import CONTROL_MARK, INERT_MARK, valued
from ugm.apply import SCOPE
from ugm.machine import Machine, SET, TEST, MEMBER, OVERLAY


# --- 1. marker lockstep ----------------------------------------------------------------------------

def test_flag_params_dual_write_markers():
    g = AttrGraph()
    c = g.add_node("scaffold", control=True)
    i = g.add_node("proof", inert=True)
    plain = g.add_node("ada")
    assert g.has_key(c, CONTROL_MARK) and not g.has_key(c, INERT_MARK)
    assert g.has_key(i, INERT_MARK) and not g.has_key(i, CONTROL_MARK)
    assert not g.has_key(plain, CONTROL_MARK) and not g.has_key(plain, INERT_MARK)


def test_control_token_autopromote_dual_writes():
    g = AttrGraph()
    d = g.add_node("<demand>")                             # `<…>` name -> auto control
    assert g.is_control(d) and g.has_key(d, CONTROL_MARK)


def test_set_control_and_set_inert_keep_lockstep_both_directions():
    g = AttrGraph()
    n = g.add_node("x")
    g.set_control(n)
    assert g.is_control(n) and g.has_key(n, CONTROL_MARK)
    g.set_control(n, False)
    assert not g.is_control(n) and not g.has_key(n, CONTROL_MARK)
    g.set_inert(n)
    assert g.is_inert(n) and g.has_key(n, INERT_MARK)
    g.set_inert(n, False)
    assert not g.is_inert(n) and not g.has_key(n, INERT_MARK)


def test_marker_in_attrs_dict_restores_flag():
    """A marker arriving IN an attrs dict (copy/absorb/deserialize path) restores its flag — the
    lockstep is convergent, so `absorb` no longer silently drops inert-ness."""
    g = AttrGraph()
    src = AttrGraph()
    prov = src.add_node("uses", inert=True)
    ctrl = src.add_node("token", control=True)
    src.add_node("ada")
    idmap = g.absorb(src)
    assert g.is_inert(idmap[prov]) and g.has_key(idmap[prov], INERT_MARK)
    assert g.is_control(idmap[ctrl]) and g.has_key(idmap[ctrl], CONTROL_MARK)


def test_set_embedding_spares_markers():
    g = AttrGraph()
    n = g.add_node("walker", control=True, embedding={"speed": 0.5})
    g.set_embedding(n, {"speed": 0.9})                     # re-embed clears prior graded dims ...
    assert g.is_control(n) and g.has_key(n, CONTROL_MARK)  # ... but never the markers
    assert g.get_attr(n, "speed").value == 0.9


# --- 2. the primitives -----------------------------------------------------------------------------

def test_test_absent_is_the_attribute_guard():
    g = AttrGraph()
    fact = g.add_node("ada")
    scaffold = g.add_node("ada", control=True)
    m = Machine()
    keep = [st.regs["x"] for nid in (fact, scaffold)
            for st in m.match(g, [SET("x", nid), TEST("x", CONTROL_MARK, absent=True)])]
    assert keep == [fact]                                  # the guard drops the marked twin


def test_member_restricts_by_register_pointed_live_set():
    g = AttrGraph()
    ada, cy = g.add_node("ada"), g.add_node("cy")
    m = Machine()
    prog_a = [SET("x", ada), MEMBER(("x",), "<focus>")]
    prog_c = [SET("x", cy), MEMBER(("x",), "<focus>")]
    # no live-set register -> no restriction (mechanism is inert until policy points it at a set)
    assert m.match(g, prog_a) and m.match(g, prog_c)
    g.registers["<focus>"] = frozenset({"ada"})            # policy: the working set's contents
    assert m.match(g, prog_a) and not m.match(g, prog_c)   # mechanism: the membership test
    g.registers["<focus>"] = None
    assert m.match(g, prog_c)                              # cleared -> unrestricted again


def test_member_is_touch_semantics_any_of():
    """Focus keeps a fact that TOUCHES the working set — the any-of disjunction across registers."""
    g = AttrGraph()
    ada, dee = g.add_node("ada"), g.add_node("dee")
    g.registers["<focus>"] = frozenset({"ada"})
    m = Machine()
    assert m.match(g, [SET("s", dee), SET("o", ada), MEMBER(("s", "o"), "<focus>")])
    assert not m.match(g, [SET("s", dee), SET("o", dee), MEMBER(("s", "o"), "<focus>")])


def test_marker_attribute_is_the_single_source_of_truth():
    """§7 step 3: the flags are DERIVED views over the marker attributes — no dataclass kind-field
    remains. Reading the flag and reading the attribute are the same read."""
    g = AttrGraph()
    n = g.add_node("x", control=True)
    assert g.node(n).control is True and CONTROL_MARK in g.node(n).attrs
    g._clear_marker(n, CONTROL_MARK)                       # remove the attribute ...
    assert g.node(n).control is False                      # ... and the "flag" is gone with it


def test_serialization_roundtrip_preserves_inertness_via_markers():
    """`to_dict` never serialized `inert`; with the marker IN `attrs`, inertness now survives the
    round-trip (the gap self-heals)."""
    g = AttrGraph()
    g.add_node("uses", inert=True)
    g2 = AttrGraph.from_dict(g.to_dict())
    assert [n for n in g2.nodes() if g2.is_inert(n)]


def test_overlay_extends_the_base_with_a_live_set():
    """OVERLAY = the 'extend' face: an unmarked node always passes (the base); a marked node passes
    only when the register-pointed set holds its ID; with no set parked it is a pure absent-test."""
    g = AttrGraph()
    fact = g.add_node("f")
    pencil = g.add_node("p", control=True)
    m = Machine()

    def passes(nid):
        return bool(m.match(g, [SET("x", nid), OVERLAY("x", CONTROL_MARK, "<ov>")]))

    assert passes(fact) and not passes(pencil)             # no overlay -> plain absent-test
    g.registers["<ov>"] = frozenset({pencil})
    assert passes(fact) and passes(pencil)                 # in-overlay marked node becomes visible
    g.registers["<ov>"] = frozenset()
    assert not passes(pencil)                              # an EMPTY overlay extends by nothing


def test_scope_pencil_visibility_is_the_overlay_op():
    """End-to-end: a pencil (control rel tagged with a scope) is invisible to a plain read, visible
    to a read within ITS scope, and invisible within ANOTHER scope — all in-program, no post-filter
    (cross-checked against the walk oracle)."""
    g = AttrGraph()
    ada, bo = g.add_node("ada"), g.add_node("bo")
    rel = g.add_relation(ada, "suspects", bo, control=True)   # a pencil ...
    g.set_attr(rel, SCOPE, valued("<hyp1>"))                  # ... of scope <hyp1>
    prev = chain._CROSSCHECK
    chain._CROSSCHECK = True
    try:
        assert chain._facts_matching(g, "suspects", "ada", None) == []
        assert len(chain._facts_matching(g, "suspects", "ada", None, scope="<hyp1>")) == 1
        assert chain._facts_matching(g, "suspects", "ada", None, scope="<hyp2>") == []
    finally:
        chain._CROSSCHECK = prev


# --- 3. the read program end-to-end ----------------------------------------------------------------

def test_focus_scope_flows_through_the_live_set_register():
    """`focus_scope` reaches the read as MEMBER-over-register (transitionally parked by
    `_facts_matching_isa` itself), and the register is restored afterwards."""
    g = AttrGraph()
    ids = {nm: g.add_node(nm) for nm in ("ada", "bo", "cy", "dee")}
    g.add_relation(ids["ada"], "knows", ids["bo"])
    g.add_relation(ids["cy"], "knows", ids["dee"])
    g.registers[chain._FOCUS_LIVE] = frozenset({"sentinel"})   # a pre-existing value must survive
    out = chain._facts_matching(g, "knows", None, None, focus_scope=frozenset({"ada"}))
    assert len(out) == 1                                   # only the fact touching the working set
    assert g.registers[chain._FOCUS_LIVE] == frozenset({"sentinel"})   # restored


def test_guarded_read_skips_marked_twins_end_to_end():
    """The in-program guard reproduces the old post-filter: same-named control/inert twins are
    invisible to a demand read (cross-checked against the walk oracle by the differential suite)."""
    g = AttrGraph()
    ada = g.add_node("ada")
    bo = g.add_node("bo")
    ctrl = g.add_node("ada", control=True)
    inert = g.add_node("bo", inert=True)
    g.add_relation(ada, "knows", bo)
    g.add_relation(ctrl, "knows", bo)                      # control subject -> invisible
    g.add_relation(ada, "knows", inert)                    # inert object -> invisible
    prev = chain._CROSSCHECK
    chain._CROSSCHECK = True
    try:
        out = chain._facts_matching(g, "knows", "ada", None)
    finally:
        chain._CROSSCHECK = prev
    assert len(out) == 1


def test_focused_chain_derivation_still_bounded():
    facts = AttrGraph()
    ids = {nm: facts.add_node(nm) for nm in ("ada", "bo", "cy", "dee")}
    facts.add_relation(ids["ada"], "knows", ids["bo"])
    facts.add_relation(ids["cy"], "knows", ids["dee"])
    rules = AttrGraph()
    h.write_rule(rules, Rule(key="ack", lhs=[Pat("?x", "knows", "?y")],
                             rhs=[Pat("?x", "ack", "?y")]))
    chain_sip(facts, ("ack", None, None), focus_scope=frozenset({"ada", "bo"}), rules=rules)
    acked = {(s, o) for s, p, o in derived_triples(facts) if p == "ack"}
    assert acked == {("ada", "bo")}
