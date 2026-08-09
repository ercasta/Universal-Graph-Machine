# Harmony — the standing criteria a representation decision is scored against

**Every representation decision in this project gets scored against the four criteria below, in a
table, before it is taken.** Not as ceremony: three decisions in the edges-as-nodes arc came out
differently once they were scored, and one encoding that looked obviously right turned out to leak.

## The name

**Harmony**, in Gentzen's inversion principle, sharpened by Prawitz into *local soundness* and *local
completeness*, and named by Dummett in *The Logical Basis of Metaphysics*: a connective's elimination
rules may extract no more than its introduction rules put in, and no less.

Read here as: **what you get out of a structure is exactly what was put into it.** Introduction is
whatever asserts or writes; elimination is whatever reads, traverses or derives.

⚠ **Borrow the fact, refuse the criterion.** Harmony pays off in logic as a *proof* — conservativity
via cut-elimination. This project has never been in the guarantees business, and nothing here is
rejected for failing to offer one. What harmony gives us is a **checklist with a sharp definition of
each entry**, plus one entry that turned out to be mechanically auditable.

## The four criteria

| | question | failure looks like |
|---|---|---|
| **not leaking** | does composition yield only what was licensed? | a derivation with no premise — traversal inventing facts |
| **not lossy** | can you recover everything that was asserted? | *when did this become true* is unaskable |
| **readable** | can a **rule** ask for it, not just Python? | the information exists and only the engine can reach it |
| **composable** | can another operation consume the result? | an island — a category that relates to nothing |

**Leaking is local soundness; lossy is local completeness.** The other two are this project's own, and
they are why the logician's version is not enough here: a representation can be perfectly harmonious
and still be unreachable from a rule, which in this engine is the same as not existing.

## ⭐⭐⭐ Expressiveness is PRIOR to the table, not a fifth row

All four criteria are **internal**: given that you said it, does the machinery behave? None of them asks
whether you can say it at all. That is requirement 1 of
[expressiveness-and-uniformity.md](expressiveness-and-uniformity.md), and its test is different in kind —
not *is there a mechanism* but **write the sentence**.

> **A representation can be perfectly harmonious about nothing.**

A graph language with no ordering is lossless, leak-free, readable and composable — about everything it
can say. So expressiveness is not a fifth criterion; **you cannot score harmony on a sentence you cannot
write**, and the two passes are separate:

| | test | when |
|---|---|---|
| **expressiveness** | *write the sentence* | first, per category. Fails locally, needs no machinery |
| **harmony** | the four criteria above | on what survived |

⚠ **Do not merge them into one notion of "completeness."** Two live cases show the criteria doing
different work: `not(p)` as a hub and `or(p, q)` as a hub both become **sayable** the moment relations
are nodes, and both still fail — `not` on *composable* (it does not compose with the frame chain; see
[facts-as-nodes.md](facts-as-nodes.md) §*Frames*) and disjunction on *composable* too, since nothing can
consume it. Merged, both would read as solved by the conversion, and neither is.

⭐ Known-negative controls are free and should be used, because a pass that finds no gaps and a pass that
cannot see gaps report the same thing: **can a rule get from a plan step's position to a moment?** —
today, no. And `step[i+1]`, unsayable because `path.Hop.index` is a literal. Any expressiveness
instrument that reports those green is broken rather than encouraging.

⭐ Across two independently authored KBs, *not leaking* has a name of its own — **conservative
extension**: `A ∪ B` proves nothing new in `A`'s vocabulary. Local soundness and conservativity are the
same idea at two scales, and the second is the cross-domain composition feature.

## How to use it

Score the candidates in a table. One row per criterion, one column per candidate, and **write the cost
down even when the choice is obvious** — the recorded cost is what stops the next session
rediscovering it as a surprise.

## The worked example: `a on b`

Four encodings, in nodes and edges, because predicate notation hides the question.

```
(i)   a --on--> b                          a labelled edge (what the engine has today)
(ii)  a --> on --> b                       a 2-hop path through a SHARED predicate node
(iii) a --> on#7 --> b   on#7 --is--> on   a 2-hop path through a PER-FACT node
(iv)  on#7 --at--> a, b  on#7 --is--> on   a hub pointing at its participants
```

| | (i) edge | (ii) shared middle | (iii) per-fact path | (iv) hub |
|---|---|---|---|---|
| not leaking | ✅ | ❌ | ✅ | ✅ |
| not lossy | ❌ | ✅ | ✅ | ✅ |
| readable | ✅ keyed lookup | ✅ | ✅ two hops | ⚠ reverse index + position filter |
| composable | ❌ | — | ⚠ **nests badly** — see below | ✅ **nests, at any depth** |

⚠⚠⚠ **(ii) is the canonical leak, and it is worth keeping in mind because it looks harmless.** With a
shared middle node, `a --> on --> b` and `c --> on --> d` put the path `a --> on --> d` in the graph.
Nobody asserted that `a` is on `d`. Two unrelated facts sharing a node composed into a third, which is
precisely *information the facts did not license*.

**(i) fails on lossy, not on leaking** — a labelled edge is not a thing, so there is nothing to date,
nothing to hang a cause on, and nothing to retract in a frame.

### ✅ The decision: (iv), the hub

**A per-fact node, one edge to the relation concept, and positional edges to the members.** Read as
`on(a, b)`; see *Notation* below.

⚠⚠⚠ **This table first recorded (iii), and the flip is the clearest instance of the criteria working —
so the reason is recorded rather than the row quietly rewritten.** The two were scored ✅/✅ on
*composable*, which was where the deciding property lived and it was never spent: **nested
reification.** Under (iv) a member may itself be a hub with no new shape —

```
f1 = on(a, b)
c1 = claimed(f1, anna)          a fact about a fact, same construct
```

— so *being pointed at is being a member*, uniformly and at every depth, which is what makes *one
construct, not a family* true rather than aspirational. Under (iii) the fact node is pointed at both by
an **entity** (its subject) and by **metadata** about it, so the direction invariant — *a goal points at
the world and is never pointed at by it* — stops being able to tell world from metadata by direction,
which is the invariant hypothesis isolation rests on.

⚠ **The cost, recorded rather than argued away: reads become a reverse lookup plus a position filter**
where (iii) had a keyed forward walk, and pattern matching becomes a join. The lever is a maintained
index above the horizon (`workbench.index` verbatim), and the evidence that it suffices is measured
rather than assumed — see [facts-as-nodes.md](facts-as-nodes.md) §*Pattern matching becomes a join*.
⚠ What (iv) buys back is on the write side: **a relation forming does not touch its participants**, so
a frame's delta grows by exactly one node per change, where (iii) mints a version of every participant.

## Notation

Two forms, and the second is only for sections that are really about storage.

**Reading form** — a bound name, the relation, positional members. Node ids appear only where identity
matters.

```
f1 = on(a, b)
c1 = claimed(f1, anna)
     attribute(a, red, 1.0)
```

**Storage form** —

```
#7 --is--> on        the relation concept, a shared node
#7 --at--> a         position 0    ordinal along one label, so position costs nothing
#7 --at--> b         position 1
```

⚠ The section above says *predicate notation hides the question*, and it did while four encodings were
live: `on(a, b)` is equally true of all four. **It is safe now for exactly that reason** — once the
encoding is settled the reading form hides nothing, and the storage form stays for the arguments that
turn on edges.

## What composability buys, concretely

Once a relation is a node, **the relation's own algebra is data**. `then --is--> transitive` is an
assertable fact, so a derivation that walks a chain has a *premise to cite*:

> *A is before C because of these turn nodes, and because `then` is transitive, which Anna declared.*

Under (i), transitivity can only live in Python — where the residue cannot cite it, and where walking
the chain and inventing the conclusion are indistinguishable. **That is a leak that becomes visible
only after the representation improves**, which is the argument for scoring encodings rather than
mechanisms.

## What is mechanized, and what is still judgement

✅ **Not leaking, for the frame construct: `python -m ugm.leak`.** Frames are Memento — they store the
transformation (`via` / `applies` / `ran` / `assumes`) alongside the delta. The two must agree, so:

> **Every entry in a frame's delta must be attributable to that frame's transformation.**

Containment form, green over a full Sussman search, with a planted-leak control and a reported *slack*
figure (currently 2.0×) that says how loose the net is — because a containment satisfied by an
over-broad licence is a green light that means nothing.

⚠ **Lossy, readable and composable are judgement calls today.** *Readable* has the nearest thing to an
instrument in `reach.py` (asked of representations rather than of code: does saying this introduce a
name nothing else reaches?), and *composable* has the derived coverage pass that
[expressiveness-and-uniformity.md](expressiveness-and-uniformity.md) §8 specifies and nobody has built.

⚠ **And the behavioural rule still governs all four**: the test is never *can the representation
distinguish these* — that is a theorem prover's question — but **would the agent act differently**. A
distinction nothing acts on is bought and never spent.

See [expressiveness-and-uniformity.md](expressiveness-and-uniformity.md) for the requirements this
serves, and `ugm/fact.py` for the wrapper the decision is being executed behind.
