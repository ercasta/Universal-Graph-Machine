# Notes for a corpus author

`docs/rules-design.md` is the design. This is the shorter, meaner document: **what actually bites when
you sit down and write a corpus**, ordered by how much time it costs before you find it.

Every claim below was run against the engine at commit `bdb6687`, not recalled. Where a number is
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

**One fact per ability, one generic rule.** The highest-leverage pattern available, and the only place
where knowledge can be facts rather than rules:

```
rule <resolve> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )
fact achieves(fireball, burned(goblin))
```

The bare-variable consequent `{+?y}` is legal because `?y` is bound by the antecedent. One rule
consumes an unlimited catalogue of abilities. ⚠ Note what it cannot do: the fact carries a **whole
proposition**, never a relation plus arguments — `?p(?x)` will not parse, so you cannot assemble an
effect from parts.

**Damage takes both members.** The wrapper says which way; the `?` stops the chain answering the old
value:

```
rule <hit> = causes( { +strike(?a, ?t) }, { ? hp(?t), +falls(hp(?t)) } )
```

Measured: **without** the `?`, `hp(goblin, 10)` still reads `10` after the hit, because silence means
*unchanged*. With it, the read reports ignorance. §16 has the argument; the magnitude — *by how much* —
is a recorded open question (§22), so `falls` is sayable and *falls by 3* is not.

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

## 5. Walls — things the document describes that the engine does not have

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

## 6. Smaller traps, each measured

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

## 7. What we would like back

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
