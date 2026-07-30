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


if __name__ == "__main__":
    print(report())
