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
from typing import Dict, List, Set

from .machine import Machine

# -- what the engine's own names are for ------------------------------------

ROLES: Dict[str, List[str]] = {
    # Not vocabulary at all: a numeral is an atom whose name reads as a number.
    "literals": list("0123456789"),
    # The surface's own marks -- connectives, signs, and the member modifier.
    "the surface": ["causes", "implies", "not", "plus", "minus", "unsure", "at"],
    # §4-§11: the history, and how to walk it.
    "the chain": ["anc", "sanc", "pred", "in_delta", "delta_next", "entry_of",
                  "span", "span_of", "rests_on", "asking"],
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
        "prefer", "excluded",
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

    print()
    for f in failures:
        print(f"  FAIL  {f}")
    print(f"{checked} checks, {len(failures)} failing")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
