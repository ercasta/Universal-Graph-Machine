# The bootstrap

If rules are facts, and applying a rule means checking whether its antecedent
holds, and checking whether something holds is itself something the agent has
to *do* — then reading a rule requires doing work, and if that work is also
made of rules, nothing ever starts.

This chapter states that circle precisely, and then tells the two-part story of
how the design actually avoided it: first by drawing a careful line through the
rules (a line this book used to call **stratum 0**), and then, later, by
removing the reason the line was needed at all.

## Only one of four steps could have been circular

Applying a rule takes four steps:

| step | what it needs | circular? |
|---|---|---|
| 1. propose candidate rules | **recall** — a function from situation to node ids | no |
| 2. read the rule's structure | members and positions | no |
| 3. check that its antecedent's members hold | **belief lookup** | no, today |
| 4. commit | the gate, the total step | no |

Step 2 is where it's easy to go wrong. Reading a rule's *structure* is not
reading its meaning: an antecedent is a node with members, and getting at them
needs ordering and nothing else — floor, per Chapter 30.

Step 3 is the one this chapter is about, and the honest answer today is *no,
not circular* — but that answer took a redesign to earn, and the history is
worth having.

## What used to make step 3 circular

An earlier version of this engine kept belief as an append-only chain: entries
deposited at moments, and *does this hold* meant walking the chain — which
moment came before which, what was deposited where. `ugm/core/rules.py` still
carries the epitaph, in its own module docstring:

> There is also one MATCHER. The second one read the chain's skeleton — `pred`,
> `in_delta`, `anc` — as structure rather than as claims, and the whole
> stratification apparatus existed to keep the two from chasing each other.

*The whole stratification apparatus.* That's stratum 0: a class of rules whose
antecedent was **entirely structural** — membership, position, node identity,
predecessor, nothing that asked *does X hold* — so they could be applied by
matching alone, without walking anything. A rule like:

```
rule <order> = implies( { +in_delta($m, $e), +entry_of($e, p, assert) },
                        { +candidate($e, p) } )
```

had every antecedent member answerable by structure, so step 3 for it never
recursed into step 3 again. That was the fixed point:

> **Stratum 0** — every antecedent member is structural. Applied without a
> read.
>
> **Stratum 1 and above** — some antecedent member asks whether something
> holds. Applied by the read that stratum 0 implements.

The check was a scan, decided by **inspecting an antecedent** rather than by a
designer assigning layers — and it worked. It is also, today, **not how this
engine reads a rule at all.**

## The skeleton went with the chain

`pred`, `anc`, `sanc`, `in_delta`, `entry_of`, `delta_next`, `rests_on` are not
reserved names any more. Nothing in `Machine.reserved` claims them, and nothing
in `match` gives them special treatment. Loading a rule that names them proves
it:

```python
kb = load(m, """
    rule <r> = implies( { +anc($s, $a) }, { +older($s, $a) } )
    fact +anc(m2, m1)
""")
m.run(limit=5)
```

```
older(m2,m1)? True
anc reserved? False
```

`anc` matched because it was **asserted as an ordinary fact**, the same as
`older` or `poisoned` or any other word a corpus invents — not because the
engine recognises it as a chain-walking primitive. There is no second matcher
for it, because there is no first one either: the append-only chain that
`pred`/`anc`/`in_delta` used to describe is gone, replaced by the scratchpad —
belief is `believed(p)` or it isn't, a single anchor lookup.

And `at $m`, the locus a member used to bind, is refused outright:

```
ParseError: line 1: `at $m` is gone with the locus. An entry has no second
time to bind, so a member cannot say where it sits -- read the chain
instead: `in_delta($m, $e), entry_of($e, p, +)` is the same claim, and
`anc`/`sanc` order the moments.
```

That error message is itself a fossil — it still recommends the chain it is
describing the retirement of. Don't follow its advice; there is nothing left
for `in_delta` or `entry_of` to hook into. Write ordinary relations of your
own if you need to talk about order, the way the passenger-rights corpus
writes `before`/`after` over its own vocabulary.

## Why step 3 stopped being circular, instead of being solved

`Scratchpad.holds` — the operation step 3 actually calls today — is one dict
lookup. It is not a rule, was never compiled from rules, and has no rule-level
definition standing behind it the way `Graph.has_var` has `_has_var_slow`
(Chapter 30). It is floor by the same argument that makes matching floor:
*checking whether a proposition is anchored* is exactly the kind of question a
read needs answered before it can do anything else, so it was never a
candidate for being *implemented as* a read.

Stratum 0 solved a circularity that existed because the chain walk was
*partly* built out of rules. Once belief stopped being a walk at all, there was
nothing left of step 3 for rules to reach into, circularly or otherwise. The
regress didn't get resolved. It stopped having a place to occur.

## Three regresses, one escape

The bootstrap was never a special problem. It's one instance of a shape this
design meets three times:

| regress | what stops it | what stops it is |
|---|---|---|
| reading needs reading | belief is a floor lookup, never a rule | a function |
| selecting needs selecting | the total tiebreak | a function |
| proposing needs proposing | recall | a function |

All three bottom out in **a function, not a search** — the same shape as the
two irreducible floor items in Chapter 30. That recurrence is the strongest
evidence available that the floor is drawn in the right place.

Recall is worth demonstrating, because it's the only component consulted
**before any rule has applied at all**:

```python
kb = load(m, "rule <boil> = implies( { +heat($w) }, { +boiling($w) } )")
about = kb.term("boiling(x)")
m.gate.write(m.g.rel(m.RECALL, about), generic=True)
m.run(limit=5)
```

```
recalled <boil>? True
```

`_answer_recall` (`ugm/core/machine.py`) answers this by an index kept by
conclusion — `by_conclusion`, keyed at the moment each rule is authored — a
lookup, not a search over the rule set. It has no antecedent to fail to read,
which is what makes it eligible to run first.

!!! note "Deep dive: there were two matchers, and one had to go"
    Worth telling as history, because the version with two matchers *worked*
    for a long time, under the old chain design.

    A skeleton member like `sanc($mq, $mp)` was said to be unmatchable, on the
    grounds that it has no sign, no locus and no licence — nobody asserted it,
    so it has no entry. That didn't follow: `pred(M3, M2)` was an ordinary
    relation instance, simply not in the *resolved state* the ordinary matcher
    was given — while stratum 0 matched the very same nodes with a second
    matcher, forbidden by the very *one interpreter* rule this book keeps
    coming back to.

    Merging the two matchers deleted an entire module — a second engine with
    its own rule type, item type and solver, over the same nodes. Two things
    fell out of that merge that weren't obvious at the time:

    - **Negation needs no notation.** A structural member has no entry, so a
      sign on one can only mean *not derived*.
    - **The layers must be derived, not assigned.** The strongly connected
      components of the dependency graph decide stratum, not a designer.

    Merging the matchers was the *first* step away from the two-tier design.
    Retiring the chain the skeleton described — and stratum 0 along with it —
    was the second, and it's the one this chapter has been about.

## What stratum 0 cost, and what replaced it

Stratum 0's own constraint, while it existed, was strict: **it had to produce
structure, not entries.** If the walk had deposited its intermediate results as
claims, it would have been reading claims to do so, and the circle would have
returned. So its working state was undated, unattributed and unexplained by
design — the price for using an ordinary rule to do the walking.

That price is why `Machine` has no `why`. The read a rule performs today —
`match`, `candidates`, `Scratchpad.holds` — is Python, permanently, and there
is no rule-level definition of it standing beside the fast path the way there
is for `has_var`. Promoting it into an ordinary rule would reinstate exactly
the regress stratum 0 was built to dodge, so nothing does. That isn't an
oversight to fix later; [what is not built](../horizon/34-not-built.md) lists
it as deliberate, at a real and named cost: you cannot ask *why did you read
it that way* through the same mechanism you ask *why do you believe that*.

What *is* still true of stratum 0's original promise is the part that never
depended on the chain: rules themselves are ordinary data. `Machine.reify`
believes `rule(<R>)` and every member of every side the moment a rule is
authored, which is a write like any other — floor, needing only the gate and
the total step. An agent can author a rule at run time and
have it enter recall and the table on the next tick. What it cannot do any
longer is author a *replacement for the read itself* — that capability left
with the layer that made it meaningful to ask for.

---

**Next:** the number that says whether any of this is true of the implementation.
[Zero phases →](32-zero-phases.md)
