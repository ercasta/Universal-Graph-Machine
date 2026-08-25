# A rule is a fact about two sides

Here is the whole of it:

```
<R> = implies( <A>, <B> )
```

`<A>` and `<B>` are **sides** — sequences of signed members (Chapter 2's signs).
`<A>` is the **antecedent** — what must hold. `<B>` is the **consequent** —
what follows.

In the surface you write it like this:

```
rule <blades> = implies( { +blade($x), no weapon($x) }, { +weapon($x) } )
```

And that is a **relation instance** — a node named `<blades>`, whose relation
is `implies` and whose two members are the antecedent side and the consequent
side.

Which means there is no rule syntax distinct from fact syntax here, because
there is no rule *node* distinct in kind from a fact node.

## Which buys three things immediately

**Rules are subjects.** Because `<R>` is a node, anything else can be about it:

```
by(<blades>, boss)              who authored it
dormant(<cool>)                 a rule that is out of the running
about(<blades>, taxonomy)       what it concerns
```

*A rule the boss gave beats one the vice gave* is now an ordinary fact, not a
feature.

**Rules are askable, not merely runnable.** *Which rules are about combat?
Which erase something? Which come from the boss?* are ordinary queries over
members, because the rule's content is data rather than a program. Chapter 10
does this properly.

**Both readings come from one statement.** Planning reads a rule backwards
(*what would make this goal true?*); execution reads it forwards (*what
follows from this?*). Two separate statements, one per direction, would drift
apart with nothing able to detect the disagreement — neither is the premise of
the other. Part 3 is the backward reading.

## Why not a program with a guard?

The obvious alternative is *condition → body*: a guard, and some code to run.
Score it against the four criteria:

| | guard → program body | one rule per direction | **`implies(side, side)`** |
|---|---|---|---|
| not leaking | the backward read is hypothesis wearing entailment's clothes, with nowhere to record it | two statements drift; neither is the other's premise | one statement; each reading cites `<R>` |
| not lossy | what it makes true is recoverable only by running it | the pair coheres only by convention | `<B>` **is** the postcondition, a sequence of signed writes |
| readable | runnable, not askable | readable, doubled | every question is a query over members |
| composable | two bodies cannot be joined | n directions means 2ⁿ statements | join on signed membership |

And the program form fails one more test outright: `dormant(<R1>)` has
no subject when a rule is a program. Nothing can be said *about* it — and
Chapter 29, where the agent writes itself a rule, becomes unreachable entirely,
because a rule the agent authored has nothing to be authored *as*.

## An antecedent is a sequence of members

Each member is an entry pattern: a sign and a proposition.

```
{ +heat($a, $w), +water($w), no altitude($w, high) }
```

`+on($x, $y)` means *this is currently believed*. A member can also name
**what it matched**, as a whole:

```
rule <blame> = implies( { +broke($p, $thing) as $what, no regrets($p, $what) },
                        { +regrets($p, $what) } )
```

```
regrets(bo, broke(bo, jug))
```

`as $t` binds the proposition itself, so a rule can refer to the very thing it
matched rather than describing it again.

**Order matters for one concrete reason: an absence member's variables must
already be bound.** `no p($x)` is a *check*, not a binder — it cannot be the
first thing in an antecedent to mention `$x`, because *for no `$x`* is a
negative existential no member is allowed to state (Chapter 9 in Part 4 has
the argument). Get the order wrong and the loader says so:

```
rule <bad> = implies( { no poisoned($x), +wounded($x) }, { +heals($x) } )
```

```
ParseError: line 1: rule 'bad' asks `no poisoned($x)` with a variable no
earlier member binds -- an absence is a check on things already picked out,
never a way of picking them out
```

Beyond that, member order does not decide correctness of matching — the
machine is free to walk the members in whatever order narrows the search
fastest.

## Reification: a rule read back out

The moment a rule is authored, it is also deposited as ordinary facts:

```
rule(<R>)
ant(<R>, pattern, mode, i)      con(<R>, pattern, mode, i)
```

one `ant`/`con` per member, `mode` one of `assert`/`erase`/`absent`, `i` the
member's position. Both the **position** and the **mode** are recorded, and
leaving either out makes a rule read back out of the graph a *different* rule:
position matters because a side is a sequence — a rule read back without it
could not say which member came first; mode matters
because `{+p} ⟹ {+q}` and `{+p} ⟹ {−q}` would otherwise be the same node, and
a claim about one of them would silently be a claim about the other.

## One thing a rule cannot do

A rule can **name** a rule. A rule cannot **match** one.

```
con(<blades>, weapon($x), assert, 0)     what reification stores: a generic pattern
+goal(weapon(sword))                     what a goal is: ground
```

A rule that tried to relate those needs one variable to be both the generic
pattern and the ground goal — and deciding that the two *correspond* is
exactly matching, which is a floor primitive that no rule may call (Chapter
30).

Four separate ambitions hit that same wall: reading a rule backwards, lifting
an uncertainty across a rule, asking whether a generic subgoal is already
satisfied, and composing two rules into one. Three of them now have a
resolution, and all three take the same shape — a **request** whose answer
arrives already instantiated. Chapter 11 shows the first one working.

---

**Next:** there is one connective. Here's how it's used, and the hazard to
watch for.
[The one connective →](07-connectives.md)
