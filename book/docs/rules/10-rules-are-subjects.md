# Asking about rules

A rule is a node. So the machine can talk about one.

That sounds like a technicality. Watch what it actually gets you.

## Rules are deposited as facts, at load

The moment a rule is authored, it is also **reified** — written out as ordinary
propositions:

```
rule(<R>)                        this is a rule
ant(<R>, pattern, mode, i)       one per antecedent member, with mode and position
con(<R>, pattern, mode, i)       one per consequent member
```

`mode` is one of `assert`, `erase`, `absent` — the reified name for a
member's `+`/`-`/`no`. Which means ordinary rules can read them. Here are two,
over a corpus of two rules:

```
rule <regen> = implies( { +wounded($x), no not(poisoned($x)) }, { +heals($x) } )
rule <bleed> = implies( { +wounded($x) }, { -stable($x) } )

rule <guarded> = implies( { +ant($r, $p, absent, $i) }, { +has_a_guard($r) } )
```

```
$ python -m ugm rules.ugm --ask "has_a_guard(<regen>)" --ask "has_a_guard(<bleed>)"
note: nothing writes wounded, and a rule reads it -- so that rule can never apply.
rules.ugm: 400 ticks, ended applied
  stopped at the tick limit (400); it had not finished

what it believes, newest first:
  has_a_guard(<regen>)

has_a_guard(<regen>): believed
has_a_guard(<bleed>): not believed
```

*Which of my rules have a guard in them?* is an ordinary query, answered
correctly here well before the tick limit — `<guarded>` also matches the
machinery's own always-loaded intake rule, and (Chapter 7) nothing stops it
re-trying that match forever once it has nothing left to learn from it. A read
-only query like this one doesn't need to reach quiescence to have already
answered you; if you need it to stop cleanly, guard it the way Chapter 7 shows.

## Where a guard actually lives

There's a natural thing to want to write, and it does not work:

```
fact unless(<regen>, poisoned($x))
```

That parses. It does absolutely nothing — `heals(bo)` fires whether or not
this fact is in the corpus:

```
$ python -m ugm unless.ugm --ask "heals(bo)"
unless.ugm: 2 ticks, ended quiescent
...
heals(bo): believed
```

The reason is Chapter 2's rule about variables: a statement's variables belong
to it. So the `$x` in that fact is a **different node** from the `$x` in the
rule — measured, verified, different. Nothing binds them, and nothing reads
the relation anyway.

The guard has to be written where the rule's variables live, which is inside
the rule, and there it's an ordinary absence member:

```
rule <regen> = implies( { +wounded($x), no not(poisoned($x)) }, { +heals($x) } )
```

That's *if not*, which is all `unless` ever meant.

!!! note "Deep dive: a name is not a gap"
    `unless` sat on this project's open-questions list for a long time,
    described in three separate documents as an unbuilt feature. It was never
    unbuilt. It was a *name* for something the surface already had.

    The thing that made it look missing was that writing the guard *elsewhere*
    genuinely is hard — and once you stop wanting to write it elsewhere,
    there's nothing to build.

    The lesson recorded at the time: ask **why** something is unsayable before
    designing around it.

And moving it inside doesn't weaken *rules are subjects*, because reification
deposits each member with its mode and position. *What would stop `<regen>`
from concluding `heals`?* is a query over `ant(<regen>, not(poisoned($x)),
absent, 1)` — which is exactly what `<guarded>` above did.

> **The guard is a fact about the rule. It simply is not a fact written
> beside it.**

## What genuinely does go beside a rule

Ground arguments. Those are fine, because they don't need to share a variable
with the rule's patterns:

```
by(<regen>, boss)              who authored it
about(<regen>, healing)        what it concerns
dormant(<regen>)               a rule taken out    (Chapter 17)
```

The test is simple: if what you want to say needs to *point at one of the
rule's own variables*, it goes inside. Otherwise it goes beside.

## The wall, stated once

A rule can **name** a rule. A rule cannot **match** one.

Reification stores generic patterns. `con(<blades>, weapon($x), assert, 0)`
names a node containing a variable. A goal, `+goal(weapon(sword))`, is
ground. Deciding that the two *correspond* is matching, and matching is a
floor primitive no rule may call.

Which is why, above, the `<guarded>` rule could bind `$p` to the pattern
`not(poisoned($x))` and conclude *that there is a guard* — but could not
check whether that guard is satisfied. It can talk about the pattern. It
cannot apply it.

Four separate capabilities hit that same wall:

- reading a rule backwards (Chapter 11),
- lifting an uncertainty across a rule (Chapter 16),
- asking whether a generic subgoal is already satisfied (Chapter 12),
- composing two rules into one (Chapter 29).

Three of them now have a resolution, and all three take the same shape.

## Use and mention

Reification forces a distinction the design would otherwise not need.
`+con(<R>, boiling($w), assert, 0)` is a **ground** claim about a rule that
happens to name a node containing variables. It is not a generic claim — but
structurally the two are identical, so nothing in the *shape* can tell them
apart.

An early attempt settled it by who was writing: the machinery *mentions*, a
rule's consequent *uses*. That's too strong, and building it is how the gap
showed. A rule whose antecedent matches `+con($r, $pat, assert, $i)` binds
`$pat` to a stored pattern — so anything it concludes about `$pat` is a
rule's consequent mentioning. Under the authorship rule that write is
refused, and rules cannot reason about rules at all.

What tells them apart is inheritance:

> **Mention propagates through bindings. A conclusion drawn from a mentioned
> entry is itself a mention.**

That's checkable, because a rule authored naming another rule with `<...>` is
marked at the moment it's built (`Rule.mentions`), and the check follows the
bindings from there. That pattern recurs so often in this design that it's
worth expecting.

!!! note "Deep dive: where the refusal actually was"
    A rule reasoning about rules was never rejected by the gate. It was
    dropped by the **quiescence check**, which treated a conclusion still
    containing variables as *nothing left to do*.

    So a rule reasoning about rules looked exactly like a rule with no work:
    no error, no trace, nothing to distinguish it from correct behaviour.

    The design had said the machinery has two places it can decline —
    matching returns nothing, or the write refuses — and both are observable.
    That was one short. *This application would change nothing* is silent by
    construction, and it is the third.

---

That's Part 2. You can now write rules, run them, and interrogate the rules
themselves — though not, any more, the specific chain of belief that made one
of your conclusions true (Chapter 9 was honest about that).

**Next:** the same rules, read the other way round.
[Reading a rule backwards →](../wanting/11-backwards.md)
