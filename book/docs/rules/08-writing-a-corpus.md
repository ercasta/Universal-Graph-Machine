# Writing a corpus

A **corpus** is a text file of statements. There are three kinds, and you say
which, so the loader never has to guess:

```
rule <boil> = causes( { +heat(?a, ?w) }, { +boiling(?w) } )
fact +water(kettle)
say  user: +raining(here)
```

- **`rule`** — a relation between two generic moments.
- **`fact`** — standing knowledge, stamped as having come from the knowledge
  base.
- **`say`** — an arrival on a channel. What is written is that the *channel*
  said so; whether you believe it is a rule's business (Chapter 21).

A fact may carry a name, in the same angle brackets a rule's goes in, because
`<...>` is the namespace of **statements** and a rule is a statement:

```
fact <no-harm> = forbidden(doing(harm(?x)))
fact overrides(<boil>, <cool>)
```

What the language may **not** write is an entry, a moment, or a stamp. An author
who could supply a deposit could date a claim to a time when it wasn't held. So
the locus, the licence and the source always come from the machinery.

## The pattern worth building a world on

Here's the one to learn first. A relation can be named by a **variable** —
`+?kind(?item)` — so *the smith sells weapons* becomes a **fact**, and applying
that class to a particular sword is the rule's job.

```
rule <can-buy> = implies(
    { +wants(?b, ?item), +sells(?s, ?kind), +?kind(?item),
      +stocks(?s, ?item), +purse(?b, ?coin) },
    { +offer(?b, ?s, ?item) } )

rule <buy> = causes(
    { +offer(?b, ?s, ?item), +purse(?b, ?coin) },
    { +owns(?b, ?item), -stocks(?s, ?item), ? purse(?b, ?coin) } )

rule <blades> = implies( { +blade(?x) }, { +weapon(?x) } )
```

...and then the world is **declared**, not coded:

```
fact +sells(smith, weapon)     fact +weapon(sword)     fact +blade(dagger)
fact +stocks(smith, sword)     fact +stocks(smith, dagger)
fact +purse(hero, 20)          fact +wants(hero, dagger)
```

Run it and ask:

```
why owns(hero,dagger)?
  +owns(hero, dagger), via kb, licensed by applied(<buy>)
    because +offer(hero, smith, dagger), via kb, licensed by applied(<can-buy>)
    because +purse(hero, 20), via kb, licensed by loaded(purse(hero, 20))
    because +wants(hero, dagger), via kb, licensed by loaded(wants(hero, dagger))
    because +sells(smith, weapon), via kb, licensed by loaded(sells(smith, weapon))
    because +weapon(dagger), via kb, licensed by applied(<blades>)
    because +stocks(smith, dagger), via kb, licensed by loaded(stocks(smith, dagger))
    because +blade(dagger), via kb, licensed by loaded(blade(dagger))
```

The smith sells daggers, though nothing ever said so. One line — *a blade is a
weapon* — and a class hierarchy is an ordinary rule.

Three things measured about this pattern, and the last two are what make it pay:

| | |
|---|---|
| the trade goes through | `owns(hero, dagger)` `+`, `stocks(smith, dagger)` `−` |
| **a whole new trade is facts** | armourer / armour / shield: **5 facts, 0 new rules** |
| **a second verb reuses the declarations** | a `<steal>` rule keys on the same `sells` and `?kind`, untouched |

> **`sells(smith, weapon)` names a class, and `?kind(?item)` is what applies
> it.** Without a variable in the relation slot, `sells` could only ever name a
> particular item, and every merchant would need its own rule.

**The cost, so you can place it deliberately.** A variable relation in a
*consequent* is free at match time and cheaper overall, because one rule
replaces many. In an *antecedent* it loses the relation index — the pattern has
no bucket, so it scans. Measured at **14× the comparisons** on a small world
with 200 unrelated facts. Above, `?kind(?item)` is affordable because `sells`
and `stocks` narrow it first. **Don't lead with the unindexed member.**

## Ability catalogues are rules, not data

The tempting alternative is a data table of what does what:

```
rule <resolve> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )
fact achieves(fireball_goblin, burned(goblin))
```

That works, and it does not parameterise. Here's the whole story in a table:

| | does `burned(goblin)` hold? |
|---|---|
| `fact achieves(fireball(?t), burned(?t))` | refused at load — a fact may not contain a variable |
| the same as a **named** fact | parses, and **never fires** |
| `fact achieves(fireball_goblin, burned(goblin))` | yes — but one fact per (spell, target) pair |
| `rule <fireball> = implies( { +did(fireball(?t)) }, { +burned(?t) } )` | yes |

The second row is the instructive one. A named fact *may* contain variables. But
then `?a` binds to the stored pattern `fireball(?t)`, and matching that against
a ground `did(fireball(goblin))` is exactly the operation no rule may perform
(Chapter 6).

> **A fact can carry a whole ground proposition as an argument. It cannot carry
> a pattern that anything will apply.**

Same reason a universal must be a rule: `fact +hostile(?x)` is refused outright.
Don't try to put your rulebook in a fact.

## Things that will bite

**Arity slips are silent.** Writing `? purse(?b)` against a `purse(hero, 20)`
fact invalidates a *different proposition* — one nobody asserted — and the old
amount goes on reading `+`. Nothing complains.

**A typo loads fine and does nothing.** `watns` for `wants` is a perfectly good
proposition that nothing else mentions. The machine can't distinguish a term
awaiting its meaning from a mistake, because both are well formed and both are
inert. It *can* notice the mismatch, though, and it does — see below.

**Precedence does not carve out cases.** *Poison stops regeneration* written as
`fact overrides(<poison>, <regen>)` stops regeneration for **everybody** the
moment anybody is poisoned. Chapter 17 has the measurement. Put the exception in
the antecedent, as a negated member.

## The machine reads your corpus back

Load a corpus with a hole in it and it says so before running:

```
$ python -m ugm goal.ugm
note: nothing writes heat, and a rule reads it -- so that rule can never apply.
A misspelling on either side does this; so does a fact you meant to assert and
did not
```

That check has a precise justification, and it's Chapter 33's subject: if the
meaning of a word is what follows from it, then a word nothing ever establishes
means nothing, and a corpus containing one is smaller than it looks.

Only one direction is a signal, and that had to be measured to find out which:

| | on four healthy corpora | on a corpus with a planted typo |
|---|---|---|
| **written, never read** | 11–17 names — bookkeeping, and a corpus's own *outputs* | fires, but buried |
| **read, never written** | **0, 0, 0, 0** | **1, and it is the bug** |

A typo always breaks a pairing, and a broken pairing always leaves some reader
with no writer — so it's caught whether the misspelling lands in the rule or in
the fact.

The known false positive, stated rather than discovered later: a corpus that
expects a *live channel* to supply a fact at run time reads a name it never
writes, and is right to.

---

**Next:** the answer to *why*, and why finding it is the same act as finding the
answer.
[Because… →](09-because.md)
