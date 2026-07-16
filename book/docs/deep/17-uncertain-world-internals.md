# Shades of maybe: the machinery

!!! note "Still on the bonus floor"
    Like the rest of Part 4, nothing here changes how you *use* the machine —
    [Living in an uncertain world](../advanced/10-uncertain-world.md) already gave you
    the whole idea. This chapter is for the reader who asked, "a *likely* — yes, but
    how, **really**?" The surprising answer: the machine barely needed new parts.

A machine that can say **likely** sounds like it must carry probabilities and do
arithmetic on them. This one doesn't — and deliberately so (Chapter 16's closed
list of ways-to-think has no "probability loop" in it, on purpose). What it does
instead is reuse two things it already had: the **pencil worlds** of Supposing
(Chapter 9) and the **degree** that matching already carries. Put them together and
"likely" falls out almost for free.

## A "likely" is a pencil world with a label

When you say *cy is likely nervous*, the machine does exactly what a supposition
does — it opens a **pencil world** holding *cy is nervous* — and then pins one
extra thing to it: a **band**, its likeliness. The band is a rung on a small scale
(*very likely, likely, unlikely, very unlikely*), read **ordinally** — the machine
only ever *compares* bands, never multiplies them. There's no probability being
computed, just a shade of maybe being remembered.

Because the possibility lives in pencil, everything from Chapter 9 comes along: it's
invisible to the machine's ordinary "what do I actually believe" reads, it can't
pollute the ink, and a whole fistful of these worlds can sit side by side.

## Reading through the fog

Now, how does a *likely* fact get *used*? Here's the neat part. The match phase
(Chapter 15 — *find, follow, check*) already carries a running **score** as it
walks: the graded layer uses it to match "how *urgent*?" rather than a plain
yes/no. Reading a possibility rides that same rail.

There's one new looking-verb, a graded twin of the "in focus?" check:

- **by likeliness** (`OVERLAY_BAND`) — when the walk steps through a pencil world's
  fact, keep going, but **dim the running score** to that world's band.

And here's why nothing else was needed: the score composes by taking the **smaller**
of what it already had and each new dimming — a *minimum*. So a chain that passes
through a *likely* (say 0.6) world and then a *very likely* (0.8) one comes out at
0.6: the **weakest link**, exactly the "doubt travels" rule from the last chapter,
falling straight out of how the score was always combined. Ink facts don't dim
anything, so a path over solid ground stays **certain**. And when the same
conclusion can be reached two ways, the machine keeps the **better** one — the
*best of the weakest-links* — which is just "take the strongest available reason."

## The dial is an α-cut

The cautious/decisive knob from the last chapter has a precise meaning down here. A
`not P` used to be pure [negation-as-failure](../appendix/index.md#negation-as-failure):
*look for P, and if you don't find it, conclude not-P.* With possibilities in play,
"find it" becomes a matter of degree, so the machine draws a line — a **threshold**,
θ:

> Block `not P` only if P is reachable at a band **at or above θ**.

Turn θ **up** and the machine ignores faint possibilities and jumps boldly (it
accuses cy over the shaky alibi). Turn θ **down** and it refuses to lean on any
absence while the opposite is even slightly possible (it holds back). The bias isn't hidden in the
code; it's this one number, out where you can set it.

## A conclusion wears its doubt

When the machine *does* fire a rule that leaned on *not P*, how sure should the
conclusion be? Only as sure as P really is **un**likely. If cy is *unlikely*
alibied (band 0.3), then "not alibied" is worth the **complement** — necessity `1
− 0.3` — and the accusation comes out at *likely* (0.7), never *certain*. (Logicians call
this the **possibility/necessity duality**: being sure of *not P* is exactly being
unsure of *P*.) It's the reason the decisive setting answered *likely* and not
*yes* — the machine folds the doubt of its assumption into the doubt of its
conclusion.

## Worlds that can't both be true

The last piece is what stops the machine fooling itself. Every derived maybe quietly
remembers the **set of pencil worlds it stands on** — its *environment*. When a rule
joins two facts, their environments **merge**; when a conclusion is drawn, it inherits
that merged set and carries it forward to the next rule.

Then one check does all the work: an `either… or…` writes its two scenarios as
alternatives of a single **choice**, and an environment that ends up needing **both
alternatives of one choice is impossible** — thrown out. That's why *tall* (scenario
one) and *loud* (scenario two) can never combine, even three rules downstream: the
contradiction is caught the moment their environments merge. This little
bookkeeping-of-assumptions is a classic device — an **assumption-based truth
maintenance system** — and it's what makes reasoning-with-maybes *sound* rather than
merely suggestive.

## Not a tenth way to think

Step back and notice what *didn't* happen. No probability arithmetic, no new
search, no backtracking trail — and, pointedly, **no tenth processing mode**.
"Likely" is a **composition** of things already on Chapter 16's closed list:
**Suppose** (the pencil worlds) + **graded matching** (the score) + **Check** read
through an α-cut (the θ dial). That's the whole discipline of this machine in one
example: a new power has to earn its place by being *nameable and visible in terms
of the old ones*, never by smuggling in machinery the graph can't see. Uncertainty
was made to pay that price — and it could.

---

**Next:** we've seen the machine's parts and its ways of thinking. The last chapter
is about its *character* — the attitude that ties it all together. [The machine's
attitude →](18-firmware.md)
