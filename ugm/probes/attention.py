"""The two measurements that say what a score in the table means.

    python -m ugm.probes.attention

Both used to sit at the bottom of `core/attention.py`; the loop is the loop and
an example is not part of it, so they live here.

    ordering is not defeasibility   a general rule declared before a specific
                                    one, and what does and does not remove its
                                    conclusion
    a score means nothing without   `stop` is a rule's output, and obeying it is
    a way to stop                   what shortens the run

See docs/design/attention.md.
"""

from ..core.attention import SETTLE, run
from ..core.machine import Machine
from ..core.text import load



PENGUIN = """
fact bird(tweety)
fact bird(pingu)
fact penguin(pingu)
fact asked(pingu)
fact asked(tweety)

rule <flies>      = implies( {{ +bird($x), +considered($x) }},    {{ +can_fly($x) }} )
rule <flightless> = implies( {{ +penguin($x), +considered($x) }}, {{ +grounded($x) }} )
rule <classify>   = implies( {{ +asked($x) }},                    {{ +considered($x) }} )
{post}
"""


def penguin() -> int:
    """Four levers on one fixture, and only the last one answers the question.

    `<flies>` is declared first, so under declaration order it wins for every
    bird, penguin included: the general rule is the more foundational one, and
    that is what declaration order says. Ordering alone cannot ground the
    penguin, because a low score delays a rule and never removes it. `tweety`
    is the control -- without an ordinary bird in the fixture, taking the
    general rule out and representation look identical, and the lever that
    breaks flight passes.

    See docs/design/attention.md#penguin.
    """
    print()
    print("  the penguin -- ordering is not defeasibility")
    wrong = 0
    DENIED = PENGUIN.replace(
        "fact penguin(pingu)",
        "fact penguin(pingu)" + chr(10) + "fact -penguin(tweety)").replace(
        "+bird($x), +considered($x) }}",
        "+bird($x), +considered($x), -penguin($x) }}")
    cases = (
        ("declaration order alone", PENGUIN.format(post="")),
        ("standing(<flightless>)",
         PENGUIN.format(post="fact standing(<flightless>)")),
        ("dormant(<flies>)",
         PENGUIN.format(post="fact dormant(<flies>)")),
        ("the KB states -penguin(tweety)", DENIED.format(post="")),
    )
    for label, src in cases:
        m = Machine()
        kb = load(m, src)
        load(m, SETTLE)
        run(m, limit=12)
        held = lambda t: m.holds(kb.term(t)) == "+"
        pingu_flies, tweety_flies = held("can_fly(pingu)"), held("can_fly(tweety)")
        print(f"    {label:32} pingu flies: {str(pingu_flies):5}  "
              f"grounded: {str(held('grounded(pingu)')):5}  "
              f"tweety flies: {tweety_flies}")
        if label.startswith(("dormant", "the KB")):
            # The two that claim to answer it: the penguin must not fly, and
            # an ordinary bird must still be able to.
            if pingu_flies:
                print(f"    FAIL  {label} left the penguin flying")
                wrong += 1
            if label.startswith("the KB") and not tweety_flies:
                print(f"    FAIL  {label} grounded tweety as well, which is not "
                      f"solving the penguin but breaking flight")
                wrong += 1
        elif not pingu_flies:
            print(f"    FAIL  {label} is an ORDERING and must not remove a "
                  f"conclusion -- if it does, ordering has become defeat")
            wrong += 1
    return wrong


# -- stopping, which is what makes a score mean anything --------------------

_IDLE = "\n".join(
    "rule <f%d> = implies( { +wood($x) }, { +step%d($x) } )" % (i, i)
    for i in range(1, 13))
_DEEP = "\n".join(
    "rule <g%d> = implies( { +step%d($x) }, { +after%d($x) } )" % (i, i, i)
    for i in range(1, 13))

# `want`, not `goal`: `goal` is the apparatus's own relation and the backward
# reader deposits its own, so a completion check written over `goal($w)` fires
# on the machinery's subgoals and reports the thing finished before it is built.
# A corpus's vocabulary is not the apparatus's.
STOPPING = """
fact +want(assembled(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood($x) },       { +have(wheel) } )
rule <axle>  = implies( { +have(wheel) },    { +have(axle) } )
rule <bed>   = implies( { +have(axle) },     { +have(bed) } )
rule <build> = implies( { +have(bed) },      { +assembled(cart) } )
rule <done>  = implies( { +want($w), +$w },  { +finished($w) } )
""" + _IDLE + "\n" + _DEEP + "\n"

# Two things wanted, one reachable: the stop fires on the one that was built
# while the other is still wanted and still unmet.
OPEN_WANT = """
fact +want(assembled(cart))
fact +want(painted(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood($x) },       { +have(wheel) } )
rule <build> = implies( { +have(wheel) },    { +assembled(cart) } )
rule <done>  = implies( { +want($w), +$w },  { +finished($w) } )
after <done> => stop
"""


def _stopping_run(src, limit=400):
    m = Machine()
    load(m, src)
    load(m, SETTLE)
    return m, run(m, limit=limit)


def stopping() -> int:
    """`stop`, and what obeying it is worth.

    Done is the output of a rule that checks against the goal. The three rows
    measure what that buys: without the postcondition the agent carries on to
    quiescence, with it the run ends when the check concludes, and raising the
    check's priority changes nothing -- the null result that says `stop` is
    obeyed rather than merely ranked.

    See docs/design/attention.md#stopping.
    """
    print()
    print("  stopping -- a cart to build, and a check that says when it is done")
    bad = 0
    seen = {}
    cases = (
        ("", "no postcondition"),
        ("after <done> => stop", "stop, <done> at the floor"),
        ("after <done> => stop\nfact standing(<done>)",
         "stop, and <done> standing"),
    )
    for post, label in cases:
        _m, r = _stopping_run(STOPPING + "\n" + post)
        done = any(p == "finished(assembled(cart))" and sg == "+"
                   for p, sg in r.state)
        seen[label] = r.ticks
        print(f"    {label:32} {r.ticks:>4} moves   finished: {done}   "
              f"stopped by {r.table.stopped}")
        if not done:
            bad += 1
    # The claim, as a number: obeying the rule is what shortens the run.
    if seen["stop, <done> at the floor"] >= seen["no postcondition"]:
        print("    FAIL  `stop` did not shorten the run")
        bad += 1
    # The null result, kept as a check so it cannot quietly come back. A bound
    # rather than an equality, and it has to stay far tighter than what `stop`
    # buys or it would stop being able to fail.
    drift = abs(seen["stop, and <done> standing"]
                - seen["stop, <done> at the floor"])
    worth = seen["no postcondition"] - seen["stop, <done> at the floor"]
    if drift > 1 or drift * 10 >= worth:
        print(f"    FAIL  raising the check's priority changed the run by "
              f"{drift} moves against {worth} for `stop` -- the null result "
              f"moved")
        bad += 1

    # The cost, measured rather than asserted: the loop stops on a `stop` even
    # with another want still open. Refusing to would need a veto over the set
    # of unmet wants, and a rule cannot speak about the set of its matches, so
    # the guarantee is a corpus's. This is the instrument that watches it.
    _m, r = _stopping_run(OPEN_WANT, limit=200)
    held = {p for p, sg in r.state if sg == "+"}
    quiet_on_open = ("want(painted(cart))" in held
                     and "painted(cart)" not in held
                     and r.table.stopped is not None)
    print(f"    {'stopped with a want still open':32} {r.ticks:>4} moves   "
          f"unmet want left behind: {quiet_on_open}")
    if not quiet_on_open:
        print("    FAIL  the open-want probe has nothing to measure")
        bad += 1
    return bad


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.strip())
    print()
    return penguin() + stopping()


if __name__ == "__main__":
    raise SystemExit(main())
