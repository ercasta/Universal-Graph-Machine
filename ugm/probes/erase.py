"""Does a DELETION leave anything that still fires? (the scratchpad's one risk)

The author's call, 2026-08-20: deletion does not repoint and does not cascade,
because *no rule will match an incomplete subgraph*. That is a claim about the
matcher, so it is asked of the matcher rather than trusted.

⚠ `merge` had to answer the same question in the other direction and its answer
was the repoint -- *without it, everything said before the merge is LOST*. This
is that question, asked of the opposite operation.

There are TWO shapes of incomplete subgraph and they do not answer alike. Erase
the PREMISE and the rule fails to bind, which is checks 1-3 and is the author's
call, holding. Erase an INDIVIDUAL a surviving premise mentions and nothing is
hidden at all -- check 4. So the only safe deletion target is the anchor.

See docs/todo.md, "THE GRAPH IS A MUTABLE SCRATCHPAD", and docs/wanting.md §7.
"""

from ..core.graph import Graph
from ..core.machine import Machine
from ..core.text import load


def main() -> int:
    import sys
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

    # 1. The index forgets it, and a re-mint is a NEW node rather than the old
    #    one coming back. If it came back, deletion would be a no-op that looked
    #    like one -- the worst of the two failure modes.
    g = Graph()
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    p = g.rel(on, a, b)
    g.delete(p)
    gone = (g.find_rel(on, a, b) is None and not g.instances_of(on))
    again = g.rel(on, a, b)
    gate("a deleted node leaves the indices, and re-minting is a NEW node",
         gone and again != p)

    # 2. A rule needing two premises, with one of them deleted underneath it.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <both> = implies( { +p(?x), +q(?x) }, { +r(?x) } )",
        "fact +p(one)", "fact +q(one)", ""]))
    before = m.run(limit=60) and m.holds(kb.term("r(one)"))
    m2 = Machine()
    kb2 = load(m2, "\n".join([
        "rule <both> = implies( { +p(?x), +q(?x) }, { +r(?x) } )",
        "fact +p(one)", "fact +q(one)", ""]))
    # erase one premise's PROPOSITION out from under the entry that claims it.
    # ⚠ The id is taken BEFORE the delete: `kb2.term(...)` re-mints, so asking
    # for it afterwards hands back a different node -- check 1's finding,
    # arriving as a trap in this file's own first draft.
    erased = kb2.term("q(one)")
    m2.g.delete(erased)
    m2.run(limit=60)
    after = m2.holds(kb2.term("r(one)"))
    print(f"    both premises present   r(one) = {before}")
    print(f"    one proposition erased  r(one) = {after}")
    print()
    gate("⚠ the control fires, so the check can fail", before == "+")
    gate("⭐⭐⭐ a rule does NOT fire on a subgraph one of whose premises was "
         "erased -- the dangling half is unreachable, not wrong", after != "+")

    # 3. ...and the ENTRY that named it is still there, dangling, harming
    #    nothing. That is what *they can stay* means, measured.
    dangling = [e for mo in m2.chain.moments for e in mo.delta
                if e.proposition == erased]
    gate("...and the entry that named it is still on the chain, dangling and "
         "inert -- deletion neither repoints nor cascades",
         bool(dangling))

    # 4. The OTHER shape, and checks 1-3 do not cover it. There the premise
    #    itself was erased, so it failed to bind. Here the premise survives and
    #    an INDIVIDUAL it mentions is erased -- and `delete` only touches the
    #    indices inside `if rel is not None`, which an individual does not have.
    #    Nothing anywhere removes a node from the buckets of OTHER nodes that
    #    mention it, so everything said about it is still matched.
    m4 = Machine()
    kb4 = load(m4, "\n".join([
        "rule <see> = implies( { +is(?d, want), +about(?d, ?x) }, "
        "{ +chasing(?x) } )",
        "fact +is(d1, want)",
        "fact +about(d1, restaurant)", ""]))
    d1 = kb4.term("d1")          # the id BEFORE the delete, per check 1
    m4.g.delete(d1)
    m4.run(limit=60)
    lives = m4.holds(kb4.term("chasing(restaurant)"))
    print(f"    premise erased          the rule is not applied  ({after})")
    print(f"    individual erased       the rule IS applied      ({lives})")
    print(f"    ...and it is still indexed: "
          f"{[m4.g.show(n) for n in m4.g.instances_of(kb4.term('is'))]}")
    print()
    gate("deleting an INDIVIDUAL hides nothing: the propositions that mention "
         "it are still indexed and still matched, so the rule is applied "
         "anyway. *No rule matches an incomplete subgraph* is true of an erased "
         "PREMISE and not of an erased individual",
         lives == "+")
    gate("...which is the pair that makes it a finding rather than a fixture: "
         "the two erasures differ, and only the first one hides anything",
         after != "+" and lives == "+")
    print("    consequence: the only safe deletion target is the ANCHOR.")
    print("    Delete anchors; never propositions, never individuals.")

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
