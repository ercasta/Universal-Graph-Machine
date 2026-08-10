# Handoff — 2026-08-10

Branch `restart`, at `77cf130 denial`, pushed and clean. `main` still holds the old 46-module engine
on purpose.

`docs/rules-design.md` is still the design and still the only doc that argues anything. **This file
is a map, not a source** — where it disagrees with the design doc, the design doc wins.

---

## Verify in one go

```
python -m ugm.selftest     161 checks, 0 failing        the runner; any False is a failure
python -m ugm.agreement     28 reads, 12/12 exercised   the rule-level read against the native one
python -m ugm.bundle         8/8 bundled rules exercised  is every shipped rule load-bearing?
python -m ugm.backward       0 missing, 0 blind         backward reading as rules vs as a phase
python -m ugm.modality       (table)                    grade vs lifted vs supposed
```

`ugm.bundle` takes a minute — it re-runs the whole suite once per bundled rule.

---

## What happened, in order

The session began by reviewing `rules-design.md` and ended with four of five interpreter phases
gone. Ten commits:

| commit | what |
|---|---|
| `spine` | the doc rewritten around a **floor / bundle** split (1902 → ~2400 lines, now 2999) |
| `stratum0` | the read written as rules; `ugm.agreement` |
| `intake` | `says` becomes a bundled rule |
| `acting` | dispatch moves to the write; `did` and `assert-act` become rules |
| `surprise` | deviation becomes four rules; `ugm.bundle` |
| `supposing` | supposition stops owning the loop |
| `own seat` | reports stop landing inside hypotheses |
| `mention` | mention propagates through bindings; rules can reason about rules |
| `fit` | match as a request; `ugm.backward` |
| `delivery` | the boundary calls in; the tick loses its first line |
| `check` | the second request; backward reading entire, in five rules |
| `handoff` | this file |
| `denial` | §9 settled by measurement: sign **and** `not`, translating one way |

### 1. The spine changed

The user's challenge: **prove `moment`, `entry` and `sign` cannot be open class.** They cannot. They
are the agent's *internal representation of reality* — teachable, replaceable, and the thing an agent
reasons better by having. So the doc is now four parts: **the floor · the internal representation of
reality · what it allows · gates**, and nearly everything is convention.

The floor is five items on **three grounds**, which matters because flattening them makes all of it
look inevitable:

* **irreducible** — variables+substitution, one total step, the register
* **by guarantee** — the stamp (reducible, but reducible provenance is forgeable)
* **by economy** — ordering (fully reducible; its reduction turns linear matching into subgraph
  isomorphism)

`recall` was never a primitive. Descent to the floor is **grammaticalization** and must be *measured*,
not decided in a sitting.

### 2. The bootstrap is solved

Only one of four steps of applying a rule is circular. **Stratum 0** = rules whose antecedent members
are all structural; they are applied without a read, and the criterion is decided by scanning an
antecedent. Three regresses (reading, selecting, proposing) all escape into **a function, not a
search**.

Consequence worth keeping: stratum-0 rules are ordinary data, so **the read is replaceable at run
time**.

### 3. Four phases left the loop, and each one taught something different

| | |
|---|---|
| **intake** | a phase can hide a **precedence claim** — "runs before any rule" became an authored order a corpus can override |
| **acting** | it was in the wrong place *and the doc already said so* (§16 puts dispatch at the write). `<assert-act>` made §18 concrete: delete it and the agent still acts, still knows it acted, but no longer assumes success |
| **surprise** | a branch hides **how many claims it was making** — one comparison became four rules, three of which nothing could kill |
| **supposing** | the hard part was not the register (3 lines) but a **nested `run()`**. Entering is a write, leaving is quiescence |
| **delivery** | **being machinery never made it a phase.** An arrival is an external event; the boundary calls in |

> **A convention hidden in vocabulary is easy to see and cheap to move; a convention hidden in
> control flow is invisible and expensive.** The census counts names, and names were the easy half.

### 4. §5's wall came down in two halves

**Quiescence is a third place the machinery declines, and it declines silently** — §2 named only
match and write. A rule reasoning about rules was dropped as *nothing left to do*.

**Use/mention by authorship was too strong**; the replacement is *mention propagates through
bindings*, checkable because consumed entries are already recorded for the trail.

**`match` from a rule is a request, not a sixth primitive — and it cannot answer with a binding**,
because a rule cannot apply one. *Match and substitute travel together.*

---

## The state of the code

14 modules, ~4.4k lines. `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine;
`selftest` `agreement` `bundle` `backward` `modality` are instruments; `stratum0` is the rule-level
read.

**One phase remains**: `Machine._expand_goal`. Everything else in `tick()` is recall → match →
defeat → quiescence → arbitrate → apply, plus a `_leave()` when a supposition runs out of work.

**Eight bundled rules** ship as data (`Machine._install_bundle`): `intake`, `did`, `assert-act`, and
four `deviation-*`, and `denial`.

**Four write-time hooks**: `_dispatch` (acting), `_enter` (supposition), `_fit`, `_settle`. These are
Python callables, which is honest debt — §21 records it.

---

## Where I would pick up

**1. Decide about the last phase.** `ugm.backward` shows five rules reproduce it *and produce more*,
because the phase starves forward reasoning. So retiring it is a **behavioural change to argue for**,
not a refactor. Two things block a clean swap:

* `blocked` is a **state, not a fact** — no rule can conclude *no rule fits*, which is an aggregate
  over a finished search. It needs a home.
* nothing says when a plan is *settled*, which is also §21's backtracking item.

**2. Pattern against pattern.** `fit` matches generic against ground. Lifting a modality and
**composing two rules** both need pattern-against-pattern, and whether that is the same operation is
unknown. Composition is the larger prize — §4 argues it is algorithmic where compilation is a
constant factor.

**Smaller, well-specified:** a seat move is not yet an entry (§17 says every seat move is a write);
write-time hooks are not rules; what a `?` conclusion becomes on the way out of a supposition (§9);
whether a channel reporting a denial should write `says(c, p, -)` or `says(c, not(p))`, and whether
permitting both splits a corpus into dialects; the transpiler sketch in §21.

---

## Two habits worth keeping

**Every gate must delete each rule of the thing it checks, one at a time, and report any rule the
fixture cannot kill.** `ugm.agreement` reported success three times while unable to fail — a revision
written at the wrong locus, a read silently picking the first candidate, a transitive rule needing a
*non-competing* entry in between. `ugm.agreement`, `ugm.bundle` and `ugm.backward` all do this to
themselves now, and it has caught something every single time.

**Commits**: sole author, short lowercase topic word, and **never** a `Co-Authored-By:` or
`Claude-Session:` trailer. Audit with `git log --all --format='%B' | grep -ci claude` — it must
return 0. It does.
