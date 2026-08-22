# A rule is a fact about two moments

Here is the whole of it:

```
<R> = causes( <A>, <B> )
```

`<A>` and `<B>` are generic moments (Chapter 4): variables, no anchored
predecessor. `<A>` is the **antecedent** — what must hold. `<B>` is the
**consequent** — what follows. Because a moment is a signed delta, `<B>` is a
delta *relative to* `<A>` without being a second kind of object.

In the surface you write it like this:

```
rule <boil> = causes( { +heat($a, $w), +water($w) },
                      { +boiling($w), -liquid($w) } )
```

And that is a **relation instance** — a node named `<boil>`, whose relation is
`causes` and whose two members are the antecedent and consequent moments.

Which means there is no rule syntax distinct from fact syntax here, because
there is no rule *node* distinct in kind from a fact node.

## Which buys three things immediately

**Rules are subjects.** Because `<R>` is a node, anything else can be about it:

```
by(<boil>, boss)              who authored it
dormant(<cool>)               a rule that is out of the running
about(<boil>, kitchen)        what it concerns
```

*A rule the boss gave beats one the vice gave* is now an ordinary fact, not a
feature.

**Rules are askable, not merely runnable.** *Which rules are about time? Which
disturb position? Which come from the boss?* are ordinary queries over members,
because the rule's content is data rather than a program. Chapter 10 does this
properly.

**Both readings come from one statement.** Planning reads a rule backwards
(*what would make this goal true?*); execution reads it forwards (*what follows
from this?*). Two separate statements, one per direction, would drift apart with
nothing able to detect the disagreement — neither is the premise of the other.
Part 3 is the backward reading.

## Why not a program with a guard?

The obvious alternative is *condition → body*: a guard, and some code to run.
Score it against the four criteria:

| | guard → program body | one rule per direction | **`connective(moment, moment)`** |
|---|---|---|---|
| not leaking | the backward read is hypothesis wearing entailment's clothes, with nowhere to record it | two statements drift; neither is the other's premise | one statement; each reading cites `<R>` |
| not lossy | what it makes true is recoverable only by running it | the pair coheres only by convention | `<B>` **is** the postcondition; `?` preserves a gap instead of erasing it |
| readable | runnable, not askable | readable, doubled | every question is a query over members |
| composable | two bodies cannot be joined | n directions means 2ⁿ statements | join on signed membership |

And the program form fails one more test outright: `dormant(<R1>)` has
no subject when a rule is a program. Nothing can be said *about* it — and
Chapter 29, where the agent writes itself a rule, becomes unreachable entirely,
because a rule the agent authored has nothing to be authored *as*.

## An antecedent is a sequence of members

Each member is an entry pattern: a sign and a proposition.

```
{ +heat($a, $w), +water($w), -altitude($w, high) }
```

`+on($x, $y)` means *an entry with this proposition and this sign*. A member can
also name **what it matched**, as a whole:

```
rule <blame> = implies( { +broke($p, $thing) as $what },
                        { +regrets($p, $what) } )
```

```
regrets(bo, broke(bo, jug))
```

`as $t` binds the proposition itself, so a rule can refer to the very thing it
matched rather than describing it again.

!!! note "There used to be a second modifier, and it is gone"
    `at $m` bound the **locus** — where the matched entry sat. An entry has no
    locus any more (Chapter 19 tells that story), so the surface **refuses**
    `at $m` rather than ignoring it: a notation that parses and is dropped is a
    rule that means something other than what it says. Reading history is now
    done with the chain's own relations — Chapter 23.

**Order matters.** Not for correctness of matching — the machine is free to walk
the members in whatever order narrows fastest — but because the trail records
which entries an application consumed, *by member position*. So authored order
is what the explanation and the tie-breaking see.

> The **walk** may be reordered freely. The **antecedent** may not.

!!! note "Deep dive: an invariant a whole test suite can't see"
    Filling the consumed-entries list in walk order rather than member order
    fails nothing. Every conclusion is identical; only the record differs. It
    had to be asserted directly, by a fixture built so that the reordered walk
    actually runs.

    That shape — a defect that changes the *record* and never the *answer* —
    recurs throughout this project, and Chapter 32 is largely about how to build
    checks that can see it.

## Two kinds of member

There is a second kind of member, and it isn't a claim at all:

```
skeleton   anc($a, $b),  in_delta($m, $e),  entry_of($e, p, plus)
claims     +on($x, $y),  +acts($a)
```

The **skeleton** relates moments and entries to each other. `anc`, `sanc`,
`pred`, `in_delta`, `entry_of`, `rests_on` — these match *structure*, not
entries. They have no sign and no licence, because nobody asserted them:
they're facts about how a node is built, not relations in the world.

A skeleton member must be **anchored** — at least one of its arguments already
bound — because an unanchored one would enumerate the whole history. That is a
rule you will meet again in Chapter 23.

The two kinds don't merge, and Chapter 31 explains why that separation is what
lets the machine boot at all.

Distinctness lives in the skeleton for the same reason. `$a ≠ $b` is a condition
on the binding, not a dated claim that two individuals differ.

## Reification: a rule read back out

The moment a rule is authored, it is also deposited as ordinary facts:

```
rule(<R>)      conn(<R>, implies)
ant(<R>, pattern, sign, i)      con(<R>, pattern, sign, i)
```

Both the **position** and the **sign** are members, and leaving either out makes
a rule read back out of the graph a *different* rule. Position matters because
an antecedent is a sequence, and because relation instances intern — a rule with
two identical members would silently lose one. Sign matters because `{+p} ⟹ {+q}`
and `{+p} ⟹ {−q}` would otherwise become the same node, and then a claim about
one of them — `dormant`, `standing`, `intercepts` — would silently be a claim
about the other.

!!! note "Deep dive: how that could have stayed hidden"
    Reading a rule's members back in *minting* order reproduces authored order by
    accident, for anything the machinery itself wrote. So a check over
    machine-written rules could never have failed. The fixture that catches it
    deposits out of order on purpose.

## One thing a rule cannot do

A rule can **name** a rule. A rule cannot **match** one.

```
con(<boil>, boiling($w), +, 0)     what reification stores: a generic pattern
+goal(boiling(kettle))             what a goal is: ground
```

A rule that tried to relate those needs one variable to be both the generic
pattern and the ground goal — and deciding that the two *correspond* is exactly
matching, which is a floor primitive that no rule may call (Chapter 30).

Four separate ambitions hit that same wall: reading a rule backwards, lifting an
uncertainty across a rule, asking whether a generic subgoal is already
satisfied, and composing two rules into one. Three of them now have a
resolution, and all three take the same shape — a **request** whose answer
arrives already instantiated. Chapter 11 shows the first one working.

---

**Next:** `causes` and `implies`. There are exactly two, and there's a test for
why.
[Two connectives, and why exactly two →](07-connectives.md)
