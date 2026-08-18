# Situations, atoms, and materialising on demand

A design, not a description of what is built. What is built is described only
where it motivates a decision or contradicts one.

## The defect this exists to fix

Containment today holds for entries and fails for structure. Probed, on a
supposition that concludes an ordinary stratum-0 fact inside itself:

    is secret(a) BELIEVED at the root?     None      the entry is contained
    is said(secret(a)) in the graph?       True      the structure is not

An entry carries a locus, so it is situation-relative by construction. A
stratum-0 conclusion is an interned relation instance -- undated, unattributed,
deniable by nothing -- so it belongs to no situation and is visible from every
one. That is not a corner case: negation as failure, counting, and the
rules-as-facts interpreter all run on that layer.

Ancestry cannot fix it, because the leak is not in the read. `at_or_after` is
checked when resolving an entry; a structural fact is never resolved, it is
enumerated straight out of the argument index.

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
`_by_arg` are global today, and the structural walkers enumerate straight out of
them. Distinct nodes alone would not close the leak if the index still spanned
situations, so the index key carries the situation. That is the concrete place
this design lives or dies.

## Materialising, on demand, like a checkout

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
