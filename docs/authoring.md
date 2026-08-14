# Notes for a corpus author

`docs/rules-design.md` is the design. This is the shorter, meaner document: **what actually bites when
you sit down and write a corpus**, ordered by how much time it costs before you find it.

Every claim below was run against the engine at commit `95d7c90` or later, not recalled. Where a number is
quoted from an earlier measurement rather than re-run here, it says so. Snippets are copy-pasteable.

The design's own conventions apply to this file: a claim with no measurement behind it is an opinion,
and it is marked as one.

---

## 1. `−` means *denied*, never *absent*

This is the one that will cost you the most, because it fails **silently** — the rule simply never
applies, and nothing anywhere says why.

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
fact +wounded(b)                     -- and nothing ever mentions poisoned(b)

heals(b) = None                      -- the rule does NOT fire
```

§9: a `−` member matches **an entry that says this does not hold**. It does not match *no entry*.
Absence means *inherit from the predecessor*, which is a positive claim that things are as they were —
not a claim that anything is false.

If you are coming from anything closed-world, essentially every "if not stunned / not dead / not
already open" rule you write will be inert. Two fixes, both measured working:

```
fact -poisoned(b)                                              -- say it outright
rule <clean> = implies( { +wounded(?x), -bitten(?x) },         -- or derive the default
                        { -poisoned(?x) } )
```

> **Write your negatives.** An RPG state block that lists only what *is* true will not drive a rule
> set that asks what is *not*.

---

## 2. Precedence does not do per-entity exceptions

*Poison stops regeneration.* `a` is poisoned, `b` is not. Both are wounded.

| how it is written | `heals(a)` | `heals(b)` | |
|---|---|---|---|
| `fact overrides(<poison>, <regen>)` | `−` | **`None`** | b is collateral damage |
| `fact supersedes(<poison>, <regen>)` | **`+`** | `+` | nothing is defeated at all |
| the exception as a premise, with the denial made real (§1 above) | `−` | `+` | ✅ |

**`overrides` is per tick and per rule.** If poison matched *anywhere* this step, regeneration does not
apply — to anyone. **`supersedes` needs a shared consumed entry**, and these two rules consume
`poisoned(a)` and `wounded(a)`, which have nothing in common, so nothing is defeated.

Neither relation expresses *this creature is the exception*. `unless(<regen>, +poisoned(?x))` is the
natural way to say it and is **described in §12 and implemented nowhere** (§22).

> **Precedence orders rules. It does not carve out cases.** Put the case in the antecedent.

---

## 3. The connective decides whether your turn loop terminates

```
rule <tick> = implies( { +quiet(?m) }, { +turn(?m) } )   ->   3 ticks, 1 turn, ends
rule <tick> = causes(  { +quiet(?m) }, { +turn(?m) } )   -> 200 ticks, 100 turns, runs to the limit
```

`implies` deposits into the same moment; `causes` moves the seat, which mints a fresh `quiet`, which
warrants the next firing. The criterion is §14's:

> **An occasion warrants a re-ask only if re-asking cannot produce one.**

It is stated, it has been violated in three separate places, and it is **not enforced**. Neither
reading of the connective is about looping, so nothing on the page warns you. If a rule keys on an
occasion the machinery deposits — `quiet`, `left`, `stopped` — reach for `implies` first.

---

## 4. What works, and is worth building on

### ⭐ Define the verb once; declare the world in facts

This is the pattern to build an RPG on, and it is the reason the engine grew a feature this week. A
class can be named by a variable — `+?kind(?item)` — so *the smith sells weapons* is a **fact**, and
applying that class to a particular sword is the rule's job:

```
rule <can-buy> = implies(
    { +wants(?b, ?item), +sells(?s, ?kind), +?kind(?item),
      +stocks(?s, ?item), +purse(?b, ?coin) },
    { +offer(?b, ?s, ?item) } )

rule <buy> = causes(
    { +offer(?b, ?s, ?item), +purse(?b, ?coin) },
    { +owns(?b, ?item), -stocks(?s, ?item), ? purse(?b, ?coin), +falls(purse(?b)) } )
```

...and then the world is **declared**, not coded:

```
fact sells(smith, weapon)      fact +weapon(sword)
fact +stocks(smith, sword)     fact +purse(hero, 20)      fact +wants(hero, sword)
```

Three things measured about that, and the last two are what make it pay:

| | |
|---|---|
| the trade goes through | `owns(hero, sword)` `+`, `stocks(smith, sword)` `−` |
| **a whole new trade is facts** | armourer / armour / shield: **5 facts, 0 new rules** |
| **a second verb reuses the declarations** | `<steal>` keys on the same `sells` and `?kind`, untouched |
| **a class hierarchy is one ordinary rule** | `{+blade(?x)} ⟹ {+weapon(?x)}` and the smith sells daggers, though nothing ever said so |

> **`sells(smith, weapon)` names a class, and `?kind(?item)` is what applies it.** Without a variable
> in the relation slot, `sells` could only ever name a particular item and every merchant would need
> its own rule.

⚠ **The cost, so you place it deliberately.** A variable relation in a **consequent** is free at match
time and cheaper overall, because one rule replaces N. In an **antecedent member** it loses §3's index
— the pattern has no bucket, so it scans — measured at **14× the unifications** on a small world with
200 unrelated facts. Above, `?kind(?item)` sits in an antecedent and is affordable because `sells` and
`stocks` narrow it first. Do not lead with the unindexed member.

⚠ **Arity slips are silent here.** The first version of that `<buy>` rule wrote `? purse(?b)` against
a `purse(hero, 20)` fact — a different proposition — so it invalidated something nobody had asserted
and the old amount went on reading `+`. Nothing complains.

### One rule per ability

If you are not using the class trick, an ability catalogue is a rule per ability, and it is a rule
rather than a fact for a reason worth understanding before you commit a design to it:

```
rule <fireball> = implies( { +did(fireball(?t)) }, { +burned(?t) } )      -- parameterised ✅
```

⚠ **The `achieves` idiom is ground-only, and this is the correction to make before you lean on it.**
The catalogue-as-data shape does work:

```
rule <resolve> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )
fact achieves(fireball_goblin, burned(goblin))        -- one fact per (spell, TARGET) pair
```

but it does not parameterise. `fact achieves(fireball(?t), burned(?t))` is refused outright — a fact
may not contain a variable. Written as a **named** fact, where variables are allowed, it parses and
then **never fires**: `?a` binds to the stored pattern `fireball(?t)`, and matching that against a
ground `did(fireball(goblin))` is `match`, which is floor and which no rule may call (§5).

| | `burned(goblin)` |
|---|---|
| `fact achieves(fireball(?t), burned(?t))` | refused at load |
| the same as a **named** fact | parses, `None` — never fires |
| `fact achieves(fireball_goblin, burned(goblin))` | `+` — but one fact per pair |
| `rule <fireball> = implies( { +did(fireball(?t)) }, { +burned(?t) } )` | `+` ✅ |

> **Ability catalogues are rules, not data.** A fact can carry a whole ground proposition as an
> argument; it cannot carry a pattern that anything will apply.

This is the same fact as the shape census, seen from the authoring side: 12.6% of rules in this
repository are ground, **0%** of the external corpora are, and the ground family *is* this idiom. Real
corpora parameterise, so real corpora are rules.

**Damage takes both members.** The wrapper says which way; the `?` stops the chain answering the old
value:

```
rule <hit> = causes( { +strike(?a, ?t) }, { ? hp(?t), +falls(hp(?t)) } )
```

Measured: **without** the `?`, `hp(goblin, 10)` still reads `10` after the hit, because silence means
*unchanged*. With it, the read reports ignorance.

### ⭐ Damage numbers: a known amount is a tool, an unknown one is a node

An earlier draft of this note said *falls by 3* was unsayable. It is not — that was another item taken
from the open-questions list without being probed. Both halves work today.

**A known amount is arithmetic, and arithmetic is a function, so it is a tool.** Nothing in the engine
knows about numbers; you register one answerer and write two ordinary rules:

```
kb.answerer("calc", "minus", fn)          -- fn returns purse(who, n - c)

rule <spend>    = implies( { +purse(?b, ?n), +buying(?b, ?i), +cost(?i, ?c) },
                           { +minus(?b, ?n, ?c) } )
rule <apply-it> = implies( { +answered(<calc>, minus(?b, ?n, ?c), ?r) },
                           { +?r, ? purse(?b, ?n), -buying(?b, sword) } )
```

Measured: the purse goes 20 → 17, and the old value reads `?`.

⚠ **That last member is load-bearing.** Without retracting the trigger the rule debits **forever** —
the first version of this fixture took the purse down in threes until the budget stopped it. Same
criterion as §3's turn loop, arriving in a corpus instead of the machinery.

**An unknown amount does not want a number — it wants a node.** Don't name the value; name the
**quantity**, and say what is known of it:

```
rule <pour> = causes( { +level(?g, ?v), +poured(?g) },
                      { ? level(?g, ?v), +greater(after(?g), ?v), +rises(level(?g)) } )
```

...and it is genuinely reasoned with, not just recorded — a downstream rule reads it:

```
rule <spill> = implies( { +greater(after(?g), ?v), +brim(?g, ?v) }, { +overflows(?g) } )
   -> overflows(glass) = +
```

This is §13's move for plurality — *mint one node for the group, and its size is a fact about that
node* — applied to a scalar. ⚠ The direct form is still refused, at **load**, with a message: a
consequent naming `level(?g, ?w)` where nothing binds `?w` is an existential, not a slot.

⚠ **The real limit is repetition.** Once the level reads `?`, a second change has nothing to compare
against, so the quantity has to be **chained** — `after1`, `after2`, `above(after2(?g), after1(?g))`
— each step its own node. That works, and it is *ordinal* tracking: the agent can come to know the
level is above the brim and can never again know that it is 5. For an RPG, prefer the **tool** wherever
the number is known, and keep the node idiom for things that are genuinely vague.

**Norms work and are cheap.** Checked at the write, never proposed, never arbitrated, and the refusal
lands on the record:

```
fact <ally-safe> = forbidden(doing(harm(?x)))
   -> refused(doing(harm(ally1)), +, forbidden(doing(harm(?x))))
```

**A universal must be a rule.** `fact +hostile(?x)` is refused — a fact may not contain a variable.
(A **named** fact may: `fact <n> = forbidden(doing(harm(?x)))`. But a named fact carrying an
implication parses and then **never fires**, because applying its stored pattern is `match`, and match
is floor. Do not try to put your rulebook in a fact.)

---

## 5. Why the unsayable things are unsayable

"Unsayable" covers four quite different situations, and confusing them will waste your time in both
directions — arguing with a wall that is really a to-do, or designing around a to-do as if it were a
wall. Probed at `bdb6687`:

| you cannot say | why, exactly | kind |
|---|---|---|
| *the goblin acts after the hero* | matching resolves the state at **one locus** and a member carries no locus of its own. Nothing forbids it | **unbuilt** |
| *while poisoned* — a span as a locus | an entry's locus is typed as a moment; no span is ever built as one | **unbuilt** |
| shapes (§13) | needs both of the above | **unbuilt** |
| `unless(<R>, +cond)` | specified in §12, implemented nowhere | **unbuilt** |
| ~~*apply the effect named by this spell* — `?p(?x)`~~ | ✅ **built, after this note first said it was a wall.** The substrate could always construct one; three separate things refused it and none was an argument — the parser would not read it, `unify` compared the relation slot by identity, `substitute` would not rebuild one | **was never a wall** |
| *my rulebook, as facts* | §8 scopes a statement's variables to it — measured, `?x` in two named facts are **different nodes**, so a rule assembled from them concludes about something nothing binds | **deliberate, and load-bearing** |
| ~~*it falls by 3*~~ | ✅ **also not a wall.** A known amount is a **tool** (arithmetic is a function); an unknown one is a **node**, per §13's move for plurality. What stays open is only *recovering a readable value after an unquantified change*, which is arguably honest ignorance | **was two questions, both answered** |
| `−` matching *nothing was said* | open-world semantics: silence inherits, it does not deny | **deliberate, and correct** |

**Four of the eight are simply not built.** That is the headline, and it is better news than the list
looks: they are absent because of implementation order, not because anything in the design resists
them. `rules.py` says so in its own first paragraph — *slice one carries the one-locus case only*.

Two are deliberate and would be wrong to change. One is a genuine gap the design records and has not
solved.

⭐ **And the eighth was not a wall at all — it was three refusals nobody had asked the reason for.**
The first draft of this note listed `?p(?x)` as unsayable. Probing it found the substrate builds one
happily, and that the parser, `unify` and `substitute` each declined it independently, none of them
on an argument. It took about an hour to allow, and it is now the pattern §4 recommends you build on.

> **Ask which of the four you are hitting before you design around it.** If it is *unbuilt*, say so
> loudly and it may get built. This note went from "here is a wall" to "here is the recommended
> pattern" in one afternoon, purely because someone asked **why** rather than accepting the list.

## 6. Walls — things the document describes that the engine does not have

Recorded in §22 and Appendix C as of this session. You will reach for all of these in an RPG.

| you want to write | status |
|---|---|
| *the goblin acts after the hero* — `where ?n = succ(?m)` | **no skeleton in the surface**, and the engine carries the one-locus case only |
| *while poisoned*, *throughout the battle* — a span as a locus | **an entry's locus is a moment**; no span is ever built as one |
| §13's shapes — *taking turns*, recursive definitions over spans | follows from the two above: **cannot be written at all** |
| `unless(<R>, +condition)` | described in §12, implemented nowhere |

**No rule can relate two moments.** That is the single largest constraint on an RPG corpus, and it is
not a bug you can route around with cleverness — it is one missing member kind. A narrower substitute
is proposed in §22 (succession as an **answerer**, so `pred` becomes askable without the whole
skeleton); it is unbuilt, and your demo is the best argument for or against building it.

---

## 7. Smaller traps, each measured

* **Two rules that say the same thing are two rules.** Restating is not revising; deny the one you
  meant.
* **Authored order decides most arbitrations.** Measured previously, not re-run here: on one episode,
  19 of 30 arbitrations were settled by the order rules were typed in. If you care which of two
  applicable rules goes first, say so with `prefer` or a precedence — do not rely on file order, and do
  not be surprised by it either.
* **A corpus tool may not share a request relation with the apparatus.** `_answer` calls *every*
  answerer bound to a relation, so a tool registered on `compose`, `fit`, `check`, `verdict`, `root`,
  `support`, `recall` or `again` would silently share a request the agent acts on. Refused at
  registration as of this session — you will get a clear error, not a mystery.
* **Arbitration is scheduling, not decision.** A rule that loses is *deferred*, not rejected, and a run
  to quiescence applies it eventually. If your agent has two ways to do something it will do both,
  unless one is forgone or forbidden. For an RPG this is a safety property before it is a quality one.
* **`standing` is what stops a rule being starved.** A conflict starves the rule that would settle it —
  two rules oscillating never let a third referee take a turn. If you write a referee, mark it
  `standing`.

---

## 8. What we would like back

Two things, and the second is worth more.

**Run `python -m ugm.shapes`** against your corpus once it is substantial. It censuses rule shapes and
the generic/ground split. Ours has 514 authored rules across every fixture; the only external corpora
we have are 14 rules from two sibling repos. Yours would be the first from a domain nobody here was
designing for, and the census's own caveat is that fixtures skew small and simple.

**Keep a running list of what you wanted to say and could not.** This is the more valuable artifact,
and the reason is structural: every gate this repo has measures conventions that **exist**. The bundle
gate deletes each shipped rule and re-runs the suite; a convention with no rules has none to delete and
reads as passing. So the absence of the skeleton was invisible to every instrument for as long as it
has existed, and was found by probing the surface by hand.

> **A missing convention is silent by construction. The only instrument for it is an author noticing.**

Rough notes are fine — *wanted a rule about two turns, wrote three facts instead* is more useful than
a polished bug report, because the workaround is the evidence.
