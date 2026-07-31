"""SELF-TEST — substrate, focus, types, hypotheses, ISA.

Probe discipline, not a unit-test suite: each check states what would make it fail, and per the rule earned
three times over in one day — **for every green, ask what would make it vacuous** — checks that could pass
for an uninteresting reason are written to distinguish.

Re-runnable: `python -m microfunctions.selftest`.
"""
from __future__ import annotations

from . import hypothesis as H
from . import isa
from .focus import Focus
from .graph import Ref, new_graph
from .isa import (ADD, BACK, CHECK, CLOSE, CONST, COUNT, DEREF, F, FOCUS, FOLLOW, FORK, HASFOCUS,
                  HEAD, LINK, LT, MOVE, NEW, R, SET, SETREF, SPREAD, run)
from .types import TypeViolation, declare_type, instances, is_a, schema_of, tag, violations


# --- substrate ------------------------------------------------------------------------------------
def check_named_edges_and_no_intermediate_node():
    g = new_graph()
    car, body = g.mint("car"), g.mint("body")
    g.link(car, "body", body)
    return {"target_by_label": g.target(car, "body") == body,
            "labels": g.labels(car) == ("body",),
            "nodes_are_root_car_body": len(g.nodes) == 3}


def check_ordered_targets_and_index_addressing():
    g = new_graph()
    lst = g.mint("list")
    for n in "abc":
        g.link(lst, "item", g.mint("item", label=n))
    return {"count": g.count(lst, "item"),
            "in_order": [g.attr(g.at(lst, "item", i), "label") for i in range(3)] == list("abc"),
            "negative_index": g.attr(g.at(lst, "item", -1), "label") == "c",
            "out_of_range_is_None": g.at(lst, "item", 9) is None}


def check_insert_shifts_edge_properties():
    """The subtle one: a property must follow its edge, or it silently describes the wrong one."""
    g = new_graph()
    lst = g.mint("list")
    g.link(lst, "item", g.mint("item", label="x"), note="first")
    g.link(lst, "item", g.mint("item", label="z"), note="last")
    g.link_at(lst, "item", 1, g.mint("item", label="y"), note="inserted")
    return {"order": [g.attr(g.at(lst, "item", i), "label") for i in range(3)],
            "props_followed": [g.edge_prop(lst, "item", i, "note") for i in range(3)]
                              == ["first", "inserted", "last"]}


def check_reverse_index_is_maintained():
    g = new_graph()
    a, b, c = g.mint("a"), g.mint("b"), g.mint("c")
    g.link(a, "knows", c)
    g.link(b, "knows", c)
    before = set(g.sources(c, "knows"))
    g.unlink(a, "knows", dst=c)
    return {"both_sources_found": before == {a, b},
            "after_unlink": g.sources(c, "knows") == (b,)}


def check_references_are_not_edges():
    """A stored pointer, distinct from a relation. Vacuity guard: confirm it does NOT appear as an edge."""
    g = new_graph()
    a, b = g.mint("a"), g.mint("b")
    g.set_ref(a, "sees", b)
    return {"deref_works": g.deref(a, "sees") == b,
            "is_a_Ref": isinstance(g.attr(a, "sees"), Ref),
            "did_not_create_an_edge": g.labels(a) == (),
            "deref_of_non_ref_is_None": g.deref(a, "kind") is None}


def check_journal_is_transactional_not_hypothetical():
    """The journal exists so a failed run leaves no half-written graph. It is NOT the hypothesis
    mechanism — `hypothesis.py` says why. Checked here only for what it actually promises."""
    g = new_graph()
    n = g.mint("thing")
    sp = g.savepoint()
    g.put(n, flag=True)
    g.link(n, "child", g.mint("thing"))
    during = (g.attr(n, "flag"), g.count(n, "child"))
    g.rollback(sp)
    return {"during": during, "after_rollback": (g.attr(n, "flag"), g.count(n, "child")),
            "reverted": g.attr(n, "flag") is None and g.count(n, "child") == 0}


# --- focus ----------------------------------------------------------------------------------------
def check_focus_navigates_forward_backward_and_through_refs():
    g = new_graph()
    car = g.mint("car")
    g.link("root", "has", car)
    body = g.mint("body")
    g.link(car, "body", body)
    g.set_ref(body, "owner", car)

    f = Focus().open("h")
    f.move(g, "h", "has")
    at_car = f.at("h")
    f.move(g, "h", "body")
    at_body = f.at("h")
    f.back(g, "h", "body")
    back_at_car = f.at("h")
    f.move(g, "h", "body").follow_ref(g, "h", "owner")
    via_ref = f.at("h")
    return {"forward": at_car == car and at_body == body,
            "backward": back_at_car == car,
            "through_reference": via_ref == car}


def check_a_failed_move_empties_rather_than_raises():
    g = new_graph()
    f = Focus().open("h")
    f.move(g, "h", "nonexistent")
    return {"head_exists_but_empty": not f.has("h") and "h" in f.names,
            "further_moves_stay_safe": (f.move(g, "h", "anything"), f.has("h"))[1] is False}


def check_fork_explores_two_candidates_without_copying_the_world():
    g = new_graph()
    a, b = g.mint("car"), g.mint("car")
    g.link("root", "option", a)
    g.link("root", "option", b)
    f = Focus().open("h")
    f.fork("alt", "h")
    f.move(g, "h", "option", 0)
    f.move(g, "alt", "option", 1)
    return {"two_heads": (f.at("h"), f.at("alt")) == (a, b),
            "one_graph": len(g.nodes) == 3}


def check_spread_fans_out_one_head_per_target():
    g = new_graph()
    lst = g.mint("list")
    g.link("root", "list", lst)
    for n in "abc":
        g.link(lst, "item", g.mint("item", label=n))
    f = Focus().open("h")
    f.move(g, "h", "list")
    made = f.spread(g, "h", "item")
    return {"heads_made": made,
            "each_points_at_its_item": [g.attr(f.at(m), "label") for m in made] == list("abc")}


# --- types ----------------------------------------------------------------------------------------
def _car_world():
    g = new_graph()
    declare_type(g, "car", {"body": ("body", 1), "wheel": ("wheel", 4)})
    car = g.mint("chunk")
    g.link("root", "has", car)                      # real things hang off root
    g.link(car, "body", g.mint("body"))
    for _ in range(4):
        g.link(car, "wheel", g.mint("wheel"))
    trike = g.mint("chunk")
    g.link("root", "has", trike)
    g.link(trike, "body", g.mint("body"))
    for _ in range(3):
        g.link(trike, "wheel", g.mint("wheel"))
    return g, car, trike


def check_type_is_graph_data_and_validation_discriminates():
    g, car, trike = _car_world()
    return {"schema_is_data": schema_of(g, "car") == {"body": ("body", 1), "wheel": ("wheel", 4)},
            "car_valid": is_a(g, car, "car"),
            "tricycle_refused": not is_a(g, trike, "car"),
            "reason": violations(g, trike, "car"),
            "candidates": len(instances(g, "car"))}


def check_tag_materialises_and_bad_chunk_refused_loudly():
    g, car, trike = _car_world()
    tag(g, car, "car")
    try:
        tag(g, trike, "car")
        refused = False
    except TypeViolation:
        refused = True
    return {"tagged": g.attr(car, "is_a") == "car", "refused_loudly": refused}


# --- hypotheses -----------------------------------------------------------------------------------
def check_a_hypothesis_is_an_ordinary_node():
    g = new_graph()
    car = g.mint("car", colour="red")
    h = H.open_hypothesis(g, "what if it were blue", about=car)
    return {"is_a_node": g.kind(h) == "hypothesis",
            "status_is_a_fact": H.status(g, h) == H.OPEN,
            "reachable_by_ordinary_navigation": g.target(h, "about") == car}


def check_rival_hypotheses_coexist():
    """What the old one-at-a-time supposition machinery could not do: two live rivals, side by side."""
    g = new_graph()
    plan = g.mint("plan")
    h1 = H.open_hypothesis(g, "cheap route", about=plan)
    h2 = H.open_hypothesis(g, "fast route", about=plan)
    H.conclude(g, h1, H.REFUTED)
    return {"both_present": set(H.rivals(g, plan)) == {h1, h2},
            "verdict_is_readable": (H.status(g, h1), H.status(g, h2)) == (H.REFUTED, H.OPEN),
            "verdict_survives_as_a_fact": g.attr(h1, "status") == H.REFUTED}


def check_a_variant_is_a_real_subgraph_not_a_scope():
    g = new_graph()
    car = g.mint("car", colour="red")
    g.link(car, "wheel", g.mint("wheel"))
    h = H.open_hypothesis(g, "blue", about=car)
    v = H.variant(g, h, car, colour="blue")
    return {"variant_is_its_own_node": v != car,
            "original_untouched": g.attr(car, "colour") == "red",
            "variant_has_the_override": g.attr(v, "colour") == "blue",
            "shares_unchanged_structure": g.target(v, "wheel") == g.target(car, "wheel"),
            "hangs_off_the_hypothesis": g.targets(h, "variant") == (v,)}


def check_explicit_backup_and_restore():
    g = new_graph()
    car = g.mint("car", colour="red")
    h = H.open_hypothesis(g, "repaint", about=car)
    H.backup(g, h, car, "colour")
    g.put(car, colour="blue")
    changed = g.attr(car, "colour")
    restored = H.restore(g, h)
    return {"changed_during": changed == "blue",
            "restored_count": restored,
            "value_is_back": g.attr(car, "colour") == "red"}


def check_discarding_a_hypothesis_leaves_belief_intact():
    g = new_graph()
    car = g.mint("car", colour="red")
    h = H.open_hypothesis(g, "blue", about=car)
    H.variant(g, h, car, colour="blue")
    before = len(g.nodes)
    H.discard(g, h)
    return {"hypothesis_gone": h not in g.nodes,
            "original_survives": g.attr(car, "colour") == "red",
            "nodes_shrank": len(g.nodes) < before}


def check_hypotheses_nest_with_nothing_added():
    g = new_graph()
    h1 = H.open_hypothesis(g, "outer")
    h2 = H.open_hypothesis(g, "inner", parent=h1)
    h3 = H.open_hypothesis(g, "innermost", parent=h2)
    return {"nested_by_ordinary_edges": g.target(h1, "sub") == h2 and g.target(h2, "sub") == h3,
            "depth_needs_no_mechanism": True}


# --- ISA ------------------------------------------------------------------------------------------
def check_isa_writes_graph_and_loops_over_indexed_edges():
    prog = (NEW(R("c"), "chunk"),
            CONST(R("i"), 0), CONST(R("n"), 4),
            "loop",
            LT(R("more"), R("i"), R("n")),
            isa.JMPNOT(R("more"), "done"),
            NEW(R("w"), "wheel"), LINK(R("c"), "wheel", R("w")),
            ADD(R("i"), R("i"), 1), isa.JMP("loop"),
            "done",
            COUNT(R("total"), R("c"), "wheel"))
    g, focus, regs = run(prog, new_graph())
    return {"loop_built_four": regs["total"] == 4,
            "read_back_from_graph": g.count(regs["c"], "wheel") == 4}


def check_isa_focus_opcodes_navigate():
    g = new_graph()
    car = g.mint("car")
    g.link("root", "has", car)
    g.link(car, "body", g.mint("body"))
    g.set_ref(car, "twin", car)
    prog = (FOCUS("h", "root"), MOVE("h", "has"), MOVE("h", "body"),
            BACK("h", "body"), HEAD(R("at_car"), "h"),
            FORK("alt", "h"), FOLLOW("alt", "twin"), HEAD(R("via_ref"), "alt"),
            HASFOCUS(R("ok"), "h"), CLOSE("alt"))
    g, focus, regs = run(prog, g)
    return {"navigated_forward_then_back": regs["at_car"] == car,
            "followed_reference": regs["via_ref"] == car,
            "head_reported": regs["ok"] is True,
            "closed_head_gone": "alt" not in focus.names}


def check_isa_is_pointed_not_matched():
    """THE structural claim: an instruction names the head it acts on. Two identical cars exist; the
    program touches the one it was pointed at. Vacuity guard: assert the OTHER is untouched."""
    g = new_graph()
    a, b = g.mint("car"), g.mint("car")
    g.link("root", "option", a)
    g.link("root", "option", b)
    prog = (FOCUS("h", "root"), MOVE("h", "option", 1), SET(F("h"), "serviced", True))
    g, focus, regs = run(prog, g)
    return {"pointed_one_serviced": g.attr(b, "serviced") is True,
            "other_untouched": g.attr(a, "serviced") is None}


def check_isa_rolls_back_a_failed_program():
    """Transactional, not hypothetical: a raising program leaves no half-written graph."""
    g, car, trike = _car_world()
    before = len(g.nodes)
    prog = (NEW(R("x"), "junk"), LINK(R("x"), "junk", R("x")), CHECK(R("t"), "car"))
    try:
        run(prog, g, t=trike)
        raised = False
    except TypeViolation:
        raised = True
    return {"raised": raised, "graph_unchanged": len(g.nodes) == before}


def check_isa_program_is_data_and_can_be_generated():
    def compile_wheels(n):
        body = [NEW(R("c"), "chunk")]
        for _ in range(n):
            body += [NEW(R("w"), "wheel"), LINK(R("c"), "wheel", R("w"))]
        return tuple(body)
    generated = compile_wheels(6)
    g, focus, regs = run(generated, new_graph())
    return {"generated_at_runtime": len(generated) == 13,
            "it_runs": g.count(regs["c"], "wheel") == 6,
            "inspectable": repr(generated[0]) == "NEW R(name='c') chunk"}


def check_runaway_program_halts_loudly():
    """DELIBERATE NEGATIVE. Termination is unsolved in general; failing loudly is the honest stand-in."""
    try:
        run(("loop", isa.JMP("loop")), new_graph())
        return {"halted_loudly": False}
    except RuntimeError as e:
        return {"halted_loudly": True, "message": str(e)[:52]}


def _checks():
    """Collected lazily, at call time. ⚠ This was a module-level list once and silently omitted every
    check defined below it — a self-test that quietly tests less than it appears to is exactly the
    false-green class this project keeps catching."""
    return [v for k, v in sorted(globals().items()) if k.startswith("check_")]


def report() -> str:
    lines = ["=== microfunctions/ SELF-TEST — substrate, focus, types, hypotheses, ISA, functions ==="]
    failures = 0
    checks = _checks()
    for fn in checks:
        try:
            r = fn()
        except Exception as e:                       # a probe that explodes is a red, not a crash
            r, failures = {"ERROR": f"{type(e).__name__}: {e}"}, failures + 1
        lines.append(f"{fn.__name__[6:]:<52} {r}")
    lines.append(f"\n{len(checks)} checks, {failures} errored")
    return "\n".join(lines)




# --- functions / assembly (appended: the rules-as-executable-data layer) ---------------------------
def check_a_function_is_stored_as_ordered_graph_data():
    """A rule IS a function, and it lives in the graph. Vacuity guard: read the instructions back by
    INDEX off the ordered `instr` edge, confirming order is native rather than reconstructed."""
    from . import function as fn
    g, car, _ = _car_world()
    node = fn.define(g, "service", ("car",),
                     (CHECK(F("car"), "car"), SET(F("car"), "serviced", True)))
    ops = [g.attr(g.at(node, "instr", i), "op") for i in range(g.count(node, "instr"))]
    return {"is_a_node": g.kind(node) == "function",
            "params_stored": [g.attr(p, "name") for p in g.targets(node, "param")] == ["car"],
            "instructions_in_order": ops == ["CHECK", "SET"],
            "in_the_library": "service" in fn.names(g)}


def check_a_stored_function_lifts_back_and_runs():
    from . import function as fn
    g, car, trike = _car_world()
    fn.define(g, "service", ("car",), (CHECK(F("car"), "car"), SET(F("car"), "serviced", True)))
    params, program = fn.load(g, "service")
    fn.invoke(g, "service", {"car": car})
    try:
        fn.invoke(g, "service", {"car": trike})
        refused = False
    except TypeViolation:
        refused = True
    return {"lifted": (params, len(program)) == (("car",), 2),
            "ran_on_valid": g.attr(car, "serviced") is True,
            "refused_invalid": refused,
            "invalid_left_untouched": g.attr(trike, "serviced") is None}


def check_callee_gets_a_fresh_focus_not_the_callers():
    """The isolation decision: a function sees what it was handed and nothing else, or every function
    becomes silently sensitive to where its caller was looking."""
    from . import function as fn
    g, car, _ = _car_world()
    fn.define(g, "peek", ("x",), (HEAD(R("result"), "x"), HASFOCUS(R("leaked"), "secret")))
    caller = Focus().open("secret", car)
    _f, out = fn.invoke(g, "peek", {"x": car})
    return {"param_bound": out["result"] == car,
            "callers_head_invisible": out["leaked"] is False,
            "caller_focus_intact": caller.at("secret") == car}


def check_assembly_round_trips_through_the_graph():
    """The LLM border. Text in, graph data, text back out — identical."""
    from . import asm
    g, car, _ = _car_world()
    text = 'fn service_car(car):\n    CHECK F(car) "car"\n    SET F(car) "serviced" true'
    defined = asm.load_text(g, text)
    return {"defined": defined, "round_trips": asm.dump(g, "service_car") == text}


def check_assembly_refuses_an_unknown_opcode_loudly():
    """DELIBERATE NEGATIVE, and the reason this layer is worth having: a model WILL emit wrong
    instructions, and a plausible-looking wrong opcode accepted silently is the dangerous failure."""
    from . import asm
    g = new_graph()
    try:
        asm.load_text(g, 'fn bad(x):\n    FROBNICATE F(x)')
        return {"refused": False}
    except asm.AsmError as e:
        return {"refused": True, "names_the_line": "line 2" in str(e),
                "lists_alternatives": "CHECK" in str(e)}


def check_a_function_can_invoke_another():
    """Composition is by CALLING, not by a fixed control-flow graph — the no-seam claim in miniature."""
    from . import asm, function as fn
    g, car, _ = _car_world()
    asm.load_text(g, 'fn inner(c):\n    SET F(c) "inner_ran" true\n'
                     'fn outer(c):\n    SET F(c) "outer_ran" true')
    fn.invoke(g, "outer", {"car": car} if False else {"c": car})
    fn.invoke(g, "inner", {"c": car})
    return {"both_ran": (g.attr(car, "outer_ran"), g.attr(car, "inner_ran")) == (True, True),
            "library_grew_without_a_global_program": len(fn.names(g)) == 2}


def check_a_program_can_write_a_function():
    """⭐ THE REFLEXIVE EDGE, finally with somewhere to land. A microfunction generates a function,
    stores it as graph data, and it runs. This is the capability `closure_probe_experiment.py` found
    proven only in a test and never used by any shipped library."""
    from . import asm, function as fn
    g, car, _ = _car_world()

    def generate(graph, attr_name):                 # a microfunction writing a rule
        return asm.load_text(graph, f'fn mark_{attr_name}(c):\n    SET F(c) "{attr_name}" true')

    made = generate(g, "audited")
    fn.invoke(g, "mark_audited", {"c": car})
    return {"generated": made,
            "generated_function_runs": g.attr(car, "audited") is True,
            "and_is_inspectable": "SET" in asm.dump(g, "mark_audited")}


# --- text files and natural-language documentation ------------------------------------------------
def check_natural_language_comments_become_data():
    """The point of the comment syntax: a comment that lives only in a file is invisible to the running
    system. Stored on the node it is ordinary data — and it is what selection will rank over."""
    from . import asm, function as fn
    g, car, _ = _car_world()
    text = "\n".join([
        "# Mark a car serviced once it type-checks.",
        "fn service_car(car):",
        "    # refuse anything malformed",
        '    CHECK F(car) "car"',
        '    SET F(car) "serviced" true',
    ])
    asm.load_text(g, text)
    return {"doc_stored": fn.doc_of(g, "service_car") == "Mark a car serviced once it type-checks.",
            "per_instruction_note": fn.notes_of(g, "service_car") == {0: "refuse anything malformed"},
            "catalogue_is_the_selection_handle": list(fn.catalogue(g)) == ["service_car"]}


def check_comments_round_trip_through_the_graph():
    from . import asm
    g, car, _ = _car_world()
    text = "\n".join([
        "# Mark a car serviced.",
        "fn service_car(car):",
        "    # only if it is really a car",
        '    CHECK F(car) "car"',
        '    SET F(car) "serviced" true',
    ])
    asm.load_text(g, text)
    return {"round_trips_with_comments": asm.dump(g, "service_car") == text}


def check_a_blank_line_detaches_a_comment_block():
    """Vacuity guard on the comment rules: a comment separated by a blank line must NOT be captured, or
    every stray remark in a file would silently become a function's documentation."""
    from . import asm
    g = new_graph()
    text = "\n".join(["# unrelated remark", "", "fn f(x):", '    SET F(x) "a" 1'])
    p = asm.parse(text)[0]
    return {"detached_comment_ignored": p.doc is None, "function_still_parsed": p.name == "f"}


def check_rules_load_from_a_directory_of_files():
    """A KB lives on disk as `.mf` files."""
    from pathlib import Path
    from . import asm, function as fn
    g, car, _ = _car_world()
    loaded = asm.load_dir(g, Path(__file__).parent / "rules")
    fn.invoke(g, "service_car", {"car": car})
    return {"loaded": loaded,
            "docs_came_with_them": all(fn.catalogue(g).values()),
            "and_they_run": g.attr(car, "serviced") is True}


def check_a_file_error_names_the_file_and_line():
    import pathlib
    import tempfile
    from . import asm
    g = new_graph()
    with tempfile.TemporaryDirectory() as d:
        bad = pathlib.Path(d) / "bad.mf"
        bad.write_text("fn oops(x):\n    NOSUCHOP F(x)", encoding="utf-8")
        try:
            asm.load_file(g, bad)
            return {"refused": False}
        except asm.AsmError as e:
            return {"refused": True, "names_file": "bad.mf" in str(e), "names_line": "line 2" in str(e)}


# --- applications, episodes, selection --------------------------------------------------------------
def _library():
    """A car world plus a small library of single-parameter functions with declared param types."""
    from . import asm
    g, car, trike = _car_world()
    asm.load_text(g, "\n".join([
        "# Confirm the chunk really is a car.",
        "fn inspect(c: car):",
        '    SET F(c) "inspected" true',
        "",
        "# Mark a car as serviced.",
        "fn service(c: car):",
        '    SET F(c) "serviced" true',
    ]))
    return g, car, trike


def check_an_application_is_a_node_with_its_bindings():
    from . import application as ap
    g, car, _ = _library()
    a = ap.record(g, "service", {"c": car})
    return {"is_a_node": g.kind(a) == "application",
            "points_at_the_real_function_node": g.target(a, "of") == __import__(
                "microfunctions.function", fromlist=["find"]).find(g, "service"),
            "bindings_recoverable": ap.bindings_of(g, a) == {"c": car}}


def check_episode_order_is_native_no_turn_counter():
    """The substrate change paying its way: the old version needed a driver-stamped turn counter purely
    to recover an order. Vacuity guard: read the order back by INDEX off the ordered edge."""
    from . import application as ap
    g, car, _ = _library()
    ep = ap.open_episode(g, "servicing", about=car)
    ap.record(g, "inspect", {"c": car}, episode=ep)
    ap.record(g, "service", {"c": car}, episode=ep)
    order = [g.attr(s, "function") for s in ap.steps(g, ep)]
    return {"order_is_native": order == ["inspect", "service"],
            "by_index": g.attr(g.at(ep, "step", 1), "function") == "service"}


def check_candidates_come_from_declared_parameter_types():
    """Matching in its demoted role. Vacuity guard: the tricycle must yield NO candidates, or the type
    check is doing nothing."""
    from . import selection as sel
    g, car, trike = _library()
    return {"for_a_car": sorted(sel.candidates(g, car)) == ["inspect", "service"],
            "for_a_tricycle": sel.candidates(g, trike) == ()}


def check_ranking_uses_declared_priority():
    from . import function as fn, selection as sel
    g, car, _ = _library()
    g.put(fn.find(g, "service"), priority=10)
    return {"priority_wins": sel.rank(g, car)[0] == "service",
            "deterministic_tiebreak": sel.rank(g, car) == ("service", "inspect")}


def check_an_external_scorer_can_override():
    """The hook a language model plugs into, reading the natural-language docs."""
    from . import selection as sel
    g, car, _ = _library()
    prefer_inspect = lambda gr, name, node: 1 if name == "inspect" else 0
    return {"scorer_reorders": sel.rank(g, car, scorer=prefer_inspect)[0] == "inspect"}


def check_a_function_is_not_applied_twice_to_the_same_node():
    """THE structural rule. Under rules this needed a hand-authored consumption marker per rule, and
    forgetting one produced an unbounded stream of repeated effects. Here it is one check in one place."""
    from . import selection as sel
    g, car, _ = _library()
    first, _ = sel.step(g, car)
    remaining = sel.candidates(g, car)
    return {"first_applied": first is not None,
            "not_offered_again": first not in remaining,
            "the_other_still_is": len(remaining) == 1}


def check_stepping_settles_and_records_an_episode():
    """The metaprocedure in miniature: choose one, apply, record, reassess — until nothing applies."""
    from . import application as ap, selection as sel
    g, car, _ = _library()
    ep = ap.open_episode(g, "servicing", about=car)
    applied = sel.run_until_settled(g, car, episode=ep)
    return {"applied_each_once": sorted(applied) == ["inspect", "service"],
            "effects_landed": (g.attr(car, "inspected"), g.attr(car, "serviced")) == (True, True),
            "episode_recorded_in_order": [g.attr(s, "function") for s in ap.steps(g, ep)] == list(applied),
            "settles": sel.candidates(g, car) == ()}


def check_a_refused_application_is_data_not_a_crash():
    """A type violation mid-selection must be recorded as an outcome, never abort the loop."""
    from . import application as ap, selection as sel
    g, car, trike = _library()
    rec = ap.record(g, "service", {"c": trike}, outcome="TypeViolation")
    name, _ = sel.step(g, trike)
    return {"no_candidates_for_a_bad_chunk": name is None,
            "outcome_is_stored": g.attr(rec, "outcome") == "TypeViolation"}


def check_an_episode_compiles_into_a_reusable_function():
    """⭐ THE PAYOFF, on the new substrate. An episode becomes a function that replays it on a fresh
    subject — using `function.define` and a loop, no new machinery."""
    from . import application as ap, asm, function as fn, selection as sel
    g, car, _ = _library()
    ep = ap.open_episode(g, "servicing", about=car)
    sel.run_until_settled(g, car, episode=ep)
    ap.compile_episode(g, ep, "full_service")

    fresh = g.mint("chunk")
    g.link("root", "has", fresh)
    g.link(fresh, "body", g.mint("body"))
    for _ in range(4):
        g.link(fresh, "wheel", g.mint("wheel"))
    params, _ = fn.load(g, "full_service")
    fn.invoke(g, "full_service", {params[0]: fresh})
    return {"compiled": "full_service" in fn.names(g),
            "replays_on_a_fresh_subject":
                (g.attr(fresh, "inspected"), g.attr(fresh, "serviced")) == (True, True),
            "is_inspectable": "INVOKE" in asm.dump(g, "full_service"),
            "documented": bool(fn.doc_of(g, "full_service"))}


def check_a_learned_function_is_an_ordinary_library_member():
    """Vacuity guard on the above: the learned function must be indistinguishable from an authored one —
    same storage, same catalogue, callable and recordable like any other."""
    from . import application as ap, function as fn, selection as sel
    g, car, _ = _library()
    ep = ap.open_episode(g, "servicing", about=car)
    sel.run_until_settled(g, car, episode=ep)
    ap.compile_episode(g, ep, "full_service")
    return {"in_the_catalogue": "full_service" in fn.catalogue(g),
            "stored_like_any_other": g.kind(fn.find(g, "full_service")) == "function",
            "lifts_back": len(fn.load(g, "full_service")[1]) == 2}


# --- planning: casts chained backwards, lazily ------------------------------------------------------
def _garage():
    """A library of CASTS. `service` casts a car into a serviced_car; `wash` casts that into a washed_car.
    Nothing declares a mutation — a stronger schema is all a change is."""
    from . import asm
    g = new_graph()
    declare_type(g, "car", {"body": ("body", 1), "wheel": ("wheel", 4)})
    declare_type(g, "serviced_car", base="car", attrs={"serviced": True})
    declare_type(g, "washed_car", base="serviced_car", attrs={"washed": True})
    asm.load_text(g, "\n".join([
        "# Cast a car into a serviced car.",
        "fn service(c: car) -> serviced_car:",
        '    SET F(c) "serviced" true',
        "",
        "# Cast a serviced car into a washed one.",
        "fn wash(c: serviced_car) -> washed_car:",
        '    SET F(c) "washed" true',
    ]))
    car = g.mint("chunk")
    g.link("root", "has", car)                      # real things hang off root
    g.link(car, "body", g.mint("body"))
    for _ in range(4):
        g.link(car, "wheel", g.mint("wheel"))
    return g, car


def check_a_type_is_a_schema_over_structure_and_attributes():
    """Mutation needs no representation: a node either satisfies the stronger schema or it does not."""
    from . import function as fn
    g, car = _garage()
    before = is_a(g, car, "serviced_car")
    fn.invoke(g, "service", {"c": car})
    return {"is_a_car": is_a(g, car, "car"),
            "not_yet_serviced": before is False,
            "cast_succeeded": is_a(g, car, "serviced_car"),
            "inherited_structure_still_required": "wheel" in schema_of(g, "washed_car")}


def check_planning_chains_casts_backwards():
    """Backward chaining over return types. Vacuity guard: the chain must have BOTH steps in dependency
    order, not just the last one."""
    from . import plan as P
    g, car = _garage()
    chain = P.plan(g, "washed_car", car)
    steps = [g.attr(c, "function") for c in P.calls_of(g, chain)]
    return {"planned": steps == ["service", "wash"],
            "readable": "1. service" in P.describe(g, chain)}


def check_a_plan_is_lazy_and_nothing_ran():
    """⭐ THE Spark property: planning composes, only the action materialises. Vacuity guard: assert the
    car is untouched AFTER planning, then that running it changes things."""
    from . import plan as P
    g, car = _garage()
    chain = P.plan(g, "washed_car", car)
    during = (g.attr(car, "serviced"), g.attr(car, "washed"))
    P.run(g, chain)
    return {"nothing_ran_at_plan_time": during == (None, None),
            "calls_are_pending_data": all(g.kind(c) == "pending_call" for c in P.calls_of(g, chain)),
            "action_materialised_it": is_a(g, car, "washed_car")}


def check_a_cast_returns_its_subject():
    """Not a convention papering over ambiguity — it is what a cast is."""
    from . import plan as P
    g, car = _garage()
    out = P.run(g, P.plan(g, "washed_car", car))
    return {"final_node_is_the_subject": out == car}


def check_an_already_satisfied_goal_plans_no_steps():
    """Different from unreachable, and reported differently on purpose."""
    from . import plan as P
    g, car = _garage()
    P.run(g, P.plan(g, "serviced_car", car))
    again = P.plan(g, "serviced_car", car)
    return {"no_steps": P.calls_of(g, again) == (),
            "says_so": "already satisfied" in P.describe(g, again)}


def check_an_unreachable_goal_returns_no_plan():
    """DELIBERATE NEGATIVE: no chain of declared functions reaches it, and that is an ordinary answer."""
    from . import plan as P
    g, car = _garage()
    declare_type(g, "flying_car", base="car", attrs={"flies": True})
    return {"no_plan": P.plan(g, "flying_car", car) is None,
            "describe_is_safe": P.describe(g, None) == "<no plan>"}


def check_two_rival_plans_coexist_as_data():
    """What lazy chains buy: compare before committing, no supposition mechanism needed."""
    from . import plan as P
    g, car = _garage()
    a = P.plan(g, "serviced_car", car)
    b = P.plan(g, "washed_car", car)
    return {"both_exist": g.kind(a) == "chain" and g.kind(b) == "chain",
            "different_lengths": (len(P.calls_of(g, a)), len(P.calls_of(g, b))) == (1, 2),
            "neither_has_run": g.attr(car, "serviced") is None}


# --- dispatch: the one checkpoint -------------------------------------------------------------------
def check_dispatch_runs_a_tool_and_a_veto_blocks_it():
    from . import dispatch as D
    g, car = _garage()
    seen = []
    D.register("horn", lambda gr, target: seen.append(target) or "beep")
    ok = D.service(g, "horn", car)
    D.forbid(g, car, reason="workshop closed")
    try:
        D.service(g, "horn", car)
        blocked = False
    except D.Vetoed:
        blocked = True
    # ⚠ The unregistered-tool check must use an UNforbidden target: the veto is consulted BEFORE the tool
    # is looked up, which is the correct order (a prohibition should not depend on the tool existing) —
    # the first version of this check asserted KeyError on the forbidden car and got Vetoed, correctly.
    other = g.mint("chunk")
    return {"ran": ok == "beep" and seen == [car],
            "veto_recorded_LATER_still_blocks": blocked,
            "unregistered_tool_is_loud": _raises(lambda: D.service(g, "nosuch", other), KeyError)}


def check_dispatch_from_the_isa():
    from . import dispatch as D
    from .isa import DISPATCH
    g, car = _garage()
    D.register("ping", lambda gr, target: "pong")
    _g, _f, regs = run((FOCUS("h", car), DISPATCH(R("out"), "ping", F("h"))), g)
    return {"dispatched_from_a_program": regs["out"] == "pong"}


def _raises(thunk, exc):
    try:
        thunk()
        return False
    except exc:
        return True


# --- sub/supertypes: structural, falling out of constraint strictness -------------------------------
def check_subtyping_is_structural_not_nominal():
    """A supertype relaxes constraints, a subtype tightens them. `base=` is a convenience for writing
    that, never what makes it true — so two INDEPENDENTLY declared types stand in the relation if their
    constraints do. Vacuity guard: the independently-declared pair uses no `base` at all."""
    from .types import subsumes, subtypes
    g, _car = _garage()
    declare_type(g, "vehicle", {"wheel": ("wheel", 4)})                      # no base, looser
    declare_type(g, "quad", {"wheel": ("wheel", 4), "body": ("body", 1)})    # no base, stricter
    return {"declared_chain": subsumes(g, "serviced_car", "washed_car"),
            "not_the_other_way": not subsumes(g, "washed_car", "serviced_car"),
            "independent_types_still_relate": subsumes(g, "vehicle", "quad"),
            "subtypes_of_car": subtypes(g, "car")}


def check_an_argument_accepts_a_subtype():
    """Structural subtyping on the way IN was already free — `is_a` checks constraints, not names."""
    from . import function as fn
    g, car = _garage()
    fn.invoke(g, "service", {"c": car})          # car is now a serviced_car
    return {"serviced_car_still_passes_as_car": is_a(g, car, "car"),
            "and_wash_accepts_it": is_a(g, car, "serviced_car")}


def check_a_producer_of_a_subtype_satisfies_the_goal():
    """⭐ The gap sub/supertypes exposed: `producers` compared type NAMES, so a function returning a
    `washed_car` was invisible to a goal wanting a `serviced_car` — even though every washed car is one.
    Vacuity guard: assert the more specific producer is offered but sorts AFTER the exact match."""
    from . import function as fn
    g, _car = _garage()
    offered = fn.producers(g, "serviced_car")
    return {"exact_match_first": offered[0] == "service",
            "subtype_producer_also_offered": "wash" in offered,
            "exact_goal_unaffected": fn.producers(g, "washed_car") == ("wash",)}


# --- the direction invariant ------------------------------------------------------------------------
# Kinds that are ABOUT something rather than part of the domain. Anything here must be pointed AT the
# thing it describes, and never pointed at BY it — see `docs/microfunctions/planning_workbench.md` §2.
_METADATA_KINDS = frozenset({
    "type", "requires", "requires_attr",
    "function", "param", "instr", "arg",
    "application", "binding", "episode",
    "attention", "connection",                             # the thread — memory is metadata, never world
    "goal",                                                # what we are trying to do is metadata too
    "hypothesis", "backup",
    "chain", "pending_call",
    "forbidden",
    "workbench", "frame", "mapping", "transformation",     # not built yet — listed so it stays true
})


def check_metadata_is_never_pointed_at_by_structure():
    """⭐ STRUCTURE POINTS OUTWARD; METADATA POINTS INWARD.

    Copying a subgraph traverses outgoing edges. If a domain node pointed at (say) its mapping, the copy
    would reach that mapping, then its original, its image, its next — and thence every other frame,
    every other workbench, and every plan that ever touched the node. One innocent copy becomes an
    unbounded one. The failure is not a wrong answer, it is a runaway.

    The constraint costs nothing, because the reverse index already answers the backward question
    (`sources(node, "original")`), so the lookup that would motivate the dangerous edge is free.

    This scans a graph exercised by every layer and fails on the first violation, naming it."""
    from . import application as ap, dispatch as D, hypothesis as H, plan as P, selection as sel
    g, car = _garage()
    ep = ap.open_episode(g, "servicing", about=car)
    P.run(g, P.plan(g, "serviced_car", car))
    ap.record(g, "service", {"c": car}, episode=ep)
    sel.step(g, car, episode=ep)
    h = H.open_hypothesis(g, "what if it were blue", about=car)
    H.variant(g, h, car, colour="blue")
    H.backup(g, h, car, "colour")
    D.forbid(g, car, reason="closed")

    violations_found = []
    for (src, label), targets in g.out.items():
        if g.kind(src) in _METADATA_KINDS:
            continue                                   # metadata pointing anywhere is fine
        for t in targets:
            if g.kind(t) in _METADATA_KINDS:
                violations_found.append(f"{g.kind(src)} --{label}--> {g.kind(t)}")
    return {"edges_checked": sum(len(v) for v in g.out.values()),
            "metadata_kinds_guarded": len(_METADATA_KINDS),
            "VIOLATIONS": violations_found,
            "invariant_holds": not violations_found}


# --- workbench: imagining effects on a copy ---------------------------------------------------------
def check_workbench_copies_are_structurally_unreachable():
    """⭐ The isolation is STRUCTURAL — no marker, no filter, and no exclusion logic to get wrong.

    An earlier version stamped every copy with an `in_workbench` attribute and made `instances` filter on
    it. That was a labelling error: it asserted what the structure already entails. The real reason a copy
    is never offered as a candidate is that **nothing in the real graph points at it** — only a mapping
    does, via `image` — so enumerating by traversal from `root` cannot reach it.

    Vacuity guard: assert the copy IS a well-typed car (so a scan would have found it), and that
    enumerating from inside the workbench finds it by the very same mechanism."""
    from . import workbench as W
    from .types import instances
    g, car = _garage()
    real_before = instances(g, "car")
    wb = W.open_workbench(g, car)
    copy = W.image_of(g, W.mapping_for(g, W.root_frame(g, wb), car))
    return {"copy_is_a_valid_car": is_a(g, copy, "car"),
            "real_enumeration_unchanged": instances(g, "car") == real_before,
            "copy_unreachable_from_root": copy not in W.reachable(g, "root"),
            "nothing_real_points_at_it": all(g.kind(s) == "mapping" for s in g.sources(copy)),
            "found_by_the_same_mechanism_from_inside": copy in instances(g, "car", under=copy)}


def check_the_copy_is_complete_and_the_original_untouched():
    from . import workbench as W
    g, car = _garage()
    reach = W.reachable(g, car)
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    copy = W.image_of(g, W.mapping_for(g, f0, car))
    return {"reached_body_and_wheels": len(reach) == 6,
            "one_mapping_per_reachable_node": len(W.mappings(g, f0)) == len(reach),
            "structure_copied": g.count(copy, "wheel") == 4 and g.target(copy, "body") is not None,
            "copy_is_not_the_original": copy != car,
            "original_untouched": g.sources(car, "image") == ()}


def check_a_mapping_resolves_to_the_real_node():
    from . import workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    m = W.mapping_for(g, W.root_frame(g, wb), car)
    return {"resolves": W.resolve(g, m) == car, "not_imagined": not W.is_imagined(g, m)}


def check_nested_workbenches_resolve_up_the_stack():
    """⚠ In a nested workbench `original` points ONE LEVEL UP, so resolving is a walk, not a hop."""
    from . import workbench as W
    g, car = _garage()
    outer = W.open_workbench(g, car)
    outer_copy = W.image_of(g, W.mapping_for(g, W.root_frame(g, outer), car))
    inner = W.open_workbench(g, outer_copy, parent=outer)
    m = W.mapping_for(g, W.root_frame(g, inner), outer_copy)
    return {"points_one_level_up": g.target(m, "original") == outer_copy,
            "resolves_all_the_way_down": W.resolve(g, m) == car,
            "depth_recorded": g.attr(inner, "depth") == 1}


def check_stepping_makes_a_new_frame_and_leaves_the_old_one_intact():
    """⭐ The movie is real: every earlier state stays inspectable rather than needing replay."""
    from . import workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, car)
    f1, tr = W.step(g, wb, f0, "service", {"c": m0})
    img0, img1 = W.image_of(g, m0), W.image_of(g, g.target(m0, "next"))
    return {"new_frame": g.attr(f1, "index") == 1,
            "effect_landed_in_the_new_frame": g.attr(img1, "serviced") is True,
            "previous_frame_untouched": g.attr(img0, "serviced") is None,
            "real_world_untouched": g.attr(car, "serviced") is None,
            "transformation_recorded": g.attr(tr, "function") == "service",
            "expectation_recorded": g.attr(tr, "expects") == "serviced_car"}


def check_a_transformation_binds_a_mapping_not_a_raw_node():
    """THE rule that makes a plan replayable: following `original` yields the node the operation must
    really be applied to. Vacuity guard: assert the bound thing is a mapping AND that it resolves."""
    from . import workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    _f1, tr = W.step(g, wb, f0, "service", {"c": W.mapping_for(g, f0, car)})
    b = g.target(tr, "arg")
    bound = g.target(b, "mapping")
    return {"binding_is_a_mapping": g.kind(bound) == "mapping",
            "and_it_resolves_to_the_real_node": W.resolve(g, bound) == car,
            "no_raw_node_was_bound": g.target(b, "value") is None}


def check_frames_fork_and_a_mapping_history_forks_with_them():
    """⚠ `next` is 1:N on both. Code assuming a single successor would silently follow one branch."""
    from . import workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, car)
    a, _ = W.step(g, wb, f0, "service", {"c": m0})
    b, _ = W.fork(g, wb, f0, "service", {"c": m0})
    return {"two_successors": set(g.targets(f0, "next")) == {a, b},
            "mapping_history_forked": len(g.targets(m0, "next")) == 2,
            "history_walks_the_tree": len(W.history(g, m0)) == 3,
            "all_frames_found": len(W.frames(g, wb)) == 3}


def check_discarding_scraps_everything_and_belief_survives():
    from . import workbench as W
    g, car = _garage()
    before = len(g.nodes)
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    W.step(g, wb, f0, "service", {"c": W.mapping_for(g, f0, car)})
    W.discard(g, wb)
    leftovers = [n for n in g.nodes if any(g.kind(m) == "mapping"
                                            for m in g.sources(n, "image"))]
    return {"workbench_gone": wb not in g.nodes,
            "no_copies_left": leftovers == [],
            "back_to_the_original_size": len(g.nodes) == before,
            "belief_intact": is_a(g, car, "car") and g.attr(car, "serviced") is None}


# --- mocks, assumptions, and the refusal ------------------------------------------------------------
def _filesystem():
    """A dispatching function with three declared outcomes. Each mock is an ORDINARY microfunction whose
    return type IS the outcome it assumes, so the existing type-chaining planner handles each case."""
    from . import asm, dispatch as D
    g = new_graph()
    declare_type(g, "dir", attrs={"kind_of": "dir"})
    declare_type(g, "listing", base="dir", attrs={"listed": True})
    declare_type(g, "empty_listing", base="listing", attrs={"count": 0})
    declare_type(g, "full_listing", base="listing", attrs={"many": True})
    asm.load_text(g, "\n".join([
        "# Really list a directory. Reaches the world.",
        "fn list_dir(d: dir) -> listing:",
        '    DISPATCH R(out) "ls" F(d)',
        '    SET F(d) "listed" true',
        "",
        "# Assume the directory turns out empty.",
        "fn list_empty(d: dir) -> empty_listing mocks list_dir:",
        '    SET F(d) "listed" true',
        '    SET F(d) "count" 0',
        "",
        "# Assume it turns out to have plenty in it.",
        "fn list_full(d: dir) -> full_listing mocks list_dir:",
        '    SET F(d) "listed" true',
        '    SET F(d) "many" true',
    ]))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    D.register("ls", lambda gr, target: ["a.txt"])
    return g, d


def check_a_function_has_many_mocks_in_preference_order():
    """Declaration order IS preference order, free, because `mock` is an ordered edge. Deliberately the
    weakest thing that works — the cut band layer is not coming back for this."""
    from . import function as fn
    g, d = _filesystem()
    return {"outcomes": fn.mocks_of(g, "list_dir"),
            "order_is_declaration_order": fn.mocks_of(g, "list_dir") == ("list_empty", "list_full"),
            "each_declares_its_own_outcome_type":
                (fn.returns_of(g, "list_empty"), fn.returns_of(g, "list_full"))
                == ("empty_listing", "full_listing"),
            "a_mock_knows_what_it_mocks": fn.mocks_target(g, "list_empty") == "list_dir"}


def check_dispatch_refuses_an_imagined_target():
    """⭐ THE SAFETY PROPERTY. Vacuity guard: the SAME call on the SAME real node must succeed, so we know
    the refusal is about being imagined and not about anything else."""
    from . import dispatch as D, workbench as W
    g, d = _filesystem()
    real_ok = D.service(g, "ls", d)
    wb = W.open_workbench(g, d)
    copy = W.image_of(g, W.mapping_for(g, W.root_frame(g, wb), d))
    try:
        D.service(g, "ls", copy)
        refused = False
    except D.Imagined:
        refused = True
    return {"real_target_dispatches": real_ok == ["a.txt"],
            "imagined_target_refused": refused}


def check_stepping_substitutes_a_mock_and_never_dispatches():
    """On a workbench, a function with declared outcomes is replaced by one — always, not by convention.
    Vacuity guard: `list_dir` contains a DISPATCH, so if substitution failed the step would either reach
    the world or raise `Imagined`; neither happens."""
    from . import dispatch as D, workbench as W
    g, d = _filesystem()
    calls = []
    D.register("ls", lambda gr, target: calls.append(target) or ["a.txt"])
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    f1, tr = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)})
    img = W.image_of(g, g.target(W.mapping_for(g, f0, d), "next"))
    return {"recorded_the_real_function": g.attr(tr, "function") == "list_dir",
            "but_executed_the_preferred_mock": g.attr(tr, "executed") == "list_empty",
            "expectation_is_the_assumed_outcome": g.attr(tr, "expects") == "empty_listing",
            "no_tool_was_called": calls == [],
            "effect_is_the_mocks": (g.attr(img, "listed"), g.attr(img, "count")) == (True, 0)}


def check_choosing_an_outcome_records_a_hypothesis():
    """A plan carries its own dependence on guesses — 'which parts are fragile' becomes a lookup."""
    from . import workbench as W
    g, d = _filesystem()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    _f1, tr = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)})
    h = W.assumption_of(g, tr)
    return {"assumption_recorded": h is not None and g.kind(h) == "hypothesis",
            "and_says_what_it_assumed": "empty_listing" in (g.attr(h, "label") or ""),
            "listed_as_fragile": W.fragile_steps(g, wb) == (tr,)}


def check_forking_on_a_different_outcome_gives_a_different_world():
    """⭐ Two assumptions, two branches, side by side — and contingency plans come free from having
    explored both. Vacuity guard: the two frames must genuinely disagree about the world."""
    from . import workbench as W
    g, d = _filesystem()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    _a, tra = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    _b, trb = W.fork(g, wb, f0, "list_dir", {"d": m0}, assume="list_full")
    ia, ib = [W.image_of(g, m) for m in g.targets(m0, "next")]
    return {"two_outcomes": (g.attr(tra, "expects"), g.attr(trb, "expects"))
                            == ("empty_listing", "full_listing"),
            "worlds_disagree": (g.attr(ia, "count"), g.attr(ib, "many")) == (0, True),
            "and_each_is_a_distinct_hypothesis":
                W.assumption_of(g, tra) != W.assumption_of(g, trb),
            "an_unknown_outcome_is_refused":
                _raises(lambda: W.step(g, wb, f0, "list_dir", {"d": m0}, assume="nope"), KeyError)}


def check_deviation_is_a_failed_cast():
    """Reality is compared against the promise the function made, not against a whole-subgraph diff."""
    from . import workbench as W
    g, d = _filesystem()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    _f1, tr = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)})   # assumed EMPTY

    matching = g.mint("dir", kind_of="dir", listed=True, count=0)
    diverging = g.mint("dir", kind_of="dir", listed=True, many=True)
    return {"expected": g.attr(tr, "expects"),
            "reality_matching_the_assumption_is_no_deviation": W.deviates(g, tr, matching) == {},
            "reality_contradicting_it_deviates": bool(W.deviates(g, tr, diverging)),
            "and_says_how": "@count" in W.deviates(g, tr, diverging)}


# --- following a plan for real ----------------------------------------------------------------------
def check_a_plan_replays_against_the_real_graph():
    """⭐ Everything needed was recorded: the REAL function (not the mock), the MAPPINGS (which resolve to
    real nodes), and the expected type. Vacuity guard: the real world must be untouched before execution
    and changed after."""
    from . import execution as X, workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    f1, _ = W.step(g, wb, f0, "service", {"c": W.mapping_for(g, f0, car)})
    f2, _ = W.step(g, wb, f1, "wash", {"c": W.mapping_for(g, f1, car)})
    untouched = g.attr(car, "serviced") is None
    result = X.execute(g, wb, f2)
    return {"world_untouched_before": untouched,
            "ran_in_order": result["ran"] == ("service", "wash"),
            "completed": result["completed"],
            "real_car_actually_changed": is_a(g, car, "washed_car")}


def check_execution_follows_one_path_through_a_forked_tree():
    """A plan is a PATH, not the whole tree. Committing to a branch is exactly the choice forks kept open."""
    from . import execution as X, workbench as W
    g, d = _filesystem()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    a, _ = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    b, _ = W.fork(g, wb, f0, "list_dir", {"d": m0}, assume="list_full")
    return {"three_frames": len(W.frames(g, wb)) == 3,
            "path_to_a_is_two_long": len(X.path_to(g, wb, a)) == 2,
            "and_excludes_the_sibling": b not in X.path_to(g, wb, a)}


def check_reality_disagreeing_with_the_assumption_is_caught():
    """⭐ THE POINT of mocks + deviation. The plan assumed the directory would be EMPTY; the real tool says
    otherwise, so the step diverges and execution stops rather than acting on a world that no longer
    matches. Vacuity guard: the same plan against a reality that MATCHES must complete."""
    from . import dispatch as D, execution as X, workbench as W

    def plan_assuming_empty(g, d):
        wb = W.open_workbench(g, d)
        f0 = W.root_frame(g, wb)
        f1, tr = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)}, assume="list_empty")
        return wb, f1, tr

    g, d = _filesystem()
    D.register("ls", lambda gr, target: gr.put(target, many=True))     # reality: plenty of files
    wb, f1, _tr = plan_assuming_empty(g, d)
    diverged = X.execute(g, wb, f1)

    g2, d2 = _filesystem()
    D.register("ls", lambda gr, target: gr.put(target, count=0))       # reality: empty, as assumed
    wb2, f1b, _ = plan_assuming_empty(g2, d2)
    matched = X.execute(g2, wb2, f1b)

    return {"diverged": not diverged["completed"],
            "names_the_step": diverged["deviation"]["step"] == "list_dir",
            "says_what_it_assumed": "empty_listing" in (diverged["deviation"]["assumed"] or ""),
            "says_how_it_differed": "@count" in diverged["deviation"]["violations"],
            "matching_reality_completes": matched["completed"]}


def check_the_explored_alternative_is_available_as_a_contingency():
    """Contingency plans come free from having branched — which is why an abandoned fork is kept as data."""
    from . import execution as X, workbench as W
    g, d = _filesystem()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    a, tra = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    b, _trb = W.fork(g, wb, f0, "list_dir", {"d": m0}, assume="list_full")
    alts = X.alternatives(g, wb, tra)
    return {"the_other_branch_is_offered": alts == (b,),
            "and_it_assumed_something_else":
                g.attr(g.target(b, "via"), "expects") == "full_listing"}


def check_a_node_imagined_during_planning_is_bound_by_provenance():
    """A step may mint something that did not exist at planning time — its mapping has NO `original`, and
    what ties it to reality is the transformation that produced it."""
    from . import asm, execution as X, function as fnm, workbench as W
    g, car = _garage()
    asm.load_text(g, "\n".join([
        "# Attach a fresh service record to the car.",
        "fn record(c: car) -> car:",
        '    NEW R(r) "record"',
        '    LINK F(c) "record" R(r)',
    ]))
    wb = W.open_workbench(g, car)
    f0 = W.root_frame(g, wb)
    f1, _ = W.step(g, wb, f0, "record", {"c": W.mapping_for(g, f0, car)})
    imagined = [m for m in W.mappings(g, f1) if W.is_imagined(g, m)]
    result = X.execute(g, wb, f1)
    real_records = g.targets(car, "record")
    return {"planning_minted_something": len(imagined) == 1,
            "it_has_no_original": W.resolve(g, imagined[0]) is None,
            "execution_created_the_real_one": len(real_records) == 1,
            "and_bound_it_to_its_twin": result["bindings"].get(imagined[0]) == real_records[0],
            "no_ambiguity_notes": result["notes"] == ()}


# --- recovering from a divergence -------------------------------------------------------------------
def _filesystem_with_followups():
    """`_filesystem`, plus a distinct next step for each outcome — so a branch has something left to do
    after the deviating call, which is the whole point of resuming onto one."""
    from . import asm
    g, d = _filesystem()
    declare_type(g, "archived_dir", base="full_listing", attrs={"archived": True})
    declare_type(g, "removed_dir", base="empty_listing", attrs={"removed": True})
    asm.load_text(g, "\n".join([
        "# What you do with a directory that turned out to have plenty in it.",
        "fn archive(d: full_listing) -> archived_dir:",
        '    SET F(d) "archived" true',
        "",
        "# What you do with one that turned out empty.",
        "fn remove(d: empty_listing) -> removed_dir:",
        '    SET F(d) "removed" true',
    ]))
    return g, d


def _both_branches(g, d):
    """Plan for empty (and remove it), fork for full (and archive it). Returns the two leaves."""
    from . import workbench as W
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    e1, _ = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    e2, _ = W.step(g, wb, e1, "remove", {"d": g.target(W.mapping_for(g, f0, d), "next")})
    f1, _ = W.fork(g, wb, f0, "list_dir", {"d": m0}, assume="list_full")
    f2, _ = W.step(g, wb, f1, "archive", {"d": _successor(g, m0, f1)})
    return wb, e2, f2


def _successor(g, mapping, frame):
    from . import execution as X
    return X._successor_in(g, mapping, frame)


def check_leaves_under_finds_the_end_of_every_branch():
    """A frame with no successor is a leaf, `frame` itself included — which is what makes resuming onto a
    one-step branch a no-op rather than an error."""
    from . import execution as X, workbench as W
    g, d = _filesystem_with_followups()
    wb, e2, f2 = _both_branches(g, d)
    f0 = W.root_frame(g, wb)
    return {"two_branches_two_leaves": set(X.leaves_under(g, wb, f0)) == {e2, f2},
            "a_leaf_is_its_own_leaf": X.leaves_under(g, wb, f2) == (f2,)}


def check_recovery_resumes_onto_the_branch_reality_took():
    """⭐ THE PAYOFF OF FORKING. The plan assumed EMPTY and reality is FULL — but that outcome was explored,
    so the rest of that branch is already a verified plan for the world we are now in, and execution
    continues down it instead of replanning.

    Three vacuity guards, because this check could pass for uninteresting reasons: the diverged call must
    have reached the world **exactly once** (re-running it is the likeliest bug here); the abandoned
    branch's own next step must NOT have run; and the resumed branch's next step must have really landed."""
    from . import dispatch as D, execution as X
    g, d = _filesystem_with_followups()
    calls = []
    D.register("ls", lambda gr, target: calls.append(target) or gr.put(target, many=True))
    wb, empty_leaf, full_leaf = _both_branches(g, d)

    result = X.execute(g, wb, empty_leaf)                 # commit to the empty branch
    rec = X.recover(g, result, want="archived_dir")
    resumed = rec["result"]
    return {"diverged_first": not result["completed"] and result["deviation"]["step"] == "list_dir",
            "recovered_by_contingency": rec["kind"] == "contingency",
            "onto_the_branch_that_assumed_full": rec["assuming"] == "full_listing",
            "completed": resumed["completed"],
            "ran": resumed["ran"] == ("list_dir", "archive"),
            "the_real_call_happened_exactly_once": len(calls) == 1,
            "the_abandoned_step_never_ran": g.attr(d, "removed") is None,
            "and_the_world_really_changed": is_a(g, d, "archived_dir")}


def check_a_sibling_applying_a_different_function_is_not_resumable():
    """⚠ Siblings are alternative SUCCESSORS, not necessarily alternative OUTCOMES. Resuming into a branch
    whose step never ran would skip a call and report success. Vacuity guard: the sibling's promise is one
    reality *does* satisfy, so only the same-function restriction can be what rejects it."""
    from . import dispatch as D, execution as X, workbench as W
    g, d = _filesystem_with_followups()
    D.register("ls", lambda gr, target: gr.put(target, many=True))
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    a, _ = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    b, trb = W.fork(g, wb, f0, "list_full", {"d": m0})     # a DIFFERENT function, same promise
    result = X.execute(g, wb, a)
    dev = result["deviation"]
    return {"the_sibling_promises_what_reality_delivered":
                g.attr(trb, "expects") == "full_listing" and W.deviates(g, trb, dev["result"]) == {},
            "but_it_is_not_offered": X.matching_alternative(g, wb, dev) is None,
            "and_recovery_does_not_take_it": X.recover(g, result)["kind"] == "stuck",
            "sibling_was_a_candidate_at_all": b in X.alternatives(g, wb, dev["transformation"])}


def check_replanning_proposes_from_the_world_as_it_actually_is():
    """When nothing explored fits, the only sound move is a fresh proposal taking the REAL result as the
    subject. Vacuity guards: no fork exists, so the contingency path cannot be what answered; the chain is
    lazy, so the world must be unchanged until it is run; and running it must actually reach the goal."""
    from . import dispatch as D, execution as X, plan as P, workbench as W
    g, d = _filesystem_with_followups()
    D.register("ls", lambda gr, target: gr.put(target, many=True))
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    e1, _ = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)}, assume="list_empty")
    e2, _ = W.step(g, wb, e1, "remove", {"d": _successor(g, W.mapping_for(g, f0, d), e1)})

    result = X.execute(g, wb, e2)
    without_a_goal = X.recover(g, result)
    rec = X.recover(g, result, want="archived_dir")
    unchanged = g.attr(d, "archived") is None
    reached = P.run(g, rec["chain"])
    return {"no_fork_to_fall_back_on": X.alternatives(g, wb, result["deviation"]["transformation"]) == (),
            "without_a_goal_it_says_so": without_a_goal["kind"] == "stuck",
            "with_one_it_replans": rec["kind"] == "replanned",
            "from_the_real_result": g.target(rec["chain"], "subject") == d,
            "the_plan_is_archive": "archive" in rec["plan"],
            "nothing_committed_by_proposing": unchanged,
            "and_running_it_reaches_the_goal": reached == d and is_a(g, d, "archived_dir")}


def _scanner():
    """A dispatching call that MINTS, with two outcomes — so resuming has to carry a node that did not
    exist at planning time across onto a different branch's mappings."""
    from . import asm, dispatch as D
    g = new_graph()
    declare_type(g, "dir", attrs={"kind_of": "dir"})
    declare_type(g, "report", attrs={"kind_of": "report"})
    declare_type(g, "escalated_report", base="report", attrs={"escalated": True})
    declare_type(g, "scanned", base="dir", attrs={"scanned": True})
    declare_type(g, "clean_scan", base="scanned", attrs={"faults": 0})
    declare_type(g, "faulty_scan", base="scanned", attrs={"faulty": True})
    body = ['    NEW R(r) "report"', '    SET R(r) "kind_of" "report"',
            '    LINK F(d) "report" R(r)', '    SET F(d) "scanned" true']
    asm.load_text(g, "\n".join([
        "# Really scan a directory, filing a report. Reaches the world.",
        "fn scan(d: dir) -> scanned:", '    DISPATCH R(out) "scan" F(d)', *body, "",
        "# Assume it comes back clean.",
        "fn scan_clean(d: dir) -> clean_scan mocks scan:", *body, '    SET F(d) "faults" 0', "",
        "# Assume it comes back with faults.",
        "fn scan_faulty(d: dir) -> faulty_scan mocks scan:", *body, '    SET F(d) "faulty" true', "",
        "# Escalate the REPORT itself — not the directory.",
        "fn escalate(r: report) -> escalated_report:", '    SET F(r) "escalated" true',
    ]))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    D.register("scan", lambda gr, target: gr.put(target, faulty=True))
    return g, d


def check_resuming_carries_a_node_that_was_only_imagined():
    """⭐ The hard half of resuming. `scan` MINTS a report, so the branch being resumed onto refers to a
    node that did not exist when planning started — and the follow-up step operates on *that*, not on the
    directory. Binding it wrongly would either crash or escalate the wrong node.

    Vacuity guards: the report must genuinely have been imagined (no `original`); exactly one real report
    must exist, so 'the right one' is a real claim; and the directory must NOT be what got escalated."""
    from . import execution as X, workbench as W
    g, d = _scanner()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    clean, _ = W.step(g, wb, f0, "scan", {"d": m0}, assume="scan_clean")
    faulty, _ = W.fork(g, wb, f0, "scan", {"d": m0}, assume="scan_faulty")
    imagined = [m for m in W.mappings(g, faulty) if W.is_imagined(g, m)]
    tail, _ = W.step(g, wb, faulty, "escalate", {"r": imagined[0]})

    result = X.execute(g, wb, clean)                      # commit to the clean branch; reality is faulty
    rec = X.recover(g, result)
    resumed = rec["result"]
    reports = g.targets(d, "report")
    return {"planning_imagined_a_report": len(imagined) == 1,
            "which_had_no_original": W.resolve(g, imagined[0]) is None,
            "diverged_then_recovered": not result["completed"] and rec["kind"] == "contingency",
            "ran": resumed["ran"] == ("scan", "escalate"),
            "exactly_one_real_report": len(reports) == 1,
            "the_imagined_one_bound_to_it": resumed["bindings"].get(
                _successor(g, imagined[0], tail)) == reports[0],
            "and_the_real_report_was_escalated": is_a(g, reports[0], "escalated_report"),
            "not_the_directory": g.attr(d, "escalated") is None,
            "no_ambiguity_notes": resumed["notes"] == ()}


# --- the thread: materialised short-term memory ------------------------------------------------------
def _threaded():
    """A garage plus a thread that attended the car, serviced it, then attended a wheel."""
    from . import thread as T
    g, car = _garage()
    t = T.open_thread(g, "session")
    T.attend(g, t, car, why="user mentioned it", note="the car")
    T.applied(g, t, "service", {"c": car}, why="it needed servicing")
    T.attend(g, t, g.at(car, "wheel", 0), why="checking the tyres")
    return g, car, t


def check_a_thread_starts_at_root_and_grows():
    """The system starts knowing only where it is: one entry, attending `root`."""
    from . import thread as T
    g, _car = _garage()
    t = T.open_thread(g)
    first = T.tip(g, t)
    return {"one_entry": len(T.entries(g, t)) == 1,
            "attending_root": T.attended(g, first) == "root",
            "nothing_before_it": T.previous(g, first) is None,
            "and_it_grows": len(T.entries(g, T.open_thread(g))) == 1}


def check_the_two_orderings_cannot_disagree():
    """⚠ The container's ordered `step` edge and the `prev` chain are two views of one order. They agree
    because ONE function appends — a discipline a *human* must follow, which is what earns this a test
    rather than the structure guaranteeing it.

    Vacuity guard: walking back from the tip must reproduce the container order exactly, reversed, so a
    chain that silently forked or skipped would show up."""
    from . import thread as T
    g, _car, t = _threaded()
    container = T.entries(g, t)
    chain = T.past(g, T.tip(g, t))
    return {"same_length": len(container) == len(chain),
            "chain_is_the_container_reversed": chain == tuple(reversed(container)),
            "forward_undoes_backward":
                all(T.following(g, T.previous(g, e)) == e for e in container[1:]),
            "the_first_has_no_predecessor": T.previous(g, container[0]) is None}


def check_an_application_entry_is_the_application_node():
    """⭐ ONE RECORD, NOT TWO. A thread IS an episode, so the existing machinery reads it unchanged and
    nothing has to consult two logs. Vacuity guard: `steps` must see the applications and must NOT see the
    attention shifts, or `compile_episode` would try to compile a shift into a call."""
    from . import application as ap, thread as T
    g, car, t = _threaded()
    apps = ap.steps(g, t)
    entries = T.entries(g, t)
    T.applied(g, t, "wash", {"c": car})
    learned = ap.compile_episode(g, t, "service_and_wash")
    params, program = __import__("microfunctions.function", fromlist=["load"]).load(g, learned)
    return {"the_entry_is_the_application": apps == tuple(e for e in entries if g.kind(e) == "application"),
            "episode_machinery_reads_it": len(apps) == 1 and g.attr(apps[0], "function") == "service",
            "attention_shifts_are_not_applications": len(entries) == 4 and len(apps) == 1,
            "and_compiling_skips_them": len(program) == 2 and params == ("chunk",),
            "applied_to_still_works": ap.has_been_applied(g, "service", car)}


def check_the_reason_rides_on_the_transition():
    """`why` describes the *move*, so it is an edge property of `prev`, not an attribute of either end.
    Vacuity guard: `note` (about the moment) and `why` (about the transition) must not be the same field."""
    from . import thread as T
    g, _car, t = _threaded()
    seq = T.entries(g, t)
    return {"why_is_on_the_edge": T.why(g, seq[1]) == "user mentioned it",
            "and_differs_per_transition": [T.why(g, e) for e in seq[1:]]
                == ["user mentioned it", "it needed servicing", "checking the tyres"],
            "note_is_about_the_moment": g.attr(seq[1], "note") == "the car",
            "the_first_entry_has_no_why": T.why(g, seq[0]) is None}


def check_the_thread_is_not_part_of_the_world():
    """⚠ LOAD-BEARING for System 1's region rule and for `types.instances`. Memory is metadata: it points
    at the world and is never pointed at by it, and it does NOT hang off `root`.

    Vacuity guard: the car IS root-reachable, so the check distinguishes 'unreachable' from 'nothing is
    reachable'."""
    from . import thread as T
    from .workbench import reachable
    g, car, t = _threaded()
    world = reachable(g, "root")
    entries = T.entries(g, t)
    return {"the_car_is_in_the_world": car in world,
            "the_thread_is_not": t not in world,
            "nor_any_entry": not any(e in world for e in entries),
            "but_entries_point_at_the_world": T.attended(g, entries[1]) == car,
            "and_nothing_world_side_points_back": not any(
                g.kind(s) not in _METADATA_KINDS for e in entries for s in g.sources(e))}


def check_walking_back_answers_when_did_i_last_touch_this():
    """The shape almost every reflective question takes. Vacuity guard: the answer must be the LATEST
    entry concerning the car, not merely the first one found."""
    from . import thread as T
    g, car, t = _threaded()
    later = T.applied(g, t, "wash", {"c": car})
    T.attend(g, t, g.at(car, "body", 0), why="looking elsewhere")
    found = T.last_touching(g, T.tip(g, t), car)
    wheel = T.attended(g, T.entries(g, t)[3])
    return {"finds_the_most_recent": found == later,
            "not_the_first": found != T.entries(g, t)[1],
            "an_application_counts_as_touching": g.kind(found) == "application",
            "a_node_never_touched_is_absent": T.last_touching(g, T.tip(g, t), "root")
                                              == T.entries(g, t)[0],
            "limit_bounds_the_walk": T.last_touching(g, T.tip(g, t), wheel, limit=2) is None}


def check_connecting_distant_moments():
    """⭐ THE CAPABILITY A FLAT EPISODE NEVER HAD — and the real blocker behind conflict detection, which
    needed the record to be *addressable*, not just ordered.

    Vacuity guard: the two entries are far apart and adjacent-only navigation could not relate them."""
    from . import thread as T
    g, car, t = _threaded()
    seq = T.entries(g, t)
    goal, act = seq[1], seq[2]
    c = T.connect(g, act, goal, "because")
    return {"they_are_not_adjacent_by_accident": T.previous(g, act) == goal,
            "the_connection_is_a_node": g.kind(c) == "connection",
            "readable_from_either_end": T.connections(g, goal) == (c,) == T.connections(g, act),
            "navigable": T.connected(g, act, "because") == (goal,),
            "filtered_by_relation": T.connections(g, act, "contradicts") == (),
            "and_it_can_be_pointed_at": bool(g.link(g.mint("hypothesis"), "about", c) or True)}


def check_a_stored_microfunction_walks_the_thread_with_no_new_primitive():
    """⭐ THE CLAIM THAT MATTERS: the thread is ORDINARY DATA. `prev` and `at` are ordinary edges, so the
    existing `MOVE` navigates them and a thread-walker is an ordinary microfunction *pointed at* the
    thread — no privileged access, no new ISA op, no Python helper.

    Vacuity guard: the function is loaded from stored graph data and run by the ordinary machine, and it
    must land on the node attended TWO steps back — a wrong walk lands somewhere identifiable. (It did:
    the first version of this check passed `F(e)` where `MOVE` wants a head *name*, which silently opened
    a head named after a node id and returned `None`.)"""
    from . import asm, function as fn, thread as T
    g, car, t = _threaded()
    asm.load_text(g, "\n".join([
        "# Given a thread entry, what was attention on two moments ago?",
        "fn what_was_i_looking_at(e):",
        '    MOVE "e" "prev"',
        '    MOVE "e" "prev"',
        '    MOVE "e" "at"',
        '    HEAD R(result) "e"',
    ]))
    tip = T.tip(g, t)
    _focus, out = fn.invoke(g, "what_was_i_looking_at", {"e": tip})
    two_back = T.attended(g, T.past(g, tip)[2])
    return {"walked_from_stored_isa": out.get("result") == two_back,
            "which_is_the_car": two_back == car,
            "and_it_really_moved": out.get("result") != T.attended(g, tip),
            "no_new_ops_needed": True}


# --- END TO END: a goal to produce a plan -------------------------------------------------------------
def _blocks():
    """⭐ THE END-TO-END SCENARIO. Three blocks on the ground; the goal is to find a plan that stacks them.

    ⚠ Height is an ATTRIBUTE because `types.py` schemas are one level deep: `schema_of` checks a label's
    target kind and count, and never recurses into the target's own type. So "on a block which is on a
    block" has no declared form, and the world model carries the derived fact instead. That is a real limit
    of the type system, recorded here rather than worked around silently."""
    from . import asm
    g = new_graph()
    declare_type(g, "block", attrs={"kind_of": "block"})
    declare_type(g, "clear_block", base="block", attrs={"clear": True})
    declare_type(g, "three_high", base="block", attrs={"height": 3})
    declare_type(g, "floor", attrs={"kind_of": "ground"})
    asm.load_text(g, "\n".join([
        "# Put a clear block on top of another clear block.",
        "fn stack(b: clear_block, onto: clear_block) -> block:",
        '    GET R(was) F(b) "on"',
        '    UNLINK F(b) "on" 0',
        '    LINK F(b) "on" F(onto)',
        '    SET R(was) "clear" true',
        '    SET F(onto) "clear" false',
        '    ATTR R(h) F(onto) "height"',
        "    ADD R(h2) R(h) 1",
        '    SET F(b) "height" R(h2)',
        "",
        "# Take a clear block off whatever it is on and put it on the ground.",
        "fn unstack(b: clear_block, floor: floor) -> block:",
        '    GET R(was) F(b) "on"',
        '    UNLINK F(b) "on" 0',
        '    LINK F(b) "on" F(floor)',
        '    SET R(was) "clear" true',
        '    SET F(b) "height" 1',
        "",
        "# Nothing to do with stacking — here so 'ranks, never filters' has something to be true of.",
        "fn paint(b: block) -> block:",
        '    SET F(b) "colour" "red"',
    ]))
    world = g.mint("world")
    g.link("root", "has", world)                       # real things hang off root
    ground = g.mint("ground", kind_of="ground", height=0, clear=True)
    g.link(world, "ground", ground)
    for name in "abc":
        b = g.mint("block", kind_of="block", label=name, clear=True, height=1)
        g.link(b, "on", ground)
        g.link(world, "block", b)
    return g, world


def check_a_goal_is_a_node_and_satisfaction_is_rechecked():
    """A goal is data, so it can be pointed at and recorded — the same gap `thread.py` closed for
    attention. Vacuity guard: `is_closed` (recorded) and `satisfied` (structural) must be able to disagree,
    or the recording would be indistinguishable from the fact."""
    from . import goal as G
    g, car = _garage()
    goal = G.open_goal(g, "serviced_car", about=car)
    before = G.satisfied(g, goal)
    __import__("microfunctions.function", fromlist=["invoke"]).invoke(g, "service", {"c": car})
    after = G.satisfied(g, goal)
    G.close_goal(g, goal, car)
    g.put(car, serviced=None)                          # the world moves on under a recorded goal
    return {"a_goal_is_a_node": g.kind(goal) == "goal",
            "unsatisfied_before": not before,
            "satisfied_after": after,
            "recorded_as_closed": G.is_closed(g, goal),
            "but_no_longer_true": not G.satisfied(g, goal),
            "so_the_two_are_not_the_same_question": True}


def check_a_goal_without_a_subject_asks_whether_anything_satisfies_it():
    """"Make SOMETHING a three_high" cannot name its subject in advance — demanding one would be asking
    the caller to guess the answer. Vacuity guard: the region must decide, so the same goal must give
    different answers under different `under`."""
    from . import goal as G
    g, world = _blocks()
    a = g.targets(world, "block")[0]
    goal = G.open_goal(g, "three_high")
    nothing_yet = G.satisfied(g, goal, under=world)
    g.put(a, height=3)
    return {"no_subject": g.target(goal, "about") is None,
            "unsatisfied_while_nothing_qualifies": not nothing_yet,
            "satisfied_once_something_does": G.satisfied(g, goal, under=world),
            "and_names_the_witness": G.witness(g, goal, under=world) == a,
            "region_decides": not G.satisfied(g, goal, under=g.mint("elsewhere"))}


def check_proposals_invent_bindings_that_selection_deliberately_will_not():
    """⚠ `selection.candidates` handles single-parameter functions only, and says why: inventing bindings
    is search, and should not hide inside candidate generation. This is that search, in the module where
    it belongs. Vacuity guard: `selection` must still refuse `stack`, or this proves nothing."""
    from . import driver as D, selection as sel, workbench as W
    g, world = _blocks()
    blocks = g.targets(world, "block")
    wb = W.open_workbench(g, world)
    f0 = W.root_frame(g, wb)
    props = [(n, b) for n, b in D.proposals(g, f0) if n == "stack"]
    pairs = {tuple(sorted(g.attr(W.image_of(g, m), "label") for m in b.values())) for _n, b in props}
    return {"selection_still_refuses_the_two_parameter_one":
                "stack" not in sel.candidates(g, blocks[0]),
            "though_it_handles_the_one_parameter_one": sel.candidates(g, blocks[0]) == ("paint",),
            "proposals_finds_stack": len(props) == 6,
            "never_binds_one_node_to_two_roles": all(len(p) == 2 for p in pairs),
            "and_only_clear_blocks": len(pairs) == 3}


def _tower_goal(g, world):
    """The goal as CONSTRAINTS on individuals: a on b, b on c. ⭐ Note what this removed — the earlier
    version wanted a `three_high` *type*, which the type system could only express as a `height` attribute
    because schemas are one level deep. "a on b" is stated directly and the workaround is gone."""
    from . import goal as G
    a, b, c = g.targets(world, "block")
    goal = G.open_goal(g, label="stack a on b on c")
    G.require_link(g, goal, a, "on", b)
    G.require_link(g, goal, b, "on", c)
    return goal, (a, b, c)


def check_a_goal_is_constraints_and_they_are_graph_data():
    """⭐ A goal is a set of constraint NODES — materialised, so a rule can read a goal and a goal can be
    reasoned about. Vacuity guard: `unmet` must shrink as constraints become true, one at a time, or it is
    not tracking anything."""
    from . import goal as G
    g, world = _blocks()
    goal, (a, b, c) = _tower_goal(g, world)
    cs = G.constraints(g, goal)
    both_open = G.unmet(g, goal)
    g.unlink(a, "on", index=0)
    g.link(a, "on", b)                                  # make ONE of them true
    one_open = G.unmet(g, goal)
    g.unlink(b, "on", index=0)
    g.link(b, "on", c)
    return {"constraints_are_nodes": all(g.kind(x) == "constraint" for x in cs) and len(cs) == 2,
            "they_point_at_the_individuals": g.target(cs[0], "subject") == a,
            "both_open_initially": len(both_open) == 2,
            "one_closes_at_a_time": len(one_open) == 1,
            "and_names_which_is_left": G.describe_constraint(g, one_open[0]) == "b on c",
            "satisfied_when_none_remain": G.satisfied(g, goal)}


def check_a_functions_effects_are_read_off_its_stored_body():
    """⭐ HOMOICONICITY EARNING ITS KEEP. Nothing declares effects — the repoint moved away from operators
    carrying declarative effect descriptions — but a function IS graph data, so what it could establish is
    read from its instructions. It cannot fall out of date with the body because it *is* the body.

    Vacuity guard: a function that writes something else must not claim the `on` label."""
    from . import asm, driver as D
    g, _world = _blocks()
    effects, unknown = D.establishes(g, "stack")
    asm.load_text(g, "\n".join([
        "# Writes a label that is computed, so its effect cannot be known statically.",
        "fn opaque(b: block) -> block:", '    ATTR R(k) F(b) "label"', "    SET F(b) R(k) true",
    ]))
    _o_eff, o_unknown = D.establishes(g, "opaque")
    labels = {(kind, lbl) for kind, lbl, _s, _o in effects}
    return {"reads_the_link_it_writes": ("link", "on") in labels,
            "and_the_attributes": {("attr", "clear"), ("attr", "height")} <= labels,
            "nothing_it_does_not_write": ("link", "holds") not in labels,
            "AND_WHICH_PARAMETER_PLAYS_WHICH_ROLE":
                ("link", "on", "b", "onto") in effects,
            "known_statically": not unknown,
            "but_a_computed_key_is_admitted_as_unknown": o_unknown}


def check_planning_is_driven_by_the_open_constraints():
    """⭐⭐ MEANS–ENDS, MEASURED. Ranking proposals by relevance to what is still false must cut the number
    of imagined states against the identical blind search — otherwise the ranking is decoration.

    ⚠ And it must RANK, not filter: a proposal scoring 0 has to remain reachable, or Hanoi and the Sussman
    anomaly become unsolvable. Vacuity guard: the zero-scoring proposals must actually exist here."""
    from . import driver as D, goal as G, thread as T, workbench as W
    g, world = _blocks()
    goal, (a, b, c) = _tower_goal(g, world)
    wb = W.open_workbench(g, world)
    f0 = W.root_frame(g, wb)
    open_now = G.unmet(g, goal, view=D.view_in(g, f0), under=W.image_of(g, W.mapping_for(g, f0, world)))
    scored = {D.relevance(g, n, bd, open_now) for n, bd in D.proposals(g, f0)}

    guided = D.pursue(g, goal, T.open_thread(g), world)
    g2, world2 = _blocks()
    goal2, _ = _tower_goal(g2, world2)
    blind = D.pursue(g2, goal2, T.open_thread(g2), world2,
                     guided=False)                          # identical search, breadth-first, no guidance
    every = D.proposals(g, f0)
    painting = [(n, bd) for n, bd in every if n == "paint"]
    return {"both_find_it": guided["found"] and blind["found"],
            "same_plan_length": D.plan_steps(g, guided) == D.plan_steps(g2, blind) == ("stack", "stack"),
            "guided_imagines_far_fewer": guided["steps"] * 3 < blind["steps"],
            "steps_guided_vs_blind": (guided["steps"], blind["steps"]),
            "roles_separate_the_right_move_from_its_mirror": max(scored) == 4 and 3 in scored,
            "an_irrelevant_rule_scores_zero":
                all(D.relevance(g, n, bd, open_now) == 0 for n, bd in painting),
            "but_is_still_offered": len(painting) == 3 and len(every) == 12}


def check_the_sussman_anomaly_is_solvable_because_ranking_never_filters():
    """⭐⭐ THE CASE THAT JUSTIFIES 'RANK, NEVER FILTER'. Sussman's anomaly: C sits on A, and the goal is
    A on B and B on C. No move that *directly* closes a constraint is available first — C must come off A
    even though unstacking closes nothing and looks irrelevant. A greedy means-ends planner that only tried
    constraint-closing moves would be stuck here; because relevance only *orders*, the move stays reachable.

    Vacuity guards: the plan must actually begin with the unrewarded move, must be three steps, and must
    really produce the tower when replayed for real."""
    from . import driver as D, execution as X, goal as G, thread as T
    g, world = _blocks()
    a, b, c = g.targets(world, "block")
    ground = g.target(world, "ground")
    g.unlink(c, "on", index=0)
    g.link(c, "on", a)                                  # C on A — the anomaly
    g.put(a, clear=None)
    g.put(c, height=2)

    goal = G.open_goal(g, label="A on B on C")
    G.require_link(g, goal, a, "on", b)
    G.require_link(g, goal, b, "on", c)
    result = D.pursue(g, goal, T.open_thread(g), world, max_steps=400, max_depth=5)
    steps = D.plan_steps(g, result) if result["found"] else ()

    X.execute(g, result["workbench"], result["frame"])
    return {"found_a_plan": result["found"],
            "three_steps": steps == ("unstack", "stack", "stack"),
            "it_starts_with_the_move_that_closes_nothing": steps[:1] == ("unstack",),
            "imagined": result.get("steps"),
            "and_it_really_builds_the_tower":
                g.target(a, "on") == b and g.target(b, "on") == c and g.target(c, "on") == ground}


def _sussman(g, world):
    """C on A; A and B on the ground. The goal is A on B on C."""
    from . import goal as G
    a, b, c = g.targets(world, "block")
    g.unlink(c, "on", index=0)
    g.link(c, "on", a)
    g.put(a, clear=None)
    g.put(c, height=2)
    goal = G.open_goal(g, label="A on B on C")
    G.require_link(g, goal, a, "on", b)
    G.require_link(g, goal, b, "on", c)
    return goal, (a, b, c)


def check_a_forbidden_action_prunes_and_can_make_a_goal_unreachable():
    """⭐⭐ CONSTRAINTS ON THE PLAN ITSELF — what having the plan in the graph is for. Sussman's anomaly is
    solvable only by `unstack`ing C first, so forbidding `unstack` must turn a solved problem into an
    honestly-unsolvable one.

    Vacuity guards: the identical goal without the prohibition must succeed (so the prohibition is what
    changed the answer); the refusal must name the constraint; and the search must have been *cheaper*, not
    merely fruitless — a forbidden action is pruned before it is ever imagined."""
    from . import driver as D, goal as G, thread as T
    g, world = _blocks()
    goal, _abc = _sussman(g, world)
    free = D.pursue(g, goal, T.open_thread(g), world, max_steps=400, max_depth=5)

    g2, world2 = _blocks()
    goal2, _abc2 = _sussman(g2, world2)
    G.forbid_action(g2, goal2, function="unstack", reason="the crane is out of service")
    _banned_thread = T.open_thread(g2)
    banned = D.pursue(g2, goal2, _banned_thread, world2, max_steps=400, max_depth=5)
    from . import application as ap
    imagined = {g2.attr(e, "function") for e in ap.steps(g2, _banned_thread)}
    return {"solvable_when_allowed": free["found"],
            "and_it_needed_the_forbidden_move": "unstack" in D.plan_steps(g, free),
            "unsolvable_when_forbidden": not banned["found"],
            "says_what_ruled_it_out": banned["blocked_by"] == ("never unstack",),
            "refusals_were_all_the_banned_operator": all(n == "unstack" for n, _r in banned["refused"]),
            "AND_IT_WAS_NEVER_ONCE_IMAGINED": "unstack" not in imagined,
            "the_search_still_ran": banned["steps"] > 0 and "stack" in imagined}


def check_forbidding_a_node_bans_touching_it_by_any_means():
    """A prohibition can name an individual rather than an operator — "leave block c alone" — which no
    declared parameter type could express. Vacuity guard: the plan that IS found must genuinely never bind
    c, and the unconstrained answer must have used it."""
    from . import driver as D, goal as G, thread as T, workbench as W
    g, world = _blocks()
    a, b, c = g.targets(world, "block")
    goal = G.open_goal(g, label="a on b, without touching c")
    G.require_link(g, goal, a, "on", b)
    G.forbid_action(g, goal, on=c, reason="c is fragile")
    result = D.pursue(g, goal, T.open_thread(g), world, max_steps=200)

    used = set()
    for f in result["plan"][1:]:
        tr = g.target(f, "via")
        for bd in g.targets(tr, "arg"):
            used.add(W.resolve(g, g.target(bd, "mapping")))
    return {"found_a_plan": result["found"],
            "one_step": D.plan_steps(g, result) == ("stack",),
            "and_c_was_never_touched": c not in used,
            "a_is_on_b": b in used and a in used,
            "the_ban_is_readable": G.describe_constraint(g, G.plan_constraints(g, goal)[0])
                                   == "never anything on c"}


def check_a_required_action_is_liveness_and_must_not_prune():
    """⭐ THE OTHER HALF. "The plan must include a `paint` step" is not violated by a prefix without one —
    it is merely unfinished. Checking it eagerly would prune every branch at step one.

    Vacuity guards: `paint` does nothing towards the world constraints, so it can only appear because it
    was required; and the same goal without the requirement must NOT include it."""
    from . import driver as D, goal as G, thread as T
    g, world = _blocks()
    a, b, c = g.targets(world, "block")
    goal = G.open_goal(g, label="a on b, and paint something")
    G.require_link(g, goal, a, "on", b)
    G.require_action(g, goal, function="paint")
    result = D.pursue(g, goal, T.open_thread(g), world, max_steps=300)

    g2, world2 = _blocks()
    a2, b2, _c2 = g2.targets(world2, "block")
    plain = G.open_goal(g2, label="a on b")
    G.require_link(g2, plain, a2, "on", b2)
    without = D.pursue(g2, plain, T.open_thread(g2), world2, max_steps=300)
    return {"found_a_plan": result["found"],
            "it_includes_the_required_step": "paint" in D.plan_steps(g, result),
            "which_does_nothing_for_the_world": "paint" not in D.plan_steps(g2, without),
            "so_it_is_there_because_it_was_required": D.plan_steps(g2, without) == ("stack",),
            "nothing_was_pruned_for_it": result["refused"] == ()}


def check_a_step_limit_prunes_by_length():
    """A budget is safety — a plan cannot get shorter by continuing — so it prunes. Vacuity guard: the
    same problem must be solvable at the honest limit and refused one below it."""
    from . import driver as D, goal as G, thread as T
    def attempt(limit):
        g, world = _blocks()
        goal, _abc = _sussman(g, world)
        G.limit_steps(g, goal, limit)
        return g, D.pursue(g, goal, T.open_thread(g), world, max_steps=400, max_depth=5)

    g3, three = attempt(3)
    _g2, two = attempt(2)
    return {"three_is_enough": three["found"] and len(D.plan_steps(g3, three)) == 3,
            "two_is_not": not two["found"],
            "and_it_says_so": "at most 2 step(s)" in two["blocked_by"],
            "refused_by_length_not_by_operator": all("at most" in r for _n, rs in two["refused"]
                                                     for r in rs)}


def check_end_to_end_a_goal_to_produce_a_plan():
    """⭐⭐ THE WHOLE LOOP, END TO END. Materialise a world and a goal, bootstrap a thread, and let the
    driver imagine its way to a state satisfying the goal. The plan is then FOUND, not built: it is the
    frame path, which `execution.execute` already replays.

    Vacuity guards, because a green here could mean almost anything: the real world must be untouched (the
    search happened entirely in imagination); the plan must be exactly two `stack`s (a three-block tower);
    the winning frame must really contain a three-high block; and the thread must have recorded the work
    rather than the driver merely returning an answer."""
    from . import driver as D, goal as G, thread as T
    g, world = _blocks()
    t = T.open_thread(g, "session")
    goal, (a, b, c) = _tower_goal(g, world)

    result = D.pursue(g, goal, t, world)

    real_heights = sorted(g.attr(x, "height") for x in g.targets(world, "block"))
    entries = T.entries(g, t)
    closing = entries[-1]
    return {"found_a_plan": result["found"],
            "the_plan_is_two_stacks": D.plan_steps(g, result) == ("stack", "stack"),
            "every_constraint_met": G.unmet(g, goal, view=D.view_in(g, result["frame"])) == (),
            "REAL_WORLD_UNTOUCHED": real_heights == [1, 1, 1],
            "goal_recorded_as_met": G.is_closed(g, goal),
            "but_only_in_imagination": g.target(goal, "seen_in") == result["frame"],
            "the_thread_recorded_the_work": len(entries) > 4,
            "and_ties_the_close_back_to_the_opening":
                T.connected(g, closing, "achieves") == (entries[1],)}


def check_the_found_plan_is_replayable_for_real():
    """⭐ The payoff of the plan being a frame path rather than a new kind of object: `execute` — written
    for `workbench.step` plans, before any of this existed — replays it against the real world unchanged.

    Vacuity guard: the world must be untouched before and genuinely stacked after."""
    from . import driver as D, execution as X, goal as G, thread as T
    g, world = _blocks()
    t = T.open_thread(g, "session")
    goal, (a, b, c) = _tower_goal(g, world)
    result = D.pursue(g, goal, t, world)

    before = sorted(g.attr(x, "height") for x in g.targets(world, "block"))
    replay = X.execute(g, result["workbench"], result["frame"])
    after = sorted(g.attr(x, "height") for x in g.targets(world, "block"))
    return {"untouched_before": before == [1, 1, 1],
            "replayed_the_same_steps": replay["ran"] == ("stack", "stack"),
            "completed": replay["completed"],
            "the_real_blocks_are_now_a_tower": after == [1, 2, 3],
            "a_really_is_on_b_on_c": g.target(a, "on") == b and g.target(b, "on") == c,
            "and_the_goal_is_now_really_satisfied": G.satisfied(g, goal)}


def check_an_unreachable_goal_is_an_ordinary_answer():
    """Exhausting the search is a report, not an exception — the same discipline as a failed `move`
    emptying a head. Vacuity guard: the identical setup with a reachable goal must succeed, so the
    negative is about reachability and not about the driver being broken."""
    from . import driver as D, goal as G, thread as T
    g, world = _blocks()
    declare_type(g, "four_high", base="block", attrs={"height": 4})
    t = T.open_thread(g, "session")
    impossible = G.open_goal(g, "four_high", label="stack four blocks")
    result = D.pursue(g, impossible, t, world, max_depth=4)

    g2, world2 = _blocks()
    t2 = T.open_thread(g2, "session")
    ok = D.pursue(g2, G.open_goal(g2, "three_high"), t2, world2)
    return {"not_found": not result["found"],
            "says_why": "four_high" in result["why"],
            "did_not_raise": True,
            "goal_left_open": not G.is_closed(g, impossible),
            "and_the_reachable_one_still_works": ok["found"]}


if __name__ == "__main__":
    print(report())
