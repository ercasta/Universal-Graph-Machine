# What cannot be a convention

Nearly everything in this book is **taught**. Beliefs, rules, modalities,
channels, shapes, goals, plans — all of it is a representation of reality the
agent uses, not machinery the engine is built out of.

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

Match, commit, write — and everything else a corpus wants (goal expansion,
approval gating, retries, escalation) becomes rules that those apply. An
interpreter with one phase per convention has, in effect, compiled the whole
taught layer into itself.

The count of phases is therefore a direct measure of how much has escaped onto
the floor. It's a number an implementation can print. Chapter 32 prints it.

## The floor, in full

```
structure + ordering        by economy
variables + substitution    irreducible
one total step               irreducible
```

Three items. And the test of whether the line is drawn correctly:

> **Nothing on it mentions reality.**

Not one of those says anything about time, belief, evidence, causation or the
world. They're about how structure is built, matched and committed.

That's down from five. Two items that used to stand here — a register that
recorded where a write landed, and a stamp that recorded what produced every
mint — left the floor entirely, and the reason each left is worth stating
before the three that remain.

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
    A relation instance whose *relation slot* holds a variable — `$p($x)` — is an
    ordinary generic node, and the substrate could always build one.

    `ugm/core/rules.py`'s `candidates` still carries the case: a member whose
    relation is a variable takes the whole believed set as its pool, the same
    one a bare variable member gets. Nobody had asked which of three separate
    refusals — the surface wouldn't parse it, the unifier compared the relation
    slot by identity, substitution wouldn't rebuild one — was the *reason* it
    used to be unmatchable, so it read as a property of the floor. It isn't.
    Genericity is floor; *which slots may be generic* is a choice.

### Two items that left

**A register.** Writes used to land at a locus — a moment the machinery was
currently standing in — and something had to point at which one. That pointer
was floor, on the argument that finding it would itself need a read, and a read
needs somewhere to stand.

The locus is gone (`+on($x,$y) at $m` is refused at load, in full, by the
parser). A write today is `Gate.write`, and it does one thing: mint the anchor
`believed(p)`. Nothing about *where* survives to ask about — `gate.py`'s own
docstring says plainly what's left: *"one function in, one function out."* The
pointer had a job only as long as writes needed a place to land, and once they
stopped needing one there was no question left for a register to answer.

The attention stack (`Machine._frames`, `push`/`pop`) sits nearby and is easy to
mistake for the register's replacement. It isn't one: a frame is Python state
scoping what the agent is thinking about, never consulted by a write and never
itself a graph node a rule could read or move — only `attentioned($x)`, a
filter, sees into it at all.

**A stamp on every mint.** Every node used to record what produced it: which
rule, under which substitution, in which state. That was the derivation
record, and `gate.py` says where it went in one line: *"The licence and the
source were the derivation record, and the derivation record went with the
chain."* `Graph._mint` today records a relation, its members, whether it's
generic — and nothing else. Ask what produced a node and there is no answer
stored anywhere to ask for; `Machine` has no `why`.

This is a real cost, not a tidy simplification, and the book doesn't pretend
otherwise — see the "Deliberate, and a real cost" list in
[what is not built](../horizon/34-not-built.md).

### 3. One total step

Something must always answer. Selection cannot be allowed to search forever or
to return nothing, because the interpreter has no outside to fall back to.

**Totality** is floor. **What it consults is convention** — a score, the order
the rules were authored in, and whatever claims the corpus has made about its
own rules. `rules.arbitrate` is the code: total over whatever matched, tie-
broken by authored order, and it has no case in which it declines to answer.

The floor requires only that the final tiebreak **does not itself reason**. It
does not require that the answer be kept anywhere, or that there be much of it.
An earlier draft said *a lookup over an authored precedence table*; the table
went first, and then the precedence relations it cached went too, and totality
was never what was at stake in either.

## Two grounds, not one

The three items don't reach the floor for the same reason, and flattening them
into one list flatters the floor by making all of it look inevitable.

| item | ground | the argument |
|---|---|---|
| **variables + substitution** | **irreducible** | defining matching requires matching |
| **one total step** | **irreducible** | selecting the selector requires selection |
| **ordering** | **by economy** | fully reducible, and its reduction turns linear matching into subgraph isomorphism |

Both irreducible items share a shape: each is **the thing that would be
needed in order to do the thing itself**. And both take the same escape —
**a function, not a search**.

Ordering is a choice, and should be defended as one: it could be given up, at
the price of complexity. The two items that used to sit beside it on a third
ground — **by guarantee**, fully reducible but kept for what giving them up
would have cost — are the register and the stamp, and both were in fact given
up. The register cost nothing measurable once the locus went with it; the
stamp cost the derivation trail, which is why it's listed as a real cost above
rather than folded quietly into "simplified."

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

All three are checkable, and the checking has repeatedly overturned the
expectation it was run to confirm. A census retired the **grade** — 4 of 3,740
rules authored a non-certain one. A second census retired the **precedence
table** — deleting it cost 6.42s against 6.38s — and a third went through every
precedence claim in the repository, found that four of seven were doing
nothing and the rest were premises in disguise, and retired the relations
themselves. The same discipline, applied again later, is what took the
register and the stamp off this very list.

None was cut for being wrong. All were cut for being *unused where it counted*,
which is a measurement and not an argument.

> **Closed is a rate, not a kind.** A closed set defended well is
> indistinguishable, from the inside, from a closed set nobody has checked.

The bar is high because grammaticalization is **irreversible in practice**. Once
something is closed class it's no longer freely coinable, and every use of it
must route through machinery that knows its name.

## Primitive is not native

One last clarification, because it's the objection people raise.

Structure and matching *feel* like floor because they sit on the hot path of
every step, so an implementation puts them in native code.

That's an optimisation, not a status, and the difference is checkable where a
compiled path still has a slow definition to be held to:

> **For every taught convention, the rule-level definition must exist, and the
> compiled path must agree with it on answers *and on behaviour*.**

`Graph.has_var` is the surviving case in point: the cached answer at every node
is checked against `_has_var_slow`, the walked definition, every time the
substrate's own suite runs it — an index is a re-implementation of what it
indexes, and it has to be held to it. Chapter 32 has the rest of what still
checks itself this way, and it is a shorter list than it used to be, for the
same reason the floor above it is a shorter list.

The second clause isn't decoration. A convention compiled into the host language
**is not interruptible**, and Chapter 25 spends its length arguing that being
able to slow a thing down and look at it is the property worth protecting.

---

**Next:** if reading a rule requires applying rules, how does anything ever
start?
[The bootstrap →](31-bootstrap.md)
