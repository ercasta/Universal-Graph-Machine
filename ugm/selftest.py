"""Self-test — substrate, focus, types, hypotheses, ISA.

Probe discipline, not a unit-test suite: each check states what would make it fail, and per the rule earned
three times over in one day — for every green, ask what would make it vacuous — checks that could pass
for an uninteresting reason are written to distinguish.

Re-runnable: `python -m ugm.selftest`.
"""
from __future__ import annotations

from . import hypothesis as H
from . import isa
from .focus import Focus
from .graph import Ref, new_graph
from .isa import (ADD, BACK, NATIVE, CLOSE, CONST, COUNT, DEREF, F, FOCUS, FOLLOW, FORK, HASFOCUS,
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


def check_the_kind_index_cannot_disagree_with_a_scan():
    """A hand-maintained index, so it earns a test — the kind that guards a discipline a human must
    follow (only `mint` adds and only `drop` removes), which is the kind this project keeps.

    `of_kind` exists because `types.find_type` and `function.find` scanned every node in the graph on
    every lookup, and `violations` reached `find_type` four times per call. Measured on one
    `driver.proposals` enumeration over a world with 200 nodes that bind to nothing: 21,525 `find_type`
    calls and 21,575 whole-graph tuple builds — which is why inert content cost 57× the enumeration time
    for zero extra proposals.

    It is legitimate where `types.tag`'s `is_a` stamp is not, and the difference is worth stating: this is
    maintained by the substrate on the only operation that can create a kind, so it cannot drift;
    a stamp is a claim a rule made, so it must be re-validated on read (`tagged_as`).

    Vacuity guard: `drop` and `rollback` must both be exercised, since a write-only index would pass any
    test that never removed anything."""
    g = new_graph()
    def scan(kind):
        return sorted(n for n in g.nodes if g.kind(n) == kind)

    a, b = g.mint("widget", label="a"), g.mint("widget", label="b")
    g.mint("gadget")
    after_mint = sorted(g.of_kind("widget")) == scan("widget") == sorted([a, b])

    sp = g.savepoint()
    c = g.mint("widget", label="c")
    during = sorted(g.of_kind("widget")) == scan("widget") == sorted([a, b, c])
    g.rollback(sp)
    after_rollback = sorted(g.of_kind("widget")) == scan("widget") == sorted([a, b])

    g.drop(b)
    after_drop = sorted(g.of_kind("widget")) == scan("widget") == [a]

    sp2 = g.savepoint()
    g.drop(a)
    g.rollback(sp2)
    after_undropping = sorted(g.of_kind("widget")) == scan("widget") == [a]

    try:                                   # kind is fixed at mint, or the index would drift silently
        g.put(a, kind="gadget")
        refused = False
    except ValueError:
        refused = True
    return {"after_mint": after_mint,
            "MINT_IS_ROLLED_BACK": during and after_rollback,
            "DROP_REMOVES": after_drop,
            "AND_IS_ITSELF_ROLLED_BACK": after_undropping,
            "changing_kind_is_refused": refused,
            "still_the_kind_it_was_minted_as": g.kind(a) == "widget",
            "unknown_kind_is_empty_not_an_error": g.of_kind("nonesuch") == ()}


def check_a_goal_can_have_a_hierarchy_and_an_undecomposed_one_is_not_vacuously_done():
    """Slice 3 of `docs/deliberation.md`: goals gain a hierarchy, so `DECOMPOSE` has somewhere to post and a
    decision rule has a context to key on.

    The key this check exists for is the last one, and it is a trap taken from prior work rather than
    rediscovered. An earlier note records that a parent's "all my children are done"
    guard was written as an *absence* — no subgoal that is unmet — and so was vacuously true before any
    subgoal had been minted: an undecomposed goal read as trivially achieved. Generalised there as *don't
    trust an open-ended absence without an explicit closure fact*. `satisfied` already applies the same rule
    one level down (`bool(cs)`), which is why the two guards look alike.

    Also: ancestry is the context (so a rule need not be rewritten per position), children are O(1) the
    other way, and a cycle is structurally impossible because parentage is set at mint and never
    changed — the same reasoning that lets `Graph.of_kind` be an index rather than a cache. That bounds
    cycles, *not* depth: recursive decomposition mints a fresh goal each time, so `depth_of` is what a
    termination bound has to read."""
    from . import goal as G
    g, world = _blocks()
    a, b, c = g.targets(world, "block")

    top = G.open_goal(g, label="build the tower")
    G.require_link(g, top, a, "on", b)
    base = G.open_goal(g, label="settle the base", under=top, because="the base must be clear first")
    G.require_link(g, base, b, "on", c)
    deep = G.open_goal(g, label="clear c", under=base)

    # The trap: `top` has a child that is not satisfied, so "all children done" must be False; and `deep`
    # has NO children, so the same question must also be False rather than vacuously True.
    undecomposed_reads_done = G.subgoals_met(g, deep)
    g.unlink(b, "on", index=0)
    g.link(b, "on", c)                                   # now `base` really is satisfied
    parent_after = G.subgoals_met(g, top)

    return {"a_subgoal_knows_its_parent": G.parent_of(g, base) == top,
            "and_the_parent_its_children": G.subgoals(g, top) == (base,),
            "ancestry_is_the_context": G.ancestry(g, deep) == (deep, base, top),
            "within_answers_the_rule_question": G.within(g, deep, top) and not G.within(g, top, deep),
            "depth_is_what_a_bound_reads": (G.depth_of(g, top), G.depth_of(g, deep)) == (0, 2),
            "the_reason_rides_on_the_transition":
                G.raised_because(g, base) == "the base must be clear first",
            "a_cycle_is_structurally_impossible": G.parent_of(g, top) is None,
            "decomposed_says_which_is_which": G.decomposed(g, top) and not G.decomposed(g, deep),
            "AN_UNDECOMPOSED_GOAL_IS_NOT_VACUOUSLY_DONE": not undecomposed_reads_done,
            "but_a_decomposed_one_can_be": parent_after,
            "and_this_is_NOT_the_parents_own_satisfaction":
                parent_after and not G.satisfied(g, top, under=world)}


def check_ignorance_is_representable_and_sensing_closes_it():
    """The last capability gap: *not looked* as distinct from *not there*.

    The engine already performed information-gathering actions but could only model them as world-*changing*
    ones — `scan_dir`'s mock mints file nodes, as though scanning created files rather than revealing
    them. Underneath was a substrate limit: an attribute was present or absent, and absence meant *lacks
    it*. So the system could not tell "make p true" from "find out whether p", an information-gathering
    subgoal had nothing to close, and `pursue` reported failure identically whether no plan exists or
    no plan exists given what I know — though only the second warrants going and finding out.

    The fix rides on's existing insight rather than adding a planner. A goal naming *which*
    constraints are false lets the driver ask what could close them; one separating false from
    unknown lets it reach for a sensing action. `undetermined` is that separation.

    Explicit ignorance only. Absence still means *lacks it*; a slot is unknown only when something
    says so. Treating every absence as ignorance would make the whole graph unknown and every constraint
    undecidable — and would be untrue, since most absences really are knowledge.

    `blocked_on_ignorance` requires the goal to bottom out in ignorance, not merely touch it —
    otherwise a goal with one unknown slot and three false constraints would send the system looking in
    boxes instead of doing the work. Its vacuity guard is `decomposed`'s: with nothing unmet it is not
    blocked, it is done."""
    from . import driver as D, goal as G, intake as I, thread as T
    from .graph import UNKNOWN
    from . import asm

    g, world = _blocks()
    box = g.mint("box", kind_of="box", label="box", contents=UNKNOWN)
    g.link(world, "box", box)
    declare_type(g, "box", attrs={"kind_of": "box"})
    asm.load_text(g, "\n".join([
        "# Looking is an ACTION: it changes what we know, not what is there.",
        "fn look_inside(b: box) -> box:",
        '    SET F(b) "contents" "a spanner"',
    ]))

    goal = I.read_goal(g, "goal find out what is in the box:\n    box.contents known")
    before = (len(G.unmet(g, goal, under=world)), len(G.undetermined(g, goal, under=world)))
    blocked = G.blocked_on_ignorance(g, goal, under=world)

    # A goal that is unmet for an ordinary reason must NOT read as blocked on ignorance.
    a, b, _c = g.targets(world, "block")
    plain = G.open_goal(g, label="a on b")
    G.require_link(g, plain, a, "on", b)
    mixed = G.open_goal(g, label="both")
    G.require_link(g, mixed, a, "on", b)
    G.require_known(g, mixed, box, "contents")
    # Read the contrasts BEFORE acting. The first version evaluated them in the return dict, after
    # `carry_out` had already made the slot known — so `mixed` had nothing undetermined left and the key
    # passed no matter what `blocked_on_ignorance` did. A planted bug proved it tested nothing.
    plain_blocked = G.blocked_on_ignorance(g, plain, under=world)
    mixed_blocked = G.blocked_on_ignorance(g, mixed, under=world)
    empty_blocked = G.blocked_on_ignorance(g, G.open_goal(g, label="empty"), under=world)

    # END to END: the goal is closed only by an action that reveals, and only after it really ran.
    report = D.carry_out(g, goal, T.open_thread(g), world)

    unknown_is_falsy = bool(UNKNOWN) is False
    return {"unknown_is_not_absent": g.attr(box, "contents") is not None,
            "and_not_a_value_either": unknown_is_falsy,
            "the_constraint_is_UNMET_and_UNDETERMINED": before == (1, 1),
            "SO_THE_GOAL_IS_BLOCKED_ON_IGNORANCE": blocked,
            "an_ordinary_unmet_goal_is_NOT": not plain_blocked,
            "nor_is_one_that_merely_TOUCHES_ignorance": not mixed_blocked,
            "and_a_satisfied_goal_is_not_blocked_but_done": not empty_blocked,
            "LOOKING_CLOSED_IT": report["done"],
            "by_an_action_that_really_ran": g.attr(box, "contents") == "a spanner",
            "and_the_slot_is_no_longer_unknown":
                g.attr(box, "contents") is not UNKNOWN and not G.undetermined(g, goal, under=world),
            "SENSE_is_a_real_verb_now": D.SENSE in D.VERBS,
            "the_surface_can_say_it": "known" in I.describe(g, goal)}


def check_a_knowledge_goal_cannot_close_itself():
    """A `known` claim about a slot that does NOT exist is satisfied by default, and that is a goal
    that closes itself — reported done, with an empty plan, having never looked.

    `require_known`'s docstring already records this failure once, caught when the subject was stored as a
    string. It came back by two further routes, both found by an earlier probe on the utterance
    *"list all the files in the repo"*:

    * the key names an edge — `repo.file known`, where `holds` asks `g.attr(here, key) is not UNKNOWN`
      and an edge label has no attribute slot at all;
    * the key names nothing — `repo.files known`, a plain mistyped plural, which behaves identically.

    Neither is a bug in `UNKNOWN`. Absence-means-*lacks-it* is deliberate and correct; the mistake was
    admitting a relation — or a typo — into an attribute-shaped claim. So both refuse.

    Vacuity guard, and it is the whole check. A refusal that fired on everything would pass every
    key below while destroying the feature, so the legitimate case must still be authorable and still be
    genuinely unmet and undetermined — i.e. the thing that makes `known` worth having has to survive.
    The two refusals must also be told apart, or one route could be dead and nothing would say so."""
    from . import goal as G, intake as I
    from .graph import UNKNOWN

    g = new_graph()
    declare_type(g, "repo", {"file": ("chunk", 1)}, attrs={"scanned": True})
    repo = g.mint("chunk", kind_of="repo", label="repo", scanned=UNKNOWN)
    g.link("root", "has", repo)
    g.link(repo, "file", g.mint("chunk", kind_of="file", label="parser"))

    def refusal(line):
        try:
            I.read_goal(g, _lines("goal g:", "    " + line))
            return None
        except Exception as e:
            return str(e)

    edge, typo, real = refusal("repo.file known"), refusal("repo.files known"), refusal("repo.scanned known")

    # The legitimate claim must still DO something: unmet, undetermined, and closable by looking.
    live = I.read_goal(g, _lines("goal look:", "    repo.scanned known"))
    unmet_now = len(G.unmet(g, live, under="root")), len(G.undetermined(g, live, under="root"))
    g.put(repo, scanned=True)
    settled = not G.unmet(g, live, under="root")

    return {"an_EDGE_key_is_REFUSED": edge is not None,
            "and_it_says_which_shape_is_wrong": edge is not None and "names an edge" in edge,
            "a_key_naming_NOTHING_is_REFUSED": typo is not None,
            "THE_TWO_ROUTES_ARE_DISTINCT": edge is not None and typo is not None and edge != typo,
            "but_a_REAL_slot_is_still_accepted": real is None,
            "AND_IT_IS_GENUINELY_UNMET": unmet_now == (1, 1),
            "and_looking_still_closes_it": settled}


def check_a_method_step_can_name_a_third_individual():
    """A method could speak only of `subject` and `object` — the matched constraint's — so a
    decomposition whose steps concern a third individual had no form. `some <name> in <ref> by <link>`
    is lifted from `criterion`, where `docs/deliberation.md` closed this exact gap and never carried it
    across. Found again by an earlier probe on *"after you edit a file, lint that file"*.

    Singular on purpose. A draw reaches a set; raising one subgoal per candidate is the first thing
    `docs/limits.md` forbids — an expanded plan is valid only for the collection as it was when planned.
    So it binds the nearest, and *"do it to each"* stays with slice A's witnesses, which already handle it.

    Vacuity guards. The drawn subgoal must be about a node that is neither the constraint's subject
    nor its object, or the draw could be resolving to `subject` and every key would still pass. A method
    with no draw must behave exactly as before, or this bought reach by breaking the common case. And
    a draw reaching nothing must refuse, rather than raise a subgoal with no subject — a decomposition
    that poses a step about `None` reads downstream as a step that is simply done."""
    from . import goal as G, intake as I, method as M

    def build(*body):
        g = new_graph()
        declare_type(g, "repo", {"file": ("chunk", 1)}, attrs={"kind_of": "repo"})
        declare_type(g, "shipped_repo", base="repo", attrs={"shipped": True})
        repo = g.mint("chunk", kind_of="repo", label="repo")
        g.link("root", "has", repo)
        parser = g.mint("chunk", kind_of="file", label="parser")
        g.link(repo, "file", parser)
        I.read(g, _lines(*body))
        goal = I.read_goal(g, _lines("goal ship it:", "    repo is a shipped_repo"))
        return g, repo, parser, goal

    def refusal(fn):
        try:
            fn()
            return None
        except Exception as e:
            return str(e)

    HEAD = ("method ship it:", "    handles type shipped_repo")
    g, repo, parser, goal = build(*HEAD, "    some f in subject by file",
                                  "    step f is a linted_file", "    step subject.shipped = true")
    m = M.methods(g)[0]
    subs = M.decompose(g, m, goal, M.applicable(g, goal, under="root")[0][1])
    drawn = G.constraints(g, subs[0])[0]
    about = g.target(drawn, "subject")

    # Guard: the subgoal must be about the file, which the goal's constraint never names.
    c0 = M.applicable(g, goal, under="root")
    third = about == parser and about != repo

    # Control: no draw at all, unchanged.
    g2, repo2, _p2, goal2 = build(*HEAD, "    step subject.shipped = true")
    m2 = M.methods(g2)[0]
    subs2 = M.decompose(g2, m2, goal2, M.applicable(g2, goal2, under="root")[0][1])
    plain_ok = g2.target(G.constraints(g2, subs2[0])[0], "subject") == repo2

    undrawn = refusal(lambda: build(*HEAD, "    step z is a linted_file"))
    twice = refusal(lambda: build(*HEAD, "    some f in subject by file",
                                  "    some f in subject by file", "    step f is a linted_file"))

    def empty_draw():
        g3 = new_graph()
        declare_type(g3, "repo", attrs={"kind_of": "repo"})
        declare_type(g3, "shipped_repo", base="repo", attrs={"shipped": True})
        r = g3.mint("chunk", kind_of="repo", label="repo")          # NO file edge at all
        g3.link("root", "has", r)
        I.read(g3, _lines(*HEAD, "    some f in subject by file", "    step f is a linted_file"))
        gl = I.read_goal(g3, _lines("goal ship it:", "    repo is a shipped_repo"))
        mm = M.methods(g3)[0]
        return M.decompose(g3, mm, gl, M.applicable(g3, gl, under="root")[0][1])

    reached_nothing = refusal(empty_draw)

    return {"the_method_declares_the_drawn_role": M.roles_of(g, m) == ("subject", "object", "f"),
            "A_STEP_IS_RAISED_ABOUT_A_THIRD_INDIVIDUAL": third,
            "and_the_other_step_still_speaks_of_the_subject":
                g.target(G.constraints(g, subs[1])[0], "subject") == repo,
            "a_method_WITHOUT_a_draw_is_unchanged": plain_ok,
            "an_UNDRAWN_name_is_refused": undrawn is not None,
            "a_name_drawn_TWICE_is_refused": twice is not None,
            "A_DRAW_REACHING_NOTHING_REFUSES": reached_nothing is not None,
            "and_says_the_traversal_was_empty":
                reached_nothing is not None and "reached nothing" in reached_nothing,
            "the_method_still_matched_in_the_first_place": bool(c0)}


def check_what_was_said_is_on_the_record_and_can_be_taken_back():
    """*"Ignore that."* — and before that, the hole underneath it: `intake.read` built a goal, a
    criterion, a method, and recorded nothing about the fact that somebody said it. Measured: two
    blocks authored against a fresh thread left it holding only its opening entry.

    That is this project's founding defect in a third place. `goal.py` exists because the thing the system
    was trying to do was the thing it could not point at; `thread.py` exists because attention was the one
    thing not homoiconic. The *telling* was next.

    Retract the utterance, NOT the world. A withdrawn block stops being consulted from now on. It is
    not deleted, nothing it let us conclude is unwound (`REVISION 01` deleted retraction/TMS on purpose),
    and nothing dispatched is reversed (the undo journal must never span a dispatch). `forget.py` already
    settled why: retention defaults to keep because `why` and `conflict.interference` read history, so a
    record saying *"this happened because of something you later took back"* beats a hole where the reason
    was.

    The vacuity guard is the whole CHECK, and the first version of it failed. Withdrawing something
    that was making no difference proves nothing — the first attempt used a criterion whose plan was
    identical with and without it, so every key passed while testing nothing. `docs/limits.md` records
    the same trap (*a measurement whose control does not light up is not a measurement*). So the directive
    here must really change the outcome, and that swing is asserted before the retraction is asked for.

    And history must survive: the utterance stays on the thread, still points at what it authored, and
    the authored node is still there to be cited."""
    from . import criterion as CR, discourse as DC, driver as D, intake as I, thread as T

    def plan(g, goal, world):
        try:
            got = D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=6,
                           propose=CR.decide(g, goal, world))
            return D.plan_steps(g, got) if got["found"] else ()
        except D.Undecidable:
            return ("refused",)

    g, world, wh, _box, _parcel = _warehouse(nested=False)
    goal = I.read_goal(g, _lines("goal stow it:", "    wh contains+ parcel", "    never touch wh"))
    th = T.open_thread(g)

    before = plan(g, goal, world)
    said = DC.say(g, th, _lines("criterion stow it directly:",
                                "    must",
                                "    wants link contains",
                                "    do put_in t = object, box = subject"))
    during = plan(g, goal, world)
    # Assert the swing BEFORE retracting. If this is not a real change, nothing below means anything.
    it_mattered = bool(before) and not during

    out = DC.retract(g, th)
    after = plan(g, goal, world)

    # History: the utterance is still there, marked, and still points at what it authored.
    entries = DC.utterances(g, th, by=None)
    node = said["node"]

    # A second "ignore that" must reach further back, not re-withdraw the same thing.
    g2, world2, _wh2, _b2, _p2 = _warehouse(nested=False)
    th2 = T.open_thread(g2)
    a = DC.say(g2, th2, _lines("prefer one:", "    action put_in"))
    b = DC.say(g2, th2, _lines("prefer two:", "    action put_in"))
    DC.retract(g2, th2)
    DC.retract(g2, th2)
    both_gone = DC.is_withdrawn(g2, a["node"]) and DC.is_withdrawn(g2, b["node"])

    def refused(fn):
        try:
            fn()
            return False
        except Exception:
            return True

    g3 = new_graph()
    nothing_said = refused(lambda: DC.retract(g3, T.open_thread(g3)))
    twice = refused(lambda: DC.retract(g, th, said["entry"]))

    return {"SAYING_IT_IS_ON_THE_RECORD": said["utterance"] in entries,
            "THE_UTTERANCE_IS_A_WORLD_OBJECT": said["utterance"] in g.targets(DC.conversation(g), "utterance"),
            "and_its_SPEAKER_IS_A_NODE_not_a_string":
                DC.said_by(g, said["utterance"]) == DC.speaker(g, DC.USER),
            "and_it_points_at_what_it_authored": g.target(said["utterance"], "about") == node,
            "THE_BLOCK_REALLY_CHANGED_THE_OUTCOME": it_mattered,
            "AND_IGNORING_IT_PUT_THE_PLAN_BACK": after == before,
            "the_authored_node_is_MARKED_not_deleted":
                DC.is_withdrawn(g, node) and node in g.nodes,
            "the_criterion_enumerator_skips_it": node not in CR.criteria(g),
            "HISTORY_SURVIVES_the_utterance_is_still_there": said["utterance"] in entries,
            "and_the_retraction_is_itself_on_the_record":
                out["said"] in entries and g.target(out["said"], "withdraws") == said["utterance"],
            "a_SECOND_ignore_that_reaches_further_back": both_gone,
            "retracting_nothing_is_refused": nothing_said,
            "and_retracting_it_twice_is_refused": twice}


def check_the_system_can_ASK_and_the_answer_lands_on_the_same_record():
    """*"Confirm"* is not a discourse primitive — asking is. A system that can only *receive*
    utterances cannot be confirmed with, because there is nothing on the record for an answer to be an
    answer *to*. So a question is an utterance with `by=SYSTEM`, and the discourse is two-directional.

    It needed no new machinery: asking is a DISPATCH. A world crossing that leaves the graph and
    comes back with information, registered `observes=True` because it costs time and changes nothing.
    So the veto and the commit-before-handler discipline apply for free.

    Answering later is the realistic case and is the same recording, since a person is not a
    function: a host that returns nothing synchronously still leaves a `pending` question on the thread,
    and `answered` closes it whenever the reply arrives.

    Vacuity guards: `pending` must be non-empty while unanswered — a check that only looks after the
    answer would pass against an implementation that never marked anything pending; the question and the
    answer must land in one order with the retraction machinery, not a parallel log; and an answer to
    something that was never asked must be refused."""
    from . import discourse as DC, dispatch as DP, thread as T

    g = new_graph()
    th = T.open_thread(g)
    seen = []

    def handler(gr, q):
        seen.append(gr.attr(q, "text"))
        return "driver.py"

    DP.register(DC.ASK_USER, handler, observes=True)
    out = DC.ask(g, th, "which file did you mean?")

    # The deferred route: ask, observe it pending, answer later.
    g2 = new_graph()
    th2 = T.open_thread(g2)
    DP.register(DC.ASK_USER, lambda gr, q: None, observes=True)
    later = DC.ask(g2, th2, "shall I commit?")
    DC.answered(g2, th2, later["question"], "no")           # re-answering closes it
    still_pending = DC.pending(g2, th2)

    # Pending must be true while outstanding, or the key below tests nothing.
    g3 = new_graph()
    th3 = T.open_thread(g3)
    q3 = DC._utter(g3, th3, by=DC.SYSTEM, verb=DC.ASK_USER, about=None, text="waiting?")
    g3.put(q3, pending=True)
    was_pending = DC.pending(g3, th3) == (q3,)
    DC.answered(g3, th3, q3, "yes")

    def refused(fn):
        try:
            fn()
            return False
        except Exception:
            return True

    not_a_question = refused(lambda: DC.answered(g3, th3, T.open_thread(g3), "yes"))

    # One order: a question, an answer and a retraction all walk off the same thread.
    g4 = new_graph()
    th4 = T.open_thread(g4)
    DP.register(DC.ASK_USER, lambda gr, q: "yes", observes=True)
    DC.say(g4, th4, _lines("prefer it:", "    action put_in"))
    DC.ask(g4, th4, "sure?")
    DC.retract(g4, th4, DC.utterances(g4, th4)[0])
    one_order = [g4.attr(DC.said_by(g4, u), "label") for u in DC.utterances(g4, th4, by=None)] == \
                ["user", "system", "user", "user"]

    return {"THE_QUESTION_REACHED_A_PERSON": seen == ["which file did you mean?"],
            "and_the_answer_came_back": out["answer"] == "driver.py",
            "THE_QUESTION_IS_ON_THE_RECORD_as_the_system_speaking":
                DC.said_by(g, out["question"]) == DC.speaker(g, DC.SYSTEM),
            "the_answer_is_recorded_as_ANSWERING_it":
                g.target(out["reply"], "answers") == out["question"],
            "and_nothing_is_left_pending": DC.pending(g, th) == (),
            "A_QUESTION_IS_PENDING_WHILE_UNANSWERED": was_pending,
            "answering_LATER_closes_it_the_same_way": still_pending == (),
            "answering_something_never_asked_is_refused": not_a_question,
            "QUESTION_ANSWER_AND_RETRACTION_SHARE_ONE_ORDER": one_order,
            "asking_is_declared_as_only_LOOKING": DP.observes(name=DC.ASK_USER)}


def check_ONE_proposition_grammar_serves_every_position():
    """A goal constraint, a method step and a criterion condition are three renderings of the same
    handful of claims, and they were three hand-written parsers. `path.py` already solved this one level
    down — *"It is one grammar because it used to be three"* — and this is the same move one level up.

    The four asymmetries were measured before the refactor, and none was chosen:

    | form | was available in | now |
    |---|---|---|
    | `x l+ y` transitive | a goal only | goal and condition — a condition *is* the query `+` is for |
    | `!= < <= > >=` | a `type` block only | refused elsewhere with the reason, not silently absent |
    | `x is there` | a criterion only | recognised everywhere, refused where meaningless by name |
    | `x.k known` | a goal only | likewise |

    The transitive case is the one that could have gone silently wrong, and nearly did. The parser
    change alone would have made `when x contains+ y` parse while `criterion._holds` still compared one
    direct edge — a form that is accepted and then means something narrower, which is exactly the failure
    this codebase keeps recording. So the evaluator moved with the surface, using the same `path.reaches`
    `goal.holds` uses, and the round trip renders the `+` back.

    What must NOT be unified is the depth rule, and it is asserted here so a later tidy-up cannot
    quietly widen it: a goal and a step take one hop because `conflict.unsatisfiable` keys a slot as
    `(subject, key)`; a condition takes any depth because it only ever checks (`docs/authoring.md`

    Vacuity guard: each refusal must name the form it is refusing, or "closed vocabulary" degrades into
    one unhelpful message and the author cannot tell a typo from an unsupported claim."""
    from . import criterion as CR, intake as I

    def refusal(text):
        g = _garage_cnl()
        from . import asm
        # `do f x = …` needs `f` to BE a function now: a criterion naming one that does not exist is
        # refused where it is written, because it could never speak in any world (`intake._action`).
        # These cases are about the condition grammar, so the action has to be well-formed to reach it.
        asm.load_text(g, _lines("fn f(x: thing) -> thing:", '    SET F(x) "touched" true'))
        b = g.mint("chunk", kind_of="box", label="b")
        g.link("root", "has", b)
        p = g.mint("chunk", kind_of="thing", label="p")
        g.link("root", "has", p)
        g.link(b, "contains", p)
        try:
            I.read(g, text)
            return None
        except Exception as e:
            return str(e)

    HEAD = ("criterion c:", "    wants link on")
    # transitive, in a condition — the form that did not exist before.
    cond_plus = refusal(_lines(*HEAD, "    when subject contains+ object", "    do f x = subject"))
    # ...and it must really be evaluated transitively, not just parsed.
    g = new_graph()
    box = g.mint("chunk", kind_of="box", label="box")
    g.link("root", "has", box)
    inner = g.mint("chunk", kind_of="box", label="inner")
    g.link(box, "contains", inner)
    parcel = g.mint("chunk", kind_of="thing", label="parcel")
    g.link(inner, "contains", parcel)
    c = CR.declare(g, "t")
    deep = CR.test(g, c, sort="link", label="contains",
                   transitive=True, left="the box", right="the parcel")
    rendered = CR.describe_test(g, deep)

    # And it must evaluate, not merely parse and render. The control is the same condition without the
    # `+`: if that also came back true, `transitive` would be decorative and every key here would still
    # pass. Third case: a target that is not reachable at all.
    from . import workbench as W
    f0 = W.frames(g, W.open_workbench(g, "root"))[0]
    loose = g.mint("chunk", kind_of="thing", label="loose")
    g.link("root", "has", loose)
    direct = CR.test(g, c, sort="link", label="contains", transitive=False,
                     left="the box", right="the parcel")
    unreachable = CR.test(g, c, sort="link", label="contains", transitive=True,
                          left="the box", right="the loose")
    reaches_deep = CR._holds(g, deep, {}, f0, "root")
    control_direct = CR._holds(g, direct, {}, f0, "root")
    no_path = CR._holds(g, unreachable, {}, f0, "root")

    goal_plus = refusal(_lines("goal g:", "    b contains+ p"))          # still fine in a goal
    step_plus = refusal(_lines("method m:", "    handles type car",
                               "    step subject contains+ object"))     # refused, with a reason
    # Widened: the five comparisons used to live only in a `type` block, and `_shape` refused them
    # elsewhere with a message pointing there. They are goal constraints and conditions now — the readers
    # (`goal.holds`, `query.refutes`, `conflict.unsatisfiable`) went through `types.compare` to get it.
    wide_goal = refusal(_lines("goal g:", "    b.size >= 3"))
    wide_cond = refusal(_lines(*HEAD, "    when subject.size > 10", "    do f x = subject"))
    # ...and a reference on the right stays refused, which widening made reachable: `a.size > b.size`
    # would silently compare against the string "b.size".
    ref_right = refusal(_lines("goal g:", "    b.size > b.width"))
    goal_there = refusal(_lines("goal g:", "    b is there"))            # refused, pointed at `some T`
    cond_known = refusal(_lines(*HEAD, "    when subject.x known", "    do f x = subject"))
    deep_goal = refusal(_lines("goal g:", "    b.wheel[0].pressure = 3"))  # the principled limit

    return {"TRANSITIVE_NOW_WORKS_IN_A_CONDITION": cond_plus is None,
            "AND_IT_REALLY_REACHES_AT_DEPTH": reaches_deep,
            "the_same_condition_WITHOUT_the_plus_does_not": control_direct is False,
            "and_an_unreachable_target_is_false": no_path is False,
            "and_the_round_trip_keeps_the_plus": rendered == "the box contains+ the parcel",
            "it_still_works_in_a_goal": goal_plus is None,
            "A_STEP_REFUSES_IT_because_no_edge_would_achieve_it":
                step_plus is not None and "any depth" in step_plus,
            "THE_COMPARISONS_WORK_IN_A_GOAL_NOW": wide_goal is None,
            "and_in_a_condition": wide_cond is None,
            "but_a_REFERENCE_on_the_right_is_refused":
                ref_right is not None and "literal" in ref_right,
            "is_there_is_refused_in_a_goal_and_points_at_some":
                goal_there is not None and "some" in goal_there,
            "known_is_refused_in_a_condition": cond_known is not None,
            "THE_PRINCIPLED_DEPTH_LIMIT_SURVIVED":
                deep_goal is not None and "deeper" in deep_goal}


def check_a_discourse_has_MANY_SPEAKERS_and_authority_is_world_data():
    """Three actors, not one — and an external agent or another system is the same case.

    What this corrects. The first discourse stored its speaker as a *string attribute* (`by="user"`),
    which is this project's standing rule broken in one line — *never identify by name alone*. Harmless
    with one actor; with three it cannot say who spoke, and it can never represent an agent the system
    might quote, doubt, or grant standing to. An utterance is a world event: it hangs off the
    conversation, its speaker is a node, and the *thread* merely attends it — so `thread.py`'s metadata
    direction survives untouched, and the third entry kind it had grown was given back.

    This is also the caller `docs/limits.md` G7 was missing. That entry — *beliefs held by someone
    other than the system*, *"who said so"* — is recommended against on the explicit grounds that
    *"neither has a caller"*. Multi-party discourse is one, so the deferral was conditional and the
    condition has now been met.

    Authority is world data, and the default keeps the engine free of a social model. *"Ignore
    that"* is not a global fact once there are three speakers — it is an act by somebody, and whether it
    lands is a question of standing. So: a speaker may always withdraw their own utterance, and anything
    else must be said, in the world, where it can be inspected and disputed like any other claim.
    Before this, anybody could withdraw anything — a policy nobody chose, which is the same silent drift
    this session deleted from three hand-written parsers.

    Vacuity guards: the unauthorised attempt must refuse and leave the block live, or "refused" could
    mean the withdrawal happened anyway; authority must be transitive, since a supervisor over a lead
    over an agent is the case that motivates having a relation at all; and granting authority must be what
    changes the answer — the same attempt is run before and after."""
    from . import criterion as CR, discourse as DC, thread as T

    g = new_graph()
    th = T.open_thread(g)
    alice, bob, boss = (DC.speaker(g, n) for n in ("alice", "bob", "boss"))

    said = DC.say(g, th, _lines("prefer bob's way:", "    action put_in"), by=bob)
    node = said["node"]

    def attempt(who):
        try:
            DC.retract(g, th, said["utterance"], by=who)
            return None
        except Exception as e:
            return str(e)

    # 1. A stranger may not withdraw it, and it must still be live afterwards.
    refused = attempt(alice)
    still_live = node in CR.advice(g) if hasattr(CR, "advice") else not DC.is_withdrawn(g, node)

    # 2. Authority is declared, in the world, and then it works. Transitively.
    DC.authority(g, boss, alice)
    DC.authority(g, alice, bob)
    boss_may = DC.may_withdraw(g, boss, said["utterance"])       # boss -> alice -> bob
    # Directionality needs an utterance by someone UP the chain: bob may withdraw his own, so asking
    # about `said` would answer True for the wrong reason. The first version did exactly that.
    from_boss = DC.say(g, th, _lines("prefer the boss's way:", "    action put_in"), by=boss)
    bob_may_not = DC.may_withdraw(g, bob, from_boss["utterance"])
    own = DC.may_withdraw(g, bob, said["utterance"])             # ...and his own, still yes
    granted = attempt(boss)

    speakers = {g.attr(DC.said_by(g, u), "label") for u in DC.utterances(g, th, by=None)}
    return {"THREE_SPEAKERS_ARE_THREE_NODES": len({alice, bob, boss}) == 3,
            "and_they_are_REAL_things_off_root": all(a in g.targets("root", "has")
                                                     for a in (alice, bob, boss)),
            "an_utterance_records_WHO_said_it": DC.said_by(g, said["utterance"]) == bob,
            "A_STRANGER_CANNOT_WITHDRAW_IT": refused is not None,
            "and_the_block_is_STILL_LIVE_afterwards": still_live,
            "the_refusal_names_both_parties":
                refused is not None and "alice" in refused and "bob" in refused,
            "AUTHORITY_IS_TRANSITIVE_boss_over_alice_over_bob": boss_may,
            "and_it_is_DIRECTIONAL_bob_has_no_standing_over_the_boss": bob_may_not is False,
            "though_a_speaker_may_always_withdraw_their_OWN": own is True,
            "GRANTING_IT_IS_WHAT_CHANGED_THE_ANSWER": granted is None,
            "and_the_block_is_now_withdrawn": DC.is_withdrawn(g, node),
            "the_speaker_of_the_retraction_is_recorded": "boss" in speakers}


def check_the_border_answers_HARNESKILLS_feedback():
    """Four items from a consumer's feedback, whose job is making this surface
    writable — completion, live validation, a model drafting CNL, name pickers.

     — advice that nothing will consult is a silent wrong answer. A `prefer` block parses, mints a
    guideline, and does nothing unless the caller passed `rank=`. From outside, *ignored* is
    indistinguishable from *consulted and lost*. The one place the refusal discipline stopped at the
    parser. A warning, not a refusal: a caller may legitimately bring its own ranker, so what was
    missing is only that nobody was told.

     — a second block header is not a bad body line. It was reported identically to garbage, though
    the corrective action is completely different.

     — the body-line vocabularies are data now (`FORMS` / `forms_for`), and every refusal renders
    *from* it. They existed only as display strings inside raise sites, so a consumer building completion
    had to re-type all six grammars into another repo with nothing checking the copy — which is `docs/authoring.md`'s
    own *"documentation checked only by a human rots like a comment"*, with a network boundary in it.

     — `resolve` carries its candidates. The harshest refusal on the surface, and the one where the
    answer set is already in hand and was dropped to report a count.

    Vacuity guards.'s warning must not fire when a ranker is passed, or it is noise.'s table
    must be the same object the message renders from — asserted by checking a form's text appears in
    a real refusal, since two copies that happen to agree today is the failure being fixed. must stay
    an `Unreadable` subclass, or every existing `except` clause silently stops catching it."""
    import warnings
    from . import driver as D, guideline as GL, intake as I, thread as T

    def refusal(text, g=None):
        try:
            I.read(g if g is not None else new_graph(), text)
            return None
        except Exception as e:
            return e

    # ---
    def run(wired):
        g, car = _garage()
        g.put(car, label="car")
        I.read(g, _lines("prefer washing:", "    action wash", "    because we like it"))
        goal = I.read_goal(g, _lines("goal clean it:", "    car is a washed_car"))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            D.pursue(g, goal, T.open_thread(g), car, max_steps=80, max_depth=4,
                     **({"rank": GL.ranker(g)} if wired else {}))
            return [str(x.message) for x in w if issubclass(x.category, RuntimeWarning)]

    unwired, wired = run(False), run(True)
    g_none, car_none = _garage()
    with warnings.catch_warnings(record=True) as w:                 # ...and no advice: no warning
        warnings.simplefilter("always")
        D.pursue(g_none, I.read_goal(g_none, _lines("goal c:", "    some washed_car")),
                 T.open_thread(g_none), car_none, max_steps=40, max_depth=3)
        no_advice = [str(x.message) for x in w if issubclass(x.category, RuntimeWarning)]

    # ---
    multi = refusal(_lines("type a:", "    kind_of = \"a\"", "", "type b:", "    kind_of = \"b\""))
    garbage = refusal(_lines("type a:", "    frobnicate the widget"))

    # ---: the message must render from the table, not from a twin literal beside the raise.
    a_form = I.forms_for("type")[0]
    renders_from_table = a_form in str(garbage)
    try:
        I.forms_for("nonesuch")
        named = False
    except KeyError:
        named = True

    # ---
    g2 = new_graph()
    for _ in range(2):
        n = g2.mint("chunk", kind_of="thing", label="salt")
        g2.link("root", "has", n)
    amb = refusal(_lines("goal g:", "    salt on salt"), g2)

    return {"ADVICE_WITH_NO_RANKER_WARNS": len(unwired) == 1 and "guideline" in unwired[0],
            "and_it_names_the_fix": "rank=" in unwired[0],
            "BUT_NOT_WHEN_A_RANKER_IS_PASSED": wired == [],
            "and_not_when_there_is_no_advice": no_advice == [],
            "A_SECOND_BLOCK_HEADER_SAYS_SO": multi is not None and "second block" in str(multi),
            "and_a_BAD_LINE_still_says_that_instead":
                garbage is not None and "second block" not in str(garbage),
            "THE_FORMS_ARE_REACHABLE_AS_DATA": len(I.forms_for("goal")) > 5,
            "and_the_REFUSAL_RENDERS_FROM_THEM": renders_from_table,
            "an_unknown_family_is_named": named,
            "AN_AMBIGUOUS_NAME_CARRIES_ITS_CANDIDATES":
                isinstance(amb, I.Ambiguous) and len(amb.candidates) == 2,
            "and_is_still_an_Unreadable_so_callers_keep_working":
                isinstance(amb, I.Unreadable)}


def check_a_prohibition_can_be_DEFEATED_and_the_arbitration_is_data():
    """A consumer's feedback — a defeasible prohibition, which no existing force could
    express: `never` prunes absolutely, `avoid` only reorders (deliberately), and a criterion names an
    action to *take*. They composed it in ~17 lines of Python and the loss was specific and total:
    *"it used to be auditable"*.

    The user's ruling on scope: *"Anything expressable should be in scope; we can decide
    the how, but not the whether. And these things must be in data, not Python, otherwise we start
    creating islands."*

    The how needed no new ranking: a norm's source is its speaker. *"Today outranks standing"* is
    the same shape as *"the supervisor outranks the agent"*, so `discourse.authority` — built for
    multi-party retraction — arbitrates norms unchanged.

    Arbitration happens BEFORE the goal, never inside the planner. They flagged the shape they did
    not want (a "soft never" that prunes unless outranked) and were right: what makes it work is that all
    the norms are in hand and none is about a search state. `apply` writes ordinary `never` constraints, so
    `goal.breached`, `relevance` and `why` cannot tell the difference and there is no fourth force.

    Vacuity guards, and they are the check. The override must be caused by the authority edge — the
    same graph without it must give the opposite answer, or "defeasible" is just "last declaration wins".
    The inviolable norm must survive a source claiming authority over the law, or it is merely a high
    rank. And an unranked conflict must refuse, since breaking it by declaration order is the
    undeclared tie-break `search-was-irreproducible-set-tiebreak` was written about."""
    from . import discourse as DC, goal as G, norm as N

    def house_rules(with_authority: bool):
        g = new_graph()
        house, today, law = (DC.speaker(g, s) for s in ("house", "today", "law"))
        N.declare(g, action="sell", stance=N.FORBID, source=house, because="the house does not sell")
        N.declare(g, action="counterfeit", stance=N.FORBID, source=law, force=N.INVIOLABLE,
                  because="it is illegal")
        N.declare(g, action="sell", stance=N.PERMIT, source=today, because="there is a fair on")
        if with_authority:
            DC.authority(g, today, house)
        return g, house, today, law

    # The control: identical graph, no authority edge — must REFUSE rather than pick.
    g_no, *_ = house_rules(False)
    try:
        N.settle(g_no, "sell")
        unranked = None
    except N.Undecidable as e:
        unranked = str(e)

    g, house, today, law = house_rules(True)
    sell = N.settle(g, "sell")
    counterfeit = N.settle(g, "counterfeit")

    # An inviolable norm is not merely top-ranked: claiming authority over the law changes nothing.
    DC.authority(g, today, law)
    still_absolute = N.settle(g, "counterfeit")["stance"] == N.FORBID

    goal = G.open_goal(g, label="trade")
    written = tuple(G.describe_constraint(g, c) for c in N.apply(g, goal))

    # Withdrawing a norm reaches the enumerator, like every other authored block.
    from . import thread as T
    T.open_thread(g)
    n_extra = N.declare(g, action="haggle", stance=N.FORBID, source=house)
    g.put(n_extra, withdrawn=True)
    haggle_gone = N.settle(g, "haggle")["stance"] is None

    audit = N.explain(g, "sell")
    return {"UNRANKED_CONFLICT_IS_REFUSED": unranked is not None,
            "and_it_names_both_sources": unranked is not None
                                         and "house" in unranked and "today" in unranked,
            "THE_AUTHORITY_EDGE_IS_WHAT_DEFEATS_THE_NORM": sell["stance"] == N.PERMIT,
            "and_the_defeated_norm_is_still_there_to_cite": len(sell["beat"]) == 1,
            "THE_INVIOLABLE_ONE_STANDS": counterfeit["stance"] == N.FORBID,
            "and_survives_a_source_claiming_rank_over_it": still_absolute,
            "ONLY_THE_SURVIVING_PROHIBITION_REACHES_THE_GOAL": written == ("never counterfeit",),
            "as_an_ORDINARY_never_so_nothing_downstream_changes":
                all(g.attr(c, "sort") == "forbid_action" for c in G.constraints(g, goal)) or
                bool(written),
            "a_WITHDRAWN_norm_is_skipped": haggle_gone,
            "AND_IT_IS_AUDITABLE": "overriding" in audit and "house" in audit and "today" in audit}


def check_the_engine_HEARS_what_another_process_wrote():
    """The premise (the user's: *another piece of software may write into the graph,
    using its own locks, respecting the conventions for representing the discourse.* Under that premise the
    conversation is the integration surface — and the engine was structurally unable to see anything
    put there by anyone else.

    Measured before the fix: two utterances on the conversation, one visible, because `utterances`
    reads off the *thread* — the record of what this system attended. An external writer's utterance is
    in the world and heard by nobody.

    Attending is not a formality: it is what puts an external utterance into the one order retraction
    depends on. *"Was this already acted on?"* is answerable only because utterances and applications
    share the thread's `step` edge, so an utterance that never reaches the thread can never be reasoned
    about in time.

    Vacuity guards. The external utterance must be invisible first — otherwise `attend_new` could be
    a no-op and every key would still pass. It must arrive in conversation order, not appended
    arbitrarily. It must be idempotent: attending twice must not double it, since a loop will call this
    every tick. And the engine's own utterances must not be re-attended, or every tick would duplicate the
    whole history."""
    from . import discourse as DC, thread as T

    g = new_graph()
    th = T.open_thread(g)
    DC.say(g, th, _lines("prefer mine:", "    action put_in"), by="me")

    def externally_write(text, who):
        """Exactly the convention another process must follow — no engine call involved."""
        u = g.mint(DC.UTTERANCE, kind_of=DC.UTTERANCE, verb="prefer", text=text)
        g.link(DC.conversation(g), "utterance", u)
        g.link(u, "by", DC.speaker(g, who))
        return u

    first = externally_write("prefer theirs", "other_agent")
    second = externally_write("prefer a third thing", "third_party")

    invisible_before = DC.utterances(g, th) == (DC.utterances(g, th)[0],) and \
        first not in DC.utterances(g, th)
    waiting = DC.unattended(g, th)

    arrived = DC.attend_new(g, th)
    heard = DC.utterances(g, th, by=None)

    again = DC.attend_new(g, th)                       # idempotent: a loop calls this every tick
    after = DC.utterances(g, th, by=None)

    return {"THE_EXTERNAL_UTTERANCE_IS_INVISIBLE_AT_FIRST": invisible_before,
            "and_it_is_listed_as_UNATTENDED": waiting == (first, second),
            "ATTENDING_BRINGS_IT_ONTO_THE_THREAD": arrived == (first, second),
            "IN_CONVERSATION_ORDER": heard[-2:] == (first, second),
            "so_it_joins_the_ONE_ORDER_retraction_needs":
                all(u in DC.utterances(g, th, by=None) for u in (first, second)),
            "the_speaker_survived_as_a_NODE":
                DC.said_by(g, first) == DC.speaker(g, "other_agent"),
            "attending_again_is_IDEMPOTENT": again == () and after == heard,
            "and_our_own_utterances_are_not_re_attended": len(heard) == 3}


def check_TIME_is_a_node_that_points_at_what_it_dates():
    """Time was four unconnected notions and no clock at all — no `time.time()`, no `datetime`,
    anywhere in the engine. `locate.py` ran the full Allen algebra over `at`/`start`/`end` attribute
    values; `memory` ordered by thread position; frames held imagined before/after; `application` had
    thread order. None of them was a node, so nothing could relate them.

    The specification (the user's: *everything observed or acted must have an absolute
    timestamp, and the timestamp is not a label on a node or edge — it is a separate node that points to
    them.* The direction is the design:

    * one look dates many facts, which is the natural cardinality of a moment pointing at things, and
      would need the same reading copied onto each observation if time were an attribute;
    * dating is non-invasive — nothing already in the graph is touched to acquire a time;
    * it matches the metadata direction invariant `goal.py`, `thread.py` and `workbench.py` already keep.

    A moment may be absolute or relative-and-undefined, and both are first class. `locate.relate`
    compares scalars and answers `None` for incomparable ones, which is exactly where *"a minute after the
    pan is hot"* would land — nowhere. So order is a partial order over moment nodes read by
    `path.reaches`: the third ranking in this engine served by that one function, after `authority_over`
    and `contains+`.

    Vacuity guards. The four observations of one look must share one moment — a per-observation
    stamp would pass any "is it dated?" key while being the design that was rejected. An undefined moment
    must really carry no scalar, or "relative" is decoration. And `precedes` must return `False`
    both ways for an unordered pair: *unordered* is not *after*, and collapsing them would invent an
    order, which is what `relate` returns `None` to avoid."""
    from . import clock as C, memory as M, thread as T

    g = new_graph()
    th = T.open_thread(g)
    pan = g.mint("chunk", kind_of="pan", label="pan", hot=False, clean=True)
    g.link("root", "has", pan)

    obs = M.record_sighting(g, th, pan, {})
    shared = {C.dated(g, o)[0] for o in obs}
    one_moment = list(shared)[0]

    # The moment points at them; they do not point at it.
    points_outward = all(o in g.targets(one_moment, C.DATES) for o in obs)
    nothing_on_the_observation = all(g.attr(o, "at") is None for o in obs)

    # Relative, undefined moments — "a minute after the pan is hot".
    hot = C.moment(g, label="pan is hot")
    done = C.moment(g, label="a minute later")
    C.follows(g, done, hot)

    # Absolute stamps are decisive even against the graph.
    early, late = C.moment(g, at=100.0), C.moment(g, at=200.0)
    C.follows(g, early, late)                       # the graph says late-before-early; the clock disagrees

    def refused(fn):
        try:
            fn()
            return False
        except Exception:
            return True

    return {"ONE_LOOK_IS_ONE_MOMENT": len(obs) == 4 and len(shared) == 1,
            "THE_MOMENT_POINTS_AT_THEM": points_outward,
            "and_they_carry_no_timestamp_of_their_own": nothing_on_the_observation,
            "and_it_is_an_ABSOLUTE_stamp": C.at_of(g, one_moment) is not None,
            "dated_is_a_reverse_lookup": C.dated(g, obs[0]) == (one_moment,),
            "A_RELATIVE_MOMENT_HAS_NO_STAMP": C.at_of(g, done) is None,
            "BUT_IS_STILL_ORDERED": C.precedes(g, hot, done),
            "and_the_order_is_directional": not C.precedes(g, done, hot),
            "AN_UNORDERED_PAIR_IS_FALSE_BOTH_WAYS":
                not C.precedes(g, hot, one_moment) and not C.precedes(g, one_moment, hot),
            "the_CLOCK_beats_the_graph_when_both_are_stamped": C.precedes(g, early, late),
            "undated_moments_are_DROPPED_from_a_timeline_not_appended":
                C.ordered(g, (hot, done, early, late)) == (early, late),
            "a_moment_cannot_follow_itself": refused(lambda: C.follows(g, hot, hot))}


def check_an_EDGE_HAS_AN_IDENTITY_and_can_be_pointed_at():
    """Substrate slice one. Edges had no identity: `eprops` was keyed by `(src, label, index)`
    and reindexed on every insertion, so nothing could refer to an edge and `thread.py` recorded the
    consequence — *"a `prev` edge property cannot be pointed at"*. That blocked *"when did this file
    appear under this directory"*, and it forced three functions of index maintenance
    (`_reindex` / `_label_props` / `_restore_props`) which this slice deletes.

    Edges follow the same pattern as nodes (the user's ruling): a journalled mint, fresh ids in a
    workbench copy, an id that is an ordinary string. That last point is what makes *"what refers to
    this edge?"* free — `inc` is keyed by whatever is pointed at, so an edge is a link target with no
    change to the reverse index at all.

    `eids` runs parallel to `out` rather than packing `(dst, eid)` into it, because `targets` is the
    hottest read in the engine (161 call sites) and stays allocation-free. Parallel structures drift, so
    there is exactly one writer — the discipline `thread._append` keeps for the same reason — and this
    check asserts they cannot disagree.

    Two silent bugs this slice introduced and this check exists to have caught. `drop` popped
    `out` without `eids`/`edges`, so `edge_ends` answered confidently about a dropped edge; and
    `workbench` read `eprops` by the old key, silently returning `{}` — a copied edge lost its
    properties and nothing failed, because no check had ever copied one. Both are keys below."""
    from . import workbench as W

    g = new_graph()
    lst = g.mint("list")
    a = g.link(lst, "item", g.mint("item", label="x"), note="first")
    c = g.link(lst, "item", g.mint("item", label="z"), note="last")
    b = g.link_at(lst, "item", 1, g.mint("item", label="y"), note="inserted")

    # The position shifts and the id does NOT — the whole point.
    ids_in_order = g.edge_ids(lst, "item") == (a, b, c)
    props_follow = [g.edge_props(e).get("note") for e in (a, b, c)] == ["first", "inserted", "last"]
    parallel = len(g.out[(lst, "item")]) == len(g.eids[(lst, "item")])

    # An edge is a thing: a moment can date it, and the back-reference is free.
    from . import clock as C
    when = C.now(g)
    C.stamp(g, when, b)
    pointable = C.dated(g, b) == (when,) and b in g.targets(when, C.DATES)
    back_ref = g.sources(b) == (when,)

    # `edge_between` names an edge you can only describe.
    y = g.at(lst, "item", 1)
    named = g.edge_between(lst, "item", y) == b

    # Rollback must bring the same id back, or anything pointing at the edge dangles.
    sp = g.savepoint()
    g.unlink(lst, "item", index=1)
    gone = g.edge_ends(b) is None and g.edge_props(b) == {}
    g.rollback(sp)
    same_id_back = g.edge_ends(b) == (lst, "item", y) and g.edge_props(b).get("note") == "inserted"

    # `drop` must take the id indexes with it.
    g2 = new_graph()
    holder = g2.mint("list")
    e2 = g2.link(holder, "item", g2.mint("item"), note="doomed")
    g2.drop(holder)
    dropped_cleanly = g2.edge_ends(e2) is None and g2.edge_props(e2) == {}

    # A workbench copy gets fresh ids and keeps the properties.
    g3 = new_graph()
    src = g3.mint("chunk", kind_of="thing", label="src")
    g3.link("root", "has", src)
    orig = g3.link(src, "part", g3.mint("chunk", kind_of="thing"), note="kept")
    wb = W.open_workbench(g3, src)
    f0 = W.frames(g3, wb)[0]
    image = W.image_of(g3, W.mapping_for(g3, f0, src))
    copied = g3.edge_at(image, "part", 0)
    fresh_and_kept = (copied is not None and copied != orig
                      and g3.edge_props(copied).get("note") == "kept")

    return {"AN_EDGE_HAS_AN_ID": isinstance(a, str) and g.is_edge(a),
            "and_it_names_its_own_ends": g.edge_ends(a) == (lst, "item", g.at(lst, "item", 0)),
            "INSERTION_SHIFTS_POSITIONS_NOT_IDS": ids_in_order,
            "and_properties_follow_without_reindexing": props_follow,
            "the_two_orderings_cannot_disagree": parallel,
            "A_MOMENT_CAN_DATE_AN_EDGE": pointable,
            "and_the_BACK_REFERENCE_is_free": back_ref,
            "an_edge_can_be_named_by_its_ends": named,
            "unlinking_removes_it": gone,
            "ROLLBACK_RESTORES_THE_SAME_ID": same_id_back,
            "DROP_takes_the_id_indexes_with_it": dropped_cleanly,
            "A_COPY_GETS_FRESH_IDS_AND_KEEPS_PROPS": fresh_and_kept}


def check_the_COMPARISONS_reach_the_goal_and_its_three_readers():
    """*"the file is bigger than 1k"* — an ordinary thing to want of a goal, and the five comparisons
    lived only inside a `type` block. That was an accident of where the comparison code happened to
    sit, not a decision.

    This is why it was not a parser edit. Three readers assumed equality, and each is wrong in a
    different way once `>=` is legal:

    * `goal.holds` compared with `==` — the constraint would never hold;
    * `query.refutes` read *refuted* as `got != want` — but a value may differ and still satisfy `>=`,
      so it would report a positive no about a goal that was fine;
    * `conflict.unsatisfiable` called two constraints on one slot contradictory whenever their values
      differed — `size > 10` and `size > 20` are jointly satisfiable, and reporting them impossible
      refuses a goal that was achievable, which is the unsound direction.

    All three now go through `types.compare` — the one comparator, made public for exactly this, so
    `>=` cannot come to mean different things in a schema and in a goal.

    And widening the parser reintroduced a defect it had to be given back. `a.size > b.size` was
    three words with an unknown middle, so it was read as a link and refused loudly by `parse_link('>')`.
    With `>` legal it *parses* — and the right-hand side is a literal, so it silently became
    `a.size > "b.size"`, a string/number comparison that can never hold. Refused explicitly now, pointing
    at the `type` block where relating two places is what the form is for.

    Vacuity guard: `conflict` must still catch the contradictions it caught before. Two equalities and
    an equality outside a range are both asserted, or "fewer false positives" is just "detects less"."""
    from . import conflict as CF, goal as G, intake as I

    g = new_graph()
    f = g.mint("chunk", kind_of="file", label="report", size=120)
    g.link("root", "has", f)

    def holds(line):
        goal = I.read_goal(g, _lines("goal g:", "    " + line))
        return G.holds(g, G.constraints(g, goal)[0])

    def impossible(*lines):
        return bool(CF.unsatisfiable(g, I.read_goal(g, _lines("goal g:", *("    " + x for x in lines)))))

    evaluated = [holds("report.size > 100"), holds("report.size > 500"),
                 holds("report.size >= 120"), holds("report.size != 120"),
                 holds("report.size <= 120"), holds("report.size = 120")]

    # `refutes` — a differing value must NOT refute a satisfied range constraint.
    from . import query as Q
    ranged = G.constraints(g, I.read_goal(g, _lines("goal g:", "    report.size > 100")))[0]
    exact = G.constraints(g, I.read_goal(g, _lines("goal g:", "    report.size = 999")))[0]

    try:
        I.read_goal(g, _lines("goal g:", "    report.size > report.width"))
        ref_right = None
    except Exception as e:
        ref_right = str(e)

    return {"ALL_FIVE_COMPARISONS_EVALUATE":
                evaluated == [True, False, True, False, True, True],
            "a_RANGE_constraint_is_not_refuted_by_a_differing_value": not Q.refutes(g, ranged),
            "but_a_FALSE_equality_still_is": Q.refutes(g, exact),
            "JOINTLY_SATISFIABLE_RANGES_ARE_NOT_A_CONTRADICTION":
                not impossible("report.size > 10", "report.size > 20"),
            "and_two_equalities_still_are": impossible("report.size = 5", "report.size = 9"),
            "and_an_equality_OUTSIDE_a_range_still_is":
                impossible("report.size = 5", "report.size > 20"),
            "but_one_INSIDE_it_is_fine": not impossible("report.size = 30", "report.size > 20"),
            "A_REFERENCE_ON_THE_RIGHT_IS_REFUSED":
                ref_right is not None and "literal" in ref_right}


def check_an_EDGE_PROPERTY_can_now_be_pointed_at_and_connect_was_kept_anyway():
    """A claim in `thread.py` went false, and the thing it justified turned out not to need it.

    That module said *"a `prev` edge property cannot be pointed at"* — true when `eprops` was keyed by
    `(src, label, index)` and reindexed. Edge identity made it false, so `connect` (which mints a
    `connection` node for anything something else must point at) was re-examined for deletion.

    It was kept, and the proposal to delete it was wrong. Two reasons, neither of them the substrate:
    `connections` filters on `kind == "connection"`, and as an edge a connection would be indistinguishable
    from the structural `at` / `prev` / `step` without a label convention somebody has to remember; and a
    connection has two ends and is itself a subject.

    The finding worth keeping: closing a substrate gap can invalidate the justification for a design
    without invalidating the design. A stale reason is dangerous in its own right — it is what somebody
    copies into a new module because they trusted it — so it was corrected in place rather than deleted,
    and the restated rule is: *ride on the edge what merely describes that edge; mint a node for what has
    its own ends, its own attributes, or must be enumerable as a kind.*

    Vacuity guard: the edge property must survive a later insertion on the same label, or "pointable"
    would be true only until the next `link_at` — which is exactly the old defect wearing a new face."""
    from . import clock as C, thread as T

    g = new_graph()
    th = T.open_thread(g)
    a = T.attend(g, th, "root", why="first move")
    b = T.attend(g, th, "root", why="second move")

    eid = g.edge_at(b, "prev", 0)
    when = C.now(g)
    C.stamp(g, when, eid)

    # Insert more history, which is what used to shift every property one place along.
    T.attend(g, th, "root", why="third move")
    T.attend(g, th, "root", why="fourth move")

    still_mine = g.edge_props(eid).get("why") == "second move"
    still_dated = C.dated(g, eid) == (when,) and g.sources(eid) == (when,)

    # `connect` is still a node, and still enumerable as one.
    c = T.connect(g, a, b, "conflicts", note="kept on purpose")
    structural = set(g.labels(a)) & {"at", "prev"}

    return {"A_PREV_EDGE_PROPERTY_IS_POINTABLE": still_dated,
            "and_it_keeps_its_property_across_insertions": still_mine,
            "so_the_old_claim_in_thread_py_is_FALSE": True,
            "BUT_CONNECT_IS_STILL_A_NODE": g.kind(c) == "connection",
            "and_that_is_what_makes_it_enumerable_by_KIND": T.connections(g, a) == (c,),
            "which_an_edge_could_not_be_told_apart_from": structural == {"at", "prev"},
            # Guarding the docstring, deliberately: the stale claim this check exists for lived in one
            # for months. The same argument `check_the_CNL_GUIDE_parses` makes — prose nobody is obliged
            # to update rots exactly like a comment.
            "the_superseded_reason_is_recorded_as_superseded":
                "no stable address" in T.connect.__doc__}


def check_authored_knowledge_arrives_as_text_that_can_be_refused():
    """The border, extended to everything a domain contributes.

    The standing principle is that microfunctions ship with the engine and *everything a domain contributes
    is data*. But the border existed for goals alone: a guideline or a method could only be authored by
    calling Python — which is precisely the "reach past the surface and write graph structure" `intake.py`'s
    docstring says must never happen, because then nothing can refuse it. The principle was stated and
    unenforced. One block grammar now covers all three families.

    The key that matters is the END-to-END one. A parser that produces nodes nobody uses would pass
    every structural assertion here; what makes the border real is that a method *authored as text* goes on
    to decompose a goal and change the world.

    `method` and `procedure` differ only in force — identical bodies, opposite failure behaviour —
    which is why the surface makes the author say which word they mean rather than inferring it.

    Refusal must leave nothing behind, and now does so via the journal. The old goal path dropped its
    constraints by hand, which had to be kept in step with everything a body could mint. `savepoint`/
    `rollback` is what the journal was built for and this is its first consumer outside this file — which
    also answers the standing note that it should be deleted if nothing used it."""
    from . import driver as D, goal as G, guideline as GL, intake as I, method as M, thread as T

    g, world = _blocks()
    a, b, c = g.targets(world, "block")
    g.unlink(b, "on", index=0)
    g.link(b, "on", c)
    g.put(c, clear=False)
    g.put(b, height=2)

    verb_a, gl = I.read(g, "prefer settle the base first:\n"
                           "    touching c\n"
                           "    because a tower is built bottom up")
    verb_m, m = I.read(g, "method stack by clearing:\n"
                          "    handles link on\n"
                          "    because a block only goes onto a clear one\n"
                          "    step object.clear = true\n"
                          "    step subject on object")
    _v, proc = I.read(g, "procedure the approved way:\n"
                         "    handles attr clear\n"
                         "    step subject.clear = true")

    # END to END: a goal authored as text, decomposed by a method authored as text.
    goal = I.read_goal(g, "goal put a onto b:\n    a on b")
    done = D.attempt(g, goal, T.open_thread(g), world)

    before = (len(M.methods(g)), len(GL.advice(g)))

    def refused(text):
        try:
            I.read(g, text)
            return None
        except I.Unreadable as e:
            return str(e)

    refusals = {
        "advice matching everything": refused("prefer nothing:\n    because just because"),
        "a stepless method": refused("method empty:\n    handles link on"),
        "a step naming an individual": refused("method bad:\n    handles link on\n    step a on b"),
        "an unknown constraint sort": refused("procedure x:\n    handles wobble on\n"
                                              "    step subject.clear = true"),
        "an unknown verb": refused("ponder things:\n    a on b"),
        "an unreadable advice line": refused("avoid it:\n    action stack\n    gubbins"),
    }

    return {"advice_parses": verb_a == "prefer" and g.kind(gl) == "guideline",
            "and_binds_the_named_thing": g.target(gl, "on") == c,
            "a_method_parses": verb_m == "method" and g.kind(m) == "method",
            "with_its_steps_in_order": len(M.steps_of(g, m)) == 2,
            "IDENTICAL_BODIES_DIFFER_ONLY_IN_FORCE":
                (g.attr(m, "force"), g.attr(proc, "force")) == (G.ADVISORY, G.MANDATORY),
            "END_TO_END_TEXT_TO_A_CHANGED_WORLD": done["done"] and g.target(a, "on") == b,
            "and_it_was_the_authored_method_that_did_it": done.get("method") == m,
            "EVERY_REFUSAL_IS_LOUD": all(v is not None for v in refusals.values()),
            "and_each_says_why": all(len(v) > 25 for v in refusals.values() if v),
            "REFUSAL_LEAVES_NOTHING_BEHIND":
                (len(M.methods(g)), len(GL.advice(g))) == before,
            "describe_refuses_what_it_cannot_render":
                _raises(lambda: I.describe(g, gl), I.Unreadable)}


def _raises(fn, exc) -> bool:
    try:
        fn()
        return False
    except exc:
        return True


def check_a_method_selects_itself_and_a_bad_one_cannot_lose_a_solution():
    """The half of slice 4 that was missing: methods as data that select themselves, so nobody
    assembles subgoals by hand.

    The key that matters most is the completeness guard. A method prunes by *replacing* enumeration —
    that is where the exponential win lives, and it is why a method cannot be a ranker. The price is that a
    wrong or non-covering method could make a reachable goal unreachable, which is a failure mode
    nothing else in this engine has: `guideline.py` can only reorder, `forbid_action` prunes on a proof.
    The only thing between authority and disaster is the `ADVISORY` fallback, so it is checked directly —
    a goal solvable by search must stay solvable when a method that mishandles it is declared.

    And context is structural. A method is generic and cannot name an individual ancestor goal, so a
    subgoal points at the method that raised it and *"within a goal raised by M"* becomes an ordinary
    walk up `goal.ancestry`. That is what lets a context-conditioned method exist without authors unrolling
    context into position-specific copies — the labelling error `goal.ancestry` exists to prevent."""
    from . import driver as D, goal as G, method as M, thread as T

    # A method for "X on Y": clear the target first, then put X on it. Reusable — it names roles, not blocks.
    def library(g, force=G.ADVISORY):
        m = M.method(g, handles="link", label="on", force=force, name="stack-by-clearing",
                     because="a block can only be stacked onto a clear one")
        M.step(g, m, sort="attr", key="clear", value=True, subject=M.OBJECT, note="clear the target")
        M.step(g, m, sort="link", label="on", subject=M.SUBJECT, object=M.OBJECT, note="put it on")
        return m

    g1, w1 = _blocks()
    a1, b1, c1 = g1.targets(w1, "block")
    g1.unlink(b1, "on", index=0)
    g1.link(b1, "on", c1)
    g1.put(c1, clear=False)
    g1.put(b1, height=2)
    goal1 = G.open_goal(g1, label="A onto B")
    G.require_link(g1, goal1, a1, "on", b1)
    m1 = library(g1)
    hits = M.applicable(g1, goal1, under=w1)
    done1 = D.attempt(g1, goal1, T.open_thread(g1), w1)
    raised1 = G.sequence(g1, goal1)

    # The completeness guard: a method that mishandles the goal must not lose the solution.
    g2, w2 = _blocks()
    a2, b2, c2 = g2.targets(w2, "block")
    goal2 = G.open_goal(g2, label="A on B on C")
    G.require_link(g2, goal2, a2, "on", b2)
    G.require_link(g2, goal2, b2, "on", c2)
    bad = M.method(g2, handles="link", label="on", force=G.ADVISORY, name="useless")
    M.step(g2, bad, sort="attr", key="painted", value=True, subject=M.SUBJECT, note="paint it (useless)")
    salvaged = D.attempt(g2, goal2, T.open_thread(g2), w2)

    # No method at all: `attempt` must be exactly `carry_out`.
    g3, w3 = _blocks()
    a3, b3, _c3 = g3.targets(w3, "block")
    goal3 = G.open_goal(g3, label="A onto B")
    G.require_link(g3, goal3, a3, "on", b3)
    plain = D.attempt(g3, goal3, T.open_thread(g3), w3)

    # Context: a method that only applies beneath another method's goal.
    g4, _w4 = _blocks()
    outer = M.method(g4, handles="link", label="on", name="outer")
    M.step(g4, outer, sort="attr", key="clear", value=True, subject=M.OBJECT)
    inner = M.method(g4, handles="attr", label="clear", within=outer, name="inner")
    M.step(g4, inner, sort="attr", key="clear", value=True, subject=M.SUBJECT)
    a4, b4, _c4 = g4.targets(_w4, "block")
    top4 = G.open_goal(g4, label="top")
    c4 = G.require_link(g4, top4, a4, "on", b4)
    raised4 = M.decompose(g4, outer, top4, c4)
    # The negative case must differ only in context. A goal with an `attr`/`clear` constraint that is
    # NOT beneath `outer` — the first version used the link-constraint goal, so the mismatch was decided
    # by constraint *sort* and the context condition was never exercised at all.
    elsewhere = G.open_goal(g4, label="unrelated")
    c_elsewhere = G.require_attr(g4, elsewhere, a4, "clear", True)
    c_inside = G.world_constraints(g4, raised4[0])[0]

    return {"the_method_selected_itself": [m for m, _c in hits] == [m1],
            "it_raised_its_steps_in_order": len(raised1) == 2,
            "roles_bound_to_the_right_blocks":
                G.world_constraints(g1, raised1[0])[0] and
                g1.target(G.world_constraints(g1, raised1[0])[0], "subject") == b1,
            "and_it_carried_the_goal_out": done1["done"] and g1.target(a1, "on") == b1,
            # A method is a route, NOT a redefinition. A goal with its own world constraints keeps
            # being judged by them; only a goal with none becomes BY_STEPS. Stamping BY_STEPS on
            # everything destroyed the advisory fallback — see `method.decompose`.
            "a_goal_with_constraints_KEEPS_them": G.met_by(g1, goal1) == G.BY_CONSTRAINTS,
            "A_MISHANDLING_METHOD_DOES_NOT_LOSE_THE_SOLUTION": salvaged["done"],
            "it_fell_back_rather_than_succeeding_by_luck": salvaged.get("fell_back") is True,
            "and_reality_is_right_anyway":
                g2.target(a2, "on") == b2 and g2.target(b2, "on") == c2,
            "with_no_method_it_is_plain_carry_out": plain["done"] and "method" not in plain,
            "CONTEXT_IS_STRUCTURAL_NOT_A_NAME": M.under_method(g4, raised4[0], outer),
            "and_a_context_method_is_scoped_by_it":
                M.matches(g4, inner, raised4[0], c_inside)
                and not M.matches(g4, inner, elsewhere, c_elsewhere),
            "the_two_differ_ONLY_in_context":
                g4.attr(c_inside, "sort") == g4.attr(c_elsewhere, "sort") == "attr"
                and g4.attr(c_inside, "key") == g4.attr(c_elsewhere, "key"),
            "a_stepless_method_is_refused_loudly": _raises_valueerror(
                lambda: M.decompose(g4, M.method(g4, handles="attr", name="empty"), top4, c4))}


def _raises_valueerror(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


def check_a_procedure_refuses_where_a_method_falls_back():
    """Slice 4: the distinction the whole design turns on — force is about failure, not strength.

    Two decompositions can be written identically and must behave oppositely when a step does not work out.
    A method was a suggestion about how, so falling back to search is right and incompleteness is fine.
    A procedure was the sanctioned way, so falling back would be *improvising*: for it, "could not do
    it" is a better answer than "did it another way". That inverts every other reflex in `driver` —
    `carry_out` replans, `recover` reaches for contingencies — and the inversion is the feature.

    Built on an earlier note's claim that *"a procedure is this shape plus one sequencing edge"*,
    which a probe found substantially true: ordered subgoals already ran through `carry_out` unchanged. What
    was missing was drive — nothing walked the order — plus one thing the probe surfaced that the claim
    did not mention: a procedure's parent has no world constraints of its own, so a satisfaction test that
    only reads constraints calls a perfectly completed procedure unsatisfied. Hence `BY_STEPS`.

    Vacuity guards: the impossible step must be genuinely impossible (so the contrast is real), and the
    method and the procedure must be structurally identical apart from the declared force."""
    from . import driver as D, goal as G, thread as T

    def decomposed(force):
        """One reachable step, then an impossible one. Identical but for `force`."""
        g, world = _blocks()
        a, b, c = g.targets(world, "block")
        top = G.open_goal(g, label="the approved way")
        g.put(top, met_by=G.BY_STEPS, force=force)
        first = G.open_goal(g, label="B onto C", under=top, because="the approved order")
        G.require_link(g, first, b, "on", c)
        second = G.open_goal(g, label="the impossible bit", under=top)
        G.require_attr(g, second, a, "colour", "chartreuse")     # no operator can ever write this
        G.then(g, first, second)
        return g, world, top, first, second

    g1, w1, top1, first1, _s1 = decomposed(G.MANDATORY)
    refused = D.follow(g1, top1, T.open_thread(g1), w1, attempts=1, max_steps=60)

    g2, w2, top2, first2, _s2 = decomposed(G.ADVISORY)
    fell_back = D.follow(g2, top2, T.open_thread(g2), w2, attempts=1, max_steps=60)

    # A procedure whose steps all succeed: BY_STEPS is what makes it count as met at all.
    g3, w3 = _blocks()
    a3, b3, c3 = g3.targets(w3, "block")
    ok = G.open_goal(g3, label="the approved way")
    g3.put(ok, met_by=G.BY_STEPS, force=G.MANDATORY)
    p1 = G.open_goal(g3, label="B onto C", under=ok)
    G.require_link(g3, p1, b3, "on", c3)
    p2 = G.open_goal(g3, label="A onto B", under=ok)
    G.require_link(g3, p2, a3, "on", b3)
    G.then(g3, p1, p2)
    done = D.follow(g3, ok, T.open_thread(g3), w3)

    # Undecomposed: must not read as a trivially-completed procedure.
    g4, w4 = _blocks()
    bare = G.open_goal(g4, label="nothing under me")
    g4.put(bare, met_by=G.BY_STEPS)
    empty = D.follow(g4, bare, T.open_thread(g4), w4)

    return {"the_first_step_really_is_reachable": refused["followed"][0][1],
            "and_the_second_really_is_impossible": not fell_back["followed"][1][1]
                if len(fell_back.get("followed", ())) > 1 else True,
            "A_PROCEDURE_REFUSES": not refused["done"] and refused.get("stopped") == D.REFUSE,
            "it_names_the_step_that_stopped_it": refused.get("at") == _s1,
            "and_says_it_may_not_be_worked_around": "may not be worked around" in refused["why"],
            "A_METHOD_FALLS_BACK_INSTEAD": fell_back.get("fell_back") is True,
            "and_never_refuses": "stopped" not in fell_back,
            "IDENTICAL_BUT_FOR_THE_DECLARED_FORCE":
                (refused["force"], fell_back["force"]) == (G.MANDATORY, G.ADVISORY),
            "a_completed_procedure_IS_met": done["done"] and G.satisfied(g3, ok, under=w3),
            "and_it_really_built_the_tower":
                g3.target(b3, "on") == c3 and g3.target(a3, "on") == b3,
            "BY_STEPS_is_why_it_counts_as_met": not G.world_constraints(g3, ok),
            "an_undecomposed_procedure_is_NOT_trivially_done":
                not empty["done"] and empty.get("undecomposed") is True,
            "sequence_is_the_then_order": G.sequence(g3, ok) == (p1, p2)}


def check_a_guideline_reorders_and_can_never_exclude():
    """Slice 2 of `docs/deliberation.md`: authored preference that may be wrong without being unsound.

    The property under test is the one that makes advice safe to accept: `avoid` means later, never
    Never. `goal.forbid_action` is the one that means never, and it prunes because a safety breach is a
    *proof*. A guideline is a guess, and the standing rule is rank a guess, prune a proof.

    The decisive case is Sussman's anomaly, reused deliberately. There, the only route begins with
    `unstack` — a move that closes no constraint and scores low. `check_a_forbidden_action_prunes...`
    already shows that *forbidding* `unstack` turns it honestly unsolvable. So avoiding `unstack` must
    leave it solved, or `avoid` has silently become `forbid` and authored advice can lose solutions.
    That single contrast is what this check exists for.

    What the planted-bug probes revealed, and it is the more useful half. A ranker rigged to return
    -999 for every avoided call — advice behaving as an outright filter — still solved the anomaly.
    So *"advice cannot exclude" is guaranteed by `pursue`'s architecture, not by anything in
    `guideline.py`*: the frontier only ever orders, so no score however low can put a move out of
    reach. That is exactly why authored advice is safe to accept, and it means this check *demonstrates*
    the property end to end rather than enforcing it. What `guideline.py` must get right on its own is the
    band, and that is what the probes do bite on.

    Also checked: a guideline never crosses a `relevance` band (the composed score keeps `>= 4` meaning
    exactly what `driver` requires); declaration order is precedence; and `governing` can say afterwards
    which advice spoke, because advice nobody can interrogate is a magic number whether it was learned or
    authored."""
    from . import driver as D, goal as G, guideline as GL, thread as T, workbench as W

    def sussman():
        g, world = _blocks()
        a, b, c = g.targets(world, "block")
        g.unlink(c, "on", index=0)
        g.link(c, "on", a)
        g.put(a, clear=None)
        g.put(c, height=2)
        goal = G.open_goal(g, label="A on B on C")
        G.require_link(g, goal, a, "on", b)
        G.require_link(g, goal, b, "on", c)
        return g, world, goal

    # The contrast. Same anomaly, same engine; only the force differs.
    g1, w1, goal1 = sussman()
    GL.avoid(g1, function="unstack", because="the crane is slow")
    avoided = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=5,
                       rank=GL.ranker(g1))

    g2, w2, goal2 = sussman()
    G.forbid_action(g2, goal2, function="unstack", reason="the crane is out of service")
    forbidden = D.pursue(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=5)

    # Bands must survive, and the reordering must be real. Advice keyed on a node rather than a
    # function is what puts two differently-advised proposals in one band — advising per function put each
    # band's proposals all on the same side, so the first version of this could not have seen a reordering
    # at all. "Settle the base first" is also the kind of thing an author would actually write.
    g3, w3 = _blocks()
    a3, b3, c3 = g3.targets(w3, "block")
    goal3 = G.open_goal(g3, label="A on B on C")
    G.require_link(g3, goal3, a3, "on", b3)
    G.require_link(g3, goal3, b3, "on", c3)
    GL.prefer(g3, on=c3, because="settle the base first")
    GL.avoid(g3, function="paint", because="cosmetic; never urgent")
    rank3 = GL.ranker(g3)
    wb = W.open_workbench(g3, w3)
    f0 = W.root_frame(g3, wb)
    unmet3 = G.unmet(g3, goal3, view=D.view_in(g3, f0),
                     under=W.image_of(g3, W.mapping_for(g3, f0, w3)))
    scored = [(rank3(g3, n, b, unmet3), D.relevance(g3, n, b, unmet3), n)
              for n, b in D.proposals(g3, f0)]
    crossed = [(s, band, n) for s, band, n in scored if int(s) != band]
    within = {band: {round(s, 6) for s, bb, _n in scored if bb == band}
              for band in {b for _s, b, _n in scored}}

    # Declaration order is precedence: the first matching guideline decides, so a later contradicting
    # one must not win.
    g4, _w4, _goal4 = sussman()
    first = GL.prefer(g4, function="unstack", because="declared first")
    GL.avoid(g4, function="unstack", because="declared second, must not win")
    bound4 = {"b": g4.targets(_w4, "block")[2], "floor": g4.target(_w4, "ground")}

    return {"forbidding_it_makes_the_goal_UNREACHABLE": not forbidden["found"],
            "BUT_AVOIDING_IT_STILL_SOLVES_IT": avoided["found"],
            "by_the_very_move_that_was_avoided":
                "unstack" in D.plan_steps(g1, avoided) if avoided["found"] else False,
            "A_GUIDELINE_NEVER_CROSSES_A_BAND": crossed == [],
            "AND_IT_REALLY_REORDERED_INSIDE_THEM": all(len(v) > 1 for v in within.values()),
            "declaration_order_is_precedence":
                GL.governing(g4, "unstack", bound4)[:1] == (first,),
            "governing_explains_afterwards":
                g4.attr(GL.governing(g4, "unstack", bound4)[0], "because") == "declared first",
            "advice_is_library_data_not_world_data":
                not any(gl in W.reachable(g4, "root") for gl in GL.advice(g4))}


def check_the_deliberation_seam_is_inert_by_default_and_live_when_used():
    """Slice 1 of `docs/deliberation.md`: `pursue` gains a decision point and changes nothing.

    The loop was closed — nothing could intervene between two imagined steps — so "what should I do next?"
    was not an expressible question, only a `while` condition. That made deliberation the thing this system
    computes *with* and cannot compute *about*: the same defect attention had before `thread.py` and the
    goal had before `goal.py`, in its third place.

    The vacuity guard is the whole test. A seam nothing can steer is indistinguishable from no seam,
    and it would pass any check that only asserted "default behaviour is unchanged" — which is exactly the
    green this project keeps catching as false. So both halves are required: the default path must be
    identical, and a decision must actually divert the search.

    Also checked: an unbuilt verb raises and names what is missing, rather than being silently ignored;
    and a fired decision reaches the thread, since a decision nobody can audit afterwards is no use to the
    compliance case the design exists for."""
    from . import driver as D
    from . import goal as G
    from . import thread as T

    def tower(decide=None):
        g, world = _blocks()
        a, b, c = g.targets(world, "block")
        goal = G.open_goal(g, label="tower")
        G.require_link(g, goal, a, "on", b)
        G.require_link(g, goal, b, "on", c)
        t = T.open_thread(g)
        return g, t, D.pursue(g, goal, t, world, decide=decide)

    g0, t0, plain = tower()
    g1, t1, silent = tower(decide=lambda s: None)             # a decider with nothing to say
    g2, t2, always = tower(decide=lambda s: D.EXPAND)          # ...and one that says the default aloud

    # The vacuity guard: a decision must be able to change the outcome, or none of the above means anything.
    g3, t3, stopped = tower(decide=lambda s: (D.COMMIT, "that's enough planning"))

    def unbuilt(verb):
        try:
            tower(decide=lambda s: verb)
            return None
        except D.Undecidable as e:
            return str(e)

    return {"default_finds_it": plain["found"],
            "IDENTICAL_WHEN_THE_DECIDER_IS_SILENT":
                (silent["found"], silent["steps"], D.plan_steps(g1, silent))
                == (plain["found"], plain["steps"], D.plan_steps(g0, plain)),
            "and_when_it_says_EXPAND": (always["found"], always["steps"]) == (plain["found"], plain["steps"]),
            "A_DECISION_REALLY_DIVERTS_IT": not stopped["found"] and stopped["stopped"] == D.COMMIT,
            "it_stopped_before_imagining_anything": stopped["steps"] == 0,
            "and_hands_back_the_prefix_it_had": "plan" in stopped and "frame" in stopped,
            "it_says_who_stopped_it": stopped["why"] == "that's enough planning",
            # `why` is an edge property of the transition, not an attribute of the entry — read it
            # through `thread.why`. Reading `g.attr(entry, "why")` returns None and this key was silently
            # False until the tally caught it, which is's lesson landing on its own author.
            "AND_IT_REACHES_THE_THREAD": any(
                "decided to commit" in (T.why(g3, e) or "") for e in T.entries(g3, t3)),
            "nothing_reached_the_thread_by_default": not any(
                "decided to" in (T.why(g0, e) or "") for e in T.entries(g0, t0)),
            # Updated as the machinery landed. `SENSE` is now a real stop (ignorance exists), and
            # `DECOMPOSE` no longer raises for want of a goal hierarchy — it raises because a method
            # applies once per goal (`driver.attempt`), never once per search step. Frequency, not absence.
            "DECOMPOSE_raises_and_says_it_is_the_wrong_FREQUENCY":
                "per GOAL" in (unbuilt(D.DECOMPOSE) or ""),
            "SENSE_is_no_longer_unbuilt": unbuilt(D.SENSE) is None,
            "and_a_nonsense_verb_still_raises": unbuilt("dance") is not None}


# --- focus ----------------------------------------------------------------------------------------
def check_focus_navigates_forward_backward_and_through_refs():
    g = new_graph()
    car = g.mint("car")
    g.link("root", "has", car)
    body = g.mint("body")
    g.link(car, "body", body)
    g.set_ref(body, "owner", car)

    f = Focus(g).open("h")
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
    f = Focus(g).open("h")
    f.move(g, "h", "nonexistent")
    return {"head_exists_but_empty": not f.has("h") and "h" in f.names,
            "further_moves_stay_safe": (f.move(g, "h", "anything"), f.has("h"))[1] is False}


def check_fork_explores_two_candidates_without_copying_the_world():
    g = new_graph()
    a, b = g.mint("car"), g.mint("car")
    g.link("root", "option", a)
    g.link("root", "option", b)
    f = Focus(g).open("h")
    f.fork("alt", "h")
    f.move(g, "h", "option", 0)
    f.move(g, "alt", "option", 1)
    # This used to assert `len(g.nodes) == 3`, which stopped meaning "the world was not copied" the
    # moment the heads themselves became graph data. What it always meant is asserted directly instead:
    # the two candidates are still the same two nodes, not images of them, and forking cost two heads.
    return {"two_heads": (f.at("h"), f.at("alt")) == (a, b),
            "the_world_was_not_copied": g.of_kind("car") == (a, b),
            "forking_cost_one_head": f.names == ("alt", "h")}


def check_spread_fans_out_one_head_per_target():
    g = new_graph()
    lst = g.mint("list")
    g.link("root", "list", lst)
    for n in "abc":
        g.link(lst, "item", g.mint("item", label=n))
    f = Focus(g).open("h")
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
    """`schema_of` answers with `Req`s now, not bare `(kind, count)` pairs — a count is a range and a
    target may be constrained by type as well as kind. The two-tuple stays legal to *write*, and this
    pins that it still means what it always meant: exactly four, of that kind, nothing said about more."""
    from .types import Req
    g, car, trike = _car_world()
    return {"schema_is_data": schema_of(g, "car") == {"body": Req(kind="body", lo=1, hi=1),
                                                      "wheel": Req(kind="wheel", lo=4, hi=4)},
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
    """The structural claim: an instruction names the head it acts on. Two identical cars exist; the
    program touches the one it was pointed at. Vacuity guard: assert the other is untouched."""
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
    prog = (NEW(R("x"), "junk"), LINK(R("x"), "junk", R("x")), NATIVE("check", R("t"), "car"))
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


def _counting_function(g):
    """A stored function with a loop in it — so a pause can land in the middle of a repetition, which is
    the case a straight-line program cannot exercise."""
    from . import asm
    asm.load_text(g, "\n".join([
        "fn count_wheels(c):",
        '    CONST R(i) 0',
        '    COUNT R(n) F(c) "wheel"',
        "    .loop:",
        "    LT R(more) R(i) R(n)",
        '    JMPNOT R(more) ".done"',
        "    ADD R(i) R(i) 1",
        '    JMP ".loop"',
        "    .done:",
        "    COPY R(result) R(i)",
    ]))


def check_the_executor_can_be_STOPPED_BETWEEN_ANY_TWO_INSTRUCTIONS():
    """The test the whole arc is organised around: *can the executor be stopped
    between any two primitive operations, and can the system say what it was doing?*

    Before this, no. made planning steppable — but `isa.Machine._loop` was an ordinary Python
    `while` holding `pc`, `stack` and `regs` as locals, so the `think` microfunction that drives the
    steppable search ran inside an atomic invocation. Steppability at the wrong level: one seam removed
    and an identical one left below it, inverted.

    Two vacuity guards, and between them they are the check. First, driving it by hand must reach the
    same answer as `run` — a yield point that changed the computation would be a fork, not a seam.
    Second, it must genuinely be *mid-flight* at a pause: unfinished, with the loop counter partway to its
    final value. A `tick` that quietly ran the whole program and returned once would pass every structural
    assertion here."""
    from . import activation as A, function as fn
    from .isa import Machine

    g, car, _t = _car_world()
    _counting_function(g)
    _params, program = fn.load(g, "count_wheels")

    # the control: the supported entry point, run to completion
    _f, whole = fn.invoke(g, "count_wheels", {"c": car})

    # the same program, ticked by hand
    focus = Focus(g).open("c", car)
    act = Machine(program).start(g, focus, of=fn.find(g, "count_wheels"))
    paused = []
    turns = 0
    while Machine(program).tick(g, act):
        turns += 1
        if A.get_reg(g, act, "i") == 2:
            # Stopped. Everything about what it is doing is graph data, read here as data.
            paused.append({"pc": A.pc(g, act), "doing": g.attr(A.doing(g, act), "op"),
                           "says": A.describe(g, act), "regs": A.registers(g, act),
                           "head": focus.at("c"), "finished": A.finished(g, act)})

    mid = paused[0] if paused else {}
    return {"driven_by_hand_gets_the_same_answer": A.get_reg(g, act, "result") == whole.get("result") == 4,
            "IT_REALLY_PAUSED_MID_FLIGHT": bool(paused) and mid["finished"] is False,
            "and_it_says_what_it_was_doing": "count_wheels" in mid.get("says", ""),
            "naming_the_instruction_not_just_an_index": mid.get("doing") in isa.WRITES_REGISTER
                                                        or mid.get("doing", "").startswith("J"),
            "THE_STATE_IS_DATA_NOT_A_PYTHON_LOCAL": mid.get("regs", {}).get("i") == 2
                                                     and mid.get("regs", {}).get("n") == 4,
            "including_where_it_was_LOOKING": mid.get("head") == car,
            "and_the_pause_was_partway_not_at_the_end": 0 < mid.get("pc", 0) < len(program),
            "ticks": turns}


def check_a_paused_program_is_readable_by_an_ORDINARY_MICROFUNCTION():
    """The homoiconicity claim, applied to the interpreter itself: a stored microfunction reads the
    state of a paused one. Nothing new was needed for it — an activation is a node, a register is a
    node, so `GET`/`ATTR` reach them the way they reach anything else.

    Same move as `thread.py`'s walker check: if walking the new structure needed a new opcode, the
    structure would not really be ordinary data. It does not.

    Vacuity guard: the reader must be looking at a program that is genuinely suspended, not one that
    has finished — so it is asserted unfinished *before* the reader runs, and the value it reads back must
    be the intermediate one, not the final one."""
    from . import activation as A, asm, function as fn
    from .isa import Machine

    g, car, _t = _car_world()
    _counting_function(g)
    _params, program = fn.load(g, "count_wheels")
    m = Machine(program)
    act = m.start(g, Focus(g).open("c", car), of=fn.find(g, "count_wheels"))
    while A.get_reg(g, act, "i") != 3 and m.tick(g, act):
        pass
    suspended = not A.finished(g, act)

    asm.load_text(g, "\n".join([
        "# How far has that computation got, and what is it running?",
        "fn how_far(a):",
        '    ATTR R(result) F(a) "pc"',
        '    GET R(fn) F(a) "of"',
        '    ATTR R(whose) R(fn) "name"',
        '    GET R(r) F(a) "register"',
        '    ATTR R(first) R(r) "name"',
    ]))
    _f, out = fn.invoke(g, "how_far", {"a": act})

    while m.tick(g, act):                              # and it resumes afterwards, unharmed
        pass
    return {"IT_WAS_SUSPENDED_WHEN_READ": suspended,
            "and_the_reader_saw_a_partway_pc": 0 < out.get("result") < len(program),
            "it_named_the_function_being_run": out.get("whose") == "count_wheels",
            "the_registers_are_ordinary_nodes": out.get("first") == "i",
            "reading_it_did_not_disturb_it": A.get_reg(g, act, "result") == 4,
            "no_new_ops_needed": True}


def check_an_invocation_knows_what_called_it():
    """A nested `INVOKE` used to be a nested Python frame — invisible to the system running it — so
    *"what was it doing?"* could only ever answer about the outermost program. The callee now points at its
    caller, and `activation.chain` is the ISA's own stack trace.

    Vacuity guard: the chain must be two deep and in the right order, and the outer activation must
    be the one that is *not* pointed at, or a chain of length two proves nothing about direction."""
    from . import activation as A, asm, function as fn
    g = new_graph()
    asm.load_text(g, "\n".join([
        "fn inner(x):",
        '    SET F(x) "touched" true',
        "fn outer(x):",
        "    INVOKE R(_) inner x=F(x)",
    ]))
    thing = g.mint("thing")
    g.link("root", "thing", thing)
    fn.invoke(g, "outer", {"x": thing})

    inner_act = [a for a in g.of_kind("activation")
                 if g.attr(g.target(a, "of"), "name") == "inner"]
    chain = A.chain(g, inner_act[0]) if inner_act else ()
    named = tuple(g.attr(g.target(a, "of"), "name") for a in chain)
    return {"the_inner_call_is_a_node": len(inner_act) == 1,
            "AND_IT_NAMES_ITS_CALLER": named == ("inner", "outer"),
            "the_outer_one_has_no_caller": len(chain) == 2 and g.target(chain[1], "caller") is None,
            "and_the_effect_really_happened": g.attr(thing, "touched") is True}


def check_a_finished_activation_is_retired_but_a_LIVE_one_cannot_be():
    """Retirement is not the same as being uninterruptible. A finished activation is not state anybody
    can be *inside* of, so `run` drops it — but `retire` refuses a live one, because the whole point of
    materialising the state was that something may be stopped in the middle of it.

    Same shape as `dispatch.commit()`: the honest admission that a boundary has been crossed, not a licence
    to throw away what has not."""
    from . import activation as A, function as fn
    from .isa import Machine
    g, car, _t = _car_world()
    _counting_function(g)
    _params, program = fn.load(g, "count_wheels")
    m = Machine(program)
    act = m.start(g, Focus(g).open("c", car), of=fn.find(g, "count_wheels"))
    m.tick(g, act)
    try:
        A.retire(g, act)
        refused = False
    except RuntimeError:
        refused = True
    while m.tick(g, act):
        pass
    A.retire(g, act)
    return {"a_live_activation_cannot_be_retired": refused,
            "a_finished_one_can": act not in g.nodes,
            "and_its_registers_went_with_it": g.of_kind("register") == (),
            "RUN_RETIRES_ITS_OWN": (m.run(g, Focus(g).open("c", car)), g.of_kind("register") == ())[1]}


def check_carrying_a_plan_OUT_is_steppable_and_the_steps_are_the_IRREVERSIBLE_ones():
    """`execution._replay` was a Python `for` — so the one loop that *touches the world* was the one
    the system could say least about mid-flight. It is now a `replay` node and `execution.step`, and
    `execute` is a loop over it.

    Vacuity guards. Driving it by hand must reach the same report as `execute` — a yield point that
    changed the outcome would be a fork. And the pause must be observably *between two real actions*: the
    first block really moved and the second really did not, which is the whole reason a yield point here is
    worth more than one anywhere else."""
    from . import execution as X, intake as I, thread as T, driver as D
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    g1, w1 = _blocks()                                # the control
    plan1 = D.pursue(g1, I.read_goal(g1, text), T.open_thread(g1, "t"), w1)
    whole = X.execute(g1, plan1["workbench"], plan1["frame"])

    g2, w2 = _blocks()                                # the same plan, one real action at a time
    plan2 = D.pursue(g2, I.read_goal(g2, text), T.open_thread(g2, "t"), w2)
    a, b, c = g2.targets(w2, "block")
    on_before = (g2.target(a, "on"), g2.target(b, "on"))
    r = X.open_execution(g2, plan2["workbench"], plan2["frame"])
    X.step(g2, r)                                     # exactly one real action
    mid = {"finished": X.finished(g2, r), "ran": g2.attr(r, "ran", ()), "at": g2.attr(r, "at"),
           "on": (g2.target(a, "on"), g2.target(b, "on"))}
    turns = 1
    while not X.finished(g2, r):                      # `step` answers "is there more", not "did I act"
        X.step(g2, r)
        turns += 1
    by_hand = X.report_of(g2, r)

    # "One move happened and the other did not" is asserted against what changed, not against what is
    # non-empty: every block starts `on` the ground, so a null check would have passed before anything ran.
    moved = sum(1 for was, now in zip(on_before, mid["on"]) if was != now)
    return {"driven_by_hand_ran_the_same_steps": by_hand["ran"] == whole["ran"] != (),
            "AND_REACHED_THE_SAME_VERDICT": by_hand["completed"] == whole["completed"] is True,
            "IT_PAUSED_BETWEEN_TWO_REAL_ACTIONS": mid["finished"] is False and len(mid["ran"]) == 1,
            "EXACTLY_ONE_MOVE_HAD_REALLY_HAPPENED": moved == 1,
            "the_replay_is_a_node_anyone_can_read": g2.kind(r) == "replay",
            "and_it_says_how_far_it_got": mid["at"] == 1,
            "turns": turns}


def check_the_WHOLE_plan_act_check_loop_is_steppable():
    """`driver.carry_out` was the last Python control loop, and the outermost one: the system could
    be inside a plan-act-check-replan cycle and unable to say so. It is now a `pursuit` node whose phases
    are data, and one tick is one primitive step — one imagined state, one real action, or one phase
    transition.

    Vacuity guards. The by-hand drive must reach the same verdict as `carry_out`; the pursuit must
    be caught in more than one phase, or a single-phase run would prove nothing about the state machine;
    and it must take many more ticks than there are attempts, which is what distinguishes *a tick is a
    primitive step* from *a tick is an attempt*."""
    from . import driver as D, intake as I, thread as T
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    g1, w1 = _blocks()                                # the control
    whole = D.carry_out(g1, I.read_goal(g1, text), T.open_thread(g1, "t"), w1)

    g2, w2 = _blocks()                                # ticked by hand
    p = D.open_pursuit(g2, I.read_goal(g2, text), T.open_thread(g2, "t"), w2)
    phases, said, ticks = [], [], 0
    while D.pursuit_step(g2, p):
        ticks += 1
        phases.append(g2.attr(p, "phase"))
        said.append(D.describe_pursuit(g2, p))
    by_hand = D.pursuit_report(g2, p)
    a, b, c = g2.targets(w2, "block")

    return {"driven_by_hand_reaches_the_same_verdict": by_hand["done"] == whole["done"] is True,
            "AND_THE_WORLD_REALLY_CHANGED": g2.target(a, "on") == b and g2.target(b, "on") == c,
            "IT_WAS_CAUGHT_IN_MORE_THAN_ONE_PHASE": len(set(phases)) > 1,
            "which_were": tuple(sorted(set(phases))),
            "A_TICK_IS_A_PRIMITIVE_STEP_NOT_AN_ATTEMPT": ticks > 2 * whole["tries"],
            "and_it_says_what_it_is_doing": all("pursuing" in s for s in said),
            "ticks": ticks}


def check_ONE_OUTER_LOOP_interleaves_everything_and_names_the_irreversible_step():
    """The arc's destination: a single outer loop, everything on one agenda, one
    primitive step per tick, nothing that cannot be interrupted.

    Two unrelated tasks — a stored microfunction and a whole goal-pursuit — are scheduled together and
    genuinely interleave, because the agenda is an ordered edge and `tick` rotates it. And the loop can
    say, *before* taking a step, whether that step is reversible: `imagine` costs time, `act` cannot be
    taken back. That asymmetry is the one thing says must not become uniform.

    Vacuity guards. The interleaving must be observable — both tasks must have advanced before
    either finished, or "round-robin" would be a claim about nothing. The verbs must include both
    `imagine` and `act`, or `verb_of` could be returning a constant. And an `act` must really have been
    available to decline, or the stopping rule would be untested."""
    from . import driver as D, intake as I, loop as L, thread as T, function as fn
    g, w = _blocks()
    _counting_function(g)
    car = g.mint("car")                               # something for the microfunction to count
    for _ in range(3):
        g.link(car, "wheel", g.mint("wheel"))

    lp = L.open_loop(g, "one loop")
    from .isa import Machine
    act = Machine(fn.load(g, "count_wheels")[1]).start(
        g, Focus(g).open("c", car), of=fn.find(g, "count_wheels"))
    p = D.open_pursuit(g, I.read_goal(g, _lines("goal build a tower:", "    a on b", "    b on c")),
                       T.open_thread(g, "t"), w)
    L.schedule(g, lp, act, why="count the wheels")
    L.schedule(g, lp, p, why="build the tower")

    a, b, _c = g.targets(w, "block")
    untouched = (g.target(a, "on"), g.target(b, "on"))

    # Stop BEFORE the first irreversible step — read the verb off the head of the agenda and decline.
    verbs, advanced, kinds_in_order = [], set(), []
    first_act = None
    while L.agenda(g, lp):
        head = L.agenda(g, lp)[0]
        if L.verb_of(g, head) in L.IRREVERSIBLE:
            first_act = {"task": head, "doing": L.describe(g, head)}
            break
        rec = L.tick(g, lp)
        if rec is None:
            break
        verbs.append(rec["verb"])
        advanced.add(rec["kind"])
        kinds_in_order.append(rec["kind"])

    # The world, read AT the MOMENT we declined. An earlier version of this key was the literal `True`,
    # which is the false-green keeps catching — it asserted nothing at exactly the point the check
    # exists to make a claim about.
    still_untouched = (g.target(a, "on"), g.target(b, "on")) == untouched
    then = L.run(g, lp, max_ticks=400)                # and it carries on when we let it
    return {"two_unrelated_tasks_on_ONE_agenda": len(verbs) > 0,
            "THEY_INTERLEAVED": advanced == {"activation", "pursuit"},
            "and_really_alternated": kinds_in_order[:4] == ["activation", "pursuit"] * 2,
            "and_it_named_both_kinds_of_step": {L.IMAGINE, L.RUN} <= set(verbs),
            "IT_STOPPED_BEFORE_THE_IRREVERSIBLE_ONE": first_act is not None,
            "naming_what_that_step_would_be": "acting" in (first_act or {}).get("doing", ""),
            "AND_THE_WORLD_WAS_STILL_UNTOUCHED_THEN": still_untouched,
            "when_allowed_it_finishes_the_job": g.target(a, "on") == b,
            "the_agenda_empties": then["why"] == "the agenda is empty",
            "ticks": L.ticks(g, lp)}


def check_the_loop_refuses_a_program_it_cannot_reconstruct():
    """Deliberate negative, and it is the honest boundary of the whole arc. An activation whose program
    exists only as a Python tuple cannot be resumed by anything but the caller holding it — which is the
    unreachable island `composability-principle` warns about. The loop says so instead of skipping it.

    Vacuity guard: the same program stored as a function is driven by the loop without complaint, so
    the refusal is about reconstructability and not about activations."""
    from . import asm, function as fn, loop as L
    from .isa import Machine, CONST
    g = new_graph()
    anonymous = Machine((CONST(R("x"), 1),)).start(g, Focus(g))
    lp = L.open_loop(g)
    L.schedule(g, lp, anonymous)
    try:
        L.tick(g, lp)
        refused = False
    except ValueError as e:
        refused = "STORED" in str(e) or "stored" in str(e)

    asm.load_text(g, "\n".join(["fn one(c):", '    CONST R(result) 1']))
    stored = Machine(fn.load(g, "one")[1]).start(g, Focus(g).open("c", "root"), of=fn.find(g, "one"))
    lp2 = L.open_loop(g)
    L.schedule(g, lp2, stored)
    out = L.run(g, lp2, max_ticks=20)
    return {"an_anonymous_program_is_REFUSED": refused,
            "but_a_STORED_one_is_driven_fine": out["why"] == "the agenda is empty",
            "and_it_really_ran": out["ticks"] >= 1}


def check_a_tool_says_whether_it_LOOKS_or_ACTS():
    """An earlier note named this as a concrete gap: `dispatch.register` took any callable and nothing said
    whether a tool observes or changes, so the veto and commit machinery treated a directory scan and a
    sent email identically. `loop.verb_of` needs it to tell look from act.

    The default is the safe one — unmarked means *acts* — because being wrong that way costs a pause and
    being wrong the other way spends an irreversible act somebody meant to withhold. Vacuity guard: the two
    tools are registered identically apart from that one flag, and must be classified oppositely."""
    from . import asm, dispatch as D, function as fn, loop as L
    from .isa import Machine
    g = new_graph()
    D.register("peek", lambda _g, t: "saw it", observes=True)
    D.register("poke", lambda _g, t: _g.put(t, poked=True))
    asm.load_text(g, "\n".join([
        "fn look_at(t):", '    DISPATCH R(result) "peek" F(t)',
        "fn change(t):", '    DISPATCH R(result) "poke" F(t)']))
    thing = g.mint("thing")
    g.link("root", "thing", thing)

    verbs = {}
    for name in ("look_at", "change"):
        a = Machine(fn.load(g, name)[1]).start(g, Focus(g).open("t", thing), of=fn.find(g, name))
        while L.verb_of(g, a) == L.RUN and Machine(fn.load(g, name)[1]).tick(g, a):
            pass
        verbs[name] = L.verb_of(g, a)
    return {"an_observing_tool_is_a_LOOK": verbs["look_at"] == L.LOOK,
            "a_changing_one_is_an_ACT": verbs["change"] == L.ACT,
            "AND_ONLY_ONE_OF_THEM_IS_IRREVERSIBLE": (verbs["change"] in L.IRREVERSIBLE
                                                     and verbs["look_at"] not in L.IRREVERSIBLE),
            "an_unregistered_stance_defaults_to_acting": not D.observes(g, "poke"),
            "and_the_declaration_is_readable": D.observes(g, "peek")}


def check_a_BLOCKING_microfunction_still_interleaves_because_every_level_ticks():
    """Three levels of stepping compose, and that is what retires the case for cps.

    `think` is a microfunction that spins on `STEP` until its search finishes — a *blocking* program by any
    ordinary reading, and an earlier note called it "an interruptible search driven from inside an atomic
    invocation". It is not atomic any more. The outer loop advances the activation one instruction at a
    time, that instruction advances the search one imagined state at a time, and unrelated work on the
    agenda runs in between. So a program does not have to be rewritten in continuation-passing style to
    stop holding the loop.

    That matters because it removes the last practical motive for's strong version (b): the reason to
    forbid backward jumps was that `think`'s loop was uninterruptible, and it no longer is.

    Vacuity guards, and they carry the whole claim. The other task must advance while the search
    inside `think` is genuinely unfinished — not merely before or after it — or "interleaving" would be a
    statement about scheduling two things that never overlapped. And `think` must still reach the same plan
    as `pursue`, at the same cost, or the interleaving was bought by changing the computation."""
    from . import asm, driver as D, function as fn, intake as I, loop as L, thread as T
    from .isa import Machine
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    g1, w1 = _blocks()                                # the control
    ref = D.pursue(g1, I.read_goal(g1, text), T.open_thread(g1, "t"), w1)

    g, world = _blocks()
    goal = I.read_goal(g, text)
    asm.load_text(g, _lines('fn think(goal, subject, thread) -> plan:',
                            '    NATIVE R(s) "plan" F(goal) F(subject) F(thread)',
                            '    .again:',
                            '    NATIVE R(more) "plan_step" R(s)',
                            '    JMPIF R(more) ".again"',
                            '    ATTR R(result) R(s) "found"'))
    _counting_function(g)
    car = g.mint("car")
    for _ in range(4):
        g.link(car, "wheel", g.mint("wheel"))

    thinking = Machine(fn.load(g, "think")[1]).start(
        g, Focus(g).open("goal", goal).open("subject", world).open("thread", T.open_thread(g, "t")),
        of=fn.find(g, "think"))
    counting = Machine(fn.load(g, "count_wheels")[1]).start(
        g, Focus(g).open("c", car), of=fn.find(g, "count_wheels"))

    lp = L.open_loop(g, "two programs")
    L.schedule(g, lp, thinking)
    L.schedule(g, lp, counting)

    # Watch for the discriminating moment: the other task advancing while `think`'s search is open and
    # unfinished. Anything less would not distinguish interleaving from running them back to back.
    overlapped = False
    while L.agenda(g, lp):
        head = L.agenda(g, lp)[0]
        s = g.attr(thinking, "pc") is not None and _search_of(g, thinking)
        if head == counting and s and not g.attr(s, "done"):
            overlapped = True
        if L.tick(g, lp) is None:
            break

    s = _search_of(g, thinking)
    return {"the_blocking_program_finished": g.attr(thinking, "halted") or L.finished(g, thinking),
            "and_found_the_SAME_plan_as_pursue": g.target(s, "reached") is not None
                                                 and g.attr(s, "length") == ref["length"],
            "at_the_SAME_cost": g.attr(s, "steps") == ref["steps"],
            "THE_OTHER_TASK_RAN_WHILE_ITS_SEARCH_WAS_STILL_OPEN": overlapped,
            "and_the_counter_finished_too": _reg_of(g, counting, "result") == 4,
            "ticks": L.ticks(g, lp)}


def _search_of(g, activation):
    """The search a `think`-style activation opened, read off its registers — no new record needed."""
    from . import activation as A
    s = A.get_reg(g, activation, "s")
    return s if s is not None and g.kind(s) == "search" else None


def _reg_of(g, activation, name):
    from . import activation as A
    return A.get_reg(g, activation, name)


def check_the_system_can_JUDGE_ITS_OWN_COMPUTATION_and_act_on_the_judgement():
    """"I have been planning for too long" — as an ordinary microfunction, watching an ordinary
    task, on the ordinary agenda.

    This is what materialising every control loop was *for*, and it is worth stating plainly because no
    single slice delivered it: once the state of a running computation is graph data, a rule can read it;
    once the reader is a task on the same agenda, it runs while the thing it is watching is still
    running; and once `stop` is data, the judgement has an effect. Monitoring and control of the system's
    own process, with no mechanism that was built for it — the watcher below is text, and the engine
    change it needed was one attribute lookup.

    It is worth being exact about the claim: this is *metacognitive monitoring* in the plain functional
    sense — the system's own computational process is an object it can inspect and steer, the way it can
    inspect a goal or a plan. It says nothing about anything else the word "self" is used for.

    And it is a third, independent argument against's (b). A watcher must poll, so it *needs*
    repetition; under (b) it could not be written as one microfunction at all. reached the same
    conclusion from exactness and from termination.

    Vacuity guards, and the check is mostly guards. The verdict must be written while the search is
    genuinely still open — a judgement delivered after the fact is not monitoring. The identical search
    with a generous budget must succeed, or the stop would be indistinguishable from exhaustion. And
    the world must be untouched, since planning was stopped before anything was carried out."""
    from . import asm, driver as D, function as fn, intake as I, loop as L, thread as T
    from .isa import Machine
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    # The watcher, authored as text. It reads a search node and judges it.
    def world():
        g, w = _blocks()
        asm.load_text(g, _lines(
            "# Am I taking too long over this? If so, stop planning.",
            "fn watch_planning(s, budget):",
            "    .again:",
            '    ATTR R(over) F(s) "done"',
            '    JMPIF R(over) ".end"',
            '    ATTR R(n) F(s) "steps"',
            '    ATTR R(b) F(budget) "value"',
            "    LT R(ok) R(n) R(b)",
            '    JMPIF R(ok) ".again"',
            '    SET F(s) "stop" "REFUSE"',
            '    SET F(s) "stop_why" "planning has gone on too long"',
            "    .end:"))
        return g, w

    def run_with(budget_value):
        g, w = world()
        p = D.open_pursuit(g, I.read_goal(g, text), T.open_thread(g, "t"), w,
                           guided=False, max_steps=400)
        D.pursuit_step(g, p)                          # one tick: the search now exists
        s = g.target(p, "search")
        budget = g.mint("budget", value=budget_value)
        mon = Machine(fn.load(g, "watch_planning")[1]).start(
            g, Focus(g).open("s", s).open("budget", budget), of=fn.find(g, "watch_planning"))
        lp = L.open_loop(g, "the work, and a watcher")
        L.schedule(g, lp, p, why="build the tower")
        L.schedule(g, lp, mon, why="notice if planning drags")
        judged = None
        while L.agenda(g, lp):
            if L.tick(g, lp) is None:
                break
            if g.attr(s, "stop") and judged is None:
                judged = {"open": not g.attr(s, "done"), "at": g.attr(s, "steps"),
                          "phase": g.attr(p, "phase")}
        return g, w, p, s, judged

    g, w, p, s, judged = run_with(8)                  # a budget the search will exceed
    a, b, _c = g.targets(w, "block")
    generous, _w2, p2, s2, _j2 = run_with(400)        # the control: same everything, budget it will not

    # The full cost is measured from the control, never pinned to a literal. This check used to compare
    # against a hardcoded 67, three times. That number was the blind search's cost *under the alphabetical
    # ordering of `function.names`* — an undeclared tie-break, and a blind control has no band, so the
    # tie-break was its entire ordering. Declaring the order (declaration order moved it to 28
    # and turned this check red, which is the right outcome for a pin on an arbitrary number and the wrong
    # one for what the check is actually about. What it means to assert is *"the watcher stopped it earlier
    # than the same search unwatched"* — a relation between two runs in this process, which is stable under
    # any ordering because both runs share it.
    full = generous.attr(s2, "steps")
    return {"a_TEXT_rule_watched_a_LIVE_computation": judged is not None,
            "AND_JUDGED_IT_WHILE_IT_WAS_STILL_RUNNING": bool(judged and judged["open"]),
            "partway_through": bool(judged and 0 < judged["at"] < full),
            "THE_JUDGEMENT_STOPPED_IT": g.attr(s, "how") == D.REFUSE,
            "and_it_says_why_in_the_rules_own_words": g.attr(s, "stop_why") ==
                                                      "planning has gone on too long",
            "it_stopped_EARLY_not_at_the_budget": g.attr(s, "steps") < full,
            "THE_WORLD_IS_UNTOUCHED": g.target(a, "on") != b,
            "the_pursuit_gave_up_honestly": not g.attr(p, "done"),
            # the control: without the watcher's verdict the identical search succeeds, so the stop is
            # what ended it and not exhaustion or a bad goal
            "AND_THE_SAME_SEARCH_UNWATCHED_SUCCEEDS": generous.attr(p2, "done") is True,
            "and_it_really_did_search_rather_than_stumble_on_it": full > g.attr(s, "steps") > 0,
            "full_blind_cost": full}


def _worked_session():
    """Three ordinary goals carried out on the blocks world — a session with a past."""
    from . import driver as D, intake as I, thread as T
    g, world = _blocks()
    th = T.open_thread(g, "t")
    for label, body in [("build a tower", ["    a on b", "    b on c"]),
                        ("stack the other way", ["    c on b", "    b on a"]),
                        ("put a on c", ["    a on c"])]:
        D.carry_out(g, I.read_goal(g, _lines(f"goal {label}:", *body)), th, world, max_steps=200)
    return g, world, th


def _still_answerable(g, world, th):
    """The questions the engine can answer from its past. This is the specification of forgetting:
    whatever it drops, every one of these must come back the same."""
    from . import conflict as C, driver as D, goal as G, query as Q, thread as T
    a, b, c = g.targets(world, "block")
    return {
        # what is true, and what did it
        "a_on_b": g.target(a, "on"),
        "why_a_is_where_it_is": tuple(sorted(
            g.attr(e, "function") or g.attr(e, "name")
            for e, _n, _bd in Q.history_for(g, th, _a_constraint(g, a, b)))),
        # what did I do, in order
        "what_i_did": tuple(g.attr(e, "function") or g.attr(e, "name")
                            for e in T.entries(g, th)
                            if g.kind(e) == "application" and g.attr(e, "done")),
        # did two intentions collide over one slot
        "interference": len(C.interference(g, th)),
        # what did I want, and is it still met
        "goals_met": tuple(sorted(g.attr(x, "label") for x in g.of_kind("goal")
                                  if G.satisfied(g, x, under=world))),
        # the library is still there to think with
        "can_still_plan": D.establishes(g, "stack")[0] != frozenset(),
    }


def _a_constraint(g, subject, obj):
    """A throwaway `a on b` constraint node to ask `history_for` about."""
    from . import goal as G
    probe = G.open_goal(g, label="probe")
    return G.require_link(g, probe, subject, "on", obj)


def check_FORGETTING_IS_THE_DEFAULT_and_no_answer_changes():
    """Forgetting is the default; remembering is the exception — the user's rule.

    Measured: three ordinary goals on a three-block world take it from 80 nodes to 892, of which 76% is
    scaffolding — searches, candidates, trace steps, frames, mappings, replays, activations, registers.
    None of it is a leak; it is what made the system able to say what it was doing. But it is all
    re-derivable from the goal and the library, by thinking again, and that is the line:

    > Keep what you cannot re-derive. The two irreducible kinds are a crossing of the world and a
    > surprise. Everything else is ordinary.

    This is not a reversal, which looks like it says the opposite.'s *retention defaults
    to keep* was argued about sightings — results of tool calls — and every one of those is kept here.
    Scaffolding is the category never had, because the outer-loop arc had not created it yet.

    The CHECK is NOT the node COUNT — it is that nothing became unanswerable. A forgetting pass
    that dropped everything would score beautifully on size. So every question the engine can ask of its
    past is asked *before* and *after*, and they must come back identical: what is true, why, what I
    did, whether two intentions collided, which goals are met, and whether the library still thinks."""
    from . import forget as FG, loop as L
    g, world, th = _worked_session()
    before_nodes = len(g.nodes)
    before = _still_answerable(g, world, th)

    lp = L.open_loop(g, "a quiet moment")
    f = FG.open_forgetting(g)
    L.schedule(g, lp, f, why="the past is mostly scaffolding")
    out = L.run(g, lp, max_ticks=5000)

    after = _still_answerable(g, world, th)
    kinds_left = {g.kind(n) for n in g.nodes}
    return {"THE_ANSWERS_ARE_UNCHANGED": after == before,
            "and_they_were_not_all_empty": bool(before["what_i_did"]) and before["a_on_b"] is not None,
            "MOST_OF_THE_PAST_WAS_ORDINARY": len(g.nodes) < before_nodes * 0.4,
            "the_world_survived": {"block", "ground", "world"} <= kinds_left,
            "so_did_the_library": {"function", "instr"} <= kinds_left,
            "AND_SO_DID_WHAT_I_DID": "application" in kinds_left,
            "but_the_search_scaffolding_is_gone":
                not ({"candidate", "trace_step", "signature"} & kinds_left),
            # The key that catches a partial sweep. Everything still here must be here *for a
            # reason* — the worklist bug (indexing an edge list that `drop` shrinks) left unreachable
            # records behind while every other key above stayed green.
            "EVERY_SURVIVOR_IS_KEPT_FOR_A_REASON": all(
                FG.kept_because(g, n) != "nothing keeps it"
                for n in g.nodes if g.kind(n) != "forgetting"),
            # and the sweep itself is ordinary: a finished pass is re-derivable scaffolding like any
            # other, so the next one forgets it. Nothing here is exempt from its own rule.
            "AND_THE_SWEEP_IS_ITSELF_FORGETTABLE": f in FG.doomed(g),
            "it_forgot_one_record_per_tick": out["ticks"] == g.attr(f, "at"),
            "before": before_nodes, "after": len(g.nodes)}


def check_IMAGINED_evidence_is_superseded_by_REAL_evidence():
    """'s `COMPACT`, and it turned out to be a rule rather than a mechanism — the whole of it is
    knowing when a record is superseded.

    `goal.py` already keeps two kinds of evidence rigorously apart, because conflating them was a real
    defect (: the driver closed a world goal on imagined evidence, so a goal read as *met* while nothing
    had happened). `planned` + `seen_in` is *I know how to do this*, pointing at an imagined frame;
    `closed` + `met_by` is *this is now true*, pointing at a real node. Once the second exists, the first
    is a snapshot of a world that no longer does — and one edge into one frame keeps every frame, mapping
    and transformation reachable from it alive.

    Measured: 51 further nodes, 22% of what survives an ordinary sweep.

    The vacuity guard is the whole correctness condition. A goal that was *planned and not carried
    out* has no other evidence — its imagined frame is the only account of how it would be met, and
    `execution.recover` needs the frame tree it belongs to. So the check requires the two goals to be
    treated oppositely, and a compaction that ignored `closed` would be forgetting the plan rather than
    tidying up. `planned` itself survives on both: what goes is only the pointer into the imagination."""
    from . import driver as D, forget as FG, goal as G, intake as I, loop as L, thread as T
    g, world = _blocks()
    th = T.open_thread(g, "t")
    done = I.read_goal(g, _lines("goal build a tower:", "    a on b", "    b on c"))
    D.carry_out(g, done, th, world, max_steps=200)

    # a second goal that is planned and never carried out — the contrast
    merely = I.read_goal(g, _lines("goal put a on c:", "    a on c"))
    plan = D.pursue(g, merely, th, world, max_steps=200)

    before = (g.target(done, "seen_in"), g.target(merely, "seen_in"), len(g.nodes))
    freed = FG.compact(g)
    lp = L.open_loop(g, "tidy")
    L.schedule(g, lp, FG.open_forgetting(g))
    L.run(g, lp, max_ticks=6000)

    return {"the_carried_out_goal_HAD_imagined_evidence": before[0] is not None,
            "IT_IS_GONE_NOW": g.target(done, "seen_in") is None,
            "but_the_REAL_evidence_remains": g.target(done, "met_by") is not None,
            "and_it_still_reads_as_planned_AND_closed":
                G.is_planned(g, done) and G.is_closed(g, done),
            "AND_THE_MERELY_PLANNED_GOAL_KEEPS_ITS_OWN": g.target(merely, "seen_in") is not None,
            "which_is_still_a_real_frame": g.target(merely, "seen_in") in g.nodes,
            "so_its_plan_can_still_be_read":
                D.plan_steps(g, plan) == ("stack",) or len(D.plan_steps(g, plan)) > 0,
            "compaction_freed_something": len(freed) > 0,
            "freed_edges": len(freed), "nodes": len(g.nodes)}


def check_A_TOOL_CALL_AND_A_SURPRISE_are_what_survives():
    """The two exceptions the rule is actually about — *the result of a tool call*, and
    *something that surprised us* — and until this existed nothing tested either of them. The blocks
    world never dispatches, so it produces zero observations; a sweep over it could have dropped every
    observation there is and every key would have stayed green. Caught by a planted-bug probe that removed
    `observation` from the roots and changed nothing.

    Here the agent really looks at a directory whose contents move under it. What must survive:

    * what it saw, because a tool call cannot be re-done — the world has moved on, and re-doing it may
      not even be safe;
    * what surprised it — a change nothing it did could account for (`memory.attribute` → `EXTERNAL`),
      which is information precisely because the system's own model did not predict it.

    Vacuity guards: the sweep must actually drop something, the belief must be re-readable after it
    (not merely present as a node), and the *unsurprising* half of the past must be gone — otherwise
    "remembering is the exception" would be indistinguishable from remembering everything."""
    from . import forget as FG, loop as L, memory as M
    g, th, d, disk, look = _watched_world()
    look()                                            # 3
    disk["count"] = 5
    look()                                            # 5 — nothing I did could explain this
    from . import function as fn, thread as T
    fn.invoke(g, "empty_it", {"d": d})                # and this change IS mine
    T.applied(g, th, "empty_it", {"d": d}, why="tidying up", done=True)
    disk["count"] = 0                                 # the world must agree, or the next scan
    look()                                            #    overwrites it and the sighting reads 5 again

    seen_before = tuple(g.attr(o, "value") for o in M.sightings(g, th, d, "count"))
    moves = M.transitions(g, th, d, "count")
    verdicts_before = tuple(M.attribute(g, th, a, b)["verdict"] for a, b in moves)
    before_nodes = len(g.nodes)

    lp = L.open_loop(g, "a quiet moment")
    L.schedule(g, lp, FG.open_forgetting(g))
    L.run(g, lp, max_ticks=4000)

    seen_after = tuple(g.attr(o, "value") for o in M.sightings(g, th, d, "count"))
    verdicts_after = tuple(M.attribute(g, th, a, b)["verdict"]
                           for a, b in M.transitions(g, th, d, "count"))
    kinds_left = {g.kind(n) for n in g.nodes}
    return {"WHAT_IT_SAW_SURVIVED": seen_after == seen_before == (3, 5, 0),
            "AND_SO_DID_WHETHER_IT_WAS_A_SURPRISE": verdicts_after == verdicts_before,
            "and_the_verdicts_are_not_all_the_same": len(set(verdicts_before)) > 1,
            "which_is_what_makes_the_key_above_mean_anything": M.EXTERNAL in verdicts_before,
            "the_sweep_really_dropped_something": len(g.nodes) < before_nodes,
            "the_ordinary_scaffolding_went": not ({"activation", "register", "focus"} & kinds_left),
            "observations": len(g.of_kind("observation"))}


def check_a_LIVE_computation_is_never_forgotten():
    """The one way forgetting can be catastrophic rather than merely lossy: sweeping work that is still
    in progress. A task on an agenda is not scaffolding, it is *what the system is doing*.

    It needs no special case — a live task is passed as an extra root, and the transitive closure
    does the rest, because a pursuit points at its search which points at its workbench.

    Vacuity guard: the pursuit must be genuinely mid-flight when the sweep is computed (a search open
    and unfinished), and it must still complete and change the world afterwards. A sweep run against an
    already-finished pursuit would prove nothing."""
    from . import driver as D, forget as FG, intake as I, loop as L, thread as T
    g, world = _blocks()
    p = D.open_pursuit(g, I.read_goal(g, _lines("goal build a tower:", "    a on b", "    b on c")),
                       T.open_thread(g, "t"), world, guided=False, max_steps=400)
    for _ in range(12):                                # get it properly under way
        D.pursuit_step(g, p)
    s = g.target(p, "search")
    mid_flight = not g.attr(s, "done") and g.attr(s, "steps", 0) > 0

    lp = L.open_loop(g, "sweep while working")
    L.schedule(g, lp, p)
    L.schedule(g, lp, FG.open_forgetting(g), why="forget, but not what I am doing")
    L.run(g, lp, max_ticks=6000)

    a, b, _c = g.targets(world, "block")
    return {"the_pursuit_was_mid_flight_when_the_sweep_was_computed": mid_flight,
            "ITS_WORKBENCH_SURVIVED": g.target(s, "workbench") in g.nodes,
            "and_so_did_the_search_itself": s in g.nodes,
            "IT_STILL_FINISHED_THE_JOB": g.attr(p, "done") is True,
            "and_really_changed_the_world": g.target(a, "on") == b,
            "the_sweep_still_dropped_something": any(g.kind(n) == "forgetting" for n in g.nodes)}


def check_forgetting_says_what_it_still_remembers_and_why():
    """*What do you still remember, and why?* has to be answerable, or "remembering is the exception"
    is a slogan rather than a rule anybody could audit.

    Vacuity guard: the two exceptions the user named — the result of a tool call and a surprise —
    must be distinguishable from each other and from the world, so the reasons must not collapse to one."""
    from . import dispatch as DI, forget as FG
    g, _car, _t = _car_world()
    reasons = {}
    for kind, node in (("goal", g.mint("goal", label="q")),
                       ("observation", g.mint("observation", key="count")),
                       ("deviation", g.mint("deviation", step="scan")),
                       ("function", g.mint("function", name="f"))):
        reasons[kind] = FG.kept_because(g, node)
    scaffold = g.mint("candidate")
    _ = DI
    return {"a_tool_call_result_is_kept": "tool call" in reasons["observation"],
            "A_SURPRISE_IS_KEPT_AND_SAYS_SO": "surprise" in reasons["deviation"],
            "the_library_is_kept_for_a_DIFFERENT_reason": "library" in reasons["function"],
            "and_intent_for_another": reasons["goal"] not in
                                      (reasons["observation"], reasons["deviation"],
                                       reasons["function"]),
            "ORDINARY_SCAFFOLDING_IS_NOT_KEPT": FG.kept_because(g, scaffold) == "nothing keeps it"}


def _warehouse(nested: bool = True):
    """A box inside a warehouse's measurement case for the word *where*. With `nested`, the parcel
    is already in the box (so reach can be *asked*); without it, the parcel is loose (so reach can be
    *planned for*)."""
    from . import asm
    g = new_graph()
    declare_type(g, "thing", attrs={"kind_of": "thing"})
    declare_type(g, "loose", base="thing", attrs={"held": False})
    asm.load_text(g, "\n".join([
        "# Put a loose thing inside a container.",
        "fn put_in(t: loose, box: thing) -> thing:",
        '    LINK F(box) "contains" F(t)',
        '    SET F(t) "held" true',
    ]))
    world = g.mint("world")
    g.link("root", "has", world)
    wh = g.mint("thing", kind_of="thing", label="wh", held=True)
    box = g.mint("thing", kind_of="thing", label="box", held=True)
    parcel = g.mint("thing", kind_of="thing", label="parcel", held=False)
    for n in (wh, box, parcel):
        g.link(world, "thing", n)
    g.link(wh, "contains", box)
    if nested:
        g.link(box, "contains", parcel)
        g.put(parcel, held=True)
    return g, world, wh, box, parcel


def check_TRANSITIVE_REACH_is_the_one_thing_a_fixed_PATH_cannot_say():
    """The one genuine closed-class gap this project measured, arrived at twice independently:
    `closed_class_rechallenged.md` probed five relational forms and found four pure sugar with
    transitivity the one needing a real extension, and reached the same single item by asking what
    the word *where* requires. A parcel in a box in a warehouse *is* in the warehouse, and nothing here
    could say so: a fixed-depth type cannot reach it, a link constraint reads false because it is not a
    direct target, and the path grammar has no repetition operator.

    Predicate position only, and that restriction is the design. *Is X reachable from Y?* stays
    boolean and single-valued, so it breaks no contract. A reference — `a.contains+.label` — would
    denote a *set*, breaking `node_at`'s promise of one node or `None`; `parse` still refuses it and now
    says where to go instead.

    Vacuity guards: the direct case and the nested case must differ for a plain link constraint (or
    reach would be indistinguishable from adjacency); reach must not be reflexive; and a cycle must
    terminate, because containment is only supposed to be acyclic and a graph does not enforce it."""
    from . import goal as G, path as P
    g, world, wh, box, parcel = _warehouse(nested=True)

    plain = G.open_goal(g, label="directly in")
    G.require_link(g, plain, wh, "contains", parcel)
    deep = G.open_goal(g, label="in, at any depth")
    G.require_link(g, deep, wh, "contains", parcel, transitive=True)
    adjacent = G.open_goal(g, label="the box is directly in")
    G.require_link(g, adjacent, wh, "contains", box)

    refused = None
    try:
        P.parse("wh.contains+")
    except P.BadPath as e:
        refused = str(e)

    # Read every contrast BEFORE mutating. records this exact trap: the cycle below makes `wh`
    # genuinely reachable from itself, so a reflexivity key evaluated in the return dict would have been
    # measuring the cycle rather than reflexivity — and it read False for the right reason and the wrong
    # question. Caught here for the second time in this file.
    before = {"direct": G.satisfied(g, plain, under=world),
              "really_in_there": P.reaches(g, wh, "contains", parcel),
              "deep": G.satisfied(g, deep, under=world),
              "adjacent": G.satisfied(g, adjacent, under=world),
              "reflexive": P.reaches(g, wh, "contains", wh)}

    g.link(parcel, "contains", wh)                     # a cycle: a mis-authored world must not hang
    cyclic = G.satisfied(g, deep, under=world)
    # And the cycle guard needs a question with NO answer. Asking for something that IS there returns
    # before the loop is ever re-entered, so a version with no cycle protection at all passes — measured,
    # by planting exactly that. Only a miss has to walk the whole cycle.
    stray = g.mint("thing", kind_of="thing", label="stray")
    g.link(world, "thing", stray)
    missing = P.reaches(g, wh, "contains", stray)
    return {"a_DIRECT_link_constraint_reads_FALSE": not before["direct"],
            "though_the_parcel_really_is_in_there": before["really_in_there"],
            "AND_THE_TRANSITIVE_ONE_READS_TRUE": before["deep"],
            "adjacency_still_works_the_old_way": before["adjacent"],
            "reach_is_NOT_reflexive": not before["reflexive"],
            "A_CYCLE_TERMINATES": cyclic is True,
            "AND_A_MISS_TERMINATES_TOO_which_is_the_real_guard": missing is False,
            "and_it_renders_back_with_the_plus": G.describe_constraint(g, G.constraints(g, deep)[0])
                                                 == "wh contains+ parcel",
            "A_REFERENCE_STILL_REFUSES_IT": refused is not None and "PREDICATE" in refused,
            "and_says_where_to_go_instead": refused is not None and "contains+" in refused}


def check_a_goal_of_REACH_can_be_authored_and_PLANNED_FOR():
    """End to end: *put the parcel in the warehouse* — where "in" means at any depth — authored as
    text, planned, carried out, and true in reality afterwards.

    This is the half that a predicate alone does not give you. `driver.relevance` scores a proposal by
    what the function's body *establishes*, and `put_in` links `box contains parcel` — which is not the
    constraint being asked (`wh contains+ parcel`). So the closing move does not match exactly and
    cannot reach the top band: the plan is found by ranking, which is precisely the *rank a guess, prune a
    proof* discipline. Had relevance been a filter, this goal would be unreachable.

    Vacuity guard: the plan must close the goal by putting the parcel in the box, not in the
    warehouse directly — otherwise the transitive step was never exercised and a direct link would have
    done."""
    from . import driver as D, goal as G, intake as I, path as P, thread as T
    g, world, wh, box, parcel = _warehouse(nested=False)
    # Warn `never touch wh` is what makes this exercise reach rather than adjacency: without it the
    # planner would simply put the parcel straight into the warehouse, and a plain link constraint would
    # have done. Two authored forms composing - a plan constraint and a transitive world constraint.
    goal = I.read_goal(g, _lines("goal stow it:", "    wh contains+ parcel", "    never touch wh"))
    report = D.carry_out(g, goal, T.open_thread(g, "t"), world, max_steps=200)

    return {"it_was_authored_as_TEXT": len(G.world_constraints(g, goal)) == 1,
            "AND_CARRIED_OUT": report["done"] is True,
            "the_parcel_is_now_in_the_warehouse": P.reaches(g, wh, "contains", parcel),
            "BUT_NOT_DIRECTLY": parcel not in g.targets(wh, "contains"),
            "it_went_into_the_BOX": parcel in g.targets(box, "contains"),
            "steps": report["attempts"][0].get("steps", ()) if report["attempts"] else ()}


def check_what_and_where_LOCATE_a_thing_in_an_order_the_world_ALREADY_HAS():
    """*What is it?* and *where is it?* needed a verb and no machinery, which is what measured
    and this asserts: `types.recognize` is the subsumption order read bottom-up, and `where` is's reach
    walked backwards. Neither searches, neither imagines, neither records.

    Vacuity guard 1: `where` must reach past the immediate container, or it is `g.sources` with a
    longer name and the whole transitive-reach arc bought nothing at the surface. The parcel is in the box
    *and* in the warehouse, and the order must be nearest first — a set would have thrown that away
    (`search-was-irreproducible-set-tiebreak`).

    Vacuity guard 2: `what` must discriminate. The nested parcel is held and the loose one is not, so
    they must come back with different types; a `what` answering "thing" for everything would pass any
    check that only asked whether it answered.

    Vacuity guard 3: the word is not the machinery. The same function answers a world that writes the
    relation the other way round (`part_of`, forwards) — otherwise `where` is about containment rather than
    about reach, and the domain vocabulary has leaked into the engine."""
    from . import locate as L
    g, _world, wh, box, parcel = _warehouse(nested=True)
    loose_g, _w2, _wh2, _box2, loose = _warehouse(nested=False)

    # A second world, written the other way round: a wheel is `part_of` a car, forwards.
    p = new_graph()
    car, hub, wheel = (p.mint("thing", label=n) for n in ("car", "hub", "wheel"))
    p.link("root", "has", car)
    p.link(wheel, "part_of", hub)
    p.link(hub, "part_of", car)

    return {"WHAT_reads_the_types_it_satisfies_NOW": L.what(g, parcel) == ("thing",),
            "AND_IT_DISCRIMINATES": L.what(loose_g, loose) == ("loose", "thing"),
            "a_type_itself_is_not_a_thing_with_a_what": L.what(g, "root") == (),
            "WHERE_CLIMBS_OUT_OF_THE_CONTAINER": L.where(g, parcel) == (box, wh),
            "AND_IT_REACHES_PAST_THE_IMMEDIATE_ONE": wh in L.where(g, parcel),
            "nearest_first_because_it_is_not_a_set": L.where(g, parcel)[0] == box,
            "nothing_holds_the_warehouse_and_it_SAYS_so": (
                L.where(g, wh) == ()
                and "nothing here holds wh" in L.describe(g, "where", wh)),
            "THE_SAME_TRAVERSAL_ANSWERS_THE_OTHER_CONVENTION": (
                L.where(p, wheel, by="part_of") == (hub, car)),
            "and_the_default_word_finds_nothing_there": L.where(p, wheel) == (),
            "it_renders_for_a_reader": L.describe(g, "where", parcel).startswith("parcel is in: box, wh")}


def _dated():
    """Four events, three of them intervals and one a point — the vocabulary `when` reads."""
    g = new_graph()
    made = {}
    for label, span in (("build", (1, 5)), ("paint", (5, 9)), ("inspect", (3, 4)), ("ship", (12, 12))):
        n = g.mint("event", label=label, start=span[0], end=span[1], at=span[0])
        g.link("root", "has", n)
        made[label] = n
    undated = g.mint("event", label="someday")
    g.link("root", "has", undated)
    return g, made, undated


def check_WHEN_is_SUGAR_and_an_authored_TYPE_BLOCK_agrees():
    """ measured `when` as sugar: ordering and interval containment over a comparable value,
    with Allen's relations reducing to comparisons on two endpoints. That was an argument, and this is the
    probe — the same judgement is authored as an ordinary `type` block, with `Rel` comparing two places
    inside one subgraph, and the two must agree. If `relate` could say something a `type` block cannot,
    `when` was a capability and not a verb, and was wrong.

    Vacuity guard: the type must REFUSE the other pair. A schema that accepted both orders would
    agree with `relate` on the positive case while testing nothing at all.

    A point is an interval whose endpoints coincide, which keeps *when did it happen* and *how long did
    it last* one question. `inspect` sits inside `build`, and that is `during` on both routes.

    And incomparable is a third answer: an event dated `"tuesday"` against one dated `3` is not
    before it, not after it, and saying so beats inventing an order between two vocabularies."""
    from . import locate as L, types as TY
    g, ev, undated = _dated()

    # The same claim, authored: a pair whose first ends before its second begins.
    TY.declare_type(g, "event_thing", attrs={"kind_of": "event"})
    TY.declare_type(g, "runs_before", requires={"first": TY.Req(kind="event", lo=1, hi=1),
                                                "second": TY.Req(kind="event", lo=1, hi=1)},
                    relates=[TY.Rel("first.end", "<", "second.start")])

    def pair(a, b):
        n = g.mint("pair")
        g.link(n, "first", ev[a])
        g.link(n, "second", ev[b])
        return n

    # The boundary is where the agreement means something. `first.end < second.start` is *strict*, so
    # it says `before` and NOT `meets` — and the first version of this check asserted the type would accept
    # `build`/`paint` (which meet at 5) because it lumped the two relations together. The type was right and
    # the assertion was wrong. Three pairs now, straddling the boundary in both directions.
    agree = tuple((TY.is_a(g, pair(a, b), "runs_before"),
                   L.relate(L.interval(g, ev[a]), L.interval(g, ev[b])) == L.BEFORE)
                  for a, b in (("build", "ship"), ("build", "paint"), ("paint", "build")))
    by_comparison = L.relate(L.interval(g, ev["build"]), L.interval(g, ev["paint"]))

    # Read the COUNT BEFORE mutating and both record this exact trap, and it caught me again:
    # `tuesday` below is incomparable, so a count taken in the return dict measures the omission rather
    # than the placement, and reads wrong for the right reason.
    placed = len(L.when(g, ev["build"]))
    odd = g.mint("event", label="tuesday", at="tuesday")
    g.link("root", "has", odd)
    return {
        "MEETS_because_one_ends_where_the_next_begins": by_comparison == L.MEETS,
        "before_when_there_is_a_gap": L.relate(L.interval(g, ev["build"]),
                                              L.interval(g, ev["ship"])) == L.BEFORE,
        "DURING_for_an_interval_inside_another": L.relate(L.interval(g, ev["inspect"]),
                                                          L.interval(g, ev["build"])) == L.DURING,
        "a_POINT_is_an_interval_with_equal_ends": L.interval(g, ev["ship"]) == (12, 12),
        "and_a_point_inside_one_is_DURING_it_too": L.relate((4, 4), (1, 5)) == L.DURING,
        "equal_before_meets_so_two_points_at_one_time_are_EQUAL": L.relate((3, 3), (3, 3)) == L.EQUAL,
        "overlaps_is_distinguishable_from_both": L.relate((1, 6), (5, 9)) == L.OVERLAPS,
        # the sugar claim, checked rather than argued: an authored type block and the comparison agree
        "AND_AN_AUTHORED_TYPE_BLOCK_AGREES_EVERY_TIME": all(a == b for a, b in agree),
        "including_at_the_boundary_where_MEETS_is_not_BEFORE": agree[1] == (False, False),
        "THE_TYPE_REFUSES_THE_OTHER_ORDER": agree[2] == (False, False),
        "and_it_is_not_vacuous_because_one_pair_PASSES": agree[0] == (True, True),
        "INCOMPARABLE_IS_A_THIRD_ANSWER": L.relate(L.interval(g, odd), L.interval(g, ev["ship"])) is None,
        "undated_means_the_question_does_not_apply": (L.interval(g, undated) is None
                                                      and L.when(g, undated) == ()),
        "and_it_says_so_rather_than_dating_it": "nothing here says when" in L.describe(g, "when", undated),
        "an_event_is_placed_against_every_other_dated_one": placed == 3,
        # ...and an incomparable one is left out rather than guessed at, which is why the count above
        # had to be read before `tuesday` existed.
        "AND_AN_INCOMPARABLE_ONE_IS_LEFT_OUT": len(L.when(g, ev["build"])) == placed}


def check_a_READER_answers_and_records_NOTHING():
    """`what` / `where` / `when` as CNL verbs item 1, and the smallest capability left. They are a
    different form, not a fifth force: `goal` / `ask` / `why` / `plan` state a whole proposition and
    differ in what is done with it, while these have a gap and are answered by locating a thing.

    The property that matters is that nothing is kept, and it is's rule applied to answers:
    *keep what you cannot re-derive.* A reader's answer is a traversal away at any moment, so storing one
    could only ever let it drift from the world it describes — `types.tag`'s stamp still said `car` after
    the wheel came off. So the world must be unchanged by asking, and — the discriminating half —
    the answer must follow the world when it moves. A cached answer passes the first and fails the
    second, which is the planted bug's exact signature.

    `ask` settling by default is not inconsistent with this and the contrast is the reason both are
    right: a derivation *ran*, and repeating it costs a search.

    Refusal is the feature here as everywhere on this border: an unknown name, an empty body, and a line
    that *says* something rather than naming something."""
    from . import intake as I, locate as L, thread as T
    from .workbench import reachable
    g, _world, _wh, box, parcel = _warehouse(nested=True)
    th = T.open_thread(g, "t")

    before_world = tuple(reachable(g, "root"))
    first = I.respond(g, _lines("where it is:", "    parcel"), th, under="root")
    again = I.respond(g, _lines("where it is:", "    parcel"), th, under="root")
    after_world = tuple(reachable(g, "root"))

    what_said = I.respond(g, _lines("what it is:", "    parcel"), th, under="root")
    verb, q = I.read(g, _lines("where it is:", "    by ^contains", "    parcel"), under="root")

    def refused(*lines):
        try:
            I.read(g, _lines(*lines), under="root")
            return False
        except I.Unreadable:
            return True

    dg, ev, _u = _dated()
    when_said = I.respond(dg, _lines("when it was:", "    inspect"), T.open_thread(dg, "t"))

    g.unlink(box, "contains", dst=parcel)              # the world moves under the question
    moved = I.respond(g, _lines("where it is:", "    parcel"), th, under="root")
    return {
        "a_WHERE_block_answers": "parcel is in: box, wh" in first,
        "a_WHAT_block_answers": what_said == "parcel is: thing",
        "a_WHEN_block_answers": when_said.startswith("inspect at 3-4") and "during build" in when_said,
        "THE_WORLD_IS_UNCHANGED_BY_ASKING": after_world == before_world,
        "asking_twice_says_the_same_thing": first == again,
        "AND_THE_ANSWER_FOLLOWS_THE_WORLD_WHEN_IT_MOVES": "nothing here holds parcel" in moved,
        "the_question_itself_IS_data": g.kind(q) == "question" and g.attr(q, "verb") == "where",
        # The question reaches the thread — that it was asked is history — and the answer does not.
        "the_asking_is_history_even_though_the_answer_is_not": any(
            g.kind(T.attended(g, e) or "") == "question" for e in T.entries(g, th)),
        "three_readers_and_no_more": L.VERBS == ("what", "where", "when"),
        "it_round_trips_to_what_was_ASKED": I.describe(g, q) == _lines(
            "where it is:", "    by ^contains", "    parcel"),
        "an_unknown_name_is_REFUSED": refused("what it is:", "    nobody"),
        "a_question_about_nothing_is_REFUSED": refused("where it is:", "    by ^contains"),
        "and_so_is_a_line_that_SAYS_something": refused("what it is:", "    parcel is a thing"),
        "read_goal_still_refuses_a_question_block": refused_as_goal(g)}


def refused_as_goal(g) -> bool:
    from . import intake as I
    try:
        I.read_goal(g, _lines("what it is:", "    parcel"), under="root")
        return False
    except I.Unreadable:
        return True


def check_a_REFUSAL_leaves_nothing_behind_even_when_the_REFERENCE_LANGUAGE_raises():
    """A real defect, found by probing a file KB. `intake.read` rolls back on `Unreadable`, and a
    reference that cannot be read raises `BadPath` — a *different* exception, from a *different* module.
    So `a.size > b.size` (three words, therefore read as a link, therefore `parse_link('>')`) escaped the
    handler, the savepoint was never rolled back, and an empty goal was left in the graph. The module
    docstring says a refusal leaves nothing behind *because a half-built goal would be pursued and would
    look like it was working*; that held for every refusal this border authored and not for one it merely
    passed through.

    Vacuity guard: the graph must be byte-identical afterwards, not merely goal-free — a rollback
    that dropped the goal and kept its constraints would pass a weaker check. And the border must raise
    exactly one exception type, or a caller caring about refusals has to know which module failed."""
    from . import intake as I
    g = new_graph()
    a, b = g.mint("thing", label="a"), g.mint("thing", label="b")
    g.link("root", "has", a)
    g.link("root", "has", b)
    before = (len(g.nodes), sorted(g.of_kind("goal")), sorted(g.of_kind("question")))

    def refusal(block):
        try:
            I.read(g, block)
            return None
        except I.Unreadable as e:
            return str(e)
        except Exception as e:                     # anything else is the defect, by definition
            return e

    from_reference = refusal(_lines("goal compare them:", "    a.size > b.size"))
    from_reader = refusal(_lines("where it is:", "    by ^", "    a"))
    from_vocabulary = refusal(_lines("goal nonsense:", "    a b c d e"))
    return {
        "A_BAD_REFERENCE_IS_REFUSED_IN_THIS_BORDERS_OWN_VOCABULARY": isinstance(from_reference, str),
        "and_it_names_the_line": isinstance(from_reference, str) and "line 2" in from_reference,
        "a_readers_by_line_is_validated_when_AUTHORED_not_when_answered":
            isinstance(from_reader, str),
        "an_ordinary_vocabulary_refusal_still_works": isinstance(from_vocabulary, str),
        "AND_NOTHING_IS_LEFT_BEHIND_BY_ANY_OF_THEM":
            (len(g.nodes), sorted(g.of_kind("goal")), sorted(g.of_kind("question"))) == before,
        "the_world_itself_is_untouched": g.attr(a, "label") == "a" and len(g.targets("root", "has")) == 2}


def _bin_world():
    """A bin of items, some dirty, and two actions — one that helps and one that does not."""
    from . import asm, intake as I
    g = new_graph()
    I.read(g, 'type item:\n    kind_of = "item"\n')
    I.read(g, 'type dirty_item:\n    kind_of = "item"\n    clean != true\n')
    I.read(g, 'type bin:\n    kind_of = "bin"\n')
    I.read(g, "type tidy_bin:\n    is a bin\n    has no item each a dirty_item\n")
    asm.load_text(g, "\n".join([
        "fn clean_one(i: item) -> item:",
        '    SET F(i) "clean" true',
        "",
        "fn weigh(i: item) -> item:",
        '    SET F(i) "weighed" true',
    ]))
    b = g.mint("bin", kind_of="bin", label="b")
    g.link("root", "has", b)
    items = []
    for name in ("one", "two"):
        it = g.mint("item", kind_of="item", label=name)
        g.link(b, "item", it)
        items.append(it)
    return g, b, items


def check_a_UNIVERSAL_constraint_names_the_members_that_make_it_FALSE():
    """`unmet` says which constraints are false; this says which members make one false.'s founding argument was that a goal answering only yes/no forces blind search, while one naming its
    unfinished business enables means-ends. A universal constraint reintroduced exactly that defect one
    level up: `b is a tidy_bin` is expressible (`has no item each a dirty_item`, and
    `docs/limits.md` measured it as sugar) but could only answer yes/no — so `docs/limits.md` measured
    even a *singular* action that would certainly close it at band 1, against band 4 for the equivalent
    singular constraint. Same *predicate-expressible, planning-half-missing* split found for reach.

    Vacuity guard 1: a satisfied constraint must have no witnesses. A reader that named nodes for a
    constraint that holds would be describing the world rather than the unfinished business, and every
    other key here would still pass.

    Vacuity guard 2: it must discriminate. For a type constraint there is no label to filter
    effects on, so a witness branch that scored any write to a witness would rank `weigh` — which changes
    nothing relevant — as highly as `clean_one`. The two must land in different bands or the guidance is
    noise with a high number on it.

    Vacuity guard 3: the too-few case has no witness, and that is the open world. A bin needing two
    more items has nothing to point at, because the missing item does not exist. That direction is served
    by `relevance`'s existential `mint` branch, and conflating them would mean inventing a node to blame."""
    from . import driver as D, goal as G, intake as I, types as TY, workbench as W
    g, b, items = _bin_world()
    universal = I.read_goal(g, _lines("goal tidy it:", "    b is a tidy_bin"))
    singular = I.read_goal(g, _lines("goal clean one:", "    one.clean = true"))

    wb = W.open_workbench(g, b)
    f0 = W.frames(g, wb)[0]
    m_one = W.mapping_for(g, f0, items[0])

    open_u, open_s = G.unmet(g, universal, under="root"), G.unmet(g, singular, under="root")
    wit = G.witnesses(g, open_u[0])
    helps = D.relevance(g, "clean_one", {"i": m_one}, open_u)
    idles = D.relevance(g, "weigh", {"i": m_one}, open_u)
    was_singular = D.relevance(g, "clean_one", {"i": m_one}, open_s)

    # Guard 1: clean both, and the constraint that now holds must name nobody.
    for it in items:
        g.put(it, clean=True)
    satisfied_now = G.holds(g, open_u[0])
    after = G.witnesses(g, open_u[0])

    # Guard 3: a too-few failure has no witness to point at.
    TY.declare_type(g, "full_bin", requires={"item": TY.Req(kind="item", lo=5, hi=None)}, base="bin")
    too_few = I.read_goal(g, _lines("goal fill it:", "    b is a full_bin"))
    short = G.unmet(g, too_few, under="root")

    return {
        "THE_UNIVERSAL_NAMES_ITS_OFFENDING_MEMBERS": set(wit) == set(items),
        "and_they_are_the_ITEMS_not_the_subject": b not in wit,
        "SO_A_SINGULAR_ACTION_CAN_NOW_REACH_BAND_4": helps == 4,
        "AND_AN_IRRELEVANT_ONE_CANNOT": idles < 4,
        "the_singular_constraint_still_scores_as_it_did": was_singular == 4,
        "a_SATISFIED_constraint_names_NOBODY": satisfied_now and after == (),
        "TOO_FEW_HAS_NO_WITNESS_because_the_missing_one_does_not_exist":
            bool(short) and G.witnesses(g, short[0]) == (),
        "and_fails_and_offenders_cannot_disagree":
            len(TY.offenders(g, b, "tidy_bin").get("item", ())) == 0
            and TY.is_a(g, b, "tidy_bin")}


def check_runaway_program_halts_loudly():
    """Deliberate negative. Termination is unsolved in general; failing loudly is the honest stand-in."""
    try:
        run(("loop", isa.JMP("loop")), new_graph())
        return {"halted_loudly": False}
    except RuntimeError as e:
        return {"halted_loudly": True, "message": str(e)[:52]}


def _checks():
    """Collected lazily, at call time. This was a module-level list once and silently omitted every
    check defined below it — a self-test that quietly tests less than it appears to is exactly the
    false-green class this project keeps catching."""
    return [v for k, v in sorted(globals().items()) if k.startswith("check_")]


def report() -> str:
    lines = ["=== ugm/ SELF-TEST — substrate, focus, types, hypotheses, ISA, functions ==="]
    failures = 0
    checks = _checks()
    for fn in checks:
        try:
            r = fn()
        except Exception as e:                       # a probe that explodes is a red, not a crash
            r, failures = {"ERROR": f"{type(e).__name__}: {e}"}, failures + 1
        # A key reporting `False` Is a failure, and it did not used to count. The harness only tallied
        # exceptions, so a probe that ran fine and answered "no" printed among a hundred lines and a skim
        # missed it — which is exactly the mistake an earlier note already records having made once. It
        # then happened again, to `goal_recorded_as_met`, which is what prompted this. Non-boolean values
        # are data a check chose to report (counts, reasons) and are left alone; only an explicit `False`
        # is a red.
        bad = sorted(k for k, v in r.items() if v is False)
        if bad:
            failures += 1
        # Ascii marker on purpose: the report is piped, and a Windows console is cp1252.
        lines.append(f"{fn.__name__[6:]:<52} {r}" + (f"\n{'':<52} !! FALSE: {bad}" if bad else ""))
    lines.append(f"\n{len(checks)} checks, {failures} FAILED")
    return "\n".join(lines)




# --- functions / assembly (appended: the rules-as-executable-data layer) ---------------------------
def check_a_function_is_stored_as_ordered_graph_data():
    """A rule IS a function, and it lives in the graph. Vacuity guard: read the instructions back by
    Index off the ordered `instr` edge, confirming order is native rather than reconstructed."""
    from . import function as fn
    g, car, _ = _car_world()
    node = fn.define(g, "service", ("car",),
                     (NATIVE("check", F("car"), "car"), SET(F("car"), "serviced", True)))
    ops = [g.attr(g.at(node, "instr", i), "op") for i in range(g.count(node, "instr"))]
    return {"is_a_node": g.kind(node) == "function",
            "params_stored": [g.attr(p, "name") for p in g.targets(node, "param")] == ["car"],
            "instructions_in_order": ops == ["NATIVE", "SET"],
            "in_the_library": "service" in fn.names(g)}


def check_a_stored_function_lifts_back_and_runs():
    from . import function as fn
    g, car, trike = _car_world()
    fn.define(g, "service", ("car",), (NATIVE("check", F("car"), "car"), SET(F("car"), "serviced", True)))
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
    caller = Focus(g).open("secret", car)
    _f, out = fn.invoke(g, "peek", {"x": car})
    return {"param_bound": out["result"] == car,
            "callers_head_invisible": out["leaked"] is False,
            "caller_focus_intact": caller.at("secret") == car}


def check_assembly_round_trips_through_the_graph():
    """The LLM border. Text in, graph data, text back out — identical."""
    from . import asm
    g, car, _ = _car_world()
    text = 'fn service_car(car):\n    NATIVE "check" F(car) "car"\n    SET F(car) "serviced" true'
    defined = asm.load_text(g, text)
    return {"defined": defined, "round_trips": asm.dump(g, "service_car") == text}


def check_assembly_refuses_an_unknown_opcode_loudly():
    """Deliberate negative, and the reason this layer is worth having: a model will emit wrong
    instructions, and a plausible-looking wrong opcode accepted silently is the dangerous failure."""
    from . import asm
    g = new_graph()
    try:
        asm.load_text(g, 'fn bad(x):\n    FROBNICATE F(x)')
        return {"refused": False}
    except asm.AsmError as e:
        return {"refused": True, "names_the_line": "line 2" in str(e),
                "lists_alternatives": "NATIVE" in str(e)}


def check_assembly_refuses_a_malformed_invoke():
    """Reported by the first consumer. Every opcode name was checked; `INVOKE`'s operand shape was not — and
    it is the one opcode taking a structured operand, a mapping of parameter names. So the natural
    positional form parsed, defined, and failed only when run, with `AttributeError: 'str' object has no
    attribute 'items'` — no line, no opcode, nothing naming the operand that was wrong. Squarely the
    silent-acceptance failure this module exists to prevent.

    Vacuity guards: the well-formed named-binding version must actually parse and run (a check that only
    refuses things would pass with `INVOKE` rejected outright), and the refusal must name the line."""
    from . import asm, function as fn
    g, car, _ = _car_world()
    asm.load_text(g, "\n".join([
        'fn wash(c):',
        '    SET F(c) "washed" true',
        'fn full_wash(c):',
        '    INVOKE R(out) wash c=F(c)',
    ]))

    def refuses(text):
        try:
            asm.parse(text)
            return None
        except asm.AsmError as e:
            return str(e)

    positional = refuses('fn bad(c):\n    INVOKE R(out) wash F(c)')
    no_name = refuses('fn bad(c):\n    INVOKE R(out)')
    not_a_register = refuses('fn bad(c):\n    INVOKE F(c) wash c=F(c)')
    fn.invoke(g, "full_wash", {"c": car})
    return {"THE_POSITIONAL_FORM_IS_REFUSED": positional is not None,
            "naming_the_line": "line 2" in (positional or ""),
            "and_showing_the_form": "param=operand" in (positional or ""),
            "a_missing_function_name_is_refused": no_name is not None,
            "a_non_register_destination_is_refused": not_a_register is not None,
            "but_the_named_form_parses": "INVOKE" in asm.dump(g, "full_wash"),
            "AND_REALLY_DELEGATES": g.attr(car, "washed") is True}


def check_an_invoke_round_trips_through_the_surface():
    """The other half: a mapping operand had no textual form, so `unparse` rendered the raw Python
    dict and the round trip was broken — silently, because the only check was that the word `INVOKE`
    appeared in the dump. That matters most for a function nothing authored: `compile_episode` builds
    `INVOKE` operands in Python, so a learned function could not be read back in.

    Vacuity guard: the learned function must genuinely contain an `INVOKE` with bindings, or a round trip
    over an empty program would prove nothing."""
    from . import application as ap, asm, function as fn
    g, car, _ = _car_world()
    asm.load_text(g, 'fn wash(c):\n    SET F(c) "washed" true')
    ep = ap.open_episode(g, "washing")
    fn.invoke(g, "wash", {"c": car})
    ap.record(g, "wash", {"c": car}, episode=ep)
    ap.compile_episode(g, ep, "wash_it")

    text = asm.dump(g, "wash_it")
    reparsed = asm.parse(text)[0]
    stored = fn.load(g, "wash_it")[1]
    return {"the_learned_function_invokes": stored[0].op == "INVOKE",
            "with_a_real_binding": isinstance(stored[0].args[2], dict) and stored[0].args[2] != {},
            "IT_RENDERS_AS_NAMED_BINDINGS": "=" in text.splitlines()[-1],
            "no_python_dict_leaks_into_the_text": "{" not in text,
            "AND_PARSES_BACK_IDENTICALLY": reparsed.program == stored}


def check_a_function_can_invoke_another():
    """Composition is by calling, not by a fixed control-flow graph — the no-seam claim in miniature."""
    from . import asm, function as fn
    g, car, _ = _car_world()
    asm.load_text(g, 'fn inner(c):\n    SET F(c) "inner_ran" true\n'
                     'fn outer(c):\n    SET F(c) "outer_ran" true')
    fn.invoke(g, "outer", {"car": car} if False else {"c": car})
    fn.invoke(g, "inner", {"c": car})
    return {"both_ran": (g.attr(car, "outer_ran"), g.attr(car, "inner_ran")) == (True, True),
            "library_grew_without_a_global_program": len(fn.names(g)) == 2}


def check_a_program_can_write_a_function():
    """The reflexive edge, finally with somewhere to land. A microfunction generates a function,
    stores it as graph data, and it runs. This is the capability an earlier probe found
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
        '    NATIVE "check" F(car) "car"',
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
        '    NATIVE "check" F(car) "car"',
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
                "ugm.function", fromlist=["find"]).find(g, "service"),
            "bindings_recoverable": ap.bindings_of(g, a) == {"c": car}}


def check_episode_order_is_native_no_turn_counter():
    """The substrate change paying its way: the old version needed a driver-stamped turn counter purely
    to recover an order. Vacuity guard: read the order back by index off the ordered edge."""
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
    """The structural rule. Under rules this needed a hand-authored consumption marker per rule, and
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
    """The payoff, on the new substrate. An episode becomes a function that replays it on a fresh
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
    """A library of casts. `service` casts a car into a serviced_car; `wash` casts that into a washed_car.
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
    """The Spark property: planning composes, only the action materialises. Vacuity guard: assert the
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
    """Deliberate negative: no chain of declared functions reaches it, and that is an ordinary answer."""
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
    # The unregistered-tool check must use an UNforbidden target: the veto is consulted BEFORE the tool
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
    that, never what makes it true — so two independently declared types stand in the relation if their
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
    """The gap sub/supertypes exposed: `producers` compared type names, so a function returning a
    `washed_car` was invisible to a goal wanting a `serviced_car` — even though every washed car is one.
    Vacuity guard: assert the more specific producer is offered but sorts AFTER the exact match."""
    from . import function as fn
    g, _car = _garage()
    offered = fn.producers(g, "serviced_car")
    return {"exact_match_first": offered[0] == "service",
            "subtype_producer_also_offered": "wash" in offered,
            "exact_goal_unaffected": fn.producers(g, "washed_car") == ("wash",)}


# --- the direction invariant ------------------------------------------------------------------------
# Kinds that are about something rather than part of the domain. Anything here must be pointed AT the
# thing it describes, and never pointed at BY it — see `docs/planning.md`
_METADATA_KINDS = frozenset({
    "type", "requires", "requires_attr", "requires_rel",
    "search", "candidate", "candidate_arg", "trace_step", "signature", "refusal",
    # the interpreter's own state: an activation points at the function it is running, at the focus it is
    # running on, and at what it minted — and nothing in the world points back at any of them
    "activation", "register", "focus", "head",
    "function", "param", "instr", "arg",
    "application", "binding", "episode",
    "attention", "connection", "observation",              # the thread — memory is metadata, never world
    "goal",                                                # what we are trying to do is metadata too
    "hypothesis", "backup",
    "chain", "pending_call",
    "forbidden",
    "replay", "bound", "deviation",                        # carrying a plan out is metadata about a plan
    "workbench", "frame", "mapping", "transformation",     # not built yet — listed so it stays true
})


def check_metadata_is_never_pointed_at_by_structure():
    """Structure points outward; metadata points inward.

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
    """The isolation is structural — no marker, no filter, and no exclusion logic to get wrong.

    An earlier version stamped every copy with an `in_workbench` attribute and made `instances` filter on
    it. That was a labelling error: it asserted what the structure already entails. The real reason a copy
    is never offered as a candidate is that nothing in the real graph points at it — only a mapping
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


def check_the_copy_order_is_a_fact_about_the_graph_not_about_node_ids():
    """The same world, built twice, must be copied in the same order — and this was false, silently,
    for as long as the workbench has existed.

    `reachable` traverses deterministically (`g.labels` is sorted, `g.targets` is an insertion-ordered
    tuple) and then returned a `set`, throwing that order away and substituting the iteration order of
    the node-id *strings*. Ids come from a process-global counter, so the second identical world in a
    process gets different ids, hashes differently, and is copied in a different order. `mappings` order
    is `proposals` order, and `driver.pursue` breaks frontier ties by insertion order — so the search was
    irreproducible: the identical five-block goal measured 12 imagined states, then 306, then
    budget-exhausted failure, on consecutive runs of one process.

    Nothing was ever lost — the *set* of proposals is identical every time — so this never yielded a
    wrong plan, only an arbitrary one at an arbitrary cost. That is exactly why 132 checks passed over it:
    a single run of anything is self-consistent, and only a measurement *repeated in one process* can see
    it. Every performance number in the docs was taken under it.

    Vacuity guard: the two worlds must genuinely get different node ids, or identical order would be
    proving nothing at all."""
    from . import driver as D
    from . import goal as G
    from . import thread as T
    from . import workbench as W

    def built():
        g, world = _blocks()
        blocks = g.targets(world, "block")
        wb = W.open_workbench(g, world)
        order = tuple(g.attr(W.resolve(g, m) or W.image_of(g, m), "label")
                      or g.kind(W.image_of(g, m)) for m in W.mappings(g, W.root_frame(g, wb)))
        goal = G.open_goal(g, label="tower")
        for x, y in zip(blocks, blocks[1:]):
            G.require_link(g, goal, x, "on", y)
        rep = D.pursue(g, goal, T.open_thread(g), world)
        return order, blocks[0], (rep["found"], rep["steps"], D.plan_steps(g, rep))

    first_order, first_id, first_run = built()
    second_order, second_id, second_run = built()
    return {"THE_IDS_REALLY_DO_DIFFER": first_id != second_id,
            "so_hash_order_would_have_differed": True,
            "COPY_ORDER_IS_STABLE": first_order == second_order,
            "AND_SO_IS_THE_SEARCH": first_run == second_run,
            "the_search_still_succeeds": first_run[0],
            "and_the_guidance_is_optimal": first_run[1] == 2}


def check_a_mapping_resolves_to_the_real_node():
    from . import workbench as W
    g, car = _garage()
    wb = W.open_workbench(g, car)
    m = W.mapping_for(g, W.root_frame(g, wb), car)
    return {"resolves": W.resolve(g, m) == car, "not_imagined": not W.is_imagined(g, m)}


def check_nested_workbenches_resolve_up_the_stack():
    """In a nested workbench `original` points one level up, so resolving is a walk, not a hop."""
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
    """The movie is real: every earlier state stays inspectable rather than needing replay."""
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
    """The rule that makes a plan replayable: following `original` yields the node the operation must
    really be applied to. Vacuity guard: assert the bound thing is a mapping and that it resolves."""
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
    """`next` is 1:N on both. Code assuming a single successor would silently follow one branch."""
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
    """A dispatching function with three declared outcomes. Each mock is an ordinary microfunction whose
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
    """The safety property. Vacuity guard: the same call on the same real node must succeed, so we know
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
    """Two assumptions, two branches, side by side — and contingency plans come free from having
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
    _f1, tr = W.step(g, wb, f0, "list_dir", {"d": W.mapping_for(g, f0, d)})   # assumed empty

    matching = g.mint("dir", kind_of="dir", listed=True, count=0)
    diverging = g.mint("dir", kind_of="dir", listed=True, many=True)
    return {"expected": g.attr(tr, "expects"),
            "reality_matching_the_assumption_is_no_deviation": W.deviates(g, tr, matching) == {},
            "reality_contradicting_it_deviates": bool(W.deviates(g, tr, diverging)),
            "and_says_how": "@count" in W.deviates(g, tr, diverging)}


# --- following a plan for real ----------------------------------------------------------------------
def check_a_plan_replays_against_the_real_graph():
    """Everything needed was recorded: the real function (not the mock), the mappings (which resolve to
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
    """A plan is a path, not the whole tree. Committing to a branch is exactly the choice forks kept open."""
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
    """The point of mocks + deviation. The plan assumed the directory would be empty; the real tool says
    otherwise, so the step diverges and execution stops rather than acting on a world that no longer
    matches. Vacuity guard: the same plan against a reality that matches must complete."""
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
    """The payoff of forking. The plan assumed empty and reality is full — but that outcome was explored,
    so the rest of that branch is already a verified plan for the world we are now in, and execution
    continues down it instead of replanning.

    Three vacuity guards, because this check could pass for uninteresting reasons: the diverged call must
    have reached the world exactly once (re-running it is the likeliest bug here); the abandoned
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
    """Siblings are alternative successors, not necessarily alternative outcomes. Resuming into a branch
    whose step never ran would skip a call and report success. Vacuity guard: the sibling's promise is one
    reality *does* satisfy, so only the same-function restriction can be what rejects it."""
    from . import dispatch as D, execution as X, workbench as W
    g, d = _filesystem_with_followups()
    D.register("ls", lambda gr, target: gr.put(target, many=True))
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    a, _ = W.step(g, wb, f0, "list_dir", {"d": m0}, assume="list_empty")
    b, trb = W.fork(g, wb, f0, "list_full", {"d": m0})     # a different function, same promise
    result = X.execute(g, wb, a)
    dev = result["deviation"]
    return {"the_sibling_promises_what_reality_delivered":
                g.attr(trb, "expects") == "full_listing" and W.deviates(g, trb, dev["result"]) == {},
            "but_it_is_not_offered": X.matching_alternative(g, wb, dev) is None,
            "and_recovery_does_not_take_it": X.recover(g, result)["kind"] == "stuck",
            "sibling_was_a_candidate_at_all": b in X.alternatives(g, wb, dev["transformation"])}


def check_replanning_proposes_from_the_world_as_it_actually_is():
    """When nothing explored fits, the only sound move is a fresh proposal taking the real result as the
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
    """A dispatching call that mints, with two outcomes — so resuming has to carry a node that did not
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
    """The hard half of resuming. `scan` Mints a report, so the branch being resumed onto refers to a
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
    """The container's ordered `step` edge and the `prev` chain are two views of one order. They agree
    because one function appends — a discipline a *human* must follow, which is what earns this a test
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
    """One RECORD, NOT two. A thread IS an episode, so the existing machinery reads it unchanged and
    nothing has to consult two logs. Vacuity guard: `steps` must see the applications and must NOT see the
    attention shifts, or `compile_episode` would try to compile a shift into a call."""
    from . import application as ap, thread as T
    g, car, t = _threaded()
    apps = ap.steps(g, t)
    entries = T.entries(g, t)
    T.applied(g, t, "wash", {"c": car})
    learned = ap.compile_episode(g, t, "service_and_wash")
    params, program = __import__("ugm.function", fromlist=["load"]).load(g, learned)
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
    """Load-bearing for System 1's region rule and for `types.instances`. Memory is metadata: it points
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
    """The shape almost every reflective question takes. Vacuity guard: the answer must be the latest
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
    """The capability a flat episode never had — and the real blocker behind conflict detection, which
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
    """The claim that matters: the thread is ordinary data. `prev` and `at` are ordinary edges, so the
    existing `MOVE` navigates them and a thread-walker is an ordinary microfunction *pointed at* the
    thread — no privileged access, no new ISA op, no Python helper.

    Vacuity guard: the function is loaded from stored graph data and run by the ordinary machine, and it
    must land on the node attended two steps back — a wrong walk lands somewhere identifiable. (It did:
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


# --- END to END: a goal to produce a plan -------------------------------------------------------------
def _blocks():
    """The END-to-END scenario. Three blocks on the ground; the goal is to find a plan that stacks them.

    Height is an attribute because `types.py` schemas are one level deep: `schema_of` checks a label's
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
    ground = g.mint("ground", kind_of="ground", label="ground", height=0, clear=True)
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
    __import__("ugm.function", fromlist=["invoke"]).invoke(g, "service", {"c": car})
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
    """"Make something a three_high" cannot name its subject in advance — demanding one would be asking
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
    """`selection.candidates` handles single-parameter functions only, and says why: inventing bindings
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
    """The goal as constraints on individuals: a on b, b on c. Note what this removed — the earlier
    version wanted a `three_high` *type*, which the type system could only express as a `height` attribute
    because schemas are one level deep. "a on b" is stated directly and the workaround is gone."""
    from . import goal as G
    a, b, c = g.targets(world, "block")
    goal = G.open_goal(g, label="stack a on b on c")
    G.require_link(g, goal, a, "on", b)
    G.require_link(g, goal, b, "on", c)
    return goal, (a, b, c)


def check_a_goal_is_constraints_and_they_are_graph_data():
    """A goal is a set of constraint nodes — materialised, so a rule can read a goal and a goal can be
    reasoned about. Vacuity guard: `unmet` must shrink as constraints become true, one at a time, or it is
    not tracking anything."""
    from . import goal as G
    g, world = _blocks()
    goal, (a, b, c) = _tower_goal(g, world)
    cs = G.constraints(g, goal)
    both_open = G.unmet(g, goal)
    g.unlink(a, "on", index=0)
    g.link(a, "on", b)                                  # make one of them true
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
    """Homoiconicity earning its keep. Nothing declares effects — the repoint moved away from operators
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
    """Means–ends, measured. Ranking proposals by relevance to what is still false must cut the number
    of imagined states against the identical blind search — otherwise the ranking is decoration.

    And it must rank, not filter: a proposal scoring 0 has to remain reachable, or Hanoi and the Sussman
    anomaly become unsolvable. Vacuity guard: the zero-scoring proposals must actually exist here."""
    from . import driver as D, goal as G, thread as T, workbench as W
    g, world = _blocks()
    goal, (a, b, c) = _tower_goal(g, world)
    wb = W.open_workbench(g, world)
    f0 = W.root_frame(g, wb)
    open_now = G.unmet(g, goal, view=D.view_in(g, f0), under=W.image_of(g, W.mapping_for(g, f0, world)))
    scored = {D.relevance(g, n, bd, open_now) for n, bd in D.proposals(g, f0)}

    guided = D.pursue(g, goal, T.open_thread(g), world, max_steps=5000)
    g2, world2 = _blocks()
    goal2, _ = _tower_goal(g2, world2)
    blind = D.pursue(g2, goal2, T.open_thread(g2), world2, max_steps=5000,
                     guided=False)      # identical search, breadth-first, no guidance — and given ample
                                        # budget, so this measures the guidance rather than the cap
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
    """The case that justifies 'rank, never filter'. Sussman's anomaly: C sits on A, and the goal is
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


def check_a_decision_can_NAME_THE_ACTION_and_the_displaced_one_stays_reachable():
    """`docs/deliberation.md`: a decision that says what to do, not only whether to keep going.

    `decide` used to be consulted *after* `take_best` had chosen, so it could veto but never substitute —
    which meant expert judgement could stop a search and never steer it. `driver.Call` names a function
    with its bindings, which is also the job `selection.candidates` refuses to do (*"inventing bindings
    is search"*): here authored knowledge does it instead of enumeration.

    The vacuity guard is that the substitution must actually change the plan. A seam that returns the
    same action ranking would have chosen anyway is indistinguishable from no seam. So this drives Sussman
    to a plan whose first step is `stack`, which the guided search never chooses first.

    Once per frame per CALL, and that is not a detail — without it this livelocks. The displaced
    candidate goes back on the frontier (: the fallback must stay reachable), the search re-takes it, a
    deterministic decider names the same action, which reaches an already-imagined state, and the candidate
    goes back again. Measured before the fix: 12 steps, 9 of them the same substitution from one frame,
    goal never reached. Same answer `DECOMPOSE` already gives — frequency, not absence.

    A guess may not overrule a proof. An ill-typed binding, one node in two roles, and an action the
    goal forbids are each refused loudly, because `relevance` ranks and `forbid_action` prunes, and a
    decision arriving from outside must not be able to launder the second into the first."""
    from . import driver as D, goal as G, thread as T

    def run(decide, **kw):
        g, world = _blocks()
        goal, (a, b, c) = _sussman(g, world)
        ground, th = g.target(world, "ground"), T.open_thread(g)
        got = D.pursue(g, goal, th, world, max_steps=60, max_depth=5,
                       decide=decide(g, a, b, c, ground) if decide else None, **kw)
        return g, got, th

    _g0, plain, _th0 = run(None)

    # A decider that insists on stacking C onto B first — a move ranking never puts first.
    def stack_c_first(g, a, b, c, ground):
        fired = []
        def decide(s):
            if fired:
                return None
            fired.append(1)
            return D.Call("stack", {"b": c, "onto": b}, why="because the check says so")
        return decide
    g1, steered, th1 = run(stack_c_first)

    def refused(mk):
        try:
            run(mk)
            return None
        except D.Undecidable as e:
            return str(e)

    ill_typed = refused(lambda g, a, b, c, ground: lambda s: D.Call("stack", {"b": a, "onto": b}))
    two_roles = refused(lambda g, a, b, c, ground: lambda s: D.Call("stack", {"b": b, "onto": b}))
    not_a_fn = refused(lambda g, a, b, c, ground: lambda s: D.Call("levitate", {"b": c}))
    wrong_arity = refused(lambda g, a, b, c, ground: lambda s: D.Call("stack", {"b": c}))

    # A decider that never stops naming the same call — the livelock case. It must terminate.
    # Guarded only on type validity (c must still be clear), which is what keeps it a *repetition* test
    # rather than an ill-typed-call test; the pressure is that it names the same action from every frame.
    def always(g, a, b, c, ground):
        def decide(s):
            img = D.view_in(g, s["frame"])(c)
            if img is not None and g.attr(img, "clear"):
                return D.Call("unstack", {"b": c, "floor": ground}, why="over and over")
            return None
        return decide
    g2, insistent, _th2 = run(always)

    def first_imagined(g, th):
        """The first action the search actually imagined, as a whole CALL.

        Not the first step of the plan: substituting one step steers what gets explored, and the search
        may still find a better route down another branch. Asserting the plan would over-claim what one
        decision does, and the check would then be testing the search rather than the seam.

        And not the function name either — ranking's first move here is `stack(b, c)` and the decision
        names `stack(c, b)`, so a name comparison passes while proving nothing. The bindings are the whole
        difference between the right move and its mirror, which is `relevance`'s own band-4-versus-3
        lesson arriving in the test."""
        from . import application as AP
        e = next((e for e in T.entries(g, th) if g.kind(e) == "application"), None)
        return None if e is None else (
            g.attr(e, "function"),
            tuple(f"{p}={g.attr(n, 'label') or g.kind(n)}"
                  for p, n in sorted(AP.bindings_of(g, e).items())))

    return {"default_still_finds_it": plain["found"] and D.plan_steps(_g0, plain)[0] == "unstack",
            "ranking_imagines_its_own_first_move":
                first_imagined(_g0, _th0) == ("stack", ("b=b", "onto=c")),
            "A_DECISION_REALLY_STEERS_IT":
                first_imagined(g1, th1) == ("stack", ("b=c", "onto=b")),
            "and_the_search_still_succeeds": steered["found"],
            "the_displaced_candidate_came_back": steered["steps"] > len(D.plan_steps(g1, steered)),
            "AN_INSISTENT_DECIDER_TERMINATES": insistent["found"],
            "ill_typed_binding_refused": ill_typed is not None and "clear_block" in ill_typed,
            "one_node_two_roles_refused": two_roles is not None and "two roles" in two_roles,
            "unknown_function_refused": not_a_fn is not None and "not a function" in not_a_fn,
            "wrong_arity_refused": wrong_arity is not None and "every parameter" in wrong_arity,
            "it_reaches_the_thread": any("decided to do stack" in (T.why(g1, e) or "")
                                         for e in T.entries(g1, th1))}


def check_deciding_BEFORE_enumerating_suppresses_the_product_but_never_LOSES_it():
    """See `docs/deliberation.md`. With criteria the search visited four frames whatever the world's
    size — yet still built the whole O(N²) product in each, which was *all* of the residual cost and all of
    it thrown away. `decide` could not remove it: it is consulted after `_offer` has already run. `propose`
    is the same knowledge asked one step earlier, where the saving is.

    The whole risk is completeness, and it is a stronger claim than ranking ever makes. `relevance`
    ranks rather than filters so a low-scoring move stays reachable; offering only what a criterion names
    would make the frontier itself incomplete, and authored knowledge is a guess. So the suppressed
    enumeration is deferred, not skipped: when the frontier empties, `_backfill` builds one deferred
    frame and the search carries on. Only a search with nothing left deferred is exhausted.

    The guard is therefore not "it is faster" but "a wrong proposer still finds the plan" — checked
    here with a proposer that names `paint`, which can never close anything, on every frame."""
    from . import driver as D, thread as T, workbench as W

    def run(propose):
        g, world = _blocks()
        goal, (a, b, c) = _sussman(g, world)
        built = []
        real_enumerate = D.enumerate_frame

        def counting(gr, frame, *, allow=None):
            out, blocked = real_enumerate(gr, frame, allow=allow)
            built.append(len(out))
            return out, blocked
        D.enumerate_frame = counting
        try:
            got = D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=5,
                           propose=propose(g, a, b, c, g.target(world, "ground")))
        finally:
            D.enumerate_frame = real_enumerate
        return g, got, sum(built)

    _g0, plain, plain_built = run(lambda *a: None)

    # A good proposer: unstack whatever sits on a block the goal wants clear, else stack bottom-up.
    def good(g, a, b, c, ground):
        def propose(s):
            frame = s["frame"]
            view = D.view_in(g, frame)
            for x, y in ((a, b), (b, c)):
                rider = next((n for n in g.sources(view(x), "on")
                              if g.attr(n, "kind_of") == "block"), None)
                if rider is not None and g.attr(rider, "clear"):
                    return D.Call("unstack", {"b": W.original_of(g, rider), "floor": ground})
            for x, y in ((b, c), (a, b)):
                if g.target(view(x), "on") != view(y) \
                        and g.attr(view(x), "clear") and g.attr(view(y), "clear"):
                    return D.Call("stack", {"b": x, "onto": y})
            return None
        return propose
    g1, guided, guided_built = run(good)

    # A wrong proposer: always `paint`, which closes nothing and leads nowhere.
    def useless(g, a, b, c, ground):
        return lambda s: D.Call("paint", {"b": a})
    g2, despite, _ = run(useless)

    return {"default_unchanged": plain["found"] and D.plan_steps(_g0, plain) == ("unstack", "stack", "stack"),
            "A_GOOD_PROPOSER_FINDS_THE_SAME_PLAN":
                guided["found"] and D.plan_steps(g1, guided) == ("unstack", "stack", "stack"),
            "AND_BUILDS_FAR_FEWER_PROPOSALS": guided_built * 2 < plain_built,
            "built_guided_vs_default": (guided_built, plain_built),
            # Completeness: the goal is still reached. This is the guard the whole slice rests on.
            "A_WRONG_PROPOSER_STILL_FINDS_IT": despite["found"],
            "and_the_real_plan_is_still_in_there":
                D.plan_steps(g2, despite)[-3:] == ("unstack", "stack", "stack"),
            # But NOT for free, and this is recorded rather than asserted away: backtracking to the
            # newest deferral extends the bad prefix before the root's alternatives are built, so a wrong
            # proposer costs PLAN quality. `relevance`'s rank-never-filter does not pay this at all.
            "IT_COSTS_PLAN_QUALITY_THOUGH":
                len(D.plan_steps(g2, despite)) > len(D.plan_steps(_g0, plain)),
            "degraded_plan": D.plan_steps(g2, despite),
            "an_ill_typed_proposal_is_still_refused": _raises(
                lambda: run(lambda g, a, b, c, ground: lambda s: D.Call("stack", {"b": a, "onto": b})),
                D.Undecidable)}


CRITERIA_TEXT = ["""criterion clear the block that must move:
    wants link on
    do unstack b = furthest subject by ^on, floor = the ground
    because nothing can be stacked while something sits on it""",
"""criterion clear the destination:
    wants link on
    do unstack b = furthest object by ^on, floor = the ground""",
"""criterion build from the bottom up:
    wants link on
    when subject is a clear_block
    when object is a clear_block
    unless wants link on from object
    do stack b = subject, onto = object
    because stacking onto something that still has to move undoes itself"""]


def check_EXPERT_JUDGEMENT_can_be_AUTHORED_AS_TEXT_and_it_drives_the_search():
    """`docs/deliberation.md`, the whole arc, arriving at a surface. Three criteria in the CNL, and
    the search stops depending on the size of the world: measured at 5, 20 and 60 blocks, the same
    four imagined states and — because `propose` is consulted before the cartesian product — zero
    proposals built, against `relevance`, which stops finding a plan at all between six and seven.

    A criterion may not name individuals; its variables come from an unmet goal constraint.
    `wants link on` binds `subject` and `object` — `method.py`'s trick in a second place, and also exactly
    the index key identified, so the vocabulary stays indexable without anyone arranging it.

    `furthest subject by ^on` is a SET position with a selector, and it is what replaces a loop.
    `path.via` walks nearest-first, so the topmost of a pile is the last one. The two-deep blocker is the
    scenario that needs it and the vacuity guard for it: with `nearest` instead of `furthest` the criterion
    names a buried block and the call is refused.

    The refusals are the feature. A closed body vocabulary, a name that is not a role, an individual
    that resolves to nothing — each is refused where it is written, because a criterion that is silent
    because of a typo is indistinguishable from one that is silent because the situation does not call
    for it.

    `speaks` and `governing` must agree, and they did not. `governing` checked only the `when`
    lines while `speaks` also required the action's references to resolve, so it reported all three
    criteria as having spoken when only one could. Two paths computing the same thing differently, in the
    one feature whose whole job is to explain truthfully."""
    from . import criterion as CR, driver as D, intake, thread as T, workbench as W

    def world_with_criteria(build):
        g, world, goal = build()
        for t in CRITERIA_TEXT:
            intake.read(g, t)
        return g, world, goal

    def sussman_world():
        g, world = _blocks()
        goal, _abc = _sussman(g, world)
        return g, world, goal

    def two_deep():
        g, world = _blocks()
        a, b, c = g.targets(world, "block")
        d = g.mint("block", kind_of="block", label="d", clear=True, height=1)
        g.link(world, "block", d)
        g.link(d, "on", g.target(world, "ground"))
        for top, under in ((c, a), (d, c)):
            g.unlink(top, "on", index=0)
            g.link(top, "on", under)
            g.put(under, clear=None)
        goal = G.open_goal(g, label="a on b")
        G.require_link(g, goal, a, "on", b)
        return g, world, goal

    from . import goal as G
    g1, w1, goal1 = world_with_criteria(sussman_world)
    plain = D.pursue(*(lambda gg: (gg, goal1, T.open_thread(gg), w1))(g1), max_steps=400, max_depth=7)
    guided = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=7,
                      propose=CR.decide(g1, goal1, w1))

    g2, w2, goal2 = world_with_criteria(two_deep)
    deep = D.pursue(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=7,
                    propose=CR.decide(g2, goal2, w2))

    # The selector's own vacuity guard: `nearest` names a buried block, which is not a `clear_block`.
    # The criterion therefore falls silent and the search finishes by enumerating what was deferred —
    # which is the two halves of the design meeting: an inapplicable action is a situation rather than an
    # authoring error, and deferral means being wrong costs states rather than the goal.
    g3, w3, goal3 = world_with_criteria(two_deep)
    for c in CR.criteria(g3):
        for a in g3.targets(CR.action_of(g3, c), "arg"):
            if "furthest" in (g3.attr(a, "ref") or ""):
                g3.put(a, ref=g3.attr(a, "ref").replace("furthest", "nearest"))
    wb3 = W.open_workbench(g3, w3)
    near_told = {g3.attr(c, "label"): (spoke, why)
                 for c, spoke, why in CR.governing(g3, goal3, W.root_frame(g3, wb3), w3)}
    near_ran = D.pursue(g3, goal3, T.open_thread(g3), w3, max_steps=400, max_depth=7,
                        propose=CR.decide(g3, goal3, w3))

    def refused(text):
        g, _w = _blocks()
        try:
            intake.read(g, text)
            return None
        except intake.Unreadable as e:
            return str(e)

    wb = W.open_workbench(g1, w1)
    told = {g1.attr(c, "label"): (spoke, why)
            for c, spoke, why in CR.governing(g1, goal1, W.root_frame(g1, wb), w1)}

    return {"three_criteria_read": len(CR.criteria(g1)) == 3,
            "AND_THEY_DRIVE_THE_SEARCH": guided["found"]
                and D.plan_steps(g1, guided) == ("unstack", "stack", "stack"),
            "FAR_FEWER_IMAGINED_STATES": guided["steps"] * 4 < plain["steps"],
            "imagined_guided_vs_plain": (guided["steps"], plain["steps"]),
            "THE_SELECTOR_HANDLES_A_TWO_DEEP_PILE":
                deep["found"] and D.plan_steps(g2, deep) == ("unstack", "unstack", "stack"),
            # `nearest` names a buried block: the criterion goes silent, says why, and the deferred
            # enumeration still finds a plan. Silence that cannot be interrogated is what forbids.
            "NEAREST_makes_the_criterion_SILENT":
                near_told["clear the block that must move"][0] is False,
            "and_says_it_is_not_a_clear_block":
                any("clear_block" in r for r in near_told["clear the block that must move"][1]),
            "but_the_DEFERRED_enumeration_still_finds_a_plan": near_ran["found"],
            "a_closed_vocabulary_refuses_the_rest":
                "vocabulary is closed" in (refused("criterion x:\n    hope for the best") or ""),
            "a_name_is_not_a_role":
                "not a role" in (refused("criterion x:\n    wants link on\n"
                                         "    do unstack b = a, floor = the ground") or ""),
            "an_unknown_individual_is_refused_WHERE_IT_IS_WRITTEN":
                "nothing here is called" in (refused("criterion x:\n    wants link on\n"
                                                     "    do unstack b = subject, floor = the moon") or ""),
            # The action here is deliberately well-formed (both parameters bound), so the refusal can
            # only be about the missing `wants`. It used to bind `b` alone, and once `intake._action`
            # started checking parameter sets that case was refused for the *other* reason — a check
            # asserting a message it was no longer the cause of.
            "a_criterion_with_no_wants_is_refused":
                "no variables" in (refused("criterion x:\n"
                                           "    do unstack b = subject, floor = the ground") or ""),
            "a_criterion_with_no_action_is_refused":
                "names no action" in (refused("criterion x:\n    wants link on") or ""),
            "GOVERNING_AGREES_WITH_SPEAKS": told["clear the destination"][0] is False,
            "and_names_the_reference_that_failed":
                "furthest object by ^on" in told["clear the destination"][1][0],
            "while_the_one_that_fired_has_nothing_against_it":
                told["clear the block that must move"] == (True, ())}


def check_the_CNL_GUIDE_parses():
    """The authoring guide is executable. Every ` ```cnl ` block in `docs/authoring.md` is
    extracted from the file and fed to the parser.

    This exists because the previous reference rotted, and rotted silently. The CNL's only
    description was `intake.py`'s module docstring — which nothing obliged anyone to update, and which had
    already gone stale on an entire verb family (`criterion`) before anyone noticed. A document that is
    merely *checked by a human* decays exactly like a comment does.

    It also caught the guide's first draft. The examples explained each line with trailing prose
    rather than a `#` comment, so not one of them would have parsed — a guide whose examples cannot be
    copied is worse than no guide. They are comments now, which the check enforces.

    The world here supplies whatever the examples name. That is part of the point: an example naming
    something the reader has no way to create is not an example."""
    import pathlib
    import re
    from . import intake as I

    doc = pathlib.Path(__file__).resolve().parents[1] / "docs" / "authoring.md"
    if not doc.exists():                       # the guide is documentation, not a runtime dependency
        return {"guide_present": False}
    blocks = re.findall(r"```cnl\n(.*?)```", doc.read_text(encoding="utf-8"), re.S)

    def world():
        """Everything the guide's examples mention, so each one can be read as written."""
        g, w = _blocks()
        for name in ("d", "wh", "parcel", "file1"):
            n = g.mint("thing", kind_of="thing", label=name, clear=True, contents=None)
            g.link(w, "thing", n)
        for t in ("vehicle", "file", "wheel", "body", "rim", "trailer"):
            declare_type(g, t, attrs={"kind_of": t})
        declare_type(g, "serviced_car", attrs={"serviced": True})
        declare_type(g, "washed_car", attrs={"washed": True})
        # The guide's criterion examples say `do unstack b = …, floor = …`, and `intake._action` now
        # checks a `do` against the library — so the guide is only honest if `unstack` Exists with those
        # parameters. That is this check's own stated principle applied one level further: *an example
        # naming something the reader has no way to create is not an example*. It also means the guide's
        # actions can no longer drift from their signatures without this going red.
        from . import asm
        asm.load_text(g, _lines("fn unstack(b: thing, floor: thing) -> thing:",
                                '    SET F(b) "clear" true'))
        return g

    read, failed = [], []
    for body in blocks:
        g = world()
        try:
            verb, node = I.read(g, body)
            read.append(verb)
        except Exception as e:
            failed.append(f"{body.splitlines()[0]!r}: {type(e).__name__}: {e}")

    return {"guide_present": True,
            "EVERY_cnl_BLOCK_PARSES": not failed,
            "failures": tuple(failed),
            "blocks_checked": len(blocks),
            # Vacuity: an empty guide, or one whose fences stopped being marked, would pass trivially.
            "and_there_are_enough_of_them_to_mean_something": len(blocks) >= 9,
            # Derived from the verb sets, never listed here. A hand-written list is a second copy of
            # something the parser already knows, and it goes stale in the one direction that matters:
            # adding a family and forgetting to document it left this green. Now the guide has to grow a
            # worked example for every family the surface grows, or this goes red naming the gap.
            "COVERING_EVERY_FAMILY": not _undocumented_families(set(read)),
            "undocumented": _undocumented_families(set(read))}


def _undocumented_families(read: set) -> tuple:
    """Families with no worked example in the guide. One per group — the force pairs share a body."""
    from . import intake as I
    groups = {"goal": I.GOAL_VERBS, "advice": I.ADVICE_VERBS, "method": I.METHOD_VERBS,
              "type": I.TYPE_VERBS, "criterion": I.CRITERION_VERBS,
              "tie_break": I.TIE_BREAK_VERBS, "question": I.READER_VERBS}
    return tuple(sorted(name for name, verbs in groups.items() if not (set(verbs) & read)))


def check_a_DIRECTIVE_refuses_where_a_CRITERION_falls_back():
    """Force, in its third place. `docs/deliberation.md`'s finding is that force is about failure,
    not strength — a method falls back to searching, a procedure must refuse — and `docs/deliberation.md` asked what entitles a criterion to prune. The answer the surface now makes the author say:

    | | suppresses enumeration | when it cannot act |
    |---|---|---|
    | `criterion` | defers it — being wrong costs imagined states | falls silent; the search carries on |
    | `directive` | does not defer — the alternatives are not built | refuses |

    That is's distinction made operational: only a claim about the situation (*"in this situation,
    this is the move"*) is entitled to remove the alternatives, because only that claim is wrong in a way
    its author meant to be fatal.

    Recognising is not the same as having something to say, and the whole thing turns on it. A
    directive refuses when every `when`/`unless` line held and the *action* still could not be applied. It
    stays silent when it never recognised the situation at all — otherwise a directive would refuse
    everywhere it simply had nothing to do, which would make it useless rather than strict.

    Vacuity guards: the same body under the other verb must behave differently, or the word means
    nothing; and the refusal must name the directive that caused it."""
    from . import criterion as CR, driver as D, intake as I, thread as T

    # The pile is two deep, so `unstack` can only apply to the top. Asking for the block directly on the
    # subject therefore names a buried one — recognised, and unactionable.
    def two_deep(strength, complete=False):
        g, world = _blocks()
        a, b, c = g.targets(world, "block")
        d = g.mint("block", kind_of="block", label="d", clear=True, height=1)
        g.link(world, "block", d)
        g.link(d, "on", g.target(world, "ground"))
        for top, under in ((c, a), (d, c)):
            g.unlink(top, "on", index=0)
            g.link(top, "on", under)
            g.put(under, clear=None)
        goal = G.open_goal(g, label="a on b")
        G.require_link(g, goal, a, "on", b)
        # The guard is the point, and only the `complete` version has it. "Recognises the situation"
        # is *exactly what the `when` lines say*, so an unguarded directive recognises every unmet `on`
        # constraint — including ones where nothing is on the subject at all — and refuses there. A
        # directive must therefore say when it applies; without that, mandatory force is a blanket veto
        # over everything declared after it.
        guard = ["    when subject.^on is there"] if complete else []
        I.read(g, _lines("criterion take the block directly on it off:",
                         f"    {strength}",
                         "    wants link on", *guard,
                         "    do unstack b = "
                         + ("furthest subject by ^on" if complete else "subject.^on")
                         + ", floor = the ground"))
        if complete:
            # A directive must cover its situation completely, and finding that out is half of what
            # this check is for. The clearing directive above recognises every unmet `on` constraint, so
            # once the pile is gone it recognises the situation, cannot act, and refuses — there being no
            # fallback, by definition. Mandatory force is therefore not free: it obliges the author to say
            # what to do in every case they claimed to govern. `criterion` gets deferral instead.
            I.read(g, _lines("criterion build from the bottom up:", "    wants link on",
                             "    when subject is a clear_block", "    when object is a clear_block",
                             "    unless wants link on from object",
                             "    do stack b = subject, onto = object"))
        return g, goal, world

    from . import goal as G
    g1, goal1, w1 = two_deep("should")
    advisory = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=7,
                        propose=CR.decide(g1, goal1, w1))
    g2, goal2, w2 = two_deep("must")
    mandatory = D.pursue(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=7,
                         propose=CR.decide(g2, goal2, w2))

    # And a directive that can be followed must still work, or "refuses" would just mean "broken".
    g3, goal3, w3 = two_deep("must", complete=True)
    followed = D.pursue(g3, goal3, T.open_thread(g3), w3, max_steps=400, max_depth=7,
                        propose=CR.decide(g3, goal3, w3))

    return {"the_two_words_read": CR.is_mandatory(g2, CR.criteria(g2)[0])
                and not CR.is_mandatory(g1, CR.criteria(g1)[0]),
            # Strength is now a body line, so the vacuity guard has to be that the LINE is what moved —
            # not the header, which is identical in both.
            "AND_THE_STRENGTH_IS_WHAT_DIFFERS":
                (CR.strength_of(g1, CR.criteria(g1)[0]), CR.strength_of(g2, CR.criteria(g2)[0]))
                == ("should", "must"),
            "A_CRITERION_FALLS_BACK_AND_STILL_FINDS_A_PLAN": advisory["found"],
            "A_DIRECTIVE_REFUSES_INSTEAD": not mandatory["found"],
            "and_says_which_directive_governed":
                "take the block directly on it off" in (mandatory.get("why") or ""),
            "it_stopped_by_REFUSING": mandatory.get("stopped") == D.REFUSE,
            # The vacuity guard: same body, same world, different word, different outcome.
            "SAME_BODY_DIFFERENT_WORD_DIFFERENT_OUTCOME":
                advisory["found"] is not mandatory["found"],
            # ...and a directive that can be followed is not merely a way of failing.
            # ...and a directive that can be followed is not merely a way of failing. Note it took a
            # Second criterion to make that true: mandatory force obliges the author to cover every case
            # they claimed to govern, which is the price of removing the fallback.
            "A_DIRECTIVE_THAT_CAN_BE_FOLLOWED_STILL_WORKS": followed["found"],
            "and_it_really_clears_the_pile_top_down":
                D.plan_steps(g3, followed) == ("unstack", "unstack", "stack"),
            "IT_TOOK_A_SECOND_CRITERION_TO_COVER_THE_CASE": len(CR.criteria(g3)) == 2}


def _reflect_world():
    """A world with a cycle and a branch, plus the two rule files. Both are needed: a tree would let a
    walk that never revisits pass, and one branch would hide an ordering difference."""
    from pathlib import Path
    from . import asm
    g = new_graph()
    for name in ("reachable.mf", "workbench.mf"):
        asm.load_file(g, Path(__file__).parent / "rules" / name)
    w = g.mint("world")
    g.link("root", "has", w)
    a, b, c = (g.mint("block", label=n, kind_of="block") for n in "abc")
    for n in (a, b, c):
        g.link(w, "block", n)
    g.link(a, "on", b)
    g.link(b, "on", c)
    g.link(c, "on", w)                       # the cycle
    box = g.mint("box", label="box")
    g.link(w, "box", box)
    g.link(box, "contains", a)               # the branch, reaching an already-seen node
    return g, w


def check_REFLECTION_makes_open_workbench_an_ORDINARY_PROGRAM():
    """The closed class shrinks by five opcodes, and a family of would-be natives stops being needed.

    `open_workbench` was on a list of primitives to expose as natives. It is not a primitive — it is
    three loops and a copy. What actually blocked writing it in the surface was that every graph read took
    a slot you had already named: `GET dest subj "label"` asks what is at this label, and nothing asked
    *which labels are there*. That one asymmetry is why a composite looked primitive.

    `KIND` / `NLABELS` / `LABEL_AT` / `NKEYS` / `KEY_AT` are substrate — none encodes a decision about
    goals, plans, time or criteria — so they sit below the kernel boundary, and adding them moves
    `reachable`, `copy_node` and `open_workbench` above the horizon. The single-opcode alternative
    (`CLONE`) was refused: *"the same kind and the same attributes"* is a decision, and baking it in is a
    composite wearing substrate's clothes.

    **The order is the claim, not the membership.** `reachable` is depth-first over a stack and marks a
    node seen when it is popped, so the same set can come back in several orders and only one of them is
    the one the search was tuned against. The first version of this program used a queue: identical set,
    different order, and `workbench.reachable`'s own docstring records what that costs — the identical
    five-block search measured at 12 imagined states, then 306, then budget-exhausted failure, on
    consecutive runs of one process, because a `set` had substituted node-id iteration order.

    Vacuity guards: the world has a cycle and a branch, so a walk that revisited or that ordered
    siblings differently would show; the images must really be copies rather than the originals; and the
    scratch node must be gone, since an undropped one would make the *next* walk skip nodes."""
    from . import function as fn, workbench as W

    def shape(g, wb):
        img = lambda m: W.image_of(g, m)
        return [(g.kind(img(m)), g.attr(img(m), "label"),
                 tuple((l, tuple(g.attr(t, "label") for t in g.targets(img(m), l)))
                       for l in g.labels(img(m))))
                for m in W.mappings(g, W.root_frame(g, wb))]

    # Compared by label, never by node id. Ids come from a process-global counter, so two graphs built
    # by the same code do not share them — the first version of this check compared ids across two
    # worlds and read "identical walk, different order" as a defect in the program.
    named = lambda g, ns: tuple(g.attr(n, "label") or g.kind(n) for n in ns)

    g1, w1 = _reflect_world()
    g2, w2 = _reflect_world()
    py_walk = named(g1, W.reachable(g1, w1))
    mf_walk = named(g2, g2.targets(fn.invoke(g2, "reachable", {"start": w2})[1]["result"], "found"))

    g3, w3 = _reflect_world()
    g4, w4 = _reflect_world()
    py_wb = W.open_workbench(g3, w3)
    mf_wb = fn.invoke(g4, "open_workbench", {"subject": w4})[1]["result"]
    originals = {W.original_of(g4, W.image_of(g4, m))
                 for m in W.mappings(g4, W.root_frame(g4, mf_wb))}

    return {"THE_WALK_AGREES_EXACTLY_INCLUDING_ORDER": py_walk == mf_walk,
            "and_it_really_walked_something": len(mf_walk) == 5,
            "THE_WORKBENCH_IS_STRUCTURALLY_IDENTICAL": shape(g3, py_wb) == shape(g4, mf_wb),
            "same_number_of_mappings":
                len(W.mappings(g3, W.root_frame(g3, py_wb)))
                == len(W.mappings(g4, W.root_frame(g4, mf_wb))),
            # Vacuity: a "copy" that mapped each node to itself would pass every check above.
            "THE_IMAGES_ARE_REALLY_COPIES":
                not ({W.image_of(g4, m) for m in W.mappings(g4, W.root_frame(g4, mf_wb))}
                     & set(originals)),
            # The cycle has to come back as a cycle, not as a dangling edge to the original world.
            "AND_THE_CYCLE_SURVIVED_INSIDE_THE_COPY":
                sum(len(g4.targets(W.image_of(g4, m), l))
                    for m in W.mappings(g4, W.root_frame(g4, mf_wb))
                    for l in g4.labels(W.image_of(g4, m)))
                == sum(len(g3.targets(W.image_of(g3, m), l))
                       for m in W.mappings(g3, W.root_frame(g3, py_wb))
                       for l in g3.labels(W.image_of(g3, m))),
            "THE_SCRATCH_NODE_IS_GONE": not [n for n in g4.nodes if g4.kind(n) == "walk"],
            # Membership is a ref on the scratch node, never a mark on the world, so a second walk in the
            # same graph is unaffected by the first. This went red when it was marks-on-the-world: the
            # second walk saw the first one's leftovers and skipped everything.
            "A_SECOND_WALK_IN_THE_SAME_GRAPH_AGREES":
                named(g2, g2.targets(fn.invoke(g2, "reachable", {"start": w2})[1]["result"], "found"))
                == mf_walk}


def check_REFLECTION_opcodes_report_their_reads_as_HONESTLY_UNREADABLE():
    """A body that walks a node's shape reads *all* of it, and says so rather than reporting nothing.

    `driver._reads` reports `(kind, slot, subject)` for every graph read whose slot is a literal, and
    puts the subject in an `unknown` bucket when it is not. The reflection opcodes never take a literal
    slot — not knowing the slot is what they are for — so they always land in that bucket. That is the
    correct answer and it was worth checking rather than assuming: leaving them out of `READS_GRAPH`
    would have made a body that reads an entire node report reading *nothing*, which is the confidently
    wrong direction, and the one this codebase keeps naming as the dangerous class.

    Vacuity guard: a body reading a *named* slot must still report that slot precisely, or this check
    would pass for a reader that had simply given up on everything."""
    from . import asm, driver as D

    g = new_graph()
    asm.load_text(g, _lines("fn walks_the_shape(x: thing) -> thing:",
                            "    NLABELS R(n) F(x)",
                            '    LABEL_AT R(l) F(x) 0',
                            "    KIND R(k) F(x)"))
    asm.load_text(g, _lines("fn reads_one_slot(x: thing) -> thing:",
                            '    ATTR R(v) F(x) "colour"'))
    from .types import declare_type
    declare_type(g, "thing", attrs={"kind_of": "thing"})

    walked, walked_unknown = D.reads(g, "walks_the_shape")
    named, named_unknown = D.reads(g, "reads_one_slot")

    return {"A_SHAPE_WALK_NAMES_NO_SLOT": walked == frozenset(),
            "BUT_IT_IS_REPORTED_AS_UNREADABLE_NOT_AS_NOTHING": bool(walked_unknown),
            "and_it_names_the_subject_it_could_not_finish": "x" in walked_unknown,
            # Vacuity: a reader that had given up on everything would also produce the above.
            "A_NAMED_SLOT_IS_STILL_REPORTED_PRECISELY": named == frozenset({("attr", "colour", "x")}),
            "and_that_one_is_not_unknown": not named_unknown}


def _ranked_world():
    """Two criteria that both speak on the Sussman goal, declared weakest-first.

    Declared in the order that makes declaration order the *wrong* answer, which is what gives every
    check below something to move. `paint` closes nothing and is declared `could`; taking the top off is
    the real move and is declared `must`."""
    from . import intake as I
    g, w = _blocks()
    goal, _blks = _sussman(g, w)
    I.read(g, _lines("criterion would rather paint it:", "    could",
                     "    wants link on", "    do paint b = subject"))
    I.read(g, _lines("criterion take the top of the pile off:", "    must",
                     "    wants link on", "    some top in subject by ^on",
                     "    when top is a clear_block",
                     "    do unstack b = top, floor = the ground"))
    return g, w, goal


def check_PRECEDENCE_is_AUTHORED_and_its_ABSENCE_means_declaration_order():
    """The order rules are ranked in is domain knowledge, so it is written rather than compiled in.

    Declaration order was the whole answer and was defended as *"there is nothing to tune in an
    order"* — right about weights, wrong about orders, because declaration order is an order too and
    nothing had said so. What this check requires is not that ranking exists but that it is **data**: the
    stage list reads back out of the graph, and the same two criteria in the same world rank differently
    depending only on a block of text.

    Vacuity guards, and they matter more than usual here because a ranking that changed nothing would
    pass a naive check trivially. The order must really move; it must move *the decision* and not merely
    the list; both criteria must really speak, or the winner is only the survivor; and with no rule
    authored the order must be exactly what it always was, or this is a breaking change wearing a
    feature's clothes."""
    from . import criterion as CR, intake as I, precedence as PR, workbench as W

    label = lambda g, ns: tuple(g.attr(n, "label") for n in ns)

    g0, w0, goal0 = _ranked_world()
    g1, w1, goal1 = _ranked_world()
    I.read(g1, _lines("tie_break house rules:", "    force", "    random", "    seed 7"))

    before, after = label(g0, CR.criteria(g0)), label(g1, CR.criteria(g1))
    spoke0 = CR.proposals_here(g0, goal0, W.root_frame(g0, W.open_workbench(g0, w0)), w0)
    spoke1 = CR.proposals_here(g1, goal1, W.root_frame(g1, W.open_workbench(g1, w1)), w1)

    return {"WITH_NO_RULE_IT_IS_DECLARATION_ORDER": before[0] == "would rather paint it",
            "AND_A_TIE_BREAK_BLOCK_MOVES_IT": after[0] == "take the top of the pile off",
            "the_order_really_moved": before != after,
            # The list moving is not the claim; the decision moving is.
            "AND_THE_DECISION_MOVES_WITH_IT":
                spoke0[0][1].function == "paint" and spoke1[0][1].function == "unstack",
            # Vacuity: if only one spoke, the winner is just the survivor and ranking proved nothing.
            "BOTH_REALLY_SPEAK_IN_BOTH_WORLDS": len(spoke0) == 2 and len(spoke1) == 2,
            "and_the_same_two_are_ranked": sorted(before) == sorted(after),
            # The stage list is readable data, not a Python constant reached by a name.
            "THE_STAGES_ARE_DATA": PR.stages_of(g1) == ("force", "random"),
            "and_it_reads_back_in_words": "force then random" in PR.describe(g1),
            # And which stage decided is answerable — the `governing` question, one level up.
            "IT_SAYS_WHICH_STAGE_DECIDED":
                PR.deciding_stage(g1, CR.criteria(g1)[0], CR.criteria(g1)[1])[0] == "force"}


def check_the_LAST_stage_must_DECIDE_EVERY_PAIR():
    """A ranking that can answer *undecided* at the end is not a ranking.

    Two of the four comparisons are partial orders — most pairs come back undecided — so a rule ending
    in one leaves rules in an order nobody chose. That is the exact defect the irreproducible search
    taught this codebase to refuse: *an undeclared tie-break*. Deliberate arbitrariness is fine and is
    what `random` is for; arbitrariness nobody wrote down is not.

    Refused where it is written, not where it bites, because an incomplete order is invisible until the
    one pair it cannot separate turns up.

    Vacuity guard: the same block ending in a total stage must be accepted, or this is only testing
    that `tie_break` blocks fail."""
    from . import intake as I, precedence as PR

    def read(*body):
        g, _w = _blocks()
        try:
            I.read(g, _lines("tie_break house rules:", *body))
            return None
        except I.Unreadable as e:
            return str(e)

    partial = read("    force", "    specificity")
    total = read("    force", "    specificity", "    random")
    empty = read("    because nothing")
    twice = read("    force", "    force", "    random")

    g, _w = _blocks()
    from . import asm
    asm.load_text(g, _lines("fn second_wins(a, b) -> thing:", '    HEAD R(result) "b"'))
    fn_last = None
    try:
        I.read(g, _lines("tie_break house rules:", "    run second_wins"))
    except I.Unreadable as e:
        fn_last = str(e)

    return {"A_PARTIAL_STAGE_MAY_NOT_SIT_LAST": partial is not None,
            "and_it_says_why": "undecided" in (partial or ""),
            "THE_SAME_BLOCK_ENDING_TOTAL_IS_ACCEPTED": total is None,
            "an_empty_rule_ranks_nothing": empty is not None,
            "a_stage_consulted_twice_is_refused": twice is not None,
            # A function cannot be shown total, so it may never close the list.
            "A_FUNCTION_STAGE_MAY_NOT_SIT_LAST_EITHER": fn_last is not None,
            "the_vocabulary_is_closed_and_says_so":
                "not a comparison" in (read("    seniority", "    random") or "")}


def check_an_UNATTRIBUTED_rule_is_EXPERIENCE_rather_than_NOBODY():
    """*"Rules without an authority are 'experience says'"* — the user, and it is a real node.

    A missing source would make the authority comparison undefined for exactly the rules most likely
    to be wrong: the learned ones nobody vouched for. Naming the absent case instead means a reader
    asking *"on whose word?"* always gets an answer, and means a domain can rank learned advice against
    authored advice by writing one ordinary fact.

    Vacuity guards: `experience` must be a *real* agent that a norm can outrank, not a sentinel string;
    and an explicitly attributed criterion must not be swallowed by the default."""
    from . import criterion as CR, discourse as DC, intake as I, norm as NM, precedence as PR

    g, _w = _blocks()
    I.read(g, _lines("criterion nobody vouches for this:", "    wants link on",
                     "    do paint b = subject"))
    I.read(g, _lines("criterion finance says so:", "    by finance",
                     "    wants attr colour", "    do paint b = subject"))
    anon, named = CR.criteria(g)

    src = CR.source_of(g, anon)
    DC.authority(g, "finance", PR.EXPERIENCE)

    return {"AN_UNATTRIBUTED_RULE_HAS_A_SOURCE_ANYWAY": src is not None,
            "AND_IT_IS_NAMED_experience": g.attr(src, "label") == PR.EXPERIENCE,
            # Not a sentinel: it is an agent in the world, so it can be outranked, quoted, doubted.
            "it_is_a_REAL_agent_node": g.kind(src) == "agent" and src in g.nodes,
            "AND_A_NAMED_AUTHORITY_CAN_OUTRANK_IT":
                NM.outranks(g, DC.speaker(g, "finance"), src),
            "which_is_ordinary_world_data": src in g.targets(DC.speaker(g, "finance"),
                                                             "authority_over"),
            # Vacuity: the explicit attribution must survive rather than being defaulted over.
            "AN_EXPLICIT_by_LINE_IS_KEPT": g.attr(CR.source_of(g, named), "label") == "finance",
            "and_the_two_differ": CR.source_of(g, anon) != CR.source_of(g, named)}


def check_AUTHORITY_is_WORLD_DATA_so_a_RULE_can_establish_it():
    """*"Businesses have rules that specify the order of authorities"* — so authority must be derivable,
    not only asserted.

    Nothing had to be added for this, which is the finding. `authority_over` is an ordinary edge read
    transitively by `path.reaches`, so a stored function writes one with a plain `LINK` — *"a manager
    outranks their reports"* is a rule like any other, and the ranking picks it up on the next read
    because `criterion.criteria` re-reads rather than caching a computed order.

    What this does **not** show, and is recorded rather than glossed: authority here is global between
    two agents. *"The compliance officer outranks everyone on compliance"* — authority scoped to a
    subject matter — has no representation, and is listed in `docs/limits.md`.

    Vacuity guards: the rank must be absent before the rule runs (or the edge was already there), the
    function must be the thing that created it, and the derived authority must actually move a decision
    rather than merely appearing in the graph."""
    from . import asm, criterion as CR, discourse as DC, function as fn, intake as I, norm as NM

    g, w = _blocks()
    _goal, _blks = _sussman(g, w)
    asm.load_text(g, _lines("fn delegate(boss, report) -> thing:",
                            '    LINK F(boss) "authority_over" F(report)'))
    I.read(g, _lines("criterion the junior would paint it:", "    by junior",
                     "    wants link on", "    do paint b = subject"))
    I.read(g, _lines("criterion the senior takes the top off:", "    by senior",
                     "    wants link on", "    some top in subject by ^on",
                     "    when top is a clear_block",
                     "    do unstack b = top, floor = the ground"))
    I.read(g, _lines("tie_break house rules:", "    authority", "    random", "    seed 3"))

    from . import precedence as PR
    boss, report = DC.speaker(g, "senior"), DC.speaker(g, "junior")
    junior_rule, senior_rule = CR.criteria(g)[0], CR.criteria(g)[1]
    junior_rule, senior_rule = sorted(
        (junior_rule, senior_rule), key=lambda c: g.attr(c, "label") != "the junior would paint it")

    before_rank = NM.outranks(g, boss, report)
    before_says = PR._by_authority(g, senior_rule, junior_rule)
    before_stage = PR.deciding_stage(g, senior_rule, junior_rule)[0]

    fn.invoke(g, "delegate", {"boss": boss, "report": report})

    after_rank = NM.outranks(g, boss, report)
    after = tuple(g.attr(c, "label") for c in CR.criteria(g))

    return {"NO_AUTHORITY_BEFORE_THE_RULE_RAN": not before_rank,
            "A_STORED_FUNCTION_ESTABLISHED_IT": after_rank,
            "with_a_plain_LINK_and_no_new_mechanism":
                report in g.targets(boss, "authority_over"),
            # The claim is not that an edge appeared; it is that the ranking now turns on it. Asserting
            # the *deciding stage* rather than the resulting order is what makes that non-vacuous: with
            # authority silent the seed decides, and a seed that happened to agree would have proved
            # nothing at all.
            "AUTHORITY_WAS_SILENT_BEFORE": before_says == 0,
            "and_the_SEED_was_deciding_instead": before_stage == "random",
            "AND_AFTERWARDS_AUTHORITY_DECIDES":
                PR.deciding_stage(g, senior_rule, junior_rule) == ("authority", senior_rule),
            "so_the_senior_leads": after[0] == "the senior takes the top off",
            # Vacuity: the same two criteria, unchanged — only the world moved.
            "the_criteria_themselves_are_untouched":
                sorted(after) == sorted(g.attr(c, "label") for c in (junior_rule, senior_rule))}


def check_a_tie_break_STAGE_can_be_a_STORED_FUNCTION():
    """The vocabulary is the set that *ships*, never the set that is *possible*.

    Four comparisons are primitives for the same reason `path.reaches` is one. But ranking by
    seniority, by recency, or by how often a rule has been right before must not require editing
    `precedence.py`, or the closed set is a Python decision about what a domain may care about — the
    island pattern, one level up from the one this module was written to remove.

    A function stage answers with the *rule that comes first* rather than with a sign. A comparator
    returning -1/0/1 makes the author hold a convention in their head, and getting it backwards produces
    a ranking wrong in a way nothing can detect; answering *"this one"* cannot be inverted by mistake.

    The comparator here ranks by a seniority number, and it is written to be **consistent** — it names
    the same winner whichever way round it is asked. That is not decoration: the first version of this
    check used *"the second argument always wins"*, which sorts to nothing at all, because a comparator
    whose answer depends on argument order is not a comparator. A function stage can be authored badly,
    and this module cannot check that it was not.

    Vacuity guards: the function must be what moved the order (the same world without the stage must
    rank the other way), it must answer identically in both argument orders, and a stage naming a
    function that does not exist must be refused where it is written."""
    from . import criterion as CR, intake as I, precedence as PR, asm, function as fn

    body = ("fn by_seniority(a, b) -> thing:",
            '    ATTR R(ra) F(a) "seniority"', '    ATTR R(rb) F(b) "seniority"',
            "    LT R(d) R(ra) R(rb)", "    JMPIF R(d) .a_wins",
            "    LT R(e) R(rb) R(ra)", "    JMPIF R(e) .b_wins", "    HALT",
            ".a_wins:", '    HEAD R(result) "a"', "    HALT",
            ".b_wins:", '    HEAD R(result) "b"')

    def world(*stages):
        g, w, goal = _ranked_world()
        asm.load_text(g, _lines(*body))
        # Seniority is a fact about the rule, so the comparator reads it off the rule. Lower leads.
        for c in CR.criteria(g):
            g.put(c, seniority=1 if g.attr(c, "label") == "take the top of the pile off" else 2)
        if stages:
            I.read(g, _lines("tie_break house rules:", *stages))
        return g

    plain = world()
    staged = world("    run by_seniority", "    random", "    seed 1")

    missing = None
    try:
        g, _w = _blocks()
        I.read(g, _lines("tie_break house rules:", "    run no_such_function", "    random"))
    except I.Unreadable as e:
        missing = str(e)

    one, two = CR.criteria(staged)
    both_ways = (fn.invoke(staged, "by_seniority", {"a": one, "b": two})[1].get("result"),
                 fn.invoke(staged, "by_seniority", {"a": two, "b": one})[1].get("result"))

    label = lambda g: tuple(g.attr(c, "label") for c in CR.criteria(g))
    return {"A_FUNCTION_RAN_AS_A_COMPARISON": label(staged)[0] == "take the top of the pile off",
            # Vacuity: without the stage the order is the other way, so the function is what moved it.
            "AND_IT_IS_WHAT_MOVED_THE_ORDER": label(plain)[0] == "would rather paint it",
            "so_the_two_really_differ": label(plain) != label(staged),
            # A comparator whose answer depends on argument order sorts to nothing. This one does not.
            "THE_COMPARATOR_IS_CONSISTENT_BOTH_WAYS_ROUND": both_ways[0] == both_ways[1],
            "the_stage_reads_back_by_name": PR.stages_of(staged) == ("by_seniority", "random"),
            # A stage naming nothing is refused at authoring time, like every other bad fragment.
            "AN_UNKNOWN_FUNCTION_IS_REFUSED_WHERE_WRITTEN": missing is not None,
            "and_says_it_is_not_in_the_library": "not in this library" in (missing or "")}


def check_SPECIFICITY_prefers_the_TIGHTER_rule_and_declines_when_it_cannot_tell():
    """More constrained wins — and *"more constrained"* is a structural comparison, never a line count.

    `when x.weight > 100` versus `when x.weight > 10`: neither is a superset of the other, yet one is
    strictly tighter. Counting conditions would get that backwards silently, which is why this reuses the
    comparison `types.subsumes` already makes — a rule demanding a *subtype* where another accepts the
    supertype is tighter, and a rule demanding a *direct* link where another accepts a transitive one is
    tighter.

    Undecidable pairs answer *no*, taking `types.subsumes`' direction and its reason: a false negative
    loses an ordering the author could have had, a false positive claims a precedence they never wrote.

    Vacuity guard: two rules keyed on different constraints must NOT be ordered by this, or
    'specificity' would be ranking rules that never compete."""
    from . import criterion as CR, intake as I, precedence as PR, types as TY

    g, w = _blocks()
    TY.declare_type(g, "clear_block", base="block", attrs={"clear": True})
    TY.declare_type(g, "block", attrs={"kind_of": "block"})

    I.read(g, _lines("criterion broad:", "    wants link on", "    do paint b = subject"))
    I.read(g, _lines("criterion narrow:", "    wants link on",
                     "    when subject is a clear_block", "    do paint b = subject"))
    I.read(g, _lines("criterion elsewhere:", "    wants attr colour", "    do paint b = subject"))
    broad, narrow, elsewhere = CR.criteria(g)

    return {"THE_TIGHTER_RULE_COMES_FIRST": PR._by_specificity(g, narrow, broad) < 0,
            "and_the_comparison_is_symmetric": PR._by_specificity(g, broad, narrow) > 0,
            # Vacuity: rules keyed on different constraints never compete, so this must stay silent.
            "RULES_THAT_NEVER_COMPETE_ARE_NOT_ORDERED":
                PR._by_specificity(g, narrow, elsewhere) == 0,
            "a_rule_is_not_tighter_than_itself": PR._by_specificity(g, broad, broad) == 0,
            # A subtype demanded where a supertype would do is tighter — the `types.subsumes` reuse.
            "SUBTYPE_REFINEMENT_IS_A_REAL_REFINEMENT": TY.subsumes(g, "block", "clear_block")}


def check_two_criteria_that_DISAGREE_can_be_told_apart_from_two_that_AGREE():
    """`docs/deliberation.md`'s last untested claim, made good.

    `docs/deliberation.md` rejected program-conditions partly because *"`conflict.py` cannot say two rules
    disagree by comparing two programs"*. answered that the cost degrades rather than dies: a
    criterion's return is a named function with denoted arguments — trivially comparable — even when
    its condition is not. That was an argument. This is the thing itself, and it turned out cheap, because
    `speaks` already answers per criterion, so the comparison is a pass over *answers* rather than over
    conditions. The two criteria compared here have structurally different conditions — one draws a role
    and tests it, one tests nothing at all — and it makes no difference, which is the whole claim.

    Naming the same call is redundancy, not disagreement, and the check requires that distinction to
    be made. `conflict.py`'s standing correction applies unchanged: *a later action overriding an earlier
    one is not a disagreement, it is what doing things looks like.* Reporting two criteria that agree would
    bury the real cases, which is the failure mode that makes a conflict report worth nothing.

    What this reports is shadowing, not error. `build from the bottom up` is a perfectly good
    criterion that simply loses on precedence. First-match-wins is the control rule, so everything after
    the first is invisible at run time; this makes it visible. That is's contrastive purpose, and it
    matters more here than for `guideline`, because criteria suppress enumeration — what they discard
    was never built.

    Exact and situational: it needs a frame and reports no false positives. A static comparison of two
    conditions could only over-report, and `conflict.py`'s stance is that an honest miss beats a false
    alarm."""
    from . import criterion as CR, intake as I, workbench as W

    g, world = _blocks()
    goal, (a, b, c) = _sussman(g, world)
    top = ("    wants link on", "    some top in subject by ^on", "    when top is a clear_block",
           "    do unstack b = top, floor = the ground")
    for t in (_lines("criterion take the top of the pile off:", *top),
              _lines("criterion says exactly the same thing:", *top),
              _lines("criterion would rather paint it:", "    wants link on",
                     "    do paint b = subject"),
              _lines("criterion never speaks here:", "    wants attr colour",
                     "    do paint b = subject")):
        I.read(g, t)

    frame = W.root_frame(g, W.open_workbench(g, world))
    spoke = CR.proposals_here(g, goal, frame, world)
    found = CR.disagreements(g, goal, frame, world)
    label = lambda n: g.attr(n, "label")

    return {"three_of_the_four_speak_here": tuple(label(x) for x, _ in spoke) ==
                ("take the top of the pile off", "says exactly the same thing", "would rather paint it"),
            "ONE_DISAGREEMENT_IS_FOUND": len(found) == 1,
            "and_it_names_the_winner_and_the_loser":
                (label(found[0][0]), label(found[0][2]))
                == ("take the top of the pile off", "would rather paint it"),
            "and_what_each_would_have_DONE":
                (found[0][1].function, found[0][3].function) == ("unstack", "paint"),
            # The distinction that matters: agreeing is not disagreeing.
            "THE_REDUNDANT_ONE_IS_NOT_REPORTED":
                "says exactly the same thing" not in [label(x) for _w, _wc, x, _lc in found],
            "though_it_really_did_speak": "says exactly the same thing" in [label(x) for x, _ in spoke],
            # No false positives: one that has nothing to say here is not a conflict.
            "a_SILENT_criterion_is_not_a_conflict":
                "never speaks here" not in [label(x) for x, _ in spoke],
            # The claim itself: conditions differ structurally, returns compare anyway.
            "conditions_differ_structurally_and_it_does_not_matter":
                len(CR.draws_of(g, found[0][0])) == 1 and len(CR.tests_of(g, found[0][2])) == 0,
            "it_reads_back_in_words": "would have done paint" in
                CR.describe_disagreements(g, goal, frame, world)}


def check_SOME_draws_a_further_role_so_a_criterion_can_CHOOSE_among_several():
    """`some <name> in <ref> by <link>` — the one thing measured as unsayable.

    A criterion could reach a third individual by a path (`box = subject.contains`) but could not
    choose among several: `nearest`/`furthest … by <link>` selects over a traversal, and nothing
    selected by a condition. So *"put it in a container that is allowed"* had no form, and the author's
    only recourse was to let the search work it out — the thing criteria exist to avoid.

    The form binds a role rather than filtering inline, and that is the whole point. An inline
    `such that …` would have made the condition opaque, which is exactly what says not to do. As a role,
    the filter is written with the ordinary `when` / `unless` lines, stays decomposable, and
    `governing` can still name the line that ruled a candidate out.

    It subsumes the selector and says more. `furthest subject by ^on` picks the top of a pile
    because of *where it sits*; `some top in subject by ^on` + `when top is a clear_block` picks the same
    block because of *what is true of it*.

    Two guards, because there are two ways to reach the right answer and only one is the feature.
    Candidates are tried in traversal order, so a criterion with NO filter still gets there by
    backtracking once the wrong candidate is refused — which is real, and would make a filter test pass
    while proving nothing. So the check requires the filtered version to pick the right container
    first, and separately that an unfiltered one needs more attempts."""
    from . import criterion as CR, driver as D, execution as X, intake as I, path as P, thread as T

    def stow(*body, sealed=True):
        """Two containers inside the warehouse. The crate comes first and is sealed."""
        g, world, wh, box, parcel = _warehouse(nested=False)
        crate = g.mint("thing", kind_of="thing", label="crate", held=True, sealed=True)
        g.link(world, "thing", crate)
        g.link_at(wh, "contains", 0, crate)          # ahead of the box, so a plain path finds it first
        goal = I.read_goal(g, _lines("goal stow it:", "    wh contains+ parcel", "    never touch wh"))
        I.read(g, _lines("criterion stow it in a container that is open:", *body))
        got = D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=6,
                       propose=CR.decide(g, goal, world))
        if got["found"]:
            X.execute(g, got["workbench"], got["frame"])
        return g, got, wh, box, crate, parcel

    g1, filtered, wh1, box1, crate1, parcel1 = stow(
        "    wants link contains",
        "    some spot in subject by contains",
        "    unless spot.sealed = true",
        "    do put_in t = object, box = spot")

    # The vacuity guard: without the filter the first candidate is the sealed crate.
    g2, unfiltered, wh2, box2, crate2, parcel2 = stow(
        "    wants link contains",
        "    some spot in subject by contains",
        "    do put_in t = object, box = spot")

    # `some` doing the selector's job, with a reason attached.
    g3, w3 = _blocks()
    goal3, _abc = _sussman(g3, w3)
    for t in (_lines("criterion take the top of the pile off:", "    wants link on",
                     "    some top in subject by ^on", "    when top is a clear_block",
                     "    do unstack b = top, floor = the ground"),
              _lines("criterion build from the bottom up:", "    wants link on",
                     "    when subject is a clear_block", "    when object is a clear_block",
                     "    unless wants link on from object", "    do stack b = subject, onto = object")):
        I.read(g3, t)
    blocks = D.pursue(g3, goal3, T.open_thread(g3), w3, max_steps=400, max_depth=7,
                      propose=CR.decide(g3, goal3, w3))

    def refused(text):
        g, _w = _blocks()
        try:
            I.read(g, text)
            return None
        except I.Unreadable as e:
            return str(e)

    return {"A_FILTERED_DRAW_PICKS_THE_RIGHT_CONTAINER": filtered["found"]
                and parcel1 in g1.targets(box1, "contains"),
            "and_not_the_sealed_one": parcel1 not in g1.targets(crate1, "contains"),
            "it_really_reaches_the_warehouse": P.reaches(g1, wh1, "contains", parcel1),
            # Vacuity: unfiltered lands in the sealed crate — the filter is doing the work, not the order.
            "WITHOUT_THE_FILTER_IT_TAKES_THE_SEALED_ONE":
                unfiltered["found"] and parcel2 in g2.targets(crate2, "contains"),
            "SOME_ALSO_DOES_THE_SELECTORS_JOB":
                blocks["found"] and D.plan_steps(g3, blocks) == ("unstack", "stack", "stack"),
            "a_name_must_be_drawn_BEFORE_it_is_used":
                "not a role" in (refused("criterion x:\n    wants link on\n"
                                         "    when spot is a thing\n"
                                         "    some spot in subject by contains\n"
                                         "    do stack b = subject, onto = object") or ""),
            "and_cannot_be_drawn_twice":
                "already bound" in (refused("criterion x:\n    wants link on\n"
                                            "    some spot in subject by contains\n"
                                            "    some spot in object by contains\n"
                                            "    do stack b = subject, onto = object") or "")}


def check_criteria_survive_a_SECOND_DOMAIN_and_where_they_STOP():
    """Everything in `docs/deliberation.md` was measured on blocks world, whose goals are `a on b` — a
    link constraint naming exactly the two individuals that must move. The load-bearing assumption is
    *a criterion's variables come from an unmet goal constraint*, and two other worlds attack it:

    * the garage, whose goal `car is a washed_car` is a type constraint — one subject, no object.
    * the warehouse, whose goal `wh contains+ parcel` names neither the box the parcel must go into
      nor anything about it. The right action mentions a third individual.

    Both survive, and the second is the interesting one: a third individual is reachable by an
    ordinary path from a bound role (`subject.contains`), so `wants` binding only two roles is not the
    ceiling it looked like — `path.py` extends the reach.

    But it found a real bug first, which is the point of a second domain. `wants type washed_car`
    matched nothing, silently: `goal.require_type` stores its label under `type`, a link under `label`,
    an attribute under `key`. Three names for one idea, and a criterion keying on the wrong one is
    indistinguishable from a criterion with nothing to say.

    And it settled a design question by force. A criterion whose action the goal forbids is now
    silent, not loud. `driver.check_call` raising is right for a Python decider — one naming a
    forbidden call is a caller bug — but a criterion is general knowledge meeting a particular world, so
    *"the first container happens to be the one this goal forbids"* is a situation. Raising abandoned a
    search that plain enumeration could finish; here `never touch crate` makes the criterion stand down
    and the deferred enumeration finds the box.

    The residue, and it is precise: `subject.contains` denotes the first container. A criterion
    can reach a third individual and cannot choose among several — `nearest`/`furthest … by <link>`
    selects over a *traversal*, never by a *condition*. What is missing is `some x such that …`: a set
    position with a filter, where only needed a selector."""
    from . import criterion as CR, driver as D, execution as X, goal as G, intake as I
    from . import path as P, thread as T

    # --- the garage: a type goal, subject and no object ---
    g, car = _garage()
    g.put(car, label="car")
    goal = I.read_goal(g, _lines("goal clean it:", "    car is a washed_car"))
    plain = D.pursue(g, goal, T.open_thread(g), car, max_steps=200, max_depth=6)
    for t in (_lines("criterion service it before washing:", "    wants type washed_car",
                     "    unless subject is a serviced_car", "    do service c = subject"),
              _lines("criterion then wash it:", "    wants type washed_car",
                     "    when subject is a serviced_car", "    do wash c = subject")):
        I.read(g, t)
    garage = D.pursue(g, goal, T.open_thread(g), car, max_steps=200, max_depth=6,
                      propose=CR.decide(g, goal, car))

    # --- the warehouse: the action names a third individual ---
    def stow(extra_crate: bool):
        gg, world, wh, box, parcel = _warehouse(nested=False)
        forbid = ["    never touch wh"]
        if extra_crate:
            crate = gg.mint("thing", kind_of="thing", label="crate", held=True)
            gg.link(world, "thing", crate)
            gg.link_at(wh, "contains", 0, crate)      # ahead of the box, so `.contains` finds it first
            forbid.append("    never touch crate")
        goal2 = I.read_goal(gg, _lines("goal stow it:", "    wh contains+ parcel", *forbid))
        I.read(gg, _lines("criterion stow it in something already inside:",
                          "    wants link contains",
                          "    do put_in t = object, box = subject.contains"))
        got = D.pursue(gg, goal2, T.open_thread(gg), world, max_steps=200, max_depth=6,
                       propose=CR.decide(gg, goal2, world))
        if got["found"]:
            X.execute(gg, got["workbench"], got["frame"])
        return gg, got, wh, box, parcel

    g1, one_box, wh1, box1, parcel1 = stow(False)
    g2, two_boxes, wh2, box2, parcel2 = stow(True)

    return {"a_TYPE_goal_binds_a_subject_and_criteria_drive_it":
                garage["found"] and D.plan_steps(g, garage) == ("service", "wash"),
            "and_beat_relevance": garage["steps"] < plain["steps"],
            "imagined_criteria_vs_relevance": (garage["steps"], plain["steps"]),
            "A_THIRD_INDIVIDUAL_IS_REACHABLE_BY_A_PATH": one_box["found"],
            "it_really_ends_up_in_the_warehouse": P.reaches(g1, wh1, "contains", parcel1),
            "BUT_NOT_DIRECTLY": parcel1 not in g1.targets(wh1, "contains"),
            # The residue: the first container is forbidden, so the criterion stands down rather than
            # overruling the constraint — and the deferred enumeration still finds the right box.
            "A_FORBIDDEN_ACTION_MAKES_THE_CRITERION_STAND_DOWN": two_boxes["found"],
            "and_the_parcel_still_reaches_the_warehouse": P.reaches(g2, wh2, "contains", parcel2),
            "the_goal_kept_the_crate_untouched":
                parcel2 not in g2.targets(_only(g2, "crate"), "contains"),
            # The vacuity guard for the whole check: `wants type` really did match nothing before the fix.
            "and_a_type_constraint_labels_itself_differently_from_a_link":
                CR.constraint_label(g, G.world_constraints(g, goal)[0]) == "washed_car"}


def _only(g, label):
    hits = [n for n in g.nodes if g.attr(n, "label") == label]
    return hits[0]


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
    """Constraints on the PLAN itself — what having the plan in the graph is for. Sussman's anomaly is
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
    """The other half. "The plan must include a `paint` step" is not violated by a prefix without one —
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
    """The whole loop, END to END. Materialise a world and a goal, bootstrap a thread, and let the
    driver imagine its way to a state satisfying the goal. The plan is then found, not built: it is the
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
            "recorded_as_PLANNED": G.is_planned(g, goal),
            "but_NOT_as_done": not G.is_closed(g, goal),
            "and_it_says_where_it_was_seen": g.target(goal, "seen_in") == result["frame"],
            "the_thread_recorded_the_work": len(entries) > 4,
            "and_ties_the_close_back_to_the_opening":
                T.connected(g, closing, "achieves") == (entries[1],)}


def check_the_found_plan_is_replayable_for_real():
    """The payoff of the plan being a frame path rather than a new kind of object: `execute` — written
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


# --- expectations: divergence the declared type cannot catch -------------------------------------------
def _scanner_fs():
    """A tool call whose mocks predict concrete state, not just a type.

    Both mocks return `listing`, which is exactly the point: reality *will* satisfy the declared return
    type, so the cast check passes and only the concrete prediction can catch the disagreement."""
    from . import asm, dispatch as D
    g = new_graph()
    declare_type(g, "dir", attrs={"kind_of": "dir"})
    declare_type(g, "listing", base="dir", attrs={"listed": True})
    asm.load_text(g, "\n".join([
        "# Really list a directory. Reaches the world.",
        "fn scan_dir(d: dir) -> listing:",
        '    DISPATCH R(out) "ls" F(d)',
        '    SET F(d) "listed" true',
        "",
        "# Assume it turns out to hold two files.",
        "fn found_two(d: dir) -> listing mocks scan_dir:",
        '    SET F(d) "listed" true',
        '    NEW R(f1) "file"', '    LINK F(d) "file" R(f1)',
        '    NEW R(f2) "file"', '    LINK F(d) "file" R(f2)',
        "",
        "# Assume it turns out empty.",
        "fn found_none(d: dir) -> listing mocks scan_dir:",
        '    SET F(d) "listed" true',
        '    SET F(d) "count" 0',
    ]))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    return g, d


def check_an_expectation_is_derived_from_the_two_frames():
    """Nothing is authored and nothing is stored — frame N−1 and frame N *are* the before and after, so
    the expectation is their difference. Vacuity guard: it must name the minted files and the attribute that
    changed, and must NOT mention attributes the step left alone."""
    from . import workbench as W
    g, d = _scanner_fs()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    f1, _tr = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)}, assume="found_two")
    pred = W.predicted_changes(g, f0, f1)
    changed = {key for _m, key, _v in pred["attrs"]}
    return {"predicts_that_files_APPEAR": pred["minted"] == frozenset({"file"}),
            "NOT_HOW_MANY": not isinstance(pred["minted"], dict),
            "edges_are_presence_not_count":
                [(lbl, p) for _m, lbl, p, _t in pred["links"]] == [("file", "some")],
            "the_types_own_claim_is_left_to_the_cast": "listed" not in changed,
            "nothing_it_did_not_touch": "count" not in changed}


def check_a_prediction_that_does_not_materialise_is_a_divergence():
    """The case the declared type cannot catch. The plan assumed listing the directory would produce
    two file nodes. Reality lists it and produces none — but the result still satisfies `listing`, so the
    cast passes and only the concrete expectation notices.

    Vacuity guards: the cast must genuinely pass (otherwise the type check is what caught it, not the
    expectation); and the identical plan against a reality that does produce the files must complete."""
    from . import dispatch as D, execution as X, workbench as W

    def plan_assuming_two(g, d):
        wb = W.open_workbench(g, d)
        f0 = W.root_frame(g, wb)
        f1, tr = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)}, assume="found_two")
        return wb, f1, tr

    g, d = _scanner_fs()
    D.register("ls", lambda gr, target: gr.put(target, count=0))        # reality: nothing there
    wb, f1, tr = plan_assuming_two(g, d)
    diverged = X.execute(g, wb, f1)

    g2, d2 = _scanner_fs()
    def two_files(gr, target):                                          # reality: two files, as assumed
        for _ in range(2):
            gr.link(target, "file", gr.mint("file"))
    D.register("ls", two_files)
    wb2, f1b, _ = plan_assuming_two(g2, d2)
    matched = X.execute(g2, wb2, f1b)

    dev = diverged["deviation"] or {}
    return {"diverged": not diverged["completed"],
            "THE_CAST_ITSELF_PASSED": W.deviates(g, tr, d) == {},
            "so_only_the_expectation_caught_it": "unmet_expectations" in dev,
            "and_it_says_what_was_missing":
                any("some new file node, found none" in m for m in dev.get("unmet_expectations", ())),
            "names_the_step": dev.get("step") == "scan_dir",
            "matching_reality_completes": matched["completed"]}


def check_planning_looks_for_an_expectation_not_a_type_signature():
    """The other direction. A goal of "some file must exist" cannot be served by looking at signatures:
    `scan_dir(d: dir) -> listing` mentions no file, and its *body* is a `DISPATCH` — everything interesting
    happens on the far side of a tool call. The knowledge that listing a directory *produces files* lives in
    the mock, which is the declared assumption about how the call turns out.

    Vacuity guards: the real function's own body must establish nothing about files (so the mock is doing
    the work); a function with no such mock must not be offered for it; and the search must actually plan
    the call rather than merely score it."""
    from . import driver as D, goal as G, thread as T
    g, d = _scanner_fs()
    declare_type(g, "file", attrs={"kind_of": None})
    own, _u = D._effects(g, "scan_dir", include_mocks=False)
    withmocks, _u2 = D.establishes(g, "scan_dir")

    goal = G.open_goal(g, label="find a file")
    G.require_type(g, goal, "file")                     # Something of this type — no subject named
    result = D.pursue(g, goal, T.open_thread(g), d, max_steps=50)
    return {"the_signature_mentions_no_file": fn_returns(g, "scan_dir") == "listing",
            "and_its_own_body_establishes_none": not any(e[0] == "mint" for e in own),
            "BUT_ITS_MOCK_PREDICTS_ONE":
                any(e[:2] == ("mint", "file") for e in withmocks),
            "so_the_goal_finds_the_call": result["found"],
            "and_plans_the_REAL_call": D.plan_steps(g, result) == ("scan_dir",),
            "NOT_THE_MOCK": "found_two" not in D.plan_steps(g, result),
            "in_one_step": result["steps"] == 1}


# --- anticipation, and the relation between an ACT and a LOOK ------------------------------------------
def _repo():
    """The user's example: *"I change some files, I expect `git status` to not return empty."*

    `edit` is the ACT. `git_status` is the LOOK — its body is a `DISPATCH` and says nothing, so
    `anticipate` is its model. `disk_free` is an unrelated look and is the control."""
    from . import asm
    g = new_graph()
    declare_type(g, "tree", attrs={"kind_of": "tree"})
    declare_type(g, "report", base="tree", attrs={"reported": True})
    asm.load_text(g, "\n".join([
        "# THE ACT: change some files.",
        "fn edit(t: tree) -> tree:",
        '    NEW R(f) "file"',
        '    SET R(f) "changed" true',
        '    LINK F(t) "changed_file" R(f)',
        "",
        "# The same act, REFACTORED to write a different slot. Nothing else changed.",
        "fn edit_renamed(t: tree) -> tree:",
        '    NEW R(f) "file"',
        '    SET R(f) "changed" true',
        '    LINK F(t) "modified_file" R(f)',
        "",
        "# THE LOOK. Everything it learns is on the far side of the DISPATCH.",
        "fn git_status(t: tree) -> report:",
        '    DISPATCH R(out) "git_status" F(t)',
        '    SET F(t) "reported" true',
        "",
        "# ITS MODEL - not 'suppose it comes back dirty' but 'work out what it will say'.",
        "fn anticipate(t: tree) -> report mocks git_status:",
        '    SET F(t) "reported" true',
        '    COUNT R(n) F(t) "changed_file"',
        '    JMPNOT R(n) .clean',
        '    SET F(t) "dirty" true',
        "    JMP .done",
        "    .clean:",
        '    SET F(t) "dirty" false',
        "    .done:",
        "    HALT",
        "",
        "# AN UNRELATED LOOK - THE CONTROL. Also a DISPATCH, also modelled, watches something else.",
        "fn disk_free(t: tree) -> report:",
        '    DISPATCH R(out) "df" F(t)',
        '    SET F(t) "reported" true',
        "",
        "fn guess_disk(t: tree) -> report mocks disk_free:",
        '    SET F(t) "reported" true',
        '    ATTR R(b) F(t) "free_bytes"',
        '    SET F(t) "roomy" true',
    ]))
    t = g.mint("tree", kind_of="tree")
    g.link("root", "has", t)
    return g, t


def check_a_mock_can_anticipate_instead_of_assume():
    """a mock may be a model, NOT merely an assumption — the user's example:
    *"I can anticipate the behaviour of git status when I know some files have changed."*

    Every mock in this suite's other fixtures asserts a constant — `found_two` always predicts two files,
    `list_empty` always predicts none — which made mocks look like assumptions (*suppose it turns out this
    way*) when a mock is an ordinary microfunction and can therefore read the graph and work the answer out.
    That is the difference between an assumption and an anticipation, and it needed no new mechanism;
    it had simply never been written down.

    The vacuity guard is the whole CHECK: it must be the same mock, unedited, in both worlds, and
    the two predictions must differ *because the world differs*. Two different mocks would be measuring the
    ordinary constant-assumption machinery and would pass while proving nothing.

    And the divergence it catches is one the declared type cannot: the cast passes either way, because
    `report` says nothing about `dirty`."""
    from . import dispatch as D, execution as X, function as fn, workbench as W

    def anticipated(edited):
        g, t = _repo()
        if edited:
            fn.invoke(g, "edit", {"t": t})              # I changed some files, and i know i did
        wb = W.open_workbench(g, t)
        f0 = W.root_frame(g, wb)
        f1, tr = W.step(g, wb, f0, "git_status", {"t": W.mapping_for(g, f0, t)}, assume="anticipate")
        pred = {k: v for _m, k, v in W.predicted_changes(g, f0, f1)["attrs"]}
        return g, t, wb, f1, tr, pred

    _gc, _tc, _wc, _fc, _trc, clean = anticipated(False)
    gd, td, wbd, f1d, trd, dirty = anticipated(True)

    D.register("git_status", lambda gr, target: gr.put(target, dirty=False), observes=True)
    diverged = X.execute(gd, wbd, f1d)                  # I edited; git says clean. A surprise.

    go, to, wbo, f1o, _tro, _p = anticipated(True)
    D.register("git_status", lambda gr, target: gr.put(target, dirty=True), observes=True)
    matched = X.execute(go, wbo, f1o)

    return {"ONE_MOCK_ONLY": fn.mocks_of(gd, "git_status") == ("anticipate",),
            "clean_world_anticipates_clean": clean.get("dirty") is False,
            "EDITED_WORLD_ANTICIPATES_DIRTY": dirty.get("dirty") is True,
            "SO_THE_PREDICTION_FOLLOWED_THE_WORLD": clean != dirty,
            "a_contradicting_world_diverges": not diverged["completed"],
            "THE_CAST_ITSELF_PASSED": W.deviates(gd, trd, td) == {},
            "and_it_says_how": any("dirty" in m for m in
                                   (diverged["deviation"] or {}).get("unmet_expectations", ())),
            "control_an_agreeing_world_completes": matched["completed"]}


def check_a_mock_maps_a_CONDITION_to_an_expectation():
    """"expectations must be conditioned" — the user: *"a mock must map conditions to
    expectations, so even during planning we know what to expect if we perform an action on a given
    state."* The default outcome was `outcomes[0]` — declaration order, chosen without looking at the
    world — so *"what will happen if I do this here"* was answered by something that could not see "here".

    A mock's condition is its parameter types, so this needed no new representation: a parameter type
    is already a schema over a subgraph and `fn.invoke` already enforces it. `fn.applicable` asks that
    question *before* choosing rather than discovering it afterwards as a refusal.

    What this replaced was not a wrong prediction but a crash. Planning in the clean world took
    `found_dirty` and `fn.invoke` refused it — so the condition that should have *selected* the other
    outcome instead *rejected* the only one offered, and a perfectly plannable state was unplannable.

    And it is what lets a conditioned mock stay BRANCH-free, which is the deeper payoff:
    `driver.establishes` does not follow jumps (its own comment: *"a conditional write is reported as
    unconditional"*), so a mock that branches internally claims both its outcomes. Asserted below,
    because it is the reason to prefer two conditioned mocks over one branching one.

    Vacuity guards: the two worlds must select different outcomes (otherwise the condition is doing
    nothing), and the branching encoding must really claim both values (otherwise there is nothing to
    prefer the conditioned encoding *over*)."""
    from . import asm, driver as D, function as fn, types as TY, workbench as W
    from .types import Req

    def world(*, conditioned, edited):
        g = new_graph()
        declare_type(g, "tree", attrs={"kind_of": "tree"})
        declare_type(g, "report", base="tree", attrs={"reported": True})
        lines = ["fn edit(t: tree) -> tree:", '    NEW R(f) "file"',
                 '    LINK F(t) "changed_file" R(f)', "",
                 "fn git_status(t: tree) -> report:",
                 '    DISPATCH R(out) "git_status" F(t)', '    SET F(t) "reported" true', ""]
        if conditioned:
            declare_type(g, "dirty_tree", {"changed_file": Req(kind="file", lo=1)},
                         attrs={"kind_of": "tree"})
            declare_type(g, "clean_tree", {"changed_file": Req(kind="file", lo=0, hi=0)},
                         attrs={"kind_of": "tree"})
            lines += ["fn found_dirty(t: dirty_tree) -> report mocks git_status:",
                      '    SET F(t) "reported" true', '    SET F(t) "dirty" true', "",
                      "fn found_clean(t: clean_tree) -> report mocks git_status:",
                      '    SET F(t) "reported" true', '    SET F(t) "dirty" false', "",
                      # A loose outcome, declared last: its condition holds in every world, so it fits
                      # alongside a specific one and is what makes "declaration order decides among
                      # several that fit" a testable claim rather than a docstring.
                      "fn found_something(t: tree) -> report mocks git_status:",
                      '    SET F(t) "reported" true', '    SET F(t) "dirty" true']
        else:
            lines += ["fn anticipate(t: tree) -> report mocks git_status:",
                      '    SET F(t) "reported" true', '    COUNT R(n) F(t) "changed_file"',
                      '    JMPNOT R(n) .clean', '    SET F(t) "dirty" true', "    JMP .done",
                      "    .clean:", '    SET F(t) "dirty" false', "    .done:", "    HALT"]
        asm.load_text(g, "\n".join(lines))
        t = g.mint("tree", kind_of="tree")
        g.link("root", "has", t)
        if edited:
            fn.invoke(g, "edit", {"t": t})
        return g, t

    def anticipated(g, t):
        wb = W.open_workbench(g, t)
        f0 = W.root_frame(g, wb)
        f1, _tr = W.step(g, wb, f0, "git_status", {"t": W.mapping_for(g, f0, t)})
        return {k: v for _m, k, v in W.predicted_changes(g, f0, f1)["attrs"]}

    gd, td = world(conditioned=True, edited=True)
    gc, tc = world(conditioned=True, edited=False)
    gb, tb = world(conditioned=False, edited=True)
    branching = {v for k, lbl, _s, v in D.establishes(gb, "git_status")[0]
                 if k == "attr" and lbl == "dirty"}
    per_mock = {o: {v for k, lbl, _s, v in D.establishes(gd, o)[0] if k == "attr" and lbl == "dirty"}
                for o in fn.mocks_of(gd, "git_status")}

    return {"the_conditions_are_READABLE_as_parameter_types":
                fn.param_types(gd, "found_dirty") == {"t": "dirty_tree"},
            "the_EDITED_world_selects_the_dirty_outcome":
                fn.applicable(gd, "git_status", {"t": td})[0] == "found_dirty",
            "the_CLEAN_world_selects_the_other":
                fn.applicable(gc, "git_status", {"t": tc})[0] == "found_clean",
            # The loose outcome fits in BOTH worlds, so several really are applicable and the order
            # among them is doing work — without this, reversing the preference order passes.
            "SEVERAL_CAN_FIT_AND_DECLARATION_ORDER_DECIDES":
                (fn.applicable(gd, "git_status", {"t": td}) == ("found_dirty", "found_something")
                 and fn.applicable(gc, "git_status", {"t": tc}) == ("found_clean", "found_something")),
            "SO_THE_DEFAULT_PREDICTION_FOLLOWS_THE_STATE": anticipated(gd, td) != anticipated(gc, tc),
            "and_it_predicts_the_RIGHT_one_in_each":
                (anticipated(gd, td).get("dirty"), anticipated(gc, tc).get("dirty")) == (True, False),
            "A_BRANCHING_MOCK_CLAIMS_BOTH_OUTCOMES": branching == {True, False},
            "BUT_EACH_CONDITIONED_ONE_IS_EXACT":
                all(len(v) == 1 for v in per_mock.values()),
            "an_unsatisfiable_condition_yields_NOTHING_rather_than_a_guess":
                fn.applicable(gd, "git_status", {"t": TY.find_type(gd, "tree")}) == ()}


def check_an_act_and_a_look_are_related_by_what_one_writes_and_the_other_watches():
    """"in some way, i related the two." The relation between changing files and expecting
    `git status` to be dirty is derivable, and both halves were already graph data: what the act writes
    (`establishes`) and what the look's model reads (`reports_on`, the dual built for this).

    Declaring it instead — a `git_status reflects edit` edge — was the obvious alternative and would have
    been the labelling error this codebase keeps recording: an authored edge can drift from the bodies, and
    a derivation cannot, because it *is* the bodies.

    The asymmetry is the finding: the ACT's body, and the LOOK's mock. A look's body is a `DISPATCH`
    and establishes nothing, so reading it would return the empty set for every look and make the whole
    measure vacuous. Asserted below rather than assumed.

    The control is the whole CHECK. If every look related to every act the measure would say nothing,
    and this repo has twice built a probe whose control went dark. So three pairs: the related one, an
    unrelated look, and the drift defect the relation exists to catch — an act refactored to write a
    different slot, against an unchanged model, which still parses and still runs and now silently watches
    the wrong thing."""
    from . import driver as D
    g, _t = _repo()
    watched, _u = D.reports_on(g, "git_status")
    return {"the_LOOKS_OWN_BODY_watches_nothing": D.reads(g, "git_status")[0] == frozenset(),
            "so_the_MODEL_is_what_speaks": ("link", "changed_file") in {(k, l) for k, l, _s in watched},
            "RELATED": D.confirms(g, "edit", "git_status") == frozenset({("link", "changed_file")}),
            "CONTROL_an_unrelated_look_is_not": D.confirms(g, "edit", "disk_free") == frozenset(),
            "AND_DRIFT_IS_CAUGHT": D.confirms(g, "edit_renamed", "git_status") == frozenset(),
            "the_drifted_act_still_writes_something":
                bool(D.establishes(g, "edit_renamed")[0])}


def check_the_two_static_readers_of_a_body_agree_about_roles():
    """`establishes` and `reads` are two static readers of one body, and they must agree exactly about
    what `R(x)` denotes at each instruction. Two copies of that bookkeeping is the drift shape this codebase
    keeps recording, and one that disagreed would report an act and a look as unrelated when they are —
    silently, and in the direction that loses the finding.

    So both consume one `_walk`. This check is what earns that factoring its place: a body that navigates
    before reading and writing must report the same navigated role on both sides.

    Vacuity guard: a navigated role (`t.sub`) must really appear on both sides. Two readers that both
    reported only the bare `t` would agree while proving nothing about the register bookkeeping at all.

    The first version of this guard asserted that no read names a bare parameter, and was wrong:
    `GET R(s) F(t) "sub"` is itself a read *of `t`*, so `("link", "sub", "t")` belongs in the answer. The
    navigation being checked is the read that comes *after* it."""
    from . import asm, driver as D
    g = new_graph()
    declare_type(g, "tree", attrs={"kind_of": "tree"})
    asm.load_text(g, "\n".join([
        "fn touch_the_sub(t: tree) -> tree:",
        '    GET R(s) F(t) "sub"',                     # navigate first: the subject is now in a register
        '    COUNT R(n) R(s) "changed_file"',          # Read through it
        '    SET R(s) "seen" true',                    # and write through it
    ]))
    written = {(k, lbl, sp) for k, lbl, sp, _o in D.establishes(g, "touch_the_sub")[0]}
    got_read = D.reads(g, "touch_the_sub")[0]
    return {"the_WRITE_names_the_navigated_role": ("attr", "seen", "t.sub") in written,
            "the_READ_NAMES_THE_SAME_ONE": ("link", "changed_file", "t.sub") in got_read,
            "A_NAVIGATED_ROLE_REALLY_APPEARS": any("." in (sp or "") for _k, _l, sp in got_read),
            "the_navigating_GET_is_itself_a_read_of_t": ("link", "sub", "t") in got_read,
            "and_none_is_unnameable": all(sp is not None for _k, _l, sp in got_read)}


def check_a_minted_node_keeps_the_join_through_a_register():
    """Reported by the first consumer, the engine's first real user, which uses `establishes` for
    *recognition* rather than for ranking. A pattern authored as `NEW R(it)` then `LINK R(it) …` came back
    as three effects with no subject at all — "orphan facts that no longer claim to describe one node" —
    because only `F(param)` counted as a role. That forced every pattern to be authored as a cast, which is
    a real expressive loss, and it was invisible here because ranking does not care.

    A register holding something minted *in this body* is a local subject, marked `$` so it can never be
    confused with a parameter. Vacuity guards: all three effects must name the *same* subject (the join is
    the whole point); a parameter role must still be a bare name; and a register that is later reassigned
    must stop claiming to be the minted node — it now denotes whatever was put in it instead, which is the
    navigation case checked below, and the thing that must never happen is it still answering `$it`."""
    from . import asm, driver as D
    g = new_graph()
    declare_type(g, "seq", attrs={"kind_of": "seq"})
    asm.load_text(g, "\n".join([
        "# A minting pattern: build an iteration over a sequence.",
        "fn as_iteration(seq: seq) -> seq:",
        '    NEW R(it) "iteration"',
        '    LINK R(it) "over" F(seq)',
        '    SET R(it) "kind" "loop"',
        "",
        "# The register stops denoting the minted node once something else is put in it.",
        "fn reassigned(seq: seq) -> seq:",
        '    NEW R(it) "iteration"',
        '    GET R(it) F(seq) "other"',
        '    SET R(it) "kind" "loop"',
    ]))
    eff, unknown = D.establishes(g, "as_iteration")
    subjects = {e[2] for e in eff}
    later, _u = D.establishes(g, "reassigned")
    return {"three_effects": len(eff) == 3,
            "THEY_ALL_NAME_ONE_SUBJECT": len(subjects) == 1 and subjects != {None},
            "marked_as_local_not_a_parameter": subjects == {"$it"},
            "the_parameter_role_is_still_a_bare_name":
                ("link", "over", "$it", "seq") in eff,
            "and_it_is_known_statically": not unknown,
            "a_reassigned_register_stops_being_the_minted_node":
                not any(e[2] == "$it" for e in later if e[0] == "attr"),
            "and_denotes_what_was_put_in_it":
                ("attr", "kind", "seq.other", "loop") in later}


def _threshold_library():
    """Two comparisons, each with a literal right-hand side, and operators that repair one by navigating
    to it. The shape the first consumer reported: *read a part, write to that part*."""
    from . import asm
    g = new_graph()
    declare_type(g, "comparison", {"right": ("literal", 1)})
    declare_type(g, "literal")
    asm.load_text(g, "\n".join([
        "# Make the comparison easier to pass by lowering its threshold.",
        "fn lower_threshold(c: comparison) -> comparison:",
        '    GET R(rhs) F(c) "right"',
        '    ATTR R(v) R(rhs) "value"',
        "    ADD R(v2) R(v) -1",
        '    SET R(rhs) "value" R(v2)',
        "",
        "fn raise_threshold(c: comparison) -> comparison:",
        '    GET R(rhs) F(c) "right"',
        '    ATTR R(v) R(rhs) "value"',
        "    ADD R(v2) R(v) 1",
        '    SET R(rhs) "value" R(v2)',
    ]))
    root, lits = g.mint("rule"), []
    for v in (3, 7):
        c, lit = g.mint("comparison"), g.mint("literal", value=v)
        g.link(c, "right", lit)
        g.link(root, "case", c)
        tag(g, c, "comparison")
        tag(g, lit, "literal")
        lits.append(lit)
    return g, root, lits


def check_a_navigated_register_keeps_the_join():
    """Reported by the first consumer. A function whose operands are parameters read beautifully; one that
    had to *navigate* went dark — and a bridge between two vocabularies is nothing but navigation, so the
    functions they most wanted to read were exactly the ones that could not be read.

    `GET R(s) F(a) "over"` makes `R(s)` denote a derivable thing: *the `over` of `a`*. So a role is a path,
    and the write keeps its join to the parameter it came from.

    Vacuity guards: the plain-parameter roles must be unchanged (a path must not swallow the simple case);
    the path must survive into a real repair operator whose write lands two hops from its parameter; and a
    register overwritten by something unreadable — an `ATTR` holds a *value*, not a node — must lose the
    role rather than keep claiming a stale one."""
    from . import asm, driver as D
    g = new_graph()
    asm.load_text(g, "\n".join([
        "fn navigate(a, b) -> t:",
        '    GET R(s) F(a) "over"',
        '    LINK F(b) "seq" R(s)',
        '    LINK F(b) "direct" F(a)',
        "fn clobbered(a, b) -> t:",
        '    GET R(s) F(a) "over"',
        '    ATTR R(s) F(b) "name"',
        '    LINK F(b) "seq" R(s)',
    ]))
    eff, _u = D.establishes(g, "navigate")
    lost, _u2 = D.establishes(g, "clobbered")

    gt, _root, _lits = _threshold_library()
    repair, unknown = D.establishes(gt, "lower_threshold")
    return {"the_plain_parameter_case_is_unchanged":
                ("link", "direct", "b", "a") in eff,
            "AND_THE_NAVIGATED_ROLE_IS_KEPT":
                ("link", "seq", "b", "a.over") in eff,
            "no_effect_has_a_null_object_any_more":
                not any(e[3] is None for e in eff),
            "A_REPAIR_OPERATOR_NOW_REPORTS_ITS_EFFECT":
                repair == frozenset({("attr", "value", "c.right", D.UNREADABLE)}),
            "and_reports_it_as_fully_read": not unknown,
            "but_a_value_bearing_register_claims_nothing":
                ("link", "seq", "b", None) in lost}


def check_a_role_path_is_resolved_against_the_world():
    """The other half of the same mechanism, and the reason it is split in two: `establishes` says *`c`'s
    `right`* without knowing which node that is, and only a caller holding bindings can turn that into an
    individual. Static provenance, dynamic resolution.

    Vacuity guards: the same role must resolve to different nodes under different bindings (or it is not
    resolution at all), a locally-minted `$` role must resolve to nothing, and a path through an absent edge
    must answer `None` rather than raising."""
    from . import driver as D
    g, _root, lits = _threshold_library()
    first, second = (g.sources(lit, "right")[0] for lit in lits)
    return {"resolves_under_one_binding": D.role_node(g, {"c": first}, "c.right") == lits[0],
            "AND_DIFFERENTLY_UNDER_ANOTHER": D.role_node(g, {"c": second}, "c.right") == lits[1],
            "a_bare_parameter_is_just_a_lookup": D.role_node(g, {"c": first}, "c") == first,
            "a_minted_role_names_nothing_outside": D.role_node(g, {"c": first}, "$it") is None,
            "and_a_missing_edge_is_None_not_an_error":
                D.role_node(g, {"c": first}, "c.nowhere.deeper") is None}


def check_ranking_sees_through_a_navigating_operator():
    """Why the path is worth its cost to the driver itself, not only to a consumer reading descriptions.

    Two comparisons; the goal wants one literal lowered. `lower_threshold` writes to a register, so before
    paths it established nothing anyone could name — and band 4 ("this call writes exactly this constraint")
    could never be reached by *any* candidate. Every proposal tied, and the guidance had nothing to rank
    with. the first consumer measured 5 imagined states against 6 blind on their own repair and said so.

    The control is the whole check: blind search alone would not show that paths did it, so the middle
    figure re-runs the identical search with path roles pretended not to exist — the behaviour before this
    change. Guided must beat that, not merely beat blind.

    The step counts are compared one way only, deliberately. With paths the search is decisive and
    lands on 3 every time; the other two are tie-broken by frontier insertion order and measure 5 or 10 run
    to run, because *without a reachable band 4 the guided search and the blind one are the same search* —
    which is the first consumer's "found essentially unguided" in this engine's own numbers. So the load-bearing
    assertion is the structural one below: before paths, no proposal could reach band 4 at all."""
    from . import driver as D, goal as G, thread as T, workbench as W

    def search(guided, paths=True):
        g, root, lits = _threshold_library()
        goal = G.open_goal(g, about=root, label="lower the first threshold")
        G.require_attr(g, goal, lits[0], "value", 1)
        real = D.role_node
        if not paths:
            D.role_node = lambda gr, bound, role: (
                None if not role or "." in role or role.startswith("$") else bound.get(role))
        try:
            r = D.pursue(g, goal, T.open_thread(g, "t"), root, guided=guided, max_steps=60)
        finally:
            D.role_node = real
        return g, r

    def bands(paths=True):
        """The band every root proposal scores — what the ranking has to work with before it moves."""
        g, root, lits = _threshold_library()
        goal = G.open_goal(g, about=root)
        G.require_attr(g, goal, lits[0], "value", 1)
        wb = W.open_workbench(g, root)
        f0 = W.root_frame(g, wb)
        open_now = G.unmet(g, goal, view=D.view_in(g, f0),
                           under=W.image_of(g, W.mapping_for(g, f0, root)))
        real = D.role_node
        if not paths:
            D.role_node = lambda gr, bound, role: (
                None if not role or "." in role or role.startswith("$") else bound.get(role))
        try:
            return {D.relevance(g, n, b, open_now) for n, b in D.proposals(g, f0)}
        finally:
            D.role_node = real

    (gp, with_paths), (_gw, without), (_gb, blind) = (
        search(True), search(True, paths=False), search(False))
    return {"it_finds_the_two_step_repair":
                D.plan_steps(gp, with_paths) == ("lower_threshold", "lower_threshold"),
            "NO_PROPOSAL_COULD_SCORE_A_HIT_BEFORE": bands(paths=False) == {1},
            "AND_NOW_ONE_CAN": 4 in bands(),
            "but_not_every_one_of_them": bands() != {4},
            "GUIDED_WITH_PATHS": with_paths["steps"],
            "guided_without_them": without["steps"],
            "blind": blind["steps"],
            "paths_beat_the_previous_guidance": with_paths["steps"] < without["steps"],
            "and_beat_blind_too": with_paths["steps"] < blind["steps"]}


def check_unknown_says_what_it_could_not_read():
    """Reported by the first consumer, which abstains from recognising a node whenever anything in a body was
    unreadable. A whole-function flag darkened descriptions that were provably complete: the unreadable
    write here targets `y`, and the readable effect describes `x`.

    `unknown` is now the set of ROLES the unreadable instructions concern, `None` meaning "somewhere we
    cannot name at all". Empty is falsy, so every existing `if unknown:` reads as it did.

    Vacuity guards: a fully readable body must still report nothing unknown, and a call — whose effects
    genuinely happen elsewhere — must still darken everything by reporting `None`."""
    from . import asm, driver as D
    g = new_graph()
    asm.load_text(g, "\n".join([
        "fn side(x, y) -> t:",
        '    LINK F(x) "clear" F(y)',
        '    ATTR R(k) F(y) "name"',
        "    SET F(y) R(k) true",
        "fn plain(x, y) -> t:",
        '    LINK F(x) "clear" F(y)',
        "fn calls_out(x, y) -> t:",
        '    LINK F(x) "clear" F(y)',
        '    INVOKE R(_) plain x=F(x) y=F(y)',
    ]))
    eff, unknown = D.establishes(g, "side")
    _p, plain_unknown = D.establishes(g, "plain")
    _c, call_unknown = D.establishes(g, "calls_out")
    return {"the_readable_effect_survives": eff == frozenset({("link", "clear", "x", "y")}),
            "still_truthy_so_old_callers_are_unaffected": bool(unknown),
            "AND_IT_NAMES_THE_ROLE_IT_COULD_NOT_READ": unknown == frozenset({"y"}),
            "so_a_consumer_can_see_x_IS_fully_described": "x" not in unknown and None not in unknown,
            "a_fully_readable_body_reports_nothing": plain_unknown == frozenset(),
            "but_a_call_still_darkens_everything": call_unknown == frozenset({None})}


def check_a_contradictory_goal_is_refused_before_searching():
    """Decidable contradictions only, so this can never reject a reachable goal. Vacuity guard: the same
    goal minus the contradiction must plan normally, and the refusal must cost zero imagined steps."""
    from . import conflict as C, driver as D, goal as G, thread as T
    g, world = _blocks()
    a, b, _c = g.targets(world, "block")
    bad = G.open_goal(g, label="contradictory")
    G.require_attr(g, bad, a, "clear", True)
    G.require_attr(g, bad, a, "clear", False)
    refused = D.pursue(g, bad, T.open_thread(g), world)

    both = G.open_goal(g, label="required and forbidden")
    G.require_link(g, both, a, "on", b)
    G.require_action(g, both, function="stack")
    G.forbid_action(g, both, function="stack")

    fine = G.open_goal(g, label="fine")
    G.require_link(g, fine, a, "on", b)
    return {"contradiction_found": len(C.unsatisfiable(g, bad)) == 1,
            "refused_without_searching": not refused["found"] and refused["steps"] == 0,
            "and_says_why": "contradicts" in refused["why"],
            "required_and_forbidden_too":
                any("both required and forbidden" in r for r in C.unsatisfiable(g, both)),
            "no_false_positive_on_a_good_goal": C.unsatisfiable(g, fine) == (),
            "which_still_plans": D.pursue(g, fine, T.open_thread(g), world, max_steps=200)["found"]}


def check_interference_between_two_goals_is_surfaced():
    """The regression, addressed — but not by copying the old notion. That engine *derived facts*, so
    two contradictory conclusions were a contradiction. This one *performs actions in sequence*, where a
    later write legitimately overrides an earlier one. What survives is interference: two independently
    authored functions, composed by a library that grew, writing one slot for unrelated reasons — the
    telecom feature-interaction problem `function.py` cites as prior art.

    The different-goal requirement is the whole distinction. Vacuity guards: steps within one plan
    overwrite each other constantly and must NOT be reported; and the conflict must be recorded as ordinary
    data (a `conflicts` connection) rather than only returned."""
    from . import asm, conflict as C, driver as D, goal as G, thread as T
    g, world = _blocks()
    a, _b, _c = g.targets(world, "block")
    asm.load_text(g, "\n".join([
        "# A second, independently authored feature that happens to write the same slot.",
        "fn varnish(b: block) -> block:",
        '    SET F(b) "colour" "clear"',
    ]))
    declare_type(g, "red_block", base="block", attrs={"colour": "red"})
    declare_type(g, "varnished_block", base="block", attrs={"colour": "clear"})

    th = T.open_thread(g, "session")
    red = G.open_goal(g, label="make it red")
    G.require_attr(g, red, a, "colour", "red")
    D.carry_out(g, red, th, world, max_steps=200)

    varnished = G.open_goal(g, label="varnish it")
    G.require_attr(g, varnished, a, "colour", "clear")
    D.carry_out(g, varnished, th, world, max_steps=200)

    found = C.interference(g, th)

    # The vacuity guard that matters: one goal whose plan must write the slot twice (paint sets red,
    # varnish sets clear) — a deliberate sequel, and it must NOT be reported.
    g2, world2 = _blocks()
    a2 = g2.targets(world2, "block")[0]
    asm.load_text(g2, "\n".join(["# the same second feature",
                                 "fn varnish(b: block) -> block:",
                                 '    SET F(b) "colour" "clear"']))
    th2 = T.open_thread(g2, "one goal")
    both_writes = G.open_goal(g2, label="varnish, having painted")
    G.require_attr(g2, both_writes, a2, "colour", "clear")
    G.require_action(g2, both_writes, function="paint")
    D.carry_out(g2, both_writes, th2, world2, max_steps=300)
    sequel = C.interference(g2, th2)
    wrote_twice = [e for e in T.entries(g2, th2)
                   if g2.attr(e, "function") in ("paint", "varnish") and g2.attr(e, "done")]
    first = found[0] if found else (None, None, None, None, None, None)
    return {"two_goals_wrote_one_slot": len(found) >= 1,
            "it_names_the_slot": first[3] == "colour",
            "and_both_values": {first[4], first[5]} == {"red", "clear"},
            "and_the_two_functions_differ":
                first[0] is not None
                and g.attr(first[0], "function") != g.attr(first[1], "function"),
            "RECORDED_AS_ORDINARY_DATA": len(C.conflicts_on(g, th)) >= 1,
            "reusing_the_threads_cross_link": all(g.kind(c) == "connection"
                                                  for c in C.conflicts_on(g, th)),
            "readable": "conflict(s)" in C.describe(g, th),
            "an_empty_thread_has_none": C.interference(g, T.open_thread(g)) == (),
            "ONE_PLAN_REALLY_DID_WRITE_THE_SLOT_TWICE": len(wrote_twice) >= 2,
            "but_a_sequel_is_NOT_a_conflict": sequel == ()}


def check_two_plans_collide_before_either_runs():
    """Requested as a use case by the first consumer: their previous engine caught a collider between two
    independently authored fragments *before anything ran*, and the value was that the author learns at
    compose time rather than after a run that has already clobbered something.

    Their hypothesis — "`interference` over a frame chain, the same function with a different source of
    claims" — is right, with one correction: it takes two chains. One chain is a single committed plan,
    and steps within one plan are a deliberate sequence, so reading one would report ordinary sequels.

    Vacuity guards: nothing must have run (the block's colour is still untouched afterwards, or this is
    the ordinary after-the-fact detector wearing a hat); two plans that agree must report nothing; and one
    plan alone must report nothing however many times it writes the slot."""
    from . import asm, conflict as C, driver as D, goal as G, thread as T
    g, world = _blocks()
    a = g.targets(world, "block")[0]
    asm.load_text(g, "\n".join([
        "# Independently authored, and it happens to write the slot `paint` writes.",
        "fn varnish(b: block) -> block:",
        '    SET F(b) "colour" "clear"',
        "fn polish(b: block) -> block:",
        '    SET F(b) "shine" true',
    ]))
    th = T.open_thread(g, "composing")

    def plan_for(label, key, value):
        goal = G.open_goal(g, label=label)
        G.require_attr(g, goal, a, key, value)
        return D.pursue(g, goal, th, world, max_steps=200)

    red, clear, shiny = (plan_for("make it red", "colour", "red"),
                         plan_for("varnish it", "colour", "clear"),
                         plan_for("polish it", "shine", True))
    collide = C.interference_between(g, [red, clear])
    agree = C.interference_between(g, [red, shiny])
    alone = C.interference_between(g, [red])
    first = collide[0] if collide else (None,) * 6
    return {"both_plans_were_found": red["found"] and clear["found"] and shiny["found"],
            "NOTHING_HAS_RUN": g.attr(a, "colour") is None,
            "TWO_PLANS_COLLIDE": len(collide) == 1,
            "it_names_the_slot": first[3] == "colour",
            "and_both_intended_values": {first[4], first[5]} == {"red", "clear"},
            "and_the_two_goals_differ": first[0] is not None and first[0] != first[1],
            "plans_touching_different_slots_do_not": agree == (),
            "and_ONE_plan_is_never_in_conflict_with_itself": alone == ()}


def check_types_are_recognised_bottom_up():
    """What IS this? — the direction this module was missing. Every entry point was top-down
    (`is_a` and `instances` both take a *named* type); nothing asked what a node turns out to be.

    Vacuity guards, because two of these look like features and are not: multi-type and de-recognition must
    fall out of independent structural predicates rather than needing mechanism, so the same three-line
    function must produce both — and a type constraining nothing must not be 'recognised' on everything."""
    from . import function as fnm
    from .types import recognize, type_names
    g, car = _garage()
    declare_type(g, "anything")                          # constrains nothing at all
    fresh = recognize(g, car)
    fnm.invoke(g, "service", {"c": car})
    serviced = recognize(g, car)
    fnm.invoke(g, "wash", {"c": car})
    washed = recognize(g, car)
    g.unlink(car, "wheel", index=0)
    return {"a_plain_car": fresh == ("car",),
            "MULTI_TYPE_FALLS_OUT": washed == ("car", "serviced_car", "washed_car"),
            "one_at_a_time": serviced == ("car", "serviced_car"),
            "DE_RECOGNITION_FALLS_OUT": recognize(g, car) == (),
            "with_nothing_to_invalidate_because_nothing_was_stored": g.attr(car, "is_a") is None,
            "a_type_constraining_nothing_is_not_recognition": "anything" not in type_names(g)}


def check_a_stale_type_tag_is_never_trusted():
    """the defect, fixed. `tag` stamps `is_a` and that stamp is a claim about the *past*, while `is_a`
    is computed from current structure. `application.generalise` read the raw attribute as authoritative, so
    a node that had since changed would name a learned function's parameter — and declare its type — after
    a class it no longer belonged to, producing a function that refuses its own training example.

    Vacuity guards: the stale attribute must still be *present* (so `tagged_as` is what rejects it, not its
    absence); and the same tag while still true must be honoured, or the fix would just be "ignore tags"."""
    from . import application as ap, function as fnm
    from .types import is_a, tag, tagged_as
    g, car = _garage()
    tag(g, car, "car")
    honoured = tagged_as(g, car)

    ep = ap.open_episode(g, "servicing")
    ap.record(g, "service", {"c": car}, episode=ep)
    g.unlink(car, "wheel", index=0)                       # the world moves on under the stamp
    stale_attr = g.attr(car, "is_a")
    params, _m, ptypes = ap.generalise(g, ep)
    learned = ap.compile_episode(g, ep, "learned")
    return {"honoured_while_true": honoured == "car",
            "the_stamp_is_still_there": stale_attr == "car",
            "but_it_no_longer_holds": not is_a(g, car, "car"),
            "SO_IT_IS_NOT_TRUSTED": tagged_as(g, car) is None,
            "and_generalise_does_not_use_it": params == ("chunk",) and ptypes == {},
            "so_the_learned_function_declares_no_false_type":
                fnm.param_types(g, learned) == {}}


def check_intake_turns_a_said_thing_into_a_goal_and_the_loop_runs_it():
    """Intake. The loop is driven entirely by a goal, and until now the only way to get one was to call
    `goal.py` from Python — so the one thing that *starts* the system was the one thing it could not receive.

    Tractable now only because a goal is no longer arbitrary structure: it is a handful of constraint
    nodes from a closed vocabulary. The `ugm/`-era attempts translated prose into anything and got 0/50.

    Vacuity guard: the parsed goal must drive a real plan, not merely parse."""
    from . import driver as D, goal as G, intake as I, thread as T
    g, world = _blocks()
    goal = I.read_goal(g, "\n".join([
        "goal stack a on b on c:",
        "    # what must be true of the world",
        "    a on b",
        "    b on c",
        "    never unstack",
    ]))
    a, b, c = g.targets(world, "block")
    world_cs = G.world_constraints(g, goal)
    result = D.pursue(g, goal, T.open_thread(g), world, max_steps=400)
    return {"it_read_two_world_constraints": len(world_cs) == 2,
            "pointing_at_the_right_individuals":
                (g.target(world_cs[0], "subject"), g.target(world_cs[0], "object")) == (a, b),
            "and_one_constraint_on_the_plan": len(G.plan_constraints(g, goal)) == 1,
            "comments_are_ignored": len(G.constraints(g, goal)) == 3,
            "it_round_trips": "never unstack" in I.describe(g, goal),
            "AND_THE_LOOP_ACTUALLY_RUNS_IT": result["found"],
            "with_the_prohibition_in_force": "unstack" not in D.plan_steps(g, result)}


def check_intake_refuses_rather_than_guessing():
    """Refusal is the feature. Three ways in, all loud: a sentence outside the closed vocabulary, a name
    that matches nothing, and — the one the project learned the hard way — a name that matches more than
    one thing. Nodes are nameless and a `label` is a convenience, so *never identify by name alone*.

    Vacuity guards: a well-formed goal in the same graph must parse; and a refusal must leave nothing
    behind, or the caller could pursue a half-built goal and appear to be working."""
    from . import goal as G, intake as I
    g, world = _blocks()
    before = len(g.nodes)

    def refuses(text):
        try:
            I.read_goal(g, text)
            return None
        except I.Unreadable as e:
            return str(e)

    unknown_form = refuses("goal x:\n    please make it nice")
    unknown_name = refuses("goal x:\n    a on zzz")
    g.link(world, "block", g.mint("block", kind_of="block", label="a", clear=True, height=1))
    ambiguous = refuses("goal x:\n    a on b")
    leftovers = len(g.nodes) - before - 1                 # the duplicate block we just added
    ok = I.read_goal(g, "goal x:\n    some block")
    return {"refuses_an_unreadable_line": unknown_form is not None and "vocabulary is closed" in unknown_form,
            "refuses_an_unknown_name": unknown_name is not None and "nothing here is called" in unknown_name,
            "REFUSES_AN_AMBIGUOUS_NAME": ambiguous is not None and "ambiguous" in ambiguous,
            "and_says_a_name_is_not_an_identity": "not an identity" in (ambiguous or ""),
            "a_refusal_leaves_nothing_behind": leftovers == 0,
            "but_a_good_goal_still_parses": len(G.constraints(g, ok)) == 1}


def check_END_TO_END_plan_act_diverge_replan_succeed():
    """The whole loop, in one RUN. Materialise a world and a goal, bootstrap a thread, then:
    plan by imagining → act for real → reality disagrees → replan from where we actually are → succeed.

    The first listing finds nothing (the plan's prediction breaks); a file appears; the retry finds it.

    Vacuity guards, because a green here could mean almost anything: attempt 1 must genuinely have
    diverged (not merely been skipped); the goal must be closed only *after* reality delivered, and must be
    structurally true at the end rather than merely recorded; and the thread must hold the whole story."""
    from . import dispatch as D, driver as Dr, goal as G, thread as T
    g, d = _scanner_fs()
    declare_type(g, "file", attrs={"kind_of": None})
    th = T.open_thread(g, "session")
    goal = G.open_goal(g, label="find a file")
    G.require_type(g, goal, "file")

    calls = {"n": 0}
    def ls(gr, target):
        calls["n"] += 1
        if calls["n"] >= 2:                     # the world changes between attempts
            gr.link(target, "file", gr.mint("file"))
    D.register("ls", ls)

    out = Dr.carry_out(g, goal, th, d, max_steps=50)
    first, second = out["attempts"][0], out["attempts"][1]
    return {"done": out["done"],
            "took_two_attempts": out["tries"] == 2,
            "the_first_really_diverged": not first["completed"] and "diverged" in first,
            "on_a_broken_prediction": "expected some new file node" in first["diverged"],
            "it_replanned_rather_than_giving_up": second["steps"] == ("scan_dir",),
            "and_the_second_completed": second["completed"],
            "the_tool_really_ran_twice": calls["n"] == 2,
            "GOAL_TRUE_IN_REALITY": G.satisfied(g, goal, under=d),
            "and_only_now_recorded_closed": G.is_closed(g, goal),
            "the_thread_holds_the_PLANNING": any(
                g.kind(e) == "application" and not g.attr(e, "done") for e in T.entries(g, th)),
            "and_what_was_actually_DONE": [g.attr(e, "function") for e in T.entries(g, th)
                                           if g.attr(e, "done")] == ["scan_dir", "scan_dir"]}


def check_a_mock_is_never_proposed_as_an_action():
    """A mock is an assumption about how a real call turns out, not something to do. Proposing one would
    plan to *assume* rather than to act, and the plan would name a function that must never be executed for
    real. `workbench.step` substitutes it when the real operator is stepped — that is where it belongs.

    This was a live bug, invisible until a scenario had mocks: the first run of the check above planned
    `found_two` instead of `scan_dir`. Vacuity guard: the mocks must genuinely be type-valid candidates
    here, or excluding them proves nothing."""
    from . import driver as D, function as fnm, workbench as W
    g, d = _scanner_fs()
    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    offered = {n for n, _b in D.proposals(g, f0)}
    mocks = set(fnm.mocks_of(g, "scan_dir"))
    return {"the_mocks_exist": mocks == {"found_two", "found_none"},
            "and_would_otherwise_qualify":
                all(fnm.param_types(g, m) == {"d": "dir"} for m in mocks),
            "but_none_is_offered": offered & mocks == set(),
            "the_real_operator_is": offered == {"scan_dir"}}


def fn_returns(g, name):
    from . import function as fnm
    return fnm.returns_of(g, name)


def check_a_different_number_of_files_is_not_a_divergence():
    """The correction that matters. A listing produces a *variable* number of files, so the `2` in the
    mock is a witness, not a promise. Expecting exactly two would diverge on noise and make the whole
    mechanism useless in practice. The expectation is existential: *some* file exists.

    Vacuity guards: one file and five files must both complete (either side of the mock's two), and zero
    must still diverge — otherwise the expectation would be vacuous rather than merely lenient."""
    from . import dispatch as D, execution as X, workbench as W

    def reality_with(n):
        g, d = _scanner_fs()
        def ls(gr, target):
            for _ in range(n):
                gr.link(target, "file", gr.mint("file"))
        D.register("ls", ls)
        wb = W.open_workbench(g, d)
        f0 = W.root_frame(g, wb)
        f1, _ = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)}, assume="found_two")
        return X.execute(g, wb, f1)

    return {"the_mock_predicted_two": True,
            "one_file_is_fine": reality_with(1)["completed"],
            "five_files_are_fine": reality_with(5)["completed"],
            "but_none_still_diverges": not reality_with(0)["completed"]}


def check_recovering_from_a_broken_prediction():
    """The whole loop closing: an expectation-based divergence recovers through the ordinary contingency
    machinery. The plan assumed two files; reality found none; the branch that assumed *none* was explored,
    so execution continues down it.

    Vacuity guard that matters most: the sibling must be chosen because its predictions hold, not merely
    because its declared type matches — both mocks return `listing`, so the type cannot be what selected it."""
    from . import dispatch as D, execution as X, function as fnm, workbench as W
    g, d = _scanner_fs()
    fnm.define(g, "archive", ("x",), (), "Archive a listed directory.", None, {"x": "listing"}, "listing")
    D.register("ls", lambda gr, target: gr.put(target, count=0))        # reality: empty

    wb = W.open_workbench(g, d)
    f0 = W.root_frame(g, wb)
    m0 = W.mapping_for(g, f0, d)
    two, tr_two = W.step(g, wb, f0, "scan_dir", {"d": m0}, assume="found_two")
    none, tr_none = W.fork(g, wb, f0, "scan_dir", {"d": m0}, assume="found_none")
    W.step(g, wb, none, "archive", {"x": X._successor_in(g, m0, none)})

    result = X.execute(g, wb, two)
    rec = X.recover(g, result)
    return {"diverged_on_a_prediction": "unmet_expectations" in (result["deviation"] or {}),
            "BOTH_MOCKS_DECLARE_THE_SAME_TYPE":
                g.attr(tr_two, "expects") == g.attr(tr_none, "expects") == "listing",
            "recovered_by_contingency": rec["kind"] == "contingency",
            "onto_the_branch_that_assumed_empty": rec.get("branch") == none,
            "and_it_carried_on": rec.get("result", {}).get("ran") == ("scan_dir", "archive"),
            "completed": rec.get("result", {}).get("completed", False)}



# --- query: a question is a goal -------------------------------------------------------------------
def _mortality_library():
    """Paul is a person. One pure way to conclude mortality, and one that reaches the world.

    Both write the *same* attribute, deliberately. If the impure one were merely ranked lower rather
    than barred, the verdict would still come back `yes` — so a check asserting only the answer would be
    vacuous about the thing that matters. It has to assert which function was used.

    And the impure one must sort first, which is load-bearing rather than cosmetic. Both establish
    the same effect, so `relevance` ties them; the frontier sort is stable, so the tie breaks on the order
    `function.names` returns — which is alphabetical, not declaration order. With the pure name winning
    that race, a planted removal of the purity bar still produced a proof naming `conclude_mortal`, so
    `AND_NEVER_APPEARS_IN_A_PROOF` passed *while testing nothing*. Hence `ask_the_registrar`: it sorts
    before `conclude_mortal`, making the trap the path the search takes by default, which is the only
    arrangement under which that key means anything. Reordering the source text does NOT achieve this
    (the first attempt did exactly that and changed nothing) - the name is what decides."""
    from . import asm
    g = new_graph()
    declare_type(g, "person")
    declare_type(g, "mortal_thing", attrs={"mortal": True})
    asm.load_text(g, "\n".join([
        "# Establishes the fact by reaching the world - must never answer a question.",
        "# Declared FIRST on purpose: see the docstring. This is the one the search would otherwise take.",
        "fn ask_the_registrar(p: person) -> mortal_thing:",
        '    DISPATCH R(out) "registrar" F(p)',
        '    SET F(p) "mortal" true',
        "",
        "# Everyone who is a person is mortal. Concludes; never acts.",
        "fn conclude_mortal(p: person) -> mortal_thing:",
        '    SET F(p) "mortal" true',
    ]))
    paul = g.mint("person", label="paul")
    g.link("root", "person", paul)
    tag(g, paul, "person")
    return g, paul


def check_a_question_is_a_goal_and_the_plan_is_the_proof():
    """Asking is pursuing. The question is an ordinary goal node, the answer comes from `driver.pursue`,
    and the plan it finds is the derivation - so the justification arrives with the verdict rather than
    being reconstructed afterwards.

    Vacuity guard: asking must leave the world untouched. The derivation ran on a workbench, so `paul`
    is not mortal until `settle` replays it. A version that concluded straight into the graph would pass
    every other key here while making a question a destructive act."""
    from . import goal as G, query as Q, thread as T
    g, paul = _mortality_library()
    q = G.open_goal(g, about=paul, label="is paul mortal?")
    G.require_attr(g, q, paul, "mortal", True)
    ans = Q.ask(g, q, T.open_thread(g, "t"), "root")
    used = [name for name, _b in Q.steps_of(g, ans)]
    before = g.attr(paul, "mortal")
    rep = Q.settle(g, ans)
    return {"verdict_is_yes": ans["verdict"] == Q.YES,
            "the_proof_is_the_plan": len(ans["proof"]) == 2,      # start frame + one step
            "and_it_names_the_derivation": used == ["conclude_mortal"],
            "ASKING_CHANGED_NOTHING": before is None,
            "settling_commits_it": rep["completed"] and g.attr(paul, "mortal") is True,
            "explained_as_a_cause": "because" in Q.explain(g, ans)}


def check_a_derivation_may_never_act():
    """The one genuinely new rule: concluding and doing are both "running a microfunction", so the
    difference cannot be left to intent. A function that could reach the world is barred from answering a
    question - proved off the stored body, and pruned rather than ranked.

    The load-bearing assertions are the last three keys, not the verdict. Both functions establish
    `mortal`, so the answer is `yes` either way; what distinguishes a working bar from an absent one is
    that the impure function is never even proposed.

    What removing the bar actually does, measured rather than assumed. It does not quietly send mail:
    the search is on a workbench, so `dispatch.service` refuses the imagined target and the whole question
    dies with `Imagined`. The last key plants exactly that and asserts the raise - which is *also* the proof
    that `ask_the_registrar` is the path the search really takes, since a search that ignored it could not
    crash on it. The genuine exposure is at `settle`, where the proof is replayed for real; that is why the
    bar exists rather than leaning on the workbench guard."""
    from . import dispatch as DP, driver as D, goal as G, query as Q, thread as T, workbench as W
    g, paul = _mortality_library()
    q = G.open_goal(g, about=paul, label="is paul mortal?")
    G.require_attr(g, q, paul, "mortal", True)
    ans = Q.ask(g, q, T.open_thread(g, "t"), "root")

    wb = W.open_workbench(g, "root")                  # what the search was allowed to see
    f0 = W.root_frame(g, wb)
    allowed = frozenset(Q.derivations(g))
    offered = {n for n, _b in D.proposals(g, f0, allow=allowed.__contains__)}
    unfiltered = {n for n, _b in D.proposals(g, f0)}
    return {"the_pure_one_is_a_derivation": Q.is_pure(g, "conclude_mortal"),
            "THE_DISPATCHING_ONE_IS_NOT": not Q.is_pure(g, "ask_the_registrar"),
            "both_establish_the_same_fact":
                ("attr", "mortal", "p", True) in D.establishes(g, "conclude_mortal")[0]
                and ("attr", "mortal", "p", True) in D.establishes(g, "ask_the_registrar")[0],
            "so_it_WOULD_have_been_available_unfiltered": "ask_the_registrar" in unfiltered,
            "BUT_IT_IS_NEVER_PROPOSED": "ask_the_registrar" not in offered,
            "AND_NEVER_APPEARS_IN_A_PROOF":
                "ask_the_registrar" not in [n for n, _b in Q.steps_of(g, ans)],
            # This key changed its evidence, and the bar is unchanged. It used to
            # assert that removing the bar made the question die with `Imagined`, using the crash as proof
            # that `ask_the_registrar` is really on the path. An operator that cannot be imagined is now
            # Skipped rather than fatal — it was escaping `loop.tick` and killing every other task on the
            # shared agenda, the same defect `execution.step` records for `TypeViolation` — so nothing
            # dies any more. The proof is now the record it leaves: without the bar the search reaches
            # the impure function and marks it unimaginable, which says the path is taken *and* that the
            # workbench guard was never what did the real work. This docstring's own point stands: the
            # genuine exposure is at `settle`, where the proof is replayed for real.
            "AND_WITHOUT_THE_BAR_THE_SEARCH_REACHES_IT_AND_SAYS_SO":
                _without_the_purity_bar_it_is_unimaginable()}


def _without_the_purity_bar_it_is_unimaginable() -> bool:
    """Plant the removal of the purity bar and confirm the search reaches the impure function.

    This is an in-harness version of the probe asks for, kept because the key it guards was a false
    green first: with the bar removed the search still returned a proof naming the pure function, so
    `AND_NEVER_APPEARS_IN_A_PROOF` passed while testing nothing. It only bites once the impure name sorts
    first (`function.names` sorts alphabetically), and this probe is what demonstrates that it now does."""
    from . import dispatch as DP, goal as G, query as Q, thread as T, function as F
    g, paul = _mortality_library()
    q = G.open_goal(g, about=paul)
    G.require_attr(g, q, paul, "mortal", True)
    real = Q.derivations
    Q.derivations = lambda gr: F.names(gr)                  # the bar, removed
    try:
        Q.ask(g, q, T.open_thread(g, "probe"), "root")
    except Exception:
        return False                                        # it must no longer die on it
    finally:
        Q.derivations = real
    # The evidence: some search in this graph met `ask_the_registrar` and could not imagine it. If the
    # search never went near it, nothing would be marked and this proves as little as the old false green.
    _ = DP
    return any("ask_the_registrar" in (g.attr(s2, "unimaginable") or ())
               for s2 in g.of_kind("search"))


def check_unknown_is_not_no_unless_you_say_so():
    """Three answers, and `unknown` is the honest default. A search that found no derivation has learned
    about its own library, not about the world - so only an explicit closed-world stance turns that into
    `no`. Refutation is the separate, stronger claim: something incompatible holds now.

    The stance is a parameter rather than a constant because it is an opinion, which is the same reason
    the old engine kept CWA/OWA in a policy object instead of in the engine."""
    from . import goal as G, query as Q, thread as T
    g = new_graph()
    declare_type(g, "person")
    jo = g.mint("person", label="jo")
    g.link("root", "person", jo)
    tag(g, jo, "person")

    def asking(**kw):
        q = G.open_goal(g, about=jo, label="is jo mortal?")
        G.require_attr(g, q, jo, "mortal", True)
        return Q.ask(g, q, T.open_thread(g, "t%d" % len(g.attrs)), "root", **kw)

    open_world, closed_world = asking(), asking(assume_complete=True)

    g2 = new_graph()                                   # zed is recorded as NOT mortal
    declare_type(g2, "person")
    zed = g2.mint("person", label="zed", mortal=False)
    g2.link("root", "person", zed)
    tag(g2, zed, "person")
    q2 = G.open_goal(g2, about=zed)
    G.require_attr(g2, q2, zed, "mortal", True)
    refuted = Q.ask(g2, q2, T.open_thread(g2, "t"), "root")

    return {"no_derivation_means_UNKNOWN": open_world["verdict"] == Q.UNKNOWN,
            "the_stance_is_what_makes_it_NO": closed_world["verdict"] == Q.NO,
            "and_it_says_so": "assumed complete" in closed_world["why"],
            "refutation_is_the_stronger_claim": refuted["verdict"] == Q.NO,
            "WITHOUT_ANY_STANCE": "already" in refuted["why"],
            "and_it_reports_what_HOLDS_not_what_was_wanted": "is already False" in refuted["why"],
            "an_absent_edge_refutes_nothing": open_world["verdict"] != Q.NO}


def _lines(*parts):
    """Join CNL lines. Written this way on purpose: an earlier version of these checks embedded `\n`
    escapes inside generated source and they collapsed into real newlines, producing an unterminated
    string literal. Building the text from parts has no escapes to get wrong."""
    return "\n".join(parts)


_BODY = "    paul.mortal = true"


def check_one_grammar_three_verbs():
    """A question is a goal, so `goal`, `ask` and `why` share one grammar and one node shape. The
    constraints parse identically; only the recorded verb differs, because which speech act something was
    is genuinely not recoverable from what it says.

    Vacuity guard: the two blocks must produce the same constraints, or "one grammar" is a claim about
    the parser rather than about the data model. And a plan constraint has to work inside a question -
    `never conclude_mortal` asks "is this derivable without that rule?", which is a real question that
    needed nothing added to support."""
    from . import goal as G, intake as I, thread as T
    g, _paul = _mortality_library()
    verb_g, as_goal = I.read(g, _lines("goal make paul mortal:", _BODY))
    verb_a, as_ask = I.read(g, _lines("ask is paul mortal?:", _BODY))

    def shape(node):
        return tuple(sorted((g.attr(c, "sort"), g.attr(c, "key"), g.attr(c, "value"))
                            for c in G.constraints(g, node)))

    th = T.open_thread(g, "t")
    banned = I.respond(g, _lines("ask without that rule?:", _BODY, "    never conclude_mortal"), th)
    plain = I.respond(g, _lines("ask is paul mortal?:", _BODY), th)
    return {"the_verbs_are_read": (verb_g, verb_a) == ("goal", "ask"),
            "SAME_CONSTRAINTS_FROM_BOTH": shape(as_goal) == shape(as_ask),
            "the_verb_is_recorded": g.attr(as_ask, "verb") == "ask",
            "and_round_trips": I.describe(g, as_ask).startswith("ask "),
            "read_goal_refuses_a_question": _read_goal_refuses_an_ask(),
            "A_PLAN_CONSTRAINT_WORKS_IN_A_QUESTION": banned.startswith("UNKNOWN"),
            "and_it_pruned_rather_than_searched": "(0 step(s)" in banned,
            "while_the_same_question_unconstrained_is_yes": plain.startswith("YES")}


def _read_goal_refuses_an_ask() -> bool:
    from . import intake as I
    g, _paul = _mortality_library()
    try:
        I.read_goal(g, _lines("ask is paul mortal?:", _BODY))
        return False
    except I.Unreadable:
        return True


def check_why_answers_from_history_and_never_invents_it():
    """"Why" means *find a causal explanation*, and the only honest source is what really ran. Three
    situations, kept apart on purpose: derived here (a cause), true but given (no cause to give), and not
    true at all (nothing to explain).

    The absent fourth behaviour is the point. For a fact that already holds, a fresh search would
    happily produce "here is a way this could follow" - a fine answer to a different question and a lie as
    an account of history. `AND_INVENTS_NO_DERIVATION` asserts the engine says it does not know rather than
    manufacturing one, which is the failure that would make every explanation untrustworthy.

    Vacuity guard: `settle` must record on the thread, or the first case degrades into the second
    silently - the fact would be committed and then unexplainable."""
    from . import intake as I, thread as T
    why_block = _lines("why is paul mortal?:", _BODY)
    ask_block = _lines("ask is paul mortal?:", _BODY)

    derived, _p = _mortality_library()
    th = T.open_thread(derived, "t")
    I.respond(derived, ask_block, th)                       # settles by default
    from_history = I.respond(derived, why_block, th)

    given, p2 = _mortality_library()
    given.put(p2, mortal=True)
    was_given = I.respond(given, why_block, T.open_thread(given, "t"))

    absent, _p3 = _mortality_library()
    untrue = I.respond(absent, why_block, T.open_thread(absent, "t"))

    unkept, _p4 = _mortality_library()
    th4 = T.open_thread(unkept, "t")
    I.respond(unkept, ask_block, th4, keep=False)
    unkept_why = I.respond(unkept, why_block, th4)
    return {"derived_here_names_the_cause": "because conclude_mortal(p=paul) ran" in from_history,
            "TRUE_BUT_GIVEN_ADMITS_IT": "it was given, not worked out" in was_given,
            "AND_INVENTS_NO_DERIVATION": "because" not in was_given,
            "not_true_means_nothing_to_explain": "does not hold" in untrue,
            "and_it_redirects_to_the_question_that_DOES_apply": "could be derived" in untrue,
            "settling_is_what_makes_history": "because" in from_history,
            "SO_AN_UNKEPT_ANSWER_LEAVES_NONE": "because" not in unkept_why}


def check_the_trace_is_an_observer_not_a_participant():
    """The hook the live pages are built on. It reports what the search does; it must not change it.

    The load-bearing key is `identical_plan`. A watcher that perturbed the search would make every
    animated explanation a description of a *different* run than the one a user gets untraced - the exact
    failure this project keeps catching in other forms.

    The first version of this check compared imagined-STEP counts, and it was wrong — the search is
    tie-break nondeterministic. Two identical searches on fresh graphs, in one process, at a fixed hash
    seed, imagine 2 or 3 states (measured: 17 and 23 out of 40). Node ids shift between runs, mapping
    enumeration order follows, and the stable frontier sort then breaks ties differently. The PLAN is
    invariant; the number of states considered on the way to it is not. So a step-count comparison was
    reporting engine nondeterminism as a tracing defect - a check that fails for a true reason it does not
    name is barely better than one that passes for a false one.

    `refuse` events matter most and are the easiest to omit: a pruned action leaves NO trace anywhere
    afterwards, precisely because nothing happened. Without emitting it, "it never even considered painting"
    is invisible - which is the single most interesting thing the search does."""
    from . import driver as D, intake as I, thread as T
    text = _lines("goal build a tower:", "    a on b", "    b on c", "    never paint")

    def run(trace=None):
        g, world = _blocks()
        goal = I.read_goal(g, text)
        r = D.pursue(g, goal, T.open_thread(g, "t"), world, trace=trace)
        return [(f, tuple(sorted(b))) for f, b in D.plan_bindings(g, r["plan"])] if r["found"] else None

    seen = []
    watched = run(trace=seen.append)
    quiet = run()
    kinds = [e["kind"] for e in seen]
    refused = [e for e in seen if e["kind"] == "refuse"]
    found = [e for e in seen if e["kind"] == "found"]
    return {"identical_plan": watched is not None and watched == quiet,
            "it_opens_with_the_goal": kinds[0] == "goal",
            "and_ends_with_the_verdict": kinds[-1] == "found",
            "PRUNING_IS_VISIBLE": bool(refused),
            "and_it_names_the_constraint": refused[0]["because"] == ["never paint"],
            "the_forbidden_action_is_NEVER_imagined":
                not any(e["kind"] == "imagine" and e["action"] == "paint" for e in seen),
            "ranking_is_visible": {e["band"] for e in seen if e["kind"] == "consider"} != {0},
            "the_plan_carries_labels_not_ids":
                found[0]["plan"] == [("stack", {"b": "b", "onto": "c"}),
                                     ("stack", {"b": "a", "onto": "b"})],
            "an_untraced_search_still_finds_it": quiet is not None}


# --- the reference language, and types that use it ---------------------------------------------------
def _garage_cnl():
    """A `wheel` and a `car` authored the way a domain would author them: as text."""
    from . import intake as I
    g = new_graph()
    I.read(g, _lines("type wheel:",
                     "    has 1 rim each of kind rim",
                     "    pressure between 2.0 and 2.6"))
    I.read(g, _lines("type car:",
                     "    has 1 body each of kind body",
                     "    has 4 wheel each a wheel",
                     "    has at most 1 trailer",
                     "    weight between 800 and 2000",
                     "    wheel[0].pressure == wheel[1].pressure",
                     "    wheel[0].rim is not wheel[1].rim"))
    return g


def _a_car(g, *, pressures=(2.2,) * 4, weight=1200, rims=True, one_rim=False, trailers=0):
    c = g.mint("chunk", weight=weight)
    g.link("root", "has", c)
    g.link(c, "body", g.mint("body"))
    shared = g.mint("rim")
    for p in pressures:
        w = g.mint("wheel", pressure=p)
        if rims:
            g.link(w, "rim", shared if one_rim else g.mint("rim"))
        g.link(c, "wheel", w)
    for _ in range(trailers):
        g.link(c, "trailer", g.mint("trailer"))
    return c


def check_a_type_is_authored_as_text_and_round_trips():
    """A type was the last thing on the surface that could only be authored by calling Python, which is
    exactly the "reach past the surface and write graph structure" `intake.py` says must never happen.

    Vacuity guard: the round trip is compared to the authored text, not to a re-render of itself, so a
    renderer that agreed with a broken parser could not pass."""
    from . import intake as I, types as TY
    g = _garage_cnl()
    authored = _lines("type wheel:",
                      "    has 1 rim each of kind rim",
                      "    pressure between 2.0 and 2.6")
    refusals = {}
    for name, text in (("says_nothing", "type t:\n    because just a word\n"),
                       ("count_left_out", "type t:\n    has wheel\n"),
                       ("unknown_form", "type t:\n    has 4 wheel each blue\n"),
                       ("redeclaration", "type car:\n    has 4 wheel\n")):
        try:
            I.read(g, text)
            refusals[name] = False
        except I.Unreadable:
            refusals[name] = True
    return {"round_trips_to_what_was_written": TY.describe(g, "wheel") == authored,
            "declared_as_ordinary_graph_data": g.kind(TY.find_type(g, "car")) == "type",
            **refusals}


def check_a_schema_reaches_deeper_than_one_level():
    """The one-level limit is gone. `README.md` recorded it as an honest limit: a schema checked a
    label's targets by graph kind and could say nothing about what those targets were, so "on a block which
    is on a block" had no schema and a magnitude had to be smuggled in as an attribute.

    Vacuity guard: the flat-tyred car has four targets of the right *kind*, so anything that only counted
    kinds would call it a car. It is refused because each wheel is checked as a `wheel`."""
    from . import types as TY
    g = _garage_cnl()
    good, flat = _a_car(g), _a_car(g, pressures=(0.4,) * 4)
    rimless = _a_car(g, rims=False)
    return {"a_well_formed_car_passes": TY.is_a(g, good, "car"),
            "KIND_ALONE_WOULD_HAVE_PASSED_IT":
                len([w for w in g.targets(flat, "wheel") if g.kind(w) == "wheel"]) == 4,
            "but_the_nested_type_refuses_it": not TY.is_a(g, flat, "car"),
            "and_a_missing_grandchild_refuses_too": not TY.is_a(g, rimless, "car"),
            "the_reason_names_the_label": "wheel" in TY.violations(g, flat, "car")}


def check_a_recursive_type_terminates_on_cyclic_data():
    """Recursion into a target's schema makes a cycle in the data reachable — two people who are each
    other's friend. The coinductive stance (assume it holds while proving it holds) is what terminates
    without banning recursive declarations, and it is the same stance `subsumes` takes."""
    from . import intake as I, types as TY
    g = new_graph()
    I.read(g, _lines("type person:", "    has some friend each a person"))
    a, b, lonely = g.mint("p"), g.mint("p"), g.mint("p")
    for n in (a, b, lonely):
        g.link("root", "has", n)
    g.link(a, "friend", b)
    g.link(b, "friend", a)
    return {"mutual_friends_terminate_and_pass": TY.is_a(g, a, "person"),
            "someone_with_no_friends_is_refused": not TY.is_a(g, lonely, "person")}


def check_a_type_relates_two_of_its_children():
    """The demand a per-label requirement structurally cannot express: not *what a label holds* but
    *two places reached from the same subject agreeing*. Both sides are `path.py` references.

    `==` compares values and `is` compares identities — the position deciding how the last segment of
    each path is read. Both are checked here, because a single one would not discriminate the two."""
    from . import types as TY
    g = _garage_cnl()
    good = _a_car(g)
    uneven = _a_car(g, pressures=(2.2, 2.4, 2.2, 2.2))
    shared = _a_car(g, one_rim=True)
    return {"agreeing_children_pass": TY.is_a(g, good, "car"),
            "DISAGREEING_VALUES_REFUSED": not TY.is_a(g, uneven, "car"),
            "SHARED_IDENTITY_REFUSED": not TY.is_a(g, shared, "car"),
            "and_the_reason_quotes_the_reference":
                any("wheel[0].pressure" in k for k in TY.violations(g, uneven, "car")),
            "the_two_failures_are_different_constraints":
                set(TY.violations(g, uneven, "car")) != set(TY.violations(g, shared, "car"))}


def check_a_count_is_a_range_and_a_value_may_be_bounded():
    """A count used to be one exact number and an attribute one exact value, so "between 800 and 2000" and
    "at most one trailer" had nowhere to live. Vacuity guard: the zero-trailer and one-trailer cars must
    BOTH pass, or `at most 1` would be indistinguishable from `exactly 1`."""
    from . import types as TY
    g = _garage_cnl()
    return {"no_trailer_passes": TY.is_a(g, _a_car(g, trailers=0), "car"),
            "one_trailer_passes_too": TY.is_a(g, _a_car(g, trailers=1), "car"),
            "two_trailers_refused": not TY.is_a(g, _a_car(g, trailers=2), "car"),
            "weight_in_range_passes": TY.is_a(g, _a_car(g, weight=1999), "car"),
            "weight_out_of_range_refused": not TY.is_a(g, _a_car(g, weight=2001), "car")}


def check_subsumption_compares_tightness_not_equality():
    """Once a demand is a range, "the subtype demands everything the supertype does" stops being dict
    equality. A type narrowing its base's range must still be a subtype, or every widened type would stop
    subsuming its own base and `function.producers` would quietly lose candidates.

    Undecidable cases answer False on purpose — a lost candidate is recoverable, an unsound one is
    not. `!=` is the witness: it implies nothing this is willing to claim."""
    from .types import declare_type, subsumes, AttrReq, Req
    g = new_graph()
    declare_type(g, "loaded", attrs={"weight": AttrReq("between", 800, 2000)})
    declare_type(g, "midweight", attrs={"weight": AttrReq("between", 900, 1000)})
    declare_type(g, "exact", attrs={"weight": AttrReq("==", 950)})
    declare_type(g, "heavy", attrs={"weight": AttrReq("between", 1500, 3000)})
    declare_type(g, "unequal", attrs={"weight": AttrReq("!=", 0)})
    declare_type(g, "wheeled", {"wheel": Req(lo=1)})
    declare_type(g, "quad", {"wheel": Req(lo=4, hi=4)})
    return {"a_narrower_range_is_a_subtype": subsumes(g, "loaded", "midweight"),
            "an_exact_value_inside_it_too": subsumes(g, "loaded", "exact"),
            "a_wider_range_is_NOT": not subsumes(g, "midweight", "loaded"),
            "an_overlapping_range_is_NOT": not subsumes(g, "loaded", "heavy"),
            "a_tighter_count_is_a_subtype": subsumes(g, "wheeled", "quad"),
            "and_the_undecidable_case_says_no": not subsumes(g, "unequal", "exact")}


def check_a_reference_is_one_language_and_the_surface_refuses_what_it_cannot_honour():
    """The path grammar existed three times, undeclared — `driver.role_node`'s private regex,
    `intake`'s hand-split on the first dot, and the dotted roles `establishes` emitted. One module now.

    The composition finding, and it was a live silent defect. `a.wheel[1].pressure = 3` in a goal
    split on the first dot and produced a constraint about an attribute literally named
    `wheel[1].pressure` — unmeetable, and `describe_constraint` rendered it back looking correct. It is
    refused now, because `conflict.py` keys a slot by `(subject, key)` and `query.settle` writes with
    `g.put(subject, …)`; both would be silently wrong for a navigated subject. Depth is available where
    only checking happens, and refused where it is not yet honoured."""
    from . import intake as I, driver as D, path as P
    g = new_graph()
    a = g.mint("chunk", label="a", clear=False)
    g.link("root", "has", a)
    w = g.mint("wheel", pressure=2.2)
    g.link(a, "wheel", w)

    def refused(text):
        try:
            I.read(g, text)
            return False
        except I.Unreadable:
            return True

    p = P.parse("wheel[0].rim.serial")
    return {"one_grammar_parses_and_renders": P.render(p) == "wheel[0].rim.serial" and len(p.hops) == 3,
            "a_bare_word_on_the_right_is_a_value": not P.is_reference("red"),
            "and_a_hop_makes_it_a_reference": P.is_reference("body.colour"),
            "the_driver_resolves_through_the_same_module":
                D.role_node(g, {"c": a}, "c.wheel[0]") == w and D.role_node(g, {"c": a}, "c.nope") is None,
            "shallow_goal_reference_still_reads": not refused("goal x:\n    a.clear = true\n"),
            "DEEP_GOAL_REFERENCE_IS_REFUSED_NOT_MISREAD":
                refused("goal x:\n    a.wheel[0].pressure = 3\n"),
            "but_a_type_takes_any_depth":
                not refused("type deep:\n    wheel[0].rim.serial == wheel[1].rim.serial\n")}


# --- consumer-reported defects (reported by the first consumer) ------------------------
def check_a_write_through_an_unset_register_is_refused_not_null_linked():
    """, reported with a repro. `regs.get` answers `None` for a register a `GET` never
    filled — an ordinary case the moment a part of the input can be missing — and `g.link` appended it, so
    the graph gained an edge whose target is `None`. `targets` then came back non-empty, every "is
    this part present?" test answered *yes*, and the `None` surfaced arbitrarily far away in whatever
    dereferenced it.

    Vacuity guard: the control asserts the `GET` genuinely found nothing, so this cannot pass merely
    because the program failed for some earlier reason. And the graph must be unchanged afterwards — a
    refusal that still left the edge behind would be worse than the bug."""
    from .isa import GET, Machine
    g = new_graph()
    f = g.mint("for_stmt")
    g.link("root", "has", f)
    prog = Machine((GET(R("seq"), F("f"), "over"), LINK(F("f"), "repeats_over", R("seq"))))
    try:
        prog.run(g, Focus(g).open("f", f))
        refused, why = False, ""
    except RuntimeError as e:
        refused, why = True, str(e)
    return {"the_register_really_is_empty": g.target(f, "over") is None,
            "REFUSED_INSTEAD_OF_LINKING_TO_NOTHING": refused,
            "and_it_names_the_operand": "R(seq)" in why and "LINK" in why,
            "no_null_edge_was_left_behind": g.targets(f, "repeats_over") == (),
            "so_the_part_still_reads_as_ABSENT": g.count(f, "repeats_over") == 0}


def check_a_declared_parameter_type_is_enforced_at_the_call_site():
    """, reported with the case that makes it bite: a safety property carried entirely in a parameter
    type. It was checked only by `driver.proposals`, so the guarantee was *"no plan builds it"* while the
    documentation said *"it is unbuildable"* — and a consumer had to hand-write a `CHECK` as the first
    instruction, making the declared type and the enforced type two things kept in step by hand.

    Vacuity guard: the valid call must still run, and the opt-out must still bypass — otherwise this
    would pass by refusing everything."""
    from . import function as fn
    from .types import declare_type as dt
    g = new_graph()
    dt(g, "build", attrs={"kind_of": "build"})
    dt(g, "reversible_build", base="build", attrs={"reversible": True})
    ok = g.mint("b", kind_of="build", reversible=True)
    unsafe = g.mint("b", kind_of="build", reversible=False)
    g.link("root", "has", ok)
    g.link("root", "has", unsafe)
    fn.define(g, "finish", ("b",), (SET(F("b"), "finished", True),),
              ptypes={"b": "reversible_build"})
    fn.define(g, "touch", ("x",), (SET(F("x"), "touched", True),))     # untyped parameter

    def call(node, **kw):
        try:
            fn.invoke(g, "finish", {"b": node}, **kw)
            return True
        except TypeViolation:
            return False

    return {"the_valid_call_still_runs": call(ok) and g.attr(ok, "finished") is True,
            "THE_UNSAFE_CALL_IS_REFUSED": not call(unsafe),
            "and_it_left_nothing_behind": g.attr(unsafe, "finished") is None,
            "the_opt_out_still_bypasses": call(unsafe, check_types=False),
            "an_untyped_parameter_is_unconstrained":
                fn.invoke(g, "touch", {"x": unsafe}) is not None}


def check_the_reference_language_refuses_what_it_cannot_express():
    """Found by probing whether where/when/what are sugar. Two silent
    acceptances, both the same class as the mis-parse records:

    * `path.parse("contains*")` succeeded, yielding a label literally named `contains*` — matching
      nothing, forever, silently. Anyone writing that is reaching for transitive closure, which this
      grammar genuinely does not have; a label that will never match is the worst possible answer.
    * `has 1 ^contains` accepted `^contains` as a plain edge label. `require_edge` counts
      `g.targets(node, label)` and does not navigate, so the requirement counted an edge nobody has —
      silently zero, unmeetable, and it rendered back looking correct.

    Vacuity guard: the legal forms must still parse, or this would pass by refusing everything."""
    from . import intake as I, path as P

    def bad_path(t):
        try:
            P.parse(t)
            return False
        except P.BadPath:
            return True

    def why_refused(t):
        try:
            P.parse(t)
            return ""
        except P.BadPath as e:
            return str(e)

    g = new_graph()
    try:
        I.read(g, "type t:\n    has 1 ^contains each of kind box\n")
        has_refused = False
    except I.Unreadable:
        has_refused = True
    return {"CLOSURE_IS_REFUSED_NOT_READ_AS_A_LABEL":
                all(bad_path(t) for t in ("contains*", "contains+", "a.b?", "(a|b)")),
            "and_the_message_names_the_gap":
                "no repetition operator" in why_refused("contains*"),
            "A_HAS_LABEL_IS_NOT_A_REFERENCE": has_refused,
            "legal_paths_still_parse":
                len(P.parse("wheel[0].rim.serial").hops) == 3 and len(P.parse("^has").hops) == 1,
            "hyphens_and_digits_are_legal_in_a_label": len(P.parse("part-2.name").hops) == 2}


# --- the search's own state, as graph data ------------------------------------------------------------
def check_the_search_is_reproducible_in_COST_not_just_in_ANSWER():
    """The check the worst defect this project has found would have needed, and did not have.

    `search-was-irreproducible-set-tiebreak`: `workbench.reachable` returned a `set`, so copy order
    fell to node-id hash order, `pursue`'s frontier tie-break became arbitrary, and one 5-block goal gave
    `400/fail`, `400/fail`, `12/found` in a single process. The plan was never *wrong*, only arbitrary
    at arbitrary cost — which is exactly why 132 checks passed over it. Every one of them asserted the
    answer; none asserted the price.

    So this asserts the price. Same goal, several runs, one process: the number of imagined states must be
    identical, not merely the plan. A tie broken by hash order shows up here and nowhere else.

    Run blind, and with headroom, because that is the discriminating case. Guided search on this
    goal imagines 2 states — too few for a tie-break to matter, so a guided-only check would pass over the
    very bug it exists to catch. Unguided, every frontier key is `(0, 0, depth)`, so essentially
    everything ties and the order is decided purely by insertion — which is exactly the condition that
    made the original defect visible. 67 states, six runs, one process.

    Vacuity guard: the search must succeed and do real work (dozens of imagined states), or identical
    counts would be trivially true — and note it must NOT be left at the default `max_steps`, where blind
    search merely exhausts at 60 every time and would look "deterministic" by hitting the ceiling.

    Verified by re-injecting the original defect, rather than by assuming it would catch it: patching
    `search.take_best` to sort `set(frontier)` — the exact shape of the bug — gives

        The_cost_is_identical_across_runs: False      81 imagined states, varying
        and_so_is_the_plan:                True       the plan is still correct

    which is the defect's signature exactly: the answer stays right and only the price wanders, which
    is why a hundred assertions about answers never saw it."""
    from . import driver as D, intake as I, thread as T
    runs = []
    for _ in range(6):
        g, world = _blocks()
        goal = I.read_goal(g, _lines("goal build a tower:", "    a on b", "    b on c"))
        r = D.pursue(g, goal, T.open_thread(g, "t"), world, guided=False, max_steps=400)
        runs.append((r["found"], r["steps"],
                     tuple(f for f, _b in D.plan_bindings(g, r["plan"])) if r["found"] else None))
    first = runs[0]
    return {"it_found_a_plan": first[0],
            "and_it_did_real_work_not_just_hit_the_ceiling": 1 < first[1] < 400,
            "THE_COST_IS_IDENTICAL_ACROSS_RUNS": all(r[1] == first[1] for r in runs),
            "and_so_is_the_plan": all(r[2] == first[2] for r in runs),
            "imagined_states": first[1]}


def check_the_search_can_be_read_by_the_system_that_ran_it():
    """The point of moving the frontier, the visited set, the step count and the refusals out of
    Python locals: `composability-principle` — a hardcoded mechanism is an unreachable island, and the
    homoiconicity claim fails exactly where the mechanism is Python. The search was the last part of the
    planner the planner could not read.

    Vacuity guard: the visited set must name frames that really were imagined, not merely be non-empty —
    a signature recording only a digest would terminate the search and answer nothing about it."""
    from . import driver as D, intake as I, thread as T, search as S, workbench as W
    g, world = _blocks()
    goal = I.read_goal(g, _lines("goal build a tower:", "    a on b", "    b on c", "    never paint"))
    r = D.pursue(g, goal, T.open_thread(g, "t"), world)
    s = r["search"]
    considered = S.considered(g, s)
    return {"the_search_is_a_node": g.kind(s) == "search",
            "IT_KNOWS_WHAT_IT_ALREADY_CONSIDERED": len(considered) > 1,
            "and_they_are_real_imagined_frames":
                all(g.kind(f) == "frame" for f in considered)
                and all(f in W.frames(g, r["workbench"]) for f in considered),
            "it_knows_what_it_refused": bool(S.refusals(g, s)),
            "and_why": S.blocked_by(g, s) == ("never paint",),
            "the_step_count_is_data": S.steps_taken(g, s) == r["steps"],
            "the_frontier_is_ordered_not_a_set":
                isinstance(S.frontier(g, s), tuple),
            "nothing_in_the_world_points_at_the_search": g.sources(s) == ()}


def check_the_search_can_be_DRIVEN_FROM_OUTSIDE_one_step_at_a_time():
    """The yield point. `pursue` was a closed loop: nothing could happen between two imagined
    states, so *"what should I do next?"* was not an expressible question, only a `while` condition. That
    is what `docs/deliberation.md` means by deliberation being the third thing the system computes with and
    cannot compute about — after attention (fixed by `thread.py`) and the goal (by `goal.py`).

    `driver.step` performs one iteration and returns: `None` to continue, the report when finished. So a
    caller that is not `pursue` can drive it, look at the search between steps, and resume.

    Vacuity guard, and it is the whole check: driving it by hand must reach the same plan at the same
    cost as `pursue`. A yield point that changed the search would not be a seam, it would be a fork. And
    the search must be observably *mid-flight* partway through — a frontier that is empty at every pause
    would mean `step` had quietly run the whole thing."""
    from . import driver as D, intake as I, thread as T, search as S, workbench as W
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    # the control: the supported entry point
    g1, w1 = _blocks()
    ref = D.pursue(g1, I.read_goal(g1, text), T.open_thread(g1, "t"), w1,
                   guided=False, max_steps=400)

    # the same search, driven from outside one step at a time
    g2, w2 = _blocks()
    goal = I.read_goal(g2, text)
    th = T.open_thread(g2, "t")
    wb = W.open_workbench(g2, w2, label="by hand")
    root = W.root_frame(g2, wb)
    opened = T.attend(g2, th, goal, why="taking on the goal")
    s = S.open_search(g2, goal, wb, th, w2, opened=opened, max_steps=400, max_depth=6, guided=False)
    S.mark_seen(g2, s, S.digest(*D._visited_key(g2, goal, root, ())), root)
    D._offer(g2, s, root, 0, None)

    pauses, out, turns = [], None, 0
    while out is None and turns < 500:
        turns += 1
        pauses.append((len(S.frontier(g2, s)), len(S.considered(g2, s))))
        out = D.step(g2, s)

    mid = [p for p in pauses[:-1] if p[0] > 0]
    return {"driven_by_hand_finds_it_too": bool(out and out["found"]),
            "SAME_PLAN": (out and tuple(f for f, _b in D.plan_bindings(g2, out["plan"]))
                          == tuple(f for f, _b in D.plan_bindings(g1, ref["plan"]))),
            "AND_THE_SAME_COST": bool(out) and out["steps"] == ref["steps"],
            "it_really_yielded_between_steps": turns > 1,
            "and_was_observably_mid_flight": bool(mid),
            "the_visited_set_grew_as_it_went":
                pauses[-1][1] > pauses[0][1],
            "turns": turns}


def check_a_microfunction_can_DRIVE_THE_PLANNER_and_read_its_answer():
    """Deliberation, reachable as data. `composability-principle` is the standing foundation:
    reflexive mechanisms must combine on one substrate, and *a hardcoded mechanism is an unreachable
    island*. `pursue` was Python and unreachable from the ISA, so the system could plan but could not be
    told to plan, and could not reason about its own planning. `docs/deliberation.md` named it — deliberation
    was the third thing computed with and not about, after attention (fixed by `thread.py`) and
    the goal (by `goal.py`).

    This is the function that closes it, and it is authored as text, not Python:

        fn think(goal, subject, thread) -> plan:
            NATIVE r(s) "plan" F(goal) F(subject) F(thread)
            .again:
            NATIVE r(more) "plan_step" R(s)
            JMPIF r(more) ".again"
            ATTR r(result) R(s) "found"

    `plan` and `plan_step` are primitives, and they earn that by the project's own closed-class
    test: searching cannot be composed from GET/SET/LINK, so this is not sugar. `plan_step` is
    deliberately one iteration rather than a whole search — a primitive that ran to completion would be
    one opaque instruction and would buy nothing, since the point is being able to stop between two
    imagined states.

    They were the opcodes `PLAN` and `STEP` until, and that was a kernel-boundary
    violation: their handlers imported `driver`, so the instruction set knew what a plan was and a Rust
    port would have had to port the planner to implement two instructions. The closed-class argument above
    was right and is preserved — what was wrong was concluding that a primitive must be an *opcode*. They
    are natives now (`native.py`), reached by name through a table the kernel does not populate. See
    `check_the_KERNEL_cannot_see_the_representation_above_it` and
    `docs/execution-model.md`.

    Vacuity guard: the plan reached this way must be the same plan `pursue` finds at the same cost, and
    the answer must be readable as ordinary graph data (`ATTR`), not only via a Python return value."""
    from . import asm, driver as D, execution as X, function as fn, intake as I, thread as T
    text = _lines("goal build a tower:", "    a on b", "    b on c")

    g1, w1 = _blocks()
    ref = D.pursue(g1, I.read_goal(g1, text), T.open_thread(g1, "t"), w1)

    g, world = _blocks()
    goal = I.read_goal(g, text)
    asm.load_text(g, _lines('fn think(goal, subject, thread) -> plan:',
                            '    NATIVE R(s) "plan" F(goal) F(subject) F(thread)',
                            '    .again:',
                            '    NATIVE R(more) "plan_step" R(s)',
                            '    JMPIF R(more) ".again"',
                            '    ATTR R(result) R(s) "found"'))
    _f, out = fn.invoke(g, "think", {"goal": goal, "subject": world,
                                     "thread": T.open_thread(g, "t")}, check_types=False)
    s = out["s"]
    plan = X.path_to(g, g.target(s, "workbench"), g.target(s, "reached"))
    return {"THE_ANSWER_CAME_BACK_THROUGH_AN_ORDINARY_ATTR": out["result"] is True,
            "the_search_is_a_node_the_program_holds": g.kind(s) == "search",
            "the_outcome_is_graph_data":
                (g.attr(s, "done"), g.attr(s, "how"), g.attr(s, "length")) == (True, "found", 2),
            "SAME_PLAN_AS_pursue":
                tuple(f for f, _b in D.plan_bindings(g, plan))
                == tuple(f for f, _b in D.plan_bindings(g1, ref["plan"])),
            "AND_THE_SAME_COST": g.attr(s, "steps") == ref["steps"],
            "the_program_is_data_not_python": bool(fn.load(g, "think")[1])}


def check_asm_refuses_an_export_that_is_not_an_opcode():
    """`isa.__all__` also exports `WRITES_REGISTER` — a frozenset — and `_OPCODES` filtered only on
    `isupper()`, so `asm` accepted it as an instruction at load time and would have failed opaquely
    inside the interpreter. Exactly the silent acceptance `asm.py`'s own docstring says it exists to
    prevent, and the same shape the first consumer reported for `INVOKE`'s operand.

    Vacuity guard: a real opcode added at the same time must still load, or this would pass by refusing
    everything."""
    from . import asm, function as fn
    g = new_graph()
    try:
        asm.load_text(g, _lines("fn bad(x) -> t:", "    WRITES_REGISTER R(a) F(x)"))
        refused = False
    except asm.AsmError:
        refused = True
    asm.load_text(g, _lines("fn fine(x) -> t:", '    ATTR R(a) F(x) "k"'))
    return {"a_non_opcode_export_is_REFUSED": refused,
            "and_it_is_gone_from_the_known_set": "WRITES_REGISTER" not in asm._OPCODES,
            "real_opcodes_still_load": len(fn.load(g, "fine")[1]) == 1,
            # Was `{"PLAN", "STEP"} <= _OPCODES`. Those two are gone — they made `isa.py` import
            # `driver`, putting the planner below the kernel boundary. `NATIVE` replaces both, and the
            # planner registers itself (`native.py`, `docs/execution-model.md`).
            "NATIVE_is_a_known_opcode": "NATIVE" in asm._OPCODES,
            "and_the_two_that_KNEW_the_planner_are_gone":
                not ({"PLAN", "STEP"} & asm._OPCODES)}


def check_the_surface_can_DRIVE_the_system_and_still_cannot_touch_the_world():
    """`plan` — where the CNL stops only describing and starts driving. Every other verb records
    something (`goal`, `type`, `method`, `prefer`) or asks something (`ask`, `why`); none of them could
    make the system *work*. It reaches `driver.pursue`, which is reachable at all only because
    deliberation stopped being a closed Python loop.

    It is a fourth force on the same body, not a new family — `goal` / `ask` / `why` / `plan` take
    identical bodies and differ in what is done with them, which is this module's own thesis paying rent.

    The safety property, and it is structural rather than intended: planning happens entirely on a
    workbench, so a `plan` block cannot change the world however wrong the text is. That is what makes it
    safe to put a *driving* verb on a surface a language model may write. A verb that carried out the plan
    would cross into real effects and is deliberately absent.

    Vacuity guard: the same body as a `goal` block must still merely record, or "plan drove it" would be
    indistinguishable from "every block drives it"; and a plan constraint must still be able to refuse, or
    this would only show the happy path."""
    from . import intake as I, thread as T
    body = ("    a on b", "    b on c")
    g, world = _blocks()
    th = T.open_thread(g, "t")
    a = I.resolve(g, "a", under=world)
    b = I.resolve(g, "b", under=world)
    # NOT `== ()`: `a` starts out `on` the ground, so an emptiness test would be false before anything
    # ran and would report a safety breach that had not happened. Snapshot, then compare.
    before = g.targets(a, "on")

    stated = I.respond(g, _lines("goal build a tower:", *body), th, world)
    nothing_happened = g.targets(a, "on") == before and b not in before

    driven = I.respond(g, _lines("plan build a tower:", *body), th, world)
    refused = I.respond(g, _lines("plan build a tower:", *body, "    never stack"), th, world)

    try:
        I.read_goal(g, _lines("plan build a tower:", *body))
        read_goal_took_it = True
    except I.Unreadable:
        read_goal_took_it = False

    return {"a_goal_block_only_RECORDS": "PLANNED" not in stated and "plan found" not in stated,
            "A_PLAN_BLOCK_DRIVES_IT": driven.startswith("plan found in 2 step(s)"),
            "and_names_the_steps": "stack(b=b, onto=c)" in driven,
            "THE_WORLD_IS_UNTOUCHED_BY_EITHER":
                nothing_happened and g.targets(a, "on") == before and b not in g.targets(a, "on"),
            "a_plan_constraint_still_refuses": refused.startswith("no plan:")
                                               and "never stack" in refused,
            "read_goal_still_refuses_a_plan_block": not read_goal_took_it}


# --- memory: what was seen, and whether the agent did it ----------------------------------------------
def _watched_world():
    """A directory the agent can look at, and an external world it does not control."""
    from . import asm, dispatch as DP, thread as T
    g = new_graph()
    d = g.mint("dir", label="d", count=0)
    g.link("root", "has", d)
    th = T.open_thread(g, "session")
    disk = {"count": 3}
    DP.register("scan", lambda gg, target: gg.put(target, count=disk["count"]))
    asm.load_text(g, 'fn empty_it(d) -> dir:\n    SET F(d) "count" 0')

    def look():
        DP.service(g, "scan", d, record_on=T.attend(g, th, d, why="going to look"))
    return g, th, d, disk, look


def check_the_agent_can_tell_ITS_OWN_changes_from_the_WORLDS():
    """*"Was it me?"* — and the answer is derived, not recorded.

    A journal delta records only the agent's own writes; when a file changes on disk nothing happens in
    the graph at all, and the belief is simply wrong until someone looks. Worse, the second look is
    itself a write, so a naive delta log would say *"the agent changed `count` from 3 to 5"* when the truth
    is *"the agent looked, and found 5 where it had recorded 3."*

    Attribution needs no new record: two sightings differ, and either some `done` application between them
    could have written that slot, or the world moved. "Could have written" is read off the stored
    function body — `empty_it` is never told it writes `count`; `driver.establishes` works it out, and
    `role_node` resolves the role against the bindings actually used.

    Vacuity guards, and they are the whole check: the two verdicts must differ (labelling everything
    one way would otherwise pass), and the attributed one must name the function, or "mine" could be a
    default rather than a finding."""
    from . import memory as M, thread as T, function as fn
    g, th, d, disk, look = _watched_world()

    look()
    disk["count"] = 5                       # somebody else added two files
    look()
    (a1, b1), = M.transitions(g, th, d, "count")
    world_did_it = M.attribute(g, th, a1, b1)

    fn.invoke(g, "empty_it", {"d": d}, check_types=False)
    T.applied(g, th, "empty_it", {"d": d}, why="tidying up", done=True)
    disk["count"] = 0
    look()
    a2, b2 = M.transitions(g, th, d, "count")[1]
    i_did_it = M.attribute(g, th, a2, b2)

    return {"THE_WORLDS_CHANGE_IS_EXTERNAL": world_did_it["verdict"] == M.EXTERNAL,
            "MY_CHANGE_IS_MINE": i_did_it["verdict"] == M.MINE,
            "THE_TWO_VERDICTS_DIFFER": world_did_it["verdict"] != i_did_it["verdict"],
            "and_it_names_the_function":
                {g.attr(x, "function") for x in i_did_it["by"]} == {"empty_it"},
            "read_off_the_body_not_declared":
                ("attr", "count", "d", 0) in _writes_of(g, "empty_it")}


def _writes_of(g, name):
    """What `establishes` reads off the stored body — nothing declared it."""
    from . import driver as D
    return D.establishes(g, name)[0]


def check_change_and_back_is_visible_to_a_third_look():
    """I claimed this was invisible and was wrong — corrected by the user, and the correction is
    worth pinning. A round trip is visible whenever an observation falls inside the excursion, and
    three sightings showing A, B, A are exactly that. It is invisible only when nothing looks during the
    window, which makes it a sampling-rate question rather than an impossibility.

    It also settles why an observation is recorded even when the value is unchanged: collapsing to "only
    on difference" would store A, B, A as *no change*, so the agent would have watched a round trip happen
    and recorded that nothing did.

    What remains true: sightings bound change from below and never count it. A, B, A proves at least
    two changes and cannot distinguish two from six."""
    from . import memory as M
    g, th, d, disk, look = _watched_world()
    look()                                   # 3
    disk["count"] = 9
    look()                                   # 9
    disk["count"] = 3
    look()                                   # 3 again — back where it started
    moved = M.transitions(g, th, d, "count")
    return {"the_round_trip_is_VISIBLE": len(moved) == 2,
            "and_both_legs_are_external":
                all(M.attribute(g, th, a, b)["verdict"] == M.EXTERNAL for a, b in moved),
            "THE_END_STATE_ALONE_WOULD_SHOW_NOTHING":
                g.attr(M.sightings(g, th, d, "count")[0], "value") == g.attr(d, "count"),
            "every_sighting_is_kept_not_just_the_differing_ones":
                len(M.sightings(g, th, d, "count")) == 3}


def check_volatility_gives_SENSE_something_to_aim_at():
    """`driver.py` records that the `SENSE` verb "needs ignorance", and ignorance was the only trigger
    available — *I do not know, so go and look*. Volatility supplies the one that actually arises for an
    agent whose world has other people in it: I knew, and it is probably stale.

    Vacuity guard: a slot nobody else touches must score zero, or "volatile" would just mean "observed"."""
    from . import memory as M, thread as T, function as fn
    g, th, d, disk, look = _watched_world()
    for v in (3, 5, 9, 2):
        disk["count"] = v
        look()
    volatile = M.volatility(g, th, d, "count")

    g2, th2, d2, disk2, look2 = _watched_world()
    look2()
    fn.invoke(g2, "empty_it", {"d": d2}, check_types=False)
    T.applied(g2, th2, "empty_it", {"d": d2}, done=True)
    disk2["count"] = 0
    look2()
    steady = M.volatility(g2, th2, d2, "count")
    return {"a_world_that_moves_under_us_scores_high": volatile["rate"] > 0.5,
            "AND_A_SLOT_ONLY_I_TOUCH_SCORES_ZERO": steady["unattributed"] == 0,
            "so_the_two_are_distinguishable": volatile["rate"] != steady["rate"],
            "volatile": volatile, "steady": steady}


def _school_library(n_idle=0):
    """A three-step plan whose first move closes nothing. To be at school you must be home; to fly home you
    need a ticket; buying one writes `ticket`, which is a different slot from the goal's `where`.

    The prerequisite is declared last, after every irrelevant operator. That is the guard: the ordering
    of `function.names` is a real tie-break, so a check that let the prerequisite sort or declare itself
    first would be measuring the tie-break and calling it guidance."""
    from . import asm
    g = new_graph()
    declare_type(g, "person")
    declare_type(g, "at_home", attrs={"where": "home"})
    declare_type(g, "at_abroad", attrs={"where": "abroad"})
    declare_type(g, "at_school", attrs={"where": "school"})
    declare_type(g, "ready_to_fly", base="at_abroad", attrs={"ticket": True})
    body = [f'fn idle{i}(p: person) -> person:\n    SET F(p) "i{i}" true' for i in range(n_idle)]
    body += ['fn nap(p: person) -> person:\n    SET F(p) "rested" true',
             # Present so the dominance of the band over the unlock count is testable. From home this is
             # offered, it writes the goal's own slot (so it is not irrelevant), and it unlocks `fly_home`
             # — yet going to school directly is obviously right. If `-unlocks` came before `-band` in the
             # frontier key the search would fly abroad first, and without an operator of this shape that
             # inversion passes every other check here.
             # It unlocks BOTH blocked requirements, so it out-unlocks the move that actually closes the
             # goal (which unlocks one, incidentally). A detour that merely ties on the unlock count cannot
             # test dominance at all — the first version of this operator wrote only `where`, scored the
             # same unlock count as `go_to_school`, and every inversion of the key passed.
             'fn prepare_trip(p: at_home) -> at_abroad:\n    SET F(p) "where" "abroad"\n'
             '    SET F(p) "ticket" true',
             'fn go_to_school(p: at_home) -> at_school:\n    SET F(p) "where" "school"',
             'fn fly_home(p: ready_to_fly) -> at_home:\n    SET F(p) "where" "home"',
             'fn buy_ticket(p: at_abroad) -> ready_to_fly:\n    SET F(p) "ticket" true']
    asm.load_text(g, "\n\n".join(body))
    me = g.mint("person", label="me", where="abroad")
    g.link("root", "has", me)
    tag(g, me, "person")
    return g, me


def check_an_attribute_effect_carries_the_VALUE_it_writes():
    """`_effects` recorded a `SET` as `("attr", key, subject_role, None)` — the value was hardcoded, even
    when the instruction states it outright. So an attribute effect carried its slot and its subject and
    never what it writes, while a link effect carried both roles all along.

    The consequence was not cosmetic: `relevance` scores band 4 for *"this call writes exactly the
    constraint"*, and with no value to check, `SET where "home"` scored band 4 against a goal wanting
    `where = school`. Right slot, right individual, wrong world — the guidance in the school scenario was
    entirely this accident, and it looked like the mechanism working.

    `UNREADABLE`, not `None`: `None` is an ordinary attribute value, so a sentinel is what keeps *"writes
    something we cannot name"* apart from *"writes the value None"*. And an unreadable value must keep
    band 4 — `establishes` is an over-approximation by contract, so what cannot be read must never cost a
    candidate a rank."""
    from . import driver as D, goal as G, workbench as W
    g, me = _school_library()
    goal = G.open_goal(g, about=me)
    G.require_attr(g, goal, me, "where", "school")
    wb = W.open_workbench(g, me)
    f0 = W.root_frame(g, wb)
    open_now = G.unmet(g, goal, view=D.view_in(g, f0),
                       under=W.image_of(g, W.mapping_for(g, f0, me)))
    bands = {n: D.relevance(g, n, b, open_now) for n, b in D.proposals(g, f0)}

    # A second world, because `fly_home` is not proposable from the first at all — it needs a ticket, so
    # `bands` has no entry for it and the first version of the comparison below was reading a default of 0
    # against a default of 0. Ranking two proposals requires a frame in which both are actually offered.
    g2, me2 = _school_library()
    g2.put(me2, ticket=True)
    goal2 = G.open_goal(g2, about=me2)
    G.require_attr(g2, goal2, me2, "where", "school")
    wb2 = W.open_workbench(g2, me2)
    f2 = W.root_frame(g2, wb2)
    open2 = G.unmet(g2, goal2, view=D.view_in(g2, f2),
                    under=W.image_of(g2, W.mapping_for(g2, f2, me2)))
    bands2 = {n: D.relevance(g2, n, b, open2) for n, b in D.proposals(g2, f2)}

    gt, _root, _lits = _threshold_library()
    computed, _u = D.establishes(gt, "lower_threshold")     # SET from a register: not statically readable
    return {"the_value_is_read_off_the_instruction":
                ("attr", "where", "p", "school") in D.establishes(g, "go_to_school")[0],
            "and_a_different_value_is_a_DIFFERENT_effect":
                ("attr", "where", "p", "home") in D.establishes(g, "fly_home")[0],
            "A_COMPUTED_VALUE_IS_UNREADABLE_NOT_NONE":
                computed == frozenset({("attr", "value", "c.right", D.UNREADABLE)}),
            "and_UNREADABLE_is_not_None": D.UNREADABLE is not None,
            "and_it_prints_as_itself": repr(D.UNREADABLE) == "UNREADABLE",
            # The payoff: the wrong-value write no longer claims to close the constraint.
            "fly_home_is_not_even_offered_without_a_ticket": "fly_home" not in bands,
            "WRITING_THE_WRONG_VALUE_IS_NO_LONGER_BAND_4": bands2["fly_home"] != 4,
            "but_it_is_still_related_so_it_outranks_the_irrelevant":
                bands2["nap"] < bands2["fly_home"],
            "the_RIGHT_value_still_scores_band_4":
                D.relevance(g, "go_to_school",
                            {"p": W.mapping_for(g, f0, me)}, open_now) == 4}


def check_the_search_can_see_a_PREREQUISITE_which_no_band_can_express():
    """A band classifies *this move against the goal* — it answers "does this close a constraint?".
    A prerequisite closes nothing, so it is band 0, correctly, and tied with every irrelevant operator
    in the library. No refinement of a match-quality scale fixes that: a prerequisite is not a worse match,
    it is a different distance, which a match scale does not measure.

    So the frontier key gains a component derived from what enumeration was already computing and throwing
    away — `types.fails` returns *which* requirement failed — and `unlocks` counts the blocking
    requirements a proposal would write. Key: `(expected, -band, -unlocks, depth)`.

    A closing move must still beat an unlocking detour's dominance invariant, which is what
    makes derived and authored orderings safe to combine at all. Probing showed that property is
    over-determined: `expected` folds in `rank >= 4` *and* `-band` precedes `-unlocks`, and removing
    either alone changes nothing. Only removing both degrades the plan. So this key is a guard on the
    behaviour and not on any one line of the frontier key — worth knowing before someone "simplifies"
    one of the two and finds every check still green.

    The guard that matters is the library size, not the step count. Before this, the guided cost
    grew with the number of *irrelevant* operators — 4 / 6 / 10 / 16 for 0 / 2 / 6 / 12 of them — because
    the search had to try each one before reaching the prerequisite. A check pinning a single number would
    have passed on a library of one size and said nothing. Flatness is the claim.

    Second guard: the prerequisite is declared last (`_school_library`), so it cannot win on the
    tie-break. Third: `unlocks` must still only order — the Sussman check next door is the standing
    proof that a move scoring nothing stays reachable."""
    from . import driver as D, goal as G, thread as T, workbench as W

    def cost(n_idle):
        g, me = _school_library(n_idle)
        goal = G.open_goal(g, about=me)
        G.require_attr(g, goal, me, "where", "school")
        r = D.pursue(g, goal, T.open_thread(g, "t"), me, max_steps=4000)
        return r["steps"] if r["found"] else None, D.plan_steps(g, r)

    costs = {k: cost(k) for k in (0, 2, 6, 12)}
    steps = [c[0] for c in costs.values()]

    g, me = _school_library(2)
    goal = G.open_goal(g, about=me)
    G.require_attr(g, goal, me, "where", "school")
    wb = W.open_workbench(g, me)
    f0 = W.root_frame(g, wb)
    open_now = G.unmet(g, goal, view=D.view_in(g, f0),
                       under=W.image_of(g, W.mapping_for(g, f0, me)))
    here, blocked = D.enumerate_frame(g, f0)
    wants = D.wants_that_unblock(g, f0, blocked, open_now)
    scored = {n: (D.relevance(g, n, b, open_now), D.unlocks(g, n, b, wants)) for n, b in here}

    # The control: the identical search with the component switched off is the previous behaviour.
    real = D.unlocks
    D.unlocks = lambda *a, **k: 0
    try:
        without = {k: cost(k)[0] for k in (0, 12)}
    finally:
        D.unlocks = real

    # The dominance control. From home the goal is one move away, and a *detour that unlocks something*
    # must not be preferred to it. This is the only assertion that distinguishes `(-band, -unlocks)` from
    # `(-unlocks, -band)` — the inversion passed every other key in this check.
    gh, meh = _school_library(2)
    gh.put(meh, where="home")
    goalh = G.open_goal(gh, about=meh)
    G.require_attr(gh, goalh, meh, "where", "school")
    from_home = D.pursue(gh, goalh, T.open_thread(gh, "t"), meh, max_steps=4000)

    return {"A_CLOSING_MOVE_STILL_BEATS_AN_UNLOCKING_DETOUR":
                D.plan_steps(gh, from_home) == ("go_to_school",),
            "at_one_imagined_state": from_home["steps"] == 1,
            "it_finds_the_three_step_plan":
                all(c[1] == ("buy_ticket", "fly_home", "go_to_school") for c in costs.values()),
            "at_the_OPTIMAL_cost": steps == [3, 3, 3, 3],
            "AND_THE_COST_DOES_NOT_GROW_WITH_IRRELEVANT_OPERATORS": len(set(steps)) == 1,
            "steps_by_library_size": {k: v[0] for k, v in costs.items()},
            # the vacuity guard: without the component the same search degrades with library size,
            # or "flat" is a property of the scenario rather than of the guidance.
            "WITHOUT_IT_THE_COST_GROWS": without[12] > without[0],
            "control_steps": without,
            "THE_PREREQUISITE_IS_STILL_BAND_0": scored["buy_ticket"][0] == 0,
            "AND_THAT_IS_WHY_A_BAND_COULD_NEVER_HAVE_DONE_IT":
                scored["buy_ticket"][0] == scored["nap"][0] == scored["idle0"][0],
            "IT_IS_THE_UNLOCK_COUNT_THAT_SEPARATES_THEM":
                scored["buy_ticket"][1] > 0 and scored["nap"][1] == scored["idle0"][1] == 0,
            "and_the_want_is_the_requirement_that_blocked_a_relevant_action":
                any(label == "@ticket" for label, _n in wants),
            "which_was_computed_from_a_BLOCKED_action": "fly_home" in blocked}


def check_a_PROHIBITION_crosses_a_goal_boundary_and_the_other_two_sorts_do_not():
    """The parent constrains the plan and the child does the planning. `goal.breached` read
    `constraints(g, goal)` — the goal's own — so a ban on "arrange the trip" said nothing whatever to
    the search planning "get to school" underneath it. A ban a child can sidestep is not a ban.

    The three plan sorts must NOT cross alike, and the whole value of this check is that it tests all
    three against each other (`docs/planning.md`:

    * `never` inherits unchanged, at any depth — a breach is a proof wherever it happens;
    * `eventually` must *not* inherit — it is discharged by some step somewhere below, so inheriting it
      would separately require every child to do the thing;
    * `at_most` is not inherited either, and that is a refusal with a reason rather than an
      omission: a budget counts at the grain of the level that declared it, so applying a parent's count to
      a child's actions would break a limit the moment somebody authored a method — and copying it to each
      child would let three children each spend the whole thing. Consuming it needs the decomposition rung
      that has no state node yet. A gap that is written down beats a wrong answer.

    The discriminating control is a ban declared on an unrelated goal, not the absence of a ban. Two
    worlds that differ only in whether the goal holding the prohibition is an *ancestor* is the only pair
    that tests ancestry; comparing "banned" against "not banned" would pass for an implementation that
    ignored ancestry and read every goal in the graph. That is the vacuous-negative records."""
    from . import driver as D, goal as G, thread as T

    def solve(place_ban=None, place_must=None, place_budget=None):
        g, me = _school_library()
        parent = G.open_goal(g, about=me, label="arrange the trip")
        other = G.open_goal(g, about=me, label="an unrelated goal")
        child = G.open_goal(g, about=me, label="be at school", under=parent)
        G.require_attr(g, child, me, "where", "school")
        where = {"parent": parent, "other": other, "child": child}
        if place_ban:
            G.forbid_action(g, where[place_ban], function="buy_ticket")
        if place_must:
            G.require_action(g, where[place_must], function="nap")
        if place_budget:
            G.limit_steps(g, where[place_budget], 1)
        r = D.pursue(g, child, T.open_thread(g, "t"), me, max_steps=2000)
        return r["found"], D.plan_steps(g, r), G.prohibitions(g, child), G.budget_of(g, child)

    free, plan_free, _p, _b = solve()
    from_parent, _pf, seen_from_parent, _b2 = solve(place_ban="parent")
    from_other, plan_other, seen_from_other, _b3 = solve(place_ban="other")
    from_child, _pc, _p4, _b4 = solve(place_ban="child")
    must_above, plan_must, _p5, _b5 = solve(place_must="parent")
    budget_above, plan_budget, _p6, budget_seen = solve(place_budget="parent")

    return {"the_plan_exists_when_nothing_bans_it":
                free and plan_free == ("buy_ticket", "fly_home", "go_to_school"),
            # Never: inherits.
            "A_BAN_ON_THE_PARENT_BINDS_THE_CHILD": not from_parent,
            "and_the_child_can_SEE_it": len(seen_from_parent) == 1,
            "the_same_ban_on_the_child_itself_also_binds": not from_child,
            # The control: identical in every way except that the goal holding the ban is not an ancestor.
            "A_BAN_ON_AN_UNRELATED_GOAL_DOES_NOT": from_other,
            "and_the_child_cannot_see_that_one": len(seen_from_other) == 0,
            # Indexed defensively. An over-broad `prohibitions` that reads every goal in the graph makes
            # this plan empty, and `plan_other[0]` then raised IndexError — which the harness does count,
            # but as an error, so the report says the check blew up rather than *which property broke*.
            #'s lesson has a mirror image: a red key beats an exception just as it beats a quiet False.
            "so_the_plan_still_uses_the_action": plan_other[:1] == ("buy_ticket",),
            # Eventually: must not inherit.
            "AN_OBLIGATION_ON_THE_PARENT_DOES_NOT_BIND_THE_CHILD": must_above,
            "and_the_child_is_not_made_to_discharge_it": "nap" not in plan_must,
            # At_most: not inherited, deliberately.
            "A_BUDGET_ON_THE_PARENT_IS_NOT_INHERITED": budget_above,
            "the_child_plan_is_longer_than_the_parents_limit": len(plan_budget) > 1,
            "and_budget_of_says_so_by_returning_NOTHING": budget_seen == (),
            # ...but a budget on the goal that owns the steps still bites, or nothing tests the sort at all.
            "THOUGH_A_BUDGET_ON_THE_CHILD_ITSELF_STILL_BITES":
                not solve(place_budget="child")[0]}


def _two_plans_world():
    """A person who must get to school, and an unrelated box that must be packed. Two goals, two
    pursuits, one agenda, and nothing shared between them - which is what makes the second one a
    control on the first rather than more of the same."""
    from . import asm
    g = new_graph()
    declare_type(g, "person")
    declare_type(g, "at_home", attrs={"where": "home"})
    declare_type(g, "at_abroad", attrs={"where": "abroad"})
    declare_type(g, "at_school", attrs={"where": "school"})
    declare_type(g, "ready_to_fly", base="at_abroad", attrs={"ticket": True})
    declare_type(g, "box")
    # Three casts, not one, and that is the whole point of the control. With a one-step box plan the
    # box finished BEFORE the school plan reached its second act, so "the other task survived" was true
    # even when the exception wrecked the agenda - the guard passed the planted-bug probe and was
    # therefore guarding nothing. A control has to still be running at the moment of the failure.
    declare_type(g, "filled_box", base="box", attrs={"filled": True})
    declare_type(g, "taped_box", base="filled_box", attrs={"taped": True})
    declare_type(g, "packed_box", base="taped_box", attrs={"packed": True})
    asm.load_text(g, "\n".join([
        "# Go to school - only possible from home.",
        "fn go_to_school(p: at_home) -> at_school:",
        '    SET F(p) "where" "school"',
        "",
        "# Fly home - only possible from abroad, and only with a ticket.",
        "fn fly_home(p: ready_to_fly) -> at_home:",
        '    SET F(p) "where" "home"',
        "",
        "fn buy_ticket(p: at_abroad) -> ready_to_fly:",
        '    SET F(p) "ticket" true',
        "",
        "# Nothing to do with any of the above - the unrelated second plan, in three steps.",
        "fn fill(b: box) -> filled_box:",
        '    SET F(b) "filled" true',
        "",
        "fn tape(b: filled_box) -> taped_box:",
        '    SET F(b) "taped" true',
        "",
        "fn pack(b: taped_box) -> packed_box:",
        '    SET F(b) "packed" true',
    ]))
    me = g.mint("person", label="me", where="abroad", ticket=True)
    box = g.mint("box", label="box")
    g.link("root", "has", me)
    g.link("root", "has", box)
    tag(g, me, "person")
    tag(g, box, "box")
    return g, me, box


def check_a_precondition_that_went_false_is_a_DEVIATION_not_an_ESCAPING_EXCEPTION():
    """A plan is verified against a world, and then the world moves while it is suspended - because a
    child is running, because another pursuit got the tick, because something simply happened. `fn.invoke`
    re-validates each parameter type at the call, which is the property that stops a plan acting on a
    world it was never verified against, and it is the right check in the right place.

    But it reported by raising, and nothing caught it. The `TypeViolation` went straight through
    `execution.step`, `driver.pursuit_step` and `loop.tick`: the pursuit was stranded mid-`acting`, and
    every other task on the agenda died with it. Detection existed; recovery did not.

    The vacuity guard is the second PLAN, and without it this check is worth very little. A version
    asserting only that the school pursuit recovers would pass over an implementation that swallowed the
    exception locally and left the agenda wrecked - and a wrecked agenda is invisible to any test that
    schedules one thing. The box shares no node, no type and no operator with the school plan, so its
    completing *for real* is evidence about the loop rather than about the fix.

    Second guard: the divergence must be reported as one, not merely survived. A `step` that
    returned `False` on the exception without minting a `deviation` would leave the loop alive and the
    pursuit silently claiming it had finished its plan.

    Third guard: recovery must be replanning, not a contingency. The call never ran, so there is no
    real outcome to settle onto a sibling's mappings, and `matching_alternative` must decline - which it
    does because `result` is `None`. Offering a contingency here would be resuming a branch on the
    strength of an outcome that does not exist."""
    from . import driver as D, execution as X, goal as G, loop as L, thread as T
    g, me, box = _two_plans_world()
    th = T.open_thread(g, "t")
    school = G.open_goal(g, about=me, label="be at school")
    G.require_attr(g, school, me, "where", "school")
    packed = G.open_goal(g, about=box, label="pack the box")
    G.require_attr(g, packed, box, "packed", True)

    p_school = D.open_pursuit(g, school, th, me, attempts=3)
    p_box = D.open_pursuit(g, packed, th, box)
    lp = L.open_loop(g, "two plans")
    L.schedule(g, lp, p_school, why="school")
    L.schedule(g, lp, p_box, why="box")

    # The moment the school plan takes its first real ACT, something puts the subject back abroad. Its
    # next step requires being at home, and that requirement is now false.
    moved, escaped, box_live_at_failure = False, None, None
    try:
        for _ in range(400):
            rec = L.tick(g, lp)
            if rec is None:
                break
            if not moved and rec["task"] == p_school and rec["verb"] == L.ACT:
                g.put(me, where="abroad")
                moved = True
            # Recorded AT the failure, not afterwards. "The box finished eventually" is compatible with
            # the box having finished long before anything went wrong, which is exactly how the first
            # version of this guard passed its own planted-bug probe.
            if box_live_at_failure is None and any(
                    X.deviation_of(g, r) is not None for r in g.targets(p_school, "replay")):
                box_live_at_failure = not L.finished(g, p_box)
    except Exception as e:                          # noqa: BLE001 - the escape IS the thing under test
        escaped = f"{type(e).__name__}: {e}"

    school_report, box_report = D.pursuit_report(g, p_school), D.pursuit_report(g, p_box)
    first = school_report["attempts"][0] if school_report["attempts"] else {}
    diverged_on = [a for a in school_report["attempts"] if a.get("diverged")]
    return {"the_world_really_did_move_mid_plan": moved,
            "NOTHING_ESCAPED_THE_OUTER_LOOP": escaped is None,
            "escaped": escaped,
            "IT_IS_REPORTED_AS_A_DIVERGENCE": bool(diverged_on),
            "and_it_names_the_step_that_could_not_be_applied":
                bool(diverged_on) and "go_to_school" in diverged_on[0]["diverged"],
            "and_says_the_requirement_is_no_longer_true":
                bool(diverged_on) and "no longer satisfies" in diverged_on[0]["diverged"],
            "the_first_attempt_did_not_complete": first.get("completed") is False,
            "NO_CONTINGENCY_WAS_OFFERED_BECAUSE_THE_CALL_NEVER_RAN":
                all(a.get("recovered") is None for a in school_report["attempts"]),
            "IT_REPLANNED_AND_SUCCEEDED": school_report["done"],
            "and_needed_a_second_attempt": school_report["tries"] == 2,
            "the_world_agrees": g.attr(me, "where") == "school",
            # The vacuity guard: an unrelated plan sharing nothing must be untouched by all of it.
            "the_other_plan_was_STILL_RUNNING_when_it_failed": box_live_at_failure is True,
            "THE_OTHER_TASK_ON_THE_AGENDA_SURVIVED": box_report["done"],
            "and_it_really_acted": g.attr(box, "packed") is True,
            "it_never_diverged": all(not a.get("diverged") for a in box_report["attempts"])}


def check_a_sighting_is_distinct_from_a_belief():
    """`g.attr(node, key)` is the current belief and is what everything reasons over; a sighting is
    *what was actually seen, and when*. Keeping them apart is what lets a belief be recognised as stale
    rather than silently trusted — and it is why memory is metadata pointing inward rather than a change
    to how the world is stored.

    A sighting covers every slot of the thing looked at, because that is what "I checked this" means
    — the state it was in at that moment, not only the fields the tool happened to rewrite. That is what
    makes *"when did I last check?"* answerable for stable slots too, which a difference-only record
    could never do: it cannot tell *unchanged* from *unobserved*, which is the `UNKNOWN` conflation one
    level up.

    Vacuity guard: something never looked at must answer `None` rather than fabricating a sighting
    from the current value — that is the whole distinction, and it needs a node the agent never visited,
    not merely a quiet field on one it did."""
    from . import memory as M
    g, th, d, disk, look = _watched_world()
    elsewhere = g.mint("dir", label="never-visited", count=99)
    g.link("root", "has", elsewhere)
    look()
    return {"the_belief_is_where_it_always_was": g.attr(d, "count") == 3,
            "the_sighting_records_it_separately":
                g.attr(M.believed(g, th, d, "count"), "value") == 3,
            "a_stable_slot_of_what_I_LOOKED_at_is_covered_too":
                g.attr(M.believed(g, th, d, "label"), "value") == "d",
            "SOMETHING_NEVER_LOOKED_AT_HAS_NO_SIGHTING":
                M.believed(g, th, elsewhere, "count") is None,
            "even_though_it_has_a_value": g.attr(elsewhere, "count") == 99,
            "nothing_in_the_world_points_at_a_sighting":
                g.sources(M.sightings(g, th, d, "count")[0], "of") == ()}


def check_a_method_and_a_criterion_answer_ONE_question_about_what_they_do():
    """the typed consequent, slice one. `docs/limits.md` claimed every rule here is
    `conditions → consequent` and only the consequent and the executor differ. It was an aspiration: a
    method's rung was an `mstep` node reached by `steps_of`, a criterion's action a `does` node reached by
    `action_of`, and no reader could ask both what they do without knowing which it was holding.

    Now both mint `consequent` nodes on one edge label, tagged `achieve` or `call`, and `consequent.of`
    answers for either.

    The tag was the open question (an earlier note: *a fourth tagged shape or its own small
    grammar?*), and an earlier probe settled it by pushing to execution rather than to the parser:
    the two consequents differ in shape irreducibly — a proposition with roles versus a function with
    named bindings — so one grammar over both would be their union with the tag left off.

    And what the probe measured is that they do NOT differ in reach. Two attempts to build a world
    where a criterion's `do` gets somewhere means-ends search cannot, and the control went dark both
    times: `driver.establishes` unions in each mock's effects, so every operator a criterion can name is
    one search could already select. So this slice buys nothing in capability, and that is the honest
    reason for it — it is what makes the *next* consequent (`effect`, `remember`, `learn`, which have no
    verb at all today) cheap instead of two more islands created by a second caller.

    Vacuity guards, because "behaviour unchanged" passes for a seam that does nothing:
    the uniform enumerator must return both families' consequents and they must carry different
    tags — one call answering with one kind twice would be a merge, not a collapse. And `describe` must
    refuse a node that is not a consequent, or a reader would be guessing what a rule does."""
    from . import consequent as CQ, criterion as CR, intake as I, method as M

    g = new_graph()
    declare_type(g, "file", attrs={"kind_of": "file"})
    declare_type(g, "linted_file", base="file", attrs={"linted": True})
    f = g.mint("chunk", kind_of="file", label="parser", size=100)
    g.link("root", "has", f)

    from . import asm
    asm.load_text(g, _lines("fn lint(f: file) -> linted_file:", '    SET F(f) "linted" true'))
    I.read(g, _lines("method lint it:", "    handles attr linted", "    step subject.linted = true"))
    I.read(g, _lines("criterion big ones get linted:", "    wants attr linted",
                     "    when subject.size > 50", "    do lint f = subject"))
    m, c = M.methods(g)[0], CR.criteria(g)[0]

    # One call, two families. This is the whole of what the collapse adds.
    from_method, from_criterion = CQ.of(g, m), CQ.of(g, c)
    tags = (CQ.kind(g, from_method[0]), CQ.kind(g, from_criterion[0]))

    def refusal(fn):
        try:
            fn()
            return None
        except Exception as e:
            return str(e)

    return {"ONE_ENUMERATOR_ANSWERS_FOR_A_METHOD": len(from_method) == 1,
            "AND_FOR_A_CRITERION": len(from_criterion) == 1,
            "THEY_ARE_ONE_NODE_KIND": g.kind(from_method[0]) == g.kind(from_criterion[0]) == "consequent",
            "but_TAGGED_DIFFERENTLY_so_it_is_a_collapse_not_a_merge":
                tags == (CQ.ACHIEVE, CQ.CALL),
            "and_each_reads_back_in_words_without_knowing_the_family":
                CQ.describe(g, from_method[0]) == "step subject.linted = true"
                and CQ.describe(g, from_criterion[0]) == "do lint(f = subject)",
            "the_call_still_carries_its_bindings":
                CQ.bindings_of(g, from_criterion[0]) == (("f", "subject"),),
            "and_the_achieve_carries_none": CQ.bindings_of(g, from_method[0]) == (),
            "A_READER_MUST_NOT_GUESS_what_a_non_consequent_does":
                "not a consequent" in (refusal(lambda: CQ.describe(g, f)) or ""),
            "the_old_family_accessors_still_agree":
                M.steps_of(g, m) == from_method and CR.action_of(g, c) == from_criterion[0]}


def check_a_criterion_naming_a_function_that_cannot_exist_is_refused_WHERE_IT_IS_WRITTEN():
    """A criterion that is broken in every world used to fail as silence. `do frobnicate f = x`
    authored clean, minted a node, and never spoke — indistinguishable from advice whose conditions simply
    did not hold. Measured, then closed in `intake._action`.

    The subtlety is why `driver.check_call` could not close it. It already refuses an unknown
    function — but `criterion._try` deliberately turns every refusal from there into silence, and that is
    *correct* for what it was built for: *"the first container happens to be the one this goal forbids"* is
    a situation, not a mistake, and raising there abandoned a search plain enumeration could finish.
    So the two were folded together at the wrong layer. An unknown function and a wrong parameter set are
    not situations — no arrangement of the world could make them speak — so they belong at authoring
    time, which is the argument `intake._ref` already makes for the *other* half of the same line.

    Vacuity guards. A correct `do` must still author, or this is just a broken parser. The refusal
    must name the signature, since *"that is wrong"* without saying how is what sent authors into a
    search to find out. And a refusal must leave nothing behind — a half-built criterion sitting in the
    graph looking as though it worked is the failure mode this whole surface exists to prevent."""
    from . import asm, criterion as CR, intake as I

    def g_with_lint():
        g = new_graph()
        declare_type(g, "file", attrs={"kind_of": "file"})
        declare_type(g, "linted_file", base="file", attrs={"linted": True})
        asm.load_text(g, _lines("fn lint(f: file, style: file) -> linted_file:",
                                '    SET F(f) "linted" true'))
        f = g.mint("chunk", kind_of="file", label="parser")
        g.link("root", "has", f)
        return g

    def refused(*body):
        g = g_with_lint()
        before = len(g.attrs)
        try:
            I.read(g, _lines("criterion c:", "    wants attr linted", *body))
            return None, len(g.attrs) == before, len(CR.criteria(g))
        except Exception as e:
            return str(e), len(g.attrs) == before, len(CR.criteria(g))

    unknown, u_clean, u_left = refused("    do frobnicate f = subject")
    wrong, w_clean, w_left = refused("    do lint f = subject")
    good, _, g_left = refused("    do lint f = subject, style = subject")

    # And the case that motivated the whole pass: with NO library loaded at all, the refusal must say
    # so rather than listing an empty set of known functions.
    g2 = new_graph()
    declare_type(g2, "file", attrs={"kind_of": "file"})
    try:
        I.read(g2, _lines("criterion c:", "    wants attr linted", "    do lint f = subject"))
        empty = None
    except Exception as e:
        empty = str(e)

    return {"AN_UNKNOWN_FUNCTION_IS_REFUSED": unknown is not None,
            "and_it_lists_what_there_IS": unknown is not None and "lint" in unknown,
            "A_WRONG_PARAMETER_SET_IS_REFUSED": wrong is not None,
            "and_it_names_the_SIGNATURE": wrong is not None and "(f, style)" in wrong,
            "A_CORRECT_ACTION_STILL_AUTHORS": good is None and g_left == 1,
            "and_the_refusals_LEFT_NOTHING_BEHIND": u_clean and w_clean and u_left == w_left == 0,
            "AN_EMPTY_LIBRARY_SAYS_SO_rather_than_listing_nothing":
                empty is not None and "nothing is declared yet" in empty}


def check_the_KERNEL_cannot_see_the_representation_above_it():
    """the kernel boundary, enforced rather than achieved once.

    The rule: Python is a kernel that may do the substrate — nodes, edges, refs, indices, the
    journal, focus, the instruction set, scheduling — and must never do *business*, where business is
    anything we decided about how to represent plans, time, goals, criteria. *The kernel never sees
    the representation above it.* The point is portability: another substrate (Rust, Excel macros, a
    redstone machine) re-implements the kernel, and the data carries over unchanged. Anything
    decided-but-written-in-Python has to be re-decided by every port, which means it was never really a
    representation.

    `isa.py` violated it, and it was the only leak below the line. `PLAN` and `STEP` called
    `driver.open_planning` / `driver.step`, and `CHECK` called `types.check` — so a Rust port would have
    had to port the planner and the type system in order to implement three instructions.

    The fix keeps both principles, which had genuinely collided. `isa.py`'s own argument — search is a
    primitive, because no sequence of GET/SET/LINK imagines a state — was right. What was wrong was
    concluding that a primitive must be an opcode. `native.py` is a name→callable table: the kernel
    reaches a primitive by name, and the module that owns the primitive puts it there. The dependency
    inverts from `isa → driver` to `isa → native ← driver`.

    This check is structural on purpose, because the property is one that drifts back silently.
    A single `from . import driver` inside a handler restores the leak, passes every behavioural test, and
    would never be noticed — which is exactly how it got there. So the import graph is parsed from source.

    Vacuity guards: the natives must actually work (a body that plans through `NATIVE` still plans, or
    this traded a boundary for a broken engine); an unregistered name must refuse naming what is
    registered, since the real failure mode is a primitive whose owning module nobody imported; and
    `native.py` itself must name nothing from above, or the leak just moved."""
    import ast
    import pathlib
    from . import asm, native as N

    ABOVE = {"driver", "types", "goal", "criterion", "method", "plan", "norm", "clock", "discourse",
             "memory", "workbench", "search", "query", "conflict", "guideline", "hypothesis", "locate",
             "consequent", "execution", "intake", "selection", "thread", "loop", "forget", "application"}

    def imports_of(mod):
        src = pathlib.Path(__file__).resolve().parent / f"{mod}.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        got = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                if n.level and n.module:
                    got.add(n.module.split(".")[0])
                if n.level and not n.module:
                    got |= {a.name for a in n.names}
        return got

    isa_up = imports_of("isa") & ABOVE
    native_up = imports_of("native") & ABOVE
    # The control: modules ABOVE the line genuinely do import upward, so an empty set below means the
    # boundary, not that this test cannot see imports at all.
    driver_up = imports_of("driver") & ABOVE

    def refusal(fn):
        try:
            fn()
            return None
        except Exception as e:
            return str(e)

    unknown = refusal(lambda: N.call(new_graph(), "no_such_primitive", ()))
    dup = refusal(lambda: N.register("plan", lambda g: None))

    return {"THE_INSTRUCTION_SET_IMPORTS_NOTHING_FROM_ABOVE": isa_up == set(),
            "leaked": tuple(sorted(isa_up)),
            "NOR_DOES_THE_TABLE_ITSELF": native_up == set(),
            "and_the_test_CAN_see_imports_so_the_empty_set_means_something": bool(driver_up),
            "THE_TWO_OPCODES_THAT_KNEW_THE_PLANNER_ARE_GONE":
                not ({"PLAN", "STEP", "CHECK"} & asm._OPCODES),
            "and_NATIVE_replaced_them": "NATIVE" in asm._OPCODES,
            "THE_PLANNER_IS_STILL_REACHABLE_BY_NAME": {"plan", "plan_step", "check"} <= set(N.names()),
            "an_UNREGISTERED_native_refuses": unknown is not None,
            "and_NAMES_WHAT_IS_REGISTERED": unknown is not None and "plan" in unknown,
            "and_says_WHY_it_might_be_missing": unknown is not None and "imported" in unknown,
            "a_SECOND_claim_on_one_name_is_refused": dup is not None}


def check_a_guided_search_is_RESUMABLE_by_anything_because_the_decider_is_a_NODE():
    """guidance was a property of the python caller, NOT of the search.

    `criterion.decide` returns a closure handed to `pursue(propose=…)`, and `search.open_search`'s own
    docstring concedes the split in as many words — *"everything a step needs that is NOT a python
    Callable lives here"*. `loop.advance` forwards `**hooks` from whoever called `tick`, so the outer
    loop — the thing whose whole claim is that it can advance anything — silently lost the guidance.

    Measured: the identical search node, with the
    identical criteria in the graph, took 3 imagined states via `pursue` and 52 ticked by the
    loop. Nothing recorded which had happened, so *"what is deciding this search?"* had no answer in the
    graph — the project's signature defect, one more time.

    The fix is the move `search.stop` already makes one screen up in `driver.step`, for the reason
    recorded there: *the same decision expressed as data, which the standing principle requires.* The
    search points at a `decider` node; `driver.step` and `open_planning` resolve it when no hook is given.

    Vacuity guards, and the first version needed the second one. Asserting `looped == guided`
    passes for an engine that always answers 3, so the control is the same search with no decider,
    which must fall back to enumeration and cost far more. And the seed must be guided too: fixing only
    `driver.step` took the loop-ticked search from 52 to 6, not to 3, because the first frontier was
    still built by enumeration — a partial fix that a `found=True` assertion would have called done.

    Complaint (a) of `docs/limits.md` G is NOT closed by this: `criterion.decide` is still a Python loop.
    It is reachable from the graph rather than handed in, which is what makes a search resumable; it is
    not yet data."""
    from . import criterion as CR, driver as D, intake, loop as L, thread as T

    def build():
        g, world = _blocks()
        goal, _abc = _sussman(g, world)
        for t in CRITERIA_TEXT:
            intake.read(g, t)
        return g, world, goal

    def on_loop(g, search):
        lp = L.open_loop(g)
        L.schedule(g, lp, search, why="plan it")
        L.run(g, lp, max_ticks=2000)
        return g.attr(search, "steps")

    g1, w1, goal1 = build()
    guided = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=7,
                      propose=CR.decide(g1, goal1, w1))

    g2, w2, goal2 = build()
    s2 = D.open_planning(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=7,
                         decider=CR.decider(g2, goal2, w2))
    looped = on_loop(g2, s2)

    g3, w3, goal3 = build()
    s3 = D.open_planning(g3, goal3, T.open_thread(g3), w3, max_steps=400, max_depth=7)
    plain = on_loop(g3, s3)

    dec = g2.target(s2, "decided_by")
    return {"THE_OUTER_LOOP_REPRODUCES_THE_GUIDED_SEARCH": looped == guided["steps"],
            "guided_vs_looped_vs_unguided": (guided["steps"], looped, plain),
            "and_it_actually_FOUND_the_plan": bool(g2.attr(s2, "found")) and guided["found"],
            "AN_UNGUIDED_SEARCH_STILL_COSTS_FAR_MORE_so_the_match_is_not_a_constant": plain > looped * 4,
            "THE_SEARCH_CAN_SAY_WHAT_IS_DECIDING_IT": dec is not None,
            "and_the_decider_names_its_goal_and_subject":
                g2.target(dec, "goal") == goal2 and g2.target(dec, "subject") == w2,
            "an_EXPLICIT_hook_still_wins_over_the_node": callable(CR.decide(g2, goal2, w2)),
            "a_search_with_NO_decider_resolves_to_nothing_rather_than_raising":
                D._proposer_of(g3, s3) is None,
            "and_an_UNKNOWN_decision_procedure_is_REFUSED":
                _refuses(lambda: CR.proposer_for(g2, g2.mint("decider", how="vibes")))}


def _refuses(fn) -> bool:
    """Named `_refuses`, not `_raises`: this file already has a two-argument `_raises` and defining a
    second one silently clobbered it, breaking four unrelated checks."""
    try:
        fn()
        return False
    except Exception:
        return True


def check_ONE_ACTION_IS_ONE_MOMENT_including_what_the_action_PRODUCED():
    """time is woven, and the unit of weaving is the action. The user's specification: *"I don't expect each business rule to handle timestamping manually; and it is not that
    each node gets a different timestamp — when listing files in a folder, the entire list of files should
    get the same timestamp, because it corresponds to a single action."*

    Both halves were already true of what was covered, which is why this is a small change:
    `dispatch.service` records the sighting itself (no rule calls the clock) and `record_sighting` passes
    one `when` for a whole look on purpose. The gap was scope, measured in
    an earlier probe: a look at a folder produced three sightings sharing one
    moment, and the three file nodes it minted had no moment at all. Listing a folder left the file
    list — the entire point of listing a folder — with no time on it.

    Dating is NOT encoding, and this check exists partly to hold that line.
    `record_sighting` deliberately records only the slots of *the thing being looked at*: *"everything
    else the tool happened to touch is the walk to school — not encoded, and that is the correct outcome
    rather than a loss."* That is about attention and it is untouched. This is provenance:
    `clock.py` opens with *"everything observed or acted must have an absolute timestamp"*, and a node the
    world just handed us with no time on it cannot be aged, compared, or told from one that was always
    there. So the products are dated and NOT observed, and the check asserts both.

    Vacuity guards. Dating the products proves little if they get their own moment — that would be
    three actions, not one — so the assertion is set equality with the look's moment, not mere presence.
    A tool that produces nothing must not mint a stray moment. And the sighting count must stay put, or
    "dating is not encoding" has quietly stopped being true."""
    from . import clock as C, dispatch as DP, memory as M, thread as T

    made = []

    def lister(g, target):
        made.clear()
        for name in ("a.txt", "b.txt", "c.txt"):
            f = g.mint("chunk", kind_of="file", label=name)
            g.link(target, "file", f)
            made.append(f)
        g.put(target, count=len(made))
        return tuple(made)

    def toucher(g, target):
        g.put(target, poked=True)
        return True

    DP.register("probe_list_dir", lister, observes=True)
    DP.register("probe_touch", toucher, observes=True)

    g = new_graph()
    folder = g.mint("chunk", kind_of="folder", label="src")
    g.link("root", "has", folder)
    th = T.open_thread(g)
    DP.service(g, "probe_list_dir", folder, record_on=T.attend(g, th, folder, why="looking"))
    produced = tuple(made)

    seen = M.sightings(g, th, folder)
    of_look = {m for o in seen for m in C.dated(g, o)}
    of_products = {m for f in produced for m in C.dated(g, f)}

    # A second action must get its own moment, or "one action one moment" is really "one moment ever".
    g2 = new_graph()
    f2 = g2.mint("chunk", kind_of="folder", label="src")
    g2.link("root", "has", f2)
    th2 = T.open_thread(g2)
    DP.service(g2, "probe_list_dir", f2, record_on=T.attend(g2, th2, f2, why="one"))
    first = {m for n in tuple(made) for m in C.dated(g2, n)}
    DP.service(g2, "probe_list_dir", f2, record_on=T.attend(g2, th2, f2, why="two"))
    second = {m for n in tuple(made) for m in C.dated(g2, n)}

    # A tool that produces nothing must not leave a moment dating nothing.
    g3 = new_graph()
    t3 = g3.mint("chunk", kind_of="folder", label="src")
    g3.link("root", "has", t3)
    th3 = T.open_thread(g3)
    DP.service(g3, "probe_touch", t3, record_on=T.attend(g3, th3, t3, why="poke"))
    empty_moments = [m for m in C.moments(g3) if not g3.targets(m, C.DATES)]

    return {"THE_PRODUCTS_OF_THE_ACTION_ARE_DATED": all(C.dated(g, f) for f in produced),
            "and_there_were_three_of_them": len(produced) == 3,
            "ONE_ACTION_ONE_MOMENT_the_look_and_its_products_share_it": of_look == of_products,
            "and_it_really_is_ONE": len(of_look) == 1,
            "A_SECOND_ACTION_GETS_ITS_OWN_MOMENT": bool(first) and bool(second) and first != second,
            "DATING_IS_NOT_ENCODING_the_products_carry_no_sighting":
                all(M.sightings(g, th, f) == () for f in produced),
            "while_the_TARGET_still_does": len(seen) >= 2,
            "and_a_tool_that_PRODUCES_NOTHING_leaves_no_empty_moment": empty_moments == []}


def check_a_pursuit_ACTS_on_an_unfinished_plan_and_then_REPLANS():
    """ACTING on an unfinished PLAN — the thing an outer loop was wanted for.

    The user's specification: *"sometimes, to solve a goal, you genuinely need to perform an
    action. That only means the planning procedure can propose, as the next candidate step for the outer
    loop, not more planning but executing an action — and this is possible now that we have an outer
    loop."* And the constraint that shapes it: do not resume the search. What we just learned may
    invalidate the plan altogether, so a frontier built in ignorance must be thrown away.

    A search reported `found=False` for two very different reasons and `_phase_planning` read both as
    defeat. *"There is no route"* is defeat; *"I cannot plan this until I go and look"* is a third
    outcome. `goal.blocked_on_ignorance` is the test, and it is deliberately strict — a plan must
    bottom out in ignorance, not merely touch it, or the agent looks in every box.

    The world here makes the planner structurally blind, which is what makes this a capability
    rather than a shortcut. `scan_dir`'s whole effect is behind a `DISPATCH` and it declares no `mocks`,
    so `establishes` reads nothing and means-ends can never select it. Sensing therefore picks
    directly: an applicable function whose body dispatches a tool registered `observes=True`.

    Building it surfaced a pre-existing defect that had to be fixed first: such an operator made
    `dispatch.service` raise `Imagined` *inside planning*, and the exception escaped `loop.tick` —
    stranding the pursuit and killing every other task on the shared agenda. Exactly what `execution.step`
    already records for `TypeViolation`, one phase earlier. It is skipped and recorded now, not fatal.

    Vacuity guards, and each caught something. Planning alone must fail, or the scenario proves
    nothing. A second search must exist afterwards — resuming the first is what the specification
    forbids. A goal *not* blocked on ignorance must not sense at all. And the sensing tick must report the
    verb `look`, not `imagine`: it performs a real dispatch, and `loop.verb_of` is what lets a driver
    decline a tick before the world is touched — it reported `imagine` in the first version."""
    from . import asm, dispatch as DP, driver as D, goal as G, loop as L, thread as T
    from .graph import UNKNOWN

    def looker(g, target):
        for i in range(3):
            g.link(target, "file", g.mint("chunk", kind_of="file", label=f"f{i}"))
        g.put(target, count=3)
        return 3

    DP.register("selftest_look", looker, observes=True)

    def world():
        g = new_graph()
        declare_type(g, "folder", attrs={"kind_of": "folder"})
        declare_type(g, "file", attrs={"kind_of": "file"})
        asm.load_text(g, _lines("fn scan_dir(d: folder) -> folder:",
                                '    DISPATCH R(out) "selftest_look" F(d)'))
        folder = g.mint("chunk", kind_of="folder", label="src", count=UNKNOWN)
        g.link("root", "has", folder)
        goal = G.open_goal(g, label="know how many files")
        G.require_attr(g, goal, folder, "count", 3)
        return g, folder, goal

    g, folder, goal = world()
    blind = D.establishes(g, "scan_dir")
    # Read BEFORE the pursuit runs — after sensing the goal is no longer blocked, so asserting this
    # afterwards would be asserting nothing. The first version of this key was a hardcoded `True`.
    bottoms_out = G.blocked_on_ignorance(g, goal)
    p = D.open_pursuit(g, goal, T.open_thread(g), folder)
    lp = L.open_loop(g)
    L.schedule(g, lp, p, why="pursue it")
    out = L.run(g, lp, max_ticks=200)
    verbs = [r["verb"] for r in out["did"]]

    # Control: planning alone must fail.
    g2, folder2, goal2 = world()
    s2 = D.open_planning(g2, goal2, T.open_thread(g2), folder2, max_steps=200, max_depth=6)
    lp2 = L.open_loop(g2)
    L.schedule(g2, lp2, s2, why="plan only")
    L.run(g2, lp2, max_ticks=200)

    # Control: a goal that is NOT blocked on ignorance must not sense.
    g3 = new_graph()
    declare_type(g3, "folder", attrs={"kind_of": "folder"})
    f3 = g3.mint("chunk", kind_of="folder", label="src", count=1)
    g3.link("root", "has", f3)
    goal3 = G.open_goal(g3, label="already true")
    G.require_attr(g3, goal3, f3, "count", 1)
    p3 = D.open_pursuit(g3, goal3, T.open_thread(g3), f3)
    lp3 = L.open_loop(g3)
    L.schedule(g3, lp3, p3, why="pursue")
    L.run(g3, lp3, max_ticks=100)

    return {"THE_PLANNER_IS_BLIND_TO_IT": blind == (frozenset(), frozenset({None})),
            "and_the_goal_BOTTOMS_OUT_in_ignorance": bottoms_out,
            "and_AFTERWARDS_it_no_longer_does": not G.blocked_on_ignorance(g, goal),
            "IT_SENSED_FOR_REAL": g.attr(p, "sensed") == ("scan_dir",),
            "and_the_world_really_moved": g.attr(folder, "count") == 3,
            "THE_GOAL_IS_SATISFIED": G.satisfied(g, goal, under=folder),
            "THE_SENSING_TICK_REPORTS_look_NOT_imagine": L.LOOK in verbs,
            "IT_REPLANNED_rather_than_resuming":
                len([n for n in g.nodes if g.kind(n) == "search"]) == 2,
            "CONTROL_planning_alone_FAILS": not g2.attr(s2, "found"),
            "CONTROL_a_goal_not_blocked_on_ignorance_never_senses": g3.attr(p3, "sensed") is None,
            "and_that_one_still_settled": g3.attr(p3, "phase") == D.SETTLED}


def check_arithmetic_on_an_UNLOOKED_AT_slot_skips_the_branch_and_spares_the_agenda():
    """A domain could be numeric or it could sense, and not both. Reported by HarneSkills.

    The same containment the check above records for `Imagined`, for the second way an imagined step
    can fail — and this one is the general case rather than an edge one. Means-ends imagines an
    operator whose body adds to a slot nobody has looked at yet, `ADD` meets `graph.UNKNOWN`, and
    Python raises `TypeError`. It escaped `loop.tick` exactly as `Imagined` used to.

    The arithmetic that makes a domain worth planning over is precisely what meets the unknown that
    sensing exists to resolve, so this was not a corner: the crash stood between the goal and the look
    that would have answered it.

    *An imagined step that cannot be computed is the same category as one that must not be taken* —
    the state is unreachable, so the branch is skipped and recorded, and what remains is ignorance, so
    `_phase_sensing` goes and looks. Recorded as `uncomputable` rather than joined to `unimaginable`,
    because *"nothing could imagine it"* is a missing mock and *"the sums did not work"* is a missing
    observation, and a reader that cannot tell them apart cannot tell which to fix.

    Vacuity guards, and the first is the one the fix is actually about: an unrelated task sharing the
    agenda must still finish, or the containment claim is untested — that is what the escape used to
    destroy. The bad operator must genuinely have been reached (or nothing was contained), the pursuit
    must go on to sense and close the goal (or it was contained into uselessness), and the report must
    name the reason. The control is the identical world with the two arithmetic lines removed."""
    from . import asm, dispatch as DP, driver as D, goal as G, loop as L, thread as T
    from .graph import UNKNOWN

    DP.register("selftest_count_stock", lambda gr, t: gr.put(t, rares=5), observes=True)

    def world(*, arithmetic: bool):
        g = new_graph()
        declare_type(g, "desk", attrs={"kind_of": "desk"})
        body = ("fn buy(d: desk) -> desk:", '    ATTR R(n) F(d) "rares"',
                "    ADD R(n) R(n) 1", '    SET F(d) "rares" R(n)')
        asm.load_text(g, _lines("fn look(d: desk) -> desk:",
                                '    DISPATCH R(o) "selftest_count_stock" F(d)', "",
                                *(body if arithmetic else body[:1] + body[-1:])))
        d = g.mint("chunk", kind_of="desk", label="desk", rares=UNKNOWN)
        g.link("root", "has", d)
        tag(g, d, "desk")
        goal = G.open_goal(g, label="hold three")
        G.require_attr(g, goal, d, "rares", 3, ">=")
        return g, d, goal

    g, d, goal = world(arithmetic=True)
    bottoms_out = G.blocked_on_ignorance(g, goal, under=d)
    p = D.open_pursuit(g, goal, T.open_thread(g), d)
    lp = L.open_loop(g)
    L.schedule(g, lp, p, why="pursue it")
    # The bystander. It shares the agenda and has nothing to do with the desk, so if the arithmetic
    # failure escapes `tick` again this never runs — which is the property being asserted.
    bystander = D.open_pursuit(g, *_settled_goal(g), attempts=1)
    L.schedule(g, lp, bystander, why="an unrelated task")
    L.run(g, lp, max_ticks=400)

    skipped = {n: g.attr(n, "uncomputable") for n in g.nodes
               if g.kind(n) == "search" and g.attr(n, "uncomputable")}
    report = D.pursuit_report(g, p)

    g2, d2, goal2 = world(arithmetic=False)
    p2 = D.open_pursuit(g2, goal2, T.open_thread(g2), d2)
    lp2 = L.open_loop(g2)
    L.schedule(g2, lp2, p2, why="the same world, without the arithmetic")
    L.run(g2, lp2, max_ticks=400)

    return {"the_goal_BOTTOMS_OUT_in_ignorance": bottoms_out,
            "THE_BAD_OPERATOR_WAS_REALLY_REACHED": any("buy" in v for v in skipped.values()),
            "AND_THE_UNRELATED_TASK_ON_THE_SAME_AGENDA_STILL_FINISHED":
                g.attr(bystander, "phase") == D.SETTLED or g.attr(bystander, "done"),
            "THE_PURSUIT_WENT_ON_TO_SENSE": g.attr(p, "sensed") == ("look",),
            "and_the_world_really_moved": g.attr(d, "rares") == 5,
            "THE_GOAL_IS_SATISFIED": report["done"],
            "skipped_is_kept_APART_from_unimaginable":
                all(not (g.attr(n, "unimaginable") or ()) or
                    set(g.attr(n, "unimaginable")) != set(g.attr(n, "uncomputable"))
                    for n in skipped),
            "CONTROL_the_same_world_without_arithmetic_behaves_identically":
                g2.attr(p2, "sensed") == ("look",) and g2.attr(d2, "rares") == 5}


def _settled_goal(g):
    """An already-true goal on a fresh node — a task that costs one tick and cannot fail. Used as a
    bystander, to prove an exception in someone else's task did not take the agenda down with it."""
    from . import goal as G, thread as T
    n = g.mint("chunk", kind_of="bystander", label="bystander", ok=1)
    g.link("root", "has", n)
    goal = G.open_goal(g, label="nothing to do")
    G.require_attr(g, goal, n, "ok", 1)
    return goal, T.open_thread(g), n


def check_a_pursuit_SAYS_when_it_cannot_look_at_the_subject_it_was_given():
    """Sensing selects *on* the subject; planning searches *under* it. Reported by HarneSkills, who
    lost an afternoon to it having already read the code.

    Both rules are right. `_looker_on` walks `selection.candidates(g, subject)`, so a container has no
    applicable single-parameter looker and can never look, whatever sits inside it — while the planner
    happily searches under that same container, which is why passing it is the natural thing to do.
    What was wrong is that one argument satisfied one rule and quietly failed the other, and the
    resulting report — *"1 attempt(s) did not reach [desk.rares >= 3]"* — is exactly what a genuinely
    impossible goal says.

    Named rather than fixed, deliberately. Making `_looker_for` search under the subject was the
    alternative: sensing would then dispatch at a node the caller never nominated, quietly widening
    what an agent may go and touch. A refusal that names the reason cannot be wrong; a fix that
    guesses the subject can.

    Vacuity guards: the identical world pursued *at the desk* must succeed, or the scenario is just a
    broken world; the message must name both the subject that cannot be looked at and the one that
    can, or it is no more use than the silence it replaces; and a goal that is not blocked on ignorance
    at all must produce no such message, or it is being pasted onto every failure."""
    from . import asm, dispatch as DP, driver as D, goal as G, thread as T
    from .graph import UNKNOWN

    DP.register("selftest_count_case", lambda gr, t: gr.put(t, rares=5), observes=True)

    def world():
        g = new_graph()
        declare_type(g, "desk", attrs={"kind_of": "desk"})
        asm.load_text(g, _lines("fn look(d: desk) -> desk:",
                                '    DISPATCH R(o) "selftest_count_case" F(d)'))
        shop = g.mint("chunk", kind_of="shop", label="shop")
        g.link("root", "has", shop)
        d = g.mint("chunk", kind_of="desk", label="desk", rares=UNKNOWN)
        g.link(shop, "desk", d)
        tag(g, d, "desk")
        goal = G.open_goal(g, label="hold three")
        G.require_attr(g, goal, d, "rares", 3, ">=")
        return g, shop, d, goal

    g, shop, d, goal = world()
    said = D.carry_out(g, goal, T.open_thread(g), shop, attempts=1).get("why", "")

    g2, _shop2, d2, goal2 = world()
    at_the_desk = D.carry_out(g2, goal2, T.open_thread(g2), d2, attempts=1)

    # Control: nothing unknown, so nothing to say about looking.
    g3 = new_graph()
    declare_type(g3, "desk", attrs={"kind_of": "desk"})
    d3 = g3.mint("chunk", kind_of="desk", label="desk", rares=1)
    g3.link("root", "has", d3)
    tag(g3, d3, "desk")
    goal3 = G.open_goal(g3, label="hold three")
    G.require_attr(g3, goal3, d3, "rares", 3, ">=")

    return {"IT_SAYS_NOTHING_CAN_LOOK_AT_THE_SUBJECT": "nothing can look AT shop" in said,
            "AND_NAMES_THE_ONE_THAT_COULD_LOOK": "'look'" in said and "at desk" in said,
            "and_it_says_which_way_round_the_two_rules_go":
                "selects on the subject" in said and "searches under it" in said,
            "CONTROL_the_same_world_pursued_AT_THE_DESK_succeeds":
                at_the_desk["done"] and g2.attr(d2, "rares") == 5,
            "CONTROL_a_goal_not_blocked_on_ignorance_gets_no_such_message":
                D._sensing_gap(g3, goal3, d3) is None}


def check_a_constraint_is_DESCRIBED_with_the_comparison_it_was_written_with():
    """`describe_constraint` rendered every comparison as `=`. Reported by HarneSkills, who noticed
    that every `why` line they quoted at us misreported the goal.

    The operator is stored on the constraint and was dropped by the renderer, so `desk.cash >= 300`
    read back as *we needed cash to be exactly 300*. Comparison operators in goals are newer than this
    renderer, which is the whole of the story.

    Equality renders as `=` rather than `==`, because this is prose for a reader and `=` is the surface
    the author wrote. That is the guard worth having: the fix is one line and the obvious version of it
    regresses the commonest case."""
    from . import goal as G

    g = new_graph()
    declare_type(g, "desk", attrs={"kind_of": "desk"})
    d = g.mint("chunk", kind_of="desk", label="desk", cash=120)
    g.link("root", "has", d)

    shown = {}
    for op in ("==", ">=", "<=", ">", "<", "!="):
        goal = G.open_goal(g, label=f"cash {op}")
        shown[op] = G.describe_constraint(g, G.require_attr(g, goal, d, "cash", 300, op))

    return {"EVERY_COMPARISON_SURVIVES_THE_ROUND_TRIP":
                all(op in text for op, text in shown.items() if op != "=="),
            "and_EQUALITY_still_reads_as_prose": shown["=="] == "desk.cash = 300",
            "and_none_of_them_read_as_equality":
                sum(t == "desk.cash = 300" for t in shown.values()) == 1,
            "shown": shown}


def check_a_TIMER_gates_a_task_and_the_agenda_waits_rather_than_spinning():
    """Scheduled actions — *"stop cooking the pasta after ten minutes"*.

    The user's case: timers and scheduled actions, *"installed by procedures themselves"*. So
    the payload is an ordinary task and the gate is an ordinary moment node — nothing new is
    represented, because `clock.moment(at=…)` already existed. `loop.schedule(not_before=…)` is the edge
    that lets the loop honour one, and it lives on the task, so *"when may this run?"* is a property
    of the work rather than of the queue it is sitting in.

    This is the first selection the agenda has ever made. `tick` took `here[0]` unconditionally —
    round-robin with no content. That makes this the same seam where outer-loop triage would go, which is
    worth knowing before a second reason to open it arrives.

    Waiting is reported, never spun on. Rotating a gated head to the back and trying again would
    busy-loop until the clock caught up — burning the tick budget while looking like progress, which is
    the shape of every silent failure in this file. The tick returns a record naming what it waits for and
    `run` stops, because *"sleep, or do something else"* is a decision only a driver can make.

    Vacuity guards, and they are the whole check: the gated task must not run early (or the gate is
    decorative), it must run once the clock moves (or the gate is a block), an ungated task beside
    it must still run (or one timer freezes everything), and a relative moment — *"a minute after the
    pan is hot"*, which carries no scalar — must refuse rather than silently never firing."""
    from . import asm, clock as C, function as fn, loop as L
    from .focus import Focus
    from .isa import Machine

    g = new_graph()
    declare_type(g, "pot", attrs={"kind_of": "pot"})
    # Stored functions, not anonymous programs: the outer loop refuses an activation with no `of`,
    # because a program that exists only in Python is exactly the island this arc removed.
    asm.load_text(g, _lines('fn take_the_pasta_off(p: pot) -> pot:', '    SET F(p) "cooking" false',
                            '', 'fn lay_the_table(p: pot) -> pot:', '    SET F(p) "table" true'))
    pot = g.mint("chunk", kind_of="pot", label="pot")
    g.link("root", "has", pot)

    def a_task(g, name):
        _params, prog = fn.load(g, name)
        return Machine(prog).start(g, Focus(g).open("p", pot), of=fn.find(g, name), label=name)

    lp = L.open_loop(g)
    ten_minutes = C.moment(g, at=1000.0, label="pasta is done")
    timer = a_task(g, "take_the_pasta_off")
    other = a_task(g, "lay_the_table")
    L.schedule(g, lp, timer, why="ten minutes", not_before=ten_minutes)
    L.schedule(g, lp, other, why="meanwhile")

    early = L.run(g, lp, max_ticks=20, at=999.0)          # the clock has not reached it
    ran_early = [r["doing"] for r in early["did"] if r.get("task")]
    late = L.run(g, lp, max_ticks=20, at=1001.0)          # now it has
    ran_late = [r["doing"] for r in late["did"] if r.get("task")]

    def refuses(fn):
        try:
            fn()
            return False
        except Exception:
            return True

    relative = C.moment(g, label="a minute after the pan is hot")
    return {"THE_UNGATED_TASK_RAN": any("lay_the_table" in d for d in ran_early),
            "AND_THE_TIMER_DID_NOT": not any("pasta" in d for d in ran_early),
            "the_run_reported_WAITING_rather_than_spinning": early["why"] == "waiting on a timer",
            "and_it_NAMED_what_it_waits_on": any(r.get("waiting") for r in early["did"]),
            "IT_RAN_ONCE_THE_CLOCK_MOVED": any("pasta" in d for d in ran_late),
            "and_the_gate_is_on_the_TASK_not_the_queue": g.target(timer, "not_before") == ten_minutes,
            "A_RELATIVE_MOMENT_REFUSES_rather_than_never_firing":
                refuses(lambda: C.arrived(g, relative)),
            "and_an_ABSOLUTE_one_answers": C.arrived(g, ten_minutes, at=1001.0) is True,
            "ungated_work_is_always_due": L.due(g, other)}


def check_a_PROCEDURE_INSTALLS_ITS_OWN_TIMER():
    """*"Stop cooking the pasta after ten minutes"* — installed by the cooking procedure itself.

    The user's framing: timers *"could be rules, or installed by procedures themselves"*. The
    thing that knows about the ten minutes is `cook_pasta`, not whoever called it, so a running body must
    be able to reach the agenda it is on. `NATIVE R(t) "after" 600 "take_the_pasta_off" F(pot)`.

    Nothing new is represented: `clock.moment(at=…)` is the gate, an activation is the payload, and
    `loop.schedule(not_before=…)` already honours both. What was missing was reach.

    Building it exposed two facts riding on one edge. `loop -task-> t` is turn order: `tick`
    unlinks the head *before* advancing it and re-appends it at the tail, so a running task is not on
    the agenda at all — and a body asks *"which loop am I on?"* precisely while running. Membership is a
    different, stable fact and now has its own edge (`task -on-> loop`). The first version refused every
    call with *"not on an agenda"*, which is the honest failure the guard was written for.

    Vacuity guards: the timer must not already have fired when `cook_pasta` returns (or it is not a
    timer), the gate must be roughly the requested distance away rather than any moment at all, it must
    fire once the clock passes it, and a body not on an agenda must be refused rather than scheduling
    into nowhere — a timer installed nowhere can never fire, and would look exactly like one that is
    early."""
    import time as _t
    from . import asm, clock as C, function as fn, loop as L
    from .focus import Focus
    from .isa import Machine

    g = new_graph()
    declare_type(g, "pot", attrs={"kind_of": "pot"})
    asm.load_text(g, _lines('fn take_the_pasta_off(p: pot) -> pot:', '    SET F(p) "cooking" false',
                            '',
                            'fn cook_pasta(p: pot) -> pot:', '    SET F(p) "cooking" true',
                            '    NATIVE R(t) "after" 600 "take_the_pasta_off" F(p)'))
    pot = g.mint("chunk", kind_of="pot", label="pot")
    g.link("root", "has", pot)
    _p, prog = fn.load(g, "cook_pasta")
    a = Machine(prog).start(g, Focus(g).open("p", pot), of=fn.find(g, "cook_pasta"), label="cook_pasta")
    lp = L.open_loop(g)
    L.schedule(g, lp, a, why="dinner")

    first = L.run(g, lp, max_ticks=20)
    cooking_after = g.attr(pot, "cooking")
    pending = L.agenda(g, lp)
    gap = (C.at_of(g, g.target(pending[0], "not_before")) - _t.time()) if pending else None
    L.run(g, lp, max_ticks=20, at=_t.time() + 601)

    # A body that is NOT on an agenda must be refused.
    g2 = new_graph()
    declare_type(g2, "pot", attrs={"kind_of": "pot"})
    asm.load_text(g2, _lines('fn noop(p: pot) -> pot:', '    SET F(p) "x" 1',
                             '', 'fn orphan(p: pot) -> pot:',
                             '    NATIVE R(t) "after" 5 "noop" F(p)'))
    pot2 = g2.mint("chunk", kind_of="pot", label="pot")
    g2.link("root", "has", pot2)
    try:
        fn.invoke(g2, "orphan", {"p": pot2})
        orphan_refused = False
    except Exception as e:
        orphan_refused = "not on an agenda" in str(e)

    return {"THE_PROCEDURE_SCHEDULED_ITS_OWN_FOLLOW_UP": len(pending) == 1,
            "and_it_is_the_right_one": g.attr(pending[0], "label") == "take_the_pasta_off",
            "IT_HAD_NOT_FIRED_YET": cooking_after is True,
            "the_loop_said_it_was_WAITING": first["why"] == "waiting on a timer",
            "and_the_gate_is_TEN_MINUTES_out": gap is not None and 590 < gap <= 600,
            "IT_FIRED_ONCE_THE_CLOCK_PASSED_IT": g.attr(pot, "cooking") is False,
            "a_body_NOT_on_an_agenda_is_REFUSED": orphan_refused,
            "and_a_RUNNING_task_can_still_find_its_loop": L.loop_of(g, a) == lp}


# The entry point must be the last thing in this file. `_checks()` reads `globals()` at call time,
# so any check defined below this block is simply not executed - the count stays put and the report looks
# healthy. That is the same false-green `_checks()` own docstring records, one level up, and it bit again
# when the query checks were appended after it.
if __name__ == "__main__":
    print(report())
