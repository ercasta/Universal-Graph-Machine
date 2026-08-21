# What cannot be a convention

Nearly everything in this book is **taught**. Moments, entries, signs,
rules, modalities, channels, frames, goals, plans — all of it is a
representation of reality the agent uses, not machinery the engine is built out
of.

An agent that has them reasons better than one that treats every proposition as
a bare fact. It can say what it used to believe, what it's merely supposing, and
on whose word. And that superiority is a matter of what it was **taught**, not
of what it is **made of**.

You could teach a person to think this way without changing the chemistry of
their brain.

So: what's the chemistry?

## The test

> **A name is engine-level only if match and write cannot be defined without it.
> Everything else is a convention, and the machinery that uses it must be
> expressible as rules.**

Applied to the vocabulary an implementation actually reserves, that test
convicts nearly all of it. And it has a falsifiable consequence, which is the
point of stating it:

> **The interpreter's step should have no phases.**

Match, commit, write — and intake, supposition, acting, deviation and goal
expansion become rules that those apply. An interpreter with one phase per
convention has, in effect, compiled the whole taught layer into itself.

The count of phases is therefore a direct measure of how much has escaped onto
the floor. It's a number an implementation can print. Chapter 32 prints it.

## The floor, in full

```
structure + ordering        by economy
variables + substitution    irreducible
a register                  irreducible
a stamp on every mint       by guarantee
one total step              irreducible
```

Five items. And the test of whether the line is drawn correctly:

> **Nothing on it mentions reality.**

Not one of those says anything about time, belief, evidence, causation or the
world. They're about how structure is built, matched and committed.

### 1. Structure and ordering

Chapter 1, in full. Nodes, ordered members, nothing else. This is the medium,
and no convention can supply it because every convention is written in it.

### 2. Variables and substitution

A node may be **generic**: it contains variables. Given a generic node and an
anchored one, there is an operation that finds a substitution making the first
identical to the second, or reports that none exists.

This is the one item that **provably** cannot be a convention, and the reason is
self-reference:

> **You cannot define matching-with-variables using rules that themselves
> require matching-with-variables.**

Everything else that felt like floor in earlier drafts was floor by association
with this. A rule is a rule *because* it's generic; a pattern is a pattern
*because* something substitutes into it. Remove this and there's no rule layer
to write conventions in.

!!! note "Deep dive: which slots may be generic was never argued"
    A relation instance whose *relation slot* holds a variable — `?p(?x)` — is an
    ordinary generic node, and the substrate could always build one.

    It never matched, because three separate things declined it and **none of
    them on an argument**: the surface wouldn't parse it, the unifier compared
    the relation slot by identity, and substitution wouldn't rebuild one.

    Nobody had asked which of the three was the reason, so it read as a property
    of the floor. It isn't. Genericity is floor; *which slots may be generic* is
    a choice. Allowing it took about an hour, and it's what makes Chapter 8's
    class-as-data pattern possible.

### 3. A register

Writes land somewhere, and something must point at where. One pointer: the node
the machinery is currently working in.

The register is floor. **That it points at a moment is convention** — nothing in
the engine knows what kind of node it holds.

And **one** register, not a stack. A process that isn't running still has a
place it was standing, and resuming restores that place — but those saved
positions are *not* registers. They're ordinary members of ordinary frame nodes:
readable, writable, attributable. Resuming is a write to the register, sourced
from a frame; suspending is the same write in the other direction, and both
leave a trail.

If saved positions were registers, the design would have an unbounded set of
privileged slots and the agent could not be asked where a suspended process was
standing, or move it.

What must be privileged is only **which one is current**, because that's the
question no read can answer: finding the answer in the graph would require a
read, and a read needs somewhere to stand.

### 4. A stamp on every mint

Every node the engine creates records what produced it: which rule, under which
substitution, with the register in which state.

This introduces no name and says nothing about channels, authority or evidence.
It's on the floor because the alternative is **voluntary** provenance, and
voluntary provenance is forgeable — and both the modality argument (Chapter 15)
and the acquisition argument (Chapter 29) make the trail load-bearing for
*correctness* rather than for explanation.

> **Nothing is prohibited; everything is stamped.**

### 5. One total step

Something must always answer. Selection cannot be allowed to search forever or
to return nothing, because the interpreter has no outside to fall back to.

**Totality** is floor. **What it consults is convention** — a score, the order
the rules were authored in, and whatever claims the corpus has made about its
own rules (Chapter 17).

The floor requires only that the final tiebreak **does not itself reason**. It
does not require that the answer be kept anywhere, or that there be much of it.
An earlier draft said *a lookup over an authored precedence table*; the table
went first, and then the precedence relations it cached went too, and totality
was never what was at stake in either.

## Three grounds, not one

The five items don't reach the floor for the same reason, and flattening them
into one list flatters the floor by making all of it look inevitable.

| item | ground | the argument |
|---|---|---|
| **variables + substitution** | **irreducible** | defining matching requires matching |
| **one total step** | **irreducible** | selecting the selector requires selection |
| **the register** | **irreducible** | finding where to write requires a read, and a read requires somewhere to stand |
| **the stamp** | **by guarantee** | fully reducible — a rule could write its own provenance. But reducible provenance is forgeable provenance. |
| **ordering** | **by economy** | fully reducible, and its reduction turns linear matching into subgraph isomorphism |

The three irreducible items share a shape: each is **the thing that would be
needed in order to do the thing itself**. And all of them take the same escape —
**a function, not a search**.

The two others are choices, and should be defended as choices. The stamp could
be given up, at the price of soundness. Ordering could be given up, at the price
of complexity. Nothing else on this list could be given up at any price.

## Descent should be measured, not argued

Ordering reaching the floor by economy is a linguistic process exactly: an
open-class item, used constantly, bleached of content, becomes closed-class
structure. Ordering has every diagnostic — it means nothing in particular, it's
on every relation instance, you can't write `on(a, b)` without committing to
which is which, and positions aren't freely coinable.

Where the analogy bites is the disanalogy. In language that happens over
centuries and nobody decides it. In earlier drafts of this design it happened in
one sitting, which is how moments, entries, signs, connectives and goals all
ended up on the floor with no evidence behind them.

So:

> **A convention descends to the floor only by measured use:** high frequency,
> on the path of an irreducible primitive, and bleached of domain content.

All three are checkable, and the checking has twice overturned the expectation
it was run to confirm. A census retired the **grade** — 4 of 3,740 rules
authored a non-certain one. A second census retired the **precedence table** —
deleting it cost 6.42s against 6.38s — and a third went through every precedence
claim in the repository, found that four of seven were doing nothing and the
rest were premises in disguise, and retired the relations themselves.

None was cut for being wrong. All were cut for being *unused where it counted*,
which is a measurement and not an argument.

> **Closed is a rate, not a kind.** A closed set defended well is
> indistinguishable, from the inside, from a closed set nobody has checked.

The bar is high because grammaticalization is **irreversible in practice**. Once
something is closed class it's no longer freely coinable, and every use of it
must route through machinery that knows its name.

## Primitive is not native

One last clarification, because it's the objection people raise.

Moments, entries and signs *feel* like floor because they sit on the hot path of
every read, so an implementation puts them in native code.

That's an optimisation, not a status, and the difference is checkable:

> **For every taught convention, the rule-level definition must exist, and the
> compiled path must agree with it on answers *and on behaviour*.**

The second clause isn't decoration. A convention compiled into the host language
**is not interruptible**, and Chapter 25 spends its length arguing that being
able to slow a thing down and look at it is the property worth protecting.

---

**Next:** if reading a rule requires applying rules, how does anything ever
start?
[The bootstrap →](31-bootstrap.md)
