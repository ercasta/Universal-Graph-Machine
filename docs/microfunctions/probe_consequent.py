"""PROBE — is there ONE right-hand side, or four?

`islands.md` §5 item 2 says *collapse `step` / `do` / a memory write / **effects** into
`conditions → consequent`*. Before building that, measure the claim it rests on:

> Every rule in this engine is `conditions -> consequent`. Only the consequent and the executor differ.
> (`islands.md` §3(e))

If that is true, the four right-hand sides should differ **only** in what runs them — and each ought to be
sayable in the others' place, or the split is real and the collapse is wishful. So each case below takes
one right-hand side and tries to write it where a *different* family's conditions already are, pushed to
authoring and, where it parses, to execution.

⚠⚠ **Every case carries a CONTROL that must light up.** `islands.md` §3(g): a measurement whose control
does not light up is not a measurement — three of last session's claims were assembled from correct
components and were false. Here the failure mode is obvious: a probe where *everything* is refused
measures nothing but that the author mistyped the CNL.

| verdict | means |
|---|---|
| `SAME`     | the two families accept the same right-hand side; the split is already cosmetic |
| `NO FORM`  | there is nothing to write — it can only be said in one family |
| `ASYMMETRY`| both accept something, and what they accept differs in a way nobody chose |
| `INFERRED` | it exists, but nothing *declares* it; it is read back off a body |
"""
from __future__ import annotations
import pathlib
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import (asm, criterion as CR, driver as D, intake as I, method as M,
                            thread as T)
from microfunctions.graph import new_graph
from microfunctions.types import declare_type


def _thread(g):
    return T.open_thread(g)


def _styles(g, got):
    """The arguments each planned call was actually given, by label. ⚠ This, not `found`, is where the two
    routes differ — see the vacuity note in c1."""
    if not got.get("found"):
        return ()
    from microfunctions import workbench as W
    out = []
    for f in got["plan"][1:]:
        tr = g.target(f, "via")
        if tr is None:
            continue
        out.append({g.attr(b, "param"): g.attr(W.image_of(g, g.target(b, "mapping")), "label")
                    for b in g.targets(tr, "arg")})
    return tuple(out)


def _lines(*ls):
    return "\n".join(ls)


# --- THE WORLD ----------------------------------------------------------------------------------------
# Deliberately the SAME shape as `probe_agentic_coding`'s: a repo, files, casts that chain. Reusing the
# shape keeps this probe's negatives comparable with that one's, which is how #1 and #14 over there were
# recognised as false successes rather than as new gaps.

LIBRARY = _lines(
    "fn read_file(f: file) -> read_file:",
    '    SET F(f) "read" true',
    "",
    "fn edit_file(f: read_file) -> edited_file:",
    '    SET F(f) "edited" true',
    "",
    "fn lint(f: edited_file) -> linted_file:",
    '    SET F(f) "linted" true',
    "",
    # ⭐ The effects case needs a body whose writes are NOT statically readable: a tool call.
    "fn scan_dir(d: folder) -> folder:",
    "    DISPATCH R(out) \"list_dir\" F(d)",
    '    SET F(d) "scanned" true',
    "",
    # ⚠⚠ TWO FAILED ATTEMPTS AT A NON-VACUOUS OPERATOR FOR c1, LEFT HERE BECAUSE THE FAILURE IS THE
    # FINDING. First `tidy` was a bare tool call, on the theory that search could not select an operator
    # whose effect is on the far side of a DISPATCH — but then nothing can IMAGINE it either, so it needs
    # a mock, and `establishes` unions the mock's effects straight back in. Then it gained a second
    # parameter, on the theory that search would have to guess the style guide — it guessed the same one.
    # There is no operator a criterion can name that search cannot select, and no binding it can name
    # that enumeration cannot produce. See c1.
    "fn tidy(f: file, style: style_guide) -> file:",
    "    DISPATCH R(out) \"tidy\" F(f)",
    "",
    "fn tidy_ok(f: file, style: style_guide) -> file mocks tidy:",
    '    SET F(f) "tidied" true',
)


def world():
    g = new_graph()
    declare_type(g, "file", attrs={"kind_of": "file"})
    declare_type(g, "read_file", base="file", attrs={"read": True})
    declare_type(g, "edited_file", base="read_file", attrs={"edited": True})
    declare_type(g, "linted_file", base="edited_file", attrs={"linted": True})
    declare_type(g, "folder", attrs={"kind_of": "folder"})
    declare_type(g, "person", attrs={"kind_of": "person"})
    declare_type(g, "style_guide", attrs={"kind_of": "style_guide"})
    asm.load_text(g, LIBRARY)

    folder = g.mint("chunk", kind_of="folder", label="src")
    owner = g.mint("chunk", kind_of="person", label="ada", name="ada")
    g.link("root", "has", folder)
    g.link("root", "has", owner)
    for name in ("house_style", "legacy_style", "draft_style"):
        sg = g.mint("chunk", kind_of="style_guide", label=name)
        g.link("root", "has", sg)
    g.link(owner, "prefers", g.mint("chunk", kind_of="style_guide", label="ada_style"))
    files = {}
    for name in ("parser", "driver"):
        f = g.mint("chunk", kind_of="file", label=name, size=100)
        g.link("root", "has", f)
        g.link(folder, "file", f)
        g.link(f, "owner", owner)
        files[name] = f
    return g, folder, owner, files


# --- THE HARNESS ---------------------------------------------------------------------------------------
CASES = []


def case(claim, note=""):
    def deco(fn):
        CASES.append((claim, note, fn))
        return fn
    return deco


def author(g, text):
    """Author one block; return None on success or the refusal message."""
    try:
        I.read(g, text)
    except Exception as e:
        return f"{type(e).__name__}: {e}"
    return None


def run():
    width = 78
    for claim, note, fn in CASES:
        print("\n" + "=" * width)
        print(f"  {claim}")
        if note:
            print(f"  {note}")
        print("-" * width)
        try:
            fn()
        except Exception:
            print("  !! probe itself blew up:")
            traceback.print_exc()


def verdict(tag, detail=""):
    print(f"  >> {tag:10} {detail}")


def control(ok, detail=""):
    print(f"  {'++ CONTROL  ' if ok else '!! CONTROL DARK '}{detail}")


# ========================================================================================================
#  1. A METHOD STEP AND A CRITERION ACTION — can either be written where the other is?
# ========================================================================================================
@case("A method decomposes into propositions. Can one rung be an ACTION?",
      "'read it, then run the linter on it' — the second rung IS a tool call, not a state to reach.")
def c1():
    g, folder, owner, files = world()
    control(author(g, _lines("method sort it out:",
                             "    handles attr linted",
                             "    step subject.read = true",
                             "    step subject.linted = true")) is None,
            "a method of two PROPOSITION steps authors fine")
    for label, line in (("`do` inside a step", "    step do lint f = subject"),
                        ("a bare `do` line", "    do lint f = subject"),
                        ("an action named as a step", "    step lint subject")):
        bad = author(g, _lines("method lint it:", "    handles attr linted", line))
        verdict("PARSES" if bad is None else "NO FORM", f"{label}: {bad or 'accepted'}")

    # ⭐⭐ THE WORKAROUND, probed before the gap is believed — the same discipline that turned c3 into
    # sugar. A rung does not have to CARRY the call: it can state the proposition and let a criterion
    # supply the call. If that composes, "a method rung cannot be an action" is a surface convenience
    # rather than a capability gap, and the collapse buys much less than §5 item 2 assumes.
    #
    # ⚠⚠ **THE CONTROL WENT DARK TWICE AND THE HONEST ANSWER IS THAT THIS IS NOT MEASURABLE HERE.**
    #   Attempt 1 — three chaining casts: search alone found the SAME plan, so `found` proved nothing.
    #   Attempt 2 — a tool-call operator with a guessable second argument: search alone found the same
    #   plan AND bound the same argument, so the binding proved nothing either.
    # The reason is structural rather than a bad world: **`establishes` unions in each mock's effects**,
    # so every operator a criterion can name is one means-ends search could already select, and every
    # binding a criterion can name is one enumeration could already produce. So the two consequents do
    # **not** differ in what they can REACH. They differ in *who chooses, how fast, and whether the
    # choice can be explained* — which is a claim about executors, and is exactly what §3(e) predicted.
    g2, _, _, files2 = world()
    bad = author(g2, _lines("method read then tidy:",
                            "    handles attr tidied",
                            "    step subject.read = true",
                            "    step subject.tidied = true"))
    bad = bad or author(g2, _lines("criterion tidying is done with the tidier:",
                                   "    wants attr tidied",
                                   "    do tidy f = subject, style = subject.owner.prefers"))
    verdict("AUTHORED" if bad is None else "NO FORM", f"rung states the state, criterion names the call: "
                                                      f"{bad or 'both accepted'}")
    if bad is None:
        goal = I.read_goal(g2, _lines("goal tidy the driver:", "    driver.tidied = true"))
        got = D.pursue(g2, goal, _thread(g2), files2["driver"], max_steps=300, max_depth=8,
                       propose=CR.decide(g2, goal, files2["driver"]))
        g3, _, _, files3 = world()
        goal3 = I.read_goal(g3, _lines("goal tidy the driver:", "    driver.tidied = true"))
        got3 = D.pursue(g3, goal3, _thread(g3), files3["driver"], max_steps=300, max_depth=8)
        verdict("NOT MEASURABLE",
                f"authored: plan={D.plan_steps(g2, got)} bindings={_styles(g2, got)}")
        control(_styles(g3, got3) != _styles(g2, got),
                f"search ALONE: plan={D.plan_steps(g3, got3)} bindings={_styles(g3, got3)} "
                f"— identical, so nothing above is attributable to the criterion")


@case("A criterion names an action. Can it name a PROPOSITION instead?",
      "'when the file is big, it needs linting' — expert judgement about a STATE, not a call.")
def c2():
    g, folder, owner, files = world()
    control(author(g, _lines("criterion big files get linted:",
                             "    wants attr linted",
                             "    when subject.size > 50",
                             "    do lint f = subject")) is None,
            "a criterion with a `do` authors fine")
    for label, line in (("a proposition line", "    subject.linted = true"),
                        ("`step` inside a criterion", "    step subject.linted = true"),
                        ("`achieve`", "    achieve subject.linted = true")):
        bad = author(g, _lines("criterion big files are linted:",
                               "    wants attr linted",
                               "    when subject.size > 50",
                               line))
        verdict("PARSES" if bad is None else "NO FORM", f"{label}: {bad or 'accepted'}")


# ========================================================================================================
#  2. THE REFERENCE LANGUAGE — the same words in two right-hand sides
# ========================================================================================================
@case("Both right-hand sides refer to things. Do they refer the SAME way?",
      "`criterion.resolve_ref` documents four forms at any depth. A step calls `role()`.")
def c3():
    g, folder, owner, files = world()
    # The CONTROL: the criterion side really does reach two hops and a named individual.
    for label, ref in (("a role", "subject"),
                       ("a path of depth 1", "subject.owner"),
                       ("a named individual", "the ada")):
        bad = author(g, _lines(f"criterion c_{label.replace(' ', '_')}:",
                               "    wants attr linted",
                               f"    do lint f = {ref}"))
        control(bad is None, f"criterion `do` takes {label}: {bad or 'accepted'}")

    # The same three, in a step's subject position.
    for label, ref in (("a role", "subject"),
                       ("a path of depth 1", "subject.owner"),
                       ("a named individual", "the ada")):
        bad = author(g, _lines(f"method m_{label.replace(' ', '_')}:",
                               "    handles attr linted",
                               f"    step {ref} is a person"))
        verdict("PARSES" if bad is None else "NO FORM", f"step subject takes {label}: {bad or 'accepted'}")

    # ⭐⭐ THE CORRECTION. The refusal above NAMES its own workaround — "draw a further role with
    # `some <name> in <ref> by <link>`" — so before calling this an island, write the workaround and see
    # whether it reaches the same place. If it does, the asymmetry is SUGAR and the surface is a
    # convenience question, not a capability one. (`plural_step.md`: the universal was sugar too.)
    bad = author(g, _lines("method m_drawn:",
                           "    handles attr linted",
                           "    some o in subject by owner",
                           "    step o is a person"))
    verdict("SUGAR" if bad is None else "ISLAND",
            f"the SAME reach via an explicit draw: {bad or 'accepted'}")
    # ...and does it reach the same node? Push past the parser.
    if bad is None:
        m = [x for x in M.methods(g) if g.attr(x, "name") == "m_drawn"][0]
        goal = I.read_goal(g, _lines("goal lint it:", "    parser.linted = true"))
        from microfunctions import goal as G
        c = G.unmet(g, goal)[0]
        raised = M.decompose(g, m, goal, c)
        subj = g.target(G.constraints(g, raised[0])[0], "subject")
        verdict("SUGAR" if subj == owner else "ISLAND",
                f"and the raised subgoal is about {g.attr(subj, 'label')!r} "
                f"(wanted 'ada' — the file's owner, two hops from the constraint)")


# ========================================================================================================
#  3. EFFECTS — the fourth right-hand side, and the one nobody can write
# ========================================================================================================
@case("An operator's effects ARE a consequent. Can a domain declare them?",
      "`islands.md` A: operators are authorable only in `.mf` assembly. Effects are read off a body.")
def c4():
    g, folder, owner, files = world()
    readable, unknown = D.establishes(g, "lint")
    control(bool(readable) and not unknown,
            f"a plain body reads completely: {readable} unknown={set(unknown)}")

    readable2, unknown2 = D.establishes(g, "scan_dir")
    verdict("INFERRED", f"scan_dir: effects={readable2} unknown={set(unknown2)}")
    verdict("INFERRED" if unknown2 else "READ",
            "a tool call is unreadable statically, and there is no form that says what it does")

    # ⚠ Only ONE thing is worth asking here: is there a surface that attaches a declared effect to a
    # FUNCTION? (A `method scan_dir:` block parses, but naming a method after an operator says nothing
    # about that operator — that would be measuring the author's choice of label, not the engine.)
    bad = author(g, _lines("effect scan_dir:", "    d.scanned = true"))
    verdict("PARSES" if bad is None else "NO FORM", f"an `effect` block: {bad or 'accepted'}")


# ========================================================================================================
#  4. A MEMORY WRITE — the third right-hand side named in §5 item 2
# ========================================================================================================
@case("`remember` and `learn` are two more right-hand sides. Is there a verb?",
      "islands.md H: four things want a surface and two do not fit `<verb> <label>:` + body.")
def c5():
    g, folder, owner, files = world()
    control("criterion" in I.VERBS and "method" in I.VERBS,
            f"the verb list is reachable and populated: {len(I.VERBS)} verbs")
    for verb in ("remember", "learn", "forbid", "effect", "rule"):
        verdict("EXISTS" if verb in I.VERBS else "NO FORM", f"verb `{verb}`")


# ========================================================================================================
#  5. THE STRUCTURE — are the two consequents the same node shape underneath?
# ========================================================================================================
@case("Underneath, is a `step` node the same kind of thing as a `does` node?",
      "If the collapse is cheap, the two should already differ only by a tag.")
def c6():
    g, folder, owner, files = world()
    author(g, _lines("method sort it out:",
                     "    handles attr linted",
                     "    step subject.linted = true"))
    author(g, _lines("criterion lint big ones:",
                     "    wants attr linted",
                     "    when subject.size > 50",
                     "    do lint f = subject"))
    m = M.methods(g)[0]
    c = CR.criteria(g)[0]
    s = M.steps_of(g, m)[0]
    d = CR.action_of(g, c)
    verdict("SHAPE", f"step node: attrs={dict(g.attrs.get(s, {}))}")
    verdict("SHAPE", f"does node: attrs={dict(g.attrs.get(d, {}))} "
                     f"args={[dict(g.attrs.get(a, {})) for a in g.targets(d, 'arg')]}")
    control(g.kind(s) != g.kind(d), "they are different node kinds, so the tag does not exist yet")


# ========================================================================================================
#  6. ⚠⚠ NOT A CONSEQUENT QUESTION — a defect found while chasing c1's control
# ========================================================================================================
@case("⚠⚠ `do f x = the <name>` authors fine and can NEVER speak, in silence.",
      "Found while chasing c1's control. STILL OPEN — its two siblings were closed, see below.")
def c7():
    g, folder, owner, files = world()
    # `resolve_ref`'s four forms include `the <name>`, and `_ref` validates it AT AUTHORING TIME — which
    # is `intake._ref`'s whole stated reason for existing: refuse a bad reference where it is written
    # rather than "report a typo from inside a search, thousands of steps later, AS SILENCE".
    control(author(g, _lines("criterion tidy to the legacy style:",
                             "    wants attr tidied",
                             "    do tidy f = subject, style = the legacy_style")) is None,
            "it authors clean — `the legacy_style` names exactly one thing in the world")

    goal = I.read_goal(g, _lines("goal tidy the driver:", "    driver.tidied = true"))
    search = D.open_planning(g, goal, _thread(g), files["driver"])
    from microfunctions import workbench as W
    root = W.root_frame(g, g.target(search, "workbench"))
    for c, spoke, reasons in CR.governing(g, goal, root, files["driver"]):
        verdict("SILENT" if not spoke else "SPEAKS", f"{g.attr(c, 'label')!r}: {reasons}")

    # ⭐ And the control that makes it a DEFECT rather than a design: the same criterion, differing only
    # in which individual it names, DOES speak — because `ada_style` happens to be reachable from the
    # subject and so was copied into the imagined world. Nothing at authoring time distinguishes them.
    g2, _, _, files2 = world()
    author(g2, _lines("criterion tidy to the owner's style:",
                      "    wants attr tidied",
                      "    do tidy f = subject, style = subject.owner.prefers"))
    goal2 = I.read_goal(g2, _lines("goal tidy the driver:", "    driver.tidied = true"))
    search2 = D.open_planning(g2, goal2, _thread(g2), files2["driver"])
    root2 = W.root_frame(g2, g2.target(search2, "workbench"))
    for c, spoke, reasons in CR.governing(g2, goal2, root2, files2["driver"]):
        control(spoke, f"reachable from the subject instead: {g2.attr(c, 'label')!r} spoke={spoke}")
    verdict("DEFECT", "author-time validation checks the WORLD; `speaks` checks the IMAGINED world, and "
                      "a name outside the subject's copied neighbourhood fails as ordinary silence")

    # ✅ THE TWO SIBLINGS, CLOSED. `driver.check_call` raises ONE exception for six causes and
    # `criterion._try` turns them all into silence — right for the cause it was built for (a forbidden
    # call is a *situation*), wrong for these two, which are wrong in every world for every subject.
    # `intake._action` refuses them at the line now. ⚠ Left in the probe as a REGRESSION guard: if either
    # goes back to authoring clean, this reports PARSES and the finding has quietly come undone.
    for label, line in (("an unknown function", "    do frobnicate f = subject"),
                        ("a wrong parameter set", "    do tidy f = subject")):
        bad = author(g, _lines("criterion c:", "    wants attr tidied", line))
        verdict("PARSES" if bad is None else "CLOSED", f"{label}: {bad or 'ACCEPTED — regression!'}")
    verdict("NOTE", "J differs from both: the name denotes exactly one real thing, so it is neither a "
                    "typo nor a fact about the domain — it is the workbench boundary showing through")


# ========================================================================================================
#  7. SLICE TWO — the two proposed new tags, probed BEFORE they are built
# ========================================================================================================
@case("`effect` is proposed as a third consequent. Is it SUGAR for a `mocks` declaration?",
      "islands.md A calls declared effects 'exact where `establishes` walks a body linearly'.")
def c8():
    # ⚠ The north star deliberately moved AWAY from operators carrying declarative effect descriptions,
    # and `driver.establishes` states the reason: effects read off a body "cannot fall out of date with
    # the body because it IS the body". A declared `effect` block reintroduces a second source of truth.
    # So before building one, measure what a mock — which is a body, and is already declared — leaves out.
    g, folder, owner, files = world()

    # `tidy`'s whole effect is on the far side of a DISPATCH. Statically its own body says nothing.
    from microfunctions import function as FN
    own, own_unknown = D._effects(g, "tidy", include_mocks=False)
    control(not own and own_unknown, f"the operator alone is unreadable: {own} unknown={set(own_unknown)}")

    # ...and with its mock, which DECLARES the assumed outcome.
    withm, withm_unknown = D.establishes(g, "tidy")
    verdict("SUGAR" if withm else "GAP",
            f"with its mock: {withm} — a mock IS a declared effect, written as a body")
    verdict("NOTE", f"mocks of tidy: {FN.mocks_of(g, 'tidy')}")

    # ⭐ And the load-bearing half: does the DECLARATION make the operator selectable for a goal about
    # that effect? If it does, "declared effects" is closed and island A is about something else.
    goal = I.read_goal(g, _lines("goal tidy the driver:", "    driver.tidied = true"))
    got = D.pursue(g, goal, _thread(g), files["driver"], max_steps=300, max_depth=8)
    verdict("SUGAR" if got["found"] else "GAP",
            f"and planning SELECTS it on the strength of the declaration: plan={D.plan_steps(g, got)}")

    # ⚠⚠ THE VACUITY GUARD, and it is the whole case. Not "remove the mock" — with no mock at all the
    # planner still tries the operator and the real DISPATCH escapes (see c10). Instead: keep a mock, but
    # let it declare a DIFFERENT effect. If the goal then becomes unreachable, the DECLARATION is what
    # planning was selecting on, which is exactly the claim.
    g2 = new_graph()
    declare_type(g2, "file", attrs={"kind_of": "file"})
    asm.load_text(g2, _lines("fn tidy(f: file) -> file:", "    DISPATCH R(out) \"tidy\" F(f)",
                             "",
                             "fn tidy_ok(f: file) -> file mocks tidy:",
                             '    SET F(f) "polished" true'))
    f2 = g2.mint("chunk", kind_of="file", label="driver")
    g2.link("root", "has", f2)
    goal2 = I.read_goal(g2, _lines("goal tidy the driver:", "    driver.tidied = true"))
    got2 = D.pursue(g2, goal2, _thread(g2), f2, max_steps=300, max_depth=8)
    control(not got2["found"],
            f"same operator, mock declaring a DIFFERENT effect: found={got2['found']} — unreachable, "
            f"so it really was the declaration doing the work")

    verdict("SO", "the `effect` half of island A is CLOSED by mocks. What is left is authoring the "
                  "MECHANICS — the body — which is the `.mf` surface, a different and larger thing")


@case("`record` is proposed as a fourth consequent, for `remember` / `learn`.",
      "HANDOFF §9: 'learn writes a CRITERION, so it needs no new family at all.' Can anything write one?")
def c9():
    g, folder, owner, files = world()
    # The claim to test: a rule writing a rule. If a microfunction can author a criterion, `learn` needs
    # no `record` tag — it is an ordinary `call` consequent whose function happens to author knowledge.
    from microfunctions import isa
    ops = tuple(o for o in isa.__all__ if o.isupper() and o not in ("R", "F", "I"))
    control(len(ops) > 20, f"{len(ops)} ISA opcodes enumerable, so this is a real search")

    # ⚠ THE CONTROL THAT MATTERS: the border works when called from Python. A criterion missing its
    # `wants` is refused, and refusal leaves nothing behind.
    bad = author(g, _lines("criterion half built:", "    do lint f = subject"))
    control(bad is not None, f"authored through `intake.read`, a bad criterion is refused: {bad}")

    # ⭐⭐ ...but an opcode does not go through it. NEW/SET/LINK write graph structure directly, and a
    # criterion IS graph structure — so a body that "learns" would hand-build one, bypassing every
    # refusal. That is precisely what `intake.py` says must never happen: *reach past the surface and
    # write graph structure, because then nothing can refuse it*. Demonstrated, not argued:
    # ⚠ Minted from an ACTUAL `.mf` body and invoked, not from Python — the claim is about what a
    # microfunction can do, and `NEW`'s kind operand is unconstrained (`v(a[1])`).
    from microfunctions import function as FN
    asm.load_text(g, _lines('fn learn_badly(x: file) -> file:',
                            '    NEW R(c) "criterion"',
                            '    SET R(c) "label" "smuggled in from a body"'))
    before = len(CR.criteria(g))
    FN.invoke(g, "learn_badly", {"x": files["driver"]})
    after = CR.criteria(g)
    verdict("BYPASS" if len(after) == before + 1 else "GUARDED",
            f"a body that mints kind 'criterion' is enumerated as one: {before} -> {len(after)}")
    smuggled = after[-1]
    verdict("BYPASS", f"...with no `wants` and no `do` at all: "
                      f"wants={g.attr(smuggled, 'wants_sort')} action={CR.action_of(g, smuggled)}")
    verdict("NOTE", "inert TODAY — `speaks` returns immediately when there is no action — so this is a "
                    "design hazard for how `learn` gets built, not a live hole. `.mf` is trusted "
                    "(HANDOFF §5y); the point is to decide BEFORE `learn` exists")
    verdict("SO", "`learn` is ONE decision about EXECUTION, not four surfaces: either an opcode that "
                  "authors THROUGH the refusing surface (then `learn` is an ordinary `call` and needs no "
                  "new tag), or a `record` consequent with its own executor. What it must NOT be is "
                  "NEW/SET/LINK in a body, which is authoring with the refusals switched off")


if __name__ == "__main__":
    run()
