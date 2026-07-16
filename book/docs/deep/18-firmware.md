# The machine's attitude

Twice now we've leaned on the machine having an *attitude* — closed world versus
open mind (Chapter 5), and a willingness to hold a "no" only until better evidence
turns up. That raises a fair question: **where does an attitude live** in a thing
made of dots and arrows? It can't be baked into the reasoning core, because the
core is supposed to be domain-blind and opinion-free. The answer is a small,
swappable layer with a deliberately humble name: **firmware**.

## A generic engine, wearing a stance

Picture the machine in layers. At the bottom, the **substrate** — dots and arrows,
which know nothing. Above it, the **engine** — match, apply, chain, check — which
knows *how* to reason but takes no position on what anything means. Only at the top
sits the **firmware**: a tiny bundle of opinions that turns the neutral reasoner
into an opinionated one.

And "tiny" is not a figure of speech. The whole stance is a little declared record
with a couple of fields:

- **How to read absence.** Is an unprovable fact *false* (closed world) or merely
  *unknown* (open world)? This is a single default setting — with room for
  per-concept exceptions, so you can keep a mostly-closed world but mark a handful
  of concepts as "here, gather evidence instead of assuming no."
- **What to do with a tangled negation.** If the rules define "not" in a circle,
  should the machine refuse the rules up front, or quietly reason with the part it
  *can* trust?

That's essentially it. **"Keep an open mind" is not a special mode of the
engine — it is this one field flipped** from *closed* to *open*. The reasoning
machinery underneath doesn't change at all; it just gets handed a different
attitude to wear. Swap the firmware and the very same engine, on the very same
facts, gives you a differently-tempered mind — cautious or open, strict or
forgiving — without a line of the core being touched.

## Defeasible: a "no" it's willing to take back

This is the right moment to name something the book has been circling since
Chapter 5. When the machine closes the world and answers **no**, that "no" is
**defeasible** — a fancy word for a plain idea: *a conclusion held only until
something better comes along.*

Contrast two kinds of "no":

- *"cy is not cleared."* The machine looked for a reason cy is cleared and found
  none, so — world closed — it concluded no. But that rests entirely on **current**
  knowledge. Tell it `cy is alibied` tomorrow and the "no" evaporates, and so does
  everything that stood on it (cy being the thief). It was never claiming
  *impossibility* — only *"nothing I have points that way, for now."*
- *"a penguin is not a flyer,"* when you've taught it that the two categories are
  incompatible. Here it doesn't merely *fail* to find flight — it can **prove** the
  opposite. That "no" is not defeasible; it's a hard no, as solid as a yes.

Most of the machine's everyday "no"s are the first kind, and that's a feature, not
a weakness. A mind that treats every failure to prove as an eternal truth will
mislead you the moment its information grows. This one keeps its defeasible
conclusions honest about their own provisionality — which is the same humility that
lets it say **unknown** when you ask it to keep an open mind.

!!! note "Revising gracefully"
    Because every conclusion carries a receipt (Chapter 8), the machine knows
    *exactly* which beliefs rested on a fact you later remove or correct — so it can
    take them back cleanly, rather than being left with orphaned conclusions whose
    support has quietly vanished. Belief revision here isn't a bolt-on; it falls out
    of keeping the reasons around.

## Mechanism versus policy (or: why rules can't cheat)

There's a second, subtler place the same discipline shows up, and it's worth seeing
because it's what keeps the reasoning *sound*.

Back in Chapter 15 we said ordinary reasoning can only ever *add* facts — there's
no "erase" among the verbs a rule compiles to. That was true, but not the whole
truth. A real fact-deletion instruction **does** exist down in the instruction set.
The trick is that **ordinary rules physically cannot reach it.** The compiler that
turns your rules into little programs simply never emits that instruction. Only one
special client — the machinery in charge of *retraction*, when you deliberately
remove or revise a fact — is allowed to assemble a program containing it.

That split has a name: **mechanism versus policy.** The *mechanism* is the raw
capability (yes, the substrate can delete). The *policy* is who's allowed to invoke
it, and when. By keeping deletion as a privilege of the retraction layer rather than
a verb in the reasoning vocabulary, the machine guarantees — by construction, not by
good behaviour — that no chain of ordinary reasoning can ever quietly unmake a fact.
Your because-trails are safe because the power to break them was never handed to the
part of the system that reasons.

## Why keep it this austere?

Two payoffs, and they're the same two the whole book has been building toward.

**You can retune the machine without rebuilding it.** Want a stricter mind for a
finished case file, or a more open one for a live investigation? Swap the firmware.
The reasoning core — the part that's hard to get right — never moves.

**You can rebuild the core without changing a single answer.** Because the engine
is generic and the opinions live in a small, separate stance, the instruction set
is a *contract*. Reimplement the interpreter in a faster language, and as long as it
honours the same instructions, it gives the same dish from a different kitchen —
exactly the promise Chapter 14 made about *Universal*.

That's the machine, all the way down: a dumb, uniform substrate; a small, generic
engine; nine ways of thinking; and a thin layer of declared attitude on top. No
magic box in the middle — just arrows, a page of instructions, and an opinion you
can read and change.

---

## The end of Part 4

You've now seen not just *what* the machine does, but *how* — the instructions, the
nine modes, and the swappable stance that gives it its temperament. There genuinely
is nothing left hidden.

- The [appendix](../appendix/index.md) collects every concept, including the full
  [instruction set](../appendix/index.md#the-instruction-set-the-data-path) and
  the [nine modes](../appendix/index.md#the-nine-processing-modes) as reference
  tables.
- The project — code, design notes, and all — lives on
  **[GitHub](https://github.com/ercasta/Universal-Graph-Machine)**.

[:material-play-circle: **Back to the playground**](../playground/detective.md){ .md-button .md-button--primary }
