# What a fight wanted to say and could not

Answering `docs/authoring.md` §8, from the other side. The corpus is
`ugm/rules/dungeon.ugm` — 21 rules, a D&D combat round: initiative, attack rolls
against AC, damage, death, fleeing, victory, and a player acting through a
channel. Three tools: `<dice>` `roll(die, what, when)`, `<arith>` `calc(op, a, b)`,
`<compare>` `beats(a, b)`. Runner and checks in `ugm/dungeon.py`; 17 checks.

Everything below was run, not recalled. Re-verified against `e57ce0b` after the
class feature landed: the fight is unchanged at 17/0 and the suite at 472/0.

---

## 1. The census you asked for

`ugm.shapes`' own `_shapes`, over the 21 authored rules, beside your two columns:

| | internal (544) | external (14) | **dungeon (21)** |
|---|---|---|---|
| generic | 88.1% | 100% | 90.5% |
| top 1 fine shape covers | 61.0% | — | **14.3%** |
| top 3 | 80.3% | — | 28.6% |
| top 10 | 93.4% | — | 61.9% |
| the two primitives together | **73.9%** | — | **28.6%** |

antecedent sizes `{1:3, 2:5, 3:4, 4:4, 5:4, 7:1}`; 18 fine shapes for 21 rules.

**The two primitives cover 73.9% of your corpora and 28.6% of this one, and the
reason is a sign.** Your dominant shape is `implies ant[+] -> con[+p]` — pure
assertion. The dungeon's is `con-signs['+', '-']`:

| coarsest shape | | |
|---|---|---|
| `implies ant['+'] con['+', '-']` | 9 | 42.9% |
| `implies ant['+'] con['+']` | 7 | 33.3% |
| `implies ant['+', '-'] con['+', '-']` | 2 | 9.5% |
| `implies ant['-'] con['+']` | 2 | 9.5% |
| `implies ant['+'] con['-']` | 1 | 4.8% |

**12 of 21 rules (57%) retract something in their own consequent.** Not as an
occasional revision — as the normal shape. A corpus that models a *changing
world* is majority-retracting, and one that accumulates conclusions about a fixed
one is not. If the fixtures skew anywhere, they skew there.

---

## 2. §6's question: **we needed the cheap half, and only the cheap half**

You asked which half of *no rule can relate two moments* we hit. Answer:
**sequencing**, and we never once wanted a fact's own history.

What we wrote instead of *the goblin acts after the hero*:

```
fact +follows(goblin1, hero)      fact +wraps(goblin2)
fact +turn(hero, 1)               fact +may(hero, 1)

rule <pass> = causes( { +done($x,$r), +turn($x,$r), +follows($y,$x) },
                      { -turn($x,$r), -done($x,$r), +turn($y,$r), +may($y,$r) } )
rule <tick> = implies( { +turn($x,$r), +wraps($x) }, { +calc(add, $r, 1) } )
rule <wrap> = causes( { ..., +answered(<arith>, calc(add,$r,1), $r2) },
                      { -turn($x,$r), -done($x,$r), +turn(hero,$r2), +may(hero,$r2) } )
```

**5 of 21 rules — 24% of the corpus — are clock scaffold**, plus a `may(x, r)`
token threaded through all six acting rules, plus `follows`/`wraps` facts, plus
the `add` operator on the arithmetic tool, which exists *solely* to count rounds
and would otherwise not be needed at all. A round integer is a moment ordinal
re-implemented in the corpus because the real one is unreachable.

**And the expensive half never came up.** `<wound>` needs the current hp and
the new one, but it has both at one locus — the tool is handed the old value and
returns the new. Nothing in a fight ever asked *what was it before*. So on this
evidence the half-day buys the whole thing and the hard half buys nothing yet.

---

## 3. Confirming §4's , and asking you to promote it

>*Without retracting the trigger the rule debits forever.*

We found this independently, in a different domain, **three times in one corpus**,
and each time it cost a run to the limit before it was visible:

| written without | what happened |
|---|---|
| `-hits` in `<wound>` | 5−2=3, 3−2=1, 1−2=0: a goblin beaten to death by **one swing** |
| `-attack` in `<wound>` | `<hit>` re-concluded `+hits` the moment `<wound>` denied it — they alternate for ever |
| a `may(x, r)` token | `turn` is a standing fact, so acting re-fired as fast as the mechanics resolved |

The third is the general form and the one that took longest to see. `turn(hero, 1)`
is *true* for as long as it is the hero's turn — it is a perfectly good fact — and
that is exactly why acting on it re-fires. What was missing was not a denial but a
**right that acting spends**.

>**An occasion is consumed. A fact is not. If a rule models something
>*happening*, something in its antecedent must stop being true because it
>happened, and the corpus is the only thing that can arrange that.**

Quiescence cannot catch any of the three, because each pass genuinely says
something new. We would put this above §1 in the running order: §1 costs you a
rule that never fires, which is inert; this costs you a run that never ends.

---

## 4. §1 has an open-domain case it does not cover

>*Write your negatives.*

Works when the negatives are enumerable. Ours were not. We wanted *the hero
attacks by default when the player has declared nothing this round* — and the
corpus cannot write `-declares(...)` for a declaration that was never made,
because it does not know what the player might have said.

The workaround is precedence, and it reads well enough that it may be the right
answer:

```
fact overrides(<hero-acts>, <hero-holds>)     -- the declaration wins when there is one
```

Both rules match; `<hero-acts>` beating `<hero-holds>` means the standing policy
applies exactly when no declaration did. But note what that costs: **the default
is expressed as a precedence between two rules rather than as a condition**, so
you cannot read `<hero-holds>` and learn when it applies. This is the shape a
`unless(<R>, +cond)` would fix (§5), and it is a second, independent argument for
it — from absence of an *arrival*, not absence of a state.

---

## 5. A refinement to §2: scheduling rescues the collateral, but only sometimes

Your table shows `b` as permanent collateral damage under `overrides`. We wrote
`fact overrides(<gob-flees>, <gob-acts>)` and measured the same effect — one
goblin fleeing defeats the *other* goblin's attack for the step — but here it is
**a one-tick deferral, not a loss** (seed 13):

```
attack(hero, goblin2, 5)  attack(goblin1, hero, 5)  fled(goblin2)
attack(hero, goblin1, 6)  attack(goblin1, hero, 6)  attack(goblin1, hero, 7)
```

The difference is whether the **winning** situation persists. Yours does —
`a` stays poisoned, so `<poison>` matches every tick and `<regen>` is defeated
every tick, for ever. Ours does not — the goblin flees and is gone, so the
suppression happens once and *arbitration is scheduling* does the rest.

>**`overrides` is survivable when the winning rule's situation is transient, and
>permanent damage when it is not.** Worth a line in §2, because the two look
>identical when you write them and only one of them is a bug.

---

## 6. `plus` and `minus` are reserved, and a corpus finds out silently

`Machine.reserved` binds `plus`/`minus` to the **sign atoms**, and `Loader`
seeds every corpus's table from it. So:

```
rule <subtract> = implies( { ... }, { +calc(minus, $h, $n) } )
```

resolves its *operator* to the minus sign. It prints as `calc(-, 5, 2)`, the tool
declines a request it should have answered, and the fight stalls after the first
blow with nothing saying why. Renaming to `sub`/`add` fixed it.

This is the twin trap inverted — not two nodes with one name, but **one node with
two meanings**, and the corpus had no way to know the name was taken. The census
in Appendix C lists reserved names; the loader does not mention them.

**Cheap fix, in the shape §7's answerer-collision refusal already took:** when
a corpus resolves a name to a reserved node in an *argument* position, say so at
load. `plus`, `minus`, `unsure`, `not` and the numerals are the ones a domain
author will reach for by accident. A registration is a declaration, and the
silence is the defect.

---

## 7. A bug class no outcome check can see

`<halt>` written the obvious way — `{ +done($x, $r) }`, exactly what `<skip>`
writes for an absent combatant — fed `<pass>`, which let `<wrap>` count the round.
The fight was **decided correctly**, the verdict was right, every check about the
outcome was green, and the agent turned an empty room over to **round 417 across
8,072 entries**. Denying `may` instead stops it dead.

>**Nothing that asserts what the agent concluded can see it still working
>afterwards.**

That is `ugm.state`'s finding about the key set, arriving from a corpus. There is
now one check in `ugm/dungeon.py` that can see it — *were any turns granted after
the verdict* — and it was written by putting the bug back. We would suggest the
generic form is worth an instrument: **did the agent keep deriving after its goal
was reached or its verdict was written, and how much.**

---

## 8. `causes` costs 12×, and both connectives reach the same verdict

A wound is an event, so §8 says `causes`. Measured, same seed, same corpus, one
connective changed, best of three:

| | time | entries | moments |
|---|---|---|---|
| `causes` | 2.08s | 1,073 | **74** |
| `implies` | 0.17s | 736 | 1 |

12× the time for 1.5× the entries — the cost is the predicted moments and the
`expects`/`deviates`/`close` traffic over them, not the entries. Both reach
`over(hero_falls)`, so the difference is cost and not outcome.

Nothing is wrong with the surprise apparatus; it is doing exactly what §18 asks.
But **a game's rules are never wrong**, so every prediction it checks is one
nothing could ever contradict. If there is a cheap way for a corpus to say *this
rule's conclusions are not worth predicting*, an RPG would use it on nearly every
mechanic. If there is not, that is worth knowing too — it means `causes` is
priced for agents and not for simulations.

**And a warning about our own number.** The first version of this said
**660×**. It was measured while the corpus still had the runaway clock of §7, so
it compared a runaway loop against a terminating one and the connective was barely
involved. The tidy quotable figure was wrong. A measurement taken across a bug
measures the bug.

---

## 9. Still open, and what we would reach for next

Not hit by combat, because a blow touches exactly one attribute:

**Atomicity.** Gold leaving one purse and entering another is two functional
updates that must be one event. §8 permits opposite signs in one locus undetected
and there is no notion of a transaction, so we expect a corpus can **mint gold**
by interleaving a rule between the debit and the credit. That is the next thing we
mean to probe, and the shop is the corpus for it.

Also unexercised by this corpus, and worth saying so plainly since it flatters the
numbers above: **zero goals were authored.** No `+goal(...)`, so backward reading —
`fit`, `check`, `verdict`, `subgoal`, `blocked`, `<give-up>` — never ran. A fight
is entirely forward. Half the apparatus is still untested by any foreign corpus.
