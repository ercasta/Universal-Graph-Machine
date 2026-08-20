# `core/graph.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

The substrate of §3: nodes, directed edges, ordered members. Nothing else.

Edges carry no information beyond connecting, so anything you want to say about a
connection has to be a node. A relation instance -- what would elsewhere be a
labelled edge -- is therefore a node with a relation and ordered members:

    on(a, b)        a node whose relation is `on` and whose members are a, b

Ordering is the one thing that is not itself structure (§3), which is why the
substrate provides it natively and provides nothing else.

Determinism: no derived result is ever read out of a set. Membership, minting
order and every iteration below are insertion-ordered, so a computation that ends
in a tie breaks it the same way on every run.

⭐⭐⭐ **And a node has two identities (`docs/situations.md`).**

    node id     the realisation of a thing INSIDE one situation
    atom id     the portable name of that thing, ACROSS situations

The defect this exists to fix is that containment held for entries and failed for
structure. An entry carries a locus, so it is situation-relative by construction;
a stratum-0 conclusion was an interned relation instance -- undated, unattributed,
deniable by nothing -- so it belonged to no situation and was visible from every
one. Probed, on a supposition concluding an ordinary fact inside itself:

    is secret(a) BELIEVED at the root?     None      the entry is contained
    is said(secret(a)) in the graph?       True      the structure was not

Ancestry could not fix it, because the leak was not in the read: `at_or_after` is
checked when resolving an entry, and a structural fact is never resolved -- it is
enumerated straight out of the argument index. **So the indices are where this is
enforced, and not the nodes.** `_interned`, `_by_rel` and `_by_arg` are keyed by
situation below, and that is the concrete place the design lives or dies.

## Whether a node is generic, decided at MINT r

⭐⭐⭐ Whether a node is generic, decided at MINT rather than on every
ask. It cannot change: a node's relation and members are fixed when it
is built, so *contains a variable somewhere* is fixed with them.

Profiled, and it was not a small share: `has_var` was **91% of the
rule-level read** -- 7.6M calls recursing the whole structure each
time, because the structural generators ask it of every instance in a
bucket on every enumeration. Computing it here is O(arity) once
instead of O(size) per question.

## Members that fell off the index, counted b

⭐ **Members that fell off the index**, counted by the member as
written -- `docs/interpretation-feedback.md` §3. `_narrowed` cannot
index a structure that still carries a variable, so it falls back to
every instance of the relation: correct, sanctioned, and until now
invisible. An instrument, not a fact -- nothing reads this but a
`Report`, and no rule can match on it.

`member as written -> [times it fell back, nodes those scans visited]`.

## -- situations (docs/situations.md) -----------

-- situations (`docs/situations.md`) ----------------------------

**A situation is a branch. A moment is a commit.** Deltas and
inheritance stay *within* a situation -- silence still means inherit,
so the frame problem stays solved where the agent spends its time.
What changes here is the STRUCTURAL layer: a node is minted into a
situation, and a situation sees its own nodes plus its ancestors' --
never a sibling's, and never a descendant's.

⚠ **Ancestor visibility is CAPPED, and the cap is what makes this a
branch rather than a window onto a moving parent.** A situation
records the node counter as it stood when it was cut; an ancestor node
minted after that is a later commit on another branch and is not in
this one. Without the cap a supposition would see the world change
under it while it reasoned, which is precisely the containment this
file exists to give.

The cap composes down a chain by `min`, and because a child is always
cut after its parent the `min` is just the nearest branch point on the
path -- see `_visible`.

## -- atoms ---------------------------------------

-- atoms --------------------------------------------------------

Every node, not only leaves. The reason is replay: a delta must
reference atoms rather than node ids, or replaying it into another
situation would reference nodes belonging to the situation it came
from -- and a delta names the relationship `healthy(paul)` as much as
it names `paul`.

⚠ **An atom is minted, never derived from the members' atoms.**
Deriving it would make identity structural rather than asserted, so
two situations that happened to build the same shape would be forced
to agree that it is the same relationship, with nothing holding the
correspondence that a rule could ask about or deny. Correspondence is
established by an ACT -- `carry` -- and by nothing else.

## -- identity (coreference within a situation) ---

-- identity (coreference within a situation) --------------------

⭐⭐⭐ **The third identity, and it is the one that can be decided
LATE.** A node is the realisation, an atom is the portable name, and
neither can express *these two turned out to be the same thing*.
Today identity is settled by construction and never inferred -- the
loader's name table decides it at intake, interning decides it for
compounds -- so two nodes are one node or they are unrelated, and
there is no third state. This is the third state.

⚠ **Leaves only, and the default is the node itself.** A compound's
identity is not stored because it is DERIVED: interning keys on the
identities of the relation and members, so the canonical node *is* the
derived identity. That is the exact opposite of the atom rule one
block up, and the asymmetry is load-bearing:

    atom      minted, never derived -- correspondence is an ACT, so a
              rule can deny that two situations mean one relationship
    identity  derived for compounds -- congruence IS the feature: if
              `a` and `b` are one thing then so are `f(a)` and `f(b)`

One id cannot be both minted and derived, which is why this is a third
id rather than a reading of the second.

⚠⚠ **An unmerged corpus pays nothing.** With no entry here every
lookup returns the node it was given, so the interning key is
byte-identical to what it was before identity existed. That is the
same discipline `count` is held to: nothing that never corefers pays.
⚠⚠⚠ **AND IT SUPERSEDES THE ATOM LAYER ABOVE -- next commit.** The
author's argument, and it is right: branching is a COPY, so two nodes
with one identity in two branches are one thing, which is the whole of
what an atom does. The objection this file records one block up --
*two situations that happened to build the same shape would be forced
to agree* -- assumes COINCIDENCE, and under branching there is none:
anything two branches share they share by DESCENT, so deriving the
same compound identity means they were built from the same parts and
genuinely are the same relationship. Independently minted things have
different identities and are not forced together.

And the clincher is structural rather than philosophical: a derived
compound identity IS `(identity of relation, identities of members)`,
so it describes its own structure -- which is exactly what
`_atom_members` was added for, and makes that table redundant.
`rebuild` can recurse on the identity term itself.

Landed beside the atom layer rather than instead of it so this commit
stays green and bisectable; the collapse is its own change.

## ...and a third, over the same instances by WHAT

...and a third, over the same instances by WHAT SITS IN EACH ARGUMENT
POSITION. `_by_rel` answers *every `delta_next`*; this answers *every
`delta_next` whose first argument is this entry*, which is what a
matcher with one argument already bound actually wants.

The entry side took this index once already -- an option set weighed
by scanning was 2,006,004 unifications and 3,003 after -- and the
structural side never did, because until §7 stopped hiding two thirds
of the chain from the matcher there was nothing here big enough to
notice. Profiled the hour it became visible: `cand` went 193 -> 2,062
in one fixture, and `<beaten-locus>` joining `cand` against `cand` by
scanning was 4.4M unifications in 60 seconds, which is 2,062 squared.

Insertion-ordered like the others, so nothing downstream inherits a
tie-break from a hash.

## `merge`

`drop` counts as `keep` from here on, in `s`. Returns nodes repointed.

        ⭐⭐⭐ **Congruence, and it is why this cannot be two dict writes.** Once
        two things are one thing, every relationship either of them stands in is
        a relationship of the one thing -- so `bright(morning)` and
        `bright(evening)` have to become one node too, and so does anything
        built on THOSE. Merging two leaves therefore induces merges all the way
        up, and the worklist below is that cascade.

        ⚠⚠⚠ **Without the repoint, everything said before the merge is LOST.**
        `bright(morning)` was interned under a key naming morning's identity;
        after the merge `rel(bright, morning)` computes a key naming the new
        one, finds nothing, and mints a third node while the original sits
        unreachable in the index. Not a leak of containment -- a silent loss of
        what the agent already believed, which is worse, because nothing reports
        it. This is the whole of what makes identity a change to the INDICES
        rather than a field on a node.

        ⚠ **Per situation, so a merge inside a hypothesis dies with it.**
        Deciding two things are the same is a decision, and a decision made
        while supposing is not a decision about the world.

        ⚠ It does NOT decide anything: the caller supplies the pair, and the
        caller is a rule concluding `same(a, b)`. `deposit-dont-decide.md` --
        the engine may compute the consequence, never make the choice.

## `rebuild`

Materialise the thing `a` names, in `target`, **from atoms alone**.

        This is what `docs/situations.md` means by *a situation is materialised*
        and it is the half stage 4 exists to build. `carry` transports a node
        that still exists; this reconstructs one from the portable record, so it
        works for a situation whose nodes were never minted or were discarded.

        ⭐ **It reads `_atom_members` and never `_members`**, which is the whole
        test of whether the atom layer is real. If this function needed a node
        to consult, atoms would be labels on a structure rather than a structure
        of their own, and nothing could ever be thrown away.

        ⚠ **Already-there wins, by the visibility walk.** If `target` can
        already see a realisation of `a`, that one is the answer -- rebuilding
        beside it would put two nodes for one thing in one situation, which is
        the twin trap wearing a replay. That is also what makes this idempotent,
        and what lets it be checked against capped visibility: rebuilding
        something a situation can already reach must be a no-op.

        ⚠ A variable rebuilds as a variable. `_is_var` is not derivable from the
        structure -- a bare variable has no relation and no members, exactly like
        an atom -- so it is carried across explicitly. Without this a replayed
        rule's members turn into ground atoms named `?x` and match nothing.

## `carry`

Transport a node into `target`, and RECORD that it landed there.

        This is what a delta referencing atoms buys, arriving one construct at a
        time instead of as a replay: a conclusion drawn inside a supposition is
        built out of that situation's nodes, and re-stating it at the caller's
        seat has to re-state it in the caller's situation or the caller's own
        indices would carry a reference to something it cannot see.

        ⚠ **Structure decides identity WITHIN the target, and the atom index
        records where the carried thing landed.** Those are two different
        claims and both are needed. The first is `docs/situations.md`'s own
        rule -- *within a situation, the same relationship is one node* -- so a
        carry that minted unconditionally would split the target's identity for
        anything it already had. The second is what keeps the design's rejection
        of structural identity honest: the correspondence exists only where a
        carry created it, so two situations that never exchanged anything are
        still never forced to agree about a shape they both happen to build.

        The consequence, stated rather than discovered: the map from atoms to
        nodes in a situation is many-to-one at a landing site. `node_of` answers
        *where did this thing go*, not *what is this node's only name*.

## The same structure again, one level up, in

⭐⭐⭐ **The same structure again, one level up, in atoms** -- and it is
the floor stage 4 stands on. A delta referencing atoms can name
`healthy(paul)`, and naming it is not enough to REBUILD it: a
compound's atom is minted and deliberately not derived from its
members', so the atom alone says nothing about what it is made of.
Without this table an atom is a name for a node that has to still
exist, which is the thing replay is for getting rid of.

⚠ Kept beside `_members` rather than replacing it. `_members` is per
NODE and is what every reader walks; this is per ATOM and is what
survives the node being discarded. They are the same shape and they
answer different questions -- which is the whole of why there are two
identities in the first place.
