# UGM — Universal Graph Machine

**An agent that plans, acts, observes and explains itself — where almost nothing about reality is
built into the engine.**

> **New here? Start with the [illustrated tutorial](https://ercasta.github.io/Universal-Graph-Machine/)**
> — a plain-language, mobile-friendly book that teaches the machine from scratch, with live pages
> that run the real engine in your browser. No background needed. The rest of this README is the
> technical overview; the full argument is [`docs/rules-design.md`](docs/rules-design.md).

UGM is a self-contained Python library with no dependencies.

```bash
python -m ugm.selftest              # 646 checks, 0 failing
python -m ugm ugm/rules/delay.ugm --why "owed(ana,money)"
```

## The one claim

**Almost nothing in this system is the engine.** Moments, entries, signs, spans, rules, modalities,
channels, frames, goals and plans are a *representation of reality that the agent uses* — open class,
shipped as ordinary data, replaceable at run time. They are not machinery the engine is built out of.

An agent that has them reasons better than one that treats every proposition as a bare fact: it can
say what it used to believe, what it is merely supposing, and on whose word. That superiority is a
matter of what it was **taught**, not of what it is **made of**. One could teach a person to think
this way without changing the chemistry of their brain.

What genuinely cannot be taught is five items, and **not one of them mentions reality**:

```
structure + ordering        by economy
variables + substitution    irreducible -- defining matching requires matching
a register                  irreducible -- finding where to write requires a read
a stamp on every mint       by guarantee -- reducible provenance is forgeable
one total step              irreducible -- selecting the selector requires selection
```

The test that draws that line:

> **A name is engine-level only if match and write cannot be defined without it. Everything else is a
> convention, and the machinery that uses it must be expressible as rules.**

It has a falsifiable consequence, which is the point of stating it: **the interpreter's step should
have no phases.** It has zero. The step is `read enough -> recall -> match -> defeat -> forgo ->
quiescence -> arbitrate -> note doubt -> apply`, and nothing in it decides anything a rule could have
decided.

> **Adding a connective adds rows, not branches.**

## What it looks like

```
rule <cancel>     = implies( { +cancelled(?f) }, { +disrupted(?f) } )
rule <crewing>    = implies( { +cause(?f, crew) }, { -extraordinary(?f) } )
rule <compensate> = implies(
    { +disrupted(?f), +booked(?p, ?f), -extraordinary(?f) },
    { +owed(?p, money) } )

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)
```

```
$ python -m ugm delay.ugm --why "owed(ana,money)"
delay.ugm: 15 ticks, ended quiescent

why owed(ana,money)?
  +owed(ana, money) @M0, via kb, licensed by applied(<compensate>)
    because +disrupted(bl204) @M0, via kb, licensed by applied(<cancel>)
    because +booked(ana, bl204) @M0, via kb, licensed by loaded(booked(ana, bl204))
    because -extraordinary(bl204) @M0, via kb, licensed by applied(<crewing>)
    because +cause(bl204, crew) @M0, via kb, licensed by loaded(cause(bl204, crew))
    because +cancelled(bl204) @M0, via kb, licensed by loaded(cancelled(bl204))
```

Nothing logs. Every entry records what licensed it and every application records what it consumed,
because the strength of a supposed conclusion, the resolution of a defeat, and learning from examples
all need those records for *correctness*. `why` is a walk over structure that was already there.

## The substrate

Nodes with **ordered members**, and nothing else. Edges carry no labels, no attributes and no truth
values, so anything you want to say about a connection has to be a node.

```
on(a, b)                     a relation instance -- a node with a relation and two members
entry(<M7>, on(a, b), +)     a CLAIM about it -- locus, proposition, sign
moment(delta, predecessor, licence)
```

A **proposition claims nothing**; only an entry does. Two levels are what negation costs, and they
buy the distinction between *the world moved* (a new entry) and *my record was wrong* (a fact about
the old entry). A system that cannot tell those apart quietly rewrites its own history.

Reading is a **walk**, ordered by two indices: **latest locus, then latest deposit**. So *what do I
now think about M7* and *what did I think at M7* are the same walk from two starting points.

Signs are `+`, `−`, `?` — and **no entry at all**, which means *inherit*, not *unknown*. So `−` means
denied, never absent, and open-world reasoning stays honest.

## What is taught

| | |
|---|---|
| **rules** | `causes(A, B)` / `implies(A, B)` — a fact relating two generic moments, so a rule is a subject and askable |
| **spans** | an entry's locus may be a stretch, so *they took turns* is sayable without inventing a number of turns |
| **shapes** | recursive definitions over spans, in ordinary vocabulary |
| **modality** | a wrapping term, `likely(p)`, crossed by **supposing** — unwrap in, re-wrap out |
| **provenance** | channels, frames and a gate; trust is a rule, never a hard-wired intake |
| **norms** | checked at the write, never in the competition, because the opaque component may not be load-bearing for safety |
| **the agent's own state** | goals, plans, expectations and surprise as ordinary entries; preemption is a precedence claim over ordinary rules |
| **acquisition** | a rule is a node, so a rule can be the conclusion of a rule |
| **attention** | a score per rule; take the first that matches, then spend — the rules stay fixed and the **postconditions** are what learning calibrates |
| **suspending it** | attention is a **stack** of queues, not one queue: `push` opens a frame on the nodes a sub-line is about, `pop` returns and carries one node back. A frame carries the expert whose rules are in play and its table, so a consultation is a resume rather than a re-run |
| **several agents** | two minds are two scopes, not two frames; what crosses is an utterance, and belief is the hearer's trust rule |
| **several experts** | the other axis: one graph and one history, separate rule sets and tables. `knows`/`extends` are ordinary facts, so inheritance is one rule and *which rules has this expert* is a query |

## Layout

Four packages, and the split is a claim about dependencies rather than a filing
system. `core` is the transitive closure of `machine`, `attention` and `text`:
**nothing outside it is needed to run an agent**, and nothing inside it imports
anything outside.

```
ugm/
  core/        9   the engine
                   graph -> chain, channels -> gate, rules -> machine
                   -> text -> sexpr, attention
  learning/    7   teaching, learning, practice, lifting, maze, surprise, forest
                   what the agent learns from use. `core` imports none of it.
  gates/       6   agreement, quiescence, state, bundle, vocabulary, necessity
                   RELEASE CRITERIA -- each holds a fast path to the slow
                   definition of the same thing. Red here is a regression.
  probes/     16   worlds and measured questions. Red here is a FINDING, and a
                   probe whose question is settled is a candidate for deletion.
  rules/           the shipped `.ugm` corpora  (see `ugm/corpora.py`)
  selftest.py      the runner
```

> **`gates` and `probes` are not the same kind of thing**, and lumping them was
> costing something: a settled probe sat in the same bucket as a floor gate, so
> nothing distinguished *this must pass to ship* from *this records what we
> learned*.

## Verification

Not pytest. One runner that prints every check's named observations and counts any `False` as a
failure, plus a set of gates that each hold a fast path to a slow definition on **every look, in
every fixture**:

```bash
python -m ugm.selftest           # 513 checks, 0 failing
./tools_sweep.sh                 # every module with a main(), found on disk

python -m ugm.gates.agreement    # the kept resolution against the raw walk
python -m ugm.gates.state        # the maintained state and its indices against the walk
python -m ugm.gates.quiescence   # the compiled verdict against the six rules defining it
python -m ugm.gates.bundle       # deletes each shipped rule and re-runs the suite
python -m ugm.gates.vocabulary   # unwebbed names, with a planted typo as a control
python -m ugm.probes.atlas       # islands, bridges, dead rules, pairs that could disagree
```

And the comparisons, which run two loops or two runs over the same corpora and report
where they differ rather than passing or failing:

```bash
python -m ugm.core.attention        # the table loop, the penguin, and `stop`
python -m ugm.learning.teaching     # a table calibrated from one demonstration against an uncalibrated one
python -m ugm.learning.learning     # the same world twice, with "no better" an allowed answer
python -m ugm.learning.practice     # rehearsing a goal inside a supposition against enacting it
python -m ugm.probes.table          # several agents talking, in-process against one process each
python -m ugm.probes.experts        # several experts over ONE graph, consulting each other
python -m ugm.probes.frames         # the attention stack: what a flat queue evicts, and what a frame keeps
```

> **An agreement gate that agrees is worth nothing until it could have disagreed.** Every gate deletes
> each rule of the thing it checks, one at a time, and reports any whose removal breaks nothing.

## Documentation

- **[The book](https://ercasta.github.io/Universal-Graph-Machine/)** — the tutorial. Source in
  [`book/`](book/).
- **[`docs/rules-design.md`](docs/rules-design.md)** — the design, and the only design doc.
  Self-contained, argued from seven requirements, with every representation decision scored in a
  table before it is taken.
- **[`docs/code-walkthrough.md`](docs/code-walkthrough.md)** — a map of the code for a developer
  about to change it: what each file owns, one tick end to end, where the caches are and what holds
  them honest, and the traps that have cost time here.
- **[`docs/authoring.md`](docs/authoring.md)** — the shorter, meaner document: what actually bites
  when you sit down and write a corpus, ordered by how much time it costs before you find it.
- **[`docs/HANDOFF.md`](docs/HANDOFF.md)** and **[`docs/observations.md`](docs/observations.md)** —
  the working record.

## House rules

> **A claim with no measurement behind it is an opinion, and it is marked as one.**

> **No feature is novel until something falsifies the claim.** Nearly everything here has a
> literature. What is claimed is the assembly and the discipline, and both stay hypotheses.

## Licence

MIT. See [`LICENSE`](LICENSE).
