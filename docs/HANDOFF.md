# Handoff — 2026-08-11

Branch `restart`. `main` still holds the old 46-module engine on purpose.

`docs/rules-design.md` is still the design and still the only doc that argues anything. **This file
is a map, not a source** — where it disagrees with the design doc, the design doc wins.

---

## Verify in one go

```
python -m ugm.selftest     175 checks, 0 failing        the runner; any False is a failure
python -m ugm.agreement     28 reads, 12/12 exercised   the rule-level read against the native one
python -m ugm.bundle         9/9 bundled rules exercised  is every shipped rule load-bearing?
python -m ugm.backward       0 missing, 0 blind         backward reading as rules vs as a phase
python -m ugm.compose        0 failing, n steps -> 1    composition, measured
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
| `compose` | pattern-against-pattern is **unification, not match**; composition built and measured |
| `occasions` | leaving a hypothesis and running out of work become **facts**; callbacks and watchdogs |

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

### 5. Two occasions, one mechanism — and the wall was protecting something

Two questions turned out to be one. *What runs on the way back out of a hypothesis?* and *what stops
reasoning dying quietly with a goal still open?* Both want something to happen at a moment the
machinery owns and no rule can name — so both get §17's treatment for arrivals and emissions:
deposit the smallest unarguable record, let rules say what it means.

    left(<frame>, <assumption>)      written by `_leave`, after discharge
    quiet(<m>)                       written by `_wake`, once per seat

**`quiet` closes §5's third silence.** Match and write were the two named places the machinery
declines; quiescence was a third that said nothing at all. It is also the moment an *aggregate over a
finished search* becomes legitimate — which is where §21's homeless `blocked` belongs. A watchdog
needs nothing more: it is an ordinary rule with `+quiet(?m)` in its antecedent, inert until the loop
stops because nothing else writes that. **The trigger is the fact** — no trigger table, no registry.

**A callback is a pointer to a rule, and it may not be a call.** `+resume(h, <R>)` hangs a rule on a
hypothesis; `<resuming>` picks it up and can only say *this rule's turn has come* (`+due(<R>)`),
because §5 forbids a rule applying a rule. A `dormant` rule is not proposed by ordinary recall; a
`due` one is. So a callback is **directed recall, not invocation** — and that is stronger than a call:
the woken rule still has to match, can still be defeated, still competes, still yields to a surprise.
Adding continuations did not weaken *nothing owns the loop*.

It also lands on §19's reserved seam: `dormant`/`due` are the first thing a corpus has ever been able
to say to `_recall`.

Three things this cost, and two of them were bugs that had been invisible:

* **substitution was minting twins.** Rebuilding a consequent goes through the interning constructor,
  so descending into a rule node returned an interned *copy* — the pointer named a rule that did not
  exist and every question about the real one answered nothing. Fixed in `substitute`/`ground`: a
  subterm nothing changed is returned unchanged.
* **mention had no source.** §14's *mention propagates through bindings* needs somewhere to start; a
  rule authored naming a rule (`<...>` in its consequent) is it. Without it a rule attaching a rule
  was dropped by quiescence as *nothing to do*.
* **the occasion persists.** `quiet` is an entry, not an event, so a watchdog is armed from quiescence
  onward, not fired once. One whose conclusion re-arms it runs to its budget. Likewise `due` is not
  consumed — a woken rule stays awake, which is fine only while recall is exhaustive.

---

## The state of the code

15 modules, ~4.7k lines. `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine;
`selftest` `agreement` `bundle` `backward` `compose` `modality` are instruments; `stratum0` is the rule-level
read.

**One phase remains**: `Machine._expand_goal`. Everything else in `tick()` is recall → match →
defeat → quiescence → arbitrate → apply, plus a `_leave()` when a supposition runs out of work and a
`_wake()` when the loop does.

**Nine bundled rules** ship as data (`Machine._install_bundle`): `intake`, `did`, `assert-act`,
`denial`, `resuming`, and four `deviation-*`.

**Four write-time hooks**: `_dispatch` (acting), `_enter` (supposition), `_fit`, `_settle`. These are
Python callables, which is honest debt — §21 records it.

---

## Where I would pick up

**1. Decide about the last phase.** `ugm.backward` shows five rules reproduce it *and produce more*,
because the phase starves forward reasoning. So retiring it is a **behavioural change to argue for**,
not a refactor. Two things block a clean swap:

* `blocked` is a **state, not a fact** — no rule can conclude *no rule fits*, which is an aggregate
  over a finished search. **`quiet` is now the home**: an aggregate over a finished search is
  legitimate exactly when the search is over, and a fact now says one is. Nothing has been moved onto
  it yet.
* nothing says when a plan is *settled*, which is also §21's backtracking item, and the same question
  as *when is a `due` rule done*.

**2. The composition trigger.** Composition is built and measured (n steps -> 1, defeat inherited).
What is missing is *when*: §4's answer is `compose what has run often and never surprised; decompose
what surprises`, and neither half is wired. `RuleSet.composed_from` already records what each shortcut
collapses, so decomposition knows where to look.

**3. Lifting a modality across a rule** — the last of the four callers of §5's wall with no service.

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
