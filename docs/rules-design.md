# Rules — a design

This document specifies how an agent represents rules, states, claims and uncertainty on a single
graph substrate, and what the engine that runs them must provide. It is self-contained: every term it
uses is defined here, and every decision is argued from the requirements stated in §1 rather than
from precedent.

**It is organised around one claim.** Almost nothing in this design is part of the engine. Moments,
entries, signs, spans, rules, modalities, channels, frames, goals and plans are a **representation of
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
and the design caught its first instance of it (§12's *achievability is not a mark*) without
generalising. This document generalises it, and then applies the generalisation to itself — twice, in
places the earlier drafts had defended at length. §16 no longer has a grade. §19's precedence is no
longer a table. Both were closed sets the engine knew by name, both were argued for well, and both
were **measured** and deleted. Those two deletions are the strongest evidence in this document that
the test in §5 is worth running on things you believe.

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
- [20. Acquisition and harmonization](#20-acquisition-and-harmonization)

**Part IV — Gates and open questions**

- [21. Acceptance](#21-acceptance)
- [22. What this design does not settle](#22-what-this-design-does-not-settle)
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
that, and on whose word?* The trail a piece of reasoning leaves behind is not a debugging aid; §16
and §20 both make it load-bearing for correctness, and §19 makes it the only training signal in the
design.

**R6 — Partial knowledge must be sayable.** *Pouring raises the level, by an unknown amount* must be
expressible as such. A representation in which the only options are *states a value* and *says
nothing* forces the agent to claim precision it does not have, or silence that means the wrong thing.

**R7 — The agent's own state is in the world it reasons about.** Expectations, commitments and
in-progress procedures must be facts on the graph, not variables in an interpreter. Otherwise the
agent cannot notice that an expectation failed, cannot be asked why it abandoned a plan, and cannot
have a strategy overridden by a statement in its knowledge base.

R7 is the one that does the most work in this draft. Taken seriously it does not stop at expectations
and commitments: it reaches the representation of belief itself. If *what I believe*, *when I came to
believe it* and *how surely* were engine-level, the agent's own epistemic state would be the one
thing it could not reason about.

**R7 has a recurring failure mode, and it is worth naming here rather than discovering it eleven
times.** The machinery routinely computes something, uses it, and throws it away — so the agent acts
on a judgement no rule can ask about. Every instance looks different and every fix is identical:

> **Something the machinery knows and no rule can ask about is a defect, and the repair is always to
> deposit the record.**

This document records eleven instances. Which rule was applied became `exercised`; a defeat became
`defeated`; which hypothesis reached a conclusion became `concluded`; what an entry rested on became
`rests_on`; a tool's binding became `answers`; the effort counters became `widened`/`reached`/
`bounded`; and — the two largest — an entry's strength became a **wrapping term** rather than a field
(§16) and the precedence table became a **claim read from the graph** rather than Python state (§19).
The pattern is stable enough to use as a search: anything the loop computes per tick and does not
write down is a candidate.

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
would change nothing (§5).

The third was found by building rather than by argument, and it is the one to watch: match returning
nothing and write refusing are both observable, while *this would change nothing* is silent by
construction.

### The criteria score a pair, not a shape

This is the correction that organises the document. A shape does not leak or fail to leak on its
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

### Composition is where the defects are

A fifth criterion was considered and rejected as a criterion, because it is not a property of a shape
at all. It is a property of *two arcs of work meeting*, and it belongs here as a method rather than a
column:

> **Two conventions that have never met are two conventions that have not been tested.**

This is not a maxim. It is the measured behaviour of this design's own construction. Four independent
pieces — a defeat becoming a record, a rule authoring a rule, an example becoming a rule, and
uncertainty becoming a wrapper — were each built with their own checks, each green, and the first
fixture that made them meet broke in **two** places at once, neither visible from inside any of the
four (§20). A design whose parts are only ever exercised separately is a design whose scoring tables
are guesses.

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

An earlier claim — *ordering is the one thing that is not itself structure* — is too strong, and
correcting it matters because it is the claim that made the floor look inevitable rather than chosen.

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

### One index, and what it may not be over

The substrate provides exactly one index: **instances by relation**. The argument is one line — *a
rule whose antecedent names a relation has to start somewhere, and scanning every node is the
alternative* — and it is the same argument, read backwards, that §19 makes for indexing rules by
what they conclude and §20 makes for indexing norms by what they forbid.

One condition governs every index in this design, and it is the condition that keeps an index from
becoming a truth-maintenance system:

> **Index what was asserted. Never index what was derived.**

An index over asserted structure is storage: it summarises writes, and a write is permanent. An index
over derived values is a **cache of something defeasible**, and maintaining it correctly means
propagating invalidations across a web of dependencies — a second machinery with its own consistency
problem running underneath the first. §16 refuses a stored grade on exactly this ground, and §19
refuses a kept precedence table on it. Every index this design has met the condition: the argument
index (below) is built at deposit, the state index is maintained from the deposit, and the rule index
is over authored consequents.

**A second filing of the same asserted structure is still asserted structure**, and this is where the
condition earns its keep rather than merely constraining. An entry filed by `(sign, relation)` alone
makes a join quadratic: a rule whose antecedent is `child(?p, ?x), child(?x, ?y)` draws every
instance of `child` for each of the first member's *N* bindings. Filing each entry additionally under
each of its arguments — `(sign, relation, position, node)` — and walking the member that binds first,
turns 2,006,004 unifications over 1,000 facts into **3,003**. Both filings are over what was
asserted; neither is a cache; and the second is the difference between a join and a scan.

**What has no bucket, and what that costs.** Two kinds of pattern cannot be filed: a **bare variable**,
and one whose **relation** is a variable (§4). Neither says anything about what it names until it
matches, so both take an *any* bucket and scan. That is the price of the two most general things the
language can say, and it is worth stating as a number rather than a caveat — measured on a small world
with 200 unrelated facts, an antecedent member whose relation is a variable costs **14× the
unifications** of the equivalent concrete rules.

> **A variable in the relation slot is exact forwards and expensive to look up.** In a **consequent**
> it costs nothing at match time and is *cheaper* overall, because one rule replaces N — measured, 4×
> fewer unifications at twelve effects by twelve targets. In an **antecedent** it should be narrowed
> by a member that does have a bucket.

That is the same shape §12 gives a bare-variable consequent — exact in one direction, vacuous or
expensive in the other — and it is why both are permitted rather than encouraged.

⚠ **The argument index files atoms only, and the restriction is load-bearing rather than cautious.**
Unification compares a ground *structure* member by member, so it accepts a structurally equal node
that is not the same node. An identity-keyed bucket drops those, which is the twin trap of §20 in
index form — measured, filing structured members loses four checks and costs 4% of the suite for a
bucket nothing can read.

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
generic one yields the anchored one, position by position, **relation included — and the relation is a
position like any other.** That is *structural* unification and nothing more.

⭐ **That last clause was a silent restriction until it was probed.** A relation instance whose
relation slot holds a **variable** — `?p(?x)` — is an ordinary generic node, and the substrate has
always been able to build one. It never matched, because three separate things declined it and none of
them on an argument: the surface would not parse it, `unify` compared the relation slot by identity
rather than unifying it, and `substitute` would not rebuild one. Nobody had asked which of the three
was the reason, so it read as a property of the floor.

It is not. Genericity is floor; *which slots may be generic* is a choice, and restricting it to
argument positions was never argued. Allowing it is what makes a **class nameable by data** —
`sells(smith, weapon)` as a fact, with `+?kind(?item)` applying it — so one rule serves a catalogue
that otherwise needs a rule per member. §3 states the price. It has no opinion about entries, loci, signs or chains — those enter
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
voluntary provenance, and voluntary provenance is forgeable. §16 and §20 both make the support trail
load-bearing for *correctness* rather than for explanation, and those arguments fail outright if a
write can decline to be stamped.

> **Nothing is prohibited; everything is stamped.**

### 5. One total step

Something must always answer. Selection cannot be allowed to search forever or to return nothing,
because the interpreter has no outside to fall back to.

Totality is floor. **What it consults is convention** — an authored precedence relation over rules,
which §18, §19 and §20 depend on being ordinary data, *read from the graph at the position the agent
is standing*. The floor requires only that a bottom-most selector exists, is a lookup rather than a
search, and always returns.

The wording matters and an earlier draft got it wrong. It said *a lookup over an authored precedence
**table***, and a table is exactly what this turned out not to be (§19). What the floor requires is
that the final tiebreak does not itself reason. It does not require that the answer be kept anywhere.

### Three grounds, not one

The five items do not reach the floor for the same reason, and flattening them into one list flatters
the floor by making all of it look inevitable. Only three are irreducible in the strong sense.

| item | ground | the argument |
|---|---|---|
| **variables + substitution** | **irreducible** | defining matching requires matching |
| **one total step** | **irreducible** | selecting the selector requires selection |
| **the register** | **irreducible** | finding where to write requires a read, and a read requires somewhere to stand |
| **the stamp** | **by guarantee** | fully reducible — a rule could write its own provenance. But reducible provenance is forgeable provenance, and §16's and §20's soundness arguments die. |
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

All three are checkable, and the checking has twice overturned the expectation it was run to confirm.
A census of what a corpus actually writes retired the **grade** — 4 of 3,740 rules authored a
non-certain one, and the one function that compared two grades was called from one place (§16). A
second census retired the **precedence table**, whose deletion cost the suite 6.42s against 6.38s
(§19). Neither was cut for being wrong. Both were cut for being *unused where it counted*, which is a
measurement and not an argument.

> **Closed is a rate, not a kind.** The reason to run the census rather than the argument is that a
> closed set defended well is indistinguishable, from the inside, from a closed set nobody has
> checked.

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
| **arbitrate** | *totality* is floor — item 5. *Precedence* is a claim in the graph, and therefore convention. |
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

**And the gate must be run against a moving target, not a fixture.** §21 states the discipline: an
optimisation of a read is a *re-implementation of its semantics*, so the slow definition stays and the
fast path is held to it **on every look, in every fixture** rather than on a test case. This design
runs three such gates — one for the read, one for the state, one for the move — and each of them
caught something no fixture could. The state gate's sharpest finding is the general form:

> **Nothing that asserts what the agent concluded can see what it was thinking about while it
> concluded it.** A wrong key set makes a worse choice, never a wrong conclusion, and every fixture
> asserts an outcome the loop reaches anyway.

### Compile rules, not control flow

The third column is what decides how compilation may be done. Compile a whole chain walk into one
host-language function and preemption is gone — nothing can surprise the agent mid-read. Compile each
**rule's matching** into a fast closure and leave the selection loop interpreted, and every preemption
point survives while nearly all the speed is captured, because the cost is in matching and not in the
loop.

> **Compile rules, not control flow.**

This is §18's *procedures are data that bias selection, never control flow that owns the loop*, one
level down. It also convicts an implementation from a second direction: interpreter **phases** are
compiled control flow. The phases are the uninterruptible part; native matching would have been fine.
Conventions with engine branches, and a bundle that cannot be interrupted, are one defect seen from
two sides. Appendix C is the census, and the count now stands at **zero phases**.

§22 sketches the further step this suggests — deriving the compiled path from the rules rather than
writing it by hand, and letting frequency and surprise decide what is compiled — and marks it as
unbuilt.

### Optimisations are licensed, and the licence has a name

Three of this design's largest speedups are Python that no rule can reach: the maintained state and
its indices, the argument index of §3, and the ordering of the candidate walk. It would be easy to
call each of them debt. They are not, and the distinction is the one this section has been drawing:

> **An optimisation of a semantics is licensed by the floor gate. A cache of a claim is debt.**

The test is what happens when the two disagree. An optimisation has a slow definition it can be held
to, every tick, and a gate that does the holding — so a divergence is a *bug*, findable and reported.
A cache of a claim has no slow definition, because the claim is the definition; a divergence is
*silence*, and the two ways it can be wrong are both invisible. That is precisely why the precedence
table was debt while the state index is not, and why deleting the first cost nothing while deleting
the second would cost an order of magnitude.

Applied honestly, an audit of this design's Python puts it in three piles and only one is debt:

| what | why it is Python | verdict |
|---|---|---|
| the maintained state, the argument index, the walk order | optimisations of a semantics | licensed; three floor gates hold them to the slow definition every tick |
| the doors — entering a supposition, dispatching an intent, adopting a rule | **doors, not questions** (§20) | argued: each needs something anchored that a generic rule cannot name |
| answerer bodies | what a tool *is* (§17) — a request answered by a function rather than a search | right by the design's own rule |
| ~~a precedence table~~ | ~~a cache of `overrides` facts~~ | **debt, and deleted** (§19) |

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
first-class node, so everything already true of rules is true of it. §20 is where that observation
stops being about speed and becomes about **acquisition**: a composed rule is the first rule the agent
authored, and it is authored by exactly the mechanism a learned rule uses.

**Measured** — `python -m ugm.compose`, over a chain of length *n*:

| n | uncomposed | composed |
|---|---|---|
| 2 | 2 | **1** |
| 4 | 4 | **1** |
| 8 | 8 | **1** |
| 16 | 16 | **1** |

*n* steps become one, for any *n*, with the same conclusion. That is the difference between
algorithmic and constant-factor stated as a number rather than as an argument.

⚠ **And *with the same conclusion* is the load-bearing half of that sentence, not a flourish.** A
chain of `implies` collapses soundly because every step is read in one moment. Composing across a
**`causes`** does not: its consequent lands in a successor (§14), so the second rule's other premises
are read a moment later than the first rule's own, and flattening them into one antecedent demands
them all at once. Measured, that loses conclusions, so it is **refused** — §22 has the case and the
exact condition.

What composition costs is not structural but epistemic, and §22 states it: intermediate conclusions
stop being deposited, so nothing can be surprised inside a shortcut, and guard conditions must be
inherited or the shortcut fires where the reasoning would not.

⭐ **One cost the earlier draft listed here no longer exists.** Composition used to refuse anything but
a `certain` conclusion, because composing a grade would have been a minimum computed once from
defeasible constituents — a cache of a derived value, §16's own objection arriving one level up. With
the grade deleted the objection goes with it, and **the restriction was deleted rather than solved**.
That is worth pausing on: a deletion two sections away removed a limitation nobody was working on.

### Pattern against pattern is a different operation from match

Composition is what needed this answered: collapsing `heat(?w) → boiling(?w)` with
`boiling(?x), leaf(?l) → tea(?x, ?l)` means unifying `boiling(?w)` against `boiling(?x)`, where
**both sides are generic**.

| | match (§4 item 2) | unification |
|---|---|---|
| sides | generic against **anchored** | generic against generic |
| a variable binds to | a thing | a thing **or another variable** |
| binding chains | never | yes — a variable's value may itself be bound |
| `?x = f(?x)` | unconstructible | constructible, so an occurs check is required |
| two rules both saying `?w` | cannot arise | must be standardised apart first |

So the floor's item 2 does **not** cover it. What follows is not a sixth floor item, for the reason
§5's `fit` already gives: a rule cannot hold the resulting substitution, let alone apply it.
Composition is therefore a **service** whose answer is a finished rule — the same shape as `fit`,
reached from a different direction, and for the same underlying reason.

§20 adds the third member of this family, and it completes a symmetry worth stating now:

| operation | asks | answers with |
|---|---|---|
| **match** | does this pattern fit that thing? | a substitution |
| **unification** | can these two patterns be made the same? | a substitution over both |
| **anti-unification** | what do these two things already agree about? | **a pattern** |

The third is the dual of the second, and it is what *learning from examples* is made of (§20).

**Defeat is inherited, and it is checkable.** Anything that overrides a constituent overrides the
composition; without it, a shortcut escapes a defeat that bound its parts on the very first tick,
rather than after some later context change. `unless` is a different matter: §12 describes it and no
engine here implements it, so only the precedence half of guard inheritance exists.

⚠ **And inheriting a defeat is now a claim the caller deposits**, not an append to a list, because
§19 deleted the list. A composition built by something with no world to write in gets no inherited
precedence — which is the honest answer rather than a silent one.

### Why the bundle ships at all

This gives the conventions their proper home: a bundled knowledge base that ships with the engine, is
inspectable by ordinary queries, and can be replaced. An agent with a better internal representation
of reality is only possible if the representation is something you can hand it.

The bundle is not optional in practice. An engine that shipped with the floor alone would be correct
and useless — every corpus would have to re-derive belief, time and evidence, and no two would agree.
Bundling is how the design ships an opinion without freezing it.

**And the bundle must be authored in the surface, which is an expressibility test and not tidiness.**
Writing the apparatus in the host language means nobody has ever checked that the surface *can say*
what the apparatus is made of. Moving it out found that it could not: two relations the bundle
depends on were unnameable by a corpus, so two bundled rules were unwritable by anyone but the engine,
and nothing reported it.

> **A bundle authored in Python is a claim about expressibility that has never been tested.**

---

## 5. The test

> **A name is engine-level only if match and write cannot be defined without it. Everything else is a
> convention, and the machinery that uses it must be expressible as rules.**

Applied to the vocabulary an implementation actually reserves, the test convicts nearly all of it.
Appendix C is the census. It has a falsifiable consequence, which is the point of stating it:

> **The interpreter's step should have no phases.** Match, commit, write — and intake, supposition,
> acting, deviation and goal expansion become rules that those apply.

An interpreter with one phase per convention has, in effect, compiled the bundle into itself. The
count of phases is therefore a direct measure of how much of the bundle has escaped onto the floor,
and it is a number an implementation can print. It now prints **zero**.

### What the test does not license

The test is about **naming**, not about speed. Native implementations of bundled conventions are
expected and encouraged; the requirement is §4's floor gate, not abolition.

Nor does it license removing conventions the agent needs. *Convention* is not *optional*. Signs, loci
and modalities are as necessary to good reasoning as they ever were. What changes is their status:
they are claims about how to represent reality well, defended in Part II and Part III, and defeasible
in the way any claim is.

### A rule can name a rule; a rule cannot match one

One consequence of item 2 being floor deserves stating early, because it is a wall reached from four
directions and it constrains everything in Part III.

Rules can be **reified** — written as ordinary facts, with a relation naming the connective and
members naming the two sides. Once reified, a rule can be spoken about freely. What a rule cannot do
is *apply* match to another rule's pattern:

```
con(<boil>, boiling(?w), +, 0)     what reification stores: the rule's PATTERN, generic
+goal(boiling(kettle))             what a goal is: ground
```

A rule that tried to relate these needs one variable to be both the generic pattern and the ground
goal. Deciding that the two *correspond* is exactly match — and match is floor, so no rule can call
it.

**Four** separate ambitions hit this same wall: reading a rule backwards (§12), lifting a modality
across a rule (§16), asking whether a generic subgoal is already satisfied (§18), and **composing two
rules** (§4) — which needs one rule's consequent unified against another's antecedent, both of them
stored patterns.

Four independent capabilities blocked by one missing operation is the strongest argument in this
document for resolving it. Three of the four now have a resolution, and they all take the same shape.

### The repair is a request, and measuring it says what the request must return

`python -m ugm.backward` runs backward reading twice over one corpus — once as an interpreter phase,
once as ordinary rules over a match **request** — and they reach the same seven goals.

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

The same shape answers the other two. Composition is a service that returns a finished **rule** (§4);
anti-unification is a service that returns a finished **pattern** (§20). In each case the caller could
not have held the intermediate, and in each case the service does the substitution on the caller's
behalf. What distinguishes them from a floor item is not their power but their *answer*: a floor item
returns a binding, and a service returns a thing.

**Satisfaction is a second request, not the same one pointed elsewhere.** *Is this goal already met*
must be computed **inside the plan's bindings**, or `tap(?t)` is met by `sink`, `under(kettle, ?t)` by
`drain`, and the plan is wrong with nothing saying so (§18). So there are two services —

```
+fit(<R>, goal)        could this rule produce it?          → fits / need / unfit
+check(<plan>, goal)   does the world already answer it?    → achieved + binds / unmet
```

— and with them, **six rules** reproduce the phase entire: ask-recall, ask-fit, plan, expand,
ask-check, and the verdict. Plans need no minting: `plan(?r, ?w)` is built by substitution into a
consequent, and substitution interns, so the same rule expanding the same goal names the same plan —
which is what a plan is.

### Two things the last phase taught

**`blocked` is not a fact, and no rule can conclude it.** The natural rule —
`implies({+goal(?w), +unfit(?r, ?w)}, {+blocked(?w)})` — fires when **some** rule does not fit, and
what `blocked` claims is that **no** rule does. That is an aggregate over a *finished* search.
Positive rules cannot say it, and §9's `−` does not help: *an entry says this does not hold* and *no
entry* are neither of them *for no `?r`*.

This is §13's and §19's discipline arriving at the last phase rather than a missing feature:

> **Bounded expansion returns a result and a state. `blocked` is the state.**

A state is what a searcher reports about *itself* when it stops. §19 gives it a home — the aggregate
becomes legitimate at `quiet`, the fact that says a search has finished — and until such a fact
existed there was nowhere in the graph where such a claim was true.

**The phase starved forward reasoning, and that is a precedence claim frozen in control flow.** It
ran before recall/match/arbitrate and returned early, so while any goal was unexpanded no ordinary
rule could apply. Measured: a goal that *is* satisfiable — `water(kettle)`, derivable forwards from the
same corpus — read as unsatisfied, because the phase never let anything derive it. The rule-level
reader interleaves, being ordinary rules, and finds it.

That is intake's finding and supposition's finding at once: **a phase does not merely hold a
convention, it asserts a precedence, and it asserts it where nothing can argue.**

### Use and mention, and where the refusal actually happens

Reification forces a distinction the design would otherwise not need. `+con(<R>, boiling(?w), +, 0)`
is a **ground** claim about a rule that happens to name a node containing variables. It is not a
generic claim, and refusing it would make rules unspeakable-about — but structurally the two are
identical, so nothing in the shape can tell them apart.

Earlier drafts settled it by **who is writing**: the machinery reifying a rule mentions, a rule's
consequent uses. That is too strong, and building it is how the gap showed. A rule whose antecedent
matches `+con(?r, ?pat, +, ?i)` binds `?pat` to a stored pattern, so anything it concludes about
`?pat` is a rule's consequent *mentioning*. Under the authorship rule that write is refused, and rules
cannot reason about rules at all — which R3 requires them to, and §20 requires absolutely.

What tells them apart is inheritance rather than authorship:

> **Mention propagates through bindings. A conclusion drawn from a mentioned entry is itself a
> mention.**

This is checkable rather than declared, because the entries match consumed are already recorded — R5
needs them for the trail. It is the trail turning out to be load-bearing for something other than
explanation, which §16 and §20 both argue is the pattern to expect.

**Mention has to start somewhere**, and a pattern authored naming a rule is the source. This is not a
detail: §19's callbacks and §20's precedence-about-a-learned-rule both hang on it, and both were
silently broken until something pointed at a rule.

**The refusal was not where the design says refusals happen.** A rule reasoning about rules was never
rejected by the gate. It was dropped by the **quiescence filter**, which treated a conclusion still
containing variables as *nothing left to do* — so a rule reasoning about rules looked exactly like a
rule with no work: no error, no trace, nothing to distinguish it from correct behaviour.

§2 says the machinery has exactly two places where it can be asked why it returned part of a
structure: `match` and `write`. That is one short.

> **Quiescence is a third place the machinery can decline, and it declines silently.**

Match returning nothing and write refusing are both observable. *This application would change
nothing* is indistinguishable from *there was nothing to apply*, which is §9's `−` against no-entry
and §19's two silences arriving in the one place the design had not looked. §19 closes it with
`quiet`.

### Adding a connective adds rows, not branches

The older statement of this test survives unchanged, and is now a corollary rather than an axiom:

> **If a new connective requires editing the engine, the connective set is not data.**

The same holds one level up for everything in Part III. If a new *convention* — a new way of
representing evidence, or plans, or time — requires editing the engine, then the bundle is not data
either, and §4's floor gate is what detects it.

⚠ **A `for` loop over four tuples is a branch wearing a row's clothes.** §18's deviation rules were
generated in Python from a list, which passes the *rows not branches* test on a count and fails it on
the point: nothing could reorder them, refuse one, or argue with the claim that a `?` disappoints an
expectation exactly as much as the opposite sign does. Written out as four rules, that claim became
arguable — and three of the four turned out to be unexercised, which a branch would have hidden
forever.

> **Data rots in a way a branch does not.** A dead branch is dead code. A rule that never applies
> costs nothing, breaks nothing, and looks exactly like a rule that works.

That is why §21's bundle gate deletes each shipped rule and re-runs the suite.

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
out. That is the fixed point, and it gives a criterion decided by inspecting an antecedent rather than
by a designer assigning layers:

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
| selecting needs selecting | the total tiebreak (§18) | a lookup that does not reason |
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
* **arbitrate** is the same total tiebreak, over a precedence nobody has claimed.

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

⚠ **And this price is charged somewhere unexpected**, which §20 discovers and does not resolve. An
entry's support — *what this was derived from* — is structural for exactly the reason above: it is
*how the entry was made*, not a claim about the world, so nobody asserted it and it cannot be denied,
dated or attributed. That makes it stratum 0's business, which makes it unreadable by ordinary rules.
The agent's own trail is therefore the richest source of examples it has and the one source its own
rules cannot see. Whether an ordinary rule should be able to read the skeleton is a real design
question and a large one (§22).

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
it is editable by the agent that runs it. §20 is what makes *editable by the agent* more than a
figure of speech.

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

### The state is what the chain answers, and it is kept rather than rebuilt

A moment stores only what changed, so a moment does not contain its state. §10 is the walk that
answers it. That walk is the design's largest recurring cost, and the shape of the only legitimate
repair is worth stating with the convention rather than with the optimisation:

> **A state changes by one claim at a time, so the index over it changes by one claim at a time, and
> so does whatever is read off it.**

Keeping the resolved state and then rebuilding everything derived from it keeps the cost you were
paying. Maintaining all three where the state is — the state, its index, and the keys read off it —
takes the loop from quadratic to **linear**: measured, 1,600 facts from 4.79s to **0.48s**, and 12,800
facts in less time than 1,600 took before. Doubling doubles.

This is an optimisation of a semantics and not a cache of a claim (§4), so it is licensed — and the
licence comes with a gate that holds the kept state to the slow walk on every look, in every fixture:
7,288 looks, 0 disagreements. ⚠ One column of that gate is the one the suite cannot supply, for §4's
reason: a wrong key set makes a worse choice and never a wrong conclusion.

⚠ **And one assumption underneath it was a claim about the fixtures rather than about the design.**
*A goal is never denied* was the reason the goal-derived keys could accumulate monotonically, and
`{+nearer(?x)} ⟹ {-goal(nearer(?x))}` is an ordinary rule. So they are **counted**, not unioned: two
goals can put one relation in play, and one of them going away must not take the other's key with it.

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
licensed_by(<e>, <application>)     said_by(<e>, anna)     at(<e>, 09:14)
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
| `licensed_by`, `said_by` | ordinary propositions about the entry | the gate (§17), from the frame | yes, by ordinary matching |

⚠ **A fact about an entry that no rule can read is the R7 defect of §1, and this design has shipped
it repeatedly.** The licence naming which hypothesis produced a conclusion was a field for a long
time, so `why()` could answer *which hypothesis produced this* and no rule could (§17). The support
an entry rests on was a Python tuple, so nothing could ask what a conclusion depended on (§20). The
list above is short because the others were moved out of it.

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

### Exactly three members, and this has now been tested by removal

Licence, speaker and clock stamp are facts about the entry, never a fourth member. The discipline
matters: with optional slots, an entry becomes a node of variable arity whose members mean different
things depending on how many there are, which is the same shape carrying several membership
semantics — unreadable and uncomposable. The same discipline keeps the connective in §12 binary, with
timing as an adjunct fact.

⭐ **An earlier draft of this document had four members**, because §16 argued at length that an
entry's strength should ride the node match already returns. That argument is sound and it answered
the wrong question — it asked *where should a grade live* and never asked *what is a grade for*. The
answer, measured three ways, was **nothing**: it was carried, composed, printed, and never obeyed
(§16). So the fourth member is gone and this section's rule is back to what it always said.

> **A slot that is written, read, and never decided on is not a representation. It is a comment.**

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

### Variables are scoped to the statement that wrote them

A statement's variables belong to it. `?x` in one authored line and `?x` in the next are different
nodes, and this is not an implementation detail — it is what makes a rule a self-contained claim
rather than a fragment of a global namespace.

It is also a wall, reached from four directions, and each time the same repair works:

| what could not be written | why | the repair |
|---|---|---|
| a norm revised from the surface (§19) | `forbidden(doing(harm(?x)))` written twice is two descriptions | name the statement, or bind it from a rule |
| an exclusion as a corpus fact (§19) | the `?t` in the fact is not the `?t` inside the plan | conclude it from a rule, which binds the plan's own variable |
| a rule's patterns written by a corpus (§20) | a `fact` may not contain a variable at all, and separate lines cannot share one | build it with a **tool**, and reach the parts by binding |
| a rule composed from two others (§4) | both may say `?w` | standardise apart |

> **Reference is binding.** Anything deposited as an entry can be bound by an antecedent, and that is
> how a plan, a hypothesis, a rule or a norm is referred to. Names are for the exceptions — they buy
> **authoring** (a second surface statement about the same thing) and a stable handle. They never
> bought reference, and assuming they did was an error the design made explicitly and corrected.

### The cost, stated

**Resolving a read is the bundle's central program.** *Does `on(a, b)` hold here?* means *walk the
chain for entries naming this proposition at the locus asked about, and order them by §10's two keys*.

Earlier drafts said the engine must know what `entry` means. It must not, and §5 is why. What must
know is the **read program**, which is bundled data. The implementation may run it natively for
speed, subject to §4's floor gate.

Propositions have one identity however often they are built; **entries do not**. An entry is an act of
claiming, so two claims about the same proposition at the same locus are two nodes — otherwise
`mistaken(<e>)` would land on both the mistake and its correction. The same rule holds one level up:
**two rules that happen to say the same thing are still two rules**, with different authors,
precedence and provenance. §20 is where that stops being a nicety, because there a rule the agent
built and a rule the graph describes must be **the same node** or everything said about one is said
about nothing.

**Contradiction is permitted and undetected.** Two entries in one locus with opposite signs is a
shape the substrate allows. This is correct: consistency is a **question you ask**, not an invariant
the substrate maintains — the alternative is checking every write against every other claim. But it
means *is this moment consistent?* is a query somebody must run, and the design does not say who.

⚠ **And there is no vocabulary for incompatibility.** You can deny a proposition; you cannot say that
two propositions cannot both hold. That is a real gap, noticed when an older engine's `refutes` had
nothing to port to (§22).

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

### Sign and `not` are not rivals

The question is *should negation be a member or a wrapping term?* The answer is **both**, and the two
things that settled it were not arguments.

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

⭐ That sentence is §16's, word for word, one level down — and §16 is where it stopped being a pairing
and became the whole answer. Negation keeps both because the machinery genuinely computes with the
sign on every read. Uncertainty keeps only the term, because nothing ever computed with the field.
**The same argument reaches opposite conclusions about two things that looked alike**, and the
difference is measurable rather than aesthetic: one of the two members was read and obeyed, and the
other was read and printed.

**The translation runs one way, and the asymmetry is the design.** `+not(p)` becomes `−p`, so a corpus
written against signs reads a term the machinery manufactured while re-wrapping. The reverse — minting
`+not(p)` for every denial — is declined: it would double every negative fact and would build
`not(not(p))` on meeting its own output. That is the cost this section warned wrappers carry, and
declining the reverse direction is where it is not paid.

> **A rule that translates both ways meets its own output.** This is the general form, and §19 hits
> it again from the crossing side: a rule that crosses every hedged fact it sees crosses the hedged
> facts it just produced. Self-applying rules need a corpus to stop them, and that they must is a
> property of self-application rather than of any one rule.

`?` is untouched and stays a sign alone. It is a statement about *reading* — stop the walk, report
ignorance — and wrapping it as a term would make it look like a claim about the world. What a `?`
conclusion should become on the way out of a supposition is not settled (§22).

### What this leaves open

**`says` keeps its third member.** §15 carries the sign of a report as `says(channel, proposition,
sign)`, and the collapse to `says(chan, not(p))` is now *available* rather than required. Which one a
channel should use is unsettled, and so is whether allowing both is a corpus splitting into two
dialects.

**A `?` conclusion crossing out of a supposition** has no defined form. `+` and `−` both become terms
under the wrapper; `?` is a statement about reading and cannot.

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

### One order throughout, and a bug that made reference undefined

The two indices settle *which* entry wins. They do not, on their own, settle the order the walk
enumerates in — and that order is what *the most recent one* means when several entries satisfy a
description.

Measured, the walk disagreed with itself: ancestry was newest-first and a moment's delta was
oldest-first, so two candidates deposited by `implies` came out in the opposite order to two
deposited by `causes`. **Which connective a rule used has nothing to do with reference.** One
reversal makes the walk one order throughout, and *a description resolves to the most recent* becomes
a claim with a check behind it rather than an accident.

> **A deterministic computation whose result depends on an undeclared enumeration order has a
> tie-break nobody authored.** §19 states the same rule for rankings and for random draws; this is the
> version that governs the read.

### At-or-before is ancestry, not depth

The candidacy test walks the predecessor relation. It cannot be a comparison of depths, because
supposing forks the chain by construction (§16) and two moments at the same depth on different
branches are not comparable at all. This is the cheapest place in the design to introduce a bug that
only appears once hypotheticals are used — and it is also what makes §17's containment free rather
than enforced, so the two stand or fall together.

### What this costs, and what it is worth

The walk is the largest recurring cost in the design. Measured on a goal fixture before anything was
done about it, resolving reads was **86%** of runtime, and sixteen of every seventeen walks were the
same walk repeated. Three changes, each measured before the next and none of them touching what the
read *means* — ask the walk once per tick rather than once per rule, index the state by (sign,
relation), and index the resolution by proposition — gave **67×**.

It is also, per §4, **a program made of rules**: transitive closure over the predecessor relation, a
filter on locus, an ordering by two keys. Nothing in it requires engine support beyond structural
matching. That is the claim §21's floor gate exists to check, and it is the one most worth checking,
because this is precisely the program an implementation will write natively first.

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

> ⚠ **DESCRIBED AND NOT IMPLEMENTED.** An entry's locus is a moment, and only a moment: no span is
> ever built as one, and the surface has no way to write one. This section is a design for a
> convention that does not exist in the engine, and §22 records it beside `unless`. Everything below
> is argued rather than built, and the argument has not been checked by anything running.

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

**A rule relates two moments and is never a flat list of its patterns**, and both failures of the flat
form are worth naming because they are silent. The arity varies with how many members the rule happens
to have, which is exactly the shape §8 refuses. And the *signs* end up nowhere, so `{+p} ⟹ {+q}` and
`{+p} ⟹ {−q}` become the same node — one rule, silently, and a precedence claim then names a rule as
overriding itself.

### Notation

An earlier draft used punctuation — `@` for a locus, `→` for a pair of endpoints, `[...]` for an
interval — which made a handful of open-class concepts look like engine syntax. They were
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

**Endpoints and intervals are nodes.** §15's timing member relates two named endpoints and carries a
bound:

```
<t> = timing(<R1>, end(<A>), start(<B>))     which endpoints this is about
      bound(<t>, 4min, 7min)                 how far apart; absent means unknown
```

⚠ **One piece of notation was deleted rather than written out.** `@likely` on a consequent's entry was
a grade, and §16 records why there is no such thing any more. What a rule says about the strength of
its conclusion is now **in the conclusion** — `{+likely(rain(?d, afternoon))}` — where a rule can read
it.

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

The backward reader therefore declines what it cannot use — and §19's index over what a rule concludes
gives that decision a natural home rather than a special case: a bare-variable consequent has no
bucket, so it is never a candidate. **The real home for this is recall** (§19): which rules come to
mind when reading backwards is learned, and a rule that has never once helped a search is exactly what
recall should stop offering.

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

> ⭐ **A MEMBER MAY NOW SAY WHERE ITS ENTRY SITS**, which is the half of the skeleton that relates two
> moments. It is written out rather than punctuated — `+acts(goblin) at ?m` — because `@` used to mean
> a grade and reusing it would be §2's island on the page:
>
> ```
> rule <order> = implies( { +acts(hero) at ?mh, +acts(goblin) at ?mg },
>                        { +sequence(?mh, ?mg) } )
> ```
>
> The matcher had the locus all along — every entry carries one — and what was missing was a *pattern*
> for it. Built because a foreign corpus measured what its absence cost: **24% of its rules were clock
> scaffold**, a round counter re-implementing a moment ordinal, plus a token threaded through six
> acting rules and an arithmetic operator that existed only to count rounds.
>
> ⚠ **What it does not buy, and the limit is exact.** A matcher sees the **resolved** state — one entry
> per proposition — so two *different* facts at different moments are relatable and **a single fact's
> own history is not**: *it was on, then it was not* still finds nothing, because the superseded entry
> is not in the state. Reaching that means matching over the raw chain, which is what §6's stratum-0
> read is for, and it reopens the bootstrap question. The corpus that asked for this needed only the
> first half and never once wanted the second.
>
> ⭐ **And two bound moments can be ordered**, by a request rather than a skeleton member (§22 argued
> the shape; §19 is the seam):
>
> ```
> { +acts(?p) at ?mp, +acts(?q) at ?mq }  ⟹  { +order(?mp, ?mq) }
> { ... +precedes(?mp, ?mq) }             ⟹  { +acted_after(?q, ?p) }
> ```
>
> It is **ancestry, never depth** — §10's warning, and the reason `Moment.at_or_after` already existed.
> Unrelated moments get no answer rather than a false one.
>
> ⭐⭐⭐ **And a rule can only ever bind moments on its own walk.** A rule matches the state resolved at
> its own locus, so every entry it binds has a locus at-or-before that locus, and two such moments are
> both on one path. Measured on a chain forking 31 times: 145 orderings requested, **every pair
> related**. Containment was already guaranteeing the thing that makes ordering well defined — which is
> why the depth mistake is unreachable today, and why the ancestry test is kept anyway for the day an
> arrival's fork puts two branches within reach.
>
> ⭐ **And a member may name WHAT it matched** — `+on(?x, ?y) as ?t` — so a rule refers to a
> proposition rather than describing it twice. `at` says where; `as` says what. Verified to be the
> **same node**, so this is reference and not a copy, which §8's *a proposition has one identity
> however often it is built* is what makes true.
>
> Without it a corpus reaches the same place by **reconstruction**: match `+?r(?x, ?y)` and rebuild
> `?r(?x, ?y)`, which interning makes identical. That works and costs §3's index, since a variable
> relation has no bucket. ⚠ What does *not* work is two members hoping to co-refer —
> `+tagged(?t), +on(?x, ?y)` links nothing, and appears to work only while there is one candidate.
>
> ⚠ **Still absent**: `where` and the skeleton's *structural* members (`?n = succ(?m)`), §12's
> `?t = entry(...)` prefix form,
> and spans as loci — so §13's shapes remain unwritable and §15's *an arrival should be a moment* has
> no route. §22 records what is left.

The two kinds do not merge, because a skeleton member is **not a claim**. `?n = succ(?m)` has no sign,
no locus and no licence; nobody asserted it, and it cannot be denied, dated or attributed. §3 says why:
ordering is a fact about how a node is built, not a relation in the world. The skeleton is the part of
the antecedent that match settles by unifying structure, rather than by walking a chain for entries.

Distinctness belongs in the skeleton for the same reason. `?a ≠ ?b` is a condition on the binding, not
a dated claim that two individuals differ.

⚠ **And the skeleton has a consequence nobody designed for.** An entry's *support* — what it was
derived from — is skeleton by exactly this test: it is how the entry was made, not a claim about the
world. So it is readable by stratum 0 and not by ordinary rules, and §20 runs into that wall from the
learning side, where the agent's own trail would be the best source of examples it has. §22 records
it as open, and it is not a small question.

**An antecedent is a sequence, and the positions are load-bearing.** §18's tiebreak reads the entries
an application consumed, and `consumed` is filled by member *position* — so authored order is what the
trail and the arbitration stamp see. This has a direct consequence for optimisation: the **walk** may
be reordered freely (§3's argument index does exactly that, pivoting on whichever member binds first),
and the **antecedent** may not. Narrowing removes only candidates unification would have rejected, so
the matching applications and their order are identical, which is why nothing downstream had to change.

⚠ That invariant can be broken with a whole suite still green — filling `consumed` in walk order
rather than member order fails nothing, and the arbitration gate cannot see it either, because it
compares two paths that would permute alike. It is asserted directly, by a fixture built so that the
pivot-first walk actually runs.

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
is a cache of a derived value, invalidated by learning a rule or gaining an authority, which is §3's
own condition on indices failing at the level of a mark.

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
    then   +boiling(?w),  −liquid(?w),  entry(?m', volume(?w), ?) )

<t> = timing(<R1>, end(<A>), start(<B>))     bound(<t>, 4min, 7min)
unless(<R1>, +altitude(?w, high))
```

```
<R2> = implies(
    given  +cloudy(?day, morning)
    then   +likely(rain(?day, afternoon)) )
```

`<R2>` is where the deletion of the grade shows on the page. What used to be an annotation on the
entry — invisible to every rule — is now an ordinary proposition, and a corpus can ask which of its
beliefs arrived this way, decline to act on them, or cross them into a supposition (§16).

### Reification, and what it must not lose

A rule is data from the moment it is authored:

```
rule(<R>)     conn(<R>, implies)
ant(<R>, pattern, sign, i)      con(<R>, pattern, sign, i)
```

⚠ **Both the position and the sign are members, and leaving either out makes a rule read back out of
the graph a different rule.** Position matters because an antecedent is a sequence (above) and because
relation instances intern — a rule with two identical members would silently lose one. This only
became visible when something read a rule back out and expected to get the same rule (§20), and it is
worth noting how it could have stayed hidden: reading members back in *minting* order reproduces
authored order by accident for anything the machinery itself wrote, so a check over that could never
have failed. The fixture deposits out of order on purpose.

### Scoring the form

| | (A) guard → program body | (B) one rule per direction | (C) `connective(moment, moment)` |
|---|---|---|---|
| not leaking | ❌ the backward read is hypothesis wearing entailment's clothes, with nowhere to record it | ❌ two statements drift; neither is the other's premise | ✅ one statement; each reading cites `<R>`, whose licence says what the citation is worth |
| not lossy | ❌ what it makes true is recoverable only by running it | ⚠ the pair coheres only by convention | ✅ `<B>` **is** the postcondition; `?` preserves a gap instead of erasing it |
| readable | ❌ runnable, not askable — fails R4 | ⚠ readable, doubled | ✅ every question about a rule is a query over its members and adjuncts |
| composable | ❌ two bodies cannot be joined | ❌ n directions means 2ⁿ statements | ✅ join on signed membership; no-entry survives composition as no-entry, so two partial rule sets merge without lying |

(A) fails an additional test outright: `overrides(<R1>, <R2>)` has no subject when a rule is a program.
Nothing can be said *about* it, so R3 is unreachable — and §20 is unreachable entirely, because a rule
the agent authored has nothing to be authored *as*.

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

> ⚠ **NEITHER OF THOSE TWO RULES CAN BE WRITTEN IN ANY CORPUS THIS ENGINE LOADS.** They use §12's
> skeleton, which is not in the surface, and they conclude at a span locus, which no entry can have.
> *Taking turns* is this document's worked example of a shape and it has never run. The section is
> kept because the argument for describing an extent rather than enumerating it is independent of
> whether spans are built — but every code block in it is a proposal, and §22 records the gap.

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
*how many times did this shape step here* is a walk over the trail — derived, dated, never stored.
§16's refusal of numbers does not transfer: it was specifically that probabilities need independence
assumptions unstatable in the graph, and a count of applications is an exact observation of the trail,
where comparison is not composition.

⭐ **Counting over the trail is also what §16 hands the evidence problem to**, and §20 is where it
becomes a mechanism: how often a rule helped, and how often it harmed, are counts over exactly this
walk. The trail keeps turning out to be the training data for whatever needs training, which is why
R5 keeps being promoted from a nicety.

### Two bounds, which must not share a slot

| | *they take at most five turns* | *expand this at most five times* |
|---|---|---|
| what it is | a **claim about the world** | a **budget on the agent's effort** |
| where it lives | `repeats`, on the shape — attributed and defeasible | §19's budget |
| can it be wrong | yes; a sixth turn is a **surprise** | no — it is not about anything |
| exhausting it yields | *no* | ***I don't know*** |

Fuse them and *the shape ended at five* becomes indistinguishable from *I stopped at five*. That is
§9's `−` against *no entry*, and §19's *nothing applies* against *nothing came to mind*, arriving a
third time, so it takes the same answer:

> **Bounded expansion returns a result and a state, never a result.**

⚠ And the budget half is itself a claim, so it is a **fact**, not a constant: `{+bounded(?w)} ⟹
{+period(8)}` deepens a search when a subgoal drags, and `{+goal(doing(?p))} ⟹ {+tolerance(4)}` makes
an agent harder to convince when the next step cannot be taken back (§19). *How hard am I trying* has
a trail rather than a threshold somebody chose once.

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
is a fact about the **entry**, not a new construct.

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
* **§21's commutation gate runs per instance, to a depth**, rather than as a property over the whole
  rule set.
* **Backward expansion can mint unboundedly.** §11's discipline — spans are minted by recognisers, never
  enumerated — becomes the stronger requirement that expansion is demand-driven and budgeted, with the
  cycle care §10 asks of any walk over derived structure.
* **A shape is two rules where an author expects one.** Recall is keyed by what a rule concludes and by
  what the situation is about (§19), so nothing guarantees that a base case and its step case surface
  together.
* **And composing a recursive shape is unrolling**, which is unbounded — so §4's composition takes the
  same budget-and-state discipline as expansion.

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
* `enables(A, B)` is `causes(A, {+possible(B)})`. Read backwards, the two are told apart by what the
  consequent *says*: a bare `B` means doing `A` achieves it; a wrapped one means `A` is a precondition
  and something else must still happen.

⚠ The second row used to read *told apart by the grade*, and rewriting it is the clearest small
demonstration of why the grade had to go. A distinction carried in an annotation is a distinction no
rule can draw. Carried in the conclusion, `enables` is decomposed by a corpus that can also argue with
the decomposition.

### Why the remaining two do not collapse

The distinction is not *logical versus worldly*. It is mechanical:

> **Retract the antecedent. Does the consequent go with it?**
> **Yes → `implies`.** The entry is *derived*. It lands in the **same** moment.
> **No → `causes`.** The entry is *asserted*. It persists, and lands in a **later** moment.

Water you have stopped heating stays boiled. That is inertia, and it is why a zero-delay cause is
still not an implication: the two cannot be merged by setting the delay to zero.

`<R2>` in §12 is the argument for keeping both. *Cloudy morning implies likely rain* passes the
persistence test as `implies` — learn it was not cloudy and the rain claim goes with it — but the
surface wording reads just as easily as causal, and clouds do not cause the afternoon's rain; a front
causes both. Written as `causes`, the backward reader produces **a plan to make it rain by making it
cloudy**. The two-connective split is precisely what makes that plan unwritable.

⚠ **And the connective decides one thing nobody expected it to.** §19's criterion — *an occasion
warrants a re-ask only if re-asking cannot produce one* — is satisfied or violated by which connective
an author reaches for, because `implies` does not move the seat and `causes` does. The same rule
written the second way mints a fresh occasion, which warrants the next re-ask: measured, 143 askings
of one question and no end. **Neither reading of the connective is about re-asking**, and the author
has no way to see it from the page.

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
moment along. The backward direction is not, and §22 records it.

### What is not a connective

Interval relations — *before*, *during*, *overlaps* — are ordinary facts about moments and spans,
which are already nodes. Adding them to a closed set would buy nothing and would start the
multiplicative growth §15 and §16 are designed to avoid. The same verdict retires `likely_causes` and
every fused name of that family: it fuses strength with defeasibility, records neither, and the name
set grows multiplicatively.

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
<e2> = entry( <afternoon>, possible(rain),   + )      licensed_by(<e2>, <e1>)
```

`<e2>` is deposited now, is about the afternoon, and is believed on Anna's word — three different
times and one authority, none of which needs a construct that does not already exist. That the claim
is hedged is *in the proposition*, so a rule can decline to act on it (§16).

### Acting is a channel read the other way

Channels carry the world in (§17). Acting carries an intent out, and needs no new construct for the
same reason an action needs none: a rule concludes `+doing(p)` like any other fact, and the machinery
carries it past the boundary because a boundary is anchored and a rule is generic.

Three things about the write that follows, each found by building it.

**The agent asserts the act.** *To execute means make this event-fact true*, so having acted, the
agent writes `+heat(anna, kettle)` — licensed by the doing, not by any report. That is not a claim
about the world's response. It is what gives the rules something to apply to, and it is what gives the
expectation of §18 something to be disappointed by. Without it the agent emits an intent into silence
and nothing downstream ever happens.

⭐ And it is a **rule**, `<assert-act>`, which is the first place in this design where a strategy
written as code became a claim: an agent that should *not* assume its acts succeed is now expressible
by dropping one rule, and it still acts and still knows it acted.

**A description cannot be acted on.** `+doing(heat(?a, ?w))` is refused: an intent with an unbound
member names no particular act. This is §12's achievability arriving where it belongs — not as a mark
on a rule's member, but as a condition at the one place effects leave the agent.

⚠⚠⚠ **And that refusal has a consequence the design did not intend.** A rule node is generic by
construction, because it holds the variables of its own patterns. So `+doing(ask(<hot>))` — *ask the
author about the rule that lost* — is refused for the same reason, and **every clarification request
about a rule is decided on and never emitted.** This is the use/mention distinction of §5 arriving at
the boundary, where the entry already carries the information needed to tell the two apart and nothing
reads it. §20 is blocked on it and §22 records it.

### What a channel reports is signed

An arrival needs a sign, and a proposition has none — only an entry does (§8). So *the gauge says it
is not boiling* has nowhere to put the negation. Writing `−says(gauge, p)` says the gauge stayed
silent, which is a different fact and not the one observed.

The shape in use is `says(channel, proposition, sign)`, with the entry always positive: the channel
did speak. That puts a sign inside a proposition, which §18 warns against, and it is the same
compromise reification makes when it stores a rule's signed members.

**Two better answers exist and neither is built.** An arrival should be a **moment** — a report is a
signed delta, and trust is then a rule relating two moments rather than a rule per sign; that needs
§12's skeleton. Alternatively §9's remaining question settles the other way and the third member
disappears on its own.

### An arrival is not something the agent does

Crossing the boundary is irreducible — a channel is anchored and a rule is generic. Crossing it **on
the agent's schedule** is a claim, and a false one.

> **An arrival is an external event, and an external event is not something the agent does.**

So delivery is the boundary calling in, at the moment the world speaks, rather than a first line of
the loop. What remains in the step is a *counter* — how much arrived since the last one — because §19
needs *nothing applied* and *nothing arrived and nothing applied* to be different silences.

The behavioural difference is visible without running anything: a report is on the graph the moment
the world speaks, and *what it means* still waits for a rule to be selected. Those were the same
instant while intake was a phase, and they are two different things.

---

## 16. Modality

*Saying how strongly.*

This section is a re-derivation. An earlier draft argued at length for an ordinal **grade** — a fourth
member on the entry, composed by weakest link, computed by the gate. The argument was sound and it
answered the wrong question; the measurement is in this section, and the conclusion is that there is
no grade. What replaces it is smaller, and it is made entirely of things Part II already provides.

### Four things called possibility

They must not share a slot.

| | what it is | where it goes |
|---|---|---|
| **strength** | how firmly this is claimed | **a wrapping proposition**: `likely(p)` |
| **confidence** | how far the agent trusts where this came from | an ordinary **claim about the source** (§17); moves with evidence |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules: `unless`, `overrides` |
| **achievability** | whether *this* agent can bring it about, now, within budget | **nowhere** — derived at read time from capabilities, budget and the rule set (§12) |

The fourth is the one with no storage at all, and that is the point: it is relative to the reader, so
any place to put it is a cache of a derived value.

Collapsed into one number, `0.6` means three things at once, and combining two such numbers is
arithmetic nonsense. Defeasibility is the load-bearing one for reasoning — *unless the front has
already passed* — and it needs **no numeric apparatus at all**: it is the same precedence machinery
that makes the boss's rule beat the vice's.

**Confidence is a property of the source, not of the rule.** *How sure am I of this rule* and *how
sure am I of this sensor* and *how far do I trust this speaker* are one question asked of three
sources, and §17 makes every entry name the source it arrived through. Rule-confidence is then the
case where the source is the knowledge base. One mechanism covers all three; a confidence slot on
rules would cover only the first and would have to be reinvented for the other two.

**Strength is per-conclusion, not per-rule.** One rule has consequences of different firmness: heating
boils the water and scorches the pan. A rule-level annotation cannot express that; it is at best
shorthand for *all conclusions the same*. So whatever carries strength has to sit on the conclusion —
and the question this section exists to settle is *what kind of thing carries it*.

### The rejected answer, and why it was rejected

The candidate was an ordinal **grade**, stored as a fourth member of the entry. The argument for it
was good, and it went like this.

Not on the proposition node — and not for reasons of cost:

> A grade stored on a proposition node is **a cache of a derived value**. *Rain is likely* holds only
> given the support that produced it, so when the support changes the tag must be invalidated. General
> invalidation over a web of dependencies is a truth-maintenance system: a second machinery, with its
> own consistency problem, running underneath the first. **An index over what was asserted is
> storage; a cache of what was derived is a truth-maintenance system.**

And not as a separate tag, because **a tag is a separate read**: reading a fact and reading its grade
would be two operations, so the grade could be obtained without the fact or the fact without the
grade — and an ungraded conclusion reads as certain. The repair proposed was elegant. *The strength
must ride the node match already has to return.* An entry cannot be matched without its sign, because
the sign is a member; put the grade there and it cannot be matched without its grade either. One read,
or none. And the entry had to exist anyway, so the slot cost nothing structurally.

That argument is valid. Every step of it is right. It settles **where a grade should live** and never
asks **what a grade is for**, and the second question has an answer that dissolves the first.

Measured three ways, and they agreed:

* **It ranked last of three treatments.** A grade is **not a term**, so no rule can ask *is this
  merely likely*. There is no guard to cross, because a grade annotates a conclusion the actor still
  sees and can still ignore. And it does not nest, because a grade has no place inside a term.
* **Almost nothing used it.** Across a whole suite, **4 of 3,740 rules** authored a non-certain grade
  and **6 of 32,289 entries** carried one.
* ⭐⭐⭐ **Nothing ever decided on it.** The function that compared two grades was called from exactly
  one place. Every other read carried the grade forward or printed it. The grade was **carried,
  composed and printed, and never obeyed** — and it could not be obeyed, precisely because it is not a
  term.

> **A knob that is read and not obeyed is the same defect wearing the fix's clothes.**

So the fourth member is gone, the closed set of five ordinal names is gone, and the entry is back to
§8's *three members and never a fourth*.

⭐⭐⭐ **And the closed set going is the larger half.** Five names the engine knew became whatever
modalities a corpus cares to write, with whatever ordering it authors. That is §4's *closed is a rate,
not a kind*, one place further down than anyone had applied it.

### What replaces it: modality is a term, and supposing is how it composes

Modality is a **proposition** — `likely(p)`, a wrapping node, the same construction as `on(a, b)` with
one arm rather than two. A hedged fact is then crossed by **entering** it:

> **Unwrap on the way in. Re-wrap on the way out.** Inside the frame the assumption is an ordinary
> fact and the ordinary rules apply to it by ordinary matching. What crosses back is `likely(q)`, a
> claim about what was concluded under the supposition — never `q`.

Three things this buys that a grade cannot, none of them arguments:

| | grade on the entry | term, supposed |
|---|---|---|
| a **rule** can ask *is this merely likely* | no — a grade is not a term, so no antecedent can name one | yes |
| the guard **holds** — nothing acts on the unwrapped conclusion | no; a grade annotates a conclusion the actor still sees | yes, structurally |
| it **nests** — `thinks(anna, likely(rain))` | no; a grade has no place inside a term | yes |

**Weakest link survives, as structure rather than as arithmetic.** Two uncertain premises give
`likely(possible(c(t)))`. Where `min` gave one ordinal and forgot which premise was weak, the nest
records both, in order. That is a better answer to the same requirement, and it was already built
before the grade was deleted.

⚠ **What is lost, stated rather than buried.** Weakest link was **automatic and total**: every write,
every rule, nothing authored. Now nothing is concluded from an uncertain premise unless a corpus
**crossed**, and what comes back is nested. Collapsing the nest — `{+likely(possible(?x))} ⟹
{+possible(?x)}` — is a corpus's table and its ordering is a corpus's claim.

> **The ordinal stops being free and starts being arguable.** That is the trade, and it is the trade
> this design makes everywhere else.

⭐ **And the deletion was worth something two sections away.** §4's composition refused anything but a
`certain` conclusion, because composing a grade would have been a minimum computed once from
defeasible constituents. With grades gone the objection goes with them, and the restriction was
deleted rather than solved.

⭐ **It also made a corpus's recklessness visible.** An agent acting on a merely-possible
classification used to be indistinguishable from one acting on a certain one, because a rule matching
`is_gothic(?c)` matched whatever grade the entry carried — nothing could read a grade, so nothing
could decline. Now declining is one line, and *what this corpus is willing to act on* is a claim with
a trail.

### Supposition and weak connection are different problems

The word *likely* covers two things, which is why *tag it or guard it* felt like a forced choice:

| | *I am supposing this — what follows?* | *this generally holds, weakly* |
|---|---|---|
| shape | a **moment** you enter and leave (§7) | a **wrapping proposition** on the conclusion |
| how many | few, deliberate | many, independent |
| nesting | free — a path in the predecessor tree | free — terms nest |
| isolation | already enforced — a read cannot reach into a moment except through the chain | not an isolation problem at all |

Under the grade, the right-hand column was a different *kind* of thing from the left. It is not: the
wrapper is what a rule concludes, and the supposition is what a rule does about it, and one ordinary
rule connects them.

```
<cross> = implies( { +likely(?p) }, { +suppose(?p, likely) } )
```

**Containment is free rather than enforced.** The frame's seat is a *successor* of the caller's, so
the caller's walk cannot reach it. That is §21's containment gate, and it is §10's ancestry doing the
work — which is why at-or-before must be a real ancestry test and not a depth comparison, since
supposing forks by construction.

### The cost is a frame per derivation, which is linear

The standing objection to supposition is combinatorial explosion: twenty independently uncertain facts
would be a million moments. That objection does not survive the distinction between a frame per
**subset** and a frame per **derivation**.

> **Crossing `likely(p)` is one hypothesis, and more when something says so.**

`<cross>` above is an ordinary rule. Considering the other case is another ordinary rule. So **there
is no branching factor in the machinery to set** — the number of branches is however many `suppose`
facts get concluded, gated on whatever a corpus gates them on, and adding one to the interpreter would
be §18's mistake again.

Why the default has to be one, stated as a cost rather than a preference: at one branch per uncertain
fact, what is spent is a frame per derivation, which is linear. At two branches, *n* independent
uncertainties give 2ⁿ combinations and the objection returns intact.

> **The first branch is free and every branch after it is exponential.** Which is exactly why the
> second must be earned.

Two things this costs that were not obvious, and they are the same thing twice.

**The alternative must be opened on resume.** Proposed alongside the first, it is enacted while the
register is already *inside* it — so it becomes a sub-hypothesis rather than a sibling, and the second
case comes back wrapped in the first. `left(<frame>, <assumption>)` is the occasion for *this
hypothesis is over*, and opening the alternative there is what makes them siblings. That is what the
frame **forest** (§17) was for.

**A crossing rule that can match its own output runs away.** A discharged conclusion is itself
`likely(...)`, and a rule keyed on `left` fires again when the alternative is left in turn — measured,
32 sibling frames before the budget stopped it. §9 already records this trap for `<denial>`. The
corpus stops it, and that it must is a property of self-applying rules rather than of this one.

### The rejected alternatives, scored

| | (A) an ordinal grade, on the proposition | (B) an ordinal grade, on the entry | (C) a guard node per uncertain fact | (D) modality as a term, crossed by supposing |
|---|---|---|---|---|
| not leaking | ❌ *likely* said of no occasion and every occasion at once; the author meant *likely given this support* | ✅ a conclusion drawn in a moment **is** in it | ⚠ the guard says uncertain-in-general, so it leaks like (A), more loudly | ✅ the wrapper is part of what was claimed |
| not lossy | ❌ a number with no premise | ✅ the support survives | ⚠ says *that* it is uncertain, not on whose word | ✅ the nest records **which** premise was weak, which `min` discards |
| readable | ⚠ readable and stale | ⚠ **readable by a program and not by a rule** — the defect that decided it | ⚠ two shapes for every consumer | ✅ an ordinary proposition; *which beliefs are merely likely* is an ordinary query |
| composable | ❌ two tagged facts combine to *what?* | ⚠ composes by an arithmetic no rule authored | ❌ every consumer handles guarded and bare | ✅ composes by nesting, and the collapse table is a corpus's claim |

(B) is the interesting column, because it is the one that was chosen and then removed. It scores well
on three criteria and fails on the one that turned out to matter, and the failure is not visible in a
table of shapes at all — it is visible in a **census of use**. That is the argument for §4's rule that
descent to a closed class must be measured.

(C)'s failure has no middle setting, which is worth naming: **optional guards mean consumers handle
two shapes and forgetting returns; mandatory guards mean an extra node and an extra hop for every
certain fact in the system.**

But the guard instinct is right about one thing — **forcing the handling**. A wrapper compels nothing
by itself, and *do not act on a merely-possible fact without acknowledging it* is a real requirement.
It belongs at **the one place effects leave the agent**: the write where an action is dispatched, where
the set is small and known, rather than making a million reads cross a guard in order to catch the one
that matters. Under (D) that check is expressible as an ordinary rule, because the wrapper is a term —
under (B) it was not expressible at all.

### The same construction, a second use: change

*Saying what changed, and which way.*

The wrapping proposition was derived above for uncertainty. It is not specific to it, and the second
use is R6's own example: **pouring raises the level, by an unknown amount.**

§9 gets half of it. `?` invalidates without replacing — it stops the walk and reports ignorance —
which is exactly what *by an unknown amount* needs, and it is why `?` had to be a distinct sign.
What `?` cannot say is **which way**. *It changed* and *it went up* are different claims, and the
second is the one a planner needs.

Direction is not a fourth sign. A sign is a member and a closed class, and *rises*, *falls*, *doubles*,
*drains* are open-class domain content — §4's floor may not mention reality. It is a **wrapping
proposition**, on the construction this section already derived:

```
rule <pour> = causes( { +pour(?w, ?g) },
                      { ? level(?g), +rises(level(?g)) } )
```

**Both members, and that is §9's pairing arriving a third time.** The wrapper alone leaks: §9 says no
entry means *inherit*, so without the `?` the chain still answers the old level and the agent reports
a stale value as current belief. The `?` invalidates; the term says which way. Negation keeps a sign
**and** a term for the same reason — *the member is what the machinery computes with, the term is what
survives nesting.*

**And what the term MEANS is a corpus's definition, mentioning a before and an after:**

```
rule <rise-means> = implies( { +rises(?q), +before(?q, ?v0), +after(?q, ?v1) },
                             { +greater(?v1, ?v0) } )
```

⭐ **The definition needs no locus, and that is what makes it work today.** Before and after are
**values** — members of a proposition — not moments. So nothing has to relate two loci, the skeleton
never comes into it, and this runs on the engine as it stands. Measured: the term is held, the level
is invalidated, and the definition derives `greater(cm7, cm2)`.

| | (A) a fourth sign, `↑` | (B) a fact about the entry, `rises(<e>)` | (C) a wrapping proposition, defined in the KB |
|---|---|---|---|
| not leaking | ❌ a closed class that must grow with every domain verb; and the floor would mention reality | ⚠ one hop from the proposition, so a rule wanting *the level is higher* reasons about an entry instead | ✅ the direction is part of what was claimed, at the locus it was claimed about |
| not lossy | ⚠ direction only; *what it means* is nowhere | ⚠ same | ✅ the definition is in the corpus, so *what does rises mean here* is a query |
| readable | ❌ no rule can name a sign | ✅ ordinary matching | ✅ ordinary matching, and it nests — `likely(rises(level(g)))` is well-formed |
| composable | ❌ every consumer must handle a growing sign set | ⚠ two corpora attach different facts to one entry | ✅ two corpora may define `rises` differently, and they can disagree in the ordinary way |

**What this does not settle**, and it splits cleanly into two halves this design tracks separately.
The **magnitude** — *by an unknown amount* — is §22's constrained-not-bound value, and the wrapper
**defers** it rather than solving it: holding `rises(level(g))` never requires minting a value that is
constrained but not bound, and the question arises only when something asks, which is the demand
criterion below. The **moments reading**, where before and after are meant as loci rather than values,
is a different matter and needs §12's skeleton or the narrower substitute §22 records.

> **Three separate gaps sit behind one English verb, and holding the verb as a term is what tells them
> apart.** Direction is expressible now; the expansion across two moments is not; the amount is not.

### Superseded, not invalidated

If a stored strength is a cache, is a stored derived *fact* not also a cache? No — and the difference
is the reason the whole design is dated.

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

### Losing your reason is not acquiring a counter-reason

The dating above says nothing about what happens when the *support* of a conclusion goes away — a
source discredited, a binding withdrawn, a premise denied. The machinery's temptation is to retract,
and it must not.

> **A discredited source does not make what it told you false; it leaves you without a reason, which
> is a different state and the one you can act on.** An engine depositing `−p` here asserts something
> nothing justified.

So what ships is an **occasion**, and the reaction is a corpus's:

```
rests_on(<entry>, <entry>)     what an entry was derived from -- STRUCTURAL (§12's skeleton)
support(p)                     a request, asked by a corpus rule
unsupported(p)                 the answer, deposited only when nothing does
```

There are at least four sensible reactions and the design picks none of them: `{+unsupported(?p)} ⟹`
`{−?p}`, or `{+goal(?p)}`, or `{+doing(ask(?p))}`, or nothing at all.

⚠ **Asked, never volunteered** — `blocked`'s reason exactly (§5). A proposition may rest on several
things, so one withdrawal says nothing until the rest are looked at. Legitimate at `quiet`, a lie
before it.

⚠ **Unsupported and false differ in both directions.** A denied *fact* is not unsupported: it was
asserted, so it never had a reason to lose.

⚠⚠⚠ **And this composes with binding revision only because a hole was closed.** Answering *is this
subgoal already satisfied* built its environment by **reading** a plan's bindings and never consuming
them — so a conclusion that relied on *which tap* did not rest on the entry that said which tap. R5
says every entry has a licence; §12 says a conclusion is no stronger than what match consumed. Both
were true and **both were vacuous**, at the one place a plan commits to something. Only the bindings
the goal actually uses are consumed, because consuming the whole environment would make every
sibling's conclusion rest on every other sibling's choice.

### Does the design run out of dimensions?

The worry behind every new distinction is that it needs a new dimension of the representation. It does
not. Everything spent so far:

| | why it could not be a node |
|---|---|
| **identity** | *this node is that node* is not a relation between two things; it is the precondition for there being two things |
| **connection** | an edge |
| **order among connections** | *the second member* — position is not a thing in the world |

Everything added since — type, sign, licence, time, authority, span, commitment, modality — is a
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
| `+boiling(?w)` in the consequent | mint the entry; stamp locus, licence and source from the frame and this application |

> **The rule's members are what the author knows. The entry's members are what the application knows.**

Locus, licence and source do not exist until the rule runs. That is the whole split.

| | (A) augment the rules | (B) authors write entries natively | (C) the machinery absorbs it |
|---|---|---|---|
| not leaking | ❌ explanations show the rewrite, not the rule | ❌ an author supplying a deposit stamp can date a claim to when it was not held | ✅ every entry is stamped by the write that made it |
| not lossy | ❌ two shapes; *why* must un-augment | ✅ | ✅ |
| readable | ❌ three times the plumbing per rule | ❌ every rule is plumbing | ✅ the rule reads as written |
| composable | ❌ resolution policy frozen at augmentation time | ⚠ | ✅ resolution can change without touching a rule |

(A) additionally cannot be written at all, per the indexical above.

### The gate

An entry is both a mechanism and a node a rule can point at. Reading is how *a claim Anna made
outranks one Bo made* gets stated at all. Writing is where soundness lives, because §20 makes the
support trail load-bearing for what the agent learns and §16 for what it is willing to act on.

The requirement that follows is narrower than it first appears:

> **No write bypasses the stamp.**

*Only the machinery may write entries* is one way to achieve that, and it is stronger than necessary.
What must be impossible is an entry whose provenance is **absent or false**. What need not be
impossible is an entry a rule caused to exist — every such entry arrives through the gate and leaves
it stamped with the rule that caused it, which is not forgery but the ordinary record.

Note the division against §4. The **stamp on the mint** is floor: unconditional, nameless, and not
something a rule reads. The **gate** is the bundled convention that turns that stamp into vocabulary —
locus, licence, source — so that the agent can reason about its own provenance. Remove the convention
and the guarantee remains but the agent goes blind to it; remove the floor item and the convention is
forgeable.

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

### The gate is where the doors are, and there are three

The write is not only where provenance becomes vocabulary. It is where everything anchored happens,
because a rule is generic and each of these needs something a generic rule cannot name:

| door | what crosses | why a rule cannot do it |
|---|---|---|
| **dispatch** | an intent, outward | no rule can name the agent's own edge |
| **enter** | the register, inward | entering a frame moves the register (§4 item 3) |
| **adopt** | a rule, inward | §20 — a rule becoming live is not a question, it is an act |

> **A door is not a question.** Doors are distinguished from the *answerers* of the next section
> precisely by having no verdict to reach: what decides that a rule is worth adopting, or an intent
> worth emitting, is a corpus concluding it. What happens then is not a judgement.

The **norm veto** is at the same place and is not a door: it refuses (§19). And dispatch is at the
write rather than polled once a tick, because that is what keeps a supposed act inside the agent
rather than emitting it and regretting it (§19).

### Channel is not authority

Every entry names where it arrived from, and that has two layers which must not be fused:

| | what it is | can it be wrong |
|---|---|---|
| **channel** | the intake path — this socket, this sensor, the knowledge base | no: mechanically observed, like a sensor that cannot misreport its own reading |
| **authority** | who is taken to have spoken, and what their word is worth | **yes** — an ordinary claim, defeasible |

The knowledge base is a channel like any other. Reading it faithfully is guaranteed; what it **says**
is as contestable as ever, which is what §12's `by(<R>, boss)` and `overrides(<R1>, <R2>)` depend on.
Fusing the two would make authority unforgeable by fiat, so that anyone reaching the right socket
would thereby be the boss.

⭐ **Splitting a phase shrinks it rather than relocating it**, and intake is the demonstration: the
boundary became the smallest unarguable record — `arrived(channel, proposition, sign)`, sourced to the
channel — and *what a report means* became a rule. Provenance landed where this section says it
should: the raw arrival unforgeable, the saying above it derived and arguable.

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
or abandoned.

What does a conclusion look like on the way out? It does not come out.

> **Conclusions stay at their locus. What crosses is a claim *about* the frame, made outside it.**

Copying a conclusion out and re-qualifying it is the alternative, and it fails on this design's own
terms: it makes one fact exist in two shapes, which is the objection to augmentation above, and it
needs invalidation the moment the supposition is discharged differently, which is what §16's dating
exists to avoid. So a caller that has learned something from a scenario writes a **new** entry at its
own seat whose proposition is about the scenario.

**Adopting** a hypothesis is a separate, deliberate, licensed write — the same shape as deciding to
trust a channel, which is the point at which *the user says it is raining* became *it is raining*.

### Which hypothesis reached which conclusion

`left(<frame>, <assumption>)` says *this hypothesis is over*. It does not say what it found, and for
a long time nothing did — which was easy to miss, because the information was never lost. Every
conclusion carried out of a frame is written with a licence naming the frame, so *why* could always
answer *which hypothesis produced this*, and **no rule could, because a licence is a field on the
entry.** §1's defect, and the eighth instance of it.

```
concluded(<frame>, <what>)       this hypothesis reached this
```

**What it costs is one write and what it buys is rivalry.** Two suppositions about the same symptom
both cross their conclusions to the same parent as `likely(q)`, and until this a corpus could open
rivals and then not compare them — the conclusions were siblings with nothing distinguishing their
origins. The discriminating case is deliberately *not* that the rivals disagree: what tells two
diagnoses apart is a prediction only one of them makes, so the comparison is a join over a shared
conclusion and a distinguishing one.

⚠ It records that the frame **reached** the conclusion, not that the conclusion is true, so it is
deposited `+` whatever the conclusion's own sign was. And it is bookkeeping, so a nested frame does
not carry `likely(concluded(...))` out — a record of the machinery's own event is not a claim about
the world for a wrapper to qualify.

### A supposition must not own the loop

Supposition looks like the hardest thing here to make interruptible, because entering a frame
genuinely needs the register. That part is three lines. The rest of it, in the implementation this
design was written against, was a **nested run of the loop** — called inside itself, to quiescence,
before returning.

That is a subroutine call, and it is the exact thing §18 spends its length refusing. The design had
that sentence aimed at corpora, and the machinery was doing it: a supposition owned the agent from the
moment it opened until it was exhausted, so nothing could preempt reasoning carried out under a
hypothesis — the one place an agent most needs to be interruptible.

The repair needed no new mechanism, only the removal of one. **Entering is a write.** **Leaving is
quiescence** — when the loop finds nothing more to do *here*, and *here* is inside a supposition, that
is not the end of the run but the end of the supposition. Three things followed at once: the caller
keeps control between every step, the supposition's own reasoning appears in the caller's trace, and
the depth budget stopped being a second, nested budget.

> **A convention hidden in vocabulary is easy to see and cheap to move; a convention hidden in
> control flow is invisible and expensive.** The name census counts names, and names were the easy
> half.

### Costs

* **A bug in the gate is systemic** — every fact in the system gets the same wrong provenance.
  Mitigated by it being one place, which makes it one check.
* **Matching becomes a chain walk rather than a lookup**, and that walk now sits on the rule-matching
  path, not only on reads.
* **Matching must record which entries it matched.** Otherwise *because a was on b, on Anna's word*
  has no answer. This is not overhead: it is half the trail, and §16, §19 and §20 all depend on it.
* **Every seat move is a write**, so deliberate reasoning about the past leaves a trail proportional to
  how often the agent shifts its attention, not to what it concludes.
* **Nothing stops a frame being seated somewhere useless.** A seat that is not an ancestor of its topic
  is as meaningless as §11's inverted span, and takes the same remedy: check it where the frame is
  minted.

---

## 18. The machinery's own state

*Saying what I am doing.*

This section is R7 applied to the agent itself: goals, plans, commitments, expectations, surprise.
Under §5's test every name here is a convention.

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
selectable — which is why they can be preempted and an interpreter's cannot.

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

⚠ **And noticing a deviation is four rules, not one comparison.** Two expected signs against the two
ways an observation can contradict one: the opposite sign, and `?`. As a single comparison, the
machinery was quietly asserting that §9's *invalidated, and I cannot say what replaced it*
disappoints an expectation exactly as much as the opposite outcome does. That is a real claim, it may
be wrong, and as a branch there was nowhere to argue with it.

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

⚠⚠ **And starvation is not only the surprise rule's problem.** A rule that would *settle* a conflict
can be starved by the conflict it would settle: `hot`, `cold`, `hot`, `cold`, and the referee never
gets a turn. That is the same shape from a third side (§20), and it takes the same answer — `standing`,
the claim that a rule must always be considered.

### One relation could not carry both intents

`overrides` is **per step**: a rule overridden by another that matched anywhere this tick does not
apply at all. That is right when the two are rival answers to one situation — a surprise is a rival
answer to the whole situation, not to one case in it, and it defeats a rule it shares no consumed
entry with. It is wrong when they are rival answers to each of several: one rule matching for one
action defeated another for *every* action in the step, and *substitute where an outcome is declared,
otherwise assume* was not sayable.

The reflex is to make defeat per-binding, and it does not work: two rules bind different variables, so
their bindings cannot be lined up. So there are two intents and one relation cannot carry both:

| | |
|---|---|
| `overrides(A, B)` | rival answers to **one** situation. B is out for the step if A matched at all. |
| `supersedes(A, B)` | rival answers to **each of several**. Only B's applications sharing a consumed entry with an application of A are out. |

**Evidence is the comparison because it is the only honest one available**: the trail already records
what each application matched, since R5 needs it, so nothing is measured that was not already kept.

⚠ **Both are narrower than they look, and §20 is where that bites.** `overrides` is per tick *and* per
rule, so one instance of the losing situation suppresses the loser about **everything**. `supersedes`
requires a shared consumed entry, and two rules reaching one conclusion from different premises share
none. A conflict that is neither of those two shapes is not a case for a third relation — it is a case
for asking whether the two rules were really contradicting each other at all.

### Precedence is read, not kept

Whatever else it is, `overrides(A, B)` is a **claim**. It is authored, it is about two rules, and it
must be as dated, deniable and arguable as anything else in the graph. That has one consequence which
this design got wrong for a long time and which is worth stating as a rule:

> **Precedence is read from the graph at the position the agent is standing. It is not kept anywhere.**

The alternative — a table, seeded once from the surface — fails in three ways, and only the third was
predicted:

1. **A rule can conclude a precedence, and the arbitrator never reads it.** The fact holds in the
   graph and the table stays empty. This is §1's defect from the far side: not *the machinery knows
   something no rule can ask about*, but **a rule says something the machinery does not listen to**,
   which is worse, because the corpus is not even wrong.
2. **A rule adopted at run time can never be ordered against anything** (§20), because a table keyed
   on names a corpus declared has no key for a rule that was never declared.
3. It is a **cache of a claim**, which §4 says is debt, and it has the two failure modes of any cache.

Maintaining the table from the write instead of from the loader fixes (1) and (2) and keeps (3).
Reading it fixes all three, and the measurement is what licensed the deletion: with the table gone,
the whole suite runs in **6.42s against 6.38s**. It was buying nothing but the two ways it could be
wrong. What went with it: a write hook, a re-scan on adoption, two seeder methods and a loader
method — and, one commit after it was written, the whole *maintenance* problem those hooks existed to
solve.

⭐ **And the only thing that broke was a fixture reaching into the table** rather than depositing a
fact. That is the whole answer to *was it debt*: the table was the anomaly, and the check that touched
it was the only thing that noticed.

Note what this does **not** change. §4's floor still requires that the bottom-most tiebreak be a
lookup that does not reason. Reading a claim is a lookup. The floor never required an answer to be
*stored*, only that finding it not be a search.

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

**And a binding can be reconsidered, once you can say what has already been tried.** A `binds` fact
was always deniable, and denying it achieved nothing, because the search re-unifies and picks the same
first candidate. **The gap was never a way to withdraw a choice — it was a way to say what had been
tried.**

```
excluded(<plan>, ?v, x)     not that one
```

⚠⚠⚠ **Both halves are needed, and either alone is worse than neither.** Measured on two viable taps:

| | result | |
|---|---|---|
| nothing reconsidered | the first tap | quiescent |
| **exclude only** | the first tap | **inert** — the surviving binding pins the variable before the exclusion is consulted |
| **deny the binding only** | the first tap, ×270 | ⚠⚠⚠ **runaway** — the same candidate chosen and denied forever |
| **both** | the first tap → **the second** | quiescent, and the goal reached |

The runaway is §19's re-ask criterion in a third place — *an occasion warrants a re-ask only if
re-asking cannot produce one* — with the binding as the occasion the re-ask itself recreates. And the
recovery rule is keyed on `quiet`, because the loop has finished there, so reconsidering cannot starve
anything still due to run.

### Requests do not leave a frame

The machinery's vocabulary is **requests and reports, not claims about the world**. A rule concludes
`+suppose(p)`, `+goal(p)` or `+doing(p)`, and the machinery does what a rule cannot: open a frame,
read a rule backwards, or carry an intent past the agent's boundary.

One consequence is easy to miss and was found by running: **nothing in this vocabulary may carry out
of a frame**. A request to suppose is not a claim about the world, so there is nothing for §16's
wrapper to qualify — and carrying one out produces `likely(suppose(...))`, which the rule that crosses
guards then crosses, so the machinery supposes its own bookkeeping without end.

⚠ **One request is deliberately exempt, and the exemption is the point.** `doing` is *not* treated as
bookkeeping, though every other request is. *What I would do under this hypothesis* is the one thing
such a hypothesis is for; treated as bookkeeping, an agent that supposed a premise and found it would
fire a missile came back knowing nothing at all. A wrapped intent is a claim, not an intent, and no
dispatch matches it.

### Supposing something must not bring it about

The reason to open a hypothesis about a course of action is to find out whether it leads anywhere
unacceptable. An agent that finds that out **by doing it** has not considered anything.

Measured: supposing a premise whose rule concludes `+doing(fire(missile))` **fired the missile.** Not
a leak in the chain — the conclusion stayed inside the frame and crossed out wrapped, exactly as §17
promises. The **boundary** was ignoring the register.

> **§17's *nothing leaves a frame* was a claim about the chain. Effects are not in the chain.**

The repair is a condition and not a phase: the boundary asks whether any frame on the path to the root
was entered by supposing, which the forest already records.

**But blocking the emission is only half of it, and the half that is easy to stop at.** A plan reasons
*past* its actions — the second step follows from the first having worked — so an agent that merely
refuses to act inside a hypothesis cannot plan at all: its plan dies at its first action.

> **Acting comes out as a conclusion — a decision to act. What planning needs from that conclusion is
> the action's assumed outcome, not its occurrence.**

So the boundary deposits the same record under a different name. Really acting writes `emitted(x)`;
deciding to act while supposing writes `taken(x)`. Both mean *this act is on the record*, and one row
rather than one branch turns either into `did(x)`, from which §15's `<assert-act>` supplies the
assumption that it worked. Measured: a three-step plan runs to its end inside a hypothesis with
nothing done at all.

**And saying *what* worked needs no plan machinery either:**

```
rule <outcome> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )
fact achieves(travel(work), at(work))
```

One rule, one fact per action — operator semantics, as data. Whether the action itself is *also*
asserted is then a precedence claim, and pointing one at that pair is what exposed the `overrides` /
`supersedes` split above.

⭐ Note which half is defeasible. That an act *was decided on* is unarguable — the agent concluded it.
That it *succeeded* is `<assert-act>`, an ordinary rule.

### Strategies are defeasible

```
<M> = causes( { +goal(?g, explain(?f)) },
              { +goal(find(?r)), +constraint(?r, causes(_, {+?f})) } )
```

Because that is a rule, `overrides(<M>, <M2>)` and `unless(<M>, +domain(?f, social))` are sayable, and
**a strategy becomes defeasible like any other claim**. A strategy written as code cannot be
overridden by a statement in the knowledge base, and that asymmetry — not interruptibility — is the
larger cost of putting machinery outside the world the agent reasons about.

⚠ **This depended on something the design assumed and did not provide:** a corpus could not *name* a
bundled rule. Every place this document says *a corpus can override this* was untrue until the
bundle's names were in the same table a corpus writes into.

### Reflection is demanded, not continuous

Meta-rules are consulted only at **named decision points the interpreter already reaches**: which rule
to apply, what to do on failure, what to do on surprise. Never between arbitrary steps. Each decision
point either receives a meta-answer or falls through to §4's total step, so no decision hangs.

Arbitration is the one that is easy to get wrong. A meta-rule that decides which rule to apply must
itself be selected, and that regress happens *at run time*, not at design time. Therefore:

> **The bottom-most arbitrator is a lookup that always returns and never searches.**

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

**(C)'s price, named:** every step costs a selection, and a badly authored precedence produces
dithering that reads as a bug in the rules rather than in the ordering. Both are measurable —
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
| status | **convention** — a bundled policy | **floor** (§4 item 2) | totality is floor; the precedence is a claim |
| complete? | **never**, by design | over what recall offered | over what matched |
| total? | — | — | **must always answer** |
| authored or learned? | **learned** | mechanical | **authored** — precedence |
| failure mode | a rule you needed never surfaced | — | dithering, or a hang |
| cost of being wrong | recoverable: a worse plan, or a surprise later | — | a wrong action |

Judgements of what is worth attempting live here too. *Don't plan to make it Tuesday* is not a fact
about the rule (§12) and not a prohibition (below); it is a learned bias about which subgoals are worth
expanding. It belongs in the step where being wrong costs a worse plan rather than a wrong action.

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
mind. That is §9's distinction between *absent* and *no entry*, one level up.

> **Recall returns a set plus a state, never a set.**

The state is cheap to compute from the wrong thing (*did I find anything?*) and expensive from the
right thing (*is this situation familiar?*). Unfamiliar-and-empty is a different event from
familiar-and-empty, and only the first should escalate.

### Index, then prefer, then learn

An agent that enumerates its whole rule set before choosing has not remembered anything, whatever it
does with the list afterwards. The first repair is not experience; it is an **index**.

§3 gives the substrate one, over instances by relation, and argues for it in a line: *a rule whose
antecedent names a relation has to start somewhere.* Read backwards the same argument holds of the
rule set — a reader asking *what could produce this goal* has to start somewhere — and nobody had made
it there. So rules are indexed by the relation they conclude, and the backward reader asks about what
came to mind rather than about everything:

```
<ask-recall>   { +goal(?w) }           ⟹  { +recall(?w) }
<ask-fit>      { +recalled(?r, ?w) }   ⟹  { +fit(?r, ?w) }
```

Measured: 751 ticks to the goal became **57**, and asking *could this rule produce this* went from 711
applications to **8** — one per goal. It is exact rather than heuristic: a rule that could produce the
goal is in the bucket, and one that could not was never a candidate. The only rules deliberately
absent are those whose consequent is a bare variable, which §12 calls vacuous backwards.

> **Index, then prefer, then learn.** An index makes the candidate set small and costs nothing in
> completeness. Preference orders what is left, and may be wrong at the price of a worse move.
> Experience improves the preference. Doing them in the other order builds a ranking over an
> enumeration, which is the thing being complained about with a sort in front of it.

### What recall is keyed by

Not the situation alone, but **the situation and the active goal**. The same world brings different
rules to mind depending on what is being attempted; recall keyed only on world features surfaces the
same set forever regardless of intent.

**The key is not the register.** Attention is the register — §4's one privileged pointer — and that is
exactly why it cannot be the key: a seat is a fresh moment every tick, so a table keyed on it would
never see the same key twice and would learn nothing. What recurs across situations is what the
situation is *about*.

**Ranking must not end in a set.** §10 requires that no derived result depend on an undeclared
enumeration order, and a ranking is a derived result. Top-K with an unseeded random tie-break is the
same bug wearing a hat: two runs of one corpus diverge and the trail records neither the choice nor
the reason. If randomness is wanted for exploration, the seed is a fact and the draw is an entry.

### A shortlist that ran dry is not a search that finished

This turns out to be a soundness condition and not only a quality one, and it only became visible once
goal expansion was rules: `blocked` is an aggregate over a finished search, asked at `quiet`. If a
narrowed recall could reach `quiet`, the agent would report *no rule fits* about rules nobody asked,
and the trail would show a completed search that never ran. So quiescence under a budget escalates to
the exhaustive pass first, and only its silence counts.

> **Nothing came to mind is not nothing is left to do.** Only the second should escalate outward; the
> first escalates inward, to recalling harder.

The same move covers facts as well as rules: a search that never looked at what it had put out of mind
has not finished either.

⭐ **And putting a domain out of mind is the strongest single lever measured in this design** — one
corpus line claiming a domain `dormant` gave 14.5×, because it removes work rather than reordering it.
That is the general rule stated below arriving as a number.

### Deliberate reasoning is not a second mechanism

Slow, exhaustive reasoning is **recall with the budget removed** — same match, same arbitrate, an
exhaustive proposal step. The fast/slow distinction therefore needs no architectural fork: a budget
parameter, and an escalation rule that is itself *a rule*. The escalation triggers are exactly the
impasses: nothing came to mind; what came to mind conflicts irreducibly; or what came to mind was
**surprising**, which is §18 feeding this rule.

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
the training data for both. **Composition is not recall**, and fusing them would repeat the mistake
this section exists to avoid: recall may be wrong at no cost beyond a worse plan; a composed rule is a
*claim*, and it can be wrong the way any rule can be wrong.

§20 is what happens when *which rules exist* stops being a special case of composition and becomes the
general question.

### Where the cost was, when it was finally measured

§19 exists because proposing every rule does not scale, and that reading of the cost turned out to be
wrong about this engine. Setting a budget made a goal fixture **slower**, and profiling said why: the
read was 86% of runtime and the same walk was being repeated once per rule per tick (§10).

Two things follow that are about the design and not about the implementation.

**Recall narrowing cannot reach an antecedent.** `<ask-fit>` matched 72 ways in a single tick with
four domain rules, because `+goal(?w), +rule(?r)` is a cross product. §19 narrows which rules are
*proposed*; it says nothing about how many ways one rule matches. So recall was never going to fix
this, and the fact that the seam is at the proposal step is a limit of the seam, not of the idea. §3's
argument index is what addresses the other half.

**A shortlist pays only where many rules match and are useless.** The obvious fixture — an *n*-rule
forward chain — cannot measure recall at any *n*, because only a handful of rules match per tick and
an indexed non-match is nearly free. Scale is not the requirement; **selectivity** is.

> **A benchmark that cannot fail is worse than none, because it reads as evidence.**

### What recall is worth, and what has to exist before it is worth anything

Measured on a workload built to have the property recall needs: D domains of knowledge, all in play,
one goal in one of them.

An **ideal** table — authored, naming exactly the rules the goal's chain needs — reaches the goal in
**8 ticks instead of 734**, with a fifth of the writes. Recall's prize is real and it is large.

And on the same run it saved **nothing at all**, because the loop went to quiescence and did every
domain anyway. That is the finding, and it is about the machine rather than about recall:

> **Recall cannot save work in a machine that runs to quiescence.** Narrowing changes the *order* in
> which everything is done, not how much is done. Only an agent that can **stop** collects the prize.

That fixed the order of work — an agent that can stop, then recall worth narrowing, then experience
worth learning — and the account of stopping follows.

⚠ **And the headline needs a correction which is itself the finding.** The *8 instead of 734* was
measured with a budget that also switched the apparatus off. Carve the apparatus back in — which
stopping requires — and the table's steering disappears behind the apparatus's authored precedence,
which decides the early ticks regardless of what recall proposed. Until that is addressed, this
workload cannot measure recall again.

### The second way to be over

The design had one, and it is **exhaustion**: the loop runs until nothing it knows has anything left
to do. A budget bounds it with a *limit*, but a limit is a budget running out rather than a reason. So
nothing could say that a plan was finished, a woken rule was done, or a question had been answered
well enough. **A machine that can only be exhausted does an amount of work its corpus fixes.**
Nothing it learns can make it cheaper, because knowing more only reorders.

The second way is **satisfaction**, and it has to be a claim:

```
enough(x)              there is nothing more worth doing about x
```

*Worth* is a judgement, and §4 puts judgements in data. So `enough` is concluded by an ordinary rule —
proposed by recall, defeasible, arbitrated, on the trail — and the loop's entire part is to read it
and stop. A satisficing agent's whole policy is then one row:

```
rule <done> = implies( { +goal-of-mine }, { +enough(goal-of-mine) } )
```

**Nothing ships concluding it**, exactly as the recall budget defaults to off: stopping is a policy,
and a bundled policy would change what every corpus means. Measured: the goal arrives at tick 57 and
the run ends at 59 instead of 124, with 470 writes instead of 706.

Four decisions, each forced rather than chosen.

**It is read before the tick's work, not after.** Arbitration is total, so by the time an application
has been chosen the move is made.

> **Being careful has to come before the move it is about.** This is an ordering trap that has now
> decided four separate designs: where `enough` is read, where doubt is recorded, where passing-up is
> deposited, and — in a fixture rather than in the engine — which of two rules keyed on one occasion
> answers first.

**It routes to leaving a frame first, so a frame is where it lands.** `enough` concluded inside a
hypothesis ends the *branch*, not the run, because a frame is already the unit of work that can be
over. That is *when is a plan settled* and *when is a woken rule done* answered at a door that already
existed: what crosses out is `likely(enough(g))`, a claim about the branch, which no relation matches,
so a satisfied branch cannot stop its parent by accident.

**It does not write `quiet`, and this is the sharp one.** The verdict rule asks at `quiet`, and
`blocked` claims that *no* rule fits — an aggregate over a **finished** search. A search that stopped
because it was satisfied has not finished, and reporting the goals it never reached as blocked is
precisely the unsoundness the exhaustive escalation exists to prevent. So the record is its own fact:

```
stopped(<seat>, x)     written by the register, after `enough` was read
```

Same treatment as `arrived`, `emitted`, `left` and `quiet`: the machinery deposits the smallest
unarguable thing and says nothing about what it means.

**And it is terminal, where `quiet` is not.** `quiet` continues the loop so a watchdog can key on it,
because *the search finished* leaves work worth doing. *Nothing more is worth doing* does not.

### A stop with a goal still open is not a stop

The first version of the above shipped without this and was wrong in the way that matters. Measured: a
corpus with two goals, a stop rule on the first, and the run ended with the second **neither achieved
nor blocked nor pursued, and nothing anywhere recording that it had been open.**

The obvious repair is a rule — *if I still have a question to ask, there is more worth doing* — and it
is the wrong repair:

> Recall may be incomplete about what to do. It may not be incomplete about what you must not do, or
> about whether to go on, or about **a goal it is dropping**.

A corpus may be wrong about what is worth doing next. It may not silently abandon what it was asked
for. So it is a **veto**: consulted before the stop is made, never proposed, never arbitrated, and
unforgettable.

```
open(<w>)              this goal was still outstanding when the agent tried to be done
```

That makes three, and they are one move rather than three mechanisms — **escalate before believing a
decline**:

| widening | a shortlist that ran dry is not a search that finished |
|---|---|
| the norm veto | a write a norm covers never happens |
| the open-goal veto | a stop with a goal still open is not a stop |

None of them is a phase. Each runs at one machinery decision and answers one question, which is the
distinction §18 draws: a phase asserts a policy in control flow; a guard refuses to believe a decline
the machinery was about to make on its own.

**The refusal writes.** A veto depositing nothing would be a silent decline, which is the failure being
designed against; and it is what makes this terminate. Each goal vetoes **once**, so what is
guaranteed is that nothing is dropped without the agent being given the occasion to react — not that
it always finds an answer, which no mechanism can promise.

**An outstanding goal outranks an `enough`; it does not delay one.** The first attempt had the veto
cost a tick and then let the stop stand, and the diagnosis never appeared, because reacting to an open
goal is ordinary reasoning of whatever length it takes and an `enough` consulted again next tick cuts
it off after one.

Two things fell out of that rather than being arranged.

**The diagnosis needed no new rule.** A bundled *open ⟹ verdict* was written, looked exactly parallel
to the existing one, and was **deleted**: because an open goal outranks the stop, a run with one
always finishes at quiescence, so the verdict is already asked for every goal. The occasion is not
redundant — it records *which* goal was nearly dropped — but a second way to ask about it was.

**And the reaction is a corpus rule, deliberately.** *Where a question goes* is a fact about a
deployment rather than about reasoning:

```
rule <ask> = implies( { +open(?w), +blocked(?w) }, { +doing(ask(?w)) } )
```

The intent crosses the boundary at the write, the run ends because a question is not work, and a later
utterance resumes it through the intake rule — an arrival being an ordinary write means nothing waits
and nothing polls. Worth noting what the agent asked about: not the goal it was given, but the precise
subgoal backward reading had worked out it was missing. Nothing arranged that, and no rule in the
corpus named it.

> **The loop may end. It may not end quietly on something it was asked for.**

### Arbitration is scheduling, not decision

§18 describes arbitration as choosing one rule among those that matched. What it does is choose one to
run **first**. The rules that lose are *deferred*, not rejected — and a loop that runs to quiescence
applies every one of them eventually.

Measured, with two ways to get water for a kettle, one of which breaks a jug that another goal needs:

```
emitted: ['fill(kettle)', 'smash(jug1)']
```

**The agent did both.** Three consequences, and they are one fact seen from three sides:

* **There is nothing for experience to be experienced about.** *Choose the better rule* has had no
  measurable content because the agent takes the better rule and the worse one.
* **It is a safety property before it is a learning one.** An agent with two ways to do something does
  the destructive one too.
* **Credit reinforces the mistake.** An outcome-based signal over an agent that cannot forgo will
  learn to prefer whatever was on the winning path, including what it should have declined.

> **A choice that cannot be forgone is not a choice.** The design has a way to stop and no way to
> *forgo* — and in an agent that acts, choosing is forgoing.

### Taking one way of getting something passes up the others

```
forgone(<R>, <w>)      R was a live way of getting w, and I took another one
```

A **fourth** way for a rule not to run, and the first that is a decision:

| defeated | `overrides`, `supersedes` — a rival answer is better |
|---|---|
| forbidden | the norm veto — it may never happen |
| not recalled | it did not come to mind |
| **forgone** | it was reasonable, and I chose otherwise |

**What makes two rules alternatives is that they answer the same want**, read off the evidence: an
application that consumed `goal(w)` is a response to wanting `w`. Note it is *not* whether a rule's
consequent could **be** the goal — that is backward reading's question and the wrong one here. A rule
concluding `doing(fill(kettle))` fits nothing, yet it is plainly a way of getting water.

**It is a deposit about the alternative, not a retraction of the goal.** The obvious alternative — have
the winner consume the want — works with no engine change, and was rejected on two measured
interactions: retract the goal and credit cannot find what it achieved, and a failed act loses the
want with nothing left to notice it, because the open-goal veto keys on `goal(?w)`.

**Passing up is the default, and complementary work is the exception a corpus declares.** The
judgement is made on which error is recoverable, not on which is more often right:

| forgo by default | an agent that should have done both **under**-does. The goal stays open, the veto deposits `open(w)`, and a rule hands the alternative back. Recoverable. |
|---|---|
| defer by default | an agent that should have done one does **both**. The jug is smashed. Not recoverable. |

So the deposit is deniable, and retrying is one ordinary corpus rule:

```
rule <retry> = implies( { +open(?w), +forgone(?r, ?w) }, { -forgone(?r, ?w) } )
```

*What I wanted is still outstanding, so reconsider what I passed up.* That is backtracking arriving as
a **consequence rather than as machinery**, and it needs three things to meet that were each built for
something else: `enough` makes the agent try to stop, the veto refuses the stop and deposits `open`,
and this reads it.

⚠ **The apparatus is exempt on both sides.** Nearly every bundled rule consumes `goal(?w)`, so without
the exemption, applying any rule would forgo backward reading entire — measured, by removing it.

### Choosing the better move

Recall is asked to make an agent *cheaper*. The sharper demand is that it make an agent **less
stupid**: given several applicable rules, take the better one. Those are not the same request, and
only the second matters on an irreversible step.

The engine was already computing what it needed. *This rule could produce what you want* is the
backward reader's answer, deposited and used by nothing else. One bundled rule turns it into a
preference, which makes **means-ends analysis data** rather than policy in the loop — and an agent
that should not favour the rules serving its current goal deletes that rule and has its old behaviour
back.

Where the preference is consulted was decided by two failures.

**A preference must order, not exclude.** Used to filter recall, goal-relevance starved the most
useful rule in a corpus — one that does not fit the goal at all.

> **Relevance to a goal is one signal, and as a filter it is silent about everything it is not about.**

**The apparatus is not a competitor.** Let loose over every rule, preference outranked the rules that
notice a surprise, and the agent went on pursuing a goal while a channel was telling it the world had
moved. Being overridable and being **forgettable** are different properties, and only the first was
ever claimed for the bundle.

So the order in arbitration is:

| | |
|---|---|
| **authority** | `overrides`, applied first as defeat — a claim about who decides, and no amount of *this usually works* may outrank it |
| **apparatus** | a `standing` rule keeps its authored place |
| **helpfulness** | what the situation recommends |
| **authoring** | the order they were written in |

The last row is what helpfulness displaces, and it is worth stating plainly: the tie among applicable,
undefeated rules was being broken by **an accident of authoring**, deciding which move an agent made.
Arbitration stays total and stays a lookup: with no preferences it is exactly the authored order it
always was.

### A preference is a score, and doubt is a tie

An order over rules cannot distinguish *one clear best* from *two I cannot separate*, and those call
for opposite behaviour — take the move, or think harder before taking it. So a preference carries a
strength.

The strength is the table's own, and **cardinal**: a row scores how much this situation recommends
this rule, and the scores of applicable rows are summed. Candidacy scores 1, the least anything can be
worth, so whatever experience has actually learned outranks it and two mere candidates tie.

> **Two rules are close when their scores differ by no more than the tolerance.** Confidence is a gap
> wide enough to rely on.

**What counts as close is a knob, so it is a fact.** `tolerance(2)` says a gap of two or less is not a
difference the agent will rely on; zero unless claimed, so the default is an exact tie and no
behaviour depends on a constant nobody chose. **A rule can turn it**, so an agent can be harder to
convince when the next step cannot be taken back:

```
rule <care> = implies( { +goal(doing(?p)) }, { +tolerance(4) } )
fact standing(<care>)
```

The `standing` on the second line is load-bearing, because being careful has to happen before the move
it is about. A corpus wants `standing` as much as the bundle does; it was never a kernel/business
distinction.

**Nothing ordinal was added to make this work**, and keeping the two scales apart is what lets each go
on meaning something. A score is a magnitude, summed and compared as a cardinal. A modality is a
wrapping proposition, composed by nesting. `+prefer(<R>, k, 3)` about a merely `likely` conclusion is
*a strong recommendation the agent is not sure of* — a sentence neither quantity could express alone.

So doubt is deposited — `close(<R1>, <R2>)`, pairwise so the arity is fixed — and nothing more. What to
do when unsure is a claim about how to reason, which makes it rules.

⚠ **A tie among the apparatus is not doubt.** `standing` rules have an authored precedence which *is*
the answer, and recording those ties buried the real cases in spurious pairs.

⚠ **Arbitration is total, so the move is already made when the doubt is recorded.** Acting on doubt
*before* committing would require a step that can be deferred, and every mechanism this design has for
deferring is the same unbuilt thing: nothing says when a line of reasoning is finished enough to act
on.

### The apparatus wins most of the agent's choices

An exact learned table — the rules of the goal's domain, keyed on the goals they served, none of the
others — reached the goal in the same number of ticks as no table at all, and so did the
hand-authored ceiling. Where each choice is actually decided, measured over one episode:

| | |
|---|---|
| arbitrations | 30 |
| won by the **apparatus** | **26** |
| won by a domain rule | 4 — and preference already decided all four |
| won by **authored order**, no reason at all | **19** |

> **Experience has almost nothing to decide, because the apparatus wins most of the agent's choices —
> and the apparatus is deliberately unrankable.** `standing` flattens every bundled rule to one rank,
> so their mutual precedence is install order.

*The apparatus's order is authored on purpose* is true of the pairs anyone thought about — read before
acting, notice before continuing — and **incidental for most of them**. Two thirds of every choice
this agent makes is settled by the order somebody typed the rules in.

The first repair proposed was to let preference order *within* the standing tier. It was prototyped
and **does not pay**: it changed the sequence of applications without changing the count of them, the
ticks, or the writes. The reason generalises:

> **The apparatus is a dependency chain, so permuting it cannot shorten it.** Narrowing changes the
> order and not the amount — as true of arbitration as of recall. **Ordering pays only where some of
> the work is avoidable**, which is why putting a domain out of mind gave 14.5× and reordering gave
> nothing.

### Recall may not be incomplete about whether to go on

**Once stopping is a rule, being late to recall it is being late to stop.** Under a budget the ideal
table pushed the rules that read, notice and stop down the shortlist — so the better the table was at
the task, the worse the agent was at noticing the task was over. Worse: with the apparatus capped out,
a run with an *ideal* table reached quiescence **slower** than exhaustive recall (182 ticks against
124), because a shortlist that has lost its machinery does more ticks doing less in each.

So a `standing` rule is never starved by a cap, alongside a `due` one. Note carefully what changed and
what did not: `standing` stays out of recall's **ordering**, because a claim about precedence once a
rule has matched is not a claim about coming to mind, and letting it sort filled every shortlist with
apparatus. **Inclusion is a different claim from ordering**, and only the first is taken here. The
cost is stated rather than hidden: a corpus that marks fifty rules `standing` has no budget left, and
that is its own claim about what must always come to mind.

⚠ **`goal` does not distinguish a root goal from a subgoal**, so the general stop rule is not writable.
`{ +goal(?w), +?w } ⟹ { +enough(?w) }` reads as *what I wanted holds, so I am done* and is unsound,
because expansion writes `+goal(sub)` for every subgoal it derives — measured, the agent stops at tick
51 of a run whose goal arrives at 57. A root goal is a `goal(?w)` with no `subgoal(?p, ?w)`, a negative
existential, which §12 says a `−` member cannot express and which is the same shape as `blocked`. It
needs a request, and it has one.

### What *in play* means, and why it is the one judgement nobody argued for

The preference row above says *matched when that key is in play*, and nothing in this document had
ever said what **in play** means. It is a convention: the relations in the current delta, plus each
live goal's content and that content's relation. It is not floor by any of §4's three grounds, no rule
can read it, and until it was measured it had no check of its own — every mutation of it failed only
checks about something else.

Measured against the smallest fixture that can tell a goal-serving rule from a useless one:

| the key is | first corpus move | over the whole suite |
|---|---|---|
| **as shipped** | `toward` | 0 failing |
| nothing | `wander` | 9 failing |
| the delta only, no goals | `wander` | 7 failing |
| goals only, no delta | `toward` | **2 failing** |
| everything the state asserts | `wander` | 7 failing |

Three things follow, and the first is the one worth carrying.

> ⭐ **The key is not a subset of what is asserted.** Nothing ever claims `nearer(a)`; what is claimed
> is `goal(nearer(a))`. So a pass over every proposition and every relation in the state — strictly
> *more* information than the shipped key — still misses the node the preference is keyed on, because
> the key reaches **inside** a proposition for its argument. More is not nearer, and a sweep is not a
> substitute for a judgement about what a situation is *about*.

**The two halves are not one idea, and the split is undeclared.** The goal half decides the case above
and carries seven of the nine checks; the delta half decides two, both about the recall **budget**.
They also differ in kind: a goal half accumulates, while the delta half is genuinely per-moment. That
asymmetry is why the obvious repair — make the key ordinary facts and let a corpus argue with it — is
**half available**. The delta half could not be facts on an append-only chain, because a key that
never expires converges on the state and the table stops discriminating.

**What is not open:** that this is convention. §4's test is whether every decision it embodies can be
an argument, and *what a situation is about* is exactly the kind of judgement this section says
experience should supply. It sits in one method, deliberately — a better answer replaces it without
touching the loop, the table, or any rule — but it sits there **named**, which it did not before.

### Credit, blame, and the arena

Two things came out of asking *where is the choice actually hard?*, and only the second was expected.

**Credit assignment needs no new bookkeeping.** R5 already licenses every derived entry with the rule
that produced it, because the trail is load-bearing elsewhere. So walking back from what was achieved
reaches the rules that produced it — and only those. Measured on a corpus with two ways to get water
and a third rule that ran and contributed nothing: the walk returns the rules that were **used**, not
the rule that was merely available, and not the rule that merely applied.

```
review()               which rules were on the support of something achieved
helped(<R>, <key>)     the smallest unarguable record of it
learned()              ...as ordinary corpus text, for the next episode
```

**Offline, and that is a position rather than an implementation detail.** Credit needs the outcome and
the outcome is not known until the episode ends, so nothing here runs in the loop.

Two choices worth naming. **The key is the goal's relation, not the goal**, because a row keyed on
`boiling(kettle)` is true of one episode and a table that cannot generalise is a cache. And **what it
takes forward is text**: experience belongs in recall precisely because being wrong there is
recoverable, and it is only recoverable if it can be read, argued with and denied. A weight cannot be.

**Failure at episode level credits nothing and blames nothing.** A rule applied on an episode that
achieved nothing was not thereby wrong — the episode may have been impossible.

**Splitting a task into subgoals is what makes blame sayable.** That refusal is right about episodes
and wrong about subgoals, and the difference is §9's sign distinction doing real work somewhere new:

| no entry at all | it was never reached. Many causes, no author. |
|---|---|
| an entry says `−` | something **made** it false, and that entry carries a licence. |

So blame is the credit walk run over a denial instead of an assertion, and it reaches the *decision*
rather than the physics: measured, from a lost `intact(jug1)` back through the rule that broke it, the
act that was taken, and the rule that chose the act.

```
harmed(<R>, <key>)     this rule is on the support of something wanted being made false
```

**What makes it land is that the decomposition names the damage without anyone anticipating it.**
Backward reading expanded `juice(jug1)` into subgoals, one of which was `intact(jug1)` — so the thing
the *other* branch broke was already a goal, and its loss is on the record. Nobody wrote that subgoal
down; the machinery produced it, and that is what a task being split buys.

⚠ **Blame needs a denial, not an absence, and that is not fastidiousness.** Most unachieved subgoals
in a real run are *generic*, produced by expansion and never meant to hold as stated. Counting those
as failures would blame every rule for every search it ever ran — the same shape as the
shortlist-that-ran-dry error: mistaking *not reached* for *shown false*.

### The carve-out

> **Recall may be incomplete about what to do. It may not be incomplete about what you must not do.**

A prohibition that fails to come to mind is a forbidden act that nothing notices. The repair is not to
make recall complete for norms — that reintroduces the exhaustive search this policy exists to avoid.
It is to take prohibitions **off the recall path entirely**: check them at the write, indexed by the
entries about to be written. That set is small and known, so the check is cheap and exhaustive.

> **A prohibition is a gate on application, not a competitor in recall.**

The shape it took is the argument. `forbidden(doing(harm(?x)))` names a class of acts — its argument
is a **description**, exactly as a reified antecedent names a class of premises. It is never proposed,
never matched, never arbitrated; the gate consults it on every write, before the deposit, so a
forbidden entry never exists — not even briefly, and not for a write hook to see. Since dispatch is a
write hook, that is what keeps the act inside the agent rather than emitting it and regretting it.

**Cheap because it is indexed by what is about to be written**, which is §3's index applied where it
belongs: a hundred norms about acting cost nothing on a write about the weather.

**A refusal writes.** `refused(p, sign, <norm>)` is an entry, licensed by the norm that caused it.

Three consequences fall out rather than being arranged:

* **quiescence still terminates.** A forbidden conclusion never lands, so the chain never says it and
  the rule would match forever. What settles it is the refusal: once *that* is recorded, applying
  again changes nothing.
* **asserting only.** `forbidden(p)` forbids bringing `p` about, and bringing about is `+`. Denying
  you are doing harm is not the forbidden act.
* **a norm is still a belief** — resolved at the writer's own position, so it can be denied, dated, or
  held only under a hypothesis. What it cannot do is fail to be consulted.

> **§19 keeps norms out of recall. It never said they were beyond argument.** A rule can retire a norm
> on evidence, with the trail intact and the refusals it made beforehand still on the record. A norm
> is unconditionally *consulted* and entirely *contestable*, and those turn out to be different
> properties.

⚠ **Naming is not what separated them, and assuming it did was the error.** A rule could always retire
a norm without a name, because matching a generic antecedent against a stored **description** treats
the description's variables as ordinary nodes: `?y` binds to the stored `?x`, and substitution rebuilds
exactly the node that was written. Naming buys **authoring** — a second surface statement about the
same description — and a stable handle. It never bought reference (§8).

### Once exploring is safe, no comparison is needed

Once a hypothesis cannot act (§18), the question a branch answers is not *which of these is better*
but **does this one lead somewhere unacceptable** — and the norm veto already answers it, used forward
in time. A hypothesis that reaches a prohibition is refused inside the frame, the refusal crosses out
as an ordinary record, and the branch has disqualified itself. Nothing is ranked, nothing is weighed.

That is a smaller mechanism than comparison and a better fit for what branching is for. It also means
the expensive part stays rare by construction: you open the second branch to look for a disqualifier,
not to score alternatives.

### Occasions, and the first thing a corpus can say to recall

Two questions arrive together and turn out to be one mechanism. *What should happen when the agent
comes back out of a hypothesis?* And *what stops reasoning from dying quietly with a goal still open?*

Both are asking for something to happen **at a moment the machinery owns and no rule can name**. A
rule is generic; leaving a frame and running out of work are anchored events, in the same way an
arrival and an emission are. §17's answer for those two was not to give the loop a phase but to
deposit the smallest unarguable record and let rules say what it means. The same answer works here:

```
left(<frame>, <assumption>)      this hypothesis, assuming this, is over
quiet(<m>)                       the loop found nothing to do at this seat
stopped(<seat>, x)               ...and this one ended because something claimed `enough`
```

`quiet` closes §5's third silence. §2 named two places the machinery declines — match and write — and
quiescence declined by saying nothing at all. It is also the moment at which an **aggregate over a
finished search** becomes legitimate: *no rule fits*, *nothing is left to try*, *that goal is still
open* are all claims about a search being over, and now there is a fact that says one is.

A watchdog needs nothing further. It is an ordinary rule with `+quiet(?m)` in its antecedent — inert
until the loop stops, because nothing else ever writes that. No trigger table, no second loop, no
registry: **the trigger is the fact.**

**A callback is a pointer to a rule, and it may not be a call.** `left` alone is not enough, because a
rule keyed on it fires when *any* hypothesis returns. What a callback needs is per-hypothesis scope,
and the natural way to write that is to hang a pointer on the hypothesis:

```
resume(h, <R>)                   when h returns, R's turn has come
```

The temptation is to read `resume` as a call, and §5 forbids it: applying a rule is substitution,
substitution is floor, and no rule crosses it. So the meta rule that picks the pointer up cannot
invoke anything. What it can do is say that a rule's **turn** has come —

```
{ +left(?f, ?a), +resume(?a, ?r) }  ⟹  { +due(?r) }
```

— and leave the machinery to propose it. A rule claimed `dormant` is not proposed by ordinary recall;
one claimed `due` is. The wall turns out to have been protecting something:

> **A callback is directed recall, not invocation.** The woken rule still has to match, can still be
> defeated, still competes in arbitration, and still yields to a surprise. None of that survives a
> subroutine call.

Which is the answer to the obvious objection — that continuations are control flow, and §18 spends its
length arguing nothing may own the loop. They are not, here. Adding continuations does not weaken
*nothing owns the loop*, which is not the usual outcome of adding continuations to anything.

It also lands where this section said the seam was: `dormant` and `due` are the first thing a corpus
has ever been able to say to recall. A pointer hung on a hypothesis is experience the author supplies
instead of the agent learning it, arriving at exactly the reserved seam.

|  | a phase that runs callbacks | **occasion + dormant/due** |
|---|---|---|
| not leaking | ❌ *what runs on return* is control flow, so nothing can override it | ✅ `resume` is a fact, defeasible and attributable like any claim |
| not lossy | ❌ a call that returned leaves no record it was made | ✅ `left`, `resume`, `due` are all entries; *why did this rule apply?* answers |
| readable | ❌ | ✅ *which rules is this hypothesis carrying?* is a query over `resume` |
| composable | ⚠ a callback that calls owns the loop until it returns | ✅ the woken rule is one candidate among others, preemptable between ticks |

Three costs, stated rather than discovered.

**The occasion persists.** `quiet` is an entry, not an event, so a watchdog is armed from quiescence
onwards rather than fired once. A watchdog whose conclusion creates new matches for itself runs until
its budget. Quiescence stops the honest ones and is not enough on its own.

**`due` is not consumed.** A woken rule stays awake. Correct while recall is exhaustive; wrong the
moment recall has a budget, and it is the same open question as when a plan is *settled*.

**Pointing at a rule is a mention, and mention has to start somewhere** (§5). Two things had been
getting this wrong silently: a rule concluding about a rule was dropped by quiescence as *nothing to
do*, and substitution was returning an interned **twin** of any rule node it descended into — so the
pointer named a rule that did not exist. Both were invisible until something pointed at a rule.

### A request can be re-asked

A request is a fact, and a fact is not an event, so a question asked once is never asked again. That
matters: *is this subgoal already satisfied* is asked when the subgoal appears, and if forward
reasoning satisfies it later, nothing asks again.

**The diagnosis everybody carried was half wrong, and the correction is the finding.** *An entry once
written is permanent, so restating it changes nothing* is true and irrelevant: the chain has always
taken a second entry about a proposition it has seen, because that is what §10's two indices are for.
What forbids the re-ask is **quiescence**, and quiescence forbids it *of a rule*. The machinery
re-delivering a request is not a rule restating one, so the prohibition never covered the act.

So it costs a wrapper and one write:

```
again(<request>, <occasion>)     ask this again, because of this
```

an ordinary node, different per occasion, so concluding it *is* a step — and what the machinery does
with it is write the wrapped request through the gate, where every answerer already listens. Not one
answerer knows re-asking exists. Retry falls out for free: re-delivering an intent makes the act leave
the agent a second time, because the boundary dedups on the entry rather than on the proposition.

**And *when* is not free choice**, which is the part worth arguing:

> **An occasion warrants a re-ask only if re-asking cannot produce one.**

Measured, and the author picks the trap or avoids it with one word — §14 has the case. This criterion
has now been violated in three separate places, and it is stated and **not enforced** (§22).

### The apparatus eats its own cooking

A tool's binding is data — visible, queryable, deniable — so that *which of these exist* is a query
rather than a fact about the source (§17 defines what a tool is). It shipped with **exactly zero
apparatus users**: every request the machinery answered, it answered because a line in a constructor
said so. §1's defect again, and the fix is the same: put it in the graph.

| statement | request | what it answers |
|---|---|---|
| `<fit>` | `fit` | could this rule produce this goal? |
| `<settle>` | `check` | is this goal already satisfied, in these bindings? |
| `<verdict>` | `verdict` | did **anything** fit it? — the aggregate |
| `<root>` | `root` | is this what I was asked for? |
| `<remember>` | `recall` | what comes to mind about this? |
| `<re-ask>` | `again` | ask that again, because of this |

Their bodies stay native, which is what an answerer **is** — a request answered by a function rather
than by a search, stratum 0's escape from §5's wall. What moves is only where the binding lives.

**One asymmetry stays, and it is the right one.** A tool's answer lands as a record a corpus may
believe or not. An apparatus answerer writes its answer directly. Same door, same trail, different
standing to speak, because **a tool is outside the agent and the apparatus is the agent**.

⚠⚠⚠ **Deniable is not the same as forgettable, and only two of the six are both.** The criterion:

> **A capability whose absence is the status quo ante is safe to retire.**

Deny re-asking and each question is asked once; deny the root request and the general stop rule never
fires. Both are what the agent did before those existed, and both were sound. The other four are this
section's carve-out arriving again — deny `fit` or `check` and backward reading stops; deny `verdict`
and a goal nothing can reach is never reported blocked. So they carry `standing`, and the denial is
**refused on the record** rather than obeyed.

⚠⚠⚠ **And one of them was in the safe column first, until it was measured.** *Narrowing off means
exhaustive recall, which is the default* is wrong about which thing the recall answerer does: it is
not recall's narrowing, it is the **answer to the recall request**, and nothing asks `fit` about
anything without it. The narrowing lives in the preference table and the budget, which are separately
deniable and were what the criterion was actually about.

> **A criterion is only as good as knowing what the thing does.**

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

## 20. Acquisition and harmonization

*Where the rules come from, and what to do when two of them fight.*

Every section before this one takes the rule set as given. A corpus is authored, the bundle ships, and
the agent's cleverness is entirely in what it does with what it was handed. §19 is the first crack in
that — recall learns, and §4's composition mints a rule — but both are about rules the agent already
had, collapsed or reordered.

This section is about the other half, and it is Part III's own claim taken seriously:

> **A rule is a node. So a rule can be the conclusion of a rule.** Nothing new is needed for the
> agent to author one, and everything already true of rules is true of what it authors.

It is placed last in Part III because it needs all of it. Adopting a rule is a **door** at the write
(§17). Learning one from examples is a **tool** (§17), for reasons three separate walls enforce.
Ordering the result against what the agent was told is **precedence read from the graph** (§18). And
deciding what a learned rule may *say* turns out to need §16's wrapper and nothing else.

The order was chosen by measurement rather than by taste. Acquisition comes before harmonization
because a census said so, and the census is where this section starts.

### Harmonization first, and the measurement redirected the work

The plan was a conflict detector: find pairs of rules that can contradict each other and report them
before they fight. Two questions, asked of an entire repository — what *could* conflict (two rules
whose consequents unify under opposite signs, standardised apart) and what *did* (a defeat actually
computed on a real run):

| | |
|---|---|
| machines / rules / rule pairs | 187 / 3,645 / 33,989 |
| latent conflicts | 3,551 |
| ...where the unifier is a **bare variable** | **3,545** |
| ...genuinely specific | **6** |
| ...ungoverned by an authored precedence | **1**, and it is a fixture written the same day |
| defeats asked / true | 19,341 / **22** |
| distinct pairs that ever fought | **4**, every one authored on purpose |

⭐⭐⭐ **There is not one unplanned conflict in the repository.** A static detector shipped on that
evidence would report 3,545 false positives, one true positive already harmonized, and one test rule.
**It could not be gated by anything.**

> **A corpus with no pathology cannot measure a detector for it.**

⚠ **The 3,545 are a fact about the bundle, not noise.** A rule concluding `−?p` — a bare variable — is
in latent conflict with every positive rule in every corpus. No filter on the consequent removes that;
the real discriminator is whether two antecedents can hold at once, which is a join and still only
says *potential*. **Static pair analysis is the wrong shape to start from.**

⚠ This is **not** evidence that harmonization does not matter. It is evidence that these corpora
cannot measure it: one author, days, dozens of rules, where the pain being imitated is volume and many
hands. The census ships so that the deferral stays revisitable — the day the last column is not zero
is the day a detector can be gated.

⚠⚠ **And the census under-counted 3.5× at first**, because it remembered which machines it had seen by
object identity, and identities are reused the moment an object is collected. It reported **0**
ungoverned where the answer is 1. The conclusion survived; the numbers it was argued from did not.

### What the census did find: a defeat is on the record

Twenty-two defeats happened and **no rule could ask about one of them.** §1's defect for the tenth
time, and the purest case yet: the loop computes exactly this on every tick, uses it, and throws it
away — so *which of my rules actually fight* was a question about a run that no run recorded.

```
defeated(<loser>, <winner>)
```

What ships is the **occasion** (§19). What to do about a rule that keeps losing — ask its author,
raise a precedence, mark it dormant — is a corpus's.

⚠ **Written outside the arbitration path**, because §21's arbitration gate re-runs that path against
the same state and its whole legitimacy is that neither side writes. **An instrument that deposits has
stopped observing.**

⚠ **A defeat is not recorded when arbitration ignored it.** An `overrides` cycle defeats everybody, so
the fallback that keeps arbitration total lets everybody through — and then nobody was defeated. And a
rule that merely **lost** the tick is not defeated either: losing is being deferred, not rejected
(§19), and recording it would report an ordered rule base as a fighting one.

### A rule can author a rule

A rule has been data since §12 — `rule(<R>)`, `conn`, `ant`, `con`, deposited at authoring — and it
went **one way**. The graph could answer *which rules do I have* and never *and now I have this one*,
which is why every amendment to a rule set was a file edit.

```
adopt(<R>)
```

⭐⭐⭐ **A door, not a question.** It belongs with entering a supposition and dispatching an intent
(§17) rather than with §19's answerers: dispatch is where an intent leaves the agent, and this is
where a rule enters it. What decides that a rule is worth having is a corpus concluding `adopt(?r)`;
what happens then is not a judgement, and there is no verdict for a rule to reach.

**Refused inside a supposition, and that is containment.** §17 makes a frame's conclusions unreadable
from outside by construction, because the seat is a successor — but the rule set is one list shared by
every frame. A rule adopted while supposing would apply after the frame is discharged, and to
everything: **supposing would change what the agent believes**, which is the one thing supposing must
not do. It is the same argument that keeps a supposed act inside the agent (§18), and it is refused on
the record, naming the supposition.

⚠ And the refusal is written *inside* the frame, so asking the root whether it holds answers nothing
however well it worked — containment caught the check before the check caught anything.

⚠⚠⚠ **The adopted rule must be the node the graph describes.** Minting a fresh one makes the live rule
a **twin** of the described one: everything a corpus had said about the described rule goes to a node
that is not a rule, and everything the machinery says about the live one names a node no corpus can
reach. This is the twin trap, and it was found only when a standing policy tried to order a learned
rule and quietly did nothing.

⚠ **And the author may say it in either order.** Written in the same consequent *before* the adoption,
a precedence lands while the subject is not yet a rule and the write drops it — so adoption re-reads
what the graph already says about the rule it is making live. §19's ordering trap again, and here the
author has no way to see it: both orders read the same on the page.

### The composer has to be a tool, and three walls say so

A corpus cannot write the new rule's insides. Three refusals, each clean rather than silent:

* a `fact` may not contain a variable at all, so a corpus cannot write a rule's patterns;
* §8 scopes a statement's variables to it, so parts written on separate lines could not share a `?x`
  even if it could;
* a rule's consequent may carry only variables its antecedent binds, or the variables of an existing
  named rule — and a rule being *built* is not one.

So the corpus never names the new rule's insides. It reaches them by **binding**, which is §8's
*reference is binding* arriving where it is load-bearing. Composing a rule is a function, and §17 says
a request answered by a function is a **tool**.

⭐ That means adoption and *learn from examples* share one seam, which was not planned and is the
reason this section is one section.

⚠⚠⚠ **And the tool must build in the corpus's name scope.** Minting a fresh atom for a relation the
corpus already uses produces a rule about a **twin** of that relation — adopted, live, and matching
nothing. The tool must answer the request the corpus can *write*, and it must build out of the names
the corpus can *reach*.

> **Anything that binds a name has to go through the table that resolves it.** This is the twin trap
> in its general form, and it is the single most frequently repeated error in this design's
> construction.

### An example becomes a rule

The operation is **anti-unification** — the dual of unification (§4). Matching asks what two
structures must agree about; this asks what they already do. Given two examples, it returns the least
general structure both are instances of.

```
fact +example(seen(door),   known(door))
fact +example(seen(window), known(window))
fact +seen(gate)                            ⟹   +likely(known(gate))
```

Two examples in, one rule out, and it fires on a third case.

⭐⭐⭐ **One mapping across the premise and the conclusion, and that is the whole of it.** Generalised
separately, the two halves share no variable, and the result is a rule concluding about something
nothing binds. Generalised **together**, `door`/`window` becomes one variable on both sides and the
result is exactly the rule a person would have written.

> **One dictionary is the difference between learning and noise.**

⚠ **What agrees is kept**, which is what makes it the *least* general generalisation: `f(a, b)` and
`f(a, c)` give `f(a, ?g)`, never `f(?g0, ?g1)`. And one disagreement is one variable however often it
appears — `f(a, a)` with `f(b, b)` is `f(?g, ?g)`, not `f(?g0, ?g1)`, or the rule fires on pairs that
never matched.

⚠ **The tool declines rather than generalising anything.** Two examples about different relations have
a *bare variable* as their least general generalisation — a rule that fires on everything. Returning
nothing is a real answer, and the check is that nothing is adopted.

⚠ **The richest source of examples is the one the agent cannot read.** Every derived entry records
what it consumed, and that trail is on the graph — but it is §12's **skeleton**, a plain relation
instance nobody asserted, so ordinary rules do not match it and only stratum 0 can read it (§6). The
agent's own experience is therefore available to the machinery and not to the agent. Whether an
ordinary rule should see the skeleton is a real design question and not a small one (§22).

### What a learned rule may conclude — and the vocabulary that looked missing is not

Now the two arcs meet, which is §2's method rather than a flourish. The agent generalises
`{+hinged(?x)} ⟹ open(?x)` from two examples, and already knows `{+sealed(?x)} ⟹ −open(?x)`. A sealed
hinged vault is a conflict. An unsealed hinged gate is not. **What should the corpus do about it?**

The expected answer was a third precedence relation, because §18's two do not fit. Measured four ways,
and the answer is *nothing*:

| the learned rule concludes | precedence | the vault | the gate | ends |
|---|---|---|---|---|
| bare | `overrides` | `−open` | **never applies** | quiescent |
| bare | `supersedes` | `−open` | `open` | ⚠ **runaway, 300 ticks** |
| **wrapped** | **none** | `−open` | `likely(open)` | **quiescent, 7 ticks** |

⚠ **`overrides` is too broad.** It is per tick and per rule, so one sealed object suppresses the
learned rule about *every* object — the gate is hinged and not sealed, and the agent still will not
conclude it is open. That is §18's own warning about the two relations, arriving from the acquisition
side.

⚠ **`supersedes` is too narrow.** It defeats applications sharing a consumed **entry**, and two rules
reaching one conclusion from different premises share none: one consumes `sealed(vault)`, the other
`hinged(vault)`. Nothing is defeated, and the two oscillate forever.

⭐⭐⭐ **So the third precedence relation this looked like it needed does not exist and should not.** A
learned rule concluding `likely(open(?x))` never contradicts `−open(?x)`, because **they are different
propositions**. The agent holds a generalisation *and* a specific fact at once, which is what it
should do. The conflict arises only if a corpus **crosses** the modality, and then the corpus is the
one asserting it and can decline.

> **A learned rule that concludes wrapped cannot fight what the agent was told.**

⭐ **This is §16's deletion paying off somewhere nobody designed for.** *How strongly a rule may speak*
had to be **in the conclusion** for any of this to be sayable. With a grade it was a field nothing
could read, so a learned rule and an authored one wrote the same proposition and had to be arbitrated.
Two sections earlier that arbitration was necessary; here it is unnecessary.

That a rule nobody authored should speak more weakly than what the agent was told is not modesty. It
is §12's own discipline: a rule states how strongly it would conclude, and what its premises were
worth is not its to say.

### The agent harmonizes itself

What is left is the case where two rules genuinely do contradict each other and the agent must settle
it from inside. That needs precedence to be a **claim** rather than a table, which is §18's finding
and the reason it is stated there rather than here.

```
rule <trust-what-i-was-told> = implies( { +rule(?r), +adopt(?r) },
                                        { +overrides(<secret>, ?r) } )
```

⭐⭐⭐ That line is what this section is for: **a precedence about a rule that did not exist when it was
written**, applying to whatever the agent learns. Two examples become a live rule, a standing policy
orders it under what the agent was told, the learned rule loses about the sealed vault, and the defeat
is on the record.

And the agent settles a conflict it did not author: it decides the precedence, the loser is defeated,
and a run reaches quiescence in **2 applications** where the unsettled pair oscillates for 60 ticks.

⚠⚠ **A conflict starves the rule that would settle it.** `hot`, `cold`, `hot`, `cold` — and the referee
never gets a turn. It needs `standing`, which is §19's carve-out arriving for the fifth time and from
a new direction. It is also the loop-detection case below.

### Retiring a rule is not the same as defeating it

The obvious response to a rule that loses is to retire it, and it is measurably wrong:

```
{+defeated(?l, ?w)} ⟹ {+dormant(?l)}
```

This works, and it **throws away every case the rule was right about** — measured, the learned rule
was retired before it ever applied. `defeated` is deduped per pair, so *how often* a rule loses is not
askable, and the corpus can only say *once is enough*, which this shows is wrong.

> **Losing an argument is not being wrong.** A rule that is right about a thousand cases and loses
> about one has one exception, not a defect.

Where the count belongs is §19's **credit walk**, which already carries one: `harmed` says a rule was
on the support of something wanted being made false, and it is a count over the trail rather than a
per-pair flag. That is the next thing to try, and it is a use of machinery that exists rather than a
new relation. The general lesson is the one §16 and §18 both reached:

> **Before adding a relation, check whether the one you want is a count over the trail.**

### Loop detection: designed, measured, and deliberately not built

A rule set the agent is amending can loop in a way an authored one does not, so this belongs here.
Every occasion the design has is a record of **stopping** — `quiet`, `left`, `stopped`, and the effort
counters — and **a loop is the failure to stop**, so none of them ever fires. Measured on a deliberate
runaway: 800 ticks, always applying, never once `quiet`.

The proposal is **rhythm detection**: check whether the recent sequence of applications repeats at
period 1, 2, 3…, and gate an expensive state comparison behind a cheap rhythm hit. That escalation is
the shape §19's guards already have — *escalate before believing the cheap answer* — mirrored here as
**escalate before believing you are making progress**.

Measured before building, and the measurement changed the design. Over a whole suite, keyed on
`(seat, rule, bindings)` per applied tick:

| | period 1 | periods 2–8 |
|---|---|---|
| **62 healthy machines, 2,038 applications** | **0** | **0** |
| the deliberate runaway | 272 | 0 |

* ⭐ **Period 1 alone is a perfect discriminator here** — zero false positives. So the cheap filter is
  not a filter; it is the whole test.
* ⭐ **Do not build the second phase.** It was a fix for a false-positive problem that does not exist.
  The deletion arrived before the code did.
* ⚠ **The seat must be in the key.** Without it, the same rule applying inside a hypothesis and outside
  it reads as a repetition. An application repeated in a different frame is not a repetition.

⚠⚠ And the first measurement was contaminated twice, both times by the instrument: no seat in the key,
and a suite that now *contains* deliberate runaways, so it cannot measure a detector's false-positive
rate without splitting them out. **A fixture that contains the pathology cannot measure the detector**
— which is the census's own finding from the opposite side.

⚠⚠⚠ **And it stays unbuilt for a stated reason.** The suite contains exactly one loop of one kind, so
*period 1 is enough* is a claim about a sample of one, and a longer-period detector shipped today
would be **unfalsifiable**. A 2-cycle fixture comes first. What it would deposit is `circling(<seat>)`,
deduped like the effort counters, and it would **not stop the loop**, for the open-goal veto's reason:
the machinery deposits the occasion and a corpus says what it means.

### Scoring

| | (A) rules are authored, full stop | (B) a learned-rule sub-language with its own semantics | (C) a learned rule is an ordinary rule |
|---|---|---|---|
| not leaking | ✅ trivially — nothing is learned | ❌ two rule shapes, and the learned one's provenance and defeasibility must be reinvented | ✅ authored and learned rules are the same node kind; a corpus cannot tell them apart except by asking |
| not lossy | ❌ *where did this rule come from* has no answer, because there is no rule to ask about | ⚠ the examples survive only if the sub-language keeps them | ✅ the licence names the tool, the examples and the adoption |
| readable | ✅ | ❌ *which rules are about time* now needs two queries | ✅ R4's questions are unchanged, and *which of my rules did I learn* is one more of them |
| composable | ❌ two authors amend one file | ⚠ a learned rule cannot be ordered against an authored one without a translation | ✅ `overrides`, `unless`, `dormant` and composition all apply unchanged |

(C)'s cost is real and is stated below. What (B) would have bought — a place to put *this one is only
learned* — turned out to be unnecessary, because §16 already provides it in the conclusion.

### Costs

* **A learned rule is a claim, and it can be wrong the way any claim can.** §19 puts learning in recall
  because being wrong there is recoverable; this is the one place in the design where learning is
  **not** confined to that step, and the compensation is that the artifact is inspectable, deniable
  and orderable rather than opaque.
* **Two examples are two examples.** Nothing here says how many are enough, or what to do when a third
  contradicts the rule the first two produced.
* **The trail is unreadable to the learner** (§6, §22), so the examples must be corpus facts rather
  than the agent's own experience — which is the source that would actually make this pay.
* **A clarification request about a rule cannot leave the agent** (§15). *Ask the author about the rule
  that lost* is decided on and never emitted, because a rule node is generic and the boundary refuses
  a description. Every human-in-the-loop story for acquisition is blocked on it.
* **Nothing retires a learned rule well.** Defeat is too blunt, and the credit walk is proposed and
  unbuilt.
* ⚠ **And the composition test is the only thing that found any of this.** Four pieces, each green in
  isolation; the first fixture that made them meet broke in two places, and neither was visible from
  inside the piece that contained it. That is §2, and it is the strongest procedural claim this
  document makes.

---

# Part IV — Gates and open questions

---

## 21. Acceptance

### The floor gate

The one that keeps Part I honest. It has two clauses and the second is the one that will be
forgotten:

> **For every bundled convention, the rule-level definition exists; the compiled path produces
> identical answers; and the compiled path is interruptible at the same points.**

Run it first on §10's read, since that is the convention an implementation is most certain to have
compiled into itself. A convention with no rule-level definition is a convention that has escaped onto
the floor, whatever the document says — and one that cannot be stopped mid-way has escaped even if its
answers agree.

Four companion counters, cheap and blunt:

* **the number of phases in the interpreter's step.** Every phase is a convention the engine knows by
  name, and — per §4 — every phase is compiled control flow. Target: zero. **It is zero.**
* **the stratum-0 scan.** Every rule the implementation applies without a read must have an antecedent
  whose members are all structural (§6).
* **the census.** Appendix C, and the count of reserved names with an interpreter branch behind them
  is the measure of progress.
* **the judgement census**, below — and it is the one with no natural advocate, because every entry on
  it is something that works.

### The judgement census, and why it is not about purity

Every counter above asks *how much machinery is there*. This one asks a different question, and it is
the one that predicts where the next defect will be:

> **Which judgements does the machinery make that no rule can argue with — and if one were wrong, how
> would the agent find out?**

The second half is the test. Most of what is not rules embodies **no judgement at all**: whether
unification succeeds, what a chain's predecessor is, what an entry was built from. There is one right
answer, so there is nothing to argue with, and being code costs nothing. §6 proves three such places
must exist — reading, selecting and proposing each bottom out in a function — and a fourth of the same
kind is free.

A **judgement** is different. *What a situation is about* has no forced answer; it is exactly the kind
of claim §19 says experience should supply, and it lives in one method. That is not a tidiness
complaint, and the cost is specific:

> **A seam is where the agent stops being able to be wrong about something.** If it is a rule it can
> be defeated, denied, dated, credited, blamed and overridden. If it is a seam, it is simply how
> things are — and the agent cannot notice it was mistaken, cannot be told, and cannot improve.

**And they accumulate silently, because the suite cannot see them either.** This is the state gate's
finding generalised: *nothing that asserts what the agent concluded can see what it was thinking about
while it concluded it.* A judgement that only degrades **quality** is invisible to every check that
asserts **correctness** — a wrong key set makes a worse choice and never a wrong conclusion, so no
fixture fails and only a purpose-built instrument ever sees it. So a seam blocks twice: the agent
cannot learn it, and nothing reports it.

⚠ **§6 states that recall is opaque and must remain the only opaque thing. That is already false, and
nothing was counting.** The census as it stands:

| judgement | argued? | if it were wrong |
|---|---|---|
| **recall** — which rules come to mind | ✅ §6's third regress; opaque by construction, and §19's carve-out keeps it off the safety path | a worse plan or a later surprise — recoverable, which is why learning lives here |
| **`_in_play`** — what a situation is about | ❌ named in §19 and never argued | worse choices forever, invisible to every check |
| ~~**the connective of a composed rule**~~ | ✅ **resolved, and by dissolving** — see below | — |

⭐ **The third entry came off this census by turning out not to be a judgement at all**, and how that
happened is the argument for keeping the census. *Which connective should a mixed composition get* had
two defensible answers, which is the census's own signature for a judgement. Asking what the composite
would **mean** found something else: composing across a `causes` **flattens two moments into one
antecedent**, because a `causes` consequent lands in a successor, so the second rule's other premises
are read one moment later than the first rule's own. Measured, on a world where the extra premise
arrives only once the first rule has acted, the derivation reaches its conclusion and the composite
does not.

So the question was wrong. It is not *which connective* — it is that **some compositions must not
happen**, and §4's claim that *n steps become one* has to mean **with the same conclusion**. The
unsound shape is now refused, and the refusal is exact rather than cautious: only premises **beyond
the seam** are relocated, so a second rule that is just the seam composes across a `causes` soundly.
Once the unsound ones are gone the connective is **forced** — a chain that crossed a causal step has
advanced a moment, so the result is `causes`, by §14's own persistence test.

> **A judgement with two defensible answers is sometimes a question asked at the wrong level.** The
> census cannot tell you that; it can only tell you where to look.

The discipline that follows is one line, and §20's `adopt` already obeys it: **the corpus decides, the
function executes.** What decides that a rule is worth adopting, or that two rules are worth composing,
is a claim; what happens afterwards is not a judgement and may be code.

### The gate must be run against a moving target

An optimisation of a read is a **re-implementation of its semantics**, so the slow definition stays and
the fast path is held to it. There are now three of these, one per thing the loop keeps:

| gate | holds | to |
|---|---|---|
| the **read** gate | the native walk | §10's rule-level read |
| the **state** gate | the maintained state, its index and its keys | §7's walk, recomputed |
| the **move** gate | the lazy choice at the top of a heap | defeat, quiescence, forgoing and arbitration computed over the whole list |

The second is the one that taught the general lesson, because one of its three columns cannot be
checked any other way:

> **Nothing that asserts what the agent concluded can see what it was thinking about while it
> concluded it.** A wrong key set makes a worse choice, never a wrong conclusion, and every fixture
> asserts an outcome the loop reaches anyway.

⚠ **An instrument that deposits has stopped observing.** The move gate re-runs the arbitration path
against the same state, so anything that path writes must be written outside it — which is why §20's
`defeated` is deposited by the tick rather than by the chooser.

⚠ **A comparison instrument can only read a mutation the fixture does not already talk about.** A gate
that reads the *shipped* method rather than capturing the definition at install will score the suite's
own deliberate mutants as disagreements, and report them as findings.

### An agreement gate that agrees is worth nothing until it could have disagreed

Running the read gate produced three false passes in a row, and the pattern is general enough to state
as a requirement rather than a war story.

The read agreed on every case — with the entire **deposit index** deleted, because the fixture's
"revision" was written at a different locus, so the locus key decided everything. Fixed, and it agreed
again with the tiebreak deleted, because the rule-level read was returning the *first* unbeaten
candidate and happened to enumerate in the same order as the native walk. Fixed by making the read
refuse ambiguity, and a third rule stayed unkillable until the fixture put an **unrelated** entry
between two competing ones, since transitivity only matters when the entry in between does not
compete.

> **Every gate must delete each rule of the thing it checks, one at a time, and report any rule the
> fixture cannot kill. A rule no fixture can kill is a rule the fixture is not testing.**

This is §13's *bounded expansion returns a result and a state* and §19's two silences, arriving now
aimed at the checks themselves: **passing** and **unable to fail** are different outcomes, and only one
of them is evidence.

Three corollaries, each of which cost this design a false result:

* **A check that stopped being able to fail is the default, not the exception.** Kill-probing found
  ungated lines in every commit it was run against.
* **A runner has to be able to say False about an absence.** A probe that crashes the runner instead of
  failing the check reports nothing, and reports it loudly.
* **Every instrument prints its count, not only its failures.** *0 failing* reads the same whether it
  ran thirty checks or none, which is how one commit silently deleted ten of them.

### The bundle gate

Delete each shipped rule and each answerer binding, one at a time, and re-run the suite. It answers
two questions, and they are two:

| | question | mutation |
|---|---|---|
| **load-bearing** | does anything depend on this? | remove it |
| **contestable** | may a corpus turn it off? | deny it, as a corpus would |

The second column is where §19's *deniable is not forgettable* was found. ⚠ And a removal that makes
the runner **raise** must print `raised` rather than a count, since the run stopped at the first check
that could not survive the absence.

### The commutation gate

Behavioural, not representational. Not *can the system reproduce this text*, but:

> For every rule `R` and every moment `s`:
> reading backwards from a goal proposes `R` at `s`
> **if and only if**
> reading `R` forwards at `s` yields a moment satisfying that goal.

Run it as a property over the whole rule set. A rule whose two readings disagree is a rule whose
consequent is lying about what it does.

The check is available **only because** there is one statement with two readings. With one rule per
direction it is untestable by construction. With program bodies it is undefined, because there is no
backward reading to compare against.

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
* **Containment.** Nothing concluded inside a supposition is readable as current belief, **and nothing
  supposed reaches the world**: no act is emitted and no rule is adopted from inside a frame. The
  first is structural (§10's ancestry); the second and third are conditions at the doors, because
  effects and rule sets are not in the chain.
* **No laundering.** A conclusion drawn from an uncertain premise crosses out wrapped, and nothing
  reaches the bare claim except a rule a corpus wrote. This replaces an earlier gate that compared
  ordinal grades along the trail; the structural version is stronger, because the nest records *which*
  premise was weak.

### Gates from acquisition

New with §20, and the first two are the reason it is a section rather than a paragraph:

* **The adopted rule is the node the graph describes**, not a twin of it — checkable by asking a
  corpus's own claim about a rule whether it holds of the live one.
* **A tool builds in the corpus's name scope**, so a rule it composes matches what the corpus can
  write.
* **Nothing supposed is adopted**, per containment above.
* **A learned rule concludes wrapped**, so it cannot contradict what the agent was told without a
  corpus crossing.

---

## 22. What this design does not settle

### On the floor and the bundle

* **Deriving the compiled path** (§4). *Compile rules, not control flow* says how compilation must be
  shaped; it does not say who does it. Today an implementation hand-writes the fast path beside a
  rule-level definition that may not exist, so the two can silently disagree and the gate is a test
  rather than a guarantee. A **transpiler from rules to the host language** would make agreement hold
  by construction, at which point *slowing down* means running the source instead of the artifact.

  Two constraints, both from §4 rather than from taste. The target language must not be named in the
  design: what ships is the **compilation contract** — derived from rules, rule boundaries preserved
  as yield points, artifact discardable. And the unit stays the rule, because the unit of compilation
  is the unit of preemption.

  What is genuinely open is the **trigger**, and the natural answer is the one §4's grammaticalization
  argument already gives: *compile what has run often and never surprised; decompile what surprises.*
  Frequency is countable and surprise is an existing mechanism, so neither half needs new machinery.
* **Composition's three silent failures** (§4, §19, §20). *n* steps become one for any *n*, defeat is
  inherited, and the artifact is an ordinary node. What is unsettled:

  **Guard inheritance.** A composed rule must carry the union of its constituents' `unless`
  conditions, or it fires where the reasoning it replaces would have been blocked. Checkable at
  composition time and not specified. It is also the failure the analogy predicts: the pathological
  shortcut is not the fast one, it is **the one that has outlived its guard conditions**.

  **Nothing can be surprised inside a shortcut.** The intermediate conclusions are never deposited, so
  §18's mechanism is blind to them by construction. This is what makes decomposition necessary rather
  than optional, and what makes the trigger tractable: the licence names the constituents, so the
  agent knows exactly which sub-steps to re-run — more than the compilation loop can offer, since that
  can only say *run the slow path* and not *look here*.

  **When to compose, and when to decompose.** Unspecified — and now unspecified in the right place.
  And composing a recursive shape is unrolling, which is unbounded, so it takes expansion's
  budget-and-state discipline.

  ⚠⚠⚠ **A fourth failure, found and closed: composing across a `causes` loses conclusions.** A
  `causes` consequent lands in a successor (§14), so the second rule's other premises are read one
  moment later than the first rule's own — and the composite asks for all of them together, which is
  a stricter question. Measured on a world where the extra premise arrives only once the first rule
  has acted: the derivation reaches its conclusion, the composite does not. Under-derivation is the
  safer direction and is still a violation of *the same conclusion*; an over-derivation was looked
  for and **not found**, which is not the same as impossible, and that gap is open.

  It is refused rather than approximated, and exactly: only premises **beyond the seam** move, so a
  second rule that is just the seam composes soundly. What this retires is stated in §21 — the
  mixed-connective question was asked at the wrong level, and once the unsound compositions are gone
  the connective is forced.

  ✅ **Two items that were here are closed.** Composition no longer refuses uncertain conclusions,
  because §16 deleted the thing that made composing them a cache. And it **has a trigger**:
  `compose(<a>, <b>)` is an ordinary request, answered by `<composer>` and refused inside a
  supposition for `adopt`'s reason — one rule set is shared by every frame, so a shortcut built while
  supposing would apply after the frame is discharged and to everything.

  ⭐ The trigger is shaped by §21's judgement census rather than by convenience. *Which* rules are
  worth collapsing is a judgement, and a judgement the machinery makes alone is a seam — the agent
  could not notice it was composing the wrong things, because a bad shortcut makes worse work and
  never a wrong conclusion, so no fixture fails. So the answerer never proposes: **the corpus decides,
  the function executes**, and *compose what has run often and never surprised* stays a corpus's rule
  rather than becoming a constant in the loop.

  ⭐ And `composed(<c>, <a>, <b>)` is deposited, which closes §1's defect for the twelfth time:
  `composed_from` was a Python dict, so *which rules is this a shortcut for* was unanswerable — and it
  is exactly what *decompose on surprise* needs, since the agent has to know which sub-steps to re-run.
* **A seat move is not yet an entry** (§17). *Every seat move is a write*, and the re-seating that
  keeps the agent's own frame current while it hypothesises is not recorded as one.
* **Write-time hooks are not rules** (§4, Appendix C). Moving action dispatch to the write was right —
  §16 had already named the write as the one place effects leave the agent — but a hook is a callable
  the gate invokes, which is a branch wearing a different shape. What is open is whether *fire this
  when an entry matching P is written* can be a rule; it looks like a demand-driven match against the
  entry about to be deposited, which is §5's wall from a fifth side.
* **Explaining a read** (§6). Stratum 0 produces structure rather than entries, so the resolution that
  fed a conclusion is undated and unattributed. R5 covers the conclusion and not the read.
* ⭐ **Whether an ordinary rule may read the skeleton** (§12, §6, §20). This is the same gap seen from
  the other side, and §20 makes it expensive rather than academic. An entry's support is structural,
  so the agent's own trail — the best source of examples it has — is readable by the machinery and not
  by the agent's rules. Promoting it to entries reinstates §6's circle; leaving it means every example
  must be a corpus fact. Neither is obviously right and the question is not small.
* **Match, callable from a rule** (§5) — **settled.** It is a request, not a sixth floor item, and it
  must answer with instantiated results rather than a binding. Pattern against pattern turned out to
  be a *different* operation — unification — and it too is a service. Anti-unification is the third
  member of the family (§20). What is still open is **lifting a modality across a rule**, the one
  caller of the four with no service — and §16 argues it is not wanted, since supposing dominates it.
* **`unless` is described and not implemented** (§12). Precedence exists; the other half of
  defeasibility does not. Composition can therefore inherit only the defeats, and §12's *unless at
  altitude* is unwritable in any corpus this engine loads.
* **The skeleton is half built** (§11, §12, §13, §15). ✅ A member may now say **where its entry
  sits** — `+acts(goblin) at ?m` — so a rule relates two moments, which is what a foreign corpus was
  spending 24% of itself simulating with a round counter. What remains absent: `where` and the
  skeleton's *structural* members (`?n = succ(?m)`), named entries, and spans as loci — an entry's
  locus is a moment and never a span, so a span is not a locus in fact however clearly §11 says it is
  one.

  ⚠ **And the built half is bounded by the read, not by the notation.** A matcher sees the resolved
  state, one entry per proposition, so two *different* facts at different moments relate and **a
  single fact's own history does not**. Reaching that means matching over the raw chain — §6's
  stratum-0 territory — and reopens the bootstrap. Measured as the discriminating case: *it was on,
  then it was not* finds nothing.

  What that costs, listed rather than implied: **§13's shapes cannot be written at all** — *taking
  turns*, the document's worked example, has never run; **§11 is a design for a construct the engine
  does not build**; **§15's *an arrival should be a moment*** has no route, so a corpus still needs
  one trust rule per sign; and **§16's expansion of a change-term** — *the level rises*, holdable
  today as a wrapping proposition, cf. R6 — cannot be discharged into a comparison across two moments,
  because relating two loci is exactly what a skeleton is for. That last one is R6's own example —
  *pouring raises the level, by an unknown amount* — and it splits in a way worth recording: the
  **direction** is holdable today as a wrapping proposition beside §9's `?`, on §16's pattern and with
  no new mechanism, while the **expansion** into a comparison across two moments needs the skeleton
  and the **magnitude** needs the constrained-not-bound value below. Three separate gaps behind one
  English verb.

  This was found by probing the surface rather than by reading it, and the way it hid is worth
  recording: **the notation is used consistently throughout this document, so it reads as
  implemented.** A convention that is never exercised looks exactly like one that works (§5's *data
  rots in a way a branch does not*), and no gate covers a convention that has no rules to delete.
  Whether the surface should grow `where` is open; that it currently promises it is not.

  ⭐ **And there is a narrower substitute, which is probably the right first move.** Measured, a rule
  can already **bind** a moment — occasions hand them over, so `{+quiet(?m)} ⟹ {+sawmoment(?m)}`
  works — and cannot **relate** two: `succ`, `pred` and `before` are all absent from the graph. So the
  gap for the ordinary cases is not the whole skeleton, it is **succession, readable**. Three ways to
  supply it, and the design already prefers the third: a skeleton member costs a new member kind and
  new surface; deposited `+succ(m7, m8)` entries make **structure deniable**, which §12 refuses, and
  cost O(n) entries nobody asked for; an **answerer** — `pred` as a request answered by a function
  over the chain — costs neither, is demand-driven, and is §19's established seam, where six already
  live. It does not reinstate §6's circle, because the function reads structure rather than entries.

  ⭐⭐ **The same move closes `rests_on` above**, which is stated as a dilemma with two bad horns —
  promote the trail to entries and the circle returns, leave it and every example must be a corpus
  fact. An answerer is the third option neither horn considered, and one mechanism would settle both.

  ⚠ It is a **substitute and not an equivalent**, and the difference decides which cases it covers. A
  skeleton member is matched *inside one match*, so a multi-locus rule fires in one application; an
  answerer is a request, an answer, then a rule — several ticks, with deposits between them and other
  rules free to interleave. Irrelevant for expanding a single change-term (§16); probably decisive for
  recognising a shape over a long stretch (§13). So this narrows the item rather than retiring it.
  ⚠ And a deposited answer *about structure* is deniable, which is mildly incoherent: denying
  `pred(m7, m8)` does not change the chain, only what rules believe about it.
* **How much of the bundle is actually rule-expressible** (§4). The gate is run for the read, the
  state and the move. It is not run for everything, and until it is, *these are conventions* is a
  claim about intent for the remainder.

### On the representation of reality

* **Is sign a member or a wrapper?** (§9) — **settled: both, and one-way translation.** What remains
  open is smaller: whether a channel reporting a denial should write `says(c, p, −)` or
  `says(c, not(p))`, and whether permitting both splits a corpus into dialects; and what a `?`
  conclusion becomes on the way out of a supposition, since `?` is about reading and cannot be a term.
* **Where uncertainty lives** (§16) — **settled, by deletion.** There is no grade. What is open is
  what replaced it: the **collapse table** for nested modalities — `{+likely(possible(?x))} ⟹
  {+possible(?x)}` — is a corpus's to write and the bundle ships nothing. Whether the bundle should
  carry a default family of these, and what it would mean for two corpora to disagree about the
  ordering, is undecided. This is the bill §16 says it is paying: the ordinal stopped being free and
  started being arguable.
* **Evidence accumulation** (§16). Two independent *likely*s should amount to more than *likely*. With
  the grade gone, the shape of the answer is clearer rather than closer: it is **counting over
  episodes** (§13, §19), with no arithmetic anywhere, and the counting scheme is unspecified.
* **Incompatibility has no vocabulary** (§8). You can deny a proposition; you cannot say that two
  propositions cannot both hold. Noticed when an older engine's `refutes` had nothing to port to.
* **Consistency within a moment** (§8). Two entries with opposite signs in one locus is permitted and
  undetected. That is the right default, since consistency is a question rather than an invariant, but
  the design does not say who asks it or when.
* ⚠⚠⚠ **A HALF-FINISHED CHANGE IS INDISTINGUISHABLE FROM A FINISHED ONE, AND AN AGENT WILL ACT ON IT**
  (§8, §17, §19). Predicted by a foreign corpus and constructed here. A transfer takes gold from one
  purse and puts it in another; with the amounts computed by a **tool**, that is necessarily two
  applications, because an answer arrives through the write on a later tick. Between them the state is
  **internally consistent and false**:

  ```
  total(10, 5)   total(7, 5)   total(7, 8)        -- 15, then 12, then 15
  ```

  Nothing contradicts anything. `purse(hero, 7)` and `purse(smith, 5)` are both perfectly good claims.
  There is simply a moment at which the world holds twelve gold and never did.

  **And it is actionable, which is what makes it serious rather than untidy.** An ordinary economy rule
  — *refuse service when the party is short* — reads the total, concludes `below(12, 15)`, and the
  agent **emits `refuse_service(hero)`**. Measured. The act leaves the agent, and §19 is emphatic that
  an act cannot be forgone once emitted. The final purses are conserved; the **decision** is not.

  > **The design has a name for two entries that disagree, and no name for a state that is halfway
  > through a change.**

  What exists today is narrower than it looks. **A consequent is atomic** — one application deposits
  all of its entries into one moment, so a transfer written in a single rule cannot be observed
  half-done, and that was measured too. But arithmetic is a tool (§22's magnitude item), and a tool's
  answer arrives on a later tick. So:

  > **Atomicity is available exactly when you do not need a tool, and you need a tool for arithmetic.**

  ✅ **ANSWERED, by making the computation part of the application.** A **computator** is a function
  given *values* and returning a value — never the machine, the frame or the entry — so it cannot
  reach the graph, the register or the world. **Purity is structural rather than declared**, which is
  cheaper and stronger than the 45 lines of transitive static analysis the deleted engine used to
  prove the same property. It is written as an antecedent member and binds with `as`:

  ```
  rule <pay> = causes(
      { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y),
        minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },
      { ? purse(?a, ?x), +purse(?a, ?x2), ? purse(?b, ?y), +purse(?b, ?y2), … } )
  ```

  Measured against the observer that caught the hole: `total(10, 5)` then `total(7, 8)`, **and nothing
  in between**. Where it belongs is §12's **skeleton** — *conditions on the binding that claim
  nothing*, which already houses distinctness — because arithmetic asserts nothing about the world; it
  says how the binding was built. A computed member accordingly consumes no entry and contributes
  nothing to the trail: five members, three on it.

  ⭐⭐⭐ **And what remains is not the same problem, which is the correction this item most needed.**
  The defect was never *an observer saw an intermediate*; it was *an observer saw an intermediate that
  corresponded to nothing*. The world never held twelve gold — the split was an artifact of arithmetic
  arriving through the write. That artifact is now gone.

  A change that genuinely waits — on the world, or on a tool that is not pure — **really does** have an
  intermediate state, and that state is **true**. The gold has left one purse and not reached the
  other. An agent that could not see it would be missing a fact rather than protected from one, and
  the same test case makes the point: refusing service to a party whose money is genuinely in transit
  is arguably right, where refusing during a two-tick arithmetic artifact was not.

  > **Only the corpus knows that two ticks are one event.** The machinery cannot know it, so it
  > cannot enforce it, and `+transferring(?a, ?b, ?n)` is not a workaround for a missing mechanism —
  > it is a judgement in the one place that can make it, which is where §4 puts judgements.

  So the earlier complaint here — that this is *a convention every corpus has to remember*, the shape
  §19 refuses — was misapplied. §19 refuses a discipline when **the machinery could have known and
  did not**. Here it genuinely cannot.

  ⭐⭐⭐ **And nothing is missing — the convention was simply written wrong.** This item said, twice,
  that the design lacked *a vocabulary for transitional states*, and proposed a moment that declares
  itself unsettled. That was §2's own warning happening live: **reaching for a new engine feature to
  rescue a convention is how islands are made.**

  §9's `?` is the vocabulary. *It invalidates without replacing: it stops the walk and reports
  ignorance.* A value part-way through a change the corpus has not finished making is **not known**,
  and saying so is what `?` is for. What produced the phantom state was a corpus asserting a number it
  had no warrant for yet:

  ```
  rule <start>    = causes( { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y) },
                            { ? purse(?a, ?x), ? purse(?b, ?y), +pending(...) } )
  rule <complete> = causes( { +pending(...), +confirmed(?a, ?b), … },
                            { +purse(?a, ?x2), +purse(?b, ?y2), -pending(...) } )
  ```

  Measured: while in transit the purses read `?`, **an observer cannot form a total at all**, and the
  only one on the record is from before the transfer began; on confirmation, `total(7, 8)`, conserved.
  No new construct, no marker fact to forget, and the guarantee is structural for the reason §9 gives —
  a reader cannot obtain the value without the sign, because the sign is a member.

  > **A change you have not finished making leaves the facts it touches UNKNOWN, and that is a
  > statement the design has always been able to make.** *In transit* is open-class domain content; the
  > ignorance it implies is not.

  ⚠ Recorded because the route to it is the finding, not the answer. This item was wrong three times:
  first that atomicity was broken (only the *artifact* half was), then that a real intermediate needed
  hiding (it is true and should be visible), then that saying so needed new vocabulary. Each correction
  came from asking which of substrate and convention was at fault, and the answer was the convention
  every time — which is what §2 says the default answer must be.

* **When a revision is warranted** (§10). The two indices make *I now think otherwise about `M7`*
  sayable, and say nothing about when an agent should write one. Left alone, a system that revises the
  past freely can rewrite its way out of any surprise, which is §18's mechanism defeated by §10's
  permission.
* **Negation versus a false value.** *The stove is not lit* and *the stove has the attribute lit,
  false* are both expressible and mean different things. Nothing guides the choice, and nothing
  detects the two being used interchangeably within one corpus.

### On what the representation allows

* **The use/mention wall at the boundary** (§15, §20). An intent naming a rule never leaves the agent,
  because a rule node is generic and the boundary refuses a description — so every clarification
  request about a rule is decided on and never emitted. The entry already carries what is needed to
  tell use from mention (§5); nothing reads it there. This is the first thing acquisition needs.
* **Cardinality in backward matching** (§13). Where a count lives is settled — a fact about a group
  node. How a backward reader *uses* one is not: unifying a wanted fact against a group of unknown
  size needs cardinality declared per relation position.
* **Shape equivalence** (§13). Undecidable in general, so duplicate shapes will accumulate undetected.
  Open: whether a decidable fragment is worth carving out.
* **Structure against claims** (§12). An antecedent carries two kinds of member and nothing
  structurally stops an author writing a claim where a skeleton constraint belongs, or the reverse.
* **Distribution** (§13). *Each file was copied* against *the files together filled the disk* is a fact
  about the entry, but which entries need it, and what a read that does not ask for it should return,
  is not specified.
* ~~**Constrained-not-bound values.**~~ **Mostly answered, and the item was asking for the wrong
  thing.** It said *the level rises by an unknown amount* wants a value member that is constrained
  rather than bound. Probed, that turns out to be three separate questions with three different
  answers, and only the last is open.

  **A known magnitude is a tool.** `20 − 3 = 17` needs no representation at all: arithmetic is a
  function, and §17 says a request answered by a function is a tool. Measured — a `minus` answerer
  and two ordinary rules take a purse from 20 to 17, with the old value invalidated. Nothing in the
  engine changed. ⚠ And the fixture that first ran it debited forever, because nothing retracted the
  trigger: §14's re-ask criterion, arriving in a corpus rather than in the machinery.

  **An unknown magnitude does not want a value slot; it wants a node.** Do not name the value — name
  the **quantity**, and say what is known of it:

  ```
  rule <pour> = causes( { +level(?g, ?v), +poured(?g) },
                        { ? level(?g, ?v), +greater(after(?g), ?v), +rises(level(?g)) } )
  ```

  That is §13's own move for plurality — *mint one node for the group and do not enumerate it; what is
  known about its size is an ordinary fact about that node* — applied to a scalar instead of a set.
  Measured, and it **composes**: a downstream rule reading `greater(after(?g), ?v)` against a brim
  concludes `overflows(?g)`, so the unknown quantity is genuinely reasoned with and not merely
  recorded. The direct form — a consequent naming `level(?g, ?w)` with `?w` unbound — stays refused,
  at load, with a message saying so, and that refusal is right: an entry whose proposition contains a
  free variable is an existential, which is the same thing §5 says a `−` member cannot express.

  ⚠ **What is actually open is narrower and is about repetition.** Once the level reads `?`, a second
  change has nothing to compare against, so the quantity must be **chained** — `after1`, `after2`,
  with `above(after2(?g), after1(?g))` — and each step needs its own node. Measured working, and it
  is ordinal tracking rather than magnitude: the agent can come to know *the level is above the brim*
  and can never again know *the level is 5*. Whether that is a gap or simply honest ignorance is the
  real question, and this design's instinct is the second — **an unknown amount yields an unreadable
  value, which is correct rather than missing.** What would refute that is a corpus needing to
  recover a readable value after an unquantified change, and none has been produced.

  Note the boundary §11 draws, which is unaffected: **recognising** an ongoing pattern does not need
  any of this — a span superseded by a longer span is ordinary versioning — only **predicting that it
  continues** wants an unbound endpoint.
* **Span normalisation** (§11). Equality of span content must be normalised by chain order rather than
  member order; the normalisation is not specified.
* **Resolving calendar terms** (§15). Calendar terms denote and the chain orders. What is unsettled is
  the resolution itself — who computes it, against whose clock, and what happens when a term denotes a
  stretch the chain does not reach, as *next Tuesday* does.
* **An arrival should be a moment** (§15, §18). A channel reports a *signed* state of affairs, and a
  proposition carries no sign, so the sign rides as a member of `says`. Needs §12's skeleton — or is
  dissolved by §9's remaining question.
* **When to cross a modality** (§16). A rule that crosses every hedged fact it sees crosses the hedged
  facts it just produced, and only terminates when the wrapped terms run out of applicable rules. Eager
  crossing has no criterion; the criterion is **demand**, which is backward reading, and the two are
  not yet connected.
* **Enforcing the gate** (§17). *No write bypasses the stamp* is a property of one place rather than a
  prohibition on rules, which makes it checkable — but the check is not written.
* **Seat discipline across processes** (§17). Frames form a forest and any of them may be in focus.
  Nothing says whether two processes may hold seats in the same moment at once, what it means if they
  do, or whether one process may move another's seat.
* **Backtracking** (§18) — **half settled.** Bindings live on a plan node, and a binding can now be
  reconsidered, because *what has already been tried* is sayable. What made it work was needing
  **both** halves — the exclusion and the denial — and either alone is worse than neither. What is
  still open is **who decides** to reconsider: the recovery rule is keyed on `quiet`, which is safe and
  is not the same as knowing that a plan has gone wrong.
* **Retracting a contradicted expectation** (§18). Precedence stops a defeated rule applying, but
  nothing retracts what it already concluded, and its antecedent still holds. The agent goes on
  believing both the expectation and its refutation. §16's *losing your reason is not acquiring a
  counter-reason* says the machinery must not deposit the denial; it does not say what should.
* **An occasion warrants a re-ask only if re-asking cannot produce one** (§14, §18, §19). Stated,
  measured both ways, violated in three separate places, and **not enforced**: nothing stops an author
  writing the version that loops. Whether it can be checked statically is unknown.
* **Loop detection** (§20). Designed, measured, and deliberately unbuilt until a fixture exists that
  can falsify a longer-period detector.
* **How badly a rule cost something** (§19, §20). `harmed` is two-valued and the learner suppresses on
  it, because the preference table's numerals are non-negative. So *this rule is slightly worse* is
  unsayable, and an agent cannot weigh a small cost against a large benefit. It is also what §20 needs
  in order to retire a learned rule on a count rather than on a flag.
* **Forgoing's remaining edges** (§19). Rivals are noticed **at the tick the choice is made**, so an
  alternative that only becomes applicable later is not passed up. And *complementary* work — two
  rules that should both run for one want — is the case a corpus must declare, with no way to declare
  it beyond denying the deposit.
* **A goal that vetoes once may be dropped on the second pass** (§19). The veto fires once per goal per
  seat, which is what makes it terminate, and it means the guarantee is *the agent was given the
  occasion to react* rather than *the goal was disposed of*. The stronger property wants a notion of a
  goal being **discharged** — achieved, refused, handed over, or explicitly abandoned — that the
  design does not have, and it is the same missing notion as *when is a plan settled*.
* **A wind-down after stopping** (§19) — **half settled.** An outstanding goal vetoes the stop and
  hands the loop back, so reacting to it is ordinary reasoning of any length. What is open is a
  wind-down that is not about a goal — putting something down, closing something, saying goodbye —
  since `stopped` is terminal and nothing can key on it.
* **Experience is one episode deep** (§19). A second preference row does not accumulate.
* **Familiarity** (§19). The escalation trigger wants *have I seen moments like this?*, which is a
  measure over the episode record and is not the same as *did recall return anything*.
* **The exploration schedule** (§19). When the exhaustive pass fires in the absence of an impasse. What
  is open is the *rate*, not the requirement; without one, recall calcifies silently.
* **Recall's prize cannot currently be measured** (§19). The apparatus's authored precedence decides
  the early ticks regardless of what recall proposed, so the workload that measured recall no longer
  can. That is not a new problem; it is the deleted phase's precedence claim surviving in authored
  order.

---

## Appendix A. Glossary

Each entry says whether the term names something on the **floor** (§4) or in the **bundle** — the
conventional representation of reality that ships with the engine and can be replaced.

| term | floor / bundle | definition |
|---|---|---|
| **adopt** | bundle | a request that makes a rule the graph describes into a live rule. A **door**, not a question — it reaches no verdict. Refused inside a supposition. |
| **again** | bundle | `again(<request>, <occasion>)` — re-deliver a request, because of this. A fresh node per occasion, so concluding it is a step. |
| **anchored** | bundle | of a moment: has individuals and a predecessor in the history. The opposite of *generic*. |
| **anti-unification** | bundle | the dual of unification: the least general pattern two structures are both instances of. What *learn from examples* is made of. A service, not a floor item. |
| **arbitrate** | mixed | choose one rule among those that matched. *Totality* is floor; the precedence it consults is a claim read from the graph. |
| **bundle** | — | the conventional representation of reality shipped with the engine: Parts II and III. Inspectable, replaceable, and authored in the surface. |
| **channel** | bundle | the intake path an entry arrived through. Mechanically observed, so it cannot be wrong. Distinct from *authority*, which can. |
| **circling** | bundle | *designed, not built* (§20) — the occasion for a loop, which is the failure of every other occasion to fire. |
| **close** | bundle | of two rules: their preference scores differ by no more than the tolerance. Doubt, deposited pairwise. |
| **composition** | bundle | collapsing a derivation into one rule. Learned, like recall; unlike recall, its output is a node and can be wrong. |
| **concluded** | bundle | `concluded(<frame>, <what>)` — this hypothesis reached this. Records that the frame reached it, never that it is true. |
| **connective** | bundle | `implies` or `causes`; the relation between a rule's two moments. Consumed by rules, not by the engine. |
| **defeated** | bundle | `defeated(<loser>, <winner>)` — the occasion for a conflict that actually happened. Not written when arbitration ignored the defeat, and not written for a rule that merely lost the tick. |
| **deposit** | bundle | the moment whose delta an entry sits in — when the claim was made. Distinct from *locus*, which is what it is about. |
| **door** | bundle | a place at the write where something anchored crosses — an intent outward, the register inward, a rule inward. Distinguished from an *answerer* by having no verdict to reach. |
| **dormant / due** | bundle | claims about whether a rule is proposed by recall. The first thing a corpus can say to recall, and what makes a callback directed recall rather than invocation. |
| **enough** | bundle | a claim that there is nothing more worth doing about something. The agent's second way to be over — *satisfaction*, against quiescence's *exhaustion*. A rule concludes it; the loop only reads it, and an open goal outranks it. |
| **entry** | bundle | a node with three members — locus, proposition, sign. The unit of assertion. Never four; see §16 for the member that was added and removed. |
| **excluded** | bundle | `excluded(<plan>, ?v, x)` — this binding has been tried. The half of binding revision that is not a denial, and useless without it. |
| **forgone** | bundle | of a rule, for a want: it was a live way of getting that want and another was taken. The fourth way a rule does not run, and the only one that is a decision. Deniable, which is what makes passing up recoverable. |
| **frame** | bundle | a reasoning in progress, as a process node. Carries a *seat* and a *topic*. Frames form a forest, not a stack. |
| **gate** | bundle | the write path, considered as the one place provenance becomes vocabulary. Distinct from the floor's *stamp*. Also where the doors and the norm veto are. |
| **generic** | floor | contains variables. A rule's two members are generic — which is also why a rule node cannot be the argument of an intent (§15). |
| **group** | bundle | a node standing for a plurality. Its membership is not stored; its size is a fact about it. |
| **harmed** | bundle | of a rule, in a finished episode: it was on the support of something wanted being made **false**. Sayable only per subgoal, because a `−` entry has a licence and an absence does not. |
| **helped** | bundle | of a rule, in a finished episode: it was on the support of something achieved. A fact about the trail; *so prefer it next time* stays a claim, hence a rule. |
| **licence** | bundle | the node that says what authorised a moment's delta, or what produced an entry. |
| **likely** *(and its family)* | bundle | a **wrapping proposition**, not an annotation: `likely(p)` is an ordinary node a rule can match, deny and reason about. There is no closed set — a corpus writes whatever modalities it wants and authors their collapse. |
| **locus** | bundle | an entry's first member: the moment or span the claim is about. |
| **match** | floor | find a substitution making a generic node identical to an anchored one. Structural, and with no opinion about entries. |
| **moment** | bundle | a signed delta, a predecessor and a licence. The bundle's only state construct. |
| **open** | bundle | a goal that was still outstanding when the agent tried to stop. Deposited by a veto, not concluded by a rule, so no corpus can forget to notice. |
| **overrides / supersedes** | bundle | two precedence relations, and one could not carry both intents: `overrides` is per step, `supersedes` per shared consumed entry. Both are **claims read from the graph**, dated and deniable, and either may be about a rule that did not exist when it was written. |
| **proposition** | bundle | a relation instance. Claims nothing until an entry places it. |
| **quiet** | bundle | the loop found nothing to do at this seat. The fact that makes an aggregate over a finished search legitimate, and the trigger a watchdog keys on. |
| **recall** | bundle | propose which rules come to mind. Learned; never complete. A policy, not a primitive. |
| **register** | floor | the one pointer: which node writes land in. That it holds a frame is convention; suspended positions are ordinary members of frame nodes, not further registers. |
| **rests_on** | bundle | what an entry was derived from. **Skeleton** (§12), not a claim — so nobody asserted it and no ordinary rule can match it, which is §22's open question. |
| **rule** | bundle | a fact whose two members are generic, related by a connective. Two rules that say the same thing are two rules. |
| **seat** | bundle | a frame's first part: the moment its writes are deposited in. Where the reasoning is standing. |
| **shape** | bundle | a pattern of indefinite extent, defined by recursive rules over spans. A node, so bounds and provenance attach to it. |
| **sign** | bundle | `+`, `−`, `?`, or the absence of an entry. A member, and — for negation only — with a term beside it. |
| **skeleton** | bundle | the part of an antecedent that relates its variable loci — succession, span endpoints, distinctness, support. Carries no sign, and claims nothing. |
| **span** | bundle | a node with two members, a start and an end moment. A locus for trajectory claims. |
| **stamp** | floor | the unconditional record, on every minted node, of what produced it. Not vocabulary. |
| **standing** | bundle | of a rule: its precedence is authored on purpose, so it outranks preference in arbitration and is never capped out of recall. **Overridable but not forgettable.** What keeps the apparatus from competing with the reasoning it serves — and what a referee needs so that a conflict cannot starve the rule that would settle it. |
| **stopped** | bundle | the register's record that the loop ended because something claimed `enough`. Deliberately not `quiet`, because an aggregate over a *finished* search is a lie about a *satisfied* one. |
| **stratum 0** | bundle | the rules whose antecedent members are all structural, so they are applied without a read. What breaks §6's bootstrap. |
| **tolerance** | bundle | how large a preference gap must be to be relied on. A knob, therefore a fact, therefore turnable by a rule — which is how *being careful* gets a trail. |
| **tool** | bundle | a request answered by a **function** rather than by a search. Proposes, never concludes: its answer is a record a corpus may believe or not. Its binding is a fact. |
| **topic** | bundle | a frame's second part: the locus its writes are stamped with. Equals the seat except when reasoning about another time. |
| **unsupported** | bundle | the answer to a request, deposited only when nothing supports a proposition. **Losing your reason is not acquiring a counter-reason** — the machinery never deposits the denial. |
| **write** | mixed | mint signed entries. The floor supplies a register and a stamp; the gate supplies locus, licence, source and deposit. |

## Appendix B. Alternatives considered

Each was scored in the section named; this table is the index.

| decision | rejected alternative | why |
|---|---|---|
| the floor (§4) | moment, entry and sign as engine-level | they are a *representation of reality* — teachable, replaceable, and the thing an agent reasons better by having |
| the floor (§4) | four primitives, recall among them | recall is a learned proposer, which is the opposite of a primitive; and *arbitrate* splits into floor totality plus an authored claim |
| the substrate (§3) | ordering as irreducible | it is encodable with unordered edges and slot nodes. It is on the floor **by economy** — its absence turns linear matching into subgraph isomorphism |
| the floor (§4) | suspended positions as further registers | an unbounded set of privileged slots, and R7 fails for the machinery's own control state |
| the floor gate (§4) | *identical answers, only slower* | a compiled convention is also uninterruptible, which is §18's objection to control flow one level down |
| the bootstrap (§6) | a distinguished region the engine reads without the convention | one fact in two shapes — §17's objection to augmentation |
| the bootstrap (§6) | stratifying by *how to think* versus *the business domain* | a real and useful cut, but trust, surprise and goal expansion are all domain-independent **and** talk about entries, so it does not bottom out |
| state (§7) | a mutable world state | overwriting makes *it changed* and *I was wrong* one operation |
| belief (§7) | a belief-set node beside the moment chain | a moment already is one; a second membership structure is a second ordering beside succession |
| assertion (§8) | truth as a value on the proposition node | minting a node in order to deny it asserts it; correction overwrites the record it corrects |
| the read (§10) | locus alone, or deposit alone | locus alone cannot tell a revision from what it revises; deposit alone lets a new belief about the past overrule a settled belief about the present |
| rule form (§12) | guard plus a program body | the backward reading is a hypothesis wearing entailment's clothes with nowhere to record it; and a program has no subject, so R3 and §20 are both unreachable |
| rule form (§12) | one rule per direction | two statements drift, neither is the other's premise, and the disagreement is undetectable |
| rule form (§12) | a flat list of patterns on the connective | arity varies with member count, and the signs end up nowhere, so two opposite rules become one node |
| antecedent (§12) | a per-member achievable/given mark | achievability is relative to the planner, the deadline, the situation and the rule set, none of which the author knows; and it lets a prohibition masquerade as an impossibility. **The design's first instance of closing an open concept.** |
| notation (§12) | `@` for a locus, `→` and `[…]` for timing, `@likely` for strength | punctuation that suggests a privileged mechanism is an island on the page; and the last of them was not notation for anything that survived |
| shapes (§13) | materialise a witness sequence | states a length nobody claimed |
| shapes (§13) | a reserved grammar with counters | a production cannot carry `unless` or `overrides`; decidability is bought and then spent on the first three extensions |
| timing (§15) | a third member of the connective | the connective's arity varies, an absent delay silently defaults, and two sources cannot disagree |
| connectives, modality (§14, §16) | fused connectives such as `likely_causes` | fuses strength with defeasibility and records neither; the name set grows multiplicatively |
| modality (§16) | a grade on the proposition node | *likely* said of no occasion and every occasion at once, and a cache of a derived value |
| modality (§16) | **a grade on the entry** | **the one that was chosen and then removed.** Scores well on three criteria and fails on use: not a term, so no rule can ask about it, no guard to cross, and no nesting. Measured at 4 of 3,740 rules, and the one comparison function had one caller. **Carried, composed, printed, never obeyed.** |
| modality (§16) | confidence as a grade on the rule | the same question is asked of sensors and speakers, so it belongs on the source |
| modality (§16) | a guard node per uncertain fact | optional guards mean two shapes for every consumer; mandatory guards mean a node and a hop per certain fact |
| modality (§16) | wrapping written per rule — a `likely` twin of every rule | the wrapped and bare corpora share nothing, since `likely(p)` and `p` are different propositions; measured at 2× |
| modality (§16) | a lifting rule over reified rules | binds against a rule's *pattern*, so it fires only where that pattern is ground — and real corpora are mostly generic rules |
| support (§16) | the machinery deposits `−p` when support is withdrawn | losing your reason is not acquiring a counter-reason; the engine would be asserting something nothing justified |
| entries (§17) | only the machinery may write entries | stronger than the requirement, which is that no write bypasses the stamp; it forbids honest past-directed claims and pushes trust into hard-wired intake |
| frames (§17) | a stack of frames | two hypotheses under comparison are siblings, both alive, neither the caller of the other |
| frames (§17) | copy conclusions out of a frame, re-qualified | one fact in two shapes, and it needs invalidation the moment the supposition is discharged differently |
| supposition (§17) | a nested run of the loop | a subroutine call, which owns the agent exactly where it most needs to be interruptible |
| precedence (§18, §19) | **a table seeded by the loader** | a rule could conclude a precedence and nothing listened; an adopted rule had no key; and it is a cache of a claim. Deleted at a measured cost of **6.42s against 6.38s** |
| precedence (§18) | one relation for both defeat intents | per-step defeat suppresses a rule for every case in the step; per-shared-evidence defeat cannot reach a rival that shares no premise |
| arbitration (§19) | preference ordering within the `standing` tier | measured: changes the sequence of applications without changing their count, the ticks or the writes. The apparatus is a dependency chain, so permuting it cannot shorten it |
| recall (§19) | goal-relevance as a filter | a preference must order, not exclude: it starved the most useful rule in a corpus, which did not fit the goal at all |
| forgoing (§19) | have the winner consume the want | retract the goal and credit cannot find what it achieved, and a failed act loses the want with nothing left to notice it |
| stopping (§19) | *if a goal is open there is more worth doing*, as a rule | recall may be incomplete about what to do, not about a goal it is dropping; so it is a veto, not a claim |
| acquisition (§20) | a third precedence relation for learned rules | measured four ways: unnecessary. A learned rule concluding **wrapped** does not contradict what the agent was told, because they are different propositions |
| acquisition (§20) | retire a learned rule on `defeated` | deduped per pair, so it can only say *once is enough* — measured, the rule was retired before it ever applied. Losing an argument is not being wrong |
| acquisition (§20) | a static conflict detector, shipped now | 3,545 false positives, one true positive already harmonized, one test rule. A corpus with no pathology cannot measure a detector for it |
| loop detection (§20) | a second, state-comparing phase behind the rhythm check | measured: period 1 alone is a perfect discriminator, so the cheap filter is the whole test |

## Appendix C. The name census

§5's test applied to the vocabulary an implementation actually reserves. The count is the measure of
progress, and it is expected to shrink.

**Survives — match or write cannot be defined without it**

| name | why |
|---|---|
| the rule form | something must know that a rule's members are its two sides, or nothing can hand match a pattern |
| the sign values | a member of the entry, and what the machinery computes with on every read |
| the register | §4 item 3 — a pointer, not a vocabulary item |

**Convention — described in this document and not implemented**

The census counts reserved names, and a name that was never reserved because the convention was never
built does not appear in it. That is a hole in the instrument, so these are listed here rather than
left to be discovered by an author writing the notation this document uses throughout.

| convention | section | status |
|---|---|---|
| the **skeleton** — `where`, named entries, a member's locus | §12 | no surface, and the engine carries the one-locus case only |
| **spans as loci** | §11 | an entry's locus is a moment; no span is ever built as one |
| **shapes** | §13 | follows from the two above — the worked definitions cannot be written |
| **`unless`** | §12 | precedence exists; the other half of defeasibility does not |

⚠ **Nothing in §21's gates can see any of these**, and that is the general lesson rather than an
oversight: the bundle gate deletes each shipped rule and re-runs the suite, so it measures what
exists. **A convention with no rules has none to delete, and reads as passing.**

**Convention — shipped as rules in the bundle**

Seventeen, in one authored file, in an order that is itself a precedence claim a corpus can override.

| group | rules | section |
|---|---|---|
| the boundary | `<intake>`, `<did>`, `<taken>`, `<assert-act>` | §15, §17, §18 |
| denial | `<denial>` — one direction only | §9 |
| callbacks | `<resuming>` | §19 |
| surprise | four deviation rules — two expected signs × two ways to disappoint one | §18 |
| backward reading | `<ask-recall>`, `<ask-fit>`, `<plan>`, `<expand>`, `<ask-check>` | §5, §19 |
| relevance | `<relevant>` — means-ends analysis as data | §19 |
| the verdict | `<give-up>` | §5, §19 |

**Doors and boundaries — machinery, and legitimately so**

| name | direction | why it cannot be a rule |
|---|---|---|
| `arrived`, `utterance` | in | a channel is **anchored** and a rule is generic. Delivery is not a step of the loop: the boundary **calls in**, at the moment the world speaks |
| `doing`, `emitted`, `taken` | out | the same, read the other way: no rule can name the agent's own edge |
| `suppose` | inward | entering a frame **moves the register**, §4 item 3 |
| `adopt` | inward | a rule becoming live is an act, not a verdict (§20) |
| `kb` | — | the channel a derived entry is sourced to |

**Answerers — eight, each bound by a fact**

`<fit>`, `<settle>`, `<verdict>`, `<root>`, `<supported>`, `<composer>`, `<remember>`, `<re-ask>`.
Their bodies are native, which is what an answerer *is*; their **bindings** are claims, so *which of
these exist* is a query. Four carry `standing`, and a denial of those is refused on the record (§19).
The other four are safe to retire by §19's test — their absence is the status quo ante.

⚠ **A corpus tool may not share a request relation with the apparatus**, and this is refused at
registration. `_answer` calls *every* answerer bound to a relation, so a corpus tool and an apparatus
answerer on one request both fire on every such write — the twin trap inverted, two answerers for one
node rather than two nodes for one name, and worse than a twin because a tool **proposes** where the
apparatus **concludes**. Found by the apparatus taking a name a fixture already used, where the two
coexisted only because each declined the other's arity.

**Guards — four, one move**

The norm veto, the widening of a dry shortlist, the recovery of a domain out of mind, and the
open-goal veto. Each runs at one machinery decision and answers one question. **Escalate before
believing a decline.**

### The count

> **Zero phases.** The step is: read `enough` → recall → match → defeat → forgo → quiescence →
> arbitrate → note doubt → apply, plus leaving a frame, waking on quiescence, and the escalations.
> Nothing in it decides anything a rule could have decided.

### What moving them taught

**Splitting a phase shrinks it rather than relocating it.** Intake became the smallest unarguable
record of a boundary event, and *what a report means* became a rule.

**A phase can hide a precedence claim.** Every phase that ran first was asserting that it should, where
nothing could argue. As rules they are merely installed first, so the authored-order tiebreak prefers
them — and a corpus can now say otherwise. Two thirds of this agent's arbitrations are still settled by
that order, which is why the bundle file is worth reading as an argument and not as a list.

**Being machinery never made it a phase.** Crossing the boundary is irreducible; crossing it *on the
agent's schedule* is a claim, and a false one.

**A branch can hide how many claims it was making.** One deviation comparison became four rules, and
the count is the finding: a single comparison had been quietly asserting that *invalidated* disappoints
an expectation exactly as much as *contradicted* does.

**Data rots in a way a branch does not.** Three of those four rules were unexercised, and a rule that
never applies costs nothing, breaks nothing, and looks exactly like a rule that works — which is why
§21's bundle gate deletes each one and re-runs the suite.

**The worst offender was control flow, not vocabulary.** Supposition's phase was three lines of
register work and a nested run of the loop. The names were the easy half.
