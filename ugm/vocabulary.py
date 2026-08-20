"""What the engine reserves, and what a corpus has to borrow. (§10, §17, §22)

The user's observation, and this module exists to test it rather than agree
with it:

> Working with an open class beats traditional programming because you do not
> have to *implement* the meaning of everything. `owning` something, `selling`
> something -- you can create valid propositions and only give them a specific
> meaning later.

That is a claim with two halves, and both are measurable.

**How much does a corpus borrow?** Counted below per corpus: distinct relation
names written, against how many of them the engine already knew.

**What is the reserved vocabulary FOR?** The interesting half. If those names
were a domain -- a little ontology of times and things and actions -- then a
corpus would be writing *inside* someone else's world model, and the observation
would be much weaker than it sounds. The classification below says they are not:
the engine's vocabulary is about **the chain, the surface, rules-as-data, the
agent's own deliberation, and the seam where a world reaches it.** Not one of
them is about any world.

⚠ **The classification is a CLAIM, not a measurement**, which is why it is
written out name by name where it can be disagreed with, and why the partition
is checked for being total: a name nobody classified would otherwise vanish from
the count and flatter whichever bucket it belonged in.
"""

import re
import sys
from typing import Dict, List, Set

from .machine import Machine

# -- what the engine's own names are for ------------------------------------

ROLES: Dict[str, List[str]] = {
    # Not vocabulary at all: a numeral is an atom whose name reads as a number.
    "literals": list("0123456789"),
    # The surface's own marks -- connectives, signs, and the member modifier.
    "the surface": ["causes", "implies", "not", "plus", "minus", "unsure", "at"],
    # §4-§11: the history, and how to walk it.
    # `licensed_by` sits beside `rests_on` and is here for its reason: *what
    # produced this entry* is a fact about the chain's own construction, not
    # about any world. ⚠ It arrived unclassified and this census is what caught
    # it -- see docs/observations.md §2.14, where the invariant was written down
    # one message before it fired.
    # `moved` sits here for `asking`'s reason rather than under deliberation:
    # both are about WHICH SEAT, which is a fact about the agent's place in the
    # history and not about what it is trying to do there.
    "the chain": ["anc", "sanc", "pred", "in_delta", "delta_next", "entry_of",
                  "span", "span_of", "rests_on", "licensed_by",
                  "arrived_on", "mentioned", "asking", "asked", "reaches",
                  "moved"],
    # R3/R4: rules are subjects, and rules are askable.
    "rules as data": ["rule", "ant", "con", "conn", "adopt", "compose",
                      "composed", "computes", "names", "binds", "exercised",
                      "overrides", "supersedes", "defeated"],
    # The agent reasoning about its own reasoning: goals, plans, backward
    # reading, recall, supposing, effort, stopping, credit.
    "the agent's deliberation": [
        "goal", "plan", "subgoal", "check", "fit", "fits", "unfit", "unmet",
        "verdict", "blocked", "pursued", "expands", "need", "recall",
        "recalled", "achieved", "enough", "stopped", "quiet", "open", "left",
        "resume", "again", "suppose", "hypotheses", "budget", "depth",
        "tolerance", "close", "forgone", "helped", "harmed", "concluded",
        "reached", "bounded", "widened", "support", "unsupported", "root",
        "rooted", "scoped", "loaded", "kb", "dormant", "due", "standing",
        # The aggregate over bindings, which is what `blocked`, `rooted` and
        # `unsupported` above are each a threshold on: a rule sees one binding
        # at a time, so *how many* is the machinery's to answer.
        "count", "counted",
        # `attention` sits beside `prefer` because it is the same claim about a
        # NODE rather than about a rule -- *think about this one* -- and it is
        # the agent's own deliberation for the same reason `prefer` is.
        "prefer", "attention", "excluded", "ticks",
        # §18's call stack: the plumbing under a recursive plan, and not a way
        # of making one. Deliberation words, chosen so they are not words a
        # WORLD uses -- `awaits`/`returned`/`advances` rather than the obvious
        # `child`/`done`/`then`, because reserving `child` takes it from every
        # corpus that has a family in it.
        "call", "stage", "spawn", "awaits", "returned", "advances", "closes",
        # The action palette, declared rather than implied. `conn(?r, causes)`
        # was the nearest thing and answers a different question -- how a rule
        # relates to the world, not that the agent may deliberately do it.
        "afforded",
        # ...and asking for one. `attempt` is the request; `declined` is what
        # becomes of a bad one, with `unafforded` the single reason the
        # MACHINERY ever gives -- what is legal is the world model's to say, in
        # its own word.
        "attempt", "declined", "unafforded",
        # Refraction (§14): what has already run, on what, and the
        # contradiction that stopping a loop would otherwise hide.
        "spent", "premises", "contested",
    ],
    # Where a world touches the agent: what arrived, what was said, what was
    # done, and what may not be. About the ACT, never about its content.
    "the seam to a world": ["arrived", "says", "answered", "answers", "emitted",
                            "did", "doing", "taken", "deviates", "expects",
                            "forbidden", "refused"],
}

# `about` says what a corpus is about, and it is what makes this a comparison
# rather than a list: a corpus about a WORLD should invent nearly all of its
# vocabulary, and the bundle -- which is about the agent's own reasoning -- should
# borrow nearly all of it. Those are opposite predictions from one classification,
# which is what stops this being a table that can only agree with itself.
CORPORA = [
    ("a D&D fight", "ugm/rules/dungeon.ugm", "a world"),
    ("passenger rights", "ugm/rules/delay.ugm", "a world"),
    ("the design's worked examples", "ugm/rules/worked.ugm", "a world"),
    ("the bundle itself", "ugm/rules/bundle.ugm", "the agent"),
]


def web(m: Machine, rules):
    """Delegates to `Machine.web`. ⚠ It used to be a second copy of it, and the
    copy is how a fix landed in one of them: a variable in relation position was
    excluded in the engine and still reported here. An index is a
    re-implementation of what it indexes -- `state` paid for that lesson, and
    this module had quietly acquired the same shape."""
    return m.web(rules)


def unwebbed(m: Machine, rules, res: Set[str]) -> List[str]:
    """Names a corpus READS and nothing ever writes -- so no rule using one can
    ever be satisfied, and the corpus is silently smaller than it looks.

    ⚠ The engine's own names are excluded because the **machinery** supplies
    them: the bundle reads `arrived`, `emitted`, `taken` and `quiet` and writes
    none of them, correctly. Without the exclusion the bundle reports 11.

    ⚠⚠ **The known false positive**: a corpus that expects a world to supply an
    open-class fact at run time -- from a channel rather than from its own text
    -- reads a name it never writes and is right to.
    """
    return m.unwebbed(rules)


def sweep() -> "tuple":
    """Every machine the suite builds, asked the unwebbed question.

    ⭐⭐⭐ **91% of this repository's rules are invisible to every instrument
    above.** 51 rules live in `ugm/rules/*.ugm`; **506 are string literals inside
    Python**, 360 of them in `selftest.py`. So the census, the atlas and the
    load-time note between them cover under a tenth of the corpus, and the
    numbers this module reports are about the tenth that happens to be in a file.

    This reaches the rest without moving a line, by `ugm.harmony`'s own trick:
    hook `Machine.run` and ask each machine once. And it paid immediately -- it
    found a bug **in the checker**, not in the corpora: a variable in relation
    position (`+?kind(?item)`) was being reported as a relation nothing writes,
    so a corpus using §4's *class as data* was told a working rule was broken.

    ⚠ **What it does NOT justify is moving the fixtures.** 62 of 239 machines
    report an unwebbed name and nearly all are correct about a deliberately
    partial fixture -- a rule loaded to test something else, whose premise nobody
    supplies. That is the same result the load-time note gave (91 fires, all
    correct, all useless), and externalising the fixtures would not change it.
    What externalising buys is **clarity about what is engine and what is
    corpus**, which is a different argument and a better one.
    """
    import io
    machines = [0, 0]
    found: List[List[str]] = []
    run = Machine.run

    def swept(self, limit=100):
        # ⚠⚠ A flag on the machine, never a set of `id()` -- CPython reuses an
        # address the moment a machine is collected, which under-counted
        # `ugm.harmony`'s census by 3.5× before it was found.
        if not getattr(self, "_swept", False):
            self._swept = True
            machines[0] += 1
            try:
                got = self.unwebbed()
            except Exception:
                got = []
            if got:
                machines[1] += 1
                found.append(got)
        return run(self, limit)

    Machine.run = swept
    try:
        from . import selftest as S
        buf, old = io.StringIO(), sys.stdout
        sys.stdout = buf
        try:
            S.main()
        finally:
            sys.stdout = old
    finally:
        Machine.run = run
    return machines[0], machines[1], found


def reserved() -> Set[str]:
    """Every name a corpus may write and the engine already understands."""
    m = Machine()
    for attr in dir(m):
        v = getattr(m, attr, None)
        if isinstance(v, dict) and "anc" in v and "goal" in v:
            return set(v)
    raise RuntimeError("the name table moved")


def relations(path: str) -> Set[str]:
    """The distinct relation names a corpus writes.

    ⚠ Read off the TEXT rather than off a loaded machine, deliberately: loading
    the bundle's own file into a machine that already has it is a redeclaration,
    and a census that can only count what loads cannot count a corpus at all.
    """
    with open(path, "r", encoding="utf-8") as fh:
        src = re.sub(r"#.*", "", fh.read())
    return set(re.findall(r"([a-z_][a-z_0-9]*)\s*\(", src))


def main() -> int:
    res = reserved()
    failures: List[str] = []
    checked = 0

    print("What the engine reserves, and what it is for")
    print()
    classified: Set[str] = set()
    for role, names in ROLES.items():
        dup = classified & set(names)
        if dup:
            failures.append(f"classified twice: {sorted(dup)}")
        classified |= set(names)
        print(f"  {role:26} {len(names):3}")
    print(f"  {'':26} ---")
    print(f"  {'total':26} {len(classified):3}")
    print()

    # ⚠ The partition must be TOTAL, or a name nobody classified disappears from
    # the count and flatters whichever bucket it should have been in. This is the
    # check that makes the table above evidence rather than decoration.
    checked += 1
    missing = res - classified
    extra = classified - res
    if missing or extra:
        failures.append(
            f"the classification is not the vocabulary: "
            f"{len(missing)} unclassified {sorted(missing)}, "
            f"{len(extra)} classified but not reserved {sorted(extra)}")
    print(f"  every reserved name is classified exactly once: "
          f"{'yes' if not (missing or extra) else 'NO'}")

    # ⭐⭐⭐ The headline. None of the roles above is a DOMAIN -- there is no
    # reserved name for a thing, a place, an amount of anything, or an act of
    # any particular kind. `did` and `says` are about the act, never about what
    # was done or said.
    checked += 1
    world = len(res) - sum(len(v) for v in ROLES.values())
    print(f"  reserved names that are about a WORLD: {world}")
    if world != 0:
        failures.append("a reserved name turned out to be a domain word")

    print()
    print("What a corpus has to borrow")
    print()
    for label, path, about in CORPORA:
        try:
            names = relations(path)
        except OSError:
            print(f"  {label:30} (not readable)")
            continue
        borrowed = sorted(names & res)
        own = len(names) - len(borrowed)
        checked += 1
        print(f"  {label:22} ({about:9}) {len(names):3} names, {own:3} its own, "
              f"{len(borrowed):2} borrowed")
        print(f"  {'':34}   borrowed: {borrowed}")
        # ⚠⚠ **The first version of this check called the bundle a failure**, and
        # the bundle is the CONTROL: it borrows 25 of 25 because it is the one
        # corpus that is about the agent's own reasoning rather than any world.
        # A check that fires on the case that proves the classification right is
        # measuring the wrong thing -- so the prediction is now signed by what
        # the corpus is about, and it can fail in either direction.
        if about == "a world" and own <= len(borrowed):
            failures.append(f"{label} is about a world and borrowed more than "
                            f"it invented -- the reserved names are a domain "
                            f"after all")
        if about == "the agent" and own > len(borrowed):
            failures.append(f"{label} is about the agent's own reasoning and had "
                            f"to invent vocabulary for it -- the apparatus is "
                            f"not sayable in the names the engine reserves")

    # ⚠⚠⚠ **A corpus that is only COUNTED is decoration.** `delay.ugm` exists to
    # be a second world, and a census over a file nobody runs would happily
    # report a vocabulary for rules that do not work. So it is run, and its
    # answers are asserted -- including the one that carries the domain: the duty
    # of care is owed whatever the cause, and compensation is not.
    print()
    print("...and the corpus that second world is counted from actually runs")
    from .text import load
    m = Machine()
    with open("ugm/rules/delay.ugm", "r", encoding="utf-8") as fh:
        kb = load(m, fh.read())
    m.run(limit=300)
    at = lambda q: m.chain.holds(kb.term(q), m.focus.topic, m.focus.seat)
    want = {
        # a crew shortage is the carrier's own doing: care AND compensation
        "owed(ana, meals)": "+", "owed(ana, money)": "+",
        "amount(ana, 600)": "+", "rerouted(ana, zr9)": "+",
        # a storm is not: care only, and the guard is what withholds the rest
        "owed(raj, meals)": "+", "owed(raj, money)": None,
        "amount(raj, 250)": None,
    }
    for q, expect in want.items():
        checked += 1
        got = at(q)
        print(f"    {q:22} {got!r:6} {'ok' if got == expect else 'FAIL'}")
        if got != expect:
            failures.append(f"{q} is {got!r}, wanted {expect!r}")

    # -- vocabulary connected to nothing -------------------------------------
    print()
    print("Vocabulary with no web -- names a corpus reads and nothing writes")
    print()
    from .text import load as _load

    def corpus(src: str):
        """A machine with the corpus loaded, and only the corpus's own rules."""
        mm = Machine()
        before = {r.node for r in mm.rules.rules}
        kb2 = _load(mm, src)
        mm.run(limit=300)
        return mm, kb2, [r for r in mm.rules.rules if r.node not in before]

    for label, path, _ in CORPORA:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
        except OSError:
            continue
        if label == "the bundle itself":
            mm = Machine()          # it is already loaded; re-loading redeclares
            rules = list(mm.rules.rules)
        elif label == "a D&D fight":
            # ⚠ It registers three computators, so it cannot be loaded from its
            # text alone -- and it is the one corpus written by another session,
            # which makes it the false-positive test that actually counts.
            from .dungeon import fight
            bundled = {r.node for r in Machine().rules.rules}
            mm, _, _ = fight(seed=1, limit=60)
            rules = [r for r in mm.rules.rules if r.node not in bundled]
        else:
            try:
                mm, _, rules = corpus(src)
            except Exception as exc:
                print(f"  {label:30} (will not load: {str(exc)[:34]})")
                continue
        orphans = unwebbed(mm, rules, res)
        checked += 1
        print(f"  {label:30} {len(orphans)} unwebbed  {orphans if orphans else ''}")
        if orphans:
            failures.append(f"{label} reads {orphans}, which nothing writes")

    # ⚠⚠⚠ **The control, and the instrument is worth nothing without it.** Every
    # corpus above reports zero, which is the same output a detector that has
    # stopped being able to fire would give. This repo has recorded a check that
    # was guarded twice over by later improvements and could no longer fail; a
    # detector reporting all-clear on every input is that trap with the numbers
    # already looking right.
    mm2, _, planted = corpus(
        "rule <trade> = implies( { +owns(?s, ?i), +wants(?b, ?i) },\n"
        "                       { +sells(?s, ?b, ?i) } )\n"
        "fact +owns(smith, sword)\n"
        "fact +watns(hero, sword)\n")
    caught = unwebbed(mm2, planted, res)
    checked += 1
    print(f"  {'a planted typo (watns/wants)':30} {len(caught)} unwebbed  {caught}")
    if caught != ["wants"]:
        failures.append(f"the control was not caught: {caught}")

    # -- and the 91% none of the above reaches ------------------------------
    if "--sweep" in sys.argv:
        print()
        print("Sweeping every machine the suite builds (91% of the rules here "
              "are inline in Python)")
        total, orphaned, found = sweep()
        flat: Dict[str, int] = {}
        for g in found:
            for n in g:
                flat[n] = flat.get(n, 0) + 1
        print(f"  machines swept              : {total}")
        print(f"  with an unwebbed name       : {orphaned}")
        print(f"  most common                 : "
              f"{sorted(flat.items(), key=lambda kv: -kv[1])[:8]}")
        checked += 1
        # ⚠ Not a failure. Nearly every one is correct about a deliberately
        # partial fixture, which is the same answer the load-time note gave.
        # What this gate asserts is that no VARIABLE is reported as a name --
        # `+?kind(?item)` was, and a working corpus was called broken.
        bogus = [n for n in flat if n.startswith("?")]
        if bogus:
            failures.append(f"a variable in relation position reported as a "
                            f"name: {bogus}")
        print(f"  variables misreported as names: {bogus if bogus else 'none'}")

    print()
    for f in failures:
        print(f"  FAIL  {f}")
    print(f"{checked} checks, {len(failures)} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
