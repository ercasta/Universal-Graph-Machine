"""Is `context: believed` needed? (wanting.md §7, asked of the engine)

The proposal: because belief becomes presence of an anchor, a rule matching a
BARE proposition would read structure as though it were belief, so every
component of every rule is wrapped at load -- `want($p)` stored as
`believed(want($p))`, and the matcher never learns what an anchor is.

The handoff leaves it unresolved with an argument on each side and one
measurement. This probe asks the engine instead, and the crux is the first
check: **the entry is already the anchor, on the read side.** A rule's stored
pattern and a mention both put a proposition in the graph, and neither makes it
matchable, because `match` reads the SITUATION -- entries -- and never the raw
graph. So the failure the wrapper exists to prevent is not a failure this engine
has.

The rest of the probe takes the constraints §7 says would MOVE from the loader
into the engine if the wrapper were dropped, and asks where each one is today.
They are already in the engine, one branch each, and none of them was written
for this question. What is left on the wrapper's side of the ledger is its own
escape (check 5) and its own hazard (check 6).

⚠⚠⚠ And check 7 is the finding rather than the verdict: there IS one path where
presence in the graph really does mean belief, and it is the STRUCTURAL path --
the one path §7's first constraint tells the wrapper to skip. A ground
structural pattern stored in a rule that is never applied reads as a deposited
fact, so a reader binds a moment that does not exist. The wrapper would not have
caught it.

⚠ Nothing here is an argument about anchors, which are not built. Every check is
about TODAY's matcher, and it is worth exactly what today's matcher shares with
the anchored one: the entry indirection, which is the half the anchor design
keeps.

See docs/wanting.md §7, docs/todo.md "...and belief is an ANCHOR", and
docs/HANDOFF.md 2026-08-22.
"""

import sys

from ..core.machine import Machine
from ..core.text import load


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

    # 1. THE CRUX. `p(thing)` is in the graph twice over -- as another rule's
    #    stored pattern and inside a mention -- and nothing asserts it. If the
    #    reader fires, the wrapper is describing a real hazard. It does not.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <reader> = implies( { +p($x) }, { +q($x) } )",
        "rule <owner>  = implies( { +p(thing) }, { +owned(thing) } )",
        "fact +said(alice, p(thing))", ""]))
    m.run(limit=30)
    print(f"      p(thing) is a node        {kb.term('p(thing)') is not None}")
    print(f"      ...and is it held?        {m.holds(kb.term('p(thing)'))}")
    print(f"      q(thing), from a pattern  {m.holds(kb.term('q(thing)'))}")
    print(f"      owned(thing), from it     {m.holds(kb.term('owned(thing)'))}")
    gate("a proposition present only as STRUCTURE matches nothing -- the entry "
         "is already the anchor, on the read side",
         kb.term("p(thing)") is not None
         and m.holds(kb.term("q(thing)")) is None
         and m.holds(kb.term("owned(thing)")) is None)

    # 2. The kill-probe for 1, and it has to be here: a fixture where the rule
    #    cannot fire for an unrelated reason would pass check 1 while measuring
    #    nothing. Assert the same proposition and the same rule applies.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <reader> = implies( { +p($x) }, { +q($x) } )",
        "fact +p(thing)", ""]))
    m.run(limit=30)
    gate("...and the same rule fires the moment something asserts it "
         "(kill-probe for 1)", m.holds(kb.term("q(thing)")) is not None)

    # 3. CONSTRAINT ONE, *skip skeleton relations and computators*. Under the
    #    wrapper this is load-time work: wrapping a structural or computed
    #    member is a category error and breaks the stratum-0 test. Without the
    #    wrapper there is nothing to skip, because `match` answers a computed
    #    member by CALLING it and an ordinary one from the situation -- two
    #    branches that have been there since computators existed.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <arith> = implies("
        "    { +cost($i, $c), twice($c) as $d }, { +double($i, $d) } )",
        "fact +cost(a, 3)", ""]))
    kb.computator("twice", lambda a: int(a) * 2)
    m.run(limit=30)
    got = m.holds(kb.term("double(a, 6)"))
    about = kb.term("twice(3)")
    print(f"      the rule applied              double(a, 6) = {got}")
    print(f"      an entry ABOUT the computed   {m.holds(about) if about else None}")
    gate("a computed member is answered by CALLING it, with no entry about it "
         "anywhere -- the constraint is a branch in `match`, not a loader rule",
         got is not None and (about is None or m.holds(about) is None))

    # 4. CONSTRAINT TWO, *do not descend into mentions*. Under the wrapper the
    #    loader must refuse to expand inside a mention, exactly as aliases do.
    #    Without it, a mention deposits an entry about the MENTIONING
    #    proposition and none about what is mentioned -- which is check 1's
    #    second half, stated on its own because it is a different constraint.
    m = Machine()
    kb = load(m, "\n".join([
        "fact +said(alice, p(thing))", ""]))
    m.run(limit=8)
    print(f"      said(alice, p(thing))  {m.holds(kb.term('said(alice, p(thing))'))}")
    print(f"      p(thing)               {m.holds(kb.term('p(thing)'))}")
    gate("a mention anchors the MENTIONING proposition and not what is "
         "mentioned -- use is anchored, mention is not, structurally",
         m.holds(kb.term("said(alice, p(thing))")) is not None
         and m.holds(kb.term("p(thing)")) is None)

    # 5. THE REFLECTIVE CASE is the one place §7 admits the wrapper needs an
    #    ESCAPE: a rule about belief would be double-wrapped, and
    #    `believed(believed(p))` is meaningful. The tempting escape is *do not
    #    wrap what is already an anchor* -- and that keys the loader's decision
    #    on a NAME. Ask what the name is worth today: nothing. `believed` is
    #    not reserved, so a corpus already owns it, and the escape would read
    #    that corpus's own word as an anchor it never meant.
    m = Machine()
    reserved = "believed" in m.reserved
    kb = load(m, "\n".join([
        "rule <mine> = implies( { +believed(alice, $q) }, { +hearsay($q) } )",
        "fact +believed(alice, sky(blue))", ""]))
    m.run(limit=30)
    mine = m.holds(kb.term("hearsay(sky(blue))"))
    print(f"      `believed` is reserved        {reserved}")
    print(f"      a corpus owning the word      hearsay(sky(blue)) = {mine}")
    gate("the wrapper's escape keys on a name no corpus has to give up: "
         "`believed` is unreserved and a corpus using it loads clean",
         reserved is False and mine is not None)

    # 6. And the hazard that is the wrapper's alone. Because the wrapper lives
    #    in rule TEXT, a corpus can wrap one rule and not the next, and the two
    #    stop being about the same thing -- silently, because both load and
    #    both are well-formed. This is the 81 -> 411 measurement at fixture
    #    size. Structurally there is nothing to apply by halves.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <wrapped>   = implies( { +believed(p(thing)) }, { +w(thing) } )",
        "rule <unwrapped> = implies( { +p(thing) }, { +u(thing) } )",
        "fact +believed(p(thing))", ""]))
    m.run(limit=30)
    w, u = m.holds(kb.term("w(thing)")), m.holds(kb.term("u(thing)"))
    print(f"      the wrapped rule    w(thing) = {w}")
    print(f"      the unwrapped one   u(thing) = {u}")
    gate("a half-wrapped corpus splits into two vocabularies that cannot meet, "
         "and both halves load clean",
         w is not None and u is None)

    # 7. AND THE HONEST EXCEPTION, which is the finding rather than the
    #    verdict. `_stored` is the one walker that reads the RAW GRAPH instead
    #    of the situation, and `_as_fact` guards it by rejecting a candidate
    #    with variables in its argument positions. A GROUND structural pattern
    #    stored in a rule has none, so it passes as a fact: below, `<reader>`
    #    binds `ee` off a rule that was never applied, for a moment that does
    #    not exist. That is exactly the use/mention hazard the wrapper was
    #    invented to prevent -- on the one path the wrapper explicitly SKIPS.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <never>  = implies("
        "    { +nope(x), in_delta(mm, ee) }, { +never_out(x) } )",
        "rule <reader> = implies("
        "    { +go(x), in_delta(mm, $e) }, { +sawdelta($e) } )",
        "fact +go(x)", ""]))
    m.run(limit=30)
    leaked = m.holds(kb.term("sawdelta(ee)"))
    print(f"      bound off a rule nobody applied   sawdelta(ee) = {leaked}")
    gate("a GROUND structural pattern in a rule reads as a deposited fact -- "
         "presence IS belief, on the structural path, today",
         leaked is not None)

    # 8. The kill-probe for 7: with the rule that stores the pattern removed,
    #    there is nothing to bind and the reader finds nothing. Without this,
    #    7 could be reading a moment the machine really made.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <reader> = implies("
        "    { +go(x), in_delta(mm, $e) }, { +sawdelta($e) } )",
        "fact +go(x)", ""]))
    m.run(limit=30)
    bound = [n for n in m.g.instances_of(kb.term("sawdelta"))
             if m.holds(n) is not None]
    print(f"      ...and without that rule          {len(bound)} bindings")
    gate("and it is the stored pattern being read, not a real moment "
         "(kill-probe for 7)", bound == [])

    print()
    print("  The wrapper's stated motivation is not a hazard on the ordinary")
    print("  path; three of its four constraints are already branches in")
    print("  `match`; the fourth is the consequent's sign, which is the anchor")
    print("  build itself and no wrapper touches it. Its own hazard (6) and its")
    print("  own escape (5) are real costs. And the ONE place where presence")
    print("  really is belief -- the structural path, check 7 -- is the path the")
    print("  wrapper skips by design. See docs/wanting.md §7.")
    print()
    print(f"  {ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
