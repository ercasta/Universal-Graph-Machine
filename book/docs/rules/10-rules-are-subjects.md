# Asking about rules

A rule is a node. So the machine can talk about one.

That sounds like a technicality. Watch what it actually gets you.

## Rules are deposited as facts, at load

The moment a rule is authored, it is also **reified** — written out as ordinary
propositions:

```
rule(<R>)                        this is a rule
conn(<R>, implies)               which connective
ant(<R>, pattern, sign, i)       one per antecedent member, with sign and position
con(<R>, pattern, sign, i)       one per consequent member
```

Which means ordinary rules can read them. Here are two, over a corpus of two
rules:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
rule <bleed> = causes(  { +wounded(?x) }, { -stable(?x) } )

rule <guarded> = implies( { +ant(?r, ?p, minus, ?i) }, { +has_a_guard(?r) } )
rule <lasting> = implies( { +conn(?r, causes) },        { +persists(?r) } )
```

```
why has_a_guard(<regen>)?
  +has_a_guard(<regen>) @M1, via kb, licensed by applied(<guarded>)
    because +ant(<regen>, poisoned(?x), -, 1) @M0, via kb, licensed by reified(<regen>)

why persists(<bleed>)?
  +persists(<bleed>) @M1, via kb, licensed by applied(<lasting>)
    because +conn(<bleed>, causes) @M0, via kb, licensed by reified(<bleed>)
```

*Which of my rules have an exception in them? Which of my conclusions will
survive their premises being withdrawn?* Ordinary queries, and the licence says
`reified(<regen>)` — that fact exists because a rule was loaded.

## Where a guard actually lives

There's a natural thing to want to write, and it does not work:

```
fact unless(<regen>, poisoned(?x))
```

That parses. It does absolutely nothing.

The reason is Chapter 2's rule about variables: a statement's variables belong
to it. So the `?x` in that fact is a **different node** from the `?x` in the
rule — measured, verified, different. Nothing binds them, and nothing reads the
relation anyway.

The guard has to be written where the rule's variables live, which is inside the
rule, and there it's an ordinary negated member:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
```

That's *if not*, which is all `unless` ever meant. It has been available since
there were members.

!!! note "Deep dive: a name is not a gap"
    `unless` sat on this project's open-questions list for a long time, described
    in three separate documents as an unbuilt feature. It was never unbuilt. It
    was a *name* for something the surface already had.

    The thing that made it look missing was that writing the guard *elsewhere*
    genuinely is hard — and once you stop wanting to write it elsewhere, there's
    nothing to build. Zero lines of engine were written to close it.

    The lesson recorded at the time: ask **why** something is unsayable before
    designing around it. Two other items on the same list turned out not to be
    walls either, and each took about an hour once somebody asked.

And moving it inside doesn't weaken *rules are subjects*, because reification
deposits each member with its sign and position. *What would cancel `<regen>`?*
is a query over `ant(<regen>, poisoned(?x), -, 1)` — which is exactly what the
`<guarded>` rule above did.

> **The guard is a fact about the rule. It simply is not a fact written beside
> it.**

## What genuinely does go beside a rule

Ground arguments. Those are fine, because they don't need to share a variable
with the rule's patterns:

```
by(<regen>, boss)              who authored it
about(<regen>, healing)        what it concerns
overrides(<poison>, <regen>)   which of two wins  (Chapter 17)
```

The test is simple: if what you want to say needs to *point at one of the rule's
own variables*, it goes inside. Otherwise it goes beside.

## The wall, stated once

A rule can **name** a rule. A rule cannot **match** one.

Reification stores generic patterns. `con(<boil>, boiling(?w), +, 0)` names a
node containing a variable. A goal, `+goal(boiling(kettle))`, is ground.
Deciding that the two *correspond* is matching, and matching is a floor
primitive no rule may call.

Which is why, above, the `<guarded>` rule could bind `?p` to the pattern
`poisoned(?x)` and conclude *that there is a guard* — but could not check
whether that guard is satisfied. It can talk about the pattern. It cannot apply
it.

Four separate capabilities hit that same wall:

- reading a rule backwards (Chapter 11),
- lifting an uncertainty across a rule (Chapter 16),
- asking whether a generic subgoal is already satisfied (Chapter 12),
- composing two rules into one (Chapter 27).

Three of them now have a resolution, and all three take the same shape.

## Use and mention

Reification forces a distinction the design would otherwise not need.
`+con(<R>, boiling(?w), +, 0)` is a **ground** claim about a rule that happens to
name a node containing variables. It is not a generic claim — but structurally
the two are identical, so nothing in the *shape* can tell them apart.

An early attempt settled it by who was writing: the machinery *mentions*, a
rule's consequent *uses*. That's too strong, and building it is how the gap
showed. A rule whose antecedent matches `+con(?r, ?pat, +, ?i)` binds `?pat` to
a stored pattern — so anything it concludes about `?pat` is a rule's consequent
mentioning. Under the authorship rule that write is refused, and rules cannot
reason about rules at all.

What tells them apart is inheritance:

> **Mention propagates through bindings. A conclusion drawn from a mentioned
> entry is itself a mention.**

That's checkable rather than declared, because the entries an application
consumed are already recorded — the trail, needed for explanation, turning out
to be load-bearing for something else. That pattern recurs so often in this
design that it's worth expecting.

!!! note "Deep dive: where the refusal actually was"
    A rule reasoning about rules was never rejected by the gate. It was dropped
    by the **quiescence check**, which treated a conclusion still containing
    variables as *nothing left to do*.

    So a rule reasoning about rules looked exactly like a rule with no work: no
    error, no trace, nothing to distinguish it from correct behaviour.

    The design had said the machinery has two places it can decline — matching
    returns nothing, or the write refuses — and both are observable. That was
    one short. *This application would change nothing* is silent by
    construction, and it is the third.

---

That's Part 2. You can now write rules, run them, and interrogate both the
conclusions and the rules themselves.

**Next:** the same rules, read the other way round.
[Reading a rule backwards →](../wanting/11-backwards.md)
