# Appendix — concepts, in plain language

Alphabetical. Each entry says what the thing is, and points at the chapter where
it earns its keep.

---

**anchored** — containing actual individuals, and connected to the real history.
The opposite of *generic*. A rule's two halves are generic; everything else is
anchored. The distinction is structural, so it's checkable rather than
maintained by etiquette. [Chapter 4](../basic/04-moments.md)

**antecedent** — the *if* half of a rule. A generic moment: a list of signed
entry patterns, plus any *skeleton* members relating their loci. Its order is
load-bearing, because the trail records what an application consumed by member
position. [Chapter 6](../rules/06-a-rule-is-a-fact.md)

**anti-unification** — given two things that happened, the pattern they already
agree about. The dual of unification, and what *learning from examples* is made
of. The whole difficulty is using **one** dictionary across premise and
conclusion. [Chapter 29](../watching/29-learning.md)

**attention** — what an applied rule **spends**. A rule's postconditions are
queries paired with **buffs**, and applying the rule runs them, moving other
rules' scores in the table. Buffs fade; the postcondition is what survives.
[Chapter 28](../watching/28-the-table.md)

**arbitration** — choosing which of the applicable rules to apply. *Totality* —
that something always answers — is a floor primitive. *Precedence* — which one
wins — is an ordinary claim read from the graph. A loser is **deferred, not
rejected**. [Chapter 17](../unsure/17-disagreement.md)

**blocked** — a claim the searcher makes about **itself**: I expanded this goal,
nothing fit, and I have stopped. Not *there is no way* — *I found no way*. No
positive rule can conclude it, because it's an aggregate over a finished
search. [Chapter 13](../wanting/13-blocked.md)

**causes** — one of two connectives. Its consequent is *asserted* and lands in a
**later** moment, so it persists: water you have stopped heating stays boiled.
[Chapter 7](../rules/07-connectives.md)

**channel** — how something got here: a person, a sensor, a socket. What's
recorded is that *the channel said so*; whether to believe it is a rule's
business. Distinct from **authority**, which is whose word it is.
[Chapter 21](../world/21-channels.md)

**computator** — a pure function given values and returning a value. Never sees
the graph, so it runs *during the match*, which keeps a whole change in one
application. Where arithmetic goes. [Chapter 22](../world/22-tools.md)

**connective** — `implies` or `causes`. There are exactly two, and the
membership test is that a connective must license a different *(forward,
backward)* reading pair. Adding one adds **rows, not branches**.
[Chapter 7](../rules/07-connectives.md)

**consequent** — the *then* half of a rule. A delta relative to the antecedent,
without being a second kind of object. May name a locus its antecedent bound.
[Chapter 6](../rules/06-a-rule-is-a-fact.md)

**corpus** — a text file of rules, facts and arrivals. What you teach the
machine. [Chapter 8](../rules/08-writing-a-corpus.md)

**delta** — the entries a moment holds. What changed. A moment stores only its
delta, which is why reading is a walk. [Chapter 4](../basic/04-moments.md)

**deposit moment** — *when a claim was made*. Not a member of the entry — it's
simply which moment's delta the entry sits in. The second of the read's two
indices. [Chapter 2](../basic/02-propositions-and-entries.md)

**entry** — a claim. Exactly three members: a **locus**, a **proposition**, and
a **sign**. Two claims about the same proposition at the same locus are two
different entries, because an entry is an *act of claiming*.
[Chapter 2](../basic/02-propositions-and-entries.md)

**frame** — a process node: what reasoning is running, where it's standing, and
where an answer is owed. Readable, writable and **selectable**, which is what a
stack frame is not. [Chapter 25](../watching/25-own-state.md)

**generic** — containing variables. A pattern. The one item on the floor that
provably cannot be taught, because you cannot define matching-with-variables
using rules that themselves require matching-with-variables.
[Chapter 30](../floor/30-the-floor.md)

**implies** — one of two connectives. Its consequent is *derived* and lands in
the **same** moment: retract the antecedent and the conclusion goes with it.
[Chapter 7](../rules/07-connectives.md)

**licence** — what authorised something. On a moment, why it differs from its
predecessor. On an entry, which rule application, load or arrival produced it.
Reading the licences is reading the machine's reasoning.
[Chapter 9](../rules/09-because.md)

**locus** — what a claim is *about*: a moment, or a **span**. The first of the
read's two indices, and the reason a claim about the past can be made now.
[Chapter 2](../basic/02-propositions-and-entries.md)

**moment** — a state of affairs. A signed delta, a predecessor, and a licence.
A state in time, a hypothetical, a supposition and a rule's antecedent are all
moments; there is no separate frame, world or context object.
[Chapter 4](../basic/04-moments.md)

**norm** — a prohibition. Checked at the **write**, never proposed and never
arbitrated, because what comes to mind is opaque and *the opaque component may
not be load-bearing for safety*. [Chapter 18](../unsure/18-norms.md)

**occasion** — a fact the machinery deposits when something notable happens:
`quiet`, `blocked`, `left`, `defeated`, `bounded`, `unsupported`. A corpus keys
on one to say *when this happens, think of me*.
[Chapter 27](../watching/27-recall.md)

**proposition** — a relation instance. The *idea* of something. Claims nothing
on its own — it has no locus and no sign, so it structurally cannot be mistaken
for a claim. [Chapter 2](../basic/02-propositions-and-entries.md)

**quiescent** — applying anything further would change nothing. **Exhaustion**,
not satisfaction. The loop may end; it may not end quietly on something it was
asked for. [Chapter 26](../watching/26-stopping.md)

**recall** — which rules come to mind. A function rather than a search, learned
from outcomes, **incomplete by design** — so it returns a set *and a state*, and
a dry shortlist must widen. [Chapter 27](../watching/27-recall.md)

**register** — the one privileged pointer: the node the machinery is currently
working in. Floor, because finding where to write requires a read, and a read
needs somewhere to stand. [Chapter 30](../floor/30-the-floor.md)

**reification** — a rule deposited as ordinary facts — `rule`, `conn`, `ant`,
`con` — so other rules can read it. Both the sign and the position are members,
or a rule read back out of the graph is a different rule.
[Chapter 10](../rules/10-rules-are-subjects.md)

**relation instance** — a node with a relation and ordered members. What would
elsewhere be a labelled edge. Everything here is one.
[Chapter 1](../basic/01-the-substrate.md)

**sign** — `+`, `−` or `?`, a member of the entry. `−` means **denied**, never
absent. `?` means *held before, does not now, and I cannot say what does*. No
entry at all means **inherit**. [Chapter 3](../basic/03-signs.md)

**skeleton** — the antecedent members that relate moments and entries to
each other rather than claim anything: `anc`, `sanc`, `pred`, `in_delta`,
`entry_of`, `rests_on`. No sign and no licence, because nobody asserted them,
and each must be **anchored** by an argument already bound.
[Chapter 6](../rules/06-a-rule-is-a-fact.md)

**span** — a stretch of the chain: a node with a start moment and an end moment.
Spans are **loci**, so a claim can be about a stretch rather than an instant.
Contents are not stored, because the predecessor relation is single-valued.
[Chapter 19](../world/19-spans.md)

**table** — a score per rule, ordered, ties broken by declaration order. The loop
takes the **first** rule in the window whose antecedent matches, then spends its
attention. Scores only fall down the table, so the window is a **prefix**: below
it, nothing is matched at all. A dry window widens.
[Chapter 28](../watching/28-the-table.md)

**table (of agents)** — several machines, each with its own scope, chain and
corpus, wired channel-to-channel. Nothing is shared; what crosses is an
**utterance**. Two minds are two scopes, not two frames.
[Chapter 24](../world/24-several-agents.md)

**stamp** — the floor-level record on every node the engine mints: what produced
it, under which substitution, with the register in which state. On the floor
because voluntary provenance is forgeable.
[Chapter 30](../floor/30-the-floor.md)

**stratum 0** — rules whose antecedent members are *all* structural. Applied
without a read, and therefore concluding structure rather than claims. One
predicate, read off the antecedent, decides both halves — which is what closes
the bootstrap circle. [Chapter 31](../floor/31-bootstrap.md)

**supposing** — entering a hypothesis. **Unwrap on the way in, re-wrap on the way
out**: inside the frame the assumption is an ordinary fact, and no rule needs a
hedged twin. Containment is free *for entries* — the frame's seat is a
*successor*, so the caller's walk can't reach it. It does not hold for
**structure**, which no walk resolves.
[Chapter 16](../unsure/16-supposing.md)

**tool** — a request answered by a function rather than by a search. Its answer
lands a tick later, and it **proposes; it never concludes**.
[Chapter 22](../world/22-tools.md)

**utterance** — what crosses between two agents: **rendered text**, re-read in
the hearer's own name scope. A proposition survives the trip; a moment, an entry,
a rule and anything generic are refused at the hearer's parser.
[Chapter 24](../world/24-several-agents.md)

**twin trap** — minting a fresh node for something the graph already describes,
so that everything said about the described thing goes to a node nothing uses,
and everything the machinery says about the live one names a node nobody can
reach. Found seven separate times here.
[Chapter 29](../watching/29-learning.md)

**marker** — the third part of an action, after the rule and its bindings: free
structure carried alongside a declared act, **read** by rules and never
**followed** by machinery. What makes the agent's context sayable, and therefore
what a learned policy would key on. [Chapter 14](../wanting/14-acting.md)

**walker** — a position in the **structure**, held as the ordinary fact
`at(<w>, <node>)`. It spawns rather than moves, its identity term *is* its
deduplication policy, and it ends when that one fact is denied.
[Chapter 24](../world/24-several-agents.md)

**discriminator** — what a failed prediction teaches: the feature true of the
case the rule got wrong and false of the cases it got right. Abstracted through
the corpus's own `is_a` facts, it becomes a claim about a **kind** rather than
about a thing. [Chapter 29](../watching/29-learning.md)

---

## Four criteria, used everywhere

Every representation decision in this design is scored against these, in a
table, **before** the decision is taken — and the cost is written down even when
the choice is obvious.

| criterion | the question |
|---|---|
| **not leaking** | Can this shape state something the author did not intend? |
| **not lossy** | Is everything the author knew recoverable from what was stored — including what they *didn't* know? |
| **readable** | Can the obvious questions about this be asked as ordinary queries? |
| **composable** | Do two independently authored instances combine without either being rewritten? |

And a fifth thing, which is a method rather than a criterion, because it's a
property of two arcs of work **meeting**:

> **Two conventions that have never met are two conventions that have not been
> tested.**

---

## Standing lessons

Collected from throughout the book, because they transfer.

> **Something the machinery knows and no rule can ask about is a defect, and the
> repair is always to deposit the record.**

> **Index what was asserted. Never index what was derived.**

> **An optimisation of a semantics is licensed by a gate. A cache of a claim is
> debt.**

> **Nothing came to mind is not nothing is left to do.**

> **A corpus with no pathology cannot measure a detector for it.**

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

> **Data rots in a way a branch does not.**

> **Closed is a rate, not a kind.**

> **A claim with no measurement behind it is an opinion.**
