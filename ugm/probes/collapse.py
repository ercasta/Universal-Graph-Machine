"""Is the `-` / `?` collapse lossy? (wanting.md §9.4, and it cannot be asked later)

Under anchors belief IS the presence of an anchor node, so a proposition is
believed or it is not. `-p` as a CONSEQUENT becomes *delete the anchor*, which
is what §7 sells as a header line rather than a rewrite. As a MEMBER both `-$p`
and `? $p` become *no anchor*, and they are then the same member. The question
this probe asks is whether anything a corpus needs to say dies in that merge.

The fixture is `bundle.ugm`'s deviation rules -- FOUR of them, not three as
wanting.md says twice -- because they are the only place in the repo where all
three signs are load-bearing in one family of rules.

Anchors are not built, so today's engine stands in for them under one mapping,
which is the whole method of this probe:

    anchor present   an entry asserting p          fact +p
    no anchor        no entry for p at all         write nothing
    denial           an anchor on not(p)           fact +not(p)

The denial is written with the apparatus's own `not`, which `<denial>` already
mints from, so nothing here is invented for the occasion.

The answer, measured below: the collapse forces a decision the sign was hiding,
and the decision is what `expects($p, minus)` MEANS once there is no minus to
observe. Read as *expect no anchor on p* it loses a row. Read as
`expects(not($p))` -- an expectation naming the proposition it wants anchored,
with no sign in it at all -- the four rules become ONE, and all six rows come
back. The collapse is not lossy; it is the sign in `expects` that was doing a
proposition's work.

See docs/wanting.md §7 and §9.4, and docs/HANDOFF.md 2026-08-22.
"""

import contextlib
import io
import sys

from ..core.chain import MINUS, PLUS, UNSURE
from ..core.machine import Machine
from ..core.text import load


# The four rules as they ship, transposed onto a private vocabulary so the
# bundle's own copies cannot answer for them. `xdev` is a corpus word; nothing
# in the apparatus knows it. `xexpects` keeps the reserved `plus`/`minus` as
# arguments deliberately -- that is the spelling under test.
SHIPPED = """
rule <x-+-contradicted> = implies( { +xexpects($p, plus), -$p }, { +xdev($p) } )
rule <x-+-invalidated>  = implies( { +xexpects($p, plus), ? $p }, { +xdev($p) } )
rule <x---contradicted> = implies( { +xexpects($p, minus), +$p }, { +xdev($p) } )
rule <x---invalidated>  = implies( { +xexpects($p, minus), ? $p }, { +xdev($p) } )
"""

# READING A, naive: every `-` member and every `?` member becomes `no`, and
# `expects($p, minus)` still means what it meant. That is what *a header line
# rather than a rewrite* means if it means anything. Two of the four rules
# become textually identical.
NAIVE_A = """
rule <x-+-contradicted> = implies( { +xexpects($p, plus), no $p }, { +xdev($p) } )
rule <x-+-invalidated>  = implies( { +xexpects($p, plus), no $p }, { +xdev($p) } )
rule <x---contradicted> = implies( { +xexpects($p, minus), +$p }, { +xdev($p) } )
rule <x---invalidated>  = implies( { +xexpects($p, minus), no $p }, { +xdev($p) } )
"""

# READING A, deduplicated: the merge taken seriously, and `expects(minus)` read
# as *expect no anchor*, which is the only thing minus can mean when there is
# no minus to observe.
TWO_ROWS_A = """
rule <x-+-disappointed> = implies( { +xexpects($p, plus), no $p }, { +xdev($p) } )
rule <x---disappointed> = implies( { +xexpects($p, minus), +$p }, { +xdev($p) } )
"""

# READING B: an expectation names the proposition it wants ANCHORED, so the
# sign leaves it -- `xexpects($p, minus)` is `xexpects(not($p))`. One rule.
ONE_ROW_B = """
rule <x-disappointed> = implies( { +xexpects($q), no $q }, { +xdev($q) } )
"""

# And the distinction the merge is accused of eating -- which WAY an expected
# anchor was disappointed -- recovered as rows over `not($q)`. No sign is read.
GRAINED_B = ONE_ROW_B + """
rule <x-contradicted> = implies(
    { +xexpects($q), no $q, +not($q) }, { +xhow($q, contradicted) } )
rule <x-invalidated> = implies(
    { +xexpects($q), no $q, no not($q) }, { +xhow($q, invalidated) } )
"""

# expectation, observation, is-it-a-deviation. The last two rows are the
# controls -- an expectation the world MET -- and the second of them is not in
# the suite today.
CASES = (
    ("plus",  "minus",  True),
    ("plus",  "unsure", True),
    ("minus", "plus",   True),
    ("minus", "unsure", True),
    ("plus",  "plus",   False),
    ("minus", "minus",  False),
)

OBSERVED = {"plus": PLUS, "minus": MINUS, "unsure": UNSURE}

NOTES: list = []


def _load(m, text):
    """Load, keeping the reserved-name note out of the table it would bury.

    `plus` and `minus` ARE the reserved sign nodes here and that is deliberate,
    so the note is correct and is printed once at the end rather than 26 times.
    """
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        kb = load(m, text)
    for line in buf.getvalue().splitlines():
        if line and line not in NOTES:
            NOTES.append(line)
    return kb


def _signs_run(rules: str, expect: str, observe: str) -> bool:
    """Today's world: three signs, written as three signs."""
    m = Machine()
    kb = _load(m, rules + "\nfact +xexpects(boiling(kettle), " + expect + ")\n")
    m.gate.write(kb.term("boiling(kettle)"), OBSERVED[observe])
    m.run(limit=12)
    return m.holds(kb.term("xdev(boiling(kettle))")) == PLUS


def _anchor_run(rules, expect, observe, read=None) -> bool:
    """The anchor world, under the mapping in the docstring.

    `expect` is a sign word under reading A, and that word with a "B" on it
    under reading B, where the expectation names the proposition instead of
    carrying a sign. ⚠ Under B the deviation is ABOUT the expected proposition,
    so a minus expectation deviates as `xdev(not(p))` -- reading `xdev(p)` for
    it reports no deviation, which looks exactly like the rule not working.
    """
    m = Machine()
    if expect in ("plusB", "minusB"):
        target = ("boiling(kettle)" if expect == "plusB"
                  else "not(boiling(kettle))")
        facts = "\nfact +xexpects(" + target + ")\n"
        read = read or "xdev(" + target + ")"
    else:
        facts = "\nfact +xexpects(boiling(kettle), " + expect + ")\n"
        read = read or "xdev(boiling(kettle))"
    if observe == "plus":
        facts += "fact +boiling(kettle)\n"
    elif observe == "minus":
        facts += "fact +not(boiling(kettle))\n"
    kb = _load(m, rules + facts)
    m.run(limit=12)
    return m.holds(kb.term(read)) == PLUS


def _table(title, run, label_of=lambda e: e):
    """Print the six rows and say which of them came out wrong."""
    print("  " + title)
    wrong = []
    for expect, observe, want in CASES:
        got = run(expect, observe)
        flag = "" if got == want else "   <- WRONG"
        print(f"      expects {label_of(expect):5} observed {observe:6} -> "
              f"dev={str(got):5}  want={want}{flag}")
        if got != want:
            wrong.append((expect, observe))
    return wrong


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failing = ran = 0

    def gate(name, ok):
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__.strip().split("\n")[0])
    print()

    # 1. The fixture answers correctly today, all six rows -- including the
    #    control the suite does not have. Without this the rest measures a
    #    transposition rather than the collapse.
    wrong = _table("today, three signs, four rules:",
                   lambda e, o: _signs_run(SHIPPED, e, o))
    gate("the four shipped rules get all six rows right, controls included",
         wrong == [])

    # 2. And the sixth row is the one the suite never asks: it has a control
    #    for expects-plus and none for expects-minus. Stated as its own check
    #    because a gap in the instrument is a finding, not a footnote.
    gate("expects minus, observed minus is NOT a deviation -- and no check in "
         "the suite asks it",
         _signs_run(SHIPPED, "minus", "minus") is False)

    # 3. READING A, naive. Two rules become the same rule, and the fourth
    #    fires on an expectation the world MET, because under anchors absence
    #    is exactly what `expects(minus)` is satisfied by. That was the
    #    standing prediction and it holds -- for `<deviation---invalidated>`,
    #    named in advance.
    print()
    wrong = _table("reading A, naive: every `-` and `?` member becomes `no`:",
                   lambda e, o: _anchor_run(NAIVE_A, e, o))
    gate("the naive collapse breaks one row, and it is the one predicted -- "
         "expects minus observed minus, by <x---invalidated>",
         wrong == [("minus", "minus")])
    gate("and it breaks it in the direction that looks like success: a "
         "deviation reported where the expectation was MET",
         _anchor_run(NAIVE_A, "minus", "minus") is True)

    # 4. READING A, deduplicated. Deleting the duplicate is not enough: with
    #    the sign kept as an argument, no set of rules gets both expects-minus
    #    rows, because the two observations that decide them are now one
    #    observation. The row that goes is the OTHER one -- so reading A loses
    #    a row whichever way it is written.
    print()
    wrong = _table("reading A, deduplicated to two rows:",
                   lambda e, o: _anchor_run(TWO_ROWS_A, e, o))
    gate("reading A cannot have both expects-minus rows: fixing one loses the "
         "other, because the sign it reads is no longer observable",
         wrong == [("minus", "unsure")])

    # 5. READING B: the sign leaves the expectation and becomes the
    #    proposition it names. `expects($p, minus)` is `expects(not($p))`. One
    #    rule, and all six rows -- including the control the suite lacks.
    print()
    wrong = _table("reading B, ONE rule, expects(not($p)) for the minus rows:",
                   lambda e, o: _anchor_run(ONE_ROW_B, e + "B", o),
                   label_of=lambda e: e)
    gate("one rule over anchors answers every row the four answered", wrong == [])

    # 6. What the merge really costs: contradicted and invalidated are one
    #    deviation now. The distinction did not leave the world, it moved into
    #    `not($q)`, which is a proposition with an anchor of its own -- and it
    #    comes back as ROWS, with no sign read anywhere.
    print()
    print("  the merged distinction, recovered as rows over not($q):")
    grained = []
    for observe in ("minus", "unsure"):
        c = _anchor_run(GRAINED_B, "plusB", observe,
                        "xhow(boiling(kettle), contradicted)")
        i = _anchor_run(GRAINED_B, "plusB", observe,
                        "xhow(boiling(kettle), invalidated)")
        print(f"      expects plus  observed {observe:6} -> "
              f"contradicted={str(c):5} invalidated={i}")
        grained.append((c, i))
    gate("expected-and-DENIED and expected-and-UNKNOWN stay apart, as rows",
         grained == [(True, False), (False, True)])

    # 7. The kill-probe for 6: without the `not($q)` members the two cases are
    #    one answer, so 6 is measuring the members and not the fixture.
    same = [_anchor_run(ONE_ROW_B, "plusB", o) for o in ("minus", "unsure")]
    gate("and without those members the two are one answer (kill-probe)",
         same == [True, True])

    # 8. The kill-probe for every table above: with no rules at all, nothing
    #    concludes a deviation. `xdev` is a corpus word, but the bundle is
    #    loaded in each of these machines and this is what says so.
    gate("with the rules removed, no row deviates -- so it is these rules "
         "answering and not the bundle (kill-probe)",
         not any(_anchor_run("", e + "B", o) for e, o, _ in CASES))

    # 9. And the four shipped rules are four, not three with a spare: dropping
    #    any one of them costs exactly one row. Without this, *four become one*
    #    would be a reduction of something already redundant.
    print()
    print("  each shipped rule dropped, one at a time:")
    lines = [ln for ln in SHIPPED.strip().splitlines()]
    costs = []
    for k, ln in enumerate(lines):
        rest = "\n".join(lines[:k] + lines[k + 1:])
        lost = [(e, o) for e, o, want in CASES
                if want and not _signs_run(rest, e, o)]
        name = ln.split(">")[0] + ">"
        print(f"      without {name:24} rows lost: {len(lost)}  {lost}")
        costs.append(len(lost))
    gate("each of the four is load-bearing -- one row each", costs == [1, 1, 1, 1])

    print()
    for line in NOTES:
        print("  (load) " + line)
    print(f"  {ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
