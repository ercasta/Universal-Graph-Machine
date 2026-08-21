# UGM — Universal Graph Machine

**An agent that plans, acts, observes and explains itself — where almost nothing about reality is
built into the engine.**

> **New here? Start with the [illustrated tutorial](https://ercasta.github.io/Universal-Graph-Machine/)**
> — a plain-language, mobile-friendly book that teaches the machine from scratch, with live pages
> that run the real engine in your browser. No background needed. The rest of this README is the
> technical overview; the full argument is [`docs/rules-design.md`](docs/rules-design.md).

UGM is a self-contained Python library with no dependencies.

```bash
python -m ugm.selftest              # 537 checks, 0 failing
python -m ugm ugm/rules/delay.ugm --why "owed(ana,money)"
```

## How it works

The system works in a very simple way. It is a loop: look at the current state, decide what to do
next, do it. The simplicity hides where the real complexity is — *decide what to do next* is the
hard part — and the design's answer is to keep that complexity **out of the engine**.

The engine is almost empty. It has no decision rules built in; it knows the conventional
representation of a few concepts (and that only for performance, and to provide mechanisms like
short-term memory independently of any decision rule). Everything it runs is supplied as data, in
two layers:

- **A world model** — the knowledge base. How things relate, inference rules, cause–effect, and
  which actions exist over that world. This says what *is* and what *would happen*.
- **Competence** — what to do. In any non-trivial world model the possible actions are legion (they
  are parametric), and knowing how the world works does not tell you what to reach for: you can
  know exactly what every move of a Rubik's cube does and still be clueless about solving one.
  Competence fills that gap: scores, attention, when to stop, what to try after what.

Competence is authored as a starting point, and the system can improve it by **learning** — an
episode ends, the trail is reviewed, and what was learned is written back as ordinary corpus text
the next episode loads.

What that buys, and what this project is for: **transparent, ownable, explainable, private
reasoning over knowledge bases you control.** Every conclusion has a trail (`--why` below), every
mechanism above the floor is data you can read and replace, and nothing needs a server.

## The one claim

**Almost nothing in this system is the engine.** Moments, entries, signs, rules, modalities,
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
have no phases.** It has zero. The step is `score -> take the first rule in the window whose
antecedent matches -> apply it -> spend its postconditions`, and nothing in it decides anything a
rule could have decided: *done* is the output of a rule that spends `stop`, *refocusing* is a rule
that spends `unattend`, and *suspend this line of work for another* is two more (`push`, `pop`).
The loop knows a score, a match, and that a rule said stop — never what any of them is for.

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
$ python -m ugm ugm/rules/delay.ugm --why "owed(ana,money)"
ugm/rules/delay.ugm: 14 ticks, ended quiescent

why owed(ana,money)?
  +owed(ana, money), via kb, licensed by applied(<compensate>)
    because +disrupted(bl204), via kb, licensed by applied(<cancel>)
    because +booked(ana, bl204), via kb, licensed by loaded(booked(ana, bl204))
    because -extraordinary(bl204), via kb, licensed by applied(<crewing>)
    because +cause(bl204, crew), via kb, licensed by loaded(cause(bl204, crew))
    because +cancelled(bl204), via kb, licensed by loaded(cancelled(bl204))
```

Nothing logs. Every entry records what licensed it and every application records what it consumed,
because the strength of a supposed conclusion, the resolution of a defeat, and learning from examples
all need those records for *correctness*. `why` is a walk over structure that was already there.

## The substrate

Nodes with **ordered members**, and nothing else. Edges carry no labels, no attributes and no truth
values, so anything you want to say about a connection has to be a node.

```
on(a, b)                     a relation instance -- a node with a relation and two members
entry(on(a, b), +)           a CLAIM about it -- proposition and sign, and never a third
moment(delta, predecessor, licence)
```

A **proposition claims nothing**; only an entry does. Two levels are what negation costs, and they
buy the distinction between *the world moved* (a new entry) and *my record was wrong* (a fact about
the old entry). A system that cannot tell those apart quietly rewrites its own history.

Reading is a **walk**, and the whole of it is **later supersedes earlier** — an entry has no second
time to be indexed by, so there is one order and no ancestry test. What the agent used to think is
still findable, because a revision *adds* rather than overwriting.

Signs are `+`, `−`, `?` — and **no entry at all**, which means *inherit*, not *unknown*. So `−` means
denied, never absent. Asking the other question — *does anything assert this?* — is `no p(?x)`, a
distinct member mode, because a rule that materialises a denial has to ask about absence first.

## What is taught

| | |
|---|---|
| **rules** | `causes(A, B)` / `implies(A, B)` — a fact relating two generic moments, so a rule is a subject and askable |
| **the world model** | entities are labelless nodes created by rules; a reified relationship has an id and can itself take part in one; a **denotation** is an expression with no id, which is what makes it a query |
| **shapes** | recursive definitions over the chain, in ordinary vocabulary |
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
python -m ugm.selftest           # 537 checks, 0 failing
./tools_sweep.sh                 # every module with a main(), found on disk

python -m ugm.gates.agreement    # the kept resolution against the raw walk
python -m ugm.gates.state        # the maintained state and its indices against the walk
python -m ugm.gates.quiescence   # the compiled verdict against the six rules defining it
python -m ugm.gates.bundle       # deletes each shipped rule and re-runs the suite
python -m ugm.gates.vocabulary   # unwebbed names, with a planted typo as a control
python -m ugm.probes.atlas       # islands, bridges, dead rules, pairs that could disagree
```

The loop itself is a door too, and what it runs are worked examples rather than a
comparison — there is no second loop left to compare it against:

```bash
python -m ugm.probes.attention      # the penguin, and `stop`
```

And the comparisons, which run two runs over the same corpora and report
where they differ rather than passing or failing:

```bash
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
- **[`docs/guide.md`](docs/guide.md)** — the author's and user's guide: install, run a corpus, read
  a trail, and the whole surface — facts, rules, signs, absence, aliases, experts, actions,
  lessons — with a worked example for each.
- **[`docs/rules-design.md`](docs/rules-design.md)** — the design, and the only design doc.
  Self-contained, argued from seven requirements, with every representation decision scored in a
  table before it is taken.
- **[`docs/authoring.md`](docs/authoring.md)** — the shorter, meaner document: what actually bites
  when you sit down and write a corpus, ordered by how much time it costs before you find it.
- **[`docs/code-walkthrough.md`](docs/code-walkthrough.md)** — a map of the code, kept with a
  stale-snapshot warning: the shape is right, the numbers are one landing old.
- **[`docs/HANDOFF.md`](docs/HANDOFF.md)** and **[`docs/observations.md`](docs/observations.md)** —
  the working record.

## House rules

> **A claim with no measurement behind it is an opinion, and it is marked as one.**

> **No feature is novel until something falsifies the claim.** Nearly everything here has a
> literature. What is claimed is the assembly and the discipline, and both stay hypotheses.

## Licence

MIT. See [`LICENSE`](LICENSE).
