"""PROBE — what happens to things a user SAYS to an agentic coding assistant?

The question is not "does the CNL parse this English". It is the one `not_supported.md` asks:

> **does the utterance reach something the engine can actually EXECUTE**, and if so, by what route?

So each case below is pushed all the way through — authored as CNL, then planned, then carried out —
and the verdict records where it stopped. Four places it can stop, and they are very different failures:

| verdict | means |
|---|---|
| `RUNS`     | authored, planned, carried out; the world moved |
| `PARSES`   | the parser accepted it and nothing downstream can use it |
| `REFUSED`  | the parser said no, with a reason |
| `NO FORM`  | there is nothing to write; the utterance cannot be started |

⚠ `PARSES` is the interesting one and the reason this probe exists rather than a parser test.
"""
from __future__ import annotations
import pathlib
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import (asm, criterion as CR, driver as D, execution as X, intake as I,
                            thread as T, types as TY)
from microfunctions.graph import new_graph
from microfunctions.types import declare_type, is_a


def _lines(*ls):
    return "\n".join(ls)


# --- THE WORLD ----------------------------------------------------------------------------------------
# A repo, three source files, a test suite. Deliberately shaped like the garage: every action is a CAST,
# so a precondition is a parameter type and an effect is a return type, and `plan.py` chains them.

LIBRARY = _lines(
    "# Read a file into the working set. Nothing may be edited before it has been read.",
    "fn read_file(f: file) -> read_file:",
    '    SET F(f) "read" true',
    "",
    "# Edit a file. Takes a file that has been READ - that is the precondition, as a parameter type.",
    "fn edit_file(f: read_file) -> edited_file:",
    '    SET F(f) "edited" true',
    "",
    "# Run the linter over one file.",
    "fn lint(f: edited_file) -> linted_file:",
    '    SET F(f) "linted" true',
    "",
    "# Run the test suite.",
    "fn run_tests(r: repo) -> tested_repo:",
    '    SET F(r) "tested" true',
    "",
    "# Commit. Only a repo whose tests have been run.",
    "fn commit(r: tested_repo) -> committed_repo:",
    '    SET F(r) "committed" true',
)


def world():
    g = new_graph()
    declare_type(g, "file", attrs={"kind_of": "file"})
    declare_type(g, "read_file", base="file", attrs={"read": True})
    declare_type(g, "edited_file", base="read_file", attrs={"edited": True})
    declare_type(g, "linted_file", base="edited_file", attrs={"linted": True})
    declare_type(g, "repo", attrs={"kind_of": "repo"})
    declare_type(g, "tested_repo", base="repo", attrs={"tested": True})
    declare_type(g, "committed_repo", base="tested_repo", attrs={"committed": True})
    asm.load_text(g, LIBRARY)

    repo = g.mint("chunk", kind_of="repo", label="repo")
    g.link("root", "has", repo)
    files = {}
    for name, size in (("parser", 120), ("driver", 940), ("vendor_lib", 300)):
        f = g.mint("chunk", kind_of="file", label=name, size=size)
        g.link("root", "has", f)          # resolvable by name from a goal block
        g.link(repo, "file", f)
        files[name] = f
    return g, repo, files


# --- THE HARNESS --------------------------------------------------------------------------------------
CASES = []


def case(utterance, note=""):
    def deco(fn):
        CASES.append((utterance, note, fn))
        return fn
    return deco


def _try_author(g, *texts):
    """Author every block; return None on success or the refusal message."""
    for t in texts:
        try:
            I.read(g, t)
        except Exception as e:
            return f"{type(e).__name__}: {e}"
    return None


def _plan_and_do(g, goal, subject, **kw):
    got = D.pursue(g, goal, T.open_thread(g), subject, max_steps=300, max_depth=8, **kw)
    if not got["found"]:
        return False, ()
    plan = D.plan_steps(g, got)
    X.execute(g, got["workbench"], got["frame"])
    return True, plan


def run():
    width = 74
    for utterance, note, fn in CASES:
        print("\n" + "=" * width)
        print(f"  “{utterance}”")
        if note:
            print(f"  {note}")
        print("-" * width)
        try:
            fn()
        except Exception:
            print("  !! probe itself blew up:")
            traceback.print_exc()


def verdict(tag, detail=""):
    print(f"  >> {tag:8} {detail}")


# ======================================================================================================
#  THE UTTERANCES
# ======================================================================================================

@case("Edit driver.py.",
      "BASELINE — does anything chain at all?")
def c1():
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal edit it:", "    driver is a edited_file"))
    ok, plan = _plan_and_do(g, goal, files["driver"])
    verdict("RUNS" if ok else "STUCK", f"plan={plan}  edited={g.attr(files['driver'], 'edited')}")


@case("To sort out a file: read it, then edit it, then lint it. Sort out driver.py.",
      "YOUR COOKING EXAMPLE — a method, and the goal that invokes it.")
def c2():
    g, repo, files = world()
    bad = _try_author(g, _lines(
        "method sort out a file:",
        "    handles type linted_file",
        "    because a file is read before it is changed and linted after",
        "    step subject.read = true",
        "    step subject.edited = true",
        "    step subject.linted = true"))
    if bad:
        return verdict("REFUSED", bad)
    goal = I.read_goal(g, _lines("goal sort it:", "    driver is a linted_file"))
    ok, plan = _plan_and_do(g, goal, files["driver"])
    verdict("RUNS" if ok else "STUCK", f"plan={plan}")


@case("Before editing a file, read it.",
      "ORDERING KNOWLEDGE — three places it could live; which accept it?")
def c3():
    g, repo, files = world()
    for label, text in (
        ("as a guideline", _lines("prefer reading first:", "    action read_file",
                                  "    because nothing may be changed unseen")),
        ("as a criterion", _lines("criterion read before editing:",
                                  "    wants attr edited",
                                  "    unless subject.read = true",
                                  "    do read_file f = subject",
                                  "    because nothing may be changed unseen")),
    ):
        bad = _try_author(g, text)
        verdict("PARSES" if not bad else "REFUSED", f"{label}: {bad or 'accepted'}")
    verdict("NOTE", "and it is ALSO already said by `fn edit_file(f: read_file)` — a parameter type")


@case("Never touch vendor_lib.",
      "A PROHIBITION over the route, not the world.")
def c4():
    # (a) the prohibition must NOT over-prune work that has nothing to do with it
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal sort out the driver:",
                                 "    driver is a linted_file",
                                 "    never touch vendor_lib"))
    ok, plan = _plan_and_do(g, goal, files["driver"])
    verdict("RUNS" if ok else "STUCK", f"unrelated work still planned: plan={plan}")
    # (b) ...and must prune work that DOES touch it
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal sort out the vendor:",
                                 "    vendor_lib is a linted_file",
                                 "    never touch vendor_lib"))
    ok, plan = _plan_and_do(g, goal, files["vendor_lib"])
    verdict("RUNS" if ok else "STUCK", "forbidden work correctly unreachable" if not ok
            else f"⚠ PROHIBITION LEAKED: plan={plan}")


@case("Run the tests, then commit.",
      "SEQUENCE AT THE TOP LEVEL — no method authored; the types alone should order it.")
def c5():
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal ship it:", "    repo is a committed_repo"))
    ok, plan = _plan_and_do(g, goal, repo)
    verdict("RUNS" if ok else "STUCK", f"plan={plan}")


@case("List all the files in the repo.",
      "THE FINDER — `not_supported.md` G0.")
def c6():
    g, repo, files = world()
    for label, text in (
        ("as a goal", _lines("goal list them:", "    repo.files known")),
        ("as a question", _lines("what they are:", "    repo")),
        ("as a plural wh", _lines("which files:", "    repo")),
    ):
        bad = _try_author(g, text)
        verdict("PARSES" if not bad else "REFUSED", f"{label}: {bad or 'accepted'}")
    print("     the capability EXISTS in Python:", TY.instances(g, "file"))

    # ⚠⚠ AND THE `known` FORM IS WORSE THAN A REFUSAL. `known` asks whether an ATTRIBUTE SLOT has been
    # looked at (`g.attr(here, key) is not UNKNOWN`), but `files` is an EDGE LABEL. `g.attr(repo,
    # "files")` is None, not UNKNOWN, so the constraint is satisfied VACUOUSLY: the system reports the
    # repo's files as known, with an empty plan, having never looked. Same shape as the `has 1 ^contains`
    # bug `cnl.md` §3 records — a label read in a position where labels do not apply, silently.
    # ✅ FIXED. Both shapes now refuse in `goal.require_known`, with a check that plants a bug against
    # each route. What the refusal does NOT do is grant the capability — "which files are in the repo"
    # still has no form, and now says so out loud instead of answering it wrongly.
    g2, repo2, _ = world()
    for shape in ("repo.file known", "repo.files known"):
        try:
            I.read_goal(g2, _lines("goal list them:", "    " + shape))
            verdict("⚠ FALSE", f"`{shape}` still accepted — the vacuous truth is back")
        except Exception as e:
            verdict("REFUSED", f"`{shape}`: {str(e)[:78]}…")


@case("For each file in the repo, lint it.",
      "THE DISTRIBUTIVE STEP — `plural_step.md`.")
def c7():
    g, repo, files = world()
    for label, text in (
        ("each ... ", _lines("goal lint them:", "    each file is a linted_file")),
        ("all ...", _lines("goal lint them:", "    all files are linted")),
        ("universal by double negation", _lines("type unlinted_file:", "    kind_of = \"file\"",
                                                "    linted != true")),
    ):
        bad = _try_author(g, text)
        verdict("PARSES" if not bad else "REFUSED", f"{label}: {bad or 'accepted'}")
    bad = _try_author(g, _lines("type tidy_repo:", "    kind_of = \"repo\"",
                                "    has no file each a unlinted_file"))
    verdict("PARSES" if not bad else "REFUSED", f"the not-exists-not paraphrase: {bad or 'accepted'}")

    # ⚠⚠ THE FIRST VERSION OF THIS CASE REPORTED A CAPABILITY GAP HERE, AND IT WAS THE PROBE'S OWN
    # DEPTH BUDGET. Nine casts are needed (3 files x read/edit/lint) and `max_depth` was 8. It plans
    # fine at 12. Recorded because it is exactly the failure `not_supported.md` warns about from the
    # other side: an unmeasured verdict read as a gap.
    goal = I.read_goal(g, _lines("goal tidy it:", "    repo is a tidy_repo"))
    got = D.pursue(g, goal, T.open_thread(g), repo, max_steps=2000, max_depth=12)
    verdict("RUNS" if got["found"] else "STUCK",
            f"plan={D.plan_steps(g, got) if got['found'] else ()}")
    verdict("COST", f"{got.get('steps')} states imagined for 9 steps over 3 files "
                    f"— the planner does not know the files are independent subproblems")


@case("If the tests have been run, commit.",
      "CONDITIONAL — action-side vs fact-side.")
def c8():
    g, repo, files = world()
    bad = _try_author(g, _lines("method commit when tested:",
                                "    handles attr committed",
                                "    when tested_repo",
                                "    because there is no point committing untested work",
                                "    step subject.committed = true"))
    verdict("PARSES" if not bad else "REFUSED", f"as a method guard (what to DO): {bad or 'accepted'}")
    bad = _try_author(g, _lines("goal ship it:", "    if repo is a tested_repo then repo is a committed_repo"))
    verdict("PARSES" if not bad else "REFUSED", f"as a conditional GOAL: {bad or 'accepted'}")


@case("Keep the tests passing.",
      "MAINTENANCE — `not_supported.md` G3.")
def c9():
    g, repo, files = world()
    for label, text in (
        ("keep ...", _lines("goal keep them green:", "    keep repo is a tested_repo")),
        ("as an achievement", _lines("goal green:", "    repo is a tested_repo")),
    ):
        bad = _try_author(g, text)
        verdict("PARSES" if not bad else "REFUSED", f"{label}: {bad or 'accepted'}")


@case("Why did you edit driver.py?",
      "EXPLANATION over something already done.")
def c10():
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal edit it:", "    driver is a edited_file"))
    _plan_and_do(g, goal, files["driver"])
    bad = _try_author(g, _lines("why it changed:", "    driver is a edited_file"))
    verdict("PARSES" if not bad else "REFUSED", bad or "accepted")


@case("Commit with the message \"fix the parser\".",
      "AN ARGUMENT THAT IS CONTENT, not a referent.")
def c11():
    g, repo, files = world()
    bad = _try_author(g, _lines("goal ship it:", "    repo.message = \"fix the parser\""))
    verdict("PARSES" if not bad else "REFUSED", bad or "accepted")


@case("After you edit a file, lint THAT file.",
      "THE SEAM — a later step naming what an earlier step touched.")
def c12():
    g, repo, files = world()
    bad = _try_author(g, _lines("method edit then lint:",
                                "    handles type edited_file",
                                "    because a change is linted before anyone sees it",
                                "    step subject.edited = true",
                                "    step subject.linted = true"))
    verdict("PARSES" if not bad else "REFUSED", f"same subject: {bad or 'accepted'}")
    bad = _try_author(g, _lines("method lint what was edited:",
                                "    handles type edited_file",
                                "    step subject.edited = true",
                                "    step the file edited by step 1 is a linted_file"))
    verdict("PARSES" if not bad else "REFUSED", f"a step naming an EARLIER STEP's result: {bad or 'accepted'}")

    # ✅ THE REACHABLE HALF IS FIXED: a step can now name a THIRD individual, via the binder lifted from
    # `criterion`. What is still absent is naming an earlier step's *result* — which is a different thing,
    # and needs the outcome/branch form this probe's last case is about.
    g2, repo2, files2 = world()
    bad = _try_author(g2, _lines("method lint the repo's file:",
                                 "    handles attr committed",
                                 "    some f in subject by file",
                                 "    because nothing ships unless its code was linted",
                                 "    step f is a linted_file",
                                 "    step subject.committed = true"))
    verdict("PARSES" if not bad else "REFUSED", f"a step about a THIRD individual: {bad or 'accepted'}")
    if not bad:
        from microfunctions import method as M, goal as GO
        m = M.methods(g2)[0]
        goal = I.read_goal(g2, _lines("goal ship it:", "    repo.committed = true"))
        pairs = M.applicable(g2, goal, under="root")
        subs = M.decompose(g2, m, goal, pairs[0][1])
        raised = [GO.describe_constraint(g2, c) for s in subs for c in GO.constraints(g2, s)]
        verdict("RUNS", f"subgoals raised: {raised}")


@case("Run the tests. If any fail, fix the file, then run them again.",
      "⭐ YOUR SECOND EXAMPLE — a step whose SUCCESSOR depends on an earlier step's OUTCOME.")
def c14():
    g, repo, files = world()
    # The engine HAS outcome branching: `mocks` declares one function as a possible outcome of another.
    asm.load_text(g, _lines(
        "# One possible outcome of running the tests.",
        "fn tests_pass(r: repo) -> tested_repo mocks run_tests:",
        '    SET F(r) "tested" true',
        '    SET F(r) "failing" false',
        "",
        "# ...and the other.",
        "fn tests_fail(r: repo) -> tested_repo mocks run_tests:",
        '    SET F(r) "tested" true',
        '    SET F(r) "failing" true'))
    verdict("EXISTS", "outcome branching is in the ENGINE: `mocks` parsed, two outcomes declared")
    for label, text in (
        ("a step conditioned on an outcome", _lines("method test and fix:",
                                                    "    handles attr tested",
                                                    "    step subject.tested = true",
                                                    "    if subject.failing = true then step driver is a edited_file")),
        ("a method guarded on the outcome", _lines("method fix what failed:",
                                                   "    handles attr failing",
                                                   "    when tested_repo",
                                                   "    because a red suite is worth a second look",
                                                   "    step subject.tested = true")),
        ("...and REPEAT until green", _lines("method until green:",
                                             "    handles attr tested",
                                             "    step subject.tested = true",
                                             "    repeat until subject.failing = false")),
    ):
        bad = _try_author(g, text)
        verdict("PARSES" if not bad else "REFUSED", f"{label}: {bad or 'accepted'}")


@case("Do it in at most three steps.",
      "A BUDGET.")
def c13():
    g, repo, files = world()
    goal = I.read_goal(g, _lines("goal sort it:", "    driver is a linted_file", "    at most 3 steps"))
    ok, plan = _plan_and_do(g, goal, files["driver"])
    verdict("RUNS" if ok else "STUCK", f"plan={plan} (3 casts needed, budget 3)")
    g2, repo2, files2 = world()
    goal2 = I.read_goal(g2, _lines("goal sort it:", "    driver is a linted_file", "    at most 2 steps"))
    ok2, plan2 = _plan_and_do(g2, goal2, files2["driver"])
    verdict("RUNS" if ok2 else "STUCK", f"plan={plan2} (budget 2 — should NOT be reachable)")


if __name__ == "__main__":
    run()
