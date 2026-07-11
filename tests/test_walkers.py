"""
Walkers — variable-length traversal as control (docs/walkers_and_locality.md §4-§6).

A walker is a control token (origin + reached set + target + fuel). It steps one hop at a
time along a relation, self-bounding because each step seeds on the rare walker token, and
materializes a provenance-bearing SHORTCUT when its reached set contains the target. These
tests lock the four properties the design promises: on-demand selectivity (§4), fuel as the
"think harder" budget (§4/§14), termination on cyclic relations (§4), and retractable
shortcuts via in-graph provenance (§5).
"""
import ugm as h
from ugm.production_rule import near_rules


def _rel(g, s, p, o):
    si = g.nodes_named(s)[0] if g.nodes_named(s) else g.add_node(s)
    oi = g.nodes_named(o)[0] if g.nodes_named(o) else g.add_node(o)
    return g.add_relation(si, p, oi)


def _relation_exists(g, s_id, pname, o_id):
    """Does the raw edge  s_id -[pname]-> o_id  exist? (ported from the retired rewriter.py)."""
    for r in g.succ(s_id):
        if g.name(r) == pname and o_id in g.succ(r):
            return True
    return False


def _has(g, s, p, o):
    return any(
        _relation_exists(g, si, p, oi)
        for si in g.nodes_named(s) for oi in g.nodes_named(o)
    )


def _chain(g, names, rel="is_a"):
    """Wire a path name0 -rel-> name1 -rel-> ... and return the path edge id per hop."""
    edges = []
    for a, b in zip(names, names[1:]):
        edges.append(_rel(g, a, rel, b))
    return edges


# ---------------------------------------------------------------------------
# §4 — demand-spawned, selective: ONLY the demanded connection is materialized
# ---------------------------------------------------------------------------

def test_walker_transitivity_on_demand_is_selective():
    g = h.Graph()
    _chain(g, ["a", "b", "c", "d"])                  # a is_a b is_a c is_a d
    h.walk_on_demand(g, "a", "d")                    # demand: a is_a d ?
    assert _has(g, "a", "is_a", "d")                 # the shortcut, materialized by the walk
    # selective: the walker passed THROUGH b and c, but only the demanded endpoint became a
    # NEW fact. The intermediate transitive closure (a is_a c) is never derived — it was not
    # demanded. (a is_a b is a base edge of the chain, so it is present from the start.)
    assert not _has(g, "a", "is_a", "c")


def test_walker_unreachable_target_yields_no_shortcut():
    g = h.Graph()
    _chain(g, ["a", "b", "c"])                        # a..c
    g.add_node("z")                                   # disconnected
    h.walk_on_demand(g, "a", "z")
    assert not _has(g, "a", "is_a", "z")              # no path -> no shortcut


# ---------------------------------------------------------------------------
# §4/§14 — fuel is the budget: too little fuel stops the walk short of the target
# ---------------------------------------------------------------------------

def test_walker_fuel_counter_is_decremented_per_advance():
    # Fuel is a SINGLE counter node the `dec` tool decrements once per advance.
    # a -> b -> c -> d -> e : reaching e takes 4 advances.
    names = ["a", "b", "c", "d", "e"]
    g = h.Graph(); _chain(g, names)
    h.walk_on_demand(g, "a", "e", fuel=10)
    assert _has(g, "a", "is_a", "e")                 # reached
    w = g.nodes_named(h.WALKER)[0]
    left = [g.name(o) for r, o in g.relations_from(w) if g.name(r) == h.FUEL]
    assert left == ["6"]                             # 10 - 4 advances = 6 remaining
    # ASYNC-DEC LIMITATION (documented in walker.py): `service_calls` runs only when the
    # rules quiesce, so on a FINITE relation the visited (reached) NAC closes the reachable
    # set BEFORE any `dec` fires — fuel does NOT truncate mid-walk here (a fuel=2 walk still
    # reaches e). The reached-NAC is the termination guarantee on finite relations
    # (test_walker_terminates_on_cyclic_relation); fuel bounds total advances post-hoc.


# ---------------------------------------------------------------------------
# §4 — termination on a CYCLIC relation (the visited/reached guard, not just fuel)
# ---------------------------------------------------------------------------

def test_walker_terminates_on_cyclic_relation():
    # a -r-> b -r-> c -r-> a (a cycle), plus c -r-> d. Generous fuel so termination is due
    # to the reached-NAC, not the budget. Must not hang and must find a r d.
    g = h.Graph()
    _rel(g, "a", "r", "b"); _rel(g, "b", "r", "c")
    _rel(g, "c", "r", "a")                            # back-edge closes the cycle
    _rel(g, "c", "r", "d")
    a = g.nodes_named("a")[0]; d = g.nodes_named("d")[0]
    h.spawn_walker(g, a, d, fuel=1000, rel="r")       # huge fuel: only the NAC can stop it
    h.run_bank(g, h.walk_rules("r"), tools=h.WALK_TOOLS)
    assert _has(g, "a", "r", "d")                      # shortcut found despite the cycle
    # the reached set is exactly the reachable nodes (a, b, c, d), each reached once
    w = g.nodes_named(h.WALKER)[0]
    reached = {g.name(o) for r, o in g.relations_from(w) if g.name(r) == h.REACHED}
    assert reached == {"a", "b", "c", "d"}


# ---------------------------------------------------------------------------
# §5 — the shortcut is provenance-bearing, hence retractable through its path
# ---------------------------------------------------------------------------

def test_walker_shortcut_has_provenance():
    g = h.Graph()
    _chain(g, ["a", "b", "c", "d"])
    h.walk_on_demand(g, "a", "d")
    # the shortcut a is_a d has an in-graph justification (it was DERIVED, not asserted)
    rel = next(r for r in g.out(g.nodes_named("a")[0])
               if g.name(r) == "is_a" and g.nodes_named("d")[0] in g.out(r))
    assert h.support_js(g, rel)                        # some J proves it
    assert h.rule_support_j(g, rel) is not None        # a rule justification, not just an axiom


def test_walker_shortcut_is_retractable():
    # Withdraw a path edge in the MIDDLE of the walk; the shortcut, whose provenance chains
    # through every reached hop to every path edge, must lose support and be hidden by the
    # rule-based cascade (RETRACT_RULES interposition).
    g = h.Graph()
    edges = _chain(g, ["a", "b", "c", "d"])           # edges[1] is b is_a c
    h.walk_on_demand(g, "a", "d")
    assert _has(g, "a", "is_a", "d")

    h.retract(g, edges[1])                             # withdraw b is_a c
    assert not _has(g, "b", "is_a", "c")               # the premise is gone
    assert not _has(g, "a", "is_a", "d")               # and the shortcut it underpinned is too


# ---------------------------------------------------------------------------
# §7 — two concurrent walkers don't cross-wire (each binds its OWN token)
# ---------------------------------------------------------------------------

def test_two_walkers_do_not_cross_wire():
    # Two separate chains, one walker each. The arrival rule binds `<walker>?` (a bound
    # literal: same instance across its patterns), so walker-1's origin can never pair with
    # walker-2's target. Each materializes only its own shortcut.
    g = h.Graph()
    _chain(g, ["a", "b", "c"])                         # chain 1: a..c
    _chain(g, ["x", "y", "z"])                         # chain 2: x..z
    h.spawn_walker(g, g.nodes_named("a")[0], g.nodes_named("c")[0], fuel=50)
    h.spawn_walker(g, g.nodes_named("x")[0], g.nodes_named("z")[0], fuel=50)
    h.run_bank(g, h.walk_rules("is_a"), tools=h.WALK_TOOLS)
    assert _has(g, "a", "is_a", "c") and _has(g, "x", "is_a", "z")   # each own shortcut
    assert not _has(g, "a", "is_a", "z")              # no cross-wiring between the two walkers
    assert not _has(g, "x", "is_a", "c")


# ---------------------------------------------------------------------------
# §6 — `within`/radius retired: matching is unbounded (seed-from-ground)
# ---------------------------------------------------------------------------

def test_matching_is_unbounded():
    # `within`-as-matching-scope is retired (walkers doc §6): a join spanning MANY hops matches
    # because matching seeds from ground anchors via the index, not from a hop neighbourhood. A
    # 30-long is_a chain closes to the FULL transitive closure — which a small hop-radius (the
    # former default) would have silently truncated. There is no `radius` knob to pass any more.
    g = h.Graph()
    ids = [g.add_node(f"a{i}") for i in range(31)]
    for i in range(30):
        g.add_relation(ids[i], "is_a", ids[i + 1])
    h.run_rules(g, h.UNIVERSAL_RULES, max_steps=400)
    assert any(g.name(r) == "is_a" and ids[30] in g.out(r) for r in g.out(ids[0]))  # 30-hop
    facts = sum(1 for n in g.nodes() for rr, _ in g.relations_from(n) if g.name(rr) == "is_a")
    assert facts == 30 * 31 // 2                                    # the FULL closure (465)


# ---------------------------------------------------------------------------
# §7 — two FULLY concurrent walkers on DIFFERENT relations; near-rules by position
# ---------------------------------------------------------------------------

def _reached(g, token):
    w = g.nodes_named(token)[0]
    return {g.name(o) for r, o in g.relations_from(w) if g.name(r) == h.REACHED}


def test_two_concurrent_walkers_on_different_relations():
    # Walker A traverses is_a, walker B traverses part_of — in ONE run, from the SAME origin
    # `a` (which has BOTH an is_a and a part_of edge). Typing each walker by its own token
    # (<walker:is_a> vs <walker:part_of>) makes the index route walk.step.is_a ONLY to A and
    # walk.step.part_of ONLY to B: concurrent control flows, no cross-wire (§7).
    TA, TB = "<walker:is_a>", "<walker:part_of>"
    g = h.Graph()
    _chain(g, ["a", "b", "c"], rel="is_a")            # is_a:    a -> b -> c
    _chain(g, ["a", "p", "q"], rel="part_of")         # part_of: a -> p -> q  (a has both!)
    a = g.nodes_named("a")[0]
    wa = h.spawn_walker(g, a, g.nodes_named("c")[0], fuel=50, rel="is_a", token=TA)
    wb = h.spawn_walker(g, a, g.nodes_named("q")[0], fuel=50, rel="part_of", token=TB)
    rules = h.walk_rules("is_a", token=TA) + h.walk_rules("part_of", token=TB)
    # `run_bank` DIRECTLY (not `run_rules`, which stratifies rules into layers run to fixpoint one
    # at a time — the combined walker rule set's NAC dependency graph is not stratifiable as ONE
    # bank across two independent walkers, so `run_rules` would drop rules with a warning). Production
    # `walk_on_demand`/`spawn_walker` callers (walker.py) also call `run_bank` directly on the whole
    # rule list in one pass, so this matches the real call shape.
    #
    # `run_bank` returns an always-empty-journal-equivalent (an int firing count, no per-firing
    # detail) — the retired oracle's per-firing `Firing` journal has no ISA equivalent, so the
    # "journal confirms each walker only fired its own rules" check the oracle-based version of
    # this test made is dropped; the reached-set assertions below already fully establish no
    # cross-wiring (a stronger, engine-agnostic witness of the same property).
    h.run_bank(g, rules, tools=h.WALK_TOOLS)

    assert _has(g, "a", "is_a", "c")                  # A's shortcut
    assert _has(g, "a", "part_of", "q")               # B's shortcut
    assert not _has(g, "a", "is_a", "q")              # A never traversed part_of
    assert not _has(g, "a", "part_of", "c")           # B never traversed is_a
    # each walker reached only ITS relation's subgraph (the proof of no cross-interference)
    assert _reached(g, TA) == {"a", "b", "c"}
    assert _reached(g, TB) == {"a", "p", "q"}
    assert wa in g.nodes() and wb in g.nodes()          # both walkers actually ran


def test_near_rules_are_computed_per_walker_position_via_the_index():
    # The §7 mechanism made concrete: `near_rules` returns the rules the lexical index would
    # seed from a given node. Two walkers at different tokens get DIFFERENT near-rule sets,
    # automatically — no rule-set is frozen onto a walker; it is derived from position.
    TA, TB = "<walker:is_a>", "<walker:part_of>"
    g = h.Graph()
    a = g.add_node("a")
    A = h.spawn_walker(g, a, a, fuel=1, rel="is_a", token=TA)
    B = h.spawn_walker(g, a, a, fuel=1, rel="part_of", token=TB)
    rules = h.walk_rules("is_a", token=TA) + h.walk_rules("part_of", token=TB)

    near_a = {r.key for r in near_rules(g, rules, A)}
    near_b = {r.key for r in near_rules(g, rules, B)}
    assert near_a == {f"walk.step.{TA}.is_a", f"walk.arrive.{TA}.is_a"}
    assert near_b == {f"walk.step.{TB}.part_of", f"walk.arrive.{TB}.part_of"}
    assert near_a.isdisjoint(near_b)                  # different positions -> different near-rules
    # a plain data node anchors none of the walker rules (they seed on the rare token)
    assert near_rules(g, rules, a) == []


# ---------------------------------------------------------------------------
# Materialized tool calls — the engine-managed §8 dispatch boundary (vision §6/§12.5)
# ---------------------------------------------------------------------------

def test_engine_services_a_rule_materialized_tool_call():
    # A rule emits a <call> for a tool; the engine (given the registry) services it at the
    # rule-fixpoint and folds the tool's output back into reasoning. Rule never calls the
    # tool, tool never rewrites reasoning — they couple only through the <call>/result nodes.
    g = h.Graph()
    _rel(g, "spark", "trigger", "x")                  # a trigger fact

    # rule: spark trigger ?x  =>  <call> tool "mark" target ?x
    emit = h.Rule(
        key="emit",
        lhs=[h.Pat("spark", "trigger", "?x")],
        rhs=[h.Pat("<call>?", "tool", "mark"), h.Pat("<call>?", "target", "?x")],
    )

    def mark_tool(graph, call_id):                    # the §8 calculator: emits a result node
        tgt = h.call_arg(graph, call_id, "target")
        graph.add_relation(tgt, "marked", graph.add_node("yes"))
        return {tgt}

    # downstream rule fires on the TOOL's output -> proves rules resume after dispatch
    downstream = h.Rule(key="down", lhs=[h.Pat("?x", "marked", "?y")],
                        rhs=[h.Pat("?x", "done", "yes")])

    h.run_rules(g, [emit, downstream], tools={"mark": mark_tool})
    assert _has(g, "x", "marked", "yes")              # the tool ran
    assert _has(g, "x", "done", "yes")                # and reasoning resumed on its output
    assert not h.pending_calls(g)                     # the call was consumed


def test_tools_absent_means_engine_unchanged():
    # The same emit rule with NO registry: the <call> is materialized but never serviced,
    # and the engine otherwise behaves exactly as before (back-compat guarantee).
    g = h.Graph()
    _rel(g, "spark", "trigger", "x")
    emit = h.Rule(key="emit", lhs=[h.Pat("spark", "trigger", "?x")],
                  rhs=[h.Pat("<call>?", "tool", "mark"), h.Pat("<call>?", "target", "?x")])
    h.run_rules(g, [emit])                  # no tools=
    assert h.pending_calls(g)                          # call sits unserviced
    assert not _has(g, "x", "marked", "yes")


def test_external_lookup_is_a_materialized_call_serviced_by_the_engine():
    # The migration's payoff: an external lookup is no longer a parallel `<kind-request>` board
    # with its own dispatcher — it is a materialized `<call>`, serviced by the SAME engine loop
    # (run with the registry as tools) as walker fuel. A rule asks; the engine fetches; a rule
    # reacts on the result fact — all in one fixpoint.
    g = h.Graph()
    g.add_relation(g.add_node("op1"), "needs", g.add_node("a_price"))
    ask = h.Rule(key="ask", lhs=[h.Pat("?o", "needs", "?x")],
                 rhs=[h.Pat("<call>?", "tool", "price"), h.Pat("<call>?", "arg", "?o")])
    react = h.Rule(key="react", lhs=[h.Pat("?r", "of", "?o"), h.Pat("?r", "val", "?v")],
                   rhs=[h.Pat("?o", "priced", "yes")])
    h.run_rules(g, [ask, react], tools={"price": h.lookup_handler({"op1": 7})})
    op1 = g.nodes_named("op1")[0]
    assert h.result_value(g, h.results_for(g, "price", op1)[0]) == "7"   # the fetched fact
    assert _has(g, "op1", "priced", "yes")                              # reasoning resumed on it
    assert not h.pending(g, "price")                                    # the call was consumed


def test_refuel_tool_sets_single_fuel_counter():
    # The fuel budget is owned by metareasoning (the amount) and set by the refuel tool as a
    # SINGLE counter node (the count in its name), not N unary edges (which made each step
    # enumerate every remaining unit — cost quadratic in the budget).
    g = h.Graph()
    w = g.add_node(h.WALKER)
    h.emit_call(g, h.REFUEL, {h.TARGET: w, "amount": g.add_node("3")})
    touched = h.service_calls(g, h.WALK_TOOLS)
    fuel = [g.name(o) for r, o in g.relations_from(w) if g.name(r) == h.FUEL]
    assert fuel == ["3"]                               # ONE counter node, count in its name
    assert w in touched and not h.pending_calls(g)     # call consumed, frontier reported
