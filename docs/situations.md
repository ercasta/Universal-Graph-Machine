# Situations, atoms, and materialising on demand

**Three of the four stages below are built.** Node ids and atom ids are two
identities; interning and both indices are keyed by situation; a supposition
cuts a branch of the graph as well as a successor of the chain, and its
structural conclusions die with it. What is *not* built is materialising a
situation by replaying its deltas, and everything that depends on it —
`?x@S` as a surface form, `reality(S)`/`current(S)`, and resolving at a named
locus. `## What is built, and what stands in for the rest` at the foot of this
file says exactly where the line falls and what the standing-in costs.

Verification is `python -m ugm.selftest`: the `situations()` group, plus two
checks inside `supposing()`.

## The defect this exists to fix

Containment held for entries and failed for structure. Probed *before* this was
built, on a supposition that concludes an ordinary stratum-0 fact inside itself:

    is secret(a) BELIEVED at the root?     None      the entry is contained
    is said(secret(a)) in the graph?       True      the structure is not

An entry carries a locus, so it is situation-relative by construction. A
stratum-0 conclusion is an interned relation instance -- undated, unattributed,
deniable by nothing -- so it belongs to no situation and is visible from every
one. That is not a corner case: negation as failure, counting, and the
rules-as-facts interpreter all run on that layer.

Ancestry could not fix it, because the leak was not in the read. `at_or_after` is
checked when resolving an entry; a structural fact is never resolved, it is
enumerated straight out of the argument index.

The same probe now, on the three-rule fixture in `supposing()`: **106 nodes
minted inside the hypothesis, 0 of them visible to the caller.** Counted rather
than named, because the number is the argument — a supposition of three rules
mints scores of nodes, and the claim has to be about all of them.

## The model

**A situation is a branch. A moment is a commit.** Deltas and inheritance stay
*within* a situation -- silence still means inherit, so the frame problem stays
solved where the agent spends its time. Across situations there is no
inheritance: a situation is materialised.

**Every node has two identities.**

    node id     the realisation of a thing INSIDE one situation
    atom id     the portable name of that thing, ACROSS situations

Every node, not only leaves. The reason is replay: **a delta must reference
atoms, not node ids**, or replaying it into another situation would reference
nodes belonging to the situation it came from. A delta names the relationship
`healthy(paul)` as much as it names `paul`, so the relationship needs an atom
too.

Deriving a compound's atom from its members' atoms is rejected. It makes
identity structural rather than asserted, so two situations that happen to build
the same shape are forced to agree that it is the same relationship, and nothing
holds the correspondence that a rule could ask about or deny.

**Interning becomes per-situation.** The key is `(situation, relation, members)`
rather than `(relation, members)`. Within a situation, the same relationship is
one node; across situations it is two nodes sharing an atom.

**The indices are where this is enforced, not the nodes.** `_by_rel` and
`_by_arg` were global, and the structural walkers enumerate straight out of
them. Distinct nodes alone would not close the leak if the index still spanned
situations, so the index key carries the situation. That is the concrete place
this design lives or dies, and `Graph._bucket` is where it lives.

## Materialising, on demand, like a checkout

> **Not built.** What stands in for it is capped ancestor visibility — a
> situation reads *through* to its ancestors, and each step is capped at the
> node counter as it stood at the cut. Same answer for the structural layer,
> computed on the way past, with no replay and no cache to discard. The one
> thing genuinely lost is that nothing can be discarded either: see the foot of
> this file.

Git stores immutable content-addressed objects and shares the unchanged ones; a
commit points at a tree, a branch points at a commit, and checkout builds the
working tree when asked. Delta compression is a storage detail, not the model.

The same shape here:

    entries are immutable                 they already are
    a situation points at a commit        a moment in a chain of deltas
    materialise when a rule asks          replay the deltas, minting a node
                                          for each atom as it is referenced
    branch                                point a new situation at an existing
                                          commit; its later deltas are its own

**No copy-on-write, and no eager copy.** A situation that nobody asks about
costs nothing but a pointer. One that is asked about is rebuilt from the deltas,
and what the rebuild produces -- the node set and the resolved state -- is a
cache that may be discarded.

**And containment falls out rather than being enforced.** A structural
conclusion is not an entry, so it is not in a delta, so it is never replayed. It
lives in the materialisation and dies with it. `said(secret(a))` derived inside
a hypothetical situation has no way to appear in another one, and no ancestry
test is consulted to keep it out.

## Reading across situations

> **Half built.** `(atom id, situation) -> node id` is `Graph.node_of` and it is
> a lookup, as below. What is *not* built is any way for a rule to write `?x@S`,
> or to name a situation at all — `reality(S)` and `current(S)` do not exist, and
> neither does resolving at a named locus. The paragraph beginning *This is a
> genuine gap* is still true word for word.

    ?x@S        take the atom of ?x, find its node in S

`(atom id, situation) -> node id` is the index that makes it a lookup rather
than a search, and it is the same index materialisation fills in.

`reality(S)` and `current(S)` are ordinary facts, so a rule can name the
situation it is in. Today the seat is a register and nothing can refer to it,
which is why `p@current` would be unwritable.

**This is a genuine gap, not sugar.** Probed: `at ?m` does *not* mean *evaluate
this at m*. It binds the locus of the entry that satisfied the member, and the
resolved state keeps one entry per proposition -- the winner. So a rule can say
*the goblin acted after the hero* (two propositions, two loci) and cannot say
*p held then and does not now* (one proposition, two times), because the earlier
claim is not in the state to be matched. Bound `?then` to a real past moment
where `ill(paul)` held, and `+ill(?x) at ?then` still did not match.

`Chain.resolve(p, locus, seat)` already answers the question. What is missing is
any way for a rule to say **which locus to resolve at**.

## What this costs, stated rather than discovered

**Interning stops being global.** Identity is decided at intake, in a scope --
now in a scope *and* a situation. Every cross-situation reference goes through
the atom index.

> **Superseded by what was built.** Interning did stop being global, as below.
> But there is no rebuild, so the paragraph after this one — and the measurement
> it asks for — no longer decide anything. Left standing because the argument is
> what would be true if the replay were built.

**Rebuild cost is O(the deltas replayed).** Cheap for a situation branched
recently, expensive for one branched near the root and asked about late.
Materialisations are caches, so the policy for keeping them is a real decision
with a measurable cost, and the number to get first is: N walkers in N
situations against N in one.

**Clock arithmetic is not free.** Moments are *ordered*, not *measured* --
`depth` is a position, not a duration. So `timeof(current) - minutes(5)` needs a
`time(M, T)` fact deposited by a clock tool, and `timeof` is then a lookup
rather than a primitive.

## What it buys

Suppositions stop needing frames for containment; situations do it, and they do
it for structure as well as for entries. Speculation and reality become the same
mechanism with different labels. Branching from an arbitrary past commit becomes
ordinary rather than absent. And comparison across situations becomes
expressible, which the probe above shows it currently is not.

## What is built, and what stands in for the rest

Three stages are in the engine. The fourth is not, and the honest thing is to
say what took its place rather than to let the absence read as an oversight.

### Built

| | where |
| --- | --- |
| two identities per node, atoms minted and never derived | `Graph._atom`, `Graph.atom_of` |
| `(atom id, situation) -> node id` | `Graph._node_by_atom`, `Graph.node_of` |
| interning keyed by situation | `Graph._interned`, `Graph._interned_lookup` |
| **both indices keyed by situation** | `Graph._by_rel`, `Graph._by_arg`, `Graph._bucket` |
| a supposition cuts a branch of the graph | `Machine.suppose` |
| the situation register moves with the frame register | `Machine.focus`, one property |
| a conclusion crossing out is transported by atom | `Machine.discharge` → `Graph.carry` |
| branching from an arbitrary past commit | `Graph.branch(born=…)`, `Moment.watermark` |

### Capped ancestor visibility, instead of replay

A situation is not rebuilt from its deltas. It reads **through** to its
ancestors, and each step of that walk is capped at the node counter as it stood
when the cut was made. An ancestor node minted after the cut is a later commit
on another branch and is not in this one.

This is what replay would have produced for the structural layer, computed on
the way past. It meets *no copy-on-write and no eager copy* more literally than
replay does — a situation nobody asks about costs a parent pointer and an
integer — and it deletes the cost the design flagged as needing a number first:
**rebuild is not O(the deltas replayed)**, it is a dict get per ancestor, cached
against the own bucket's length because every ancestor's visible half is frozen
by the cap. So *N walkers in N situations against N in one* is no longer the
measurement that decides anything, and the suite runs in the same 7 seconds it
did before situations existed.

What is genuinely given up: **the graph is not reconstructible from the deltas,
so a materialisation cannot be discarded.** Nodes minted inside a hypothesis
live as long as the graph does. That is a leak of memory and not of
containment — nothing can *see* them — but a long-running agent that supposes
constantly accumulates them, and the fix is the replay this stands in for.

### Deltas still reference node ids

The design's reason for atoms is replay: *a delta must reference atoms, not node
ids*. With no replay there is nothing yet to fail, and `Chain.deposit` still
records nodes. The atom layer is built underneath it and is exercised at the one
place a node genuinely crosses a boundary — `carry`, at discharge.

### Two things the caller can still see, and both are consequences

**Whatever it deliberately carried out.** `likely(q)` names `q`, so a caller
holding a crossed conclusion has `q` in its own situation. That node is *minted
there by `carry`*, not the hypothesis's node leaking; but a rule at the caller
that counts or negates-as-failure over `q`'s shape will find it. This is §16's
re-wrap, not a hole — the caller is talking about `q`, and a wrapper containing
its content is what a wrapper is.

**Provenance.** `rests_on(<crossed>, <inside>)` is minted at the caller and
names an entry node inside the discharged hypothesis, because `trail()` has to
reach it — *why do you believe that* is load-bearing for soundness (§12), and an
answer that stopped at the frame boundary would be the untraceability §20
complains about, restored. So support crosses where belief does not. That is
deliberate and it is the one asymmetry in the containment claim.

### And the correspondence is many-to-one at a landing site

`carry` re-interns in the target, because *within a situation the same
relationship is one node* is the design's own rule and a carry that minted
unconditionally would split the target's identity for anything it already had.
So a carried thing may land on a node whose own atom differs, and `node_of`
answers *where did this thing go* rather than *what is this node's only name*.

What that preserves is the reason the design rejected derived atoms in the first
place: the correspondence exists **only where a carry created it**, so two
situations that never exchanged anything are still never forced to agree about a
shape they both happen to build. `situations()` checks exactly that pair — two
siblings building `on(b, c)` get two nodes with two atoms, and the correspondence
appears when, and only when, one is carried into the other.

### Not built

`?x@S` as a surface form a rule can write; `reality(S)` and `current(S)` as
ordinary facts; and *which locus to resolve at*. The last is the genuine gap the
design identified and it is untouched: `Chain.resolve(p, locus, seat)` still
answers the question, and there is still no way for a rule to say which locus to
put it about. `at ?m` binds the locus of the entry that satisfied the member, not
the moment to evaluate at — so *p held then and does not now* remains
unwritable. Clock arithmetic is likewise unchanged: `Chain.TIME` is deposited
when the clock is on, and `timeof` would be a lookup over it rather than a
primitive.
