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
| composable | ❌ | — | ✅ | ✅ |

⚠⚠⚠ **(ii) is the canonical leak, and it is worth keeping in mind because it looks harmless.** With a
shared middle node, `a --> on --> b` and `c --> on --> d` put the path `a --> on --> d` in the graph.
Nobody asserted that `a` is on `d`. Two unrelated facts sharing a node composed into a third, which is
precisely *information the facts did not license*.

**(i) fails on lossy, not on leaking** — a labelled edge is not a thing, so there is nothing to date,
nothing to hang a cause on, and nothing to retract in a frame.

### ✅ The decision: (iii), the per-fact 2-hop path

⚠ **With its cost recorded rather than argued away: the participants are versioned.** `a` gains an
outgoing edge when a relation about it forms, so under sparse frames a change to any relation about `a`
mints a version of `a`. (iv) avoids that and pays for it on every read instead. The choice was taken
knowing this.

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
