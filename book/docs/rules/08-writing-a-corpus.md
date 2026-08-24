# Writing a corpus

A **corpus** is a text file of statements. There are three kinds, and you say
which, so the loader never has to guess:

```
rule <blades> = implies( { +blade($x), no weapon($x) }, { +weapon($x) } )
fact +blade(dagger)
say  user: +raining(here)
```

- **`rule`** — a relation between two sides, antecedent and consequent.
- **`fact`** — standing knowledge, stamped as having come from the knowledge
  base.
- **`say`** — an arrival on a channel. What is written is that the *channel*
  said so; whether you believe it is a rule's business.

A fact may carry a name, in the same angle brackets a rule's goes in, because
`<...>` is the namespace of **statements** and a rule is a statement:

```
fact <how-many> = count(goblin($x))
```

What the language may **not** write is a generic proposition outside a rule.
`fact +hostile($x)` is refused at load — only a rule's members may contain a
variable. An author who could write a bare universal as a fact could assert
something that binds nothing and matches nothing, silently.

```
$ python -m ugm hostile.ugm
ParseError: line 1: a fact may not contain a variable -- only a rule's
members are generic
```

## The pattern worth building a world on

Here's the one to learn first. A relation can be named by a **variable** —
`+$kind($item)` — so *the smith sells weapons* becomes a **fact**, and
applying that class to a particular sword is the rule's job.

```
rule <can-buy> = implies(
    { +wants($b, $item), +sells($s, $kind), +$kind($item),
      +stocks($s, $item), +purse($b, $coin), no offer($b, $s, $item) },
    { +offer($b, $s, $item) } )

rule <buy> = implies(
    { +offer($b, $s, $item), no bought($b, $item) },
    { +owns($b, $item), -stocks($s, $item), +bought($b, $item) } )

rule <blades> = implies( { +blade($x), no weapon($x) }, { +weapon($x) } )
```

...and then the world is **declared**, not coded:

```
fact +sells(smith, weapon)     fact +weapon(sword)     fact +blade(dagger)
fact +stocks(smith, sword)     fact +stocks(smith, dagger)
fact +purse(hero, 20)          fact +wants(hero, dagger)
```

Run it and ask:

```
$ python -m ugm shop.ugm --ask "owns(hero,dagger)"
shop.ugm: 4 ticks, ended quiescent

what it believes, newest first:
  bought(hero, dagger)
  owns(hero, dagger)
  offer(hero, smith, dagger)
  weapon(dagger)
  wants(hero, dagger)
  purse(hero, 20)
  stocks(smith, sword)
  blade(dagger)
  weapon(sword)
  sells(smith, weapon)

owns(hero,dagger): believed
```

The smith sells daggers, though nothing ever said so. One line — *a blade is a
weapon* — and a class hierarchy is an ordinary rule.

Notice every rule above carries a `no <its own conclusion>` (or `no
bought(...)`) guard. Without it, this corpus does not reach *quiescent* at
all — Chapter 7 showed why, and it is not optional here: `<blades>` alone,
left unguarded, runs to the tick limit concluding the same fact four hundred
times.

**Two things measured about this pattern, and the second is what makes it
pay:**

- the trade goes through — `owns(hero, dagger)` written, `stocks(smith,
  dagger)` erased;
- **a whole new trade is facts.** Adding armour — an armourer, an armour
  item, a shield rule — needs no new rule, only new `sells`/`stocks`/`blade`-
  style facts naming the class. A second verb (`<steal>`) reuses the same
  `sells`/`$kind` declarations, untouched.

> **`sells(smith, weapon)` names a class, and `$kind($item)` is what applies
> it.** Without a variable in the relation slot, `sells` could only ever name
> a particular item, and every merchant would need its own rule.

**The cost, so you place it deliberately.** A relation named by a variable —
`+$kind($item)` above — has no index to sit in: `rel is None` isn't true and
the relation itself isn't known until match time, so the match falls back to
scanning everything currently believed rather than one relation's bucket.
Above it's affordable because `sells` and `stocks` narrow the search first.
**Don't lead the antecedent with the unindexed member.**

## Ability catalogues are rules, not data

The tempting alternative is a data table of what does what:

```
rule <resolve> = implies( { +did($a), +achieves($a, $y), no $y },
                          { +$y } )
fact <ach> = achieves(fireball($t), burned($t))
fact +did(fireball(goblin))
```

That loads, and it never fires:

```
$ python -m ugm resolve.ugm --ask "burned(goblin)"
resolve.ugm: 1 ticks, ended quiescent

what it believes, newest first:
  did(fireball(goblin))
  achieves(fireball($t), burned($t))

burned(goblin): not believed
```

Here's the whole story in a table:

| | does `burned(goblin)` hold? |
|---|---|
| `fact achieves(fireball($t), burned($t))` | refused at load — a fact may not contain a variable |
| the same as a **named** fact | parses, and **never fires** |
| `fact achieves(fireball_goblin, burned(goblin))` | yes — but one fact per (spell, target) pair |
| `rule <fireball> = implies( { +did(fireball($t)), no burned($t) }, { +burned($t) } )` | yes |

The second row is the instructive one. A named fact *may* contain variables.
But then `$a` binds to the stored pattern `fireball($t)`, and matching that
against a ground `did(fireball(goblin))` is exactly the operation no rule may
perform (Chapter 6).

> **A fact can carry a whole ground proposition as an argument. It cannot
> carry a pattern that anything will apply.**

Same reason a universal must be a rule: `fact +hostile($x)` is refused
outright, as shown above. Don't try to put your rulebook in a fact.

## Things that will bite

**Arity slips are silent.** `purse($b)` and `purse($b, $coin)` are different
relations to the matcher the moment their argument counts differ, even though
both read `purse`. A rule keyed on the wrong arity simply never matches — no
error, because a well-formed pattern that matches nothing is indistinguishable
from one that is correctly unsatisfied yet.

**A typo loads fine and does nothing.** `watns` for `wants` is a perfectly
good proposition that nothing else mentions. The machine can't distinguish a
term awaiting its meaning from a mistake, because both are well formed and
both are inert. It *can* notice the mismatch, though, and it does — see below.

**An unguarded rule does not carve out cases; it loops.** Chapter 7's
"guard by default" isn't a style preference — an antecedent that survives its
own consequent reapplies until the tick limit, and *nothing* about the
conclusion looks wrong when it does. Every fixture built without the guard
above ran to 400 ticks and answered correctly anyway, because being right and
being finished are different questions here.

## The machine reads your corpus back

Load a corpus with a hole in it and it says so before running:

```
rule <trade> = implies( { +owns($s, $i), +wants($b, $i) },
                        { +sells($s, $b, $i) } )
fact +owns(smith, sword)
fact +watns(hero, sword)
```

```
$ python -m ugm typo.ugm
note: nothing writes wants, and a rule reads it -- so that rule can never
apply. A misspelling on either side does this; so does a fact you meant to
assert and did not
typo.ugm: 1 ticks, ended quiescent
```

That check has a precise justification: if the meaning of a word is what
follows from it, then a word nothing ever establishes means nothing, and a
corpus containing one is smaller than it looks.

The known false positive, stated rather than discovered later: a corpus that
expects a *live channel* to supply a fact at run time reads a name it never
writes, and is right to.

---

**Next:** what a corpus can tell you about its own beliefs — and what it
can't.
[Because… →](09-because.md)
