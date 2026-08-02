# UGM — Universal Graph Machine

**An agent that plans, acts, and can always show you the reasoning — because the reasoning is data it
can read.**

> 📘 **New here? Start with the [illustrated tutorial →](https://ercasta.github.io/Universal-Graph-Machine/)**
> — a plain-language, mobile-friendly book that teaches the machine from scratch, with live pages
> that run the real engine in your browser. No background needed. The rest of this README is the
> technical overview; the full documentation is in [`docs/`](docs/README.md).

UGM is a self-contained Python library with no dependencies. It holds a world in a graph, takes
goals, finds plans by imagining, carries them out, notices when reality disagrees, and answers
questions with the derivation that produced the answer.

```bash
pip install universal-graph-machine     # no dependencies, Python >= 3.9
python -m ugm.selftest                  # 221 checks, 0 FAILED
```

## The one idea

**Everything is in one graph, in one representation.** Facts, rules, goals, plans, hypotheses,
memories, explanations, conflicts, the planner's own frontier and the interpreter's own program
counter are all ordinary nodes and named edges. So the machine can reason *about* a rule as easily as
it reasons *with* one.

That is not a slogan about elegance; it is what every capability below is made of. The planner works
by **reading the stored instructions of the rules it might use**. Learning is a rule that writes a
rule. Refusing to answer a question with a rule that would act is *inspecting* that rule before
running it. None of those needed a subsystem — they needed the same substrate, asked a different
question.

### A rule is a function you point at something

The second idea, and the one that most distinguishes this from a rule engine:

> **Nothing fires.** A rule has parameters and runs when something calls it, on the arguments it was
> given, and never otherwise.

```
# Put the lid on a jar.
fn seal(j: jar) -> sealed_jar:
    SET F(j) "sealed" true
```

There is no `when` clause, because the circumstances are the caller's business. The trade is
explicit: you lose automatic cascades, and you gain a rule that cannot fire twice by accident, cannot
be triggered by a fact you did not expect, and cannot interact with a rule written by someone who
never heard of it. The library grows without any global program needing re-verification.

`F(j)` reads a *head* — the thing this rule was pointed at. A callee gets a fresh set of heads
holding only its own arguments, never its caller's.

### Types are shapes, so change needs no representation

A type is a **schema over a subgraph** — structure and attributes — checked by looking at the node,
never by consulting a tag. So `seal(j: jar) -> sealed_jar` is a **cast**, and whatever it changes is
merely how the cast is achieved. Nothing records that a mutation happened, because a node either
satisfies the stronger shape now or it does not.

Precondition and effect collapse into parameter type and return type. Multi-type membership and
de-recognition fall out rather than needing mechanism.

## What it does

### Goals, and plans that are *found* rather than built

A goal is a set of **constraint** nodes. Which constraints are still false is what turns search from
generate-and-test into means–ends.

The machine imagines each step on a **workbench** (a private copy of the world), keeping a **frame**
per step. When a frame satisfies the goal, the path to it already *is* a replayable plan. There was
never a plan-construction step to write.

```python
from ugm import asm, types as TY, thread as T, driver as D, intake as I
from ugm.graph import Graph

g = Graph()
TY.declare_type(g, "jar", attrs={"kind_of": "jar"})
TY.declare_type(g, "sealed_jar", base="jar", attrs={"sealed": True})
asm.load_text(g, 'fn seal(j: jar) -> sealed_jar:\n    SET F(j) "sealed" true')

shelf = g.mint("shelf"); g.link("root", "has", shelf)
salt = g.mint("jar", kind_of="jar", label="salt")
g.link(shelf, "jar", salt); TY.tag(g, salt, "jar")

th   = T.open_thread(g, "session")
goal = I.read_goal(g, "goal seal the salt:\n    salt.sealed = true")

D.carry_out(g, goal, th, shelf)      # {'done': True, 'tries': 1}
g.attr(salt, "sealed")               # True
```

**Guidance, measured.** On a three-crate tower: 2–3 imagined states guided against 53–87 blind, same
optimal plan. Both are ranges because tie-breaking varies between runs; the *plan* is invariant.

**Rank a guess; prune a proof.** Relevance is a guess about what will help, so it only ever *orders*
candidates — filtering on it would make Sussman's anomaly unsolvable, since that puzzle must *begin*
with a move that closes nothing. A safety constraint (`never unstack`, `at most 3 steps`) is a proof
that a branch is dead, so it prunes, before the step is imagined.

### Questions are goals

"Is Paul mortal?" is the goal *find out whether Paul is mortal*. There is no second control loop and
no query evaluator — the same search runs, and **the plan it finds is the proof**.

```python
I.respond(g, "ask is the salt sealed?:\n    salt.sealed = true", th)
# YES - derived in 1 step(s) (1 step(s) considered)
# yes, because:
#   seal(j=salt)
```

Asking changes nothing: the derivation runs on a workbench, so the salt is not sealed by having
asked. Answering then settles the verdict so the next question need not re-derive it.

Three verdicts, and the third is not a failure: `yes`, `no` (something incompatible holds *now*), and
`unknown`. A failed search has learned about its own library, not about the world. Closing the world
is a **stance** you pass per question, never a property of the machinery.

A derivation may never act: concluding and doing are both "running a rule" here, so a rule may answer
a question only if it **provably never dispatches**, read off its stored body and transitively
through its calls. That is a proof, so it prunes — and it is deliberately conservative in the
refusing direction, because an unreadable body is barred.

### Explanations that refuse to be invented

```python
I.respond(g, "why is the salt sealed?:\n    salt.sealed = true", th)
# salt.sealed = True: because seal(j=salt) ran
```

Three honest answers — *derived here*, *true but given*, *not true at all* — and a deliberately
absent fourth. For a fact that already holds with no recorded history, a fresh search would happily
produce "here is a way this could follow". That is a fine answer to a *different* question and a lie
as an account of history, so the machine says it does not know. An engine that manufactures plausible
history makes **every** explanation untrustworthy.

### When reality disagrees

Expectations are **derived** from the two frames the workbench already holds — never authored, never
stored — and they are **qualitative, never quantitative**: a mock minting two files is a *witness,
not a promise*. One file completes the plan, five complete it, zero diverges.

On divergence the machine stops at that step (everything after it assumed the step held) and does
**not** roll back — real effects have already left. Then either **resume** onto an explored branch
that assumed what actually happened, or **replan** by re-pursuing the goal from the world as it now
is.

### Deliberation, memory, learning

- **Authored knowledge is data.** Guidelines reorder, methods decompose, criteria name the move to
  make, directives refuse when they cannot act, and norms can be defeated by a higher authority. With
  criteria, a search imagines five states whatever the size of the world, where structural guidance
  alone stops finding a plan at all between six and seven blocks.
- **The thread** — attention shifts and applications, in order, each carrying *why* it followed the
  last. Ordinary graph data, so a rule can walk it.
- **Learning** — compiling an episode produces a new rule, stored identically to an authored one and
  indistinguishable from it. No learning subsystem; writing a rule is writing nodes.
- **Interference** — two independently authored rules writing one slot for *different goals*,
  distinguished from a deliberate sequel, without which the detector is noise.
- **Forgetting is the default.** Keep what cannot be re-derived; sweep the rest. On the measured
  case, 892 nodes down to 238 with every answer unchanged.

## Talking to it

Three verbs over **one grammar**, because a question is a goal:

```
goal build a tower:      ask is it built?:      why is it built?:
    a on b                   a on b                 a on b
    b on c                   b on c                 b on c
```

The whole vocabulary is eight forms — a relationship, an attribute value, an existential, a type;
plus `never f`, `never touch x`, `must f`, `at most n steps`. The route constraints work in questions
too: `never phone_the_registrar` asks *"can you establish this without reaching outside?"*

**Refusal is the feature**, three ways, all loud: a line outside the vocabulary, a name matching
nothing, and a name matching **more than one thing** — because guessing between two candidates would
invent a referent. A refusal leaves nothing behind.

**Where a language model fits:** a model may *write this text*; the parser then accepts or refuses it
deterministically. What a model must never do is reach past the surface and write graph structure,
because then nothing could refuse it.

See **[docs/authoring.md](docs/authoring.md)** for the full guide.

## Three limits, three jobs

They are layers, not duplicates — each catches something the others structurally cannot.

| limit | where | stops |
|---|---|---|
| goal constraints | while planning | actions being *considered* |
| the dispatch door | at the moment of acting | effects reaching the world |
| the purity bar | while answering | thinking that would *act* |

Two rules govern the door, both established by experiment before anything was built on them: **check
when the action happens, not when it is planned** (so a prohibition recorded later still blocks it),
and **commit the graph before going through** (once an effect leaves, no rollback reaches it — so a
rollback boundary must never span a dispatch).

## Honest limits

- **Planner:** depth-limited best-first, first solution wins. No cost model, no backtracking across a
  committed subgoal. Adequate for a handful of steps; not a general-purpose planner.
- **Copy cost:** a full copy per frame. Copy-on-write implements *exactly* these semantics more
  cheaply and is the known lever — deliberately not taken; measure first.
- **Type schemas constrain one argument at one call site**, so `stack(b, onto)` cannot declare that
  its arguments differ. The planner enforces that itself.
- **References reach any depth in a `type` block, one hop in a `goal` or `method` one** — refused
  loudly at intake rather than silently mishandled.
- **Episode compilation** generalises single-argument operations on one subject. Multi-argument
  replay is a real question about *analogy*, not a missing mechanism.
- **Search is tie-break nondeterministic:** the plan is invariant, the number of imagined states is
  not.
- **Termination and conflict arbitration** are both open. A runaway program raises at a step limit as
  an honest stand-in for the first.
- **No indexing** beyond the reverse index.
- **There is no notion of *find*.** The engine models acting and checking; an operation whose point
  is to yield a *referent* has no slot in either, which is why denotation — *the newest file*, *the
  three biggest* — cannot be said.

The full account is in **[docs/limits.md](docs/limits.md)**.

## Documentation

| where | what |
|---|---|
| [`docs/`](docs/README.md) | the reference documentation — concepts, planning, deliberation, memory, execution model, authoring, limits |
| [`book/`](https://ercasta.github.io/Universal-Graph-Machine/) | the tutorial, with pages that run the engine in your browser |
| `CHANGELOG.md` | what landed, in order |

## Prior art

Microfunctions over a graph, goal-directed planning, and structural typing are each well-trodden. The
claim here is narrower and specific: **the same representation for rules and for everything else**,
so that a rule can read another rule's body — which is what makes effects derivable rather than
declared, learning a rule that writes a rule, and safety a matter of inspecting a body before running
it.

The design is informed by classical planning (means–ends, Sussman's anomaly as a test), SHACL shapes
and Minsky's frames for schemas, feature-interaction analysis from telecoms, controlled natural
language as a *surface* rather than engine input, and the Spark separation between composing
transformations and materialising them.

## History

This engine supersedes an earlier one — a label-less attribute graph with a matching ISA,
demand-driven firmware, possibilistic bands, and a large controlled language — and an experimental
successor to it. Both, and their test suites, were retired and removed; they remain in git history.

The repoint that produced this one separated two ideas that had been welded together from the start.
The bet was always **content as data**: rules, goals, plans and explanations in one graph so anything
can be reasoned about. It was never **pattern matching as the execution model**. Essentially all of
the accidental complexity came from the weld. Separating them changed almost nothing about what the
system represents and almost everything about how it computes.

## Licence

MIT.
