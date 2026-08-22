# `core/chain.py` — the argument

Moved out of the module so the code reads as code. Nothing here is required to
work on `chain.py`; it is the record of *why*, and the module carries a one-line
pointer at each place it applies.

## Module overview

Moments (§4) and entries (§5), and the walk that reads them.

A moment is a signed delta, a predecessor and a licence. A proposition claims
nothing; the claim is a separate node, the entry, with exactly three members --
locus, proposition, sign.

An entry carries two times, and keeping them apart is the whole of §4's second
half:

    locus       what the claim is about
    deposit     the moment whose delta it sits in -- when the claim was made

In the common case they coincide. They come apart when the agent learns
something about a time that has already passed, which is what makes belief
revision ordinary rather than a second mechanism.

## There is no closed set of grades

`GRADES` was five names in Python — unknown, unlikely, possible, likely, certain
— with an ordinal `weaker` composing them by weakest link on every write. It was
deleted. What replaces it is `likely(p)`: an ordinary proposition, crossed into a
supposition by an ordinary rule, coming back out wrapped. A corpus may now have
whatever modalities it likes, with whatever ordering it authors, so §10's
*closed is a rate, not a kind* holds one place further.

Measured three ways before deleting. `ugm.probes.modality` already ranked the
grade last of three treatments — **not a term, so no rule can ask about it; no
guard to cross; does not nest**. The suite authored one in **4 of 3,740 rules**
and carried one on **6 of 32,289 entries**. And `weaker` was called from exactly
one place: the grade was carried, composed and printed, and **nothing ever
decided on it** — this repo's own *read and not obeyed* defect at the floor.

 What was lost: weakest link was AUTOMATIC and TOTAL. A conclusion drawn from
an uncertain premise is now derived only if a corpus crossed, and what comes out
is nested (`likely(possible(x))`) where `min` gave one ordinal. Collapsing that
is a corpus's table and its ordering is a corpus's claim. The ordinal stops being
free and starts being arguable.

## `Moment.watermark`

Where the structural world stood when the moment was made — the node counter,
the only monotone thing the graph has, and therefore the only thing a
situation's cut can be expressed in (`docs/situations.md`). A moment is a commit;
this is what makes *branch from that commit* something a caller can ask for
rather than something the design merely claims.

Nothing in the loop reads it. It is recorded at the moment's birth because
recording it at only one of the two sites a moment is born would give the chain
a hole in its watermarks that nothing reports.

## `Entry.atom` — the delta's own reference, in the portable identity

`docs/situations.md`: *a delta must reference atoms, not node ids*. Every other
field names a node, and a node belongs to one situation, so a delta made of nodes
can only be replayed into the situation it came from — which is not a replay.

 It is redundant with `g.atom_of(proposition)` **today**, and that is the point
rather than an objection: it stops being redundant the moment a materialisation
is discarded, which is the leak that stage exists to close. `Chain.materialise`
reads THIS and never `atom_of`, so the redundancy is under test rather than
asserted.

## The wall clock is off by default

A stamp is STRUCTURAL, like `pred` — not an entry — so switching the clock on
leaves the entries of two runs byte-identical and only the stamps differ.
`ugm.probes.dungeon`'s *the same seed replays the same fight, entry for entry* is
untouched.

What does diverge is a corpus that READS the clock: its conclusions are entries
and carry a number that was different last time. So the clock is inert until
asked for, and off by default, because a source of nondeterminism should be
requested rather than inherited.

 What it is NOT: a way to order moments. `pred` and `anc` already do that, and
they are exact where a clock is only monotone-ish. The stamp answers *how long
ago*, which the chain could not answer at all — moments are ORDERED, not
MEASURED, and `depth` is a position rather than a duration.

## `asking(<seat>)` — the question, as a skeleton fact

It is what the read is anchored ON, and it is the difference between a read and
an enumeration of the history. Every other member of the read's rules walks or
looks up from something already bound; this is what binds the first one.

Skeleton by the same test as the rest: nobody asserted it, it cannot be denied,
dated or attributed, and it says how the graph is being read rather than anything
about the world. The machinery seeds it; §6's price applies exactly as to `cand`
and `best`.

 Without it the read's first member is unanchored, and the only way to bind a
seat is to enumerate every moment — which is what the second matcher did, and why
it was *deliberately slow*: it derived the read for every seat in the history
whether or not anything asked.

## `resolve` — two orderings, as one comparison

    latest locus first    the most recent claim about the world wins, which is
                          what makes silence mean *inherit*
    latest deposit next   among claims about the same time, the agent's current
                          view wins over what it used to think

Both are needed. Locus alone cannot tell a revision from the original; deposit
alone would let an old belief about a late moment be overruled by a new belief
about an early one.

The old loop went newest-moment-first and newest-within-a-moment-first and
replaced `best` only on a strictly later locus — so the winner was the entry with
the greatest `(locus depth, seat depth, position)`, which is what is computed
now. Containment still costs an ancestry test: a depth comparison cannot replace
it once anything forks, and supposing forks by construction.
