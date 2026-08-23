# The scratchpad

There is one graph and it is the state.

That sentence is the whole architecture, and it replaced one that took a
module of its own to say. Belief used to live in a CHAIN: an append-only
history of moments, each holding a delta of signed entries, and `resolve`
computed a view over it -- *the last claim about this proposition wins*.
`holds(p)` asked the chain, and the chain answered by walking.

Now the graph holds belief, and the question is presence:

    boiling($w)              structure. A rule's stored pattern. Never believed.
    believed(boiling(k))     a node. Present = believed. Absent = not.

## Why the anchor, and not the proposition

A proposition on its own cannot mean belief, and the reason is §14. The graph
is full of propositions nothing asserts: every rule's stored patterns are in
it, and so is everything any claim merely mentions. If presence of `p` meant
belief in `p`, a rule would match its own antecedent.

The anchor makes the use/mention distinction STRUCTURAL rather than recorded.
USE is anchored; MENTION is not. `Entry.mention` was a boolean the writer had
to get right, and the writer that got it wrong wrote a fact nobody could tell
from a description.

The anchor is INTERNED, so a proposition has at most one, and asserting
something already believed is not a second act -- there is nowhere for a second
act to go. That is what made `Chain.deposit` need `instance` rather than `rel`:
two claims about one proposition were two events, because a chain is a record
of events. A scratchpad is not a record of anything.

## What falls out

    assert     mint the anchor
    retract    DELETE the anchor. `p` survives as structure, which is correct --
               rules mention it -- and the state is back where it started, with
               no scar and no un-claim primitive.
    deny       `believed(not(p))`, a DIFFERENT node. Both can be absent, and
               that is ignorance.
    ignorance  absence. *Never considered* and *considered and dropped* are the
               same state.

The signs went with the entry, and that is a reduction rather than a loss. `?`
existed because absence was AMBIGUOUS in an append-only chain -- never
considered, or not yet derived? -- so ignorance had to be written down to be
distinguishable from silence. Nothing here disambiguates, because nothing here
remembers: absence is ignorance, and there is no third thing for a mark to say.

`-` survives only in a CONSEQUENT, where it erases. There is no `-` premise,
because there is no denying entry to find, and a corpus that writes one is
REFUSED rather than read as one of the two things it might have meant: `no p`
(nothing anchors it) or `+not(p)` (something anchors its denial). Guessing
would turn a migration into a silent change of meaning, and the two readings
are opposites.

## Deletion: the one thing to get right

Only an ANCHOR is ever a safe deletion target.

`Graph.delete` does no repoint and no cascade. `merge` had to repoint --
*without it, everything said before the merge is LOST* -- because a merged node
still means something, and a deleted one does not. Anything still naming a
deleted node is left dangling on the argument that **no rule matches an
incomplete subgraph**: a premise that needs it fails to bind, so the dangling
half is unreachable rather than wrong.

That argument was verified for one shape -- the matched proposition is gone, so
the premise fails -- and NOT for the shape where a surviving proposition
mentions a gone thing. Deleting an individual hides nothing: nothing removes a
node from the buckets of the nodes that name it, so the rule still fires and
the fact still reads. Hence the rule, and it is not a style preference: delete
anchors, never propositions, never entities.

## What this costs

**Quiescence is observed rather than predicted.** The engine used to compute,
per candidate, whether applying it would change anything, and cache the
verdict. That was a second implementation of what applying does, and it had to
be held equal to the first. Now an application is applied, and then marked
inert -- because whatever it concluded is in its target state now, since
putting it there is what applying was. `_revive` un-marks it when any of those
propositions moves, so quiescence is not a one-way door.

**Negation-as-failure is order-sensitive.** `no p` is asked of the state as it
stands. The stratification pass that computed an order in which every negation
was safe -- and refused a corpus that had none -- belonged to the second
matcher, which read the chain's skeleton. It went with it. A corpus whose
absence check can be falsified by another rule must author that rule ABOVE it;
`rules/delay.ugm` says so in its own comment, and it is measured rather than
supposed.

**A corpus can oscillate.** An assert and an erase that answer each other never
settle: each move really does undo the other, and nothing remembers that it has
happened before. Under a chain the second claim merely outvoted the first and
the pair went quiet. The loop's bound is what ends it, and a corpus that wants
to stop has to say so.
