# Handoff — 2026-08-11

Branch `restart`. `main` still holds the old 46-module engine on purpose.

`docs/rules-design.md` is still the design and still the only doc that argues anything. **This file
is a map, not a source** — where it disagrees with the design doc, the design doc wins.

---

## Verify in one go

```
python -m ugm.selftest     201 checks, 0 failing        the runner; any False is a failure
python -m ugm.agreement     28 reads, 12/12 exercised   the rule-level read against the native one
python -m ugm.bundle        14/14 bundled rules exercised  is every shipped rule load-bearing?
python -m ugm.backward       0 failing, 0 blind         backward reading, as the rules that replaced the phase
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
| `nophases` | the last phase deleted. `tick()` has no line a rule could have written |
| `recall` | §19's first slice: `prefer(<R>, k)` as facts, a budget, and widening |
| `norms` | §19's carve-out: a prohibition is a **veto at the gate**, never a competitor in recall |
| `naming` | a **fact may carry a name**; a named norm is a node rules can retire |
| `reference` | reference is **binding**; the walk is one order; the naming claim corrected |

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

### 6. The last phase went, and the count is zero

`_expand_goal` is deleted. `tick()` is now recall → match → defeat → quiescence → arbitrate → apply,
plus the two things a register owes: `_leave` when a hypothesis runs out of work, `_wake` when the
loop does. **There is no line in it a rule could have written.**

Backward reading ships as five bundled rules over three requests — `<ask-fit>`, `<plan>`, `<expand>`,
`<ask-check>`, `<give-up>`. What made the last one possible is the `verdict` request: `blocked` claims
that **no** rule fits, an aggregate over a finished search, and `quiet` is the fact that says a search
has finished. The machinery answers it by counting `fits` and `achieved` entries **the rules
produced** — it runs no search, so *which rules were considered* stays recall's business.

Two supporting changes:

* **rules are data when authored** (`RuleSet.on_rule` → `Machine.reify`). Backward reading enumerates
  `+rule(?r)`, so a rule loaded after someone called `reify_all()` was invisible to it with nothing
  reporting so. `reify_all()` is kept and idempotent.
* **R2 moved from the licence to the trail.** The phase stamped subgoals `wanted`; now `<expand>`
  writes them, so the licence is `applied(<expand>)` and the reading is recovered one hop back —
  `<expand>` consumed a `need` entry, and `_fit` licences everything it answers `wanted(<R>, goal)`.
  Checked by walking the trail rather than by trusting a stamp.

**What it cost, measured.** 98 steps where the phase took ~10 on the same corpus; `ugm.backward`'s
fixture is 194 steps / 411 writes. `ask-fit` asks every reified rule about every goal, which is
exactly what §19 exists to narrow — the phase hid that cost by hard-coding the narrowing.

**Two gaps this made visible, neither of them new:**

* **a root goal is never checked** for satisfaction. `<ask-check>` keys on `subgoal(plan, ?w)`, and
  *a goal with no plan* is not expressible. Checking every goal binding-free would reintroduce §18's
  sibling failure, so this needs a real answer, not a rule.
* **a request can only be made once.** `<ask-check>` asks when the subgoal appears; if forward
  reasoning satisfies it three ticks later, nothing asks again, because re-concluding `+check(p, w)`
  changes nothing and quiescence drops it. This is why `ugm.backward`'s historical 29th fact
  (`achieved(water(kettle))`) is no longer produced — recorded there as a claim about the phase, not
  as a current output. A re-ask needs a fresh request node; §21.

### 7. Recall stops proposing everything

§19's seam is open. `prefer(<R>, k)` is a table of **ordinary facts** — *when `k` is in play, bring
`R` to mind* — authored for now, learnable later from the trail R5 already deposits. `recall_budget`
is `None` by default, so behaviour is unchanged until a corpus claims something.

**The key is not the register.** Attention *is* the register (`Machine.focus`, a `Frame(seat, topic)`
— §4's one privileged pointer), and that is why it cannot be the key: a seat is a fresh moment every
tick, so a table keyed on it never sees the same key twice. The key is **a relation in play**
(`_in_play` = the relations in the current moment's delta — *what just changed*). That is one method
wide, deliberately; a better key replaces it without touching the loop, the table, or any rule.

**A shortlist that ran dry is not a search that finished** — and this is a *soundness* condition, not
a quality one. `<give-up>` asks its verdict at `quiet`, and `blocked` is an aggregate over a finished
search. So quiescence under a budget escalates to the exhaustive pass first (`_widen`, step state
`widened`), and only its silence writes `quiet`. Take the line away and the same corpus gives up on a
goal it can reach — checked, and the check is shown able to fail.

**Randomness was considered and not taken.** §3 forbids reading a derived result out of a set, and an
unseeded top-K draw is that bug wearing a hat: two runs diverge and the trail records neither the
choice nor the reason. The tie-break is authored order, the same one arbitration uses. If exploration
is what randomness was for, §19 already has the better answer — the exhaustive pass on novelty or a
schedule, which injects what a draw *from the shortlist* structurally cannot.

### 8. Norms come off the recall path

§19's carve-out, and it is the one place the design refuses to be incomplete:

> Recall may be incomplete about what to do. It may not be incomplete about what you must not do.

`forbidden(<pattern>)` is a norm. Its argument is a **description** — `forbidden(doing(harm(?x)))`
names a class of acts the way `ant(<R>, heat(?a, ?w))` names a class of premises. It is never
proposed, matched or arbitrated: `Gate.veto` consults it on every write, **before the deposit**, so a
forbidden entry never exists — not even briefly, and not for an `on_write` hook to see. Dispatch *is*
an `on_write` hook, so that is what keeps the act inside the agent instead of emitting it and
regretting it.

Cheap because it is indexed by what is about to be written (§3's instances-by-relation): only norms
whose pattern shares the proposition's relation are resolved.

**A refusal writes.** `refused(p, sign, <norm>)`, licensed by the norm. A veto that deposited nothing
would be a fourth silent decline, and silence about norms is the exact failure being designed against.

Three things fell out rather than being arranged: quiescence still terminates (the *refusal* is what
stops the rule re-applying — otherwise a norm is a livelock); a norm forbids `+` only, because
bringing about is asserting; and a norm is still an ordinary belief, resolved at the writer's own
position.

### 9. Naming a statement, and what it separated

Stating a norm was not enough. A norm's argument is a **description**, a description is an authored
statement, and §8 scopes a statement's variables to it — so `forbidden(doing(harm(?x)))` written twice
is *two nodes that say a similar thing*, and denying the second leaves the first forbidding, silently.
**Restating is not revising.** That is §8's own rule about rules arriving somewhere it had not been
noticed.

The repair was already in the surface. A fact may carry a name:

    fact <no-harm> = forbidden(doing(harm(?x)))
    fact -<no-harm>

`<...>` is the namespace of **statements**, and a rule is a statement — so it is one table, not two.
A rule and a norm sharing a name would be two things with one name, which is what the marker exists
to prevent.

A separate consequence, about the carve-out rather than about naming:

> **§19 keeps norms out of recall. It never said they were beyond argument.**

A rule can retire a norm on evidence — `{+says(fire, evacuate, +)} ⟹ {-<no-harm>}` — trail intact,
with the refusals it made beforehand still on the record. **Unconditionally consulted** and **entirely
contestable** are different properties.

⚠ **Naming is not what separated them.** Measured afterwards: a rule could always do this *without*
the name, by describing the norm's shape — matching a generic antecedent against a stored description
treats the description's variables as ordinary nodes, so `?y` binds to the stored `?x` and
substitution rebuilds exactly the node written. Naming buys **authoring** (a second surface statement
about one description) and a handle for facts that are not about its shape. It never bought
reference.

Forced, not chosen: a rule may conclude about a named fact and a named fact may be about a rule, so
the loader does three passes — name what is self-contained, then rules, then everything else. A name
needs only its node, and a statement referring to no other statement can be built without one.

### 10. Reference is binding, and the walk was two orders

The question was *what else wants a name — a supposition, a plan?* Answer, measured: **mostly nothing
does.** A plan, a hypothesis, a rule and a norm are all referable already, because anything deposited
as an entry can be bound by an antecedent, and **binding is reference**. Language works the same way —
it says *the plan we made before*, not a name. Names are for the exceptions.

What binding does not supply is **which one**, and that turned up a live bug. Several entries match
one description; the walk decides which is tried first, and the walk disagreed with itself:

* `Moment.ancestors()` — newest moment first
* a moment's `delta` — oldest entry first

So two candidates deposited by `implies` (same moment) came out in the *opposite* order to two
deposited by `causes` (different moments) — and which connective a rule used has nothing to do with
reference. One `reversed()` in `current_state` makes it one order throughout, and *a description
resolves to the most recent* is now a claim with a check behind it instead of an accident.

⚠ **It changed a result, and the change is the finding.** `ugm.backward`'s sibling-agreement fixture
flipped: with the taps authored one way the plan now succeeds, the other way it still blocks. Same
world. Because:

> **Reference resolves to the most recent, and nothing reconsiders.** `_settle` takes the first entry
> that satisfies a subgoal and never returns to it. Checking siblings inside the plan's bindings stops
> a wrong plan being reported as a good one; it does not *find* the right one.

`ugm.backward` now runs both orders and prints both outcomes — §21's backtracking item measured rather
than asserted. And the old fixture was, it turns out, measuring the walk order rather than the
guarantee.

**One bug fixed on the way**: `discharge` dropped `mention` when carrying a conclusion out of a frame,
so a conclusion *about a rule* drawn under a hypothesis was refused by the gate — §14's propagation
with a hole in it at the one place conclusions change hands.

---

## The state of the code

15 modules, ~4.7k lines. `chain` `graph` `gate` `rules` `channels` `machine` `text` are the engine;
`selftest` `agreement` `bundle` `backward` `compose` `modality` are instruments; `stratum0` is the rule-level
read.

**No phases remain.** `tick()` is recall → match → defeat → quiescence → arbitrate → apply, plus
`_leave()` when a supposition runs out of work and `_wake()` when the loop does.

**Fourteen bundled rules** ship as data (`Machine._install_bundle`): `intake`, `did`, `assert-act`,
`denial`, four `deviation-*`, `resuming`, and backward reading's `ask-fit`, `plan`, `expand`,
`ask-check`, `give-up`.

**Five write-time hooks**: `_dispatch` (acting), `_enter` (supposition), `_fit`, `_settle`,
`_verdict`. These are Python callables, which is honest debt — §21 records it.

**One veto**: `_forbid`, §19's carve-out. Not a hook and not a rule — it runs *before* the deposit,
which is the whole of its guarantee.

---

## Where I would pick up

**1. Recall, continued.** The seam is open, the first slice is in and the carve-out is done (§7, §8
below). What is *not*: the table is authored, never learned; `_in_play` is the cheapest key that
recurs and deserves a measured comparison against alternatives; and the exhaustive pass fires only on
a dry shortlist, never on novelty or a schedule, which §19 says is what stops recall calcifying
exactly where it is performing well.

**Definite reference — which one.** Binding refers; nothing selects. A rule cannot say *the latest*,
and `_settle` never reconsiders a binding it took. That is one question wearing three hats: §21's
backtracking, *when is a plan settled*, and *when may a request be re-asked*.

Also still open, and the same question three ways: nothing says when a plan is *settled*, when a `due`
rule is *done*, or when a request may be *re-asked*.

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
