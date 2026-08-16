# UGM — Universal Graph Machine

**An agent that plans, acts, observes and explains itself — where almost nothing about reality is
built into the engine.**

> **New here? Start with the [illustrated tutorial](https://ercasta.github.io/Universal-Graph-Machine/)**
> — a plain-language, mobile-friendly book that teaches the machine from scratch, with live pages
> that run the real engine in your browser. No background needed. The rest of this README is the
> technical overview; the full argument is [`docs/rules-design.md`](docs/rules-design.md).

UGM is a self-contained Python library with no dependencies.

```bash
python -m ugm.selftest              # 549 checks, 0 failing
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
delay.ugm: 11 ticks, ended quiescent

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

## Verification

Not pytest. One runner that prints every check's named observations and counts any `False` as a
failure, plus a set of gates that each hold a fast path to a slow definition on **every look, in
every fixture**:

```bash
python -m ugm.selftest        # 549 checks, 0 failing
python -m ugm.agreement       # the kept resolution against the raw walk
python -m ugm.state           # the maintained state and its indices against the walk
python -m ugm.arbitration     # the fast chooser against the slow one
python -m ugm.quiescence      # the compiled verdict against the six rules defining it
python -m ugm.bundle          # deletes each shipped rule and re-runs the suite
python -m ugm.vocabulary      # unwebbed names, with a planted typo as a control
python -m ugm.atlas           # islands, bridges, dead rules, pairs that could disagree
```

> **An agreement gate that agrees is worth nothing until it could have disagreed.** Every gate deletes
> each rule of the thing it checks, one at a time, and reports any whose removal breaks nothing.

## Documentation

- **[The book](https://ercasta.github.io/Universal-Graph-Machine/)** — the tutorial. Source in
  [`book/`](book/).
- **[`docs/rules-design.md`](docs/rules-design.md)** — the design, and the only design doc.
  Self-contained, argued from seven requirements, with every representation decision scored in a
  table before it is taken.
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
