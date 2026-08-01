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


def check_the_kind_index_cannot_disagree_with_a_scan():
    """⚠ A HAND-MAINTAINED INDEX, so it earns a test — the kind that guards a discipline a human must
    follow (only `mint` adds and only `drop` removes), which is the kind this project keeps.

    `of_kind` exists because `types.find_type` and `function.find` scanned every node in the graph on
    every lookup, and `violations` reached `find_type` four times per call. Measured on one
    `driver.proposals` enumeration over a world with 200 nodes that bind to nothing: 21,525 `find_type`
    calls and 21,575 whole-graph tuple builds — which is why inert content cost 57× the enumeration time
    for zero extra proposals.

    It is legitimate where `types.tag`'s `is_a` stamp is not, and the difference is worth stating: this is
    maintained by the **substrate** on the only operation that can create a kind, so it cannot drift;
    a stamp is a **claim** a rule made, so it must be re-validated on read (`tagged_as`).

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
    """⭐ SLICE 3 of `deliberation.md`: goals gain a hierarchy, so `DECOMPOSE` has somewhere to post and a
    decision rule has a context to key on.

    **⚠ The key this check exists for is the LAST one, and it is a trap taken from prior work rather than
    rediscovered.** `docs/units/goal_machinery.md` §8 records that a parent's "all my children are done"
    guard was written as an *absence* — no subgoal that is unmet — and so was **vacuously true before any
    subgoal had been minted**: an undecomposed goal read as trivially achieved. Generalised there as *don't
    trust an open-ended absence without an explicit closure fact*. `satisfied` already applies the same rule
    one level down (`bool(cs)`), which is why the two guards look alike.

    Also: ancestry is the context (so a rule need not be rewritten per position), children are O(1) the
    other way, and **a cycle is structurally impossible** because parentage is set at mint and never
    changed — the same reasoning that lets `Graph.of_kind` be an index rather than a cache. ⚠ That bounds
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

    # THE TRAP: `top` has a child that is not satisfied, so "all children done" must be False; and `deep`
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
    """⭐⭐ THE LAST CAPABILITY GAP: *not looked* as distinct from *not there*.

    The engine already performed information-gathering actions but could only model them as world-*changing*
    ones — `scan_dir`'s mock mints file nodes, as though scanning **created** files rather than revealing
    them. Underneath was a substrate limit: an attribute was present or absent, and absence meant *lacks
    it*. So the system could not tell "make p true" from "find out whether p", an information-gathering
    subgoal had nothing to close, and `pursue` reported failure identically whether **no plan exists** or
    **no plan exists given what I know** — though only the second warrants going and finding out.

    **⭐ The fix rides on §5d's existing insight rather than adding a planner.** A goal naming *which*
    constraints are false lets the driver ask what could close them; one separating **false** from
    **unknown** lets it reach for a sensing action. `undetermined` is that separation.

    **⚠ Explicit ignorance only.** Absence still means *lacks it*; a slot is unknown only when something
    says so. Treating every absence as ignorance would make the whole graph unknown and every constraint
    undecidable — and would be untrue, since most absences really are knowledge.

    ⚠ `blocked_on_ignorance` requires the goal to **bottom out** in ignorance, not merely touch it —
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
    # ⚠ Read the CONTRASTS BEFORE acting. The first version evaluated them in the return dict, after
    # `carry_out` had already made the slot known — so `mixed` had nothing undetermined left and the key
    # passed no matter what `blocked_on_ignorance` did. A planted bug proved it tested nothing.
    plain_blocked = G.blocked_on_ignorance(g, plain, under=world)
    mixed_blocked = G.blocked_on_ignorance(g, mixed, under=world)
    empty_blocked = G.blocked_on_ignorance(g, G.open_goal(g, label="empty"), under=world)

    # END TO END: the goal is closed only by an action that reveals, and only after it really ran.
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


def check_authored_knowledge_arrives_as_text_that_can_be_refused():
    """⭐⭐ THE BORDER, EXTENDED TO EVERYTHING A DOMAIN CONTRIBUTES.

    The standing principle is that microfunctions ship with the engine and *everything a domain contributes
    is data*. But the border existed for **goals alone**: a guideline or a method could only be authored by
    calling Python — which is precisely the "reach past the surface and write graph structure" `intake.py`'s
    docstring says must never happen, because then nothing can refuse it. **The principle was stated and
    unenforced.** One block grammar now covers all three families.

    **⚠ The key that matters is the END-TO-END one.** A parser that produces nodes nobody uses would pass
    every structural assertion here; what makes the border real is that a method *authored as text* goes on
    to decompose a goal and change the world.

    **⚠ `method` and `procedure` differ ONLY in force** — identical bodies, opposite failure behaviour —
    which is why the surface makes the author say which word they mean rather than inferring it.

    **⚠ Refusal must leave nothing behind, and now does so via the JOURNAL.** The old goal path dropped its
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

    # END TO END: a goal authored as text, decomposed by a method authored as text.
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
    """⭐⭐ The half of slice 4 that was missing: methods as **data that select themselves**, so nobody
    assembles subgoals by hand.

    **⚠ The key that matters most is the COMPLETENESS guard.** A method prunes by *replacing* enumeration —
    that is where the exponential win lives, and it is why a method cannot be a ranker. The price is that a
    wrong or non-covering method could make a reachable goal **unreachable**, which is a failure mode
    nothing else in this engine has: `guideline.py` can only reorder, `forbid_action` prunes on a proof.
    The only thing between authority and disaster is the `ADVISORY` fallback, so it is checked directly —
    a goal solvable by search must **stay solvable** when a method that mishandles it is declared.

    **⭐ And context is structural.** A method is generic and cannot name an individual ancestor goal, so a
    subgoal points at the **method that raised it** and *"within a goal raised by M"* becomes an ordinary
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

    # THE COMPLETENESS GUARD: a method that mishandles the goal must not lose the solution.
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
    # ⚠ The negative case must differ ONLY in context. A goal with an `attr`/`clear` constraint that is
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
            # ⚠ A METHOD IS A ROUTE, NOT A REDEFINITION. A goal with its own world constraints keeps
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
    """⭐⭐ SLICE 4: the distinction the whole design turns on — **force is about FAILURE, not strength.**

    Two decompositions can be written identically and must behave oppositely when a step does not work out.
    A **method** was a suggestion about how, so falling back to search is right and incompleteness is fine.
    A **procedure** was the sanctioned way, so falling back would be *improvising*: for it, "could not do
    it" is a better answer than "did it another way". That inverts every other reflex in `driver` —
    `carry_out` replans, `recover` reaches for contingencies — and the inversion is the feature.

    ⭐ Built on `goal_machinery.md` §8's claim that *"a procedure is this shape plus one sequencing edge"*,
    which a probe found substantially true: ordered subgoals already ran through `carry_out` unchanged. What
    was missing was **drive** — nothing walked the order — plus one thing the probe surfaced that the claim
    did not mention: a procedure's parent has no world constraints of its own, so a satisfaction test that
    only reads constraints calls a perfectly completed procedure unsatisfied. Hence `BY_STEPS`.

    Vacuity guards: the impossible step must be genuinely impossible (so the contrast is real), and the
    method and the procedure must be **structurally identical apart from the declared force**."""
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
    """⭐⭐ SLICE 2 of `deliberation.md`: authored preference that may be WRONG without being UNSOUND.

    **The property under test is the one that makes advice safe to accept: `avoid` means LATER, never
    NEVER.** `goal.forbid_action` is the one that means never, and it prunes because a safety breach is a
    *proof*. A guideline is a guess, and the standing rule is rank a guess, prune a proof.

    ⚠ **The decisive case is Sussman's anomaly, reused deliberately.** There, the only route begins with
    `unstack` — a move that closes no constraint and scores low. `check_a_forbidden_action_prunes...`
    already shows that *forbidding* `unstack` turns it honestly unsolvable. So **avoiding `unstack` must
    leave it solved**, or `avoid` has silently become `forbid` and authored advice can lose solutions.
    That single contrast is what this check exists for.

    ⚠ **What the planted-bug probes revealed, and it is the more useful half.** A ranker rigged to return
    -999 for every avoided call — advice behaving as an outright filter — **still solved the anomaly.**
    So *"advice cannot exclude" is guaranteed by `pursue`'s architecture, not by anything in
    `guideline.py`*: the frontier only ever **orders**, so no score however low can put a move out of
    reach. That is exactly why authored advice is safe to accept, and it means this check *demonstrates*
    the property end to end rather than enforcing it. What `guideline.py` must get right on its own is the
    **band**, and that is what the probes do bite on.

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

    # THE CONTRAST. Same anomaly, same engine; only the force differs.
    g1, w1, goal1 = sussman()
    GL.avoid(g1, function="unstack", because="the crane is slow")
    avoided = D.pursue(g1, goal1, T.open_thread(g1), w1, max_steps=400, max_depth=5,
                       rank=GL.ranker(g1))

    g2, w2, goal2 = sussman()
    G.forbid_action(g2, goal2, function="unstack", reason="the crane is out of service")
    forbidden = D.pursue(g2, goal2, T.open_thread(g2), w2, max_steps=400, max_depth=5)

    # ⚠ Bands must survive, AND the reordering must be real. Advice keyed on a NODE rather than a
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
    """⭐ SLICE 1 of `deliberation.md`: `pursue` gains a decision point and changes nothing.

    The loop was closed — nothing could intervene between two imagined steps — so "what should I do next?"
    was not an expressible question, only a `while` condition. That made deliberation the thing this system
    computes *with* and cannot compute *about*: the same defect attention had before `thread.py` and the
    goal had before `goal.py`, in its third place.

    **⚠ The vacuity guard is the whole test.** A seam nothing can steer is indistinguishable from no seam,
    and it would pass any check that only asserted "default behaviour is unchanged" — which is exactly the
    green this project keeps catching as false. So both halves are required: the default path must be
    **identical**, and a decision must **actually divert** the search.

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

    # THE VACUITY GUARD: a decision must be able to change the outcome, or none of the above means anything.
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
            # ⚠ `why` is an edge property of the TRANSITION, not an attribute of the entry — read it
            # through `thread.why`. Reading `g.attr(entry, "why")` returns None and this key was silently
            # False until the tally caught it, which is §5g's lesson landing on its own author.
            "AND_IT_REACHES_THE_THREAD": any(
                "decided to commit" in (T.why(g3, e) or "") for e in T.entries(g3, t3)),
            "nothing_reached_the_thread_by_default": not any(
                "decided to" in (T.why(g0, e) or "") for e in T.entries(g0, t0)),
            # ⚠ Updated as the machinery landed. `SENSE` is now a real stop (ignorance exists), and
            # `DECOMPOSE` no longer raises for want of a goal hierarchy — it raises because a method
            # applies once per GOAL (`driver.attempt`), never once per search step. Frequency, not absence.
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
    """⚠ `schema_of` answers with `Req`s now, not bare `(kind, count)` pairs — a count is a RANGE and a
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
        # ⚠ A KEY REPORTING `False` IS A FAILURE, and it did not used to count. The harness only tallied
        # exceptions, so a probe that ran fine and answered "no" printed among a hundred lines and a skim
        # missed it — which is exactly the mistake `HANDOFF.md` §7 already records having made once. It
        # then happened again, to `goal_recorded_as_met`, which is what prompted this. Non-boolean values
        # are data a check chose to report (counts, reasons) and are left alone; only an explicit `False`
        # is a red.
        bad = sorted(k for k, v in r.items() if v is False)
        if bad:
            failures += 1
        # ASCII marker on purpose: the report is piped, and a Windows console is cp1252.
        lines.append(f"{fn.__name__[6:]:<52} {r}" + (f"\n{'':<52} !! FALSE: {bad}" if bad else ""))
    lines.append(f"\n{len(checks)} checks, {failures} FAILED")
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


def check_assembly_refuses_a_malformed_invoke():
    """⭐ REPORTED BY `../pystrider`. Every opcode NAME was checked; `INVOKE`'s operand SHAPE was not — and
    it is the one opcode taking a structured operand, a mapping of parameter names. So the natural
    positional form parsed, defined, and failed only when run, with `AttributeError: 'str' object has no
    attribute 'items'` — no line, no opcode, nothing naming the operand that was wrong. Squarely the
    silent-acceptance failure this module exists to prevent.

    Vacuity guards: the well-formed named-binding version must actually parse AND run (a check that only
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
    """The other half of §6: a mapping operand had no textual form, so `unparse` rendered the raw Python
    dict and the round trip was broken — silently, because the only check was that the word `INVOKE`
    appeared in the dump. That matters most for a function nothing authored: `compile_episode` builds
    `INVOKE` operands in Python, so a LEARNED function could not be read back in.

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
    "type", "requires", "requires_attr", "requires_rel",
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


def check_the_copy_order_is_a_fact_about_the_graph_not_about_node_ids():
    """⭐⭐ THE SAME WORLD, BUILT TWICE, MUST BE COPIED IN THE SAME ORDER — and this was false, silently,
    for as long as the workbench has existed.

    `reachable` traverses deterministically (`g.labels` is sorted, `g.targets` is an insertion-ordered
    tuple) and then returned a **`set`**, throwing that order away and substituting the iteration order of
    the node-id *strings*. Ids come from a process-global counter, so the second identical world in a
    process gets different ids, hashes differently, and is copied in a different order. `mappings` order
    is `proposals` order, and `driver.pursue` breaks frontier ties by insertion order — so the search was
    **irreproducible**: the identical five-block goal measured 12 imagined states, then 306, then
    budget-exhausted failure, on consecutive runs of one process.

    ⚠ **Nothing was ever lost** — the *set* of proposals is identical every time — so this never yielded a
    wrong plan, only an arbitrary one at an arbitrary cost. That is exactly why 132 checks passed over it:
    a single run of anything is self-consistent, and only a measurement *repeated in one process* can see
    it. Every performance number in the docs was taken under it.

    Vacuity guard: the two worlds must genuinely get **different node ids**, or identical order would be
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
            "recorded_as_PLANNED": G.is_planned(g, goal),
            "but_NOT_as_done": not G.is_closed(g, goal),
            "and_it_says_where_it_was_seen": g.target(goal, "seen_in") == result["frame"],
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


# --- expectations: divergence the declared type cannot catch -------------------------------------------
def _scanner_fs():
    """A tool call whose mocks predict **concrete state**, not just a type.

    ⚠ Both mocks return `listing`, which is exactly the point: reality *will* satisfy the declared return
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
    """⭐ Nothing is authored and nothing is stored — frame N−1 and frame N *are* the before and after, so
    the expectation is their difference. Vacuity guard: it must name the minted files AND the attribute that
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
    """⭐⭐ THE CASE THE DECLARED TYPE CANNOT CATCH. The plan assumed listing the directory would produce
    two file nodes. Reality lists it and produces none — but the result still satisfies `listing`, so the
    cast passes and only the concrete expectation notices.

    Vacuity guards: the cast must genuinely pass (otherwise the type check is what caught it, not the
    expectation); and the identical plan against a reality that DOES produce the files must complete."""
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
    """⭐⭐ THE OTHER DIRECTION. A goal of "some file must exist" cannot be served by looking at signatures:
    `scan_dir(d: dir) -> listing` mentions no file, and its *body* is a `DISPATCH` — everything interesting
    happens on the far side of a tool call. The knowledge that listing a directory *produces files* lives in
    the **mock**, which is the declared assumption about how the call turns out.

    Vacuity guards: the real function's own body must establish nothing about files (so the mock is doing
    the work); a function with no such mock must not be offered for it; and the search must actually plan
    the call rather than merely score it."""
    from . import driver as D, goal as G, thread as T
    g, d = _scanner_fs()
    declare_type(g, "file", attrs={"kind_of": None})
    own, _u = D._effects(g, "scan_dir", include_mocks=False)
    withmocks, _u2 = D.establishes(g, "scan_dir")

    goal = G.open_goal(g, label="find a file")
    G.require_type(g, goal, "file")                     # SOMETHING of this type — no subject named
    result = D.pursue(g, goal, T.open_thread(g), d, max_steps=50)
    return {"the_signature_mentions_no_file": fn_returns(g, "scan_dir") == "listing",
            "and_its_own_body_establishes_none": not any(e[0] == "mint" for e in own),
            "BUT_ITS_MOCK_PREDICTS_ONE":
                any(e[:2] == ("mint", "file") for e in withmocks),
            "so_the_goal_finds_the_call": result["found"],
            "and_plans_the_REAL_call": D.plan_steps(g, result) == ("scan_dir",),
            "NOT_THE_MOCK": "found_two" not in D.plan_steps(g, result),
            "in_one_step": result["steps"] == 1}


def check_a_minted_node_keeps_the_join_through_a_register():
    """⭐⭐ REPORTED BY `../pystrider`, the engine's first real user, which uses `establishes` for
    *recognition* rather than for ranking. A pattern authored as `NEW R(it)` then `LINK R(it) …` came back
    as three effects with **no subject at all** — "orphan facts that no longer claim to describe one node" —
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
                ("attr", "kind", "seq.other", None) in later}


def _threshold_library():
    """Two comparisons, each with a literal right-hand side, and operators that repair one by NAVIGATING
    to it. The shape `../pystrider` reported: *read a part, write to that part*."""
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
    """⭐⭐ REPORTED BY `../pystrider`. A function whose operands are parameters read beautifully; one that
    had to *navigate* went dark — and a bridge between two vocabularies is nothing but navigation, so the
    functions they most wanted to read were exactly the ones that could not be read.

    `GET R(s) F(a) "over"` makes `R(s)` denote a derivable thing: *the `over` of `a`*. So a role is a PATH,
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
                repair == frozenset({("attr", "value", "c.right", None)}),
            "and_reports_it_as_fully_read": not unknown,
            "but_a_value_bearing_register_claims_nothing":
                ("link", "seq", "b", None) in lost}


def check_a_role_path_is_resolved_against_the_world():
    """The other half of the same mechanism, and the reason it is split in two: `establishes` says *`c`'s
    `right`* without knowing which node that is, and only a caller holding bindings can turn that into an
    individual. Static provenance, dynamic resolution.

    Vacuity guards: the same role must resolve to DIFFERENT nodes under different bindings (or it is not
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
    """⭐⭐ WHY THE PATH IS WORTH ITS COST TO THE DRIVER ITSELF, not only to a consumer reading descriptions.

    Two comparisons; the goal wants one literal lowered. `lower_threshold` writes to a register, so before
    paths it established nothing anyone could name — and band 4 ("this call writes exactly this constraint")
    could never be reached by *any* candidate. Every proposal tied, and the guidance had nothing to rank
    with. `../pystrider` measured 5 imagined states against 6 blind on their own repair and said so.

    ⚠ The control is the whole check: blind search alone would not show that PATHS did it, so the middle
    figure re-runs the identical search with path roles pretended not to exist — the behaviour before this
    change. Guided must beat that, not merely beat blind.

    ⚠ **The step counts are compared one way only, deliberately.** With paths the search is decisive and
    lands on 3 every time; the other two are tie-broken by frontier insertion order and measure 5 or 10 run
    to run, because *without a reachable band 4 the guided search and the blind one are the same search* —
    which is `../pystrider`'s "found essentially unguided" in this engine's own numbers. So the load-bearing
    assertion is the structural one below: before paths, **no proposal could reach band 4 at all**."""
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
    """⭐ REPORTED BY `../pystrider`, which abstains from recognising a node whenever anything in a body was
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
    """⭐ Decidable contradictions only, so this can never reject a reachable goal. Vacuity guard: the same
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
    """⭐⭐ THE REGRESSION, ADDRESSED — but not by copying the old notion. That engine *derived facts*, so
    two contradictory conclusions were a contradiction. This one *performs actions in sequence*, where a
    later write legitimately overrides an earlier one. What survives is **interference**: two independently
    authored functions, composed by a library that grew, writing one slot for unrelated reasons — the
    telecom feature-interaction problem `function.py` cites as prior art.

    ⚠ The different-goal requirement is the whole distinction. Vacuity guards: steps within ONE plan
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

    # ⚠ THE VACUITY GUARD THAT MATTERS: one goal whose plan MUST write the slot twice (paint sets red,
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
    """⭐ REQUESTED AS A USE CASE BY `../pystrider`: their previous engine caught a collider between two
    independently authored fragments *before anything ran*, and the value was that the author learns at
    compose time rather than after a run that has already clobbered something.

    Their hypothesis — "`interference` over a frame chain, the same function with a different source of
    claims" — is right, with one correction: it takes **two** chains. One chain is a single committed plan,
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
    """⭐ **What IS this?** — the direction this module was missing. Every entry point was top-down
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
    """⚠ **THE DEFECT, FIXED.** `tag` stamps `is_a` and that stamp is a claim about the *past*, while `is_a`
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
    """⭐⭐ INTAKE. The loop is driven entirely by a goal, and until now the only way to get one was to call
    `goal.py` from Python — so the one thing that *starts* the system was the one thing it could not receive.

    ⚠ Tractable now only because a goal is no longer arbitrary structure: it is a handful of constraint
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
    """⚠ REFUSAL IS THE FEATURE. Three ways in, all loud: a sentence outside the closed vocabulary, a name
    that matches nothing, and — the one the project learned the hard way — a name that matches **more than
    one thing**. Nodes are nameless and a `label` is a convenience, so *never identify by name alone*.

    Vacuity guards: a well-formed goal in the same graph must parse; and a refusal must leave **nothing
    behind**, or the caller could pursue a half-built goal and appear to be working."""
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
    """⭐⭐⭐ THE WHOLE LOOP, IN ONE RUN. Materialise a world and a goal, bootstrap a thread, then:
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
    """⚠ A mock is an assumption about how a real call turns out, not something to do. Proposing one would
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
    """⭐⭐ THE CORRECTION THAT MATTERS. A listing produces a *variable* number of files, so the `2` in the
    mock is a **witness, not a promise**. Expecting exactly two would diverge on noise and make the whole
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
    """⭐ The whole loop closing: an expectation-based divergence recovers through the ordinary contingency
    machinery. The plan assumed two files; reality found none; the branch that assumed *none* was explored,
    so execution continues down it.

    ⚠ Vacuity guard that matters most: the sibling must be chosen because ITS predictions hold, not merely
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
    """Paul is a person. One PURE way to conclude mortality, and one that reaches the world.

    ⚠ Both write the *same* attribute, deliberately. If the impure one were merely ranked lower rather
    than barred, the verdict would still come back `yes` — so a check asserting only the answer would be
    vacuous about the thing that matters. It has to assert WHICH function was used.

    ⚠⚠ **And the impure one must SORT first, which is load-bearing rather than cosmetic.** Both establish
    the same effect, so `relevance` ties them; the frontier sort is stable, so the tie breaks on the order
    `function.names` returns — which is **alphabetical**, not declaration order. With the pure name winning
    that race, a planted removal of the purity bar still produced a proof naming `conclude_mortal`, so
    `AND_NEVER_APPEARS_IN_A_PROOF` passed *while testing nothing*. Hence `ask_the_registrar`: it sorts
    before `conclude_mortal`, making the trap the path the search takes by default, which is the only
    arrangement under which that key means anything. ⚠ Reordering the source text does NOT achieve this
    (the first attempt did exactly that and changed nothing) - the NAME is what decides."""
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
    """⭐ Asking is pursuing. The question is an ordinary goal node, the answer comes from `driver.pursue`,
    and the plan it FINDS is the derivation - so the justification arrives with the verdict rather than
    being reconstructed afterwards.

    ⚠ Vacuity guard: asking must leave the world UNTOUCHED. The derivation ran on a workbench, so `paul`
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
    """⭐⭐ The one genuinely new rule: concluding and doing are both "running a microfunction", so the
    difference cannot be left to intent. A function that could reach the world is barred from answering a
    question - PROVED off the stored body, and pruned rather than ranked.

    ⚠ THE LOAD-BEARING ASSERTIONS ARE THE LAST THREE KEYS, not the verdict. Both functions establish
    `mortal`, so the answer is `yes` either way; what distinguishes a working bar from an absent one is
    that the impure function is never even proposed.

    ⭐ **What removing the bar actually does, measured rather than assumed.** It does not quietly send mail:
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
                ("attr", "mortal", "p", None) in D.establishes(g, "conclude_mortal")[0]
                and ("attr", "mortal", "p", None) in D.establishes(g, "ask_the_registrar")[0],
            "so_it_WOULD_have_been_available_unfiltered": "ask_the_registrar" in unfiltered,
            "BUT_IT_IS_NEVER_PROPOSED": "ask_the_registrar" not in offered,
            "AND_NEVER_APPEARS_IN_A_PROOF":
                "ask_the_registrar" not in [n for n, _b in Q.steps_of(g, ans)],
            "AND_WITHOUT_THE_BAR_THE_QUESTION_DIES_ON_IT": _without_the_purity_bar_it_raises()}


def _without_the_purity_bar_it_raises() -> bool:
    """Plant the removal of the purity bar and confirm the question becomes unanswerable.

    ⚠ This is an in-harness version of the probe §7 asks for, kept because the key it guards was a **false
    green** first: with the bar removed the search still returned a proof naming the pure function, so
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
        return False                                        # it answered anyway: the probe proves nothing
    except DP.Imagined:
        return True
    except Exception:
        return False
    finally:
        Q.derivations = real


def check_unknown_is_not_no_unless_you_say_so():
    """⭐ Three answers, and `unknown` is the honest default. A search that found no derivation has learned
    about its own library, not about the world - so only an explicit closed-world STANCE turns that into
    `no`. Refutation is the separate, stronger claim: something incompatible holds NOW.

    ⚠ The stance is a parameter rather than a constant because it is an opinion, which is the same reason
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
    """Join CNL lines. ⚠ Written this way on purpose: an earlier version of these checks embedded `\n`
    escapes inside generated source and they collapsed into real newlines, producing an unterminated
    string literal. Building the text from parts has no escapes to get wrong."""
    return "\n".join(parts)


_BODY = "    paul.mortal = true"


def check_one_grammar_three_verbs():
    """⭐⭐ A question is a goal, so `goal`, `ask` and `why` share ONE grammar and one node shape. The
    constraints parse identically; only the recorded verb differs, because which speech act something was
    is genuinely not recoverable from what it says.

    ⚠ Vacuity guard: the two blocks must produce the SAME constraints, or "one grammar" is a claim about
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
    """⭐ "Why" means *find a causal explanation*, and the only honest source is what really ran. Three
    situations, kept apart on purpose: derived here (a cause), true but given (no cause to give), and not
    true at all (nothing to explain).

    ⚠⚠ THE ABSENT FOURTH BEHAVIOUR IS THE POINT. For a fact that already holds, a fresh search would
    happily produce "here is a way this could follow" - a fine answer to a different question and a lie as
    an account of history. `AND_INVENTS_NO_DERIVATION` asserts the engine says it does not know rather than
    manufacturing one, which is the failure that would make every explanation untrustworthy.

    ⚠ Vacuity guard: `settle` must record on the thread, or the first case degrades into the second
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
    """⭐ The hook the live pages are built on. It reports what the search does; it must not change it.

    ⚠ THE LOAD-BEARING KEY IS `identical_plan`. A watcher that perturbed the search would make every
    animated explanation a description of a *different* run than the one a user gets untraced - the exact
    failure this project keeps catching in other forms.

    ⚠⚠ **The first version of this check compared IMAGINED-STEP COUNTS, and it was wrong — the search is
    tie-break nondeterministic.** Two identical searches on fresh graphs, in one process, at a fixed hash
    seed, imagine 2 or 3 states (measured: 17 and 23 out of 40). Node ids shift between runs, mapping
    enumeration order follows, and the stable frontier sort then breaks ties differently. The PLAN is
    invariant; the number of states considered on the way to it is not. So a step-count comparison was
    reporting engine nondeterminism as a tracing defect - a check that fails for a true reason it does not
    name is barely better than one that passes for a false one.

    ⚠ `refuse` events matter most and are the easiest to omit: a pruned action leaves NO trace anywhere
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
    """⭐ A type was the last thing on the surface that could only be authored by calling Python, which is
    exactly the "reach past the surface and write graph structure" `intake.py` says must never happen.

    Vacuity guard: the round trip is compared to the AUTHORED text, not to a re-render of itself, so a
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
    """⭐⭐ **The one-level limit is gone.** `README.md` recorded it as an honest limit: a schema checked a
    label's targets by graph KIND and could say nothing about what those targets were, so "on a block which
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
    """⚠ Recursion into a target's schema makes a cycle in the DATA reachable — two people who are each
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
    """⭐⭐ The demand a per-label requirement structurally cannot express: not *what a label holds* but
    *two places reached from the same subject agreeing*. Both sides are `path.py` references.

    ⚠ `==` compares VALUES and `is` compares IDENTITIES — the position deciding how the last segment of
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
    """⚠ Once a demand is a RANGE, "the subtype demands everything the supertype does" stops being dict
    equality. A type narrowing its base's range must still be a subtype, or every widened type would stop
    subsuming its own base and `function.producers` would quietly lose candidates.

    ⚠ Undecidable cases answer **False** on purpose — a lost candidate is recoverable, an unsound one is
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
    """⭐ The path grammar existed three times, undeclared — `driver.role_node`'s private regex,
    `intake`'s hand-split on the first dot, and the dotted roles `establishes` emitted. One module now.

    ⚠ **The composition finding, and it was a live silent defect.** `a.wheel[1].pressure = 3` in a goal
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


# ⚠ THE ENTRY POINT MUST BE THE LAST THING IN THIS FILE. `_checks()` reads `globals()` at call time,
# so any check defined BELOW this block is simply not executed - the count stays put and the report looks
# healthy. That is the same false-green `_checks()` own docstring records, one level up, and it bit again
# when the query checks were appended after it.
if __name__ == "__main__":
    print(report())
