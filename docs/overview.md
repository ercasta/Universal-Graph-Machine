# Overview

The Universal Graph Machine is an agent that holds a world in a graph, takes goals, finds plans by
imagining them, carries them out, notices when reality disagrees, and answers questions with the
derivation that produced the answer. It is a self-contained Python library with no dependencies.

Two commitments shape everything else.

## One representation for everything

Facts, rules, goals, plans, hypotheses, memories, explanations, conflicts, the planner's own
frontier, and the interpreter's own program counter are all ordinary nodes and named edges in one
graph. Nothing is held in a Python data structure that the system cannot read.

This is not a claim about elegance. It is what the capabilities are made of. The planner works by
reading the stored instructions of the rules it might use, so effects are derived rather than
declared and cannot fall out of date with the body that produces them. Learning is a rule that
writes a rule, using the same storage as an authored one. Refusing to answer a question with a rule
that would act is inspecting that rule's body before running it. None of those needed a subsystem;
they needed the same substrate asked a different question.

The same commitment sets the limit on where a language model may sit. A model may write text at a
border that can refuse it. It may not reach past that border and write graph structure, because then
nothing could refuse it.

## A rule is a function you point at something

Nothing fires. A rule has parameters and runs when something calls it, on the arguments it was
given, and never otherwise.

```
# Put the lid on a jar.
fn seal(j: jar) -> sealed_jar:
    SET F(j) "sealed" true
```

There is no `when` clause, because the circumstances are the caller's business. `F(j)` reads a
*head* — the thing this rule was pointed at — and a callee receives a fresh set of heads holding
only its own arguments, never its caller's.

The trade is explicit. You lose automatic cascades, and you gain a rule that cannot fire twice by
accident, cannot be triggered by a fact you did not anticipate, and cannot interact with a rule
written by someone who never heard of it. The library grows without any global program needing
re-verification. In exchange, something must decide what to do next, and that decision becomes the
whole of the system's control flow — which is why [deliberation](deliberation.md) is a substantial
part of the engine rather than a scheduling detail.

## Types are shapes, so change needs no representation

A type is a schema over a subgraph — structure and attributes — checked by looking at the node,
never by consulting a tag. So `seal(j: jar) -> sealed_jar` is a **cast**, and whatever it changes is
merely how the cast is achieved. Nothing records that a mutation happened, because a node either
satisfies the stronger shape now or it does not.

Precondition and effect collapse into parameter type and return type. Multi-type membership and
de-recognition fall out rather than needing mechanism.

## A first example

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

`carry_out` planned by imagining, ran the plan against the real world, and checked that the goal
actually closed. Asking the same world a question uses the same search:

```python
I.respond(g, "ask is the salt sealed?:\n    salt.sealed = true", th)
# YES - already known
```

Asked *before* anything sealed the salt, the answer would have been derived instead, and the plan
found would have been the proof:

```
YES - derived in 1 step(s) (1 step(s) considered)
yes, because:
  seal(j=salt)
```

## What the system does

**Goals and plans.** A goal is a set of constraint nodes. Which constraints are still false is what
turns search from generate-and-test into means–ends. Steps are imagined on a private copy of the
world, one frame per step; when a frame satisfies the goal, the path to that frame already is a
replayable plan. See [Planning and acting](planning.md).

**Questions.** "Is Paul mortal?" is the goal *find out whether Paul is mortal*. There is no second
control loop and no query evaluator — the same search runs, and the plan it finds is the proof.
Three verdicts, and the third is not a failure: `yes`, `no` (something incompatible holds now), and
`unknown`. A failed search has learned about its own library, not about the world.

**Explanations that refuse to be invented.** For a fact that already holds with no recorded history,
a fresh search would happily produce "here is a way this could follow". That is a fine answer to a
different question and a lie as an account of history, so the machine says it does not know. An
engine that manufactures plausible history makes every explanation untrustworthy.

**Divergence and recovery.** Expectations are derived from the two frames the workbench already
holds, never authored and never stored, and they are qualitative rather than quantitative. On
divergence the machine stops at that step and does not roll back — real effects have already left.
It then either resumes onto a branch that assumed what actually happened, or replans from the world
as it now is.

**Memory, learning, conflict.** The thread records attention shifts and applications in order, each
carrying why it followed the last, as ordinary graph data a rule can walk. Compiling an episode
produces a new rule indistinguishable from an authored one. Interference — two independently
authored rules writing one slot for different goals — is distinguished from a deliberate sequel.

**Deliberation.** Guidelines reorder, methods decompose, criteria name the move to make, directives
refuse when they cannot act, and norms can be defeated by a higher authority. All of it is authored
data rather than Python, and all of it is inspectable.

## Three limits, three jobs

They are layers, not duplicates. Each catches something the others structurally cannot.

| limit | where it applies | what it stops |
|---|---|---|
| goal constraints | while planning | actions being *considered* |
| the dispatch door | at the moment of acting | effects reaching the world |
| the purity bar | while answering | thinking that would *act* |

Two rules govern the door, both established by experiment before anything was built on them: check
when the action happens rather than when it was planned, so a prohibition recorded later still
blocks it; and commit the graph before going through, because once an effect has left no rollback
reaches it — a rollback boundary must never span a dispatch.

## Prior art, and the narrow claim

Microfunctions over a graph, goal-directed planning, and structural typing are each well-trodden.
Type schemas sit where SHACL shapes and Minsky's frames sit. Planning draws on classical means–ends
analysis, with Sussman's anomaly used as a test. The separation between composing transformations
and materialising them is the one Spark makes. The argument for a library that grows without global
re-verification comes from feature-interaction analysis in telecoms. Controlled natural language is
used as a *surface*, never as engine input.

The claim specific to this system is narrower: **the same representation for rules and for
everything else**, so a rule can read another rule's body. That is what makes effects derivable
rather than declared, learning a rule that writes a rule, and safety a matter of inspecting a body
before running it.

## History

This engine supersedes an earlier one — a label-less attribute graph with a matching ISA,
demand-driven firmware, possibilistic bands and a large controlled language — and an experimental
successor to it. Both were retired and removed; they remain in git history.

The repoint that produced the current system separated two ideas that had been welded together from
the start. The bet was always *content as data*: rules, goals, plans and explanations in one graph so
anything can be reasoned about. It was never *pattern matching as the execution model*. Essentially
all of the accidental complexity came from the weld. Separating them changed almost nothing about
what the system represents and almost everything about how it computes.
