# Notes for a corpus author

`docs/rules-design.md` is the design. This is the shorter, meaner document: **what actually bites when
you sit down and write a corpus**, ordered by how much time it costs before you find it.

Every claim below was run against the engine at commit `f250528`, not recalled. Where a number is
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

Neither relation expresses *this creature is the exception*. ⭐ **A negated member does**, and it is
row four of that table — it is what `unless` means, and it has always been in the surface:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )
```

⚠ Write it **inside the rule**, not beside it. `fact unless(<regen>, poisoned(?x))` parses and does
nothing at all: §8 scopes a rule's variables to its own statement, so that `?x` is a *different
variable* from the rule's, and nothing reads the relation anyway. The guard has to be where the
rule's variables are.

⭐ And it stays **askable**, which is the only thing writing it separately would have bought: `reify`
deposits every member with its sign, so *what would cancel this rule* is a query over
`ant(<regen>, poisoned(?x), -, 1)`.

> **Precedence orders rules. It does not carve out cases.** Put the case in the antecedent — that
> *is* `unless`.

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

⭐ **Better: a computator, which keeps the whole change in one application.** A tool answers through
the write, so its answer lands a tick later and a transfer can be caught half-done. A **computator** is
a function given values and returning a value — it never sees the graph — so it runs *during the
match*:

```
kb.computator("minus", lambda a, b: int(a) - int(b))

rule <pay> = causes(
    { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y),
      minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },
    { ? purse(?a, ?x), +purse(?a, ?x2), ? purse(?b, ?y), +purse(?b, ?y2), -pays(?a, ?b, ?n) } )
```

Measured: a standing observer sees `total(10, 5)` then `total(7, 8)` and **never the 12 in between**.
Use a computator wherever the arithmetic is pure; keep a tool for anything that talks to the world.

⭐ **And when a change genuinely takes more than one tick, do not assert a value you do not yet have.**
If your transfer waits on a die roll, a player, or anything outside, then part-way through you *do not
know* what the purses hold — so say `?` and assert the numbers only on settlement:

```
rule <start>    = causes( { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y) },
                          { ? purse(?a, ?x), ? purse(?b, ?y), +pending(...) } )
rule <complete> = causes( { +pending(...), +confirmed(?a, ?b),
                            minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },
                          { +purse(?a, ?x2), +purse(?b, ?y2), -pending(...) } )
```

Measured: mid-transfer the purses read `?`, an observer **cannot form a total at all**, and on
confirmation it is `total(7, 8)`, conserved. No marker fact anyone has to remember to consult — a
reader cannot get the value without the sign, because the sign is a member of the entry (§9).

⚠ The tempting alternative — a `+transferring(...)` flag that observers check — is worse, and for the
reason §16 rejected grades: **it is a separate read, so it can be obtained without the facts it
qualifies.** An observer that does not think to ask sees a settled state. Prefer `?`.

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
wall. Probed at `f250528`:

| you cannot say | why, exactly | kind |
|---|---|---|
| *the goblin acts after the hero* | matching resolves the state at **one locus** and a member carries no locus of its own. Nothing forbids it | **unbuilt** |
| *while poisoned* — a span as a locus | an entry's locus is typed as a moment; no span is ever built as one | **unbuilt** |
| shapes (§13) | needs both of the above | **unbuilt** |
| ~~`unless(<R>, +cond)`~~ | ✅ **built, and this note was wrong twice about it.** *if not* is a negated antecedent member (§2 above). What is absent is **amendment at a distance** — adding a guard to a rule you did not write — which is a different thing wearing this one's name | **was a name, not a gap** |
| ~~*apply the effect named by this spell* — `?p(?x)`~~ | ✅ **built, after this note first said it was a wall.** The substrate could always construct one; three separate things refused it and none was an argument — the parser would not read it, `unify` compared the relation slot by identity, `substitute` would not rebuild one | **was never a wall** |
| *my rulebook, as facts* | §8 scopes a statement's variables to it — measured, `?x` in two named facts are **different nodes**, so a rule assembled from them concludes about something nothing binds | **deliberate, and load-bearing** |
| ~~*it falls by 3*~~ | ✅ **also not a wall.** A known amount is a **tool** (arithmetic is a function); an unknown one is a **node**, per §13's move for plurality. What stays open is only *recovering a readable value after an unquantified change*, which is arguably honest ignorance | **was two questions, both answered** |
| `−` matching *nothing was said* | open-world semantics: silence inherits, it does not deny | **deliberate, and correct** |

Counting the rows: **four are simply not built**, **two are deliberate** and would be wrong to change,
and **two were never walls at all.**

The four unbuilt ones are absent through implementation order, not because anything in the design
resists them — `rules.py` says so in its own first paragraph, *slice one carries the one-locus case
only*. That is better news than the list looks.

⭐ **The last two are the reason this section exists.** The first draft of this note listed both
`?p(?x)` and *falls by 3* as unsayable, straight off the design's open-questions list. Probed, neither
was a limit anybody had argued:

* `?p(?x)` was **three independent refusals** — the parser would not read it, `unify` compared the
  relation slot by identity, `substitute` would not rebuild one — and the substrate had been able to
  construct the node all along. About an hour to allow. It is now the pattern §4 recommends you build
  on.
* *falls by 3* was **two questions filed as one**. A known amount is arithmetic, arithmetic is a
  function, and a function is a tool — no representation needed. An unknown amount wants a **node**
  rather than a value slot, which is §13's move for plurality sitting one section away from the item
  that said it was missing.

Neither took a day. Both had been on the open list for a long time.

> **Ask which of these four kinds you are hitting before you design around it** — and if the answer is
> not obvious, that is itself the signal. Two of the eight rows above changed status in a single
> afternoon, purely because someone asked **why** instead of accepting the list. If you hit something
> and it smells like a wall, say so loudly rather than routing around it.

## 6. The four unbuilt ones, in detail

These are the *unbuilt* rows of §5, with what each blocks. Recorded in §22 and Appendix C as of this
session. You will reach for all of them in an RPG.

| you want to write | status |
|---|---|
| *the goblin acts after the hero* — relating two moments | ✅ **BUILT.** `at ?m` binds a locus; `sanc`/`anc` relate them |
| *the door was open and now is closed* — one fact's own history | ✅ **BUILT.** Two rules over the raw chain; see below |
| *while poisoned*, *throughout the battle* — a span as a locus | ✅ **BUILT.** `span_of` mints a stretch; a consequent's `at ?s` deposits at one |
| §13's shapes — *taking turns*, recursive definitions over spans | ✅ **BUILT.** They run; see below |
| ~~`unless(<R>, +condition)`~~ | ✅ **BUILT** — it is a negated antecedent member, written inside the rule (§2) |

⭐⭐⭐ **There are no unbuilt rows left in this table.** Relating two moments, a fact's own history,
spans as loci, the shapes that follow from them — and `unless`, which was never unbuilt at all: it is
*if not*, and *if not* has been a negated member since there were members.

⚠ **What IS absent, correctly named:** **amendment at a distance** — adding a guard to a rule you did
not write and cannot edit. That is refused by decision rather than missing by omission. An ordinary
rule may not reach into another rule's application (§5's wall), and amending a rule belongs to
harmonization: the agent authors a better rule through `adopt`, so the amendment is itself a claim
you can date, attribute and argue with.

⭐ **It has been probed and sized, and it splits in two. Tell us which half you needed.**

| | |
|---|---|
| **sequencing** — two *different* facts at different moments, *the goblin acts after the hero* | ✅ **BUILT.** Write `+acts(goblin) at ?m` and the locus binds. Your clock scaffold should collapse |
| **a fact's own history** — the *same* proposition at two moments, *the door was open and now is closed* | ✅ **BUILT.** It did not reopen the bootstrap. See below |

So turn order, initiative, *who acted before whom* — all now writable, on your evidence that it was
worth building.

✅ **And *it used to be X and now it is Y* about ONE fact is now writable too.** It was recorded as
materially harder because a matcher sees the **resolved** state — one entry per proposition — so the
superseded entry is not there, and reaching it means matching the **raw chain**, which looked like it
reopened the bootstrap. It does not, and the reason is worth knowing because it shapes how you write
it: **a rule whose antecedent is entirely structural concludes structure rather than a claim.** So the
chain-reading rule cannot assert anything, and that is exactly why it is allowed to read the chain.

It takes **two rules** — one to see it, one to say it:

```
rule <flip> = implies(
  { asking(?s), anc(?s, ?d1), in_delta(?d1, ?e1), entry_of(?e1, ?l1, ?p, plus),
    anc(?s, ?d2), in_delta(?d2, ?e2), entry_of(?e2, ?l2, ?p, minus),
    sanc(?l2, ?l1) },
  { flipped(?p) } )

rule <note> = implies( { flipped(?p), +watching(x) }, { +changed(?p) } )
```

`<flip>` mentions only skeleton, so it concludes into the skeleton: `flipped(open(door))` is a plain
node, undated, unattributed, and **not deniable**. `<note>` mentions an entry (`+watching(x)`), so it
is an ordinary rule and concludes an ordinary claim. That is the whole bridge.

**The skeleton members you now have:**

| | |
|---|---|
| `asking(?s)` | the seat the agent is standing at — **what anchors everything else** |
| `anc(?s, ?a)` / `sanc(?s, ?a)` | ancestry, reflexive and strict |
| `pred(?s, ?p)` | the immediate predecessor. ⚠ This used to silently mean `anc` |
| `in_delta(?m, ?e)` | the entries deposited at a moment |
| `entry_of(?e, ?locus, ?prop, ?sign)` | an entry's three members |
| `delta_next(?e, ?f)` | deposit order within one moment |
| `rests_on(?e, ?c)` | what an entry was derived from — **the agent's own trail** |
| `span_of(?s, ?start, ?end)` | a **stretch** of the chain. Endpoints bound ⟹ it mints one; the span bound ⟹ it decomposes |

⚠⚠⚠ **Every one of them must be anchored, and the authored order is what anchors it.** Start from
`asking(?s)` and walk outward; a member whose turn comes before anything binds it finds **nothing**,
silently. That is the single trap in this whole area, and it is why `<flip>` above reads in the order
it does.

⚠ A `-` on a skeleton member means **not derived** — negation as failure — not *an entry denies it*.
There are no entries here for a sign to be about.

✅ **And ordering landed too — as an ordinary member, not a request:**

```
rule <after> = implies( { +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp) },
                       { +acted_after(?q, ?p) } )
```

`sanc(?later, ?earlier)` holds when the second moment is a strict ancestor of the first. It is
**ancestry, not a depth comparison**, so it stays correct once anything forks.

⚠ **The first argument must already be bound.** A structural member walks from an anchored moment
*toward the root*, and that direction is single-valued — which is exactly why it can never reach into
a sibling hypothesis. Written the other way round (`sanc(?anything, ?m)`) it loads fine and finds
nothing; nothing is refused, there is simply nowhere to go. Between `at` and this, your initiative and
round-order scaffold should go.

⭐ **And a member can name what it matched:** `+on(?x, ?y) as ?t`, then use `?t`. It binds the *same
node*, so it is reference rather than a copy. ⚠ Two members hoping to co-refer — `+tagged(?t),
+on(?x, ?y)` — do **not** link, and look like they work while there is only one candidate.

⚠ Please distinguish the two when you write your list. They look identical when you hit them and they
cost completely different amounts.

### ✅ *Throughout the battle* — a claim whose subject is a STRETCH

Some claims are not about a moment at all. *They took turns*, *it rained throughout*, *he was poisoned
for three rounds* — none is true of any instant. Those take a **span** as their locus:

```
rule <r> = implies( { +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp),
                      span_of(?s, ?mp, ?mq) },
                   { +took_turns(?p, ?q) at ?s } )
```

`span_of(?s, ?start, ?end)` **mints** the stretch when both endpoints are bound — that is what a
recogniser does — and **decomposes** one when the span is bound instead. `at ?s` on the consequent is
what puts the claim there. No new notation: `at` is the member locus you already have, on the other
side of the rule.

**Three things to know before you write one.**

⚠ **Only the endpoints are stored.** What lies between them is the chain's to settle, and asking a
span *what is inside you* is not a question — the answer would be a second story that could disagree
with the chain. Participants stay in the proposition (`took_turns(anna, bo)`), never in the span, so
one stretch can host several unrelated recognitions.

⚠⚠⚠ **A claim about an instant does NOT become a claim about the stretch.** *It rained at M9* will
not answer *did it rain throughout M7..M12* — deliberately, because the read returns one winner rather
than scanning an interval, so a denial in the middle would be invisible and you would get a confident
wrong answer. If your corpus wants *it held at the start, so it held throughout*, **write that rule**;
then it is yours, and it is dated and deniable like everything else. The same goes for one span
answering about a shorter one inside it: `during(?s2, ?s1)` is an ordinary fact about endpoints.

✅ **What does hold: a recognition is an ordinary fact once the stretch is over.** From the end moment
onward any ordinary rule reads `+took_turns(anna, bo)` without knowing a span was involved. That is
what makes a shape worth recognising.

⚠ An **inverted** span (`span_of(?s, ?later, ?earlier)`) and a **degenerate** one (start = end) are
both refused. The second is deliberate: a one-moment span would be a second name for a moment, and two
ways to say one locus is exactly the ambiguity the read cannot afford.

### ✅ §13's shapes — a pattern of indefinite extent

*Taking turns* is a **recursive definition over spans**: a base case of two turns, and a step that
consumes one turn and defers the rest. It needs the **raw chain** rather than the resolved state, and
for the reason above — an alternation repeats its actors, so `acts(anna)` at M1 is superseded by
`acts(anna)` at M3, and the step needs precisely that earlier turn.

So it is the `<flip>`/`<note>` split again, one construct larger: **two structural rules to see it,
one ordinary rule to say it.**

```
rule <tt-base> = implies(
  { asking(?q), anc(?q, ?p),
    in_delta(?p, ?ep), entry_of(?ep, ?p, acts(?b), plus),
    pred(?p, ?n),
    in_delta(?n, ?en), entry_of(?en, ?n, acts(?a), plus),
    pred(?n, ?m), span_of(?s, ?m, ?p) },
  { turns(?s, ?a, ?b) } )

rule <tt-step> = implies(
  { turns(?s2, ?b, ?a), span_of(?s2, ?n, ?e),
    in_delta(?n, ?en), entry_of(?en, ?n, acts(?a), plus),
    pred(?n, ?m), span_of(?s, ?m, ?e) },
  { turns(?s, ?a, ?b) } )

rule <say> = implies( { turns(?s, ?a, ?b), +watching(x) },
                     { +taking_turns(?a, ?b) at ?s } )
```

Over five alternating moments that recognises the pattern over **every stretch it holds over** — ten
of them. ⭐ The **argument swap** (`?a, ?b` in the head, `?b, ?a` in the recursive member) is the whole
of it: remove it and the definition says *someone acts repeatedly*.

⚠ You must call for the structural layer to settle (`ask_read`, then the stratum-0 fixpoint) before
the ordinary loop can see `turns`. Nothing in the tick loop does that for you yet.

---

## 6b. ✅ How to test a corpus before it disappoints you

Two commands, and between them they catch the failures that are otherwise silent.

```
python -m ugm <corpus.ugm>          # runs it, and warns about names nothing writes
python -m ugm.atlas <corpus.ugm>    # maps what can be inferred from what
python -m ugm.atlas <corpus.ugm> --mermaid    # ...as a diagram
```

⭐⭐⭐ **The one that will save you the most: a rule that can never apply.** §1
above is this document's most expensive trap because it fails *silently* — you
write `-poisoned(?x)`, nothing ever denies poison, and the rule is simply inert.
`ugm.atlas` says so without you running anything:

```
rule <keep> = implies( { +held(?x), -gone(?x) }, { +kept(?x) } )
fact +held(thing)

  rules that can NEVER apply   : ['keep']
  FOUND  <keep> can never apply (needs ['gone'])
```

⭐ **And it is transitive**, which is the part you cannot check by eye. A name
nothing writes is easy to spot; a rule whose premise is written *only by a rule
that itself can never apply* is not, and that is the shape a corpus acquires as
it grows, because every link looks fine on its own:

```
rule <a> = implies( { +p(?x) }, { +q(?x) } )   # nothing asserts p
rule <b> = implies( { +q(?x) }, { +r(?x) } )   # so <b> is dead too

  rules that can NEVER apply   : ['a', 'b']
```

⚠ **What it will not tell you.** It ignores arguments: `owns(smith, sword)`
grounds `owns` for any rule reading `owns(?a, ?b)`. So a rule it calls live may
still never fire — but a rule it calls **dead genuinely cannot**. The false
direction is the safe one, and silence is not a guarantee.

⚠ A corpus that registers **tools** cannot be mapped from the command line, since
its answerers are installed by its host. Call `atlas.survey(machine, rules)` from
wherever you build the machine.

### The last line is a question, not a defect

`pairs that could disagree` lists rules that could conclude opposite signs of one
thing with nothing on the record saying who wins. **Read it as a prompt.**
Measured: **1** on the passenger-rights corpus — and it is a real question, since
a flight both storm-delayed and short of crew has two answers — against **28** on
the dungeon, where almost all of them are the ordinary grant-and-spend cycle of a
world model. If your rules retract in their own consequents, expect a long list
that is mostly your corpus working correctly.

---

## 7. Smaller traps, each measured

* **Two rules that say the same thing are two rules.** Restating is not revising; deny the one you
  meant.
* **Authored order decides most arbitrations.** Measured previously, not re-run here: on one episode,
  19 of 30 arbitrations were settled by the order rules were typed in. If you care which of two
  applicable rules goes first, say so with `prefer` or a precedence — do not rely on file order, and do
  not be surprised by it either.
* ⭐ **A reserved name in an argument position is now reported at load.** `reserved` binds `plus` and
  `minus` to the **sign atoms**, so a corpus writing an arithmetic operator got the sign —
  `calc(minus, 5, 2)` landed as `calc(-, 5, 2)` and the tool declined a request it should have
  answered. It is a *report*, not a refusal: `+expects(?p, plus)` is legitimate and the loader cannot
  tell an operator from a sign. Numerals are excluded, because `cost(sword, 3)` sharing the numeral
  the machinery uses is correct.
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
