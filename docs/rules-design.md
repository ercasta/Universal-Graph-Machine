# Rules — a design

This document specifies how an agent represents rules, states, claims and uncertainty on a single
graph substrate, and what the engine that runs them must provide. It is self-contained: every term it
uses is defined here, and every decision is argued from the requirements stated in §1 rather than
from precedent.

**It is organised around one claim.** Almost nothing in this design is part of the engine. Moments,
entries, signs, spans, rules, grades, channels, frames, goals and plans are a **representation of
reality that the agent uses**, not machinery the engine is built out of. They are open class. An agent
that has them reasons better than one that treats every proposition as a bare fact — it can say what it
used to believe, what it is merely supposing, and on whose word — and that superiority is a matter of
what it was *taught*, not of what it is *made of*. One could teach a person to think this way without
changing the chemistry of their brain.

So the document has four parts:

* **Part I — the floor.** What genuinely cannot be a convention, and the test that decides.
* **Part II — the internal representation of reality.** The bundle: moments, entries, signs, and the
  read. This is the part you would teach first.
* **Part III — what the representation allows.** Everything else, grouped by what it is *for*, each
  scored as a joint property of substrate and convention.
* **Part IV — gates and open questions.**

Earlier drafts placed most of Part II and all of Part III inside the engine. That was a mistake with a
recognisable shape: treating an open-class concept as closed creates an island that no rule can reach,
and the design already caught one instance of it (§12's *achievability is not a mark*) without
generalising. This draft generalises it.

## Contents

**Part I — The floor**

- [1. Requirements](#1-requirements)
- [2. Evaluation criteria](#2-evaluation-criteria)
- [3. The substrate](#3-the-substrate)
- [4. The floor](#4-the-floor)
- [5. The test](#5-the-test)
- [6. The bootstrap](#6-the-bootstrap)

**Part II — The internal representation of reality**

- [7. Moments](#7-moments)
- [8. Propositions and entries](#8-propositions-and-entries)
- [9. Signs](#9-signs)
- [10. The read](#10-the-read)

**Part III — What the representation allows**

- [11. Spans](#11-spans)
- [12. Rules](#12-rules)
- [13. Shapes](#13-shapes)
- [14. Connectives](#14-connectives)
- [15. Time](#15-time)
- [16. Modality](#16-modality)
- [17. Provenance — channels, frames and the gate](#17-provenance--channels-frames-and-the-gate)
- [18. The machinery's own state](#18-the-machinerys-own-state)
- [19. Recall](#19-recall)

**Part IV — Gates and open questions**

- [20. Acceptance](#20-acceptance)
- [21. What this design does not settle](#21-what-this-design-does-not-settle)
- [Appendix A. Glossary](#appendix-a-glossary)
- [Appendix B. Alternatives considered](#appendix-b-alternatives-considered)
- [Appendix C. The name census](#appendix-c-the-name-census)

Concepts are introduced in dependency order: no section relies on a construct defined below it,
except that §7 forward-references *entries*, whose definition is §8.

---

# Part I — The floor

---

## 1. Requirements

The system is an agent that plans, acts, observes and explains itself. Rules are how it knows what
follows from what. Seven requirements shape everything below. They are cited by number throughout,
and glossed at each citation, because a bare `R4` is unreadable at a distance.

**R1 — Two readings of one statement.** Planning reads a rule **backwards** (*what would make this
goal true?*); execution reads it **forwards** (*what follows from this state?*). Both readings must
come from the same statement. Two statements, one per direction, would drift apart with no way to
detect the disagreement, because neither is the premise of the other.

**R2 — The reading must be recoverable.** Reading a rule backwards is reading its converse. *Four
wheels ⇒ car*, run backwards, licenses *a cart is a car*. That is legitimate as a hypothesis and
catastrophic if a planner treats it as entailment, so the representation must record which kind of
step a given inference was.

**R3 — Rules are subjects.** *A rule the boss gave beats one the vice gave* requires a rule to be a
thing other facts can be about. So must *this rule is about assembly*, *this rule takes four to seven
minutes*, *this rule does not apply at altitude*.

**R4 — Rules are askable, not merely runnable.** *Which rules are about time? Which disturb position?
Which come from the boss?* must be ordinary queries. A rule whose content is a program is data you
can run but cannot ask about, so those questions become impossible.

**R5 — Every conclusion carries its support.** The agent must be able to answer *why do you believe
that, and on whose word?* The trace a piece of reasoning leaves behind is not a debugging aid; §16
makes it load-bearing for correctness.

**R6 — Partial knowledge must be sayable.** *Pouring raises the level, by an unknown amount* must be
expressible as such. A representation in which the only options are *states a value* and *says
nothing* forces the agent to claim precision it does not have, or silence that means the wrong thing.

**R7 — The agent's own state is in the world it reasons about.** Expectations, commitments and
in-progress procedures must be facts on the graph, not variables in an interpreter. Otherwise the
agent cannot notice that an expectation failed, cannot be asked why it abandoned a plan, and cannot
have a strategy overridden by a statement in its knowledge base.

R7 is the one that does the most work in this draft. Taken seriously it does not stop at expectations
and commitments: it reaches the representation of belief itself. If *what I believe*, *when I came to
believe it* and *how strongly* were engine-level, the agent's own epistemic state would be the one
thing it could not reason about.

---

## 2. Evaluation criteria

Every representation decision below is scored against four criteria, in a table, before the decision
is taken. The cost is written down even when the choice is obvious.

| criterion | the question |
|---|---|
| **not leaking** | Can this shape state something the author did not intend? *Scoped to the shape alone — see below.* |
| **not lossy** | Is everything the author knew recoverable from what was stored — including what they *didn't* know? |
| **readable** | Can the obvious questions about this be asked as ordinary queries, without a special mechanism? |
| **composable** | Do two independently authored instances of this combine without either being rewritten? |

The most common leak has an innocent shape: a two-hop path through a shared node, which no one
authored and which nothing forbids reading as a claim.

**Leaking is a property of the shape alone.** A reader that drops part of a shape and concludes too
much is not a leak; the unauthored claim is in the reader, not in the graph. That failure is real, but
it is a question about the machinery — *why did the machinery return part of a structure?* — and the
machinery has a small number of places where it can be asked: **match**, which is what returns
entries; **write**, which is what deposits them; and **quiescence**, which decides that an application
would change nothing (§5). A criterion that charged shapes for reader behaviour would score the same
shape differently depending on who read it, which is not a property of a representation.

The third was found by building rather than by argument, and it is the one to watch: match returning
nothing and write refusing are both observable, while *this would change nothing* is silent by
construction.

### The criteria score a pair, not a shape

This is the correction that reorganises the document. A shape does not leak or fail to leak on its
own; it does so **given the conventions in force**. `moment(delta, predecessor, licence)` is leakless
because there is a convention about what a delta is and a discipline about who writes one. Change the
convention and the same three-member node scores differently.

> **Leaklessness, losslessness, readability and composability are joint properties of the substrate
> and the convention layered on it.**

Two consequences run through the rest of the document.

**Every scoring table in Part III scores a convention**, not the substrate. They are therefore
arguments, open to a better convention, rather than axioms. Part I's tables are the only ones scoring
something that cannot be replaced.

**When the design hits a wall, the first question is which of the two is at fault.** The default
answer must be *the convention*, because a convention is cheap to replace and a substrate provision is
permanent. Reaching for a new engine feature to rescue a convention is how islands are made: the
feature can manipulate the convention and nothing else can, so the convention stops being data.

---

## 3. The substrate

The design assumes only this much:

* There are **nodes** and **directed edges**. Edges carry no information beyond connecting.
* A node may have **ordered members**: an edge to a target at a known position.
* Nothing else. In particular, edges have no labels, no attributes and no truth values; anything you
  want to say about a connection must be a node.

A **relation instance** — what would elsewhere be a labelled edge — is therefore a node with a
relation and ordered members:

```
on(a, b)        a node whose members are, in order, a and b
```

This is why the rest of the design can attach facts to anything: rules, claims, moments and time
spans are all nodes, so all of them can be spoken about without introducing a new kind of thing.

### Ordering is reducible, and provided anyway

Earlier drafts claimed *ordering is the one thing that is not itself structure*. That is too strong,
and correcting it matters because it is the claim that made the floor look inevitable rather than
chosen.

Ordered members can be encoded with unordered edges alone, using the same V-shape the rest of the
design uses to keep a path from being followed without a rule:

```
n  → s1, s2, r          the relation instance
s1 → pos_1, a           a slot: which position, and what sits in it
s2 → pos_2, b
r  → rel_marker, on
```

*Member at position 1 of `n`* becomes: find `x` with `n → x` and `x → pos_1`, and take `x`'s other
target. One node and three edges become three nodes and seven, and the reader must know `pos_1` is a
position marker — so the closed class does not disappear, it relocates.

This works. It is what RDF does. What it costs falls on the one thing that genuinely cannot be
replaced:

> **With ordered members, matching a pattern is linear in the pattern. With unordered edges, matching
> is subgraph isomorphism.**

Ordering *fixes the correspondence* between the parts of a pattern and the parts of a target. Remove
it and unification must search over which edge answers to which — the same problem, and NP-complete in
general. So the substrate provides ordering not because it could not be otherwise, but because its
absence makes §4's irreducible primitive combinatorially harder on every match, forever.

§4 states the three different grounds on which something reaches the floor, of which this is one.

---

## 4. The floor

The floor is what remains when everything teachable has been removed. It is short, and — this is the
test of whether it has been drawn correctly — **nothing on it mentions reality**. No item below says
anything about time, belief, evidence, causation or the world. They are about how structure is built,
matched and committed.

### 1. Structure and ordering

§3, in full. Nodes, ordered members, nothing else. This is the medium, and no convention can supply
it because every convention is written in it.

### 2. Variables and substitution

A node may be **generic**: it contains variables. Given a generic node and an anchored one, there is
an operation that finds a substitution making the first identical to the second, or reports that none
exists. Applying a substitution to a generic node yields a node.

This is the one item that provably cannot be a convention, and the reason is self-reference:

> **You cannot define matching-with-variables using rules that themselves require
> matching-with-variables.**

Everything else that felt like floor in earlier drafts was floor by association with this. A rule is a
rule *because* it is generic; a pattern is a pattern *because* something substitutes into it. Remove
this and there is no rule layer to write conventions in.

**What match means, stated once.** Two nodes match under a substitution σ when applying σ to the
generic one yields the anchored one, position by position, relation included. That is *structural*
unification and nothing more. It has no opinion about entries, loci, signs or chains — those enter
only because the **program** that reads a chain (§10) is written in terms of them, and that program is
a convention.

The distinction matters because §2 charges leaks to `match`. What match returns is a substitution over
structure. Whether it returned *part of* a claim is a question about the program that called it, and
the program is data.

### 3. A register

Writes land somewhere, and something must point at where. One pointer: the node the machinery is
currently working in.

The register is floor. **That it points at a moment is convention.** Nothing in the engine knows what
kind of node it holds; §17 is what decides to put a frame there, and §7 is what decides that a frame's
seat is a moment.

**One register, many suspended positions.** A process that is not running still has a place it was
standing, and resuming it restores that place. Those saved positions are *not* registers — they are
ordinary members of ordinary frame nodes (§17), readable, writable and attributable like anything
else. Resuming is a write to the register, sourced from a frame; suspending is the same write in the
other direction, and both leave a trail.

The distinction is exactly §17's *entering is writing*. If saved positions were registers, the design
would have an unbounded set of privileged slots and R7 would fail for the machinery's own control
state — the agent could not be asked where a suspended process was standing, or move it. What must be
privileged is only **which one is current**, because that is the question no read can answer: finding
the answer in the graph would require a read, and a read needs somewhere to stand.

That circularity is not incidental. It is the same one §6 addresses for the read itself, and it is why
the register is floor by irreducibility rather than by economy.

### 4. A stamp on every mint

Every node the engine creates records what produced it: which rule, under which substitution, with the
register in which state.

This is a property of the write operation, not a vocabulary item — it introduces no name and says
nothing about channels, authority or evidence. It is on the floor because the alternative is
voluntary provenance, and voluntary provenance is forgeable. §16 makes the support trail load-bearing
for *correctness* rather than for explanation, and that argument fails outright if a write can decline
to be stamped.

> **Nothing is prohibited; everything is stamped.**

### 5. One total step

Something must always answer. Selection cannot be allowed to search forever or to return nothing,
because the interpreter has no outside to fall back to.

Totality is floor. **The table it consults is convention** — an authored precedence relation over
rules, which §18 and §19 depend on being ordinary data. The floor requires only that a bottom-most
selector exists, is a lookup rather than a search, and always returns.

### Three grounds, not one

The five items do not reach the floor for the same reason, and flattening them into one list flatters
the floor by making all of it look inevitable. Only two are irreducible in the strong sense.

| item | ground | the argument |
|---|---|---|
| **variables + substitution** | **irreducible** | defining matching requires matching |
| **one total step** | **irreducible** | selecting the selector requires selection |
| **the register** | **irreducible** | finding where to write requires a read, and a read requires somewhere to stand |
| **the stamp** | **by guarantee** | fully reducible — a rule could write its own provenance. But reducible provenance is forgeable provenance, and §16's soundness argument dies. |
| **ordering** | **by economy** | fully reducible (§3), and its reduction turns linear matching into subgraph isomorphism |

The three irreducible items share a shape: each is the thing that would be needed *in order to do the
thing itself*. That is worth naming, because it is also the shape of §6's bootstrap and of §18's
arbitration regress, and all of them take the same escape — **a function, not a search.**

The two others are choices, and should be defended as choices. The stamp could be given up, at the
price of soundness. Ordering could be given up, at the price of complexity. Nothing else on this list
could be given up at any price.

### Descent is grammaticalization, and should be measured

Ordering reaching the floor by economy is the linguistic process exactly: an open-class item, used
constantly, bleached of content, becomes closed-class structure. Ordering has every diagnostic —
**semantic bleaching** (*the second member* means nothing in particular), **frequency** (every relation
instance), **obligatoriness** (you cannot write `on(a, b)` without committing to which is which),
**reduction** (seven nodes to one index), and a **closed paradigm** (positions are not freely coinable).

The framing is not decorative. Closed-class elements *structure* the content that open-class elements
*provide*, and that is Part I against Parts II–III, restated in someone else's vocabulary.

Where the analogy bites is the disanalogy. In language, grammaticalization is **diachronic** — it
happens through use and nobody decides it. In earlier drafts of this document it happened in one
sitting, which is how moments, entries, signs, connectives and goals all ended up on the floor with no
evidence behind them. So:

> **A convention descends to the floor only by measured use: high frequency, on the path of an
> irreducible primitive, and bleached of domain content.**

All three are checkable. Frequency is countable, and this design has counted before — a census of
what the corpus actually writes has previously overturned the expectation it was run to confirm. The
prediction here is that **none** of Appendix C's nineteen conventions qualifies, because none of them
sits on the matching path the way ordering does.

The reason for the bar being high is that grammaticalization is **irreversible in practice**. Once
something is closed class it is no longer freely coinable, and every use of it must route through
machinery that knows its name — which is the island of §2, arrived at by drift rather than by
decision.

### That is the whole floor

```
structure + ordering        §3 — by economy
variables + substitution    irreducible
a register                  irreducible
a stamp on every mint       by guarantee
one total step              irreducible
```

Earlier drafts named **four primitives** — recall, match, write, arbitrate. Against this list they
decompose unevenly, and the unevenness is informative:

| earlier primitive | verdict |
|---|---|
| **match** | floor — item 2 |
| **write** | floor — items 3 and 4 (a register to write into, a stamp on the result) |
| **arbitrate** | *totality* is floor — item 5. *Precedence* is authored data, and therefore convention. |
| **recall** | **entirely convention.** Which rules come to mind is an index plus a policy; §19 argues it should be learned, and a learned proposer is the opposite of a primitive. |

So one of the four was never a primitive at all. It survives as §19, which is where it belongs: it is
the most consequential *policy* in the design, and calling it a primitive obscured that it is a
choice.

### Primitive is not native

The reason moments, entries and signs feel like floor is that they sit on the hot path of every read,
so an implementation puts them in native code. That is an optimisation and not a status, and the
difference is checkable rather than rhetorical:

> **For every bundled convention, the rule-level definition must exist, and the compiled path must
> agree with it on answers *and on behaviour*.**

The second clause is not decoration, and an earlier wording that said *identical answers, only
slower* was wrong in a way this design cannot afford. **A convention compiled into the host language
is not interruptible.** §18 spends its length arguing that a procedure written as control flow owns
the agent until it returns, and that this — not speed — is the reason procedures must be data. The
same argument applies one level down, to the bundle, and earlier drafts did not apply it there.

An automatic thought is fast, unexamined, and effective right up to the point where it is wrong; what
makes it changeable is being able to slow it down and look at it. That is the property being
protected, and it names three states rather than two:

| | fast | inspectable | interruptible |
|---|---|---|---|
| **floor** | — | n/a | n/a |
| **convention, interpreted** | no | yes | yes |
| **convention, compiled** | yes | no | **only at rule boundaries** |

> **Nothing may exist only in the third state.**

### Compile rules, not control flow

The third column is what decides how compilation may be done. Compile a whole chain walk into one
host-language function and preemption is gone — nothing can surprise the agent mid-read. Compile each
**rule's matching** into a fast closure and leave the selection loop interpreted, and every preemption
point survives while nearly all the speed is captured, because the cost is in matching and not in the
loop.

> **Compile rules, not control flow.**

This is §18's *procedures are data that bias selection, never control flow that owns the loop*, one
level down. It also convicts the current implementation from a second direction: Appendix C's five
interpreter phases **are** compiled control flow. The phases are the uninterruptible part; native
matching would have been fine. Nineteen conventions with engine branches, and a bundle that cannot be
interrupted, are one defect seen from two sides.

§21 sketches the further step this suggests — deriving the compiled path from the rules rather than
writing it by hand, and letting frequency and surprise decide what is compiled — and marks it as
unbuilt.

### Two optimisations, and the second is the larger one

Compilation is not the only way a chain of reasoning becomes fast, and it is not the more powerful
way. The other is **composition**: collapsing a derivation into a single rule. Having derived `e` from
`a` by way of `b`, `c` and `d`, mint the rule `a → e` and use it directly next time.

The two are easily conflated and behave oppositely:

| | **compilation** | **composition** |
|---|---|---|
| what it produces | a host-language artifact | **a rule — an ordinary node** |
| what it reduces | the cost of one step | **the number of steps** |
| the gain | a constant factor | algorithmic; a search that was exponential in depth can become a lookup |
| inspectable | no | yes |
| interruptible | at rule boundaries | it *is* a rule boundary |
| defeasible | no | yes — `overrides` and `unless` apply |
| where it lives | outside the graph | in the graph |

> **Compilation makes a step cheaper. Composition makes the step unnecessary.**

The decisive difference is the second row from the bottom. **A composed rule violates nothing in Part
I**: it is data, askable under R4 (*rules are askable*), attributable under R3 (*rules are subjects*),
defeasible like any other rule, and it carries a licence naming the rules it collapses — so R5's trail
is recoverable one hop deeper rather than lost. Compilation needs the three-states rule above to keep
it honest. Composition needs no such protection, because the artifact never leaves the language.

This is Soar's chunking and explanation-based learning; what this design adds is that the chunk is a
first-class node, so everything already true of rules is true of it.

What composition costs is not structural but epistemic, and §21 states it: intermediate conclusions
stop being deposited, so nothing can be surprised inside a shortcut; guard conditions must be
inherited or the shortcut fires where the reasoning would not; and the composed grade is a cache of a
derived value, which is §16's own objection arriving one level up.

### Why the bundle ships at all

This gives the conventions their proper home: a bundled knowledge base that ships with the engine, is
inspectable by ordinary queries, and can be replaced. An agent with a better internal representation
of reality is only possible if the representation is something you can hand it.

The bundle is not optional in practice. An engine that shipped with the floor alone would be correct
and useless — every corpus would have to re-derive belief, time and evidence, and no two would agree.
Bundling is how the design ships an opinion without freezing it.

---

## 5. The test

> **A name is engine-level only if match and write cannot be defined without it. Everything else is a
> convention, and the machinery that uses it must be expressible as rules.**

Applied to the vocabulary an implementation actually reserves, the test convicts nearly all of it.
Appendix C is the census; the summary is that of twenty-two reserved names, three survive, and the
nineteen failures each have an interpreter branch behind them.

That gives the test a falsifiable consequence, which is the point of stating it:

> **The interpreter's step should have no phases.** Match, commit, write — and intake, supposition,
> acting, deviation and goal expansion become rules that those apply.

An interpreter with one phase per convention has, in effect, compiled the bundle into itself. The
count of phases is therefore a direct measure of how much of the bundle has escaped onto the floor,
and it is a number an implementation can print.

### What the test does not license

The test is about **naming**, not about speed. Native implementations of bundled conventions are
expected and encouraged; the requirement is §4's agreement gate, not abolition.

Nor does it license removing conventions the agent needs. *Convention* is not *optional*. Signs,
loci and grades are as necessary to good reasoning as they ever were. What changes is their status:
they are claims about how to represent reality well, defended in Part II and Part III, and defeasible
in the way any claim is.

### A rule can name a rule; a rule cannot match one

One consequence of item 2 being floor deserves stating early, because it is a wall reached from three
directions and it constrains everything in Part III.

Rules can be **reified** — written as ordinary facts, with a relation naming the connective and
members naming the two sides. Once reified, a rule can be spoken about freely. What a rule cannot do
is *apply* match to another rule's pattern:

```
con(<boil>, boiling(?w), +)     what reification stores: the rule's PATTERN, generic
+goal(boiling(kettle))          what a goal is: ground
```

A rule that tried to relate these needs one variable to be both the generic pattern and the ground
goal. Deciding that the two *correspond* is exactly match — and match is floor, so no rule can call
it.

**Four** separate ambitions hit this same wall: lifting a modality across a rule (§16), reading a rule
backwards (§12), asking whether a generic subgoal is already satisfied (§18), and **composing two
rules** (§19) — which needs one rule's consequent unified against another's antecedent, both of them
stored patterns.

Four independent capabilities blocked by one missing operation is the strongest argument in this
document for resolving it.

### The repair is a request, and measuring it says what the request must return

`python -m ugm.backward` runs backward reading twice over one corpus — once as the interpreter phase,
once as two ordinary rules over a match **request** — and they reach the same seven goals.

The design of the request is the finding, and it is not the obvious one. The natural shape is *ask
whether this pattern matches, and be given the binding*. That cannot work, and the reason is not an
implementation detail:

> **A binding is a map from variables to nodes, and a rule cannot hold one — let alone apply one,
> because applying is substitution, and substitution is floor (§4 item 2).**

So the answer has to arrive **already instantiated**:

```
+fit(<R>, goal)                  the request: could this rule produce this?
+fits(<R>, goal)                 it could
+need(<R>, goal, <subgoal>)      one per antecedent member, substituted
+unfit(<R>, goal)                it could not
```

which gives the general statement:

> **Match and substitute travel together, because the caller cannot do the second half.**

That settles the fifth-primitive question against itself. A primitive a rule invokes would hand back a
binding the rule cannot use, so it would not help; and the moment the answer is instantiated, the
service is doing the substitution too, which is a request and not a primitive. **The floor stays at
five.**

Two rules then carry the whole of backward reading's core step:

```
<ask-fit>  implies( {+goal(?w), +rule(?r)},              {+fit(?r, ?w)} )
<expand>   implies( {+fits(?r, ?w), +need(?r, ?w, ?s)},  {+goal(?s)} )
```

Neither was writable before the use/mention repair above: the first concludes about a rule node, which
contains variables. And asking *every* rule is what recall exists to narrow (§19) — doing it
exhaustively is the deliberate-reasoning setting, not a shortcut.

**Satisfaction is a second request, not the same one pointed elsewhere.** *Is this goal already met*
must be computed **inside the plan's bindings**, or `tap(?t)` is met by `sink`, `under(kettle, ?t)` by
`drain`, and the plan is wrong with nothing saying so (§18). So there are two services —

```
+fit(<R>, goal)        could this rule produce it?          → fits / need / unfit
+check(<plan>, goal)   does the world already answer it?    → achieved + binds / unmet
```

— and with them, **five rules** reproduce the phase entire: ask-fit, plan, expand, ask-check, and
nothing else. Plans need no minting: `plan(?r, ?w)` is built by substitution into a consequent, and
substitution interns, so the same rule expanding the same goal names the same plan — which is what a
plan is.

### Two things the last phase taught

**`blocked` is not a fact, and no rule can conclude it.** The natural rule —
`implies({+goal(?w), +unfit(?r, ?w)}, {+blocked(?w)})` — fires when **some** rule does not fit, and
what `blocked` claims is that **no** rule does. That is an aggregate over a *finished* search.
Positive rules cannot say it, and §9's `−` does not help: *an entry says this does not hold* and *no
entry* are neither of them *for no `?r`*.

This is §13's and §19's discipline arriving at the last phase rather than a missing feature:

> **Bounded expansion returns a result and a state. `blocked` is the state.**

A state is what a searcher reports about *itself* when it stops, and nothing that stopped is a fact
about the world. So this one verdict stays with whatever runs the search.

**The phase starves forward reasoning, and that is a precedence claim frozen in control flow.** It
runs before recall/match/arbitrate and returns early, so while any goal is unexpanded no ordinary rule
can apply. Measured: a goal that *is* satisfiable — `water(kettle)`, derivable forwards from the same
corpus — reads as unsatisfied, because the phase never let anything derive it. The rule-level reader
interleaves, being ordinary rules, and finds it.

That is intake's finding and supposition's finding at once: **a phase does not merely hold a
convention, it asserts a precedence, and it asserts it where nothing can argue.**

### Use and mention, and where the refusal actually happens

Reification forces a distinction the design would otherwise not need. `+con(<R>, boiling(?w), +)` is a
**ground** claim about a rule that happens to name a node containing variables. It is not a generic
claim, and refusing it would make rules unspeakable-about — but structurally the two are identical, so
nothing in the shape can tell them apart.

Earlier drafts settled it by **who is writing**: the machinery reifying a rule mentions, a rule's
consequent uses. That is too strong, and building it is how the gap showed. A rule whose antecedent
matches `+con(?r, ?pat, +)` binds `?pat` to a stored pattern, so anything it concludes about `?pat` is
a rule's consequent *mentioning*. Under the authorship rule that write is refused, and rules cannot
reason about rules at all — which R3 requires them to.

What tells them apart is inheritance rather than authorship:

> **Mention propagates through bindings. A conclusion drawn from a mentioned entry is itself a
> mention.**

This is checkable rather than declared, because the entries match consumed are already recorded — R5
needs them for the trail. It is the trail turning out to be load-bearing for something other than
explanation, which §16 argues is the pattern to expect.

**The refusal was not where the design says refusals happen.** Such a rule was never rejected by the
gate. It was dropped by the **quiescence filter**, which treated a conclusion still containing
variables as *nothing left to do* — so a rule reasoning about rules looked exactly like a rule with no
work: no error, no trace, nothing to distinguish it from correct behaviour.

§2 says the machinery has exactly two places where it can be asked why it returned part of a
structure: `match` and `write`. That is one short.

> **Quiescence is a third place the machinery can decline, and it declines silently.**

Match returning nothing and write refusing are both observable. *This application would change
nothing* is indistinguishable from *there was nothing to apply*, which is §9's `−` against no-entry
and §19's two silences arriving in the one place the design had not looked.

### Adding a connective adds rows, not branches

The older statement of this test survives unchanged, and is now a corollary rather than an axiom:

> **If a new connective requires editing the engine, the connective set is not data.**

The same holds one level up for everything in Part III. If a new *convention* — a new way of
representing evidence, or plans, or time — requires editing the engine, then the bundle is not data
either, and §4's agreement gate is what detects it.

### One interpreter

Meta-rules buy nothing if the interpreter special-cases them. The interpreter's step is *select, then
apply*, and object-rules and meta-rules must be indistinguishable to it — a flat tower, not a stacked
one. If, standing inside the interpreter, you cannot answer *which level am I on?*, that is the sign
it is built correctly.

---

## 6. The bootstrap

If rules are facts, and facts are entries read by walking a chain, and the walk is made of rules, then
reading a rule requires applying rules and nothing ever starts. This section states the circle
precisely — it is narrower than it first appears — and closes it.

### Only one of four steps is circular

Applying a rule takes four steps, and the temptation is to say that all of them need a read:

| step | what it needs | circular? |
|---|---|---|
| 1. propose candidate rules | **recall** — a function from situation to node ids | no |
| 2. read the rule's structure | §4 item 1: members and positions | no |
| 3. check that its antecedent's entries hold | **the chain walk** | **yes** |
| 4. commit | §4 items 3, 4, 5 | no |

Step 2 is where earlier drafts went wrong. Reading a rule's *structure* is not reading the chain: an
antecedent is a node with members, and getting at them needs ordering and nothing else. What needs the
walk is deciding whether the antecedent's entries *hold*, which is step 3 alone.

### Stratum 0: antecedents that mention only structure

Look at what a chain-walking rule actually asks for:

```
given  ?m' = predecessor(?m)
       ?e ∈ delta(?m)
       ?e = entry(?l, ?p, ?s)
then   candidate(?e, ?p)
```

Every member is **structural** — membership, position, node identity, predecessor. Not one of them is
*does X hold at Y*. So step 3 for these rules is answered by §4's item 2 by itself, and they bottom
out. That is the fixed point, and it gives a criterion that is decided by inspecting an antecedent
rather than by a designer assigning layers:

> **Stratum 0 — every antecedent member is structural. Applied without a read.**
> **Stratum 1 and above — some antecedent member is an entry. Applied by the read stratum 0
> implements.**

The check is a scan. An implementation can run it over its own bundle and report which rules claim
stratum 0 and are not entitled to it.

### Two stratifications, and only one of them boots

There is a second, obvious way to stratify: **metarules about how to think, independent of the
business domain.** That cut is real and useful — it is what makes the bundle *shippable*, since one
knowledge base of thinking-rules can serve every corpus.

It is not the cut that breaks the circle. Trust rules, surprise rules and goal expansion are all
domain-independent thinking-rules, and every one of them talks about entries and beliefs, so all of
them are stratum 1 or above. Domain-independence makes the bundle shippable; structural antecedents
make it **bootable**. Keeping the two apart matters, because the first is much easier to satisfy and
looks like it should be enough.

### Three regresses, one escape

The bootstrap is not a special problem. It is the third instance of a shape the design already meets
twice:

| regress | escape | what the escape is |
|---|---|---|
| reading needs reading | stratum 0 | a set of rules that need no read |
| selecting needs selecting | the total precedence lookup (§18) | a table |
| proposing needs proposing | **recall** (§19) | a function |

All three bottom out in **a function, not a search**, which is also the shape of §4's three
irreducible items. That recurrence is the strongest evidence available that the floor is drawn in the
right place.

Recall is the one worth dwelling on, because it is the only component that can be consulted **before
any rule has been applied at all**. A function has no antecedent to read. Whether it is an index, a
table with defaults, or a trained network is an implementation choice among function approximators —
§19 already specifies it as incomplete by design, learned from outcomes, and recoverable when wrong,
which is the specification of an approximator written before anyone said the word.

### Stratum 0 runs under the same interpreter

The rules of stratum 0 must themselves be selected and applied, and it would defeat the purpose if
that took a second interpreter. It does not:

* **recall** for stratum 0 is *all of them, every time* — the set is small and fixed, so the policy is
  a different table, not a different mechanism;
* **match** is floor;
* **arbitrate** is the same total lookup, over a precedence relation that happens to be authored once.

That is one more row, not one more branch, which is §5's own test applied to the escape rather than to
the conventions.

**Termination** is a proof obligation rather than a difficulty: the walk is transitive closure over
the predecessor relation, which is finite and acyclic, and forking preserves both.

### The price, stated

**Stratum 0 must produce structure, not entries.** If the walk deposited its intermediate results as
claims, it would be reading entries and the circle would return. So the read's own working state is
undated, unattributed and unexplained.

The consequence is worth writing down rather than discovering:

> **You cannot ask *why did you read it that way* through the same mechanism you ask *why do you
> believe that*.**

R5 (*every conclusion carries its support*) covers conclusions, not the resolution that fed them.
Promoting the read into stratum 1 to fix this reinstates the circle, so the gap is structural rather
than an oversight.

A second price, from the other escape: **recall is opaque, and must remain the only opaque thing.**
*Why did you consider that rule?* has no answer, so R5 in practice reads *every conclusion carries its
support, among what surfaced*. §19's carve-out — prohibitions come off the recall path entirely and
are checked at the write — now reads as the general principle rather than a special case: **the opaque
component may not be load-bearing for safety.**

### What this buys

Stratum 0 rules are ordinary data. Creating one is a write, and a write needs only the register and
the stamp, both floor. Therefore:

> **The read is replaceable at run time.**

That is the whole claim of this document's preamble — that an agent with a better internal
representation of reality reasons better, and that the representation is something you can hand it —
turned from an aspiration into a mechanism. The bundle is not merely shipped rather than compiled in;
it is editable by the agent that runs it.

---

# Part II — The internal representation of reality

Everything from here on is convention. It is the bundle: what the agent is taught about how reality is
shaped, so that it can reason about what was, what is believed, and what is merely supposed.

Part II is the core of the bundle — the part every other convention is written against. It is
presented in the order you would teach it.

---

## 7. Moments

A **moment** is the bundle's only construct for a state of affairs. A state in time, a hypothetical, a
supposition and a rule's antecedent are all moments; there is no separate "frame", "world" or
"context" object.

A moment has three parts and nothing else:

```
<M> = a signed delta      +  a predecessor          +  a licence
      (entries, §8)          (an edge to a moment)     (an edge to a node)
```

The delta is what changed. The predecessor says what it changed *from*. The licence says what
authorised the difference. Only the licence varies by reading:

| the moment is | its predecessor is | its licence says |
|---|---|---|
| a state in **time** | the previous state | *an event happened* |
| an **imagined state** | the imagined state before it | *I applied this rule in supposition* |
| an **assumption** | where I was standing when I made it | *I decided to suppose this* |
| a rule's antecedent or consequent | **none**, or another generic moment | — |

### Anchored and generic

The distinction that carries weight is not between kinds of moment but between:

* an **anchored** moment — individuals, and a predecessor in the history;
* a **generic** moment — variables, and no *anchored* predecessor.

A generic moment may have a **generic** predecessor. This is what lets a pattern say *and then*: a
pattern is a chain, not a point, and the same construct serves whether the chain is one link or many.
What a generic moment may not do is point into the history, because a pattern that named a particular
past would be about that one occasion.

A rule's two members are generic. Everything else is anchored. Because this distinction is
structural, it is checkable rather than maintained by convention — the one place in Part II where that
is true, and it is true because *generic* is §4's floor item 2 showing through.

The bundle's central operation is then one line:

> **To match a moment is to unify a generic chain against an anchored one.**

*Unify* is §4's item 2: find a substitution making the generic side identical to the anchored side.
The chain part is what makes this a **program** rather than a primitive — §10 is that program, and it
is data.

The one-link case is the common one, and reads as the older, narrower rule: unify a generic moment
against an anchored one.

**Nesting needs no mechanism.** A supposition inside a supposition is a path in the predecessor tree.
There is no depth limit and no scope object. *Scope* nesting is ancestry, and ancestry is derived —
there is nothing to push. This says nothing about **control**, which is a separate structure and §17's
subject: which reasoning invoked which, and where an answer is owed. Control is not scope, and the
absence of a scope stack does not mean the absence of the other.

### A moment is a belief state

A moment's delta is entries, and an entry names the moment it is **about** (§8). Those need not be the
same moment. An entry deposited in `M12` may have `M7` as its locus — *I now think it was raining
then* — and that is the ordinary form of learning something about the past.

So a moment carries two things at once, and the bundle needs no separate construct for the second:

| | |
|---|---|
| the world at a point | the entries in the delta whose locus is the moment itself |
| **what the agent believes here, about any time** | the delta entire |

**There is no belief-set object.** A moment already is one. What would be *the current beliefs* is the
chain read at the moment you are standing in, and belief revision is ordinary succession — the same
relation, with a licence saying *I came to think otherwise*. Introducing a second membership structure
for beliefs would create a second ordering beside succession, and two orderings that agree by
convention drift without detection.

### Time and derivation share a core

Two orderings could easily become unrelated: succession in time, and succession in a derivation.
Under one construct they are **one relation with two licences**. Succession is the shared core; time
adds a clock stamp above it, derivation adds a licensing rule above it.

The invariant that must survive this sharing: **supposing takes no time.** A derivation step is
succession without duration. If the shared core carried a clock, the two would have been collapsed
rather than related, and every hypothetical would falsely advance the world.

### Scoring the convention

| | (A) a mutable world state | (B) a set of currently-believed facts | (C) moment = delta + predecessor + licence |
|---|---|---|---|
| not leaking | ❌ overwriting loses the claim it replaced, so *it changed* and *I was wrong* are one operation | ⚠ a set says what is believed and nothing about when or why | ✅ every difference is licensed and dated |
| not lossy | ❌ history is gone | ❌ the previous set is gone unless separately kept | ✅ nothing is overwritten |
| readable | ✅ a lookup | ✅ a lookup | ❌ **a read is a walk** — the design's largest single cost, accepted in §10 |
| composable | ❌ two writers contend for one cell | ⚠ union of sets is not merge of beliefs | ✅ forks are free; two successors of one moment need no coordination |

The ❌ in the readable column is the price of the whole design and it is paid on every read. It buys
supposition at no cost, immutable history, and a date on every claim.

---

## 8. Propositions and entries

A relation instance is a **proposition**. It claims nothing. `on(a, b)` is the *idea* that a is on b,
not the assertion that it is.

The claim is a separate node, the **entry**:

```
<e> = entry(<M7>, on(a, b), +)          three members: locus, proposition, sign
```

An entry has exactly three members:

* **locus** — the moment (§7) or span (§11) the claim is about;
* **proposition** — what is claimed;
* **sign** — how it is claimed (§9).

### An entry is in a moment's delta

The delta of §7 is where entries live, and the relation is ordinary membership: a moment's delta is
its entries, and an entry is deposited by being placed in one.

```
<M12> = moment( delta:       <e1>, <e2>, <e3>
                predecessor: <M11>
                licence:     <application-of-R1> )
```

**When the claim was made is not a fourth member of the entry.** An entry is in some moment's delta,
and that is its **deposit moment** — *believed since here*. It is already structure, so it costs
nothing and cannot be omitted. The locus says **what the claim is about**; the delta membership says
**when it was made**. Keeping them apart is what lets the agent revise its view of the past without
rewriting it, and conflating them is what would force every claim to be about the moment it occurred
to someone.

An entry therefore has two temporal coordinates and stores exactly one of them as a member. The other
is where it sits. §10 is the read that uses both.

### Everything else about an entry is an ordinary fact about it

```
grade(<e>, likely)     licensed_by(<e>, <application>)     said_by(<e>, anna)     at(<e>, 09:14)
```

This is how the source channel is recorded, and it answers the obvious objection that provenance
appears in two places. It does not. §4's stamp is a floor-level record on the *mint* — what produced
this node — and is not a vocabulary item; nobody queries it directly. The **channel**, the
**authority** and the **licence** are ordinary facts about the entry, written by the gate (§17)
because the gate is what knows them. The stamp is the guarantee that these facts were not chosen by
the rule; the facts are what the agent reasons with.

| | what it is | who writes it | can a rule read it |
|---|---|---|---|
| the mint stamp | floor-level provenance on the node | the write operation, always | not as vocabulary — it is the guarantee, not the record |
| `licensed_by`, `said_by`, `grade` | ordinary propositions about the entry | the gate (§17), from the frame | yes, by ordinary matching |

### Why two levels are forced

To say *`on(a, b)` is false at M12*, you must be able to point at `on(a, b)` — so the proposition
must exist in order to be denied. If the proposition node were itself the assertion, then minting a
node in order to negate it would assert it. Two levels are what negation costs. In exchange, nothing
in the system has to remember that a bare proposition means nothing: it structurally cannot be
mistaken for a claim, because it has no locus and no sign.

### Where the regress stops

An entry is itself a fact. Does it need an entry of its own? No: **an entry names its locus, so it is
located by being one.** A proposition needs an entry to be placed in a moment; an entry places itself.
The recursion terminates at depth one, structurally.

The claim is narrow, and the narrowness is what makes it survive. An entry needs no entry **to be
located**. It may freely be the **subject** of another entry's proposition, and it has to be, or the
bundle loses three things it depends on:

```
mistaken(<e>)                     correction — my record was wrong
outranks(<e1>, <e2>)              §17's arbitration — a claim Anna made beats one Bo made
supposed(<e>, <S>)                a belief held about a belief, where <S> is the supposition
                                  moment (§7) it was held under
```

Those are ordinary entries with ordinary propositions that happen to point at entry nodes, and each
locates itself. **Locus and member are different relations to an entry, and only the first would
regress.**

### Exactly three members

Grade, licence, speaker and clock stamp are facts about the entry, never a fourth member. The
discipline matters: with optional slots, an entry becomes a node of variable arity whose members mean
different things depending on how many there are, which is the same shape carrying several membership
semantics — unreadable and uncomposable. The same discipline keeps the connective in §12 binary, with
timing as an adjunct fact.

### What the two levels buy

The world changing and the agent having been wrong become **different operations**:

| | what happened | how it is written |
|---|---|---|
| they stopped being on each other | the world moved | a **new entry**: opposite sign, later locus |
| I was mistaken that they ever were | my record was wrong | a **fact about the old entry**; the entry is unchanged |

If truth were a value stored on the proposition node, these would be indistinguishable — both are
*change it* — and a system that cannot distinguish them quietly rewrites its own history.

| | (A) truth as a value on the proposition | (B) proposition + entry |
|---|---|---|
| not leaking | ❌ minting a node to deny it asserts it | ✅ a proposition with no entry claims nothing |
| not lossy | ❌ correction overwrites the record it corrects | ✅ correction is a new fact; the original survives |
| readable | ⚠ one hop | ⚠ two hops, but *who claimed this, when, on what grounds* are ordinary queries |
| composable | ❌ two sources disagreeing means one overwrites the other | ✅ two entries, two attributions, arbitration by rule |

### The cost, stated

**Resolving a read is the bundle's central program.** *Does `on(a, b)` hold here?* means *walk the
chain for entries naming this proposition at the locus asked about, and order them by §10's two keys*.

Earlier drafts said the engine must know what `entry` means. It must not, and §5 is why. What must
know is the **read program**, which is bundled data. The implementation may run it natively for
speed, subject to §4's agreement gate.

Propositions have one identity however often they are built; **entries do not**. An entry is an act of
claiming, so two claims about the same proposition at the same locus are two nodes — otherwise
`mistaken(<e>)` would land on both the mistake and its correction.

**Contradiction is permitted and undetected.** Two entries in one locus with opposite signs is a
shape the substrate allows. This is correct: consistency is a **question you ask**, not an invariant
the substrate maintains — the alternative is checking every write against every other claim. But it
means *is this moment consistent?* is a query somebody must run, and the design does not say who.

---

## 9. Signs

An entry's sign says how the proposition is claimed at its locus. There are three signs plus the
absence of an entry, and their meaning differs between anchored and generic moments — because a
generic moment has no predecessor to inherit from.

| sign | in an **anchored** moment | in a **generic** moment |
|---|---|---|
| `+` | holds here | must hold |
| `−` | does not hold here | must not hold |
| `?` | **held before; does not now; I cannot say what does** | — |
| *no entry* | **unchanged — inherit from the predecessor** | don't care / not constrained |

### No entry means inherit, not unknown

This follows from §10: the chain walk continues past a moment with no entry and finds an older one. In
an anchored moment, silence is therefore a positive claim — *this is as it was*.

That is why `?` must exist as a distinct sign. R6 (*partial knowledge must be sayable*) has as its
example *pouring raises the level by an unknown amount*, and it cannot be written by writing nothing,
because writing nothing means the chain returns the **old** level. Without `?`, the one thing the
author was trying to say is the one thing that could not be said. `?` **invalidates without
replacing**: it stops the walk and reports ignorance.

The generic `?` (*I don't constrain this*) and the anchored `?` (*this was invalidated and I cannot
say what replaced it*) are different claims. They share a symbol because the anchored/generic split
already distinguishes them structurally, but they are not the same thing and a reader is owed the
distinction.

### Sign and `not` are not rivals — measured

The question this section carried was *should negation be a member or a wrapping term?* The answer is
**both, and for the same reason §16 keeps both a grade and a modal term**. Two things settled it, and
neither was an argument.

**A sign can already be reasoned about.** The case for wrappers included *a rule cannot ask about a
denial*. It can: an antecedent member carrying `−` with a bare-variable pattern binds the denied
proposition, which is exactly how §18's deviation rules read an observation. That half of the case
was wrong.

**A sign cannot nest, and the design nests by construction.** §16 re-wraps a conclusion on the way out
of a supposition. Conclude `−b` under a `likely` supposition and the claim is *likely, not-b*. With
only a sign to carry it, what crosses out is `−likely(b)` — *it is not likely that b*. A different
claim, and a stronger one. That was live in the implementation, not hypothetical.

So the sign stays, and a **term** is added beside it:

| | what it is | what it is for |
|---|---|---|
| the `−` **sign** | a member of the entry | the ordinary case; matched, and never forgotten, because match cannot return an entry without it |
| `not(p)` | a **proposition** | the nested case, where only a term can sit inside another term |

> **The member is what the machinery computes with. The term is what survives nesting.**

That is §16's sentence about grades and `likely`, word for word, one level down — which is some
evidence the pairing is the right shape rather than a patch.

**The translation runs one way, and the asymmetry is the design.** `+not(p)` becomes `−p`, so a corpus
written against signs reads a term the machinery manufactured while re-wrapping. The reverse — minting
`+not(p)` for every denial — is declined: it would double every negative fact and would build
`not(not(p))` on meeting its own output. That is the cost this section warned wrappers carry, and
declining the reverse direction is where it is not paid.

`?` is untouched and stays a sign alone. It is a statement about *reading* — stop the walk, report
ignorance — and wrapping it as a term would make it look like a claim about the world. What a `?`
conclusion should become on the way out of a supposition is not settled (§21).

### What this leaves open

**`says` keeps its third member.** §15 carries the sign of a report as `says(channel, proposition,
sign)`, and the collapse to `says(chan, not(p))` is now *available* rather than required — a report
that something is not so could be written either way. Which one a channel should use is unsettled, and
so is whether allowing both is a corpus splitting into two dialects.

**A `?` conclusion crossing out of a supposition** has no defined form. `+` and `−` both become terms
under the wrapper; `?` is a statement about reading and cannot. What *likely, and I cannot say* should
look like outside the frame is not specified.

---

## 10. The read

This section is the bundle's central program. Everything in Part II exists so that this walk can
answer well, and everything in Part III is written against its answers.

Because a moment stores only what changed, a moment does not contain its state; **the state is what
the chain answers.** Reading is a walk, not a lookup.

### The two indices

Because an entry has both a locus and a deposit moment (§8), the walk is ordered by **two keys, in
this order**:

> **Latest locus, then latest deposit.**

An entry is a candidate if its locus is at or before the moment asked about — that is inheritance, and
it is why the locus cannot simply be matched for equality: `on(a, b)` asserted at `M3` is what makes it
hold at `M7`, where no entry mentions it at all. Among the candidates, the **latest locus** wins,
because the most recent claim about the world is the one that governs. Only when two claims share a
locus does the **latest deposit** decide, and that is exactly the revision case.

Both keys are needed, and neither alone will do. Locus alone cannot tell a revision from the claim it
revises. Deposit alone would let a newly formed belief about an early moment overrule a long-standing
one about a later moment — the agent would forget that the world had moved on.

### Two questions, one structure

To ask *what do I now think about `M7`?*, walk back from where you are standing. To ask *what did I
think at `M7`?*, walk back from `M7` instead: the entries deposited later are simply not on that walk.
In the common case — an entry deposited at its own locus — the two questions coincide, which is why
the distinction can be missed.

A design with a single index would have to choose which of those two questions to keep.

### At-or-before is ancestry, not depth

The candidacy test walks the predecessor relation. It cannot be a comparison of depths, because
supposing forks the chain by construction (§16) and two moments at the same depth on different
branches are not comparable at all. This is the cheapest place in the design to introduce a bug that
only appears once hypotheticals are used.

### What this costs, and what it is worth

The walk is the largest recurring cost in the design. It is also, per §4, **a program made of rules**:
transitive closure over the predecessor relation, a filter on locus, an ordering by two keys. Nothing
in it requires engine support beyond structural matching.

That is the claim §4's agreement gate exists to check, and it is the one most worth checking, because
this is precisely the program an implementation will write natively first.

| | (A) locus only | (B) deposit only | (C) two keys, locus first |
|---|---|---|---|
| not leaking | ⚠ a revision and the claim it revises are indistinguishable, so one silently wins | ❌ a new belief about the distant past overrules a settled belief about the recent past | ✅ each key answers the question it is for |
| not lossy | ✅ | ✅ | ✅ both the original and the revision remain readable |
| readable | ✅ one walk | ✅ one walk | ⚠ one walk, two comparisons |
| composable | ⚠ two authors revising the same locus collide | ❌ | ✅ later deposit settles it, and both survive |

---

# Part III — What the representation allows

Everything here is built on Part II and adds no engine capability. Each section states what it is
*for*, and its scoring table scores the convention.

---

## 11. Spans

*Saying when, over a stretch.*

Some claims are not about a moment at all. *They are taking turns* is not true of any instant; its
subject is a **stretch of the chain**. So is *it rained throughout*, and so is any constraint on the
order in which things happen.

A **span** is a node with exactly two members: a start moment and an end moment.

```
<s> = span(<M7>, <M12>)                        position 0 = start, position 1 = end
<e> = entry(<s>, taking_turns(anna, bo), +)    the locus of this entry is the span
```

Spans are loci. Nothing else about the entry changes — which is the point: §8 said the locus is a
moment *or a span*, and nothing in the read (§10) had to grow to accommodate the second.

### Membership is not stored

The moments an **anchored** span contains are **not** listed, and the reason is structural: **the
predecessor relation is single-valued.** A moment has one parent; forking produces several successors,
never several parents. So the walk back from `M12` is unique, and if `M7` lies on it the span's
contents are fully determined by the chain.

The table below therefore scores anchored spans, where the chain is available to settle the question.

| | (A) endpoints only | (B) enumerate the moments | (C) a description of the stretch |
|---|---|---|---|
| not leaking | ✅ contents derived from the chain, so they cannot disagree with it | ❌ two answers to *what is in this span* | ✅ |
| not lossy | ✅ | ⚠ records the extent, not why those | ✅ |
| readable | ✅ fixed 2-ary | ❌ an extent claim wearing positional clothes; arity varies with duration | ⚠ |
| composable | ✅ interval relations compare two pairs of endpoints | ⚠ comparing spans means comparing lists | ❌ comparing descriptions is not expressible |

### Two things stay out of the span

**Participants.** `anna` and `bo` are members of the proposition, never of the span. This is what lets
one span host several unrelated recognitions — *they took turns* and *it rained throughout* — over the
same stretch.

**Disjunction.** *On Monday and on Wednesday* is two spans plus a fact relating them, never one span
with a hole in it. A span with holes would smuggle disjunction into a shape nothing can consume.

### Recognition and prescription are one predicate read twice

A **generic** span, with variables for its endpoints, is a constraint to be satisfied — *do these in
this order*. An **anchored** span is a recognition that a pattern held. Same predicate, same shape;
the anchored/generic split of §7, one level up.

### A generic span's interior must be described

A generic span has no chain, so nothing determines what lies between its endpoints. Endpoints alone
say only *start before end*; enumerating an interior would invent a length nobody claimed. **For a
generic span, option (C) is not a rejected alternative but the only one available** — the interior is
given by a *description*, and §13 is what descriptions are made of. The ❌ in (C)'s composability
column is the bill that comes with it, and §13 states what it costs.

### Costs

* Spans are **directional**, so equality of content must be normalised by chain order, not by member
  order — otherwise two spans over the same stretch can fail to be equal.
* Any two moments form a span, so the population is quadratic. Spans are therefore **minted by
  recognisers, never enumerated**.
* Nothing prevents constructing a span whose start is not an ancestor of its end. Such a span is
  meaningless, so the ancestry check belongs at the **minting site**, where it is cheap and where the
  mistake is still attributable.

---

## 12. Rules

*Saying what follows.*

A rule is a **fact relating two moments**.

```
<R> = causes( <A>, <B> )
```

`<A>` and `<B>` are generic (§7): variables, no anchored predecessor. `<A>` is the antecedent. `<B>` is
the consequent, and because a moment is a signed delta, `<B>` is a delta **relative to** `<A>` without
being a second kind of object.

Because `<R>` is a node, everything else about it is an ordinary fact — which is R3 (*rules are
subjects*):

```
by(<R>, boss)          overrides(<R>, <R2>)          about(<R>, assembly)
unless(<R>, +altitude(?w, high))
```

And because the rule's content is data rather than a program, R4's questions (*rules are askable*) are
ordinary queries: *which rules are about time* is a query over `about`; *which rules disturb position*
is a query over the consequent's members.

### Notation

This document previously used punctuation — `@` for a locus, `→` for a pair of endpoints, `[...]` for
an interval — which made a handful of open-class concepts look like engine syntax. They were
abbreviations, and this draft writes them out. Punctuation that suggests a privileged mechanism is
exactly the island §2 warns about, at the level of the page rather than the graph.

**Loci are ordinary members, and entries may be named.** An antecedent member is written as the entry
it is:

```
?e1 = entry(?m, on(?x, ?y), +)          named, because something below refers to it
      entry(?n, acts(?a), +)            unnamed
```

The short form `+on(?x, ?y)` remains legal and means *an entry with this proposition and this sign,
whose locus is the one the frame supplies* (§17). It is an abbreviation, not a different construct,
and it stops being available the moment the rule needs to name the locus or the entry.

**Facts about a consequent's entry are written about the named entry:**

```
then  ?e = entry(?m', boiling(?w), +)
      grade(?e, certain)
```

**Endpoints and intervals are nodes.** §15's timing member relates two named endpoints and carries a
bound:

```
<t> = timing(<R1>, end(<A>), start(<B>))     which endpoints this is about
      bound(<t>, 4min, 7min)                 how far apart; absent means unknown
```

### The three readings

*Unify* is §4's substitution. *Want* is the backward reader's goal — a proposition it is trying to make
true. *Disturb* is what a `?` entry does: it says the rule changes something and cannot say to what.

| reading | what it does |
|---|---|
| **forward** | match `<A>` against the current chain; apply `<B>`'s signs into a successor moment |
| **backward** | unify a wanted fact against `<B>`'s `+`/`−` entries; `<A>`'s unsatisfied members become subgoals, as far as the agent can discharge them |
| **`?` entries, backward** | *this rule disturbs that and cannot say how* — a **want**, not a failure, and not a false *it stays as it was* |

### Two readings, not two equally useful ones

R1 (*two readings of one statement*) asks that both readings come from one statement. It does not
promise that both are informative, and one shape makes the difference sharp: a consequent that is a
**bare variable**.

```
<trust> = implies( { entry(?m, says(?c, ?p, +), +) }, { entry(?m, ?p, +) } )
```

Forwards this is exact and is the whole of §17's *trust is a rule* — whatever the channel said,
believe it. Backwards it says *this rule can conclude anything*, so it proposes itself for every goal,
and its subgoal is another goal of the same shape, without end. It is not wrong; it is vacuous.

The backward reader therefore declines what it cannot use, and that is a placeholder rather than an
answer. **The real home for this is recall** (§19): which rules come to mind when reading backwards is
learned, and a rule that has never once helped a search is exactly what recall should stop offering.
Declining bare-variable consequents is a fixed rule standing in for a learned one, and it should be
retired when recall is.

Direction is a **query over the rule**, never a field in it. This is R1: one statement, two readings.
R2 (*the reading must be recoverable*) is met because each reading cites `<R>`, and the licence
recorded on the resulting entry says which reading produced it — so a hypothesis formed by reading
backwards is distinguishable, permanently, from a conclusion drawn forwards.

### An antecedent has two kinds of member

An entry names its own locus (§8). So an antecedent is not *entries at one moment*; it is **signed
entries whose loci are variables**, together with the **skeleton** that relates those variable loci:

```
where    ?n = succ(?m),   ?s = span(?m, ?e)              skeleton — how the loci connect
given    entry(?m, on(?x, ?y), +),  entry(?n, acts(?a), +)     what is claimed, and where
```

The one-locus case, where every entry sits at the same moment and the skeleton is empty, is the common
one and is written without either keyword, using the short form above.

The two kinds do not merge, because a skeleton member is **not a claim**. `?n = succ(?m)` has no sign,
no locus and no licence; nobody asserted it, and it cannot be denied, dated or attributed. §3 says why:
ordering is a fact about how a node is built, not a relation in the world. The skeleton is the part of
the antecedent that match settles by unifying structure, rather than by walking a chain for entries.

Distinctness belongs in the skeleton for the same reason. `?a ≠ ?b` is a condition on the binding, not
a dated claim that two individuals differ.

### A consequent may name its locus, when the locus is bound

An antecedent binds variable loci; a consequent may use them. §13's shape rules already depend on this
— concluding `taking_turns(?a, ?b)` at the span `?s` the skeleton bound — and without it a recognition
about a stretch could only ever be deposited as a claim about the instant it was noticed.

This does not weaken §17's argument that a rule cannot name a locus, because the two say different
things. A rule may not name **a particular** locus; that is what makes it generic. It may name a
**variable** one that match bound, because a variable is exactly what does not commit the rule to an
occasion. Where a consequent names no locus at all, the frame supplies it (§17), and that is the
common case.

### Achievability is not a mark

This is the design's earliest instance of the error Part I generalises, and it is worth keeping in
full for that reason: the temptation was to close an open concept by giving the engine a mark to read.

Read backwards, an antecedent member becomes a subgoal — but not every member should. *To unbolt it,
it must be on the bench, and you may put it there; it must be a Tuesday.*

That difference is **not a property of the member**, and cannot be marked on it, because achievability
is relative to four things the rule's author does not know:

| relative to | *make it Tuesday* is |
|---|---|
| **who is planning** | out of reach for me, in reach for whoever can move the meeting |
| **the deadline** | achievable if I have a week, not if I need it within the hour |
| **the situation** | already true, on a Tuesday |
| **the rules known** | achievable exactly when `wait` is among them |

A mark authored once, at rule-writing time, is relative to none of them — and it is the wrong shape
besides. Achievability is *derived* from capabilities, budget and the rule set; stored on the rule it
is a cache of a derived value, invalidated by learning a rule or gaining an authority, which is the
defect §16 names when it refuses to store a grade on a proposition.

What the mark would have been doing is three things, each with a home already:

| the work | where it belongs |
|---|---|
| *don't expand this, you will thrash* | **recall** (§19) — learned, incomplete, and the one step where being wrong is recoverable |
| *achievable, but only by waiting, or only for the boss* | a **claim**, attributed and defeasible, with its cost as §15 timing |
| *you could, and you must not* — seeding clouds to make it rain | a **prohibition** (§19), gated at the write |

The third is the reason to insist. A mark lets a norm masquerade as a physical impossibility, and
those must not share a slot.

So every antecedent member is simply a required entry, and *is this one worth planning for* is asked
of the agent, not read off the rule. **Waiting is an action**, so a precondition that takes time is
achievable at a price — which §15's timing already states in a form that may be absent, attributed and
compared against a deadline:

```
+tuesday(?d)                                   an ordinary requirement
<t> = timing(<WAIT>, start(<A>), end(<B>))     what discharging it costs
      bound(<t>, 0, 7days)
```

The bill is that backward search loses a static bound: *make it Tuesday* is now a subgoal a planner may
genuinely expand. §13 states the discipline that replaces it — bounded expansion returns a result **and
a state**, so *I found no way* stays distinguishable from *there is no way*.

### Worked

```
<R1> = causes(
    given  +heat(?a, ?w),  +water(?w),  +open(?vessel)
    then   ?e1 = entry(?m', boiling(?w), +)     grade(?e1, certain)
           ?e2 = entry(?m', liquid(?w), −)      grade(?e2, certain)
           entry(?m', volume(?w), ?) )

<t> = timing(<R1>, end(<A>), start(<B>))     bound(<t>, 4min, 7min)
unless(<R1>, +altitude(?w, high))
```

```
<R2> = implies(
    given  +cloudy(?day, morning)
    then   ?e = entry(?m, rain(?day, afternoon), +)     grade(?e, likely) )
```

### Scoring the form

| | (A) guard → program body | (B) one rule per direction | (C) `connective(moment, moment)` |
|---|---|---|---|
| not leaking | ❌ the backward read is hypothesis wearing entailment's clothes, with nowhere to record it | ❌ two statements drift; neither is the other's premise | ✅ one statement; each reading cites `<R>`, whose licence says what the citation is worth |
| not lossy | ❌ what it makes true is recoverable only by running it | ⚠ the pair coheres only by convention | ✅ `<B>` **is** the postcondition; `?` preserves a gap instead of erasing it |
| readable | ❌ runnable, not askable — fails R4 | ⚠ readable, doubled | ✅ every question about a rule is a query over its members and adjuncts |
| composable | ❌ two bodies cannot be joined | ❌ n directions means 2ⁿ statements | ✅ join on signed membership; no-entry survives composition as no-entry, so two partial rule sets merge without lying |

(A) fails an additional test outright: `overrides(<R1>, <R2>)` has no subject when a rule is a program.
Nothing can be said *about* it, so R3 is unreachable.

---

## 13. Shapes

*Saying what follows, over an indefinite extent.*

Some things are known by their **shape** rather than by their extent. *Anna and Bo are taking turns*
can be said having watched a sequence, and it can be said having watched nothing — *imagine they are
taking turns* — and it is the same claim either way. The second reading is the demanding one: there is
no sequence to point at, and materialising one would state a number of turns nobody claimed.

Two kinds of indefiniteness need this, and they are not one construct:

| | *taking turns* | *some files* |
|---|---|---|
| indefinite in | **extent along the chain** | **multiplicity within a moment** |
| composes by | succession — ordered, and the elements are moments | membership — unordered, and the elements are individuals |
| leak if materialised | invents a number of turns | invents a number of files |

They share one principle, which §11 already applies to spans and which this section generalises:

> **Describe the extent. Never enumerate it.**

### A shape is a definition, not a term

Given §12's antecedent, a shape needs no new construct: it is a **recursive definition over spans**,
written as ordinary rules in open-class vocabulary. *Taking turns* needs at least two turns, so that
is the base case, and the step case consumes one turn and defers the rest:

```
<TT-base> = implies(
    where    ?n = succ(?m),  ?p = succ(?n),  ?s = span(?m, ?p),  ?a ≠ ?b
    given    entry(?n, acts(?a), +),   entry(?p, acts(?b), +)
    then     entry(?s, taking_turns(?a, ?b), +) )

<TT-step> = implies(
    where    ?n = succ(?m),  ?s = span(?m, ?e),  ?s' = span(?n, ?e)
    given    entry(?n, acts(?a), +),   entry(?s', taking_turns(?b, ?a), +)
    then     entry(?s, taking_turns(?a, ?b), +) )
```

`acts` is an entry rather than anything special, because §15 already settles that an action is an
ordinary fact holding over an interval.

**The alternation is the argument swap** — `?a, ?b` in the head, `?b, ?a` in the recursive member.
Remove it and the definition says *someone acts repeatedly*. That swap is a back-reference, and it is
the reason a shape is a definition rather than a pattern term.

The two readings of §12 are what make one definition serve both cases. **Forwards** it recognises an
observed stretch. **Backwards** it generates a hypothetical one, expanded only as far as a goal
demands, each step an imagined moment with its own licence (§7). So *they took turns* and *imagine they
are taking turns* are R1 one level up: one statement, two readings.

### These definitions are already a grammar

`<TT-step>` threads a start, a middle and an end through its members. That is a difference list, and a
rule consuming a chain between two endpoints is a grammar production over the moment chain. Spans are
the difference lists; §11 built them. So the question is never *grammar or not* — it is whether the
grammar is reserved or open-class, which is §5's test one level up.

Reserved would buy exactly one thing: **decidable equivalence**, the ❌ in §11's (C) column. It does not
survive contact with what shapes are actually for:

* *the same actor does not go twice running* — a back-reference;
* *each turn touches a different file* — inequality across an unbounded set;
* *at most five times, **unless** interrupted* — defeasibility, which needs `unless` and precedence
  **inside** the parser.

Each leaves the class that made equivalence decidable, and the last is not a grammar question at all:
a production cannot carry `unless` or `overrides` without re-deriving precedence inside a second
engine. A reserved formalism buys decidability and then spends it on its first three extensions.

### Bounds are facts about the shape

A shape needs a subject — something for a bound and a provenance to attach to, since neither belongs to
the base rule or the step rule alone. That subject is one open-class relation:

```
<TT> = shape( taking_turns(?a, ?b) )
repeats(<TT>, 0, 5)                       absent means unbounded
by(<TT>, boss)     about(<TT>, protocol)     unless(<TT>, +interrupted(?s))
```

This is §15's timing member, exactly: a constraint on an extent, sayable as an interval, absent meaning
unknown, and permitted to disagree with another source. It reads in both directions the same way —
**forwards**, exceeding the bound is a deviation, so §18's surprise rule applies unchanged;
**backwards**, the bound is a filter, and therefore the termination discipline for expansion.

Counting costs nothing structurally. Every entry carries a licence naming its application (§17), so
*how many times did this shape step here* is a walk over the trail — derived, dated, never stored,
which is the discipline §16 states for grades. §16's refusal of numbers does not transfer: it was
specifically that probabilities need independence assumptions unstatable in the graph, and a count of
applications is an exact observation of the trail, where comparison is not composition.

### Two bounds, which must not share a slot

| | *they take at most five turns* | *expand this at most five times* |
|---|---|---|
| what it is | a **claim about the world** | a **budget on the agent's effort** |
| where it lives | `repeats`, on the shape — attributed, gradeable, defeasible | §19's budget |
| can it be wrong | yes; a sixth turn is a **surprise** | no — it is not about anything |
| exhausting it yields | *no* | ***I don't know*** |

Fuse them and *the shape ended at five* becomes indistinguishable from *I stopped at five*. That is
§9's `−` against *no entry*, and §19's *nothing applies* against *nothing came to mind*, arriving a
third time, so it takes the same answer:

> **Bounded expansion returns a result and a state, never a result.**

### Plurality is a group, and its membership is not stored

*Some files were copied* has the same defect under materialisation and takes the same principle. Mint
**one** node for the plurality and do not enumerate it; what is known about its size is an ordinary
fact about that node:

```
<fs> = files                 a group; members not stored
atleast(<fs>, 2)             absent means unknown
+copied(<fs>)
```

This is §11's move — *membership is not stored* — over membership instead of over a chain. It also
disposes of counting-in-positional-clothing: *made of four wheels* is a claim about a group's size, not
a four-place relation, and it is then attributable and defeasible like any other claim.

Whether the claim distributes — *each file was copied* against *the files together filled the disk* —
is a fact about the **entry**, not a new construct. Same slot discipline as the grade in §16.

### Scoring

| | (A) materialise a witness sequence | (B) a reserved grammar with counters | (C) recursive definitions, bounds as facts |
|---|---|---|---|
| not leaking | ❌ states a length nobody claimed; a consumer reads three turns as *the* number | ⚠ a production's reading pair is fixed by the engine, so it has no premise and appears in no explanation | ✅ only the shape is asserted; every expansion step is licensed and dated as supposition |
| not lossy | ❌ *how many?* answered by an artefact | ⚠ the parse is recoverable only by running the parser, unless the chart is deposited as entries — which is the trail again | ✅ the definition **is** the shape; ignorance of length is recorded by there being no length |
| readable | ✅ trivially | ⚠ *which shapes bound repetition* needs a walk over production terms — a second query language | ✅ shapes are rules and bounds are facts, so R4's questions stay ordinary queries |
| composable | ❌ two witness sequences of different length are not the same claim | ❌ a second closed set, and a production cannot carry `unless` or `overrides` | ✅ definitions compose as rules; `repeats`, `by` and `unless` attach unchanged |

### Costs

* **Shape equivalence is undecidable.** §11 named this as (C)'s price and this is where it is paid: with
  recursion you can say *taking turns*, and you can no longer decide in general whether two definitions
  describe the same shape.
* **§20's commutation gate runs per instance, to a depth**, rather than as a property over the whole
  rule set.
* **Backward expansion can mint unboundedly.** §11's discipline — spans are minted by recognisers, never
  enumerated — becomes the stronger requirement that expansion is demand-driven and budgeted, with the
  cycle care §16 asks of any walk over derived structure.
* **A shape is two rules where an author expects one.** Recall is keyed by shared terms (§19), so
  nothing guarantees that a base case and its step case surface together.

---

## 14. Connectives

*Saying which kind of following.*

Two connectives, and the question this section answers is why exactly two — not why the engine knows
about them, because per §5 it must not.

### The membership test

> **A connective earns its place only if it licenses a different (forward, backward) reading pair.**

If two candidates read the same way in both directions, they are one connective, and the difference
between them belongs in a member. Applying the test eliminates the obvious candidates:

* `prevents(A, B)` is `causes(A, {−B})`. Consequents are signed, so prevention is already sayable.
* `enables(A, B)` is `causes(A, {+B, grade possible})`. Read backwards, the two are told apart by the
  grade: `certain` means doing `A` achieves `B`; `possible` means `A` is a precondition and something
  else must still happen.

### Why the remaining two do not collapse

The distinction is not *logical versus worldly*. It is mechanical:

> **Retract the antecedent. Does the consequent go with it?**
> **Yes → `implies`.** The entry is *derived*. It lands in the **same** moment.
> **No → `causes`.** The entry is *asserted*. It persists, and lands in a **later** moment.

Water you have stopped heating stays boiled. That is inertia, and it is why a zero-delay cause is
still not an implication: the two cannot be merged by setting the delay to zero.

`<R2>` in §12 is the argument for keeping both. *Cloudy morning likely implies rainy afternoon* passes
the persistence test as `implies` — learn it was not cloudy and the rain claim goes with it — but the
surface wording reads just as easily as causal, and clouds do not cause the afternoon's rain; a front
causes both. Written as `causes`, the backward reader produces **a plan to make it rain by making it
cloudy**. The two-connective split is precisely what makes that plan unwritable.

### Neither connective needs engine support

This is what §5's test demands and it is worth showing rather than asserting. The two connectives
differ in exactly one respect: **which moment the consequent's entries are deposited in.** Same moment
for `implies`; a successor for `causes`.

The write operation is told where to deposit — that is the register, §4's item 3. It is not told which
connective was involved and has no way to ask. So the connective is consumed by the *rule that applies
rules*, which is bundled data:

```
<F-implies> = causes(
    given  +rule(?r),  +conn(?r, implies),  +matched(?app, ?r, ?m)
    then   +deposit_into(?app, ?m) )

<F-causes> = causes(
    given  +rule(?r),  +conn(?r, causes),  +matched(?app, ?r, ?m),  ?m' = succ(?m)
    then   +deposit_into(?app, ?m') )
```

A third connective is a third rule of the same shape. That is §5's *rows, not branches*, and it is
also the whole content of the older claim that a connective is a table entry.

The honest caveat is §5's wall: these rules read a *reified* rule, and reification stores generic
patterns. Matching a goal against a stored pattern is the operation no rule can perform. The forward
direction above is safe because it never matches a pattern — it dispatches on `conn` and hands the
moment along. The backward direction is not, and §21 records it.

### What is not a connective

Interval relations — *before*, *during*, *overlaps* — are ordinary facts about moments and spans,
which are already nodes. Adding them to a closed set would buy nothing and would start the
multiplicative growth §15 and §16 are designed to avoid.

---

## 15. Time

*Saying when, in the world's terms.*

**An action is not a new kind of thing.** An action is an event; an event is a moment; and
`heat(?a, ?w)` is a fact that holds over an interval. An action therefore enters a rule's antecedent
as an ordinary member, and *to execute* means **make this event-fact true**. There is no action
construct, no operator schema and no plan-step type alongside the rules.

Expressing *…and it boils five minutes later* takes three decisions.

**1. Say which endpoints.** *The heating takes five minutes*, *boiling starts five minutes after
heating starts* and *boiling starts five minutes after heating stops* are three different rules that
plan differently. The timing member therefore relates **named endpoints** — the end of `<A>` and the
start of `<B>` — never a bare scalar.

**2. It is a constraint, not a number.** A closed interval, a lower bound alone, *eventually* and
*unknown* must all be sayable, or R6's problem returns one level up as precision-by-silence. Absent
timing means unknown timing, and that is both legal and readable.

**3. It is a fact about the rule, not a third member of the connective.** This keeps the connective
binary; lets the delay be genuinely absent rather than defaulted; and lets two timing claims coexist
with different sources — *the manual says five, I measured seven* — which is real and unsayable if
the delay is a slot.

| | timing as a connective member | timing as a fact about the rule |
|---|---|---|
| not leaking | ❌ an absent delay defaults to something nobody stated | ✅ absent means absent |
| not lossy | ❌ one delay per rule, no provenance | ✅ several claims, each attributed |
| readable | ⚠ | ✅ *which rules are slower than five minutes* is a query |
| composable | ❌ the connective's arity varies | ✅ timing joins independently of the connective |

Timing is read in both directions, which is the payoff. **Forward**, it says when to expect the
effect, and therefore when its absence is a **deviation** rather than merely patience — this is what
§18 matches against. **Backward**, it is a **filter**: needing boiling water within two minutes rules
this rule out of the plan. A rule with no timing expresses neither.

Because waiting is an action like any other, this is also how a precondition the agent cannot *make*
true gets planned for. *It must be a Tuesday* is achievable at a price of up to seven days, and the
price is a timing constraint — sayable, absent when unknown, and compared against the deadline. That
is what §12 leans on when it refuses to mark a member unachievable.

### Three times, and only one ordering

Time shows up in three places, and it is worth being explicit that this is not three time systems.

| | what it is | where it lives |
|---|---|---|
| **about-when** | the stretch a claim concerns | the entry's **locus** |
| **believed-since** | when the agent came to think so | the entry's **deposit moment** (§8) |
| **event description** | *afternoon*, *Tuesday*, *morning* | **members of a proposition** |

The first two are §10's two indices. The third is the one that needs discipline, because it is already
in use — `cloudy(?day, morning)` in `<R2>`, and `tuesday(?d)` in §12 — and left unexamined it would
be a second ordering competing with succession.

It is not one, and the rule is:

> **Calendar terms denote. The chain orders.**

*Afternoon* is a **name for a stretch of the chain**, resolved against the clock stamp §7 puts above
succession. It is not an ordering relation and nothing may compare two calendar terms directly; to ask
which came first is to resolve both to spans and compare endpoints, which §11 already provides. A
vocabulary that ordered calendar terms among themselves would be §7's warning realised — two orderings
that agree by convention and drift without detection.

This is what makes reported speech expressible, which the timing member alone could not do:

```
<e1> = entry( <M9>,        says(anna, <p>),  + )      Anna spoke, at the moment of speaking
<e2> = entry( <afternoon>, rain,             + )      grade(<e2>, possible)
                                                      licensed_by(<e2>, <e1>)
```

`<e2>` is deposited now, is about the afternoon, and is believed on Anna's word — three different
times and one authority, none of which needs a construct that does not already exist.

### Acting is a channel read the other way

Channels carry the world in (§17). Acting carries an intent out, and needs no new construct for the
same reason an action needs none: a rule concludes `+doing(p)` like any other fact, and the machinery
carries it past the boundary because a boundary is anchored and a rule is generic.

Two things about the write that follows, both found by building it:

**The agent asserts the act.** *To execute means make this event-fact true*, so having acted, the
agent writes `+heat(anna, kettle)` — licensed by the doing, not by any report. That is not a claim
about the world's response. It is what gives the rules something to apply to, and it is what gives the
expectation of §18 something to be disappointed by. Without it the agent emits an intent into silence
and nothing downstream ever happens.

**A description cannot be acted on.** `+doing(heat(?a, ?w))` is refused: an intent with an unbound
member names no particular act. This is §12's achievability arriving where it belongs — not as a mark
on a rule's member, but as a condition at the one place effects leave the agent.

### What a channel reports is signed

An arrival needs a sign, and a proposition has none — only an entry does (§8). So *the gauge says it
is not boiling* has nowhere to put the negation. Writing `−says(gauge, p)` says the gauge stayed
silent, which is a different fact and not the one observed.

The shape in use is `says(channel, proposition, sign)`, with the entry always positive: the channel
did speak. That puts a sign inside a proposition, which §18 warns against, and it is the same
compromise reification makes when it stores a rule's signed members.

**Two better answers exist and neither is built.** An arrival should be a **moment** — a report is a
signed delta, and trust is then a rule relating two moments rather than a rule per sign; that needs
§12's skeleton. Alternatively §9's open question settles the other way and negation becomes a
wrapping proposition, at which point the third member disappears on its own. Until one of the two
lands, a corpus needs one trust rule per sign.

---

## 16. Modality

*Saying how strongly.*

Four different things get called *possibility*, and they must not share a slot.

| | what it is | where it goes |
|---|---|---|
| **strength** | how often the effect actually follows | a grade on the **entry** |
| **confidence** | how far the agent trusts where this came from | a grade on the **source** (§17); moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules: `unless`, `overrides` |
| **achievability** | whether *this* agent can bring it about, now, within budget | **nowhere** — derived at read time from capabilities, budget and the rule set (§12) |

The fourth is the one with no storage at all, and that is the point: it is relative to the reader, so
any place to put it is a cache of a derived value.

Collapsed into one number, `0.6` means three things at once, and combining two such numbers is
arithmetic nonsense. Defeasibility is the load-bearing one for reasoning — *unless the front has
already passed* — and it needs **no numeric apparatus at all**: it is the same precedence machinery
that makes the boss's rule beat the vice's.

**Grades are per-entry, not per-rule.** One rule has consequences of different strength: heating boils
the water (certain) and scorches the pan (unlikely). A rule-level grade cannot express that; it is at
best shorthand for *all entries the same*.

**Confidence is a property of the source, not of the rule.** *How sure am I of this rule* and *how
sure am I of this sensor* and *how far do I trust this speaker* are one question asked of three
sources, and §17 makes every entry name the source it arrived through. Rule-confidence is then the
case where the source is the knowledge base. One mechanism covers all three; a grade slot on rules
would cover only the first and would have to be reinvented for the other two.

**Grades are ordinal, not probabilistic.** Real probabilities require independence assumptions that
cannot be stated in the graph, so multiplying them leaks silently — the product looks like a
measurement and is an artefact. Ordinal grades compose by **weakest link**. A numeric member may sit
*beside* the grade where its own provenance is a member — *from 300 observations* — but never in
place of it.

**Weakest link is sound down a chain and silent across a convergence**, and the two cases must not be
confused:

| | shape | what min does |
|---|---|---|
| **chain** — a source I half-trust, reporting a rule that only usually holds | sequential attenuation | correct, and correct as an *upper bound*: no conclusion is surer than the weakest step that produced it |
| **convergence** — two sources independently reporting the same thing | corroboration | **wrong**: belief should rise, and min holds it flat |

The honest cost is the second row. Two independent *likely*s ought to amount to more than *likely*.
Ordinal grades do not accumulate evidence, and the right place to fix that is **counting over
episodes**, not arithmetic over grades; §21 records it as unsettled. What the design must not do
meanwhile is let the chain case silently stand in for both.

**The grade a rule authors is a contribution, not a verdict.** §12's consequents carry per-entry
grades, and those are one link in the chain, never the answer. The grade of the deposited entry is
`min(authored, support)`. Without that, a rule that says `certain` on the strength of a source graded
*possible* launders a weak input into a strong output, and the weak link vanishes from exactly the walk
this section relies on. **A rule states how strongly it would conclude, given its premises. What its
premises were worth is not its to say.**

Grade is orthogonal to the `?` sign. A `?` entry says *this changed and I cannot say to what*; a
`possible` grade says *this might become true*. Different ignorance, different slot.

### Where the grade lives

Not on the proposition node — and not for reasons of cost.

> A grade stored on a proposition node is **a cache of a derived value**. *Rain is likely* holds only
> given the support that produced it, so when the support changes the tag must be invalidated. General
> invalidation over a web of dependencies is a truth-maintenance system: a second machinery, with its
> own consistency problem, running underneath the first. **An index over what was asserted is
> storage; a cache of what was derived is a truth-maintenance system.**

A second, independent reason: **a tag is a separate read.** Reading a fact and reading its grade are
two operations, so the grade can be obtained without the fact or the fact without the grade — and an
ungraded conclusion reads as certain.

This is **not** a leak. Nothing unauthored is in the graph: the fact was asserted and the grade is
attached, and the extra content — *certainly* — is manufactured by a reader's convention. §2 says why
that is the machinery's question rather than the shape's. But it is still the machinery's question,
and it has an answer here: **the grade must ride the node that match already has to return.** An entry
cannot be matched without its sign, because the sign is a member; put the grade there and it cannot be
matched without its grade either. One read, or none.

That is the difference between a discipline and a structure, and it is available only because the
entry exists anyway.

**Every fact already has a node that records where it came from — the entry of §8. The grade goes
there.**

| the fact came from | the node that already exists | it carries |
|---|---|---|
| a rule applying | the application | the rule's per-entry grade |
| someone saying so | the utterance | how firmly they said it, and their authority |
| observing | the sighting | sensor confidence |
| a supposition | the moment's licence | the grade of what was supposed |

The entry had to exist anyway, because the **sign** has nowhere else to live — edges carry no facts.
So the grade slot costs nothing structurally. A shape that absorbs a new requirement without growing
is a shape that was right rather than convenient.

*If §9's open question resolves toward wrapping, this argument needs re-running: an entry with two
members still exists, and the grade still rides it, but the "sign is already a member" step is gone.*

### Superseded, not invalidated

If a stored grade is a cache, is a stored derived *fact* not also a cache? No — and the difference is
the reason the whole design is dated.

> **A dated derived fact needs no invalidation.** At `M7` the agent recognised that they were taking
> turns. At `M12` something writes the opposite. The `M7` entry stays true **of `M7`**. Nothing is
> retracted, nothing propagates, and *are they taking turns?* resolves through the chain to the most
> recent entry.

The demanding case is not the world changing but the agent changing its mind about a time that has
already passed — *at `M12` I conclude they were not taking turns at `M7` after all*. That is a second
entry with the **same locus** `M7` and a **later deposit**, and the property still holds:

| the question | the walk | the answer |
|---|---|---|
| what do I now think about `M7`? | from `M12`, locus `M7`, latest deposit | the revision |
| what did I think at `M7`? | from `M7` | the original |

Nothing was invalidated, nothing propagated, and both answers survive — which is what makes *why did
you change your mind?* a query rather than an archaeology. **The property is a consequence of §10's
two indices, not of writes always landing at now.**

One line covers modality and recognition together:

> **Store it on the entry — dated, signed, attributed, superseded.
> Never on the node — timeless, and therefore requiring invalidation.**

### Supposition and weak connection are different problems

The word *likely* covers two things, which is why *tag it or guard it* feels like a forced choice:

| | *I am supposing this — what follows?* | *this generally holds, weakly* |
|---|---|---|
| shape | a **moment** you enter and leave (§7) | a **grade**, recorded on the entry when the rule applies |
| how many | few, deliberate | many, independent |
| nesting | free — a path in the predecessor tree | does not nest; composes by weakest link |
| isolation | already enforced — a read cannot reach into a moment except through the chain | not an isolation problem at all |

Keeping these apart is what prevents combinatorial explosion — **if** the unit is a *subset*. Twenty
independently uncertain facts would be a million moments only if every combination were a moment.

### Supposing is how modality composes — measured

That objection does not survive the distinction between a frame per **subset** and a frame per
**derivation**, and `python -m ugm.modality` measures the difference. Modality can be a **term** —
`likely(p)`, a wrapping node, the same construction as `on(a, b)` with one arm rather than two — and
then a hedged fact is crossed by *entering* it:

> **Unwrap on the way in. Re-wrap on the way out.** Inside the frame the assumption is an ordinary
> fact and the ordinary rules apply to it by ordinary matching. What crosses back is `likely(q)`, a
> claim about what was concluded under the supposition — never `q`.

Three things this buys that a grade cannot, none of them arguments:

| | grade on the entry | term, supposed |
|---|---|---|
| a **rule** can ask *is this merely likely* | no — a grade is not a term, so no antecedent can name one | yes |
| the guard **holds** — nothing acts on the unwrapped conclusion | no; a grade annotates a conclusion the actor still sees | yes, structurally |
| it **nests** — `thinks(anna, likely(rain))` | no; a grade has no place inside a term | yes |

The cost is a frame per derivation, which is linear. The alternative — a *lifting* rule that rewrites
`likely(X)` into `likely(Y)` over reified rules — costs one rule instead of a frame, and fails: it
binds against a rule's **pattern**, so it fires only where that pattern is ground, and real corpora
are mostly generic rules. That is §5's wall again. Supposing has no such limit because nothing is ever
mentioned.

**Containment is free rather than enforced.** The frame's seat is a *successor* of the caller's, so
the caller's walk cannot reach it. That is §20's containment gate, and it is §10's ancestry doing the
work — which is why at-or-before must be a real ancestry test and not a depth comparison, since
supposing forks by construction.

**What is still true of grades.** Weakest link is computed once, by the gate, over the entries match
consumed, and no author can forget it. That is worth keeping for the ordinary attenuation of a chain.
The two are not rivals: the grade is what the gate computes, the term is what a rule can reason about.

**Use moments where the agent *chooses* to suppose, and where a hedge must be reasoned about; use
grades where the world is merely weakly connected and nobody needs to ask.**

### Scoring

| | (A) grade on the proposition node | (B) a guard node per uncertain fact | (C) moments + graded entries, weakest link computed |
|---|---|---|---|
| not leaking | ❌ a grade on a timeless node is *likely* said of no occasion and every occasion at once; the author meant *likely given this support* | ⚠ the guard says uncertain-in-general, so it leaks the same way, more loudly | ✅ a conclusion drawn in a moment **is** in it; the grade is recomputed from support |
| not lossy | ❌ a number with no premise | ⚠ says *that* it is uncertain, not on whose word | ✅ speaker, rule and sighting all survive |
| readable | ⚠ readable and stale | ⚠ | ✅ *which conclusions rest on something merely possible* is a walk |
| composable | ❌ two tagged facts combine to *what?* | ❌ every consumer must handle both shapes, guarded and bare | ✅ weakest link over the support chain |

Separately from the scoring — because it is not a property of these shapes but of the machinery that
reads them — (A) and (B) differ in whether the grade **can be obtained without the fact**. Under (A)
it can, and an ungraded read is the default one. Under (C) it cannot, because the grade is a member of
the node match already returns. That is the argument above about tags and structures, and it is why
(C) wins by more than the table shows.

(B)'s failure has no middle setting, which is why it is worth naming: **optional guards mean consumers
handle two shapes and forgetting returns; mandatory guards mean an extra node and an extra hop for
every certain fact in the system.**

But the guard instinct is right about one thing — **forcing the handling**. A computed grade compels
nothing, and *do not act on a merely-possible fact without acknowledging it* is a real requirement. It
belongs at **the one place effects leave the agent**: check the grade of what licenses an **action**
at the dispatch point, where the set is small and known, rather than making a million reads cross a
guard in order to catch the one that matters.

### What (C) costs

* *How likely is this?* becomes a **walk, not a read** — the same shape and the same cost as reading
  a fact at all (§10). Accepted as a consequence of dating everything, not paid separately.
* **The support trail becomes load-bearing for correctness, not only for explanation.** A write that
  loses its attribution does not merely become unexplainable — it becomes **falsely confident**,
  because a missing support link removes a weak link from the minimum. This is what promotes R5 from
  a nicety to a soundness condition, and it is why §4 puts the stamp on the floor.
* Cycles in the support chain need the same termination care as any walk over derived structure.

### Does the design run out of dimensions?

The worry behind every new distinction is that it needs a new dimension of the representation. It does
not. Everything spent so far:

| | why it could not be a node |
|---|---|
| **identity** | *this node is that node* is not a relation between two things; it is the precondition for there being two things |
| **connection** | an edge |
| **order among connections** | *the second member* — position is not a thing in the world |

Everything added since — type, sign, licence, grade, time, authority, span, commitment — is a
**member of a node**, and cost no dimension.

> **You run out of dimensions only if you try to say something that is not about anything.**

If a candidate distinction can be phrased as *X stands in relation R to Y*, it is structure, and
structure is nodes. Order is the one thing that genuinely cannot be, which is why the substrate
provides it and nothing else.

---

## 17. Provenance — channels, frames and the gate

*Saying who says.*

Every claim is made through an entry (§8). So: are rules **augmented** to speak about entries, or does
the **machinery** apply rules to entries? The machinery — and the alternative is not merely costly, it
cannot be written.

### Augmentation is a category error

```
+on(a, b)      ⟶      entry( <the moment I am in> , on(a, b), + )
                             ^^^^^^^^^^^^^^^^^^^^
```

**The locus is an indexical.** A rule is generic: variables, and no anchored predecessor. An entry is
anchored. A rule that named a locus would be about that one occasion and could not be reused. So
augmentation cannot produce a whole entry — only one with a hole in it. And **a hole that the
machinery fills at run time is the machinery doing the work anyway.**

It buys nothing, and costs four things:

1. **It is a translation, and translations must commute.** Every explanation would show the rewritten
   rule rather than the rule the author wrote. Since the trail *is* the explanation (R5), this is the
   expensive loss.
2. **One fact in two shapes.** Authored and augmented forms must be kept in sync, and answering *why*
   means un-augmenting.
3. **It freezes the resolution policy into every rule.** The property being bought here is that *the
   machinery can change what a read means without editing a single rule*. Augment, and a policy change
   means rewriting the corpus.
4. Every rule triples in size in plumbing, which makes R4's questions harder to answer, not easier.

### The split

| the rule says | the machinery supplies |
|---|---|
| `+on(?x, ?y)` in the antecedent | walk the chain for entries naming that proposition; return those signed `+` |
| `+boiling(?w)` in the consequent | mint the entry; stamp locus, licence, source and grade from the frame and this application |

> **The rule's members are what the author knows. The entry's members are what the application knows.**

Locus, licence, source and grade-at-this-application do not exist until the rule runs. That is the
whole split.

| | (A) augment the rules | (B) authors write entries natively | (C) the machinery absorbs it |
|---|---|---|---|
| not leaking | ❌ explanations show the rewrite, not the rule | ❌ an author supplying a deposit stamp can date a claim to when it was not held | ✅ every entry is stamped by the write that made it |
| not lossy | ❌ two shapes; *why* must un-augment | ✅ | ✅ |
| readable | ❌ three times the plumbing per rule | ❌ every rule is plumbing | ✅ the rule reads as written |
| composable | ❌ resolution policy frozen at augmentation time | ⚠ | ✅ resolution can change without touching a rule |

(A) additionally cannot be written at all, per the indexical above.

### The gate

An entry is both a mechanism and a node a rule can point at. Reading is how *a claim Anna made
outranks one Bo made* gets stated at all. Writing is where soundness lives, because §16 makes the
support trail load-bearing: a write that loses its attribution does not merely become unexplainable,
it becomes **falsely confident**, since a missing support link removes a weak link from the minimum.

The requirement that follows is narrower than it first appears:

> **No write bypasses the stamp.**

*Only the machinery may write entries* is one way to achieve that, and it is stronger than necessary.
What must be impossible is an entry whose provenance is **absent or false**. What need not be
impossible is an entry a rule caused to exist — every such entry arrives through the gate and leaves
it stamped with the rule that caused it, which is not forgery but the ordinary record.

Note the division against §4. The **stamp on the mint** is floor: unconditional, nameless, and not
something a rule reads. The **gate** is the bundled convention that turns that stamp into vocabulary —
locus, licence, source, grade — so that the agent can reason about its own provenance. Remove the
convention and the guarantee remains but the agent goes blind to it; remove the floor item and the
convention is forgeable.

Two things this distinction rescues, which the stronger prohibition forbids by accident:

**Backdating is not the same as claiming about the past.** Backdating is lying about when a claim was
made — a false stamp. Writing now, honestly, about an earlier time is a **past locus with a present
deposit**, and the record reads *at `M12`, by this rule, I came to think it rained at `M7`*. §10's two
indices make the second sayable and the first still impossible, because the deposit is structure and
not an argument.

**Trust is a rule, not a hard-wired intake.** *The user says it is raining* becomes *it is raining* by
an ordinary rule that the agent can be asked about, argue with and override. An intake path that wrote
the second directly would be the genuinely unsafe design, and it is what a blanket
rules-may-not-write encourages.

### Channel is not authority

Every entry names where it arrived from, and that has two layers which must not be fused:

| | what it is | can it be wrong |
|---|---|---|
| **channel** | the intake path — this socket, this sensor, the knowledge base | no: mechanically observed, like a sensor that cannot misreport its own reading |
| **authority** | who is taken to have spoken, and what their word is worth | **yes** — an ordinary claim, gradeable and defeasible |

The knowledge base is a channel like any other. Reading it faithfully is guaranteed; what it **says**
is as contestable as ever, which is what §12's `by(<R>, boss)` and `overrides(<R1>, <R2>)` depend on.
Fusing the two would make authority unforgeable by fiat, so that anyone reaching the right socket
would thereby be the boss.

### Frames

A rule cannot name a locus, and the machinery must supply one. **The frame is what it supplies it
from.** A frame is the reasoning in progress — a process node, and therefore a fact on the graph,
which is R7 discharged for the machinery itself.

A frame carries two things:

| | |
|---|---|
| **seat** | the moment its writes are deposited in — *where I am standing* |
| **topic** | the locus its writes are stamped with — *what I am reasoning about* |

Normally they coincide, and that is the case §8 describes. They come apart exactly twice: reasoning
about the past, where the topic is an earlier moment and the seat is now; and reasoning under a
supposition, where the seat is inside the supposition.

### Where the agent is standing is not where its reasoning is

The register says where the machinery is working. It does **not** say where the agent is, and
conflating them is a mistake with a specific, ugly consequence.

The world does not stop talking while the agent hypothesises. If a report is deposited wherever the
register happens to point, then a report arriving during a supposition lands inside it — and leaves
it re-wrapped, so the agent's record of what a channel said becomes `likely(says(...))`. The channel
record, which this section calls **unforgeable**, has been turned into a hedge by a hypothesis it had
nothing to do with, and the plain record is unreadable at the agent's own seat. That was true of the
implementation until it was measured.

> **A channel delivers to the agent, not to the agent's current hypothesis.**

Two things follow, and the second is the one worth stating as a rule.

**The agent's own seat is derived, not held.** It is the outermost frame in the register's ancestry
that is not a supposition. §4 allows exactly one privileged pointer, and a second register for *where
the agent is* would have been the easy wrong answer — the position is recoverable from the forest, so
it does not need to be stored, exactly as ancestry and scope are not stored.

**Delivering forks the chain.** The report lands on a **successor** of the agent's own seat, which is a
sibling of the supposition's branch rather than an ancestor. Appending it to the seat the supposition
already descends from would be the tempting shortcut and is wrong twice over: deposit order is
position along the walk (§10), so a report arriving now would read as *older* than everything
concluded since; and the hypothesis would silently acquire evidence it was not entered with. A
hypothesis is entered from a state of the world, and it keeps that state. What the world said
afterwards is on the other branch, waiting at the seat the agent returns to.

That gives the whole of what the gate does:

> **Proposition and sign come from the rule. Locus, licence, source and deposit come from the frame
> and the clock. A rule may not name the second four.**

| stamped | taken from |
|---|---|
| **locus** | the consequent's bound locus if it has one (§12), otherwise the frame's topic |
| **deposit** | the frame's seat |
| **licence** | this application: the rule, and the entries match consumed |
| **source** | the channel this arrived through |

A frame is `frame(seat, topic)` — a node with two ordered members, structurally identical to §11's
`span(start, end)`. It reserves no engine name. What the engine holds is §4's **register**: which node
is the current frame. That is a pointer, not a vocabulary item, and it is the only privileged thing
here.

> **The machinery is written in the language it interprets. Only the register is privileged.**

Two properties fall out rather than being enforced. **Hypothetical containment is structural** — a
conclusion drawn inside a supposition cannot land outside it, because the locus was never the rule's to
give. And **forgery stops being a category**: nothing is prohibited, everything is stamped.

### Entering and inspecting

Two operations look like they need primitives and neither does.

**Inspecting is matching.** Match unifies a generic chain against an anchored one, and nothing
requires the anchored chain to be the one you are standing in. Reading another frame's conclusions is
match with an explicit anchor, and it changes nothing.

**Entering is writing.** Moving the seat is writing a fact about a process node, stamped and dated
like any other write, so the trail reads *this reasoning moved to `M7` and then concluded*. A rule can
therefore relocate its own seat — which is not a hole but the mechanism by which deliberate reasoning
about the past happens at all, and it is auditable precisely because the move is itself an entry.

One requirement is load-bearing:

> **Reading never moves the seat. Inspecting a frame is not entering it.**

Otherwise weighing two hypotheses would adopt both.

### Frames form a forest, and nothing leaves one

Frames are not a stack. A stack assumes one live frame and a return to the caller, and the case that
breaks it is the ordinary one: **two hypotheses under comparison are siblings, both alive, neither the
caller of the other.** Frames form a forest; what looks like a stack is the ancestor path of whichever
frame is in focus, and ancestry is derived, so there is nothing to maintain. This is §7's *nesting
needs no mechanism*, one level up.

A frame ends when its goal is discharged, its budget is spent, or arbitration moves on — and it ends
the way every bounded thing in this design ends, with **a result and a state**: discharged, exhausted
or abandoned. That is §9's `−` against no-entry, §13's bound, and §19's two silences, arriving a fourth
time.

What does a conclusion look like on the way out? It does not come out.

> **Conclusions stay at their locus. What crosses is a claim *about* the frame, made outside it.**

Copying a conclusion out and re-qualifying it is the alternative, and it fails on this design's own
terms: it makes one fact exist in two shapes, which is the objection to augmentation above, and it
needs invalidation the moment the supposition is discharged differently, which is what §16's dating
exists to avoid. So a caller that has learned something from a scenario writes a **new** entry at its
own seat whose proposition is about the scenario — `yields(<S1>, +boiling(w))`, or
`preferable(<S1>, <S2>)`.

Comparing two hypotheses is then inspecting both and writing a preference; neither is adopted.
**Adopting** one is a separate, deliberate, licensed write — the same shape as deciding to trust a
channel, which is the point at which *the user says it is raining* became *it is raining*.

### Costs

* **A bug in the gate is systemic** — every fact in the system gets the same wrong provenance.
  Mitigated by it being one place, which makes it one check.
* **Matching becomes a chain walk rather than a lookup**, and that walk now sits on the rule-matching
  path, not only on reads.
* **Matching must record which entries it matched.** Otherwise *because a was on b, on Anna's word*
  has no answer. This is not overhead: it is half the trail, and it is what makes a misbehaving rule
  distinguishable from a misresolving chain.
* **Every seat move is a write**, so deliberate reasoning about the past leaves a trail proportional to
  how often the agent shifts its attention, not to what it concludes.
* **Nothing stops a frame being seated somewhere useless.** A seat that is not an ancestor of its topic
  is as meaningless as §11's inverted span, and takes the same remedy: check it where the frame is
  minted, while the mistake is still attributable.

---

## 18. The machinery's own state

*Saying what I am doing.*

This section is R7 applied to the agent itself, and it is the largest single group of conventions in
the design: goals, plans, commitments, expectations, surprise. Under §5's test every name here is a
convention, and each currently has an interpreter branch behind it. That is the debt Part I names.

### Surprise is a match

> **Surprise is a match.** It is an *expected* entry and an *observed* entry that disagree.

That is the entire mechanism, and it is the sharpest illustration of R7. If the agent's expectations
live in interpreter variables, an expectation is unmatched not because the rule is weak but because
there is nothing there to match. Three obligations follow.

**1. Forward application deposits a predicted moment.** Applying `causes(A, B)` at `M3` mints a moment
whose predecessor is `M3` and whose licence is *R applied, predicted*, carrying `B`'s entries, plus a
due-time derived from §15's timing member. Without the deposit there is nothing to be surprised
against.

Note what this avoids: a bespoke relation like `expected(+boiling(w), by t+7)` is not writable in this
vocabulary at all, because it puts a **sign inside a proposition**, and a sign is a member of an
entry. The moment form is not a workaround for that restriction — it is better, because it makes
surprise a **comparison of two moments**, which is an operation the design already needs.

**2. The continuation is a moment.** What the agent is doing, where it is in it, and what it is
waiting for are signed entries — not a stack frame.

*Stack frame* here means the interpreter's: opaque, owned by the runtime, and unreachable by a rule.
§17's frames are the opposite of that in every respect — process nodes, readable, writable, and
selectable — which is why they can be preempted and an interpreter's cannot. The word is unfortunate;
the distinction is the whole of this section.

**3. Surprise is an ordinary rule that wins on precedence:**

```
<S> = causes(
    where  ?t' = now
    given  +predicted(?p, ?m),  +due(?p, ?t),  after(?t', ?t),  +deviates(?p, ?actual)
    then   +goal(explain_failure(?p)),  −committed(?proc) )
```

**There is no interrupt mechanism.** Preemption is `<S>` outranking the rule that would have continued
what the agent was doing — which is possible only because *continue what you were doing* was itself a
selectable rule. That is exactly what a stack frame is not.

### The precedence claim is load-bearing, not decorative

Built without it, the loop does not merely respond slowly — it never responds at all, and the failure
is worth recording because it is not the one you would predict.

An agent heats water and expects it to boil. The gauge reports it is not boiling. Now two rules apply
forever: the causal rule re-concludes `+boiling` because its antecedent still holds, and the trust
rule re-concludes `−boiling` because the gauge still said so. They alternate. The surprise rule is
never selected, because arbitration prefers the rule authored first, and **the oscillation starves
it**. Nothing is wrong with any of the three rules; the deviation is even noticed and recorded. It
simply never gets acted on.

One authored fact fixes it:

```
overrides(<why>, <boil>)
```

That is this section's claim, exactly: preemption is a precedence relation over ordinary rules, and it
works because the rule that would have continued is selectable and therefore defeatable. The other
half is that being overridden must mean **not applying at all** (defeat), never merely applying
second, or the loser simply re-asserts on the following tick and the winner is quietly undone.

**Defeat is about whose antecedent holds, not about who still has work to do.** Filtering out rules
whose conclusions are already written must therefore happen *after* defeat, not before — otherwise the
winner disappears the moment its conclusion is present, and the loser is left unopposed.

The general shape, since it will recur: **a contradicted expectation does not stop being re-derived.**
Nothing in the design retracts the rule that produced it, so something must outrank it. That something
is authored, which is the point — a strategy defeated by a statement in the knowledge base rather than
by an interpreter.

### Procedures as data

A procedure is a committed order, and a committed order is precisely the thing that cannot be
preempted midway: if *to find an answer, look for causes* is control flow, step three owns the agent
until it returns.

> **Procedures exist, but as data that biases selection — never as control flow that owns the loop.**

`committed(?proc, step_3)` is an entry in the current moment that raises the precedence of continuing.
It does not remove the alternatives. So commitment is real — the agent does not dither — it stays
preemptable, and *dropping* it is a **write**, which means the agent can be asked why it abandoned
something.

### Plans carry their bindings

A backward search's working state is facts, not interpreter variables. This is the row that could have
been avoided and should not be: putting bindings on a `plan` node is R7 applied to the machinery's own
working state, and it is what makes *why did you think that goal was met* answerable.

It was also found by building. Two sibling subgoals — `tap(?t)` and `under(kettle, ?t)` — will each
report satisfied against *different* taps unless the bindings that satisfied one are visible to the
other. A plan node carrying its bindings is what makes them one plan rather than two coincidences.

### Requests do not leave a frame

The machinery's vocabulary is **requests and reports, not claims about the world**. A rule concludes
`+suppose(p)`, `+goal(p)` or `+doing(p)`, and the machinery does what a rule cannot: open a frame,
read a rule backwards, or carry an intent past the agent's boundary. Each needs something anchored — a
locus, a match, a channel — that a generic rule cannot name.

One consequence is easy to miss and was found by running: **nothing in this vocabulary may carry out
of a frame**. A request to suppose is not a claim about the world, so there is nothing for §16's
wrapper to qualify — and carrying one out produces `likely(suppose(...))`, which the rule that crosses
guards then crosses, so the machinery supposes its own bookkeeping without end.

### Strategies are defeasible

```
<M> = causes( { +goal(?g, explain(?f)) },
              { +goal(find(?r)), +constraint(?r, causes(_, {+?f})) } )
```

Because that is a rule, `overrides(<M>, <M2>)` and `unless(<M>, +domain(?f, social))` are sayable, and
**a strategy becomes defeasible like any other claim**. A strategy written as code cannot be
overridden by a statement in the knowledge base, and that asymmetry — not interruptibility — is the
larger cost of putting machinery outside the world the agent reasons about.

### Reflection is demanded, not continuous

Meta-rules are consulted only at **named decision points the interpreter already reaches**: which rule
to apply, what to do on failure, what to do on surprise. Never between arbitrary steps. Each decision
point either receives a meta-answer or falls through to §4's total step, so no decision hangs. Without
this discipline, meta-cost is paid on every step and the tower never bottoms out in practice even
though it does in principle.

Arbitration is the one that is easy to get wrong. A meta-rule that decides which rule to apply must
itself be selected, and that regress happens *at run time*, not at design time. Therefore:

> **The bottom-most arbitrator is a lookup over an authored precedence table that always returns and
> never searches.**

Reflection may be arbitrarily deep; the final tiebreak may not be reflective. That is the
stratification condition for *selection*, and it is the same shape as §6's stratum 0 for *reading* and
§19's recall for *proposing*: each regress ends in a function rather than a search.

### Scoring, and the price

| | (A) strategy and continuation in the engine | (B) all rules, no floor | (C) rules + §4's floor + a total step |
|---|---|---|---|
| not leaking | ❌ engine decisions have no premise and appear in no explanation | ❌ regress; never grounds | ✅ every step cites its rule; the floor is five named things, none about reality |
| not lossy | ❌ *why did you stop?* has no answer | ⚠ | ✅ deposits, commitments and abandonments are all entries |
| readable | ❌ strategy invisible to a query, undefeatable by data | ✅ | ✅ *which strategies are about explanation?* is a query |
| composable | ❌ two authors cannot add a strategy | ⚠ meta-rules cannot be ordered | ✅ new strategy means new rules; ordering means precedence |

**(C)'s price, named:** every step costs a selection, and a badly authored precedence table produces
dithering that reads as a bug in the rules rather than in the table. Both are measurable —
**selections per useful write**, and **commitments dropped per commitment made**. Those two counters
belong in the interpreter from the first version, not added after the symptom appears.

---

## 19. Recall

*Which rules come to mind.*

Recall is where the agent's experience lives: the right rules coming to mind at the right moment is
what expertise consists of.

Earlier drafts called it a primitive. It is not, and §4 says why — a learned proposer is the opposite
of a primitive. It is the design's most consequential **policy**, and naming it correctly makes its
properties choices to defend rather than facts to accept.

The three selection steps have **opposite requirements**, which is why they are three:

| | **recall** | **match** | **arbitrate** |
|---|---|---|---|
| job | which rules come to mind | do they actually fit | which one, now |
| status | **convention** — a bundled policy | **floor** (§4 item 2) | totality is floor; the table is convention |
| complete? | **never**, by design | over what recall offered | over what matched |
| total? | — | — | **must always answer** |
| authored or learned? | **learned** | mechanical | **authored** — precedence |
| failure mode | a rule you needed never surfaced | — | dithering, or a hang |
| cost of being wrong | recoverable: a worse plan, or a surprise later | — | a wrong action |

Judgements of what is worth attempting live here too. *Don't plan to make it Tuesday* is not a fact
about the rule (§12) and not a prohibition (below); it is a learned bias about which subgoals are worth
expanding — which is to say, about which rules come to mind when reading backwards. It belongs in the
step where being wrong costs a worse plan rather than a wrong action.

### Why experience belongs in recall specifically

Two structural reasons, neither of which is an appeal to cognitive plausibility:

1. **It is the only step where being wrong is recoverable.** A missed rule costs a worse plan or a
   later surprise — both of which the machinery already handles. A wrong arbitration costs a wrong
   *action*. Put learning where errors are survivable.
2. **It is the only step with no authored ground truth.** *Which rules should have come to mind?* has
   no answer other than *the ones that turned out to matter*, so it can only be learned. Arbitration
   has the opposite property: `by(<R>, boss)` and `overrides(<R1>, <R2>)` **are** the ground truth, and
   learning them instead of reading them would be wrong.

### What incompleteness costs immediately

Once recall may miss, **"no rule applies" is ambiguous**: either nothing applies, or nothing came to
mind. That is §9's distinction between *absent* and *no entry*, one level up, landing on the machinery
that reads it.

> **Recall returns a set plus a state, never a set.**

The state is cheap to compute from the wrong thing (*did I find anything?*) and expensive from the
right thing (*is this situation familiar?*). Unfamiliar-and-empty is a different event from
familiar-and-empty, and only the first should escalate.

### What recall is keyed by

Not the situation alone, but **the situation and the active goal**. The same world brings different
rules to mind depending on what is being attempted; recall keyed only on world features surfaces the
same set forever regardless of intent.

The mechanism is an index over shared terms: rules are linked to other rules by the members they have
in common, and recall is spreading activation over that web, seeded from both the current moment and
the current goal.

### Deliberate reasoning is not a second mechanism

Slow, exhaustive reasoning is **recall with the budget removed** — same match, same arbitrate, an
exhaustive proposal step. The fast/slow distinction therefore needs no architectural fork: a budget
parameter, and an escalation rule that is itself *a rule*:

```
<E> = causes( { +decision_point(?d), +recalled(?d, ∅), −familiar(?s) },
              { +goal(exhaustive_recall(?d)) } )
```

The escalation triggers are exactly the impasses: nothing came to mind; what came to mind conflicts
irreducibly; or what came to mind was **surprising**, which is §18 feeding this rule.

### What trains it, and the trap

The training signal is already deposited by the machinery: which rule was applied where, and whatever
explanation a surprise produced. Recall learns from its own outputs that survived.

That has one failure mode which must be designed against rather than discovered:

> **Training recall on its own accepted outputs narrows it monotonically.** A rule that never
> surfaces is never applied, never reinforced, and becomes permanently invisible.

The exhaustive pass is therefore **not a fallback**. It is the only thing that injects candidates
recall would never have produced, so it must fire on novelty or on a schedule — not only on impasse.
Otherwise the agent calcifies precisely in the domains where it is performing well, and nothing
reports it.

### Experience has a second home: composition

Recall is where experience lives, and it is not the only place. **Composition** — collapsing a
derivation into a single rule (§4) — is learned from the same signal, deposited by the same
machinery, and attacks the same cost from the other side:

| | **recall** | **composition** |
|---|---|---|
| what it learns | which rules come to mind | **which rules exist** |
| what it changes | the search, over a fixed rule set | the rule set, so less search is needed |
| the gain | fewer candidates per step | fewer steps |
| its output is | a ranked set, opaque | **a node**, inspectable and defeasible |
| trained by | which rules were applied and survived | the trail itself — a successful derivation *is* a candidate composition |

The last row is the reason they belong in one section. §17 already requires every entry to name the
rule and the entries that produced it, because R5 demands it for explanation. That trail is exactly
the training data for both: recall reads it for *which rules mattered*, composition reads it for
*which sequences recurred*. Neither needs an instrument the design does not already run for other
reasons — which is the same observation §13 makes about counting.

They are complementary rather than alternatives, and composition is the larger lever, because a
constant-factor improvement in proposal cannot match removing steps from a search that is exponential
in its depth.

**Composition is not recall**, and fusing them would repeat the mistake §19 exists to avoid. Recall
may be wrong at no cost beyond a worse plan; a composed rule is a *claim*, it can be wrong the way any
rule can be wrong, and §21 lists the three ways it silently is.

### The carve-out

> **Recall may be incomplete about what to do. It may not be incomplete about what you must not do.**

A prohibition that fails to come to mind is a forbidden act that nothing notices. The repair is not to
make recall complete for norms — that reintroduces the exhaustive search this policy exists to avoid.
It is to take prohibitions **off the recall path entirely**: check them at the write, indexed by the
entries about to be written. That set is small and known, so the check is cheap and exhaustive.

> **A prohibition is a gate on application, not a competitor in recall.**

### Scoring and price

| | one undifferentiated `select` | **recall + match + arbitrate** |
|---|---|---|
| not leaking | ❌ an incomplete step reports as authoritative; *nothing applies* asserts more than was checked | ✅ the two silences are distinguishable, and only one escalates |
| not lossy | ❌ *did you consider R?* is unanswerable | ✅ recalled, matched and rejected are three separate records |
| readable | ⚠ | ✅ *which rules does this situation bring to mind?* is a query, askable without applying anything |
| composable | ❌ learning and authority contend for one slot | ✅ learned proposal, authored arbitration, no contest |

The price is three records per decision instead of one, and an index that must be maintained as
episodes accumulate. The second is the real cost, and it is a **rebuild from the episode record, never
a patch of the previous index** — an index patched incrementally drifts from the history it claims to
summarise, and nothing detects it.

---

# Part IV — Gates and open questions

---

## 20. Acceptance

### The floor gate

New in this draft, and the one that keeps Part I honest. It has two clauses and the second is the one
that will be forgotten:

> **For every bundled convention, the rule-level definition exists; the compiled path produces
> identical answers; and the compiled path is interruptible at the same points.**

Run it first on §10's read, since that is the convention an implementation is most certain to have
compiled into itself. A convention with no rule-level definition is a convention that has escaped onto
the floor, whatever the document says — and one that cannot be stopped mid-way has escaped even if its
answers agree.

Two companion counters, cheap and blunt:

* **the number of phases in the interpreter's step.** Every phase is a convention the engine knows by
  name, and — per §4 — every phase is compiled control flow. Target: zero.
* **the stratum-0 scan.** Every rule the implementation applies without a read must have an antecedent
  whose members are all structural (§6). Any that does not is a circularity waiting to be discovered
  by a corpus rather than by a check.

### An agreement gate that agrees is worth nothing until it could have disagreed

Running the first one produced three false passes in a row, and the pattern is general enough to state
as a requirement rather than a war story.

The read agreed on every case — with the entire **deposit index** deleted, because the fixture's
"revision" was written at a different locus, so the locus key decided everything. Fixed, and it
agreed again with the tiebreak deleted, because the rule-level read was returning the *first*
unbeaten candidate and happened to enumerate in the same order as the native walk. Fixed by making
the read refuse ambiguity, and a third rule stayed unkillable until the fixture put an **unrelated**
entry between two competing ones, since transitivity only matters when the entry in between does not
compete.

> **Every gate must delete each rule of the thing it checks, one at a time, and report any rule the
> fixture cannot kill. A rule no fixture can kill is a rule the fixture is not testing.**

This is §13's *bounded expansion returns a result and a state* and §19's two silences, arriving for
the fifth time and now aimed at the checks themselves: **passing** and **unable to fail** are
different outcomes, and only one of them is evidence.

### The commutation gate

Behavioural, not representational. Not *can the system reproduce this text*, but:

> For every rule `R` and every moment `s`:
> reading backwards from a goal proposes `R` at `s`
> **if and only if**
> reading `R` forwards at `s` yields a moment satisfying that goal.

Run it as a property over the whole rule set. A rule whose two readings disagree is a rule whose
consequent is lying about what it does.

The check is available **only because** there is one statement with two readings. With one rule per
direction it is untestable by construction — the two rules are simply different statements. With
program bodies it is undefined, because there is no backward reading to compare against.

Over a recursive shape (§13) the property cannot be run to exhaustion, so it is run per instance to a
depth. That is a weaker gate, and it is the price of being able to state the shape at all.

### Gates from the requirements

* **R2** — for any conclusion, the agent can say whether it was reached forwards or backwards.
* **R5** — every entry in the graph has a licence and a source, and no entry has a stamp the gate did
  not set.
* **R6** — *the level rises by an unknown amount* is expressible, and reading the level afterwards
  reports ignorance rather than the old value.
* **R7** — a procedure in progress can be preempted by a surprise without any interrupt mechanism,
  and afterwards the agent can say why it stopped.

### Gates from provenance

The three a first implementation is most likely to get wrong:

* **Two indices.** After revising a belief about an earlier moment, *what do I now think about `M7`?*
  and *what did I think at `M7`?* both answer, and answer differently.
* **Containment.** Nothing concluded inside a supposition is readable as current belief. The only way
  a scenario's content reaches the agent's own seat is an explicit write whose proposition is about
  the scenario.
* **No laundering.** For every derived entry, its grade is no stronger than the weakest grade among
  the entries match consumed — checkable directly over the trail, without running anything.

---

## 21. What this design does not settle

### On the floor and the bundle

* **Deriving the compiled path** (§4). *Compile rules, not control flow* says how compilation must be
  shaped; it does not say who does it. Today an implementation hand-writes the fast path beside a
  rule-level definition that may not exist, so the two can silently disagree and the agreement gate is
  a test rather than a guarantee. A **transpiler from rules to the host language** would make the fast
  path an artifact derived from the source, at which point agreement holds by construction and
  *slowing down* means running the source instead of the artifact — no decompilation required.

  Two constraints on such a thing, both following from §4 rather than from taste. The target language
  must not be named in the design: what ships is the **compilation contract** — derived from rules,
  rule boundaries preserved as yield points, artifact discardable — and a transpiler is one
  implementation of it. And the unit stays the rule, because the unit of compilation is the unit of
  preemption.

  What is genuinely open is the **trigger**. The natural answer is the one §4's grammaticalization
  argument already gives and §18 already implements: *compile what has run often and never surprised;
  decompile what surprises.* Frequency is countable and surprise is an existing mechanism, so neither
  half needs new machinery. What that would buy is a bundle whose fast paths are a record of the
  agent's own history rather than of the author's guesses — and *why is this one fast?* becomes
  answerable. It is unbuilt, and it is a larger commitment than it looks.
* **Composition** (§4, §19). Collapsing a derivation into one rule is the design's largest available
  speedup — algorithmic rather than a constant factor — and the artifact is an ordinary node, so
  nothing in Part I resists it. What is unsettled is the three ways it goes wrong silently:

  **Guard inheritance.** A composed rule must carry the union of its constituents' `unless`
  conditions, or it fires where the reasoning it replaces would have been blocked. This is checkable
  at composition time and is not specified. It is also the failure the analogy predicts: the
  pathological shortcut is not the fast one, it is **the one that has outlived its guard conditions**
  — the context changed and nothing re-derived it.

  **The composed grade is a cache.** §16 computes an entry's grade as the minimum over the support
  match consumed. Compose the chain and that minimum is computed once, from constituent grades that
  are themselves defeasible — learn that a sensor is unreliable and every composed rule that crossed
  it is stale, with nothing to invalidate it. This is §16's own objection to grades on proposition
  nodes, one level up. The proposed repair is the design's standing answer: **a composed rule is
  dated and superseded, not corrected** — it stays true of the support it was composed from, and a
  later composition supersedes it. Unverified.

  **Nothing can be surprised inside a shortcut.** The intermediate conclusions are never deposited, so
  §18's mechanism is blind to them by construction. This is the cost that makes decomposition
  necessary rather than optional, and it is what makes the trigger tractable: *compose what has run
  often and never surprised; on surprise, re-derive through the constituents.* The licence names them,
  so the agent knows exactly which sub-steps to re-run and the suppressed intermediates become visible
  again — which is more than the compilation loop can offer, since that can only say *run the slow
  path* and not *look here*.

  Two further constraints. Composing a recursive shape (§13) is unrolling, and unrolling is unbounded,
  so composition takes the same budget-and-state discipline as expansion. And composition needs a rule
  to unify one rule's consequent against another's antecedent, which is §5's wall — it is blocked until
  that is resolved.
* **A seat move is not yet an entry** (§17). *Every seat move is a write*, and the re-seating that
  keeps the agent's own frame current while it hypothesises is not recorded as one. Until it is, the
  trail cannot answer *when did the agent's own position advance, and why*.
* **Write-time hooks are not rules** (§4, Appendix C). Moving action dispatch to the write was right —
  §16 had already named the write as the one place effects leave the agent — but it is implemented as
  a Python callable the gate invokes, which is a branch wearing a different shape. What is open is
  whether *fire this when an entry matching P is written* can be a rule; it looks like a demand-driven
  match against the entry about to be deposited, which is §5's wall again from a fifth side.
* **Explaining a read** (§6). Stratum 0 produces structure rather than entries, so the resolution that
  fed a conclusion is undated and unattributed. R5 covers the conclusion and not the read. Whether
  anything cheap recovers this without reinstating the circle is unknown.
* **Match, callable from a rule** (§5) — **settled in shape, unfinished in reach.** It is a request,
  not a sixth floor item, and the request must answer with instantiated results rather than a binding
  (§5, measured by `python -m ugm.backward`). What remains open is the other two callers: lifting a
  modality across a rule, and composing two rules, both need to match a pattern against *another
  pattern* rather than against a ground term. The service as built matches generic against ground,
  which is §7's definition of matching at all. Whether pattern-against-pattern is the same operation
  or a different one is not known.
* **Removing the last phase changes behaviour for the better, so it is not a swap** (§5, §18). Five
  rules over two requests reproduce goal expansion, and produce *more* — because the phase starves
  forward reasoning. That means retiring it is a behavioural change to be argued for, not a
  refactor to be measured into equivalence, and the `<blocked>` verdict has to find a home first.
* **`blocked` needs a home** (§5). It is a state, not a fact, so no rule concludes it. Either the
  searcher keeps reporting it, or there is a request answered once a search settles — which needs a
  notion of *settled* that the design does not have. Related: nothing yet says who decides a plan is
  exhausted, which is also §21's backtracking item.
* **Backward dispatch over reified rules** (§14). The forward direction of connective dispatch is
  writable as rules; the backward direction needs the operation above.
* **How much of the bundle is actually rule-expressible** (§4). The agreement gate is stated and not
  run. Until it is, *these are conventions* is a claim about intent rather than a measured property,
  and the honest status of Part II is *asserted to be convention*.

### On the representation of reality

* **Is sign a member or a wrapper?** (§9) — **settled: both, and one-way translation.** The member is
  what the machinery computes with; the term is what survives nesting. What remains open is smaller:
  whether a channel reporting a denial should write `says(c, p, −)` or `says(c, not(p))`, and whether
  permitting both splits a corpus into dialects; and what a `?` conclusion becomes on the way out of a
  supposition, since `?` is about reading and cannot be a term.
* **Consistency within a moment** (§8). Two entries with opposite signs in one locus is permitted and
  undetected. That is the right default, since consistency is a question rather than an invariant, but
  the design does not say who asks it or when.
* **When a revision is warranted** (§10). The two indices make *I now think otherwise about `M7`*
  sayable, and say nothing about when an agent should write one. Left alone, a system that revises the
  past freely can rewrite its way out of any surprise, which is §18's mechanism defeated by §10's
  permission.
* **Negation versus a false value.** *The stove is not lit* and *the stove has the attribute lit,
  false* are both expressible and mean different things — a claim about the moment versus a claim
  about the stove. Nothing guides the choice, and nothing detects the two being used interchangeably
  within one corpus.

### On what the representation allows

* **Cardinality in backward matching** (§13). Where a count lives is settled — a fact about a group
  node. What is unsettled is how a backward reader *uses* one: unifying a wanted fact against a group
  of unknown size needs cardinality declared per relation position, alongside arity and ordering.
* **Shape equivalence** (§13). Undecidable in general, so *are these two definitions the same shape*
  has no answer and duplicate shapes will accumulate undetected. Open: whether a decidable fragment is
  worth carving out.
* **Structure against claims** (§12). An antecedent carries two kinds of member and nothing
  structurally stops an author writing a claim where a skeleton constraint belongs, or the reverse.
  Stated and unenforced.
* **Distribution** (§13). *Each file was copied* against *the files together filled the disk* is a fact
  about the entry, but which entries need it, and what a read that does not ask for it should return,
  is not specified.
* **Constrained-not-bound values.** *The level rises by an unknown amount* wants a value member that
  is constrained rather than bound. Note the boundary §11 draws: **recognising** an ongoing pattern
  does not need this — a span superseded by a longer span is ordinary versioning — only **predicting
  that it continues** wants an unbound endpoint.
* **Span normalisation** (§11). Equality of span content must be normalised by chain order rather than
  member order; the normalisation is not specified.
* **Resolving calendar terms** (§15). Calendar terms denote and the chain orders. What is unsettled is
  the resolution itself — who computes it, against whose clock, and what happens when a term denotes a
  stretch the chain does not reach, as *next Tuesday* does.
* **An arrival should be a moment** (§15, §18). A channel reports a *signed* state of affairs, and a
  proposition carries no sign, so the sign currently rides as a member of `says`. Needs §12's skeleton
  — or is dissolved by the §9 question resolving toward wrapping.
* **Evidence accumulation** (§16). Two independent *likely*s should amount to more than *likely*.
  Counting over episodes, with no arithmetic on grades; the counting scheme is unspecified.
* **When to cross a guard** (§16). A rule that crosses every hedged fact it sees crosses the hedged
  facts it just produced, and only terminates when the wrapped terms happen to run out of applicable
  rules. Eager crossing has no criterion; the criterion is **demand**, which is backward reading, and
  the two are not yet connected.
* **Enforcing the gate** (§17). *No write bypasses the stamp* is a property of one place rather than a
  prohibition on rules, which makes it checkable — but the check is not written, and until it is,
  §16's soundness argument rests on the gate having no second door.
* **Seat discipline across processes** (§17). Frames form a forest and any of them may be in focus.
  Nothing says whether two processes may hold seats in the same moment at once, what it means if they
  do, or whether one process may move another's seat.
* **Backtracking** (§18). Bindings live on a `plan` node, so sibling subgoals are satisfied on
  bindings that agree — but the first match commits. If `tap(sink)` is chosen and the sibling then
  fails, nothing reconsiders `tap(?t)` against another tap. A plan is a node, so an alternative is
  expressible; what is missing is who decides to take one, which is arbitration over plans.
* **Retracting a contradicted expectation** (§18). Precedence stops a defeated rule applying, but
  nothing retracts what it already concluded, and its antecedent still holds. The agent goes on
  believing both the expectation and its refutation, distinguished only by which rule outranks which.
  Whether that is right — §8 does say consistency is a question rather than an invariant — or whether
  a deviation should discharge the expectation, is not settled.
* **Familiarity** (§19). The escalation trigger needs *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule** (§19). When the exhaustive pass fires in the absence of an impasse.
  What is open is the *rate*, not the requirement; without one, recall calcifies silently.

---

## Appendix A. Glossary

Each entry says whether the term names something on the **floor** (§4) or in the **bundle** — the
conventional representation of reality that ships with the engine and can be replaced.

| term | floor / bundle | definition |
|---|---|---|
| **anchored** | bundle | of a moment: has individuals and a predecessor in the history. The opposite of *generic*. |
| **arbitrate** | mixed | choose one rule among those that matched. *Totality* is floor; the precedence table is authored data. |
| **bundle** | — | the conventional representation of reality shipped with the engine: Parts II and III. Inspectable, and replaceable. |
| **channel** | bundle | the intake path an entry arrived through. Mechanically observed, so it cannot be wrong. Distinct from *authority*, which can. |
| **connective** | bundle | `implies` or `causes`; the relation between a rule's two moments. Consumed by rules, not by the engine. |
| **deposit** | bundle | the moment whose delta an entry sits in — when the claim was made. Distinct from *locus*, which is what it is about. |
| **entry** | bundle | a node with three members — locus, proposition, sign. The unit of assertion. |
| **frame** | bundle | a reasoning in progress, as a process node. Carries a *seat* and a *topic*. Frames form a forest, not a stack. |
| **gate** | bundle | the write path, considered as the one place provenance becomes vocabulary. Distinct from the floor's *stamp*. |
| **generic** | floor | contains variables. A rule's two members are generic. |
| **grade** | bundle | an ordinal modality on an entry: certain, likely, possible, unlikely, unknown. |
| **group** | bundle | a node standing for a plurality. Its membership is not stored; its size is a fact about it. |
| **licence** | bundle | the node that says what authorised a moment's delta, or what produced an entry. |
| **locus** | bundle | an entry's first member: the moment or span the claim is about. |
| **match** | floor | find a substitution making a generic node identical to an anchored one. Structural, and with no opinion about entries. |
| **moment** | bundle | a signed delta, a predecessor and a licence. The bundle's only state construct. |
| **proposition** | bundle | a relation instance. Claims nothing until an entry places it. |
| **recall** | bundle | propose which rules come to mind. Learned; never complete. A policy, not a primitive. |
| **register** | floor | the one pointer: which node writes land in. That it holds a frame is convention; suspended positions are ordinary members of frame nodes, not further registers. |
| **composition** | bundle | collapsing a derivation into one rule. Learned, like recall; unlike recall, its output is a node and can be wrong. |
| **stratum 0** | bundle | the rules whose antecedent members are all structural, so they are applied without a read. What breaks §6's bootstrap. |
| **rule** | bundle | a fact whose two members are generic, related by a connective. |
| **seat** | bundle | a frame's first part: the moment its writes are deposited in. Where the reasoning is standing. |
| **shape** | bundle | a pattern of indefinite extent, defined by recursive rules over spans. A node, so bounds and provenance attach to it. |
| **sign** | bundle | `+`, `−`, `?`, or the absence of an entry. See §9, including whether it should be a member at all. |
| **skeleton** | bundle | the part of an antecedent that relates its variable loci — succession, span endpoints, distinctness. Carries no sign, and claims nothing. |
| **span** | bundle | a node with two members, a start and an end moment. A locus for trajectory claims. |
| **stamp** | floor | the unconditional record, on every minted node, of what produced it. Not vocabulary. |
| **topic** | bundle | a frame's second part: the locus its writes are stamped with. Equals the seat except when reasoning about another time. |
| **write** | mixed | mint signed entries. The floor supplies a register and a stamp; the gate supplies locus, licence, source and grade. |

## Appendix B. Alternatives considered

Each was scored in the section named; this table is the index.

| decision | rejected alternative | why |
|---|---|---|
| the floor (§4) | moment, entry and sign as engine-level | they are a *representation of reality* — teachable, replaceable, and the thing an agent reasons better by having. The read that uses them is a program, not a primitive. |
| the floor (§4) | four primitives, recall among them | recall is a learned proposer, which is the opposite of a primitive; and *arbitrate* splits into floor totality plus an authored table |
| the substrate (§3) | ordering as irreducible | it is encodable with unordered edges and slot nodes. It is on the floor **by economy** — its absence turns linear matching into subgraph isomorphism |
| the floor (§4) | suspended positions as further registers | an unbounded set of privileged slots, and R7 fails for the machinery's own control state; saved positions are ordinary members of frame nodes |
| the agreement gate (§4) | *identical answers, only slower* | a compiled convention is also uninterruptible, which is precisely §18's objection to control flow, one level down |
| the bootstrap (§6) | a distinguished region the engine reads without the convention | one fact in two shapes — §17's objection to augmentation; and it violates the agreement gate silently |
| the bootstrap (§6) | stratifying by *how to think* versus *the business domain* | a real and useful cut, but trust, surprise and goal expansion are all domain-independent **and** talk about entries, so it does not bottom out |
| state (§7) | a mutable world state | overwriting makes *it changed* and *I was wrong* one operation |
| belief (§7) | a belief-set node beside the moment chain | a moment already is one; a second membership structure for beliefs is a second ordering beside succession |
| assertion (§8) | truth as a value on the proposition node | minting a node in order to deny it asserts it; correction overwrites the record it corrects |
| the read (§10) | locus alone, or deposit alone | locus alone cannot tell a revision from what it revises; deposit alone lets a new belief about the past overrule a settled belief about the present |
| rule form (§12) | guard plus a program body | the backward reading is a hypothesis wearing entailment's clothes with nowhere to record it; and a program has no subject, so nothing can be said about the rule |
| rule form (§12) | one rule per direction | two statements drift, neither is the other's premise, and the disagreement is undetectable |
| antecedent (§12) | a per-member achievable/given mark | achievability is relative to the planner, the deadline, the situation and the rule set, none of which the author knows; and it lets a prohibition masquerade as an impossibility. **The design's first instance of closing an open concept.** |
| notation (§12) | `@` for a locus, `→` and `[…]` for timing | punctuation that suggests a privileged mechanism is an island on the page; loci are ordinary members and bounds are ordinary facts |
| shapes (§13) | materialise a witness sequence | states a length nobody claimed |
| shapes (§13) | a reserved grammar with counters | a production cannot carry `unless` or `overrides`; decidability is bought and then spent on the first three extensions |
| timing (§15) | a third member of the connective | the connective's arity varies, an absent delay silently defaults, and two sources cannot disagree |
| timing, modality (§14, §16) | fused connectives such as `likely_causes` | fuses strength with defeasibility and records neither; the name set grows multiplicatively |
| modality (§16) | grade on the proposition node | *likely* said of no occasion and every occasion at once, and a cache of a derived value — which is a truth-maintenance system |
| modality (§16) | confidence as a grade on the rule | the same question is asked of sensors and speakers, so it belongs on the source |
| modality (§16) | a guard node per uncertain fact | optional guards mean two shapes for every consumer; mandatory guards mean a node and a hop per certain fact |
| modality (§16) | wrapping written per rule — a `likely` twin of every rule | the wrapped and bare corpora share nothing, since `likely(p)` and `p` are different propositions; measured at 2x |
| modality (§16) | a lifting rule over reified rules | binds against a rule's *pattern*, so it fires only where that pattern is ground — and real corpora are mostly generic rules |
| entries (§17) | only the machinery may write entries | stronger than the requirement, which is that no write bypasses the stamp; it forbids honest past-directed claims and pushes trust into hard-wired intake |
| frames (§17) | a stack of frames | two hypotheses under comparison are siblings, both alive, neither the caller of the other |
| frames (§17) | copy conclusions out of a frame, re-qualified | one fact in two shapes, and it needs invalidation the moment the supposition is discharged differently |

## Appendix C. The name census

§5's test applied to the vocabulary an implementation actually reserves. This is the census as of the
current `ugm/` build; it is expected to shrink, and the count is the measure of progress.

**Survives — match or write cannot be defined without it**

| name | why |
|---|---|
| the rule form | something must know that a rule's members are its two sides, or nothing can hand match a pattern |
| the sign values | floor *only if* §9 resolves toward sign-as-member; under wrapping, one reserved relation takes their place |
| the register | §4 item 3 — a pointer, not a vocabulary item |

**Convention — shipped as a rule in the bundle**

| name | the rule | section |
|---|---|---|
| `says` | `<intake>` — `implies({+arrived(?c, ?p, ?s)}, {+says(?c, ?p, ?s)})` | §17 |
| `did` | `<did>` — `implies({+emitted(?w)}, {+did(?w)})` | §15 |
| — | `<assert-act>` — `implies({+did(?w)}, {+?w})`, §15's *the agent asserts the act* | §15 |
| `deviates` | four rules — `implies({+expects(?p, σ), σ'(?p)}, {+deviates(?p)})` for each way an observation disappoints an expectation | §18 |

**Convention — fails the test, and still has an interpreter branch**

| names | what they are for | section |
|---|---|---|
| `causes`, `implies` | which moment a consequent lands in | §14 |
| `goal`, `achieved`, `blocked`, `plan`, `subgoal`, `binds`, `expands` | backward search's working state | §18 |
| `expects` | deposited by forward application, which is not a phase | §18 |

**Boundary — machinery, and legitimately so**

| names | direction | why it cannot be a rule |
|---|---|---|
| `arrived`, `utterance` | in | a channel is **anchored** and a rule is generic, so no rule can name the socket a report came in on. Delivery is not a step of the loop: the boundary **calls in**, at the moment the world speaks. |
| `doing`, `emitted` | out | the same, read the other way: no rule can name the agent's own edge |
| `suppose` | inward | entering a frame **moves the register**, which is §4 item 3 and irreducible for the same reason as the bootstrap. Everything else about supposing is convention. |
| `kb` | — | the channel a derived entry is sourced to |

**The outward boundary has exactly two names, one per direction, and the inward one is the register.**
The first symmetry is §15's *acting is a channel read the other way* turning out to be true of the
implementation and not only of the prose. The second is §17's *entering is writing*: what a rule cannot
do is not *change the world* but *say where it is standing*. These rows are the only ones in this
appendix that are not debt.

Thirteen conventions with branches, four shipped as **seven** rules, **one** interpreter phase
remaining — goal expansion. §20's counter target is zero, and the last one is the hard one: reading a
rule backwards is precisely a rule matching a rule, which is §5's wall.

### What moving four taught

**Splitting a phase shrinks it rather than relocating it.** `_intake` became the smallest unarguable
record of a boundary event — `arrived(channel, proposition, sign)`, sourced to the channel — and *what
a report means* became a rule. The arrival's grade now reaches the `says` claim through §16's weakest
link instead of through a keyword argument, so nothing special-cases it, and provenance landed where
§17 says it should: the raw arrival unforgeable, the saying above it derived and arguable.

**A phase can hide a precedence claim.** Intake ran *before any rule was considered*. The rule is
merely installed first, so §18's authored-order tiebreak prefers it — and a corpus can now say
otherwise, which is the difference §18 spends its length arguing for.

**Being machinery never made it a phase.** Even after `says` became a rule, *draining the channels*
stayed the first line of the loop — and nothing required that. Crossing the boundary is irreducible;
crossing it **on the agent's schedule** is a claim, and a false one.

> **An arrival is an external event, and an external event is not something the agent does.**

So delivery is the boundary calling in, the same shape as the write hooks, and the tick lost its first
line. What remains in the step is a *counter* — how much arrived since the last one — because §19 still
needs *nothing applied* and *nothing arrived and nothing applied* to be different silences.

The behavioural difference is visible without running anything: a report is on the graph the moment
the world speaks, and *what it means* still waits for a rule to be selected. Those were the same
instant while intake was a phase, and they are two different things.

**Acting was in the wrong place, and this section said so already.** §16 puts action dispatch at *the
one place effects leave the agent* — the write — and §19 puts the prohibition check there for the same
reason. The implementation polled for intents once a tick, which had quietly moved that decision into
control flow. Moving it to the write removed the phase without inventing anything: the loop lost a
branch because the design had already named a better home for it.

**And it made §18's central claim concrete.** *The agent asserts the act* was a line of the
interpreter, and therefore unarguable. As `<assert-act>` it is a claim, so an agent that does **not**
assume its acts succeed is now expressible by dropping one rule — and it still acts, and still knows
it acted. A strategy written as code cannot be overridden by a statement in the knowledge base; this
is the first place in the implementation where one can.

The debt this incurred is named rather than hidden: the write-time hook is a Python callable, and §21
records that the bundle should be rules. A hook is not one.

**A branch can hide how many claims it was making.** Noticing a deviation was one comparison — *the
observed sign is not the expected one* — and became **four** rules: two expected signs against the two
ways an observation contradicts one, the opposite sign and `?`. The count is the finding. A single
comparison had been quietly asserting that §9's *invalidated, and I cannot say what replaced it*
disappoints an expectation exactly as much as the opposite outcome does. That is a real claim, it may
be wrong, and as a branch there was nowhere to argue with it.

**Data rots in a way a branch does not.** Three of those four rules were unexercised, and — unlike a
dead branch — a rule that never applies costs nothing, breaks nothing, and looks exactly like a rule
that works. The phase had never tested those cases either; writing them as rules is what made the gap
visible. `python -m ugm.bundle` now deletes each bundled rule and re-runs the suite, so a rule nothing
can kill is reported rather than accumulated.

**The worst offender was the machinery's own control flow, not its vocabulary.** Supposition looked
like the hardest phase to move, because entering a frame genuinely needs the register. That part was
three lines. The rest of the phase was a **nested `run()`** — the loop, called inside itself, to
quiescence, before returning.

That is a subroutine call, and it is the exact thing §18 spends its length refusing:

> *if `to find an answer, look for causes` is control flow, step three owns the agent until it
> returns.*

The design had that sentence aimed at corpora, and the machinery was doing it. A supposition owned the
agent from the moment it opened until it was exhausted, so nothing could preempt reasoning carried out
under a hypothesis — the one place an agent most needs to be interruptible, since a hypothesis is by
construction something it is not sure about.

The repair needed no new mechanism, only the removal of one. **Entering is a write** (the request is
an ordinary entry, and the register moves at the write, like §16's action dispatch). **Leaving is
quiescence** — when the loop finds nothing more to do *here*, and *here* is inside a supposition, that
is not the end of the run but the end of the supposition. Reasoning inside a hypothesis became
ordinary ticks of the ordinary loop, and three things followed at once: the caller keeps control
between every step, the supposition's own reasoning appears in the caller's trace (R7, for the
machinery's hypotheses), and the depth budget stopped being a second, nested budget.

The lesson generalises past this one phase. **A convention hidden in vocabulary is easy to see and
cheap to move; a convention hidden in control flow is invisible and expensive.** The census counts
names, and names were the easy half.
