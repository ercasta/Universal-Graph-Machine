# Execution model

This page describes how the machine actually runs: the single outer loop that drives everything, the
instruction set that stored rules are written in, the interpreter state that makes a running program
inspectable, and the boundary between what the kernel may know and what it must not.

The organising principle is one sentence:

> There is a single outer control loop. Planning is not a separate execution loop — its control state
> is represented as data, and the outer loop always interleaves and ticks. No seams, no fixpoint
> procedures that cannot be interrupted.

The test that makes this checkable rather than a slogan: **can the executor be stopped between any
two primitive operations, and can the system say what it was doing?**

## One agenda, one tick

Every control loop in the engine is a **node plus a `step`**:

| task | one primitive step is |
|---|---|
| activation | one instruction |
| search | one imagined state |
| replay | one real action |
| pursuit | one step of plan, act, check, replan |
| forgetting | one swept record |

So the outer loop is an **ordered agenda** and a dispatch on the task's kind. Adding a kind of work
means writing its `step`, not touching the loop. A tick takes the task at the head of the agenda,
advances it by one step, and puts it back at the tail, so interleaving is not a policy the loop
implements but the ordinary consequence of the agenda being an ordered edge. Two goals pursued at
once really do interleave, one primitive step each, and *which one is next* is a question anybody can
ask of the graph.

### What must not become uniform: irreversibility

Advancing a search costs time; advancing a replay can send an email. That asymmetry is the single
most important safety property in the design, and a uniform cycle is exactly what would erode it. So
a tick **reports the verb it performed** — `imagine`, `look`, `act`, `run` — *before* taking it, and
a caller can stop before the first irreversible one.

Dispatch is not a seam to be removed. Once a handler is called the world is executing, not us. The
loop can decline to take the step; it cannot make the step reversible.

### What the loop does not do

It does not flatten the goal. A game loop *simulates*; this *pursues*. The unmet constraints of a
goal are the gradient, and they are the entire reason guidance works. The loop's shape governs what
may happen at a step; the goal still governs how the step is chosen.

## The instruction set

Rules are stored as programs. A program that is *data* can be inspected, generated, stored and
learned; a Python function is fast and readable but opaque, and an episode cannot be compiled into
one. Both coexist by one test: **Python for mechanism nothing reasons about; instructions for
anything that must be inspectable, generated, or learned.**

Three operand conventions. A bare Python value is a **literal**; `R("x")` reads a **register**;
`F("h")` reads the node a **focus head** points at. The third is what makes a program *pointed*: an
instruction names the head it acts on, never "whatever matches".

Control flow is by label — a bare string in the program is a jump target, not an instruction. The
full opcode list is in [reference/isa.md](reference/isa.md).

A machine carries a graph (mutated in place), registers, and a focus. It runs inside a savepoint, so
a failed or hypothetical run rewinds at a cost proportional to the changes made.

### The interpreter's state is graph data

The interpreter's main loop was once an ordinary Python `while` holding the program counter, the call
stack and the registers as locals. That made planning steppable while the rule *driving* the planning
ran inside an atomic invocation — steppability at the wrong level, one seam removed and an identical
one left below it.

Now an **activation record** lives in the graph, and `run` is a loop over `tick` and nothing else:

```
activation(pc, steps, stack, halted) ──focus──▶ focus ──head──▶ head ──at──▶ world
                                     ──register──▶ register(name, value)
                                     ──of──▶ function          (when the program is a stored one)
                                     ──caller──▶ activation    (so the call chain is readable)
```

Four things had to materialise, not three: the program counter, the call stack, the registers, and
the **focus** — which is as much interpreter state as the registers, and easy to miss because it
looks like a helper rather than a loop variable.

A register is a **node**, not an attribute of the activation. An attribute keyed by register name
would collide with the activation's own slots, and a program with a register called `pc` would
corrupt the interpreter. One node per register also gives a register a stable address, so something
can point at one. Its value is stored as an attribute rather than an edge, because a register holding
a node holds a *pointer*, and an edge would be a claim that the two are related.

There is exactly one implementation of a step. Keeping a fast Python loop "just for the hot path"
would mean two executors that are supposed to agree, which is the drift class this codebase keeps
re-finding, and it would drift silently. Slow and singular beats fast and forked.

Retirement is not the same as being uninterruptible: a finished activation is dropped along with its
registers, because a finished activation is not state anybody can be inside of.

## The kernel boundary

This is the **lower** of two lines, and conflating it with the other is easy enough to be worth
saying once. The kernel boundary separates the substrate from everything we decided; the *horizon*
([concepts.md](concepts.md)) separates the closed class of primitive forms from the web of authored
data above it. A port re-implements both layers below the horizon — a `goal` is something we
decided, so it is business, and it is still primitive. "Business" and "expressible in terms of
something else" are different questions.

Two principles were both right and collided. Search is a genuine primitive — there is no sequence of
`GET`/`SET`/`LINK` that imagines a state — so it earns a place beside dispatch. But the kernel may do
the **substrate** and must never do **business**, where business is anything we decided about how to
represent plans, time, goals, or criteria. The system has to be portable to another substrate by
re-implementing the kernel while the data carries over unchanged, and the kernel must never see the
representation above it.

The collision was concrete: the instruction set imported the planner so that two opcodes could call
it, which meant a port would have had to port the entire planner in order to implement two
instructions. The useful test is not *is this a loop?* but **would a port re-make a decision here?**

Both principles hold once a primitive stops having to be an opcode. A **native** is still primitive
and still uninterruptible where it must be; what changes is that the kernel reaches it by name
through a table it does not populate:

```
before:   isa  ──imports──▶  driver          (the kernel names the planner)
after:    isa  ──looks up──▶ native  ◀──registers──  driver
```

The table is substrate; its contents are not. The native module names nothing from the layer above —
no goal, no plan, no criterion — and a `register` call belongs in the module that owns the thing being
registered. A dictionary of names in the kernel would be the same leak with an extra hop.

Registration is an import side effect, so a native is callable only once its owner has been imported.
An unknown native therefore refuses by listing what *is* registered: the failure worth designing for
is a program reaching for a primitive whose module nobody loaded, and a bare "unknown native" is
indistinguishable from a typo.

Natives are deliberately not policed. Anything registered can do anything Python can, exactly as the
opcodes they replaced could. Policing becomes necessary when untrusted rule files are loaded, and
nothing does that yet.

## Dispatch — the one door to the world

Every effect goes through one function, so one check covers every tool that will ever be registered,
including tools written by code that never heard of prohibitions. A check each caller is supposed to
remember is not the same guarantee.

Two rules govern the door, both established by experiment before anything was built on them.

**Check at apply time, not at mint time.** A pending call is inert data until the dispatcher reaches
it, so a prohibition recorded *after* the call was planned still blocks it. This recovers the
order-independence that ambient matching used to give for free, and checking at creation time would
lose it.

**A rollback boundary must never span a dispatch.** The graph is committed *before* the handler runs.
Past that point the journal is worthless, and pretending otherwise would be worse than not having it.

A veto is ordinary data — a `forbidden` node pointing at a target blocks any dispatch naming it. The
dispatcher knows one reserved name and never interprets a value.

The door is also where imagined targets are refused, where an observation is recorded, and where the
moment of an action is minted. See [Planning and acting](planning.md) and [Memory and
time](memory.md).

## Selection

Under rule matching, dispatch was automatic: everything applicable fired. Under this model nothing
happens unless something chooses, so selection is not an optimisation — it *is* the control flow, at
the level below deliberation. Three stages, kept separate because conflating them is what made
matching hard to reason about:

1. **Candidates** — which functions could apply to a head, from their declared parameter types. This
   is matching in its demoted role: bounded, one node at a time, no fixpoint. It is restricted to
   single-parameter functions on purpose, because a multi-parameter function needs a *binding*
   proposed, and that is search; hiding search inside candidate generation would misplace it.
2. **Ranking** — a declared priority, plus one structural rule, plus an optional external scorer,
   which is where a language model plugs in, reading the function catalogue's natural-language docs.
3. **Applying** — invoke, and record the application, so the next round can see what happened.

**The structural rule that earned its place: a function is never applied twice to the same node.**
Under rules this needed a hand-authored consumption marker per rule, and forgetting one produced an
unbounded stream of repeated effects — the most persistent defect of the old design. Here it is one
check in one place, possible only because applications are recorded.

A refused application is data, not a crash: the outcome is stored and the loop continues.

Selection is greedy, deliberately and for now. Non-greedy choice informed by which subsequences work
well is the goal, and it needs the episode corpus this module produces, so it comes after rather than
with. The hooks are explicit: an external scorer, and recorded episodes.
