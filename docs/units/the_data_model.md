# What a goal, a plan, and a hypothesis actually are — the data model in plain language

**Status: design, 2026-07-30. Written in prose deliberately, the same way `planning_meta_concepts_arc.md`
was, because this is the document someone should be able to read cold and come away understanding how the
system represents what it is thinking about.** Its analytical companion is `graph_data_model.md`, which
carries the same content as signature tables, a mechanical closure check, and the probe list; read that one
when you want to verify something, and this one when you want to understand it. Terms are explained where
they first appear rather than assumed.

---

## Why this document exists

For most of this project's life, the interesting questions have been about mechanism: what the engine can
execute, what has to be a primitive, what turns out to be ordinary content in disguise. That line of work
reached a fairly settled answer — the part of the system that genuinely has to be built into the machine is
small, and almost everything else is data that generic rules read. But settling that exposed a gap nobody
had filled. If goals, plans, procedures, questions and hypotheses are all *data*, then someone has to say
precisely what that data looks like. And nobody had. Each of these concepts had been described somewhere,
in passing, in the middle of a document about something else — goals in a table inside the goal-machinery
write-up, plan steps in the comments of a planning ruleset, hypotheses in the docstring of the supposition
function. Three different vocabularies, never brought together, never checked against each other.

This document brings them together. It describes what each concept is made of, what the system does to
them, and why the particular way they are built means they can be nested inside each other without limit.

---

## The one idea underneath everything: there are no special objects

The single most important thing to understand is that none of these concepts is a special kind of thing.
There is no goal object, no plan class, no hypothesis structure. There is one substrate — a graph, meaning
nodes connected by named edges, where nodes can also carry simple labelled values — and every concept in
this document is built out of exactly that, using nothing the substrate did not already have.

This is not an aesthetic preference. It is the property the whole system depends on. Because a goal is made
of ordinary nodes and edges, an ordinary rule can look at one. Because a plan is made of ordinary nodes and
edges, a goal can be *about* a plan. Because a hypothesis is made of ordinary nodes and edges, the system
can hypothesise about a plan for answering a question. If any one of these had been given its own special
representation — a Python object, a dedicated table, a structured value packed into a single field — then
everything that wanted to reason *about* it would have needed special handling too, and the special cases
would multiply until the system could only do the combinations somebody thought of in advance.

There is a second, related discipline that matters just as much and is easier to get wrong: **the parts of
a concept are always separate nodes joined by named edges, never values bundled together inside one node.**
A goal does not contain its satisfaction condition; it *points at* a node which is that condition. A plan
step does not contain a list of prerequisites; it has one edge per prerequisite, each pointing at a node.
The difference sounds pedantic and is not. A node at the end of an edge can be matched by a rule, walked
to, reasoned about, and pointed at by something else in turn. A value bundled inside another value can only
be unpacked by code that already knows the packing. Every time this project has kept the parts separate, the
composition it wanted later turned out to be free; the one general principle behind that is that a graph can
only compose along its edges.

---

## What a goal is

A goal is a node that points at a claim it wants to be true.

That is the whole of it, and its plainness is the point. The node itself carries no meaning — it is a
handle, something to attach things to and point at. The meaning lives entirely in the edge, labelled
`wants`, and in whatever the claim at the other end says. The claim is ordinary content, exactly the same
shape as any other fact the system holds. Nothing about it is marked as goal-flavoured, and this matters
more than it seems: it is why the same claim can be something the system *believes*, something it *wants*,
and something it is *asking about*, without three separate representations.

Goals resolve by getting a mark. When the claim a goal wants turns out to be true, a rule puts `achieved`
on the goal node. When the claim turns out false, a rule puts `diverged` on it. When a goal is given up on,
it gets `abandoned`. These are all *positive* marks, deliberately, and there is a specific failure this
guards against that was found the hard way. It would be tempting to say a goal is achieved when nothing is
outstanding — to read success off an absence. But an absence is trivially true before any work has started
at all: a goal that has not yet been broken into subgoals has no unfinished subgoals, and so would report
success the moment it was created, before doing anything. That defect was hit in practice and fixed by
requiring positive evidence — there must be something there, and it must have succeeded. The general lesson,
which recurs throughout this system, is that you can never trust an open-ended absence unless something
separately establishes that the thing is complete enough for the absence to mean anything.

Goals nest. A goal can raise other goals, joined by an edge labelled `raised`, and each of those is a goal
in exactly the sense just described, with its own condition and its own outcome. A parent's outcome then
depends on its children's, and because the children are ordinary goals, they can raise children of their
own to any depth. There is one piece of care needed here that is worth mentioning because it is easy to
miss: when a goal raises a subgoal, it must not raise the *same* subgoal twice as the system keeps running.
That requires the rule to be able to see what it itself concluded on a previous turn, which is not
automatic, and getting it wrong produces a visibly duplicated subgoal rather than a silent problem — which
is how it was caught.

Finally, and this turned out to be one of the more useful simplifications the project found: **a question is
a goal.** Not something like a goal — a goal, with no difference in representation. The only distinction is
what the wanted claim is about. An ordinary goal wants something to be true of the world; a question wants
something to be *known*. Both resolve through the same `achieved`/`diverged` marks, applied by the same
rules, which do not look at and do not care which kind they are handling. This was not assumed, it was
built and run, and no seam appeared.

---

## What a plan is

A plan is a set of steps, each of which is a node, related to each other and to the world by named edges.

A step points at what must be true before it can run — one edge per prerequisite, labelled `pre`. It points
at whatever must happen before it, labelled `before`. It may point at what it is expected to produce. And it
accumulates marks as it moves through its life: `chosen` when it has been selected for execution, `unmet`
for each prerequisite not yet satisfied, `waits_for` for each predecessor not yet finished, `ready` once
nothing is outstanding, `done` once it has run.

The mechanism connecting these is worth describing because it is the same trick used in several other
places. Rather than a step asking "am I ready?" and computing an answer, the system attaches a small
blocking marker for every specific reason the step *cannot* run — one per unsatisfied prerequisite, one per
unfinished predecessor. Each marker is removed the moment its particular reason clears. When the last
marker is gone, and only then, the step becomes ready. Readiness is therefore not a calculation anybody
performs; it is what remains when every obstruction has been individually removed. This makes it robust to
things happening in any order, which matters, because in a system where new information can arrive at any
time nothing can be assumed to happen in a fixed sequence.

Two things about plans have not been settled, and are worth being honest about. The first is that **a plan
is currently implicit**. There is no node that is "the plan" — there are only steps that happen to be marked
`chosen`. That works fine when there is one plan, and stops working the moment two candidate plans should be
compared before either is committed to, which is precisely the situation the system is meant to handle. The
second is that a plan and a procedure are almost the same thing, distinguished only by where they came from:
a procedure is a plan somebody wrote down in advance, a plan proper is one the system assembled itself. They
converge immediately — both produce steps marked `chosen`, and from that point on a single mechanism runs
them both. This is a genuinely good outcome, since it means the system does not need separate machinery for
following instructions and for figuring things out.

---

## What a hypothesis is

A hypothesis is a region of the graph in which things can be held true provisionally, without those things
being true anywhere else.

The system needs this constantly. Before committing to a plan, it should be able to ask what would happen
if the plan ran. Before acting, it should be able to ask what would follow if some uncertain thing turned
out to be the case. Doing this by making the assumption real, drawing conclusions, and then trying to undo
everything afterwards is the obvious approach and a bad one, because working out exactly what to undo is
the hard part and getting it slightly wrong corrupts everything downstream.

Instead, the assumption is placed inside a marked region, and everything concluded from it is marked as
belonging to that region too. Conclusions inside the region can be inspected freely, and they do not leak,
because anything looking at the system's actual beliefs simply does not look inside the region. Discarding
the hypothesis is then not an undo operation at all — it is dropping the region, and everything that only
ever existed inside it goes with it. Confirming a hypothesis is the reverse: the assumption is promoted out
of the region into the system's real beliefs.

There is one deliberate protection here that is easy to underrate. A rule that *acts on the world* — calls
a tool, sends something, changes something outside the system — cannot do so from inside a hypothesis. This
is enforced by the machinery rather than by rule authors remembering to check, which is the right place for
it, because a rule author who forgets would otherwise cause a real action to happen as a side effect of the
system merely wondering about something. This is checked by a test that exists specifically to guard it.

The gap here, and it is a real one, is that **a hypothesis's verdict is not currently something a rule can
see.** The system can entertain an assumption, reason inside it, and reach a conclusion about whether the
prediction held — but that conclusion comes back to the surrounding program rather than being recorded on
the hypothesis itself. So no rule can react to "that hypothesis was refuted." This is exactly the asymmetry
that goals do not have, since a goal's outcome is a mark on the goal that anything can read, and the fix is
almost certainly to do the same thing here.

---

## What the system does — the operations

Everything the system does to these structures is done by a generic rule: one rule, written once, that
matches a *shape* without knowing what the specific content means. A rule that turns a causal claim into a
plan step does not understand causation; it matches the shape a causal claim is written in and produces the
shape a plan step is written in. This distinction — between content the system *reads* and structure the
system *executes* — took a long time to name and turned out to explain several earlier findings that had
seemed unrelated.

There are roughly fifteen such operations, and describing them as a group is more useful than listing them,
because they fall into a small number of families.

**Some operations create goals.** Something arrives — a request from a user, a prerequisite that is not
satisfied, a concept flagged as needing real investigation rather than an assumption — and a rule responds
by minting a goal that wants the corresponding thing to be true. What is notable is how nearly identical
these rules are to each other despite their triggers having nothing in common. That was checked
deliberately: if a question and a command genuinely needed different machinery, the two rules would have had
to differ, and they turned out to differ only in which value they match. Once a goal exists, where it came
from has done its entire job and contributes nothing further.

**Some operations break goals down.** A goal becomes several subgoals; a procedure's written-down steps
become chosen steps; an ordering written by a person becomes the ordering the executor actually uses. These
are the operations that generate structure, and they are also, as it turns out, the ones that would build a
learned procedure — a point §7 returns to.

**Some operations move steps toward execution.** Blocking markers are attached and removed, readiness
emerges, and a ready step produces a *proposal to act* — not an action. That distinction is load-bearing.
A rule never performs an action directly; it mints a node that describes an action it would like performed,
and a single, separate, deliberately unintelligent dispatcher is the only thing in the entire system that
turns such a proposal into a real effect. Because there is exactly one such place, a check applied there
covers everything, which is very much not true of a check that each rule is supposed to remember.

**Some operations close things out.** A wanted claim settles true or false and the goal is marked achieved
or diverged. A step finishes but the world does not look the way it should, and a mismatch is recorded — as
an ordinary fact, notably, which further rules react to by reconsidering alternatives and trying again.
There is no error handling in the usual sense anywhere in this loop; failure is just more information, and
recovery is just more rules.

**One operation stops others.** A prohibition is not a mechanism — it is an ordinary recorded fact saying
that some particular thing must not be done, consulted as a condition by whatever rule would otherwise
proceed. It was verified that a prohibition recorded *before* a command arrives blocks that command, and
that the order of the two does not matter.

**And one operation writes rules.** The system can read authored content and produce, as ordinary data, a
description of a new rule, which a fixed piece of machinery then turns into something executable. This is
the reflexive edge, and it is the one that distinguishes this design from the long lineage of goal-driven
architectures it otherwise resembles. Goals, subgoals, procedures and tool calls are decades old; a system
in which a rule can write a rule, in the same representation as everything else, is the actual bet.

---

## Why this can nest without limit

The reason all this composes is simple enough to state in a sentence, and the simplicity is the point.

**Every operation reads structures built from this vocabulary, and produces structures built from this same
vocabulary.** Nothing any operation creates is outside the set of things operations know how to read.

That is a closure property, and it means depth is not a series of increasingly difficult cases to be tested
one at a time — it is the same case repeated. A procedure whose step is a question whose answer requires a
hypothesis about another procedure is not a fourth-level problem requiring fourth-level machinery. It is a
procedure, and a question, and a hypothesis, each already understood, arranged so that each one's parts
happen to be another. The reason a query about a procedure is not execution of that procedure is the same
closure seen from the other side: a procedure's steps are ordinary nodes, so reading them is ordinary
reading.

This was not left as an argument. Four specific combinations that had been worried about were built into a
single scenario and run — a procedure decomposing into ordered steps, the first of which was a question,
the second an action gated both on the question resolving and on no prohibition applying. With no
prohibition present, the procedure completed in the right order and not before. With one present, the
question still resolved on its own schedule, the action never ran, and the procedure honestly never claimed
success. Nothing had to be adjusted to make this work.

**What closure does not give**, and this should not be glossed over: it guarantees that deep structures are
well-formed, not that building them terminates, and not that they agree with each other. Some operations
are recursive by nature and could unfold indefinitely; the machinery for telling convergent recursion from
a runaway loop is known to be inadequate and is untouched. And when two lines of reasoning at depth conclude
incompatible things, the system detects the disagreement rather than letting one silently win — but it has
no declared way to *settle* it, so a detected conflict stays honestly unresolved. Both of these are real,
both are separate from composition, and neither is solved by anything in this document.

---

## A familiar shape: this is close to entity-component-systems

Raised in conversation, and worth recording because the fit is unusually good and the places it *stops*
fitting are informative rather than merely academic.

In the entity-component-system pattern, common in game engines, an entity is a bare identifier carrying no
meaning of its own. Data is attached to entities as components. Behaviour lives in systems, which are
stateless processors that ask for every entity carrying some particular combination of components and do
something to them. Crucially, systems do not call each other. A system communicates by writing a component
that some other system is watching for, and the two need know nothing about each other beyond the shared
convention of what that component means.

Almost every part of that description has already appeared in this document under a different name. The
bare entity is the node this document called a handle — a goal node carries no meaning, it exists to attach
things to. Components are the marks and the role edges: `chosen`, `ready`, `achieved`, `wants`. Systems are
the generic rules, which match a shape and act on everything carrying it without knowing what the content
means. And the communication discipline is not merely similar, it is a rule this project arrived at
independently and states almost word for word in the dispatcher's own documentation: a rule never calls a
tool, a tool never rewrites, and they couple only through nodes. The recovery machinery is the same idea
again — a step that fails does not raise anything or call a handler, it records a mismatch as an ordinary
fact, and whichever rules care about mismatches pick it up.

The watchdog case makes the fit concrete. A watchdog would be a rule that watches for some condition and,
on finding it, records a prohibition or raises a goal — never reaching into whatever it is guarding, never
being called by it, and remaining entirely ignorant of what else is running. That is exactly the shape the
prohibition machinery already has, and it is why a prohibition recorded before a command works identically
to one recorded after: neither party knows about the other, so there is no ordering for them to get wrong.

Four places the analogy breaks, in increasing order of interest:

**Components are usually flat; here everything is relational.** Classic entity-component-systems store
plain values in components and are famously awkward when one entity needs to point at another — relations
are a known weak spot that later designs have had to add deliberately. This system is relational from the
start, since its whole discipline is that parts are separate nodes joined by edges. So this is something
more like a graph-relational version of the pattern, and the relational part is not a bolt-on.

**There is no notion of provisional state.** A system in a game engine has one world, and everything in it
is the case. Hypotheses have no analogue: there is nowhere to hold something true tentatively and then
discard it cleanly.

**Systems cannot write systems.** A game engine's systems are authored in advance and fixed at runtime. The
reflexive edge — a rule producing, as ordinary data, the description of another rule — has no counterpart,
and it is the single thing this design is actually betting on. This deserves care, and the next section is
that care, because the obvious way to state the advantage overstates it.

**And the scheduler is fixed — which is precisely what this project says it must not be.** In an
entity-component-system, the order in which systems run each frame is authored, fixed, and the entire
reason the pattern is predictable. That is an algorithm, and running a fixed algorithm over the graph is
exactly the posture rejected here: the world does not cooperate, and which operation should run next is
supposed to be chosen, not scheduled in advance. So the analogy holds for everything except the part that
actually decides how well the system works.

That last divergence is worth pausing on, because a second, unrelated thought experiment reached the same
place. Asking whether this model could run on an ordinary graph database — a useful question, since a query
language is a much harsher test of a specification than prose is — showed that the matching, the effects,
and the negation all port more or less directly, and that what does *not* port is the control of when things
run and what happens when two conclusions disagree. Two quite different framings, arrived at from different
directions, both leave the same two things behind. That is a fairly strong hint about where this system's
real content lives: not in its matching, which is ordinary, but in its restrictions and its choices.

The first of those — choosing what runs next — is the subject of the next section. The second, arbitrating
between conclusions that disagree, is detected today but not resolved, and remains genuinely open.

---

## Stating the actual advantage narrowly enough to survive contact with the prior art

The natural way to state what makes this system different is that its rules are data rather than code —
that business logic lives in the graph rather than in Python. That is true, and it is the right
neighbourhood, but as stated it is not a distinguishing claim, and the observation that game engines are
not so different is exactly the reason why. Game AI has been doing rules-as-data for twenty years, and in
at least three forms that are uncomfortably close to parts of this document.

Goal-oriented action planning, which shipped in *F.E.A.R.* in 2005 and has been standard since, gives an
agent a goal, a set of actions each declaring its preconditions and its effects as data, and a planner that
searches for a sequence connecting the current state to the goal. That is very nearly the plan-step model
described above — preconditions, ordering, effects, replanning when the world diverges — and it was not
merely designed but shipped, in a commercial product, at scale. Behaviour trees are data-driven control
flow, authored in a visual editor by designers who write no code, serialised, hot-reloaded, and inspected
at runtime. Utility systems select among candidate actions by scoring them against considerations that are
themselves data, tuned without recompiling — which is a direct attack on the selection problem this
document's last section calls the missing piece. Blackboard architectures, older still, are the
communicate-only-through-shared-data discipline in its original form.

So "the rules are data" is not the differentiator, and claiming it as one would invite exactly the response
that someone solved this in 2005. The honest version is narrower and, being narrower, is actually
defensible:

**The rules are data in the same representation the system reasons over — so a rule can be reasoned about,
and a rule can write a rule.**

Every one of the game-AI examples keeps its behaviour data in a separate representation from the world
state the behaviour operates on. A behaviour tree is a tree, authored in an editor; the world is a
blackboard or a component store. A goal-oriented planner's action definitions are a static table; the
world state is a bitfield. The behaviour data is data *to the tools*, and code *to the running system* —
authored offline by a person, loaded, and thereafter fixed. Nothing in a behaviour tree can match against
a behaviour tree. Nothing in a planner's action table can add an entry to the action table, because
deciding what should be in it was the designer's job and the running system has no representation in which
that question could even be posed.

Here, a rule is written in the same node-and-edge vocabulary as everything the rules operate on. That single
fact is what makes the reflexive edge possible rather than special: a rule matching rule-shaped data is not
a new capability requiring a meta-layer, it is an ordinary rule matching ordinary structure, and the system
already has an ordinary rule that observes what tends to co-occur and writes a new rule from it. It is also
what makes the missing piece of the last section *small* rather than architectural — recording reasoning
steps in the same vocabulary as everything else means learning from them needs no new machinery, only the
node.

This is the same conclusion reached from a different direction elsewhere in this project: what is old here
is the goal-and-plan vocabulary, which the Soar and ACT-R lineage worked out decades ago and which game AI
then shipped commercially. What is not old is rules-as-data *in one uniform representation*, such that a
rule can mint another rule. Every framing this document has entertained — the graph database, the
entity-component pattern, game AI — converges on the same shape of answer: the ordinary parts are genuinely
ordinary and well-precedented, and the whole bet sits in one place. Which is a good position to be in, since
it means there is exactly one thing to be wrong about.

---

## The one thing genuinely missing

Everything above describes what the system reasons *about*. There is one conspicuous absence: **the system
keeps no record of its own reasoning steps.**

When a rule is applied, the only trace is whatever it produced. Nothing anywhere says *this operation was
applied, to this goal, at this moment, and this is what followed from it.* And this absence is exactly what
blocks the ambition that motivated writing all of this down.

The system is supposed to work by choosing, step by step, which operation to apply next — not by running a
fixed procedure, because the world does not cooperate with fixed procedures. Its effectiveness is therefore
determined by how well it chooses. But choosing requires candidates to choose *among*, and a candidate has
to be something you can point at. Since an operation's application is not a thing in the graph, there is
nothing to point at, and so nothing to prefer, rank, record, or reconsider. What happens instead is that
everything applicable simply happens — which is precisely the undirected behaviour this design set out to
replace. Notably, the machinery for preference-based choosing already exists and is used to choose between
plan *steps*. It is one level below where it is needed.

The same absence blocks three further things. Choosing non-greedily means looking ahead, which means
hypothesising about an operation before applying it — impossible if the application is not a thing. Learning
from what worked means recording a sequence of applications that closed a goal — impossible for the same
reason. And the destination, learned procedures, needs both.

That destination is worth stating precisely, because it is unusually clean. **If an operation's application
were a node, a learned procedure would need no new representation whatsoever.** A record of what the system
did is a sequence of application nodes. Turning that sequence into something reusable is decomposition and
ordering — two operations that already exist and are already built — applied to application nodes instead of
to ordinary steps. A learned procedure would simply be a procedure whose steps are reasoning operations
rather than actions, run by the same machinery that runs any other procedure. There is even direct
precedent: the system already has an ordinary rule that watches what tends to occur together and writes a
new rule from it, which is the same shape aimed at a different target.

So the whole ambition reduces to one missing kind of node, and to nothing else new. That is a strong enough
claim that it should be distrusted until it has actually been tried — which is what `graph_data_model.md`
§7's probes are for, and the second of them is the one that decides it.
