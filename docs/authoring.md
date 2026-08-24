# Notes for a corpus author

What actually bites when you sit down and write rules, ordered by how much time it costs before you
find it. See [`guide.md`](guide.md) for the syntax and [the book](https://ercasta.github.io/Universal-Graph-Machine/)
for why it's built this way.

## 0. An occasion is consumed. A fact is not.

If a rule models something **happening**, something in its antecedent must stop being true *because*
it happened, or the rule re-fires forever. `turn(hero, 1)` is a perfectly good fact and stays true for
the whole turn — that's exactly why acting on it re-fires unless acting spends a right, not just a
denial:

```
rule <swing> = implies( { +turn($x, $r), +may($x, $r), ... },
                        { -may($x, $r), +attack($x, $d, $r) } )
```

**Exception: never consume what you were told.** `arrived(...)` is the record of a boundary event
nothing retracts. Denying `says(...)` derived from it just gets restored next tick. What works at a
boundary is a gate that legitimately closes — state the denial up front and let the world's own
change supersede it, rather than trying to consume the arrival itself.

A run still working when the tick limit bites deposits `bounded(ticks)`, so a corpus can notice its
own runaway:

```
rule <panic> = implies( { +bounded(ticks) }, { +goal(diagnose(myself)) } )
```

## 1. `-` is consequent-only. A premise cannot deny.

Belief is a flat set: asserting a proposition puts it in, erasing takes it out, asserting twice is a
no-op. `-` is how a rule *changes* that set — it has nothing to match against as a premise, because
there's no separate "denied" state to check for. Writing `-p` in an antecedent is refused at load,
with a message pointing you at the two things it could have meant:

```
rule <regen> = implies( { +wounded($x), -poisoned($x) }, { +heals($x) } )
```
```
line 1: `-` is a consequent mode -- it erases. A premise cannot erase, and there is no denying
sign left to read it as. Say which you meant: `no ...` (nothing anchors it) or `+not(...)`
(its denial is believed).
```

`no p` — the one that fails **silently** if you reach for `-` out of habit — matches when `p` is not
currently in the believed set at all: neither asserted nor its `not(p)` denial believed. It's what an
"if not stunned / not dead / not already open" rule almost always wants:

```
rule <regen> = implies( { +wounded($x), no poisoned($x) }, { +heals($x) } )
```

**Write your negatives.** A state block that lists only what *is* true won't drive rules that ask
what is *not* — `no poisoned(b)` holds by default only until something asserts `+poisoned(b)`.

## 2. There's no precedence relation. The exception goes inside the rule.

There used to be an `overrides`/`supersedes` fact a corpus could write beside two competing rules;
it's gone from the engine now. The only ways left to control which of two applicable rules wins are
**authored order** (see §5) and putting the exception **inside the losing rule**, as a negated
member — which is what `unless` means here and was always the more precise tool anyway:

```
rule <regen> = implies( { +wounded($x), no poisoned($x) }, { +heals($x) } )
```

Write it inline, not beside the rule: a rule's variables are scoped to its own statement, so a fact
naming the exception separately can't reach the rule's own `$x`.

## 3. The connective decides whether a loop terminates

There's one connective (`implies`) since `causes` was retired — it's refused at load with a message.
Under the old two-connective design the criterion was: *an occasion warrants a re-ask only if
re-asking cannot produce one.* With only `implies`, that risk is narrowed but not eliminated — see §0:
what still loops is a rule whose antecedent survives its own consequent.

## 4. What works, and is worth building on

**Define the verb once; declare the world in facts.** A class named by a variable —
`+$kind($item)` — lets *the smith sells weapons* be a fact, and applying that class to a particular
sword be the rule's job:

```
rule <can-buy> = implies(
    { +wants($b, $item), +sells($s, $kind), +$kind($item),
      +stocks($s, $item), +purse($b, $coin) },
    { +offer($b, $s, $item) } )

fact +sells(smith, weapon)   fact +weapon(sword)   fact +stocks(smith, sword)
```

A whole new trade is facts, not new rules: five facts add armour, zero new rules. A second verb
(`<steal>`) reuses the same declarations untouched. A class hierarchy is one ordinary rule
(`{+blade($x)} => {+weapon($x)}`).

**Cost, so you place it deliberately.** A variable relation in a **consequent** is free — one rule
replaces N. In an **antecedent** member it loses indexing and scans; put it after members that narrow
the search first, not leading.

**Ability catalogues are rules, not data.** A fact can't carry a pattern that anything will apply — a
named fact holding `achieves(fireball($t), burned($t))` parses but never fires, because applying a
stored pattern is matching, and matching is floor, closed to a rule. Write the ability as a rule:

```
rule <fireball> = implies( { +did(fireball($t)) }, { +burned($t) } )
```

**A known amount is a tool; an unknown one is a node.** Arithmetic is a pure function, so it's a
`kb.computator` — it runs during the match, so a multi-field change (a purse transfer) lands
atomically instead of being caught half-done by a slower `kb.answerer`. An amount you genuinely don't
know yet isn't a value slot — mint a node for the quantity and say what's known of it
(`+greater(after($g), $v)`), and read it back with an ordinary rule.

**When a change takes more than one tick, erase the old value and don't assert a replacement until
you know it** — don't claim a value you don't have yet. A reader that matches `+purse($b, $n)` simply
finds nothing mid-transfer, which is the honest state; asserting a number midway is a value nobody
actually knows yet.

## 5. Smaller traps, each worth knowing

- **Two rules that say the same thing are two rules.** Restating isn't revising — deny the one you
  meant to change.
- **Authored order is the arbitration tiebreak** when nothing else settles it, since there's no
  precedence relation any more (see §2). If you care which of two applicable rules goes first, that's
  the only lever — don't be surprised by it either.
- **A reserved name in an argument position is reported at load**, not refused — `plus`/`minus` are
  the sign atoms, so `calc(minus, 5, 2)` silently means something else than an author might expect.
  Numerals are excluded from the report, since sharing the numeral the machinery uses is correct.
- **A corpus tool may not share a request relation with the apparatus** — refused at registration,
  with a clear error, not a silent collision.
- **Arbitration is scheduling, not decision.** A rule that loses is *deferred*, not rejected — a run
  to quiescence applies it eventually unless something forgoes or forbids it.
- **`standing(<r>)` is what stops a rule being starved.** Two rules oscillating never let a third
  referee take a turn unless the referee is marked `standing`.

## 6. Testing a corpus before it disappoints you

```bash
python -m ugm <corpus.ugm>          # runs it, and warns about names nothing writes
python -m ugm.selftest              # the one test runner
```

There's no static rule-reachability checker (`ugm.atlas`/`ugm.shapes`) shipped in this repo at
present — see [`feature-requests.md`](feature-requests.md) for that idea's history. Until then, the
cheapest check is running the corpus and reading what it printed as unwebbed (a name nothing writes,
reported at load) — most silent-inert rules trace back to §1 above.
