# A code walkthrough

>  **STALE SNAPSHOT (noted 2026-08-21, release sweep).** Run at `907e6c9`,
> before the module tree grew `core/`, `gates/`, `learning/` and `probes/`,
> before the table loop shipped as *the* loop, and before `ugm.walkers`,
> `ugm.arbitration`, `ugm.modality` and `ugm.workload` were deleted. Every
> `python -m ugm.<name>` below needs the subpackage path now (`ugm.probes.dungeon`),
> two of the four commands name modules that no longer exist, every count and
> line number has moved, and §4 walks the retired option-set loop,
> which has since been deleted outright — `Machine.tick` is now one bounded
> step of the table loop. The
> *shape* of the map is still roughly right; trust nothing quantitative. The
> current entry points: `python -m ugm.selftest`, `./tools_sweep.sh`, and
> `docs/design/*.md` per module.

For a developer who has to work on the engine and has not read 30,000 lines of it. This is a map of
the **code**: what each file owns, what one step of the loop actually does, where the caches are, and
which mistakes cost real time here.

It is not the argument. `docs/rules-design.md` is the design and says *why*; `docs/representation.md`
is the shorter reference for *how things are represented and what goes wrong the other way*;
`docs/authoring.md` is for writing a corpus rather than the engine. Read this one first if you are
about to change Python.

Everything below was run at commit `907e6c9`, not recalled. Timings are from one machine and are
there to tell you what is instant from what you should start and walk away from.

---

## 1. Run it before reading it

```bash
python -m ugm.selftest                                     # 523 checks, 0 failing -- 6.7s
python -m ugm ugm/rules/delay.ugm --why "owed(ana,money)"  # the whole thing on one page
python -m ugm.dungeon                                      # 17 checks -- a corpus nobody designed for
python -m ugm.walkers                                      # 16 checks -- a search written as facts
```

The second is the fastest orientation available: fifteen ticks, a conclusion, and a trail that names
every entry it rests on. If the `why` output makes sense to you, the substrate will.

**Nothing is pytest**, and that is deliberate. `ugm/selftest.py` is one runner: `check(section, name,
value)` appends a named observation, `main()` prints every one of them and counts any `False` as a
failure. A check whose *name* does not say what was observed is not this repo's style.

---

## 2. The shape of the tree

30k lines of Python and about a thousand lines of corpus, of which the engine is a third. Most of the
repository is instruments and fixtures, and knowing which is which is the difference between a
two-hour and a two-day orientation.

| role | modules | what it means for you |
|---|---|---|
| **the engine** | `graph` 397, `chain` 336, `rules` 1484, `gate` 156, `machine` 4582, `text` 1450, `attention` 705, `channels` 91 | changing these changes what the machine *is* |
| **the corpus that ships** | `ugm/rules/bundle.ugm` | conventions as **rules**, not branches. Editing this is not editing the engine |
| **floor gates** | `state`, `agreement`, `arbitration`, `quiescence`, `bundle`, `necessity`, `vocabulary`, `atlas` | each holds a fast path to a slow definition, on every look |
| **comparisons** | `attention`, `teaching`, `learning`, `practice`, `table`, `experts` | two loops or two runs over one corpus; *no better* is an allowed answer |
| **probes and arcs** | `modality`, `shapes`, `compose`, `backward`, `harmony`, `workload`, `tools`, `forest`, `walkers`, `acting`, `surprise`, `lifting`, `clock`, `hindsight`, `interpret`, `artefact`, `maze` | one question each, measured, with the write-up **in the module docstring** |
| **corpora as fixtures** | `dungeon`, `quest`, `melee`, and `ugm/rules/*.ugm` | worlds to run the engine against |
| **the runner** | `selftest` 7466 | every claim the design makes, as a named observation |

Two conventions that will save you time:

**A module's docstring is its paper.** `python -m ugm.<name>` prints it and then runs the checks it
argues for. If you want to know what `ugm.surprise` established, read the top of `ugm/surprise.py` —
it is the finding, with the trail and the negative results, not a usage note.

**The `§` numbers in the code are stale.** They predate the current numbering in `rules-design.md`:
`gate.py` says `(§13)` and frames are now §17; `rules.py` says `Rules (§8)` and rules are now §12.
Match on the section **title**, never on the number.

---

## 3. The five files that are the machine

### `graph.py` — the substrate, 215 lines

Nodes with ordered members. Three calls decide everything downstream:

```python
g.atom("paul")        # a fresh node with a name -- DOES NOT INTERN
g.rel(r, a, b)        # r(a, b) -- INTERNS: same relation and members, same node
g.instance(r, a, b)   # r(a, b) -- MINTS: a new node every call
```

`rel` interns so one proposition spoken of twice is one node. `instance` mints so two things that are
alike are still two — moments, frames, entries. **Names are for printing; nodes are identity**
(`call_it` cannot make two nodes one or tell two apart).

Three indices, all insertion-ordered so nothing downstream inherits a tie-break from a hash:
interned instances by `(rel, members)`, instances by relation, instances by `(relation, position,
member)`. The third is what makes a join a join rather than a scan.

### `chain.py` — moments, entries, and the read, 597 lines

```python
Entry(node, locus, proposition, sign, licence, source, consumed, mention)
Moment(node, predecessor, chain)         # a state of affairs; moments form a TREE
chain.deposit(seat=..., locus=..., proposition=..., sign=...)
chain.resolve(p, locus, seat)            # does p hold AT locus, as believed AT seat?
```

The **proposition** is `entry(locus, proposition, sign)` — three members and never a fourth. Licence,
source and what the application consumed are ordinary facts *about* the entry rather than fields of
the claim, which is what lets `why(p)` walk back to the die roll. `Moment.delta` is the entries
deposited in it; the Python attributes are a mirror of graph content, maintained where the state is,
and `ugm.state` is the gate that holds the mirror to the walk.

`resolve` is the single most important function in the repository, and the ordering inside it is the
design: **latest locus first** (so silence means inherit), **latest deposit next** (so the current
view beats what the agent used to think). `Moment.at_or_after` walks the predecessor relation — an
ancestry test, never a depth comparison, because supposing forks the chain.

Measured: the walk was **86% of runtime** before it was indexed, and 16 of every 17 walks were the
same walk repeated. That is why `Situation` and the caches in §5 exist.

### `rules.py` — rules, matching, arbitration, 1992 lines

```python
Member(sign, pattern, locus=None, binds=None)   # one premise or one conclusion
Rule(node, connective, antecedent, consequent, name="")
match(...)          # pattern against the resolved state
unify / unify_patterns / generalise             # and generalise is anti-unification
arbitrate(...) / defeat(...)
Situation(...)      # the resolved state, indexed by (sign, relation), per tick
```

A member with a **sign** is about an entry; a member **without** one is structural — it matches the
graph, and `−` on it means *not derived* rather than *someone denied it*. That one distinction is
where negation as failure lives, and `structural_relations(chain)` is the table of what a structural
member may ask the chain (`anc`, `pred`, `in_delta`, `entry_of`, `span_of`, `holds_at`, …).

### `gate.py` — the one place a stamp is applied, 232 lines

```
Proposition and sign come from the rule.
Locus, deposit, licence and source come from the frame and the channel.
A rule may not name the second four.
```

`Gate.write` is the whole write path: the **norm veto** runs first (so a forbidden entry never exists,
not even briefly), then the deposit, then `on_write` hooks — which is where effects leave the agent.
If you are looking for "where does the agent act", it is here, not in a phase of the loop.

### `machine.py` — the interpreter, 5592 lines

Big, and the last thousand lines are instruments hanging off the loop rather than loop: `report`,
`why`, `review`, `blame`, `refine`, `save`/`replay`, and the induction helpers at the bottom. The loop
itself is one method, and `_install_bundle` is four lines that load a corpus.

---

## 4. One tick, end to end

`Machine.tick()` is worth reading in full once — 130 lines, and the comments are the design.
The claim it exists to make is that **the step has no phases**: nothing in it decides anything a rule
could have decided.

```
tick()
  g.rel(ASKING, seat)          # the seat is askable, so chain-reading rules have an anchor
  channels.since_last_tick()   # how much of the world arrived since the last step
  _enough()                    # the second way to be over: a corpus said stop
  _recall()                    # which rules come to mind -- a function, not a search
  _situation()                 # ONE walk, resolving the state for this tick
  _applications(...)           # match each recalled rule against it
  _in_play() / _rank()         # what the table recommends now
  _choose()                    # defeat -> quiescence -> passing-up -> arbitration, lazily
  _note_defeat() / _note_doubt() / _forgo()      # what lost, on the record, BEFORE the move
  _apply(chosen)               # write the consequent
  _spend(chosen, wrote)        # refraction, and the table's cost
```

When nothing is chosen, the escalation order is the interesting part: `_widen` (the shortlist ran
dry, so recall harder), `_recover` (look again at what was put out of mind), `_leave` (a hypothesis
ran out of work — carry its conclusions out), `_wake`, then `quiescent`. **A shortlist that ran dry is
not a search that finished**, and `blocked` depends on the difference.

`_apply` is the forward read: `implies` deposits into the *same* moment (derived — retract the
antecedent and it goes), `causes` deposits into a *later* one (asserted — water you stopped heating
stays boiled). `_conclude_at` decides the locus: a consequent's own `at $m` when it has one, the
frame's topic otherwise. The register moves only on `causes` — and the move is itself a write now:
`Gate.reseat` deposits `+moved(<from>, <to>)` with the licence that caused it, which was the oldest
item on the acceptance section's owed list. *Position is where and was always recorded; the seat is
when and was not.*

---

## 5. The surface, and the bundle

`text.py` is the authoring surface. Statement kinds: `rule`, `fact`, `say <channel>:`, `expert`,
and `after` / `frozen` / `when` (postconditions and rerankers). There is one surface: a
second s-expression reader was deleted on 08-22, unexercised by anything.

Two things about the loader that are load-bearing rather than incidental:

**Identity is decided at intake, in a scope.** Documents loaded under one scope share a name table, so
`kettle` means one node inside a corpus by construction rather than by inference. There is no
`sameas`.

**Reserved names are how the surface reaches the machinery.** `Machine.reserved` maps every name the
engine coins to its node, and the loader seeds its table from it.

>  `Graph.atom` **does not intern**. A relation the machinery uses that is missing from `reserved` is
> a node no corpus can reach: a rule written against it mints a second node with the same name,
> `is_stratum0` quietly answers no, the member matches nothing, and **nothing raises**. Five
> occurrences on record.

`Machine._vocabulary_is_surface_nameable()` is the guard that turned that into a loud failure for the
bundle's own vocabulary — it raises with the list of unreachable names. If you add a computed relation
(`holds_at`, `time`, `entry_of` …), register it there **and** add it to `ugm/vocabulary.py`'s
classification, or two gates go red.

`ugm/rules/bundle.ugm` is the conventions that ship, as rules: `<intake>`, `<denial>`, `<give-up>` and
the rest. It used to be 250 lines of Python inside `_install_bundle`. Moving it out is the design's
own claim being tested — and it immediately found two names (`arrived`, `not`) that no corpus could
write. **Order in that file is load-bearing**: the authored order is the arbitration tie-break, and
two thirds of this agent's arbitrations are still settled by it.

---

## 6. Where the caches are, and what keeps them honest

Everything fast in this engine is an index over a definition that is slow and obvious. The rule is
that **the slow definition stays runnable and something compares them on every look**:

| fast path | slow definition | gate | cost |
|---|---|---|---|
| `Chain._claims`, `_by_node` | the walk in `resolve` | `python -m ugm.state` | 13s |
| the kept resolution | the raw walk, as **rules** | `python -m ugm.agreement` | 0.3s |
| `_choose`'s heap | the list version of the same four steps | `python -m ugm.arbitration` | 6.5s |
| the compiled *this would change nothing* | the six rules that define it | `python -m ugm.quiescence` | 2m44s, exits 1 |
| every bundled rule | delete it and re-run the suite | `python -m ugm.bundle` | 162s |

> **An agreement gate that agrees is worth nothing until it could have disagreed.** Every gate here
> deletes each rule of the thing it checks, one at a time, and reports any whose removal breaks
> nothing. If you add a gate, add the kill-probe in the same commit — a check that cannot fail is the
> failure mode this project has caught most often.

`Situation.__init__` and `_in_play` were both O(state) per candidate once, and both showed up as the
top of the profile. If you are making the loop slower, those are where it will show.

---

## 7. Reading the comments

The engine's comments carry two marks, and they are worth grepping:

```
⭐ / ⭐⭐ / ⭐⭐⭐     the finding: why this line is this way, and what it buys
  /  /       the trap: what breaks if you undo it, usually with the measurement
```

125 / 31 / 168 of the first and hundreds of the second. `⭐⭐⭐` in `machine.py` and `rules.py` is
close to a table of contents for the design decisions that are actually in force. Before changing a
line that carries one, read it — most of them record something that was already tried.

---

## 8. Four recipes

**Add a relation a corpus can use.** Nothing to do. The class is open: write `owns(paul, boat)` in a
corpus and it is a node. The engine implements no meaning for it, which is the point.

**Add a relation the *engine* computes** (like `holds_at`). Implement the answerer in
`rules.structural_relations` or as a `Machine.answerer`, add the name to `Machine.reserved`, and add
it to `ROLES` in `ugm/vocabulary.py`. Skip the second and it silently matches nothing; skip the third
and the vocabulary census fails.

**Add a shipped convention.** Write it as a rule in `ugm/rules/bundle.ugm`, in the position its
precedence needs. `python -m ugm.bundle` will delete it and tell you whether anything depended on it —
if nothing does, it is not load-bearing and should not ship.

**Add a check.** In `selftest.py`, a function per claim, `check("§n", "what was observed", value)`,
and call it from `main()`. Name it as an observation, not as a label: *the trail reaches the
utterance*, not *test_trail*. For a whole arc, write a module instead — docstring as the paper, a
`main()` that prints it, runs gated checks, and returns 1 on any failure.

---

## 9. Traps that have cost real time here

Collected from `docs/representation.md` §7 and the module docstrings, because every one of them was
paid for at least once:

- **`atom` does not intern.** See §5. Five occurrences.
- **A rule's own pattern is an instance of its relation.** `instances_of(said)` returns the pattern
  `said($p)` alongside the real ones. Filter with `has_var`, or a count is wrong and a numeric read
  raises.
- **A variable-bearing structure is not a value.** Using one as an index pivot asks for the bucket of
  the pattern node itself, which nothing is an instance against — so the member matches nothing,
  silently. Fixed in `_narrowed`; the suite was 518/0 with and without the fix at the time, because a
  corpus that only writes atoms in argument positions cannot reach it.
- **Minting the answer interns it.** A harness that builds its question as a node can later find it as
  its own answer. Compute and bind by hand.
- **The cheapest-looking run is often the broken one.** A walker design that lost a branch finished in
  fewer ticks, with less work, no error and no diagnostic. **Assert the absence the failure produces**,
  not the presence you hope for.
- **A homogeneous fixture cannot measure a discriminator**, and a check whose sensitivity depends on a
  race reports green while the bug is there.
- **A postcondition cannot see what its own rule just concluded** — its query is matched against the
  state as of the start of the tick.
- **Never compare node ids across machines.** Two graphs built in the same order assign the same
  integers, so a cross-machine identity test is accidentally right often enough to pass. Compare
  rendered text.

---

## 10. The state of the tree, 2026-08-18

Measured while writing this, so it is a snapshot rather than a promise:

```
selftest      523/0     6.7s        dungeon    17/0    2.9s     walkers   16/0   0.2s
agreement     28/0      0.3s        quest       9/0    0.4s     acting    11/0   1.2s
state         0 disagreements 13s   table      16/0    0.4s     surprise   7/0   0.1s
arbitration   0 disagreements 6.5s  experts     7/0    0.1s     lifting    7/0   0.1s
bundle        19/19 exercised 162s  interpret   6/0    0.6s     clock      8/0   0.1s
compose        9/0      0.1s        backward    7/0    0.2s     hindsight  8/0   0.1s
maze           7/0      0.1s
```

Three things a newcomer should not mistake for their own breakage:

**`python -m ugm.vocabulary` fails 2 of 18.** `holds_at` and `time` were added to `Machine.reserved`
and never classified in `ROLES`, so the partition is not total and the *no reserved name is a domain
word* check reports 2. A stale classification, not a leak in the vocabulary — and the same commit
that added `moved` did classify it, which is the tell: **classifying the name is the step that gets
forgotten**, and the census is what catches it.

**`python -m ugm.quiescence` exits 1.** It reports **145 candidates, 0 disagreeing** — the gate
itself passes — and then exits non-zero on its own coverage hole: `<silent>` *derived nothing in any
of 12 fixtures*, so suppressing it changes nothing and the fixture cannot test it. That is the gate
reporting honestly rather than a failure to fix blindly. 2m44s here, down from the ~16 minutes
recorded in `docs/HANDOFF.md` before the kill-probe was reworked.

**`python -m ugm.necessity` did not finish inside 400s** in this run. It kill-probes reserved names,
which is a full suite per name.

And one real defect, so it does not surprise you when you meet it in the code:

> **Containment holds for entries and fails for structure.** A conclusion drawn inside a supposition
> is not believed outside it; a **stratum-0** conclusion drawn inside it is in the graph and visible
> everywhere, because it is an interned relation instance belonging to no moment. `rules-design.md`
> §16 carries the probe, and `docs/situations.md` is the proposed answer.

---

## 11. Where to go next

- `docs/rules-design.md` — the design and the argument. Long, and the only place the *why* is complete.
- `docs/representation.md` — the reference: the substrate, the two layers, and every settled
  representation strategy with the reason.
- `docs/authoring.md` — for writing corpora rather than engine code.
- `docs/observations.md` — the audit of what is in Python that should not be, with the contagion
  measured. Read before proposing to move something into the engine.
- `docs/HANDOFF.md` — the working record, newest session first.
- `book/` — the tutorial, if you would rather learn the machine than the code.
