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
queries paired with something to spend, and applying the rule runs them. There
are five: `attend($x, n)` and `unattend`, which are claims about a **node**;
`stop`, which ends the run; and `push`/`pop`, which suspend a line of work for
another. None of them moves a score. (Three that did — `boost`, `damp`,
`reset` — are retired, because they named a *rule*, and a rule id goes stale.)
[Chapter 28](../watching/28-the-table.md)

**arbitration** — choosing which of the applicable rules to apply. *Totality* —
that something always answers — is a floor primitive. What it consults is a
score, authored order, and whatever the corpus has claimed about its own rules.
A loser is **deferred, not rejected**. [Chapter 17](../unsure/17-disagreement.md)

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

**delta (between two spans)** — what stands between where you are and where you
want to be, computed by the `<difference>` tool and materialised one `missing` /
`extra` entry per difference. A tool because a rule matches one entry and cannot
speak about a set. [Chapter 12](../wanting/12-plans.md)

**dormant** — a claim that a rule is out of the running: not considered at all
until something claims `due`. The only thing that removes a rule, and it is per
rule, which is why an exception belongs in a premise instead.
[Chapter 17](../unsure/17-disagreement.md)

**deposit moment** — *when a claim was made*. Not a member of the entry — it's
simply which moment's delta the entry sits in. The second of the read's two
indices. [Chapter 2](../basic/02-propositions-and-entries.md)

**entry** — a claim. Exactly two members: a **proposition** and a **sign**. Two
claims about the same proposition are two different entries, because an entry
is an *act of claiming*. (It had a third, the **locus**, and Chapter 2 says
what removing it bought.)
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

**locus** — *removed.* It said what a claim was **about**, as against when it
was deposited, and it was the first of the read's two indices. With it gone the
read is one rule — later supersedes earlier — and saying something about
another time is a corpus's job, written in the proposition.
[Chapter 5](../basic/05-the-read.md)

**moment** — a state of affairs. A signed delta and a predecessor. A state in
time and a rule's antecedent are both moments, so the thing a rule is made of
is the thing history is made of. (It carried a **licence** too; that is
recorded on the entry now.)
[Chapter 4](../basic/04-moments.md)

**norm** — a prohibition, written as a **trigger** that concludes `drop`.
Consulted on what a rule concluded, never proposed and never arbitrated, because
what comes to mind is opaque and *the opaque component may not be load-bearing
for safety*. [Chapter 18](../unsure/18-norms.md)

**occasion** — a fact the machinery deposits when something notable happens:
`quiet`, `blocked`, `refused`, `bounded`, `unsupported`, `pushed`, `popped`.
A corpus keys on one to say *when this happens, think of me*.
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

**stretch** — two moments, a start and an end, in a relation a **corpus**
names. A claim about a stretch carries it in the proposition. Contents are not
stored, because the predecessor relation is single-valued, so the walk between
the endpoints is unique. (It used to be an engine node, `span`, and a kind of
**locus**; both went together.)
[Chapter 19](../world/19-spans.md)

**table** — a score per rule, ordered, ties broken by declaration order. The loop
takes the **first** rule in the window whose antecedent matches, then spends its
attention. Scores only fall down the table, so the window is a **prefix**: below
it, nothing is matched at all. A dry window widens.
[Chapter 28](../watching/28-the-table.md)

**table (of agents)** — several machines, each with its own scope, chain and
corpus, wired channel-to-channel. Nothing is shared; what crosses is an
**utterance**. Two minds are two scopes, not two frames.

**trigger** — an ordinary rule marked `intercepts(<T>, after)`, consulted on
what another rule is about to conclude. It matches `producing(<R>, p)` — a fact
that exists only while that question is asked and is never deposited — and what
it concludes is an instruction: `instead(p, q)` replaces, `drop(p)` refuses,
anything else is added. Norms, hypothesis marking and wrapping are all this one
mechanism. [Chapter 18](../unsure/18-norms.md)
[Chapter 24](../world/24-several-agents.md)

**stamp** — the floor-level record on every node the engine mints: what produced
it, under which substitution, with the register in which state. On the floor
because voluntary provenance is forgeable.
[Chapter 30](../floor/30-the-floor.md)

**stratum 0** — rules whose antecedent members are *all* structural. Applied
without a read, and therefore concluding structure rather than claims. One
predicate, read off the antecedent, decides both halves — which is what closes
the bootstrap circle. [Chapter 31](../floor/31-bootstrap.md)

**supposing** — *the mechanism is removed.* It entered a hypothesis by forking
the chain into a frame, unwrapping the assumption on the way in and re-wrapping
conclusions on the way out; containment was free, because the caller's walk
could not reach down the branch. Nothing forks now, so a corpus holds a
hypothesis in the **proposition** instead — `given(h1, p)` — and the wrapper is
the containment.
[Chapter 16](../unsure/16-supposing.md)

**absence** — `no p($x)`, a fourth way an antecedent member relates to the
state: it holds when nothing **asserts** `p($x)`. Distinct from `-p($x)`
(*something denies it*) on purpose, because the rule that materialises a denial
must ask about absence first. It checks, never binds, and can never be
concluded.

**alias** — corpus-defined shorthand for a structure: `alias sale($s, $b) = {
... }`. Expanded by the loader, so nothing downstream sees one. A nested
occurrence is **not** expanded, because nested is a denotation.

**entity** — a labelless node: nothing but an id. Created by a rule, with the
`+marker` mint in a consequent, and everything it answers to — including its
name — is an ordinary claim about it.

**denotation** — an expression with no id of its own, like
`attack(goblin, you)`. Not a thing in the world but a **criterion for matching
one**, which is what makes it a query. A relation declared
`relationship(<rel>)` may only relate things that *have* ids, so a denotation
in one of its argument places is refused at the write.

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

**walker** — a **corpus pattern**, not engine machinery: a position in the
structure held as the ordinary fact `at(<w>, <node>)`, spawning rather than
moving, ending when that one fact is denied. Still writable; the probe that
measured it was deleted, so the numbers once quoted for it are history.
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
