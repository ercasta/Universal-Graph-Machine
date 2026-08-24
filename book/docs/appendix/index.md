# Appendix — concepts, in plain language

Alphabetical. Each entry says what the thing is, and points at the chapter
where it earns its keep. Some entries are marked *retired* — the mechanism
they name has been removed from the engine. They're kept rather than deleted,
because a reader who hits the old term in an old blog post, an old corpus, or
their own memory of an earlier version of this book should still find out
what happened to it.

---

**absence** — `no p($x)`, a mode a member can be in alongside assert. It
holds when nothing at all asserts `p($x)`. Distinct from a denial on
purpose: `+not(p($x))` is a separate, ordinary proposition, and asserting it
does not by itself make `no p($x)` fail — a rule that wants to treat the two
the same has to check for both. Absence checks, never binds, and can never
be concluded. [Chapter 3](../basic/03-signs.md)

**alias** — corpus-defined shorthand for a structure: `alias sale($s, $b) = {
... }`. Expanded by the loader, so nothing downstream sees one. A nested
occurrence is **not** expanded, because nested is a denotation.

**anchored** — a proposition currently believed, as against merely mentioned
by some rule's stored pattern. `believed(p)` is the anchor; the opposite of
*generic*, which is about containing variables rather than about being
believed. [Chapter 2](../basic/02-propositions-and-entries.md)

**antecedent** — the *if* half of a rule: a list of members, each asserting,
denying by absence, or computing. [Chapter 6](../rules/06-a-rule-is-a-fact.md)

**anti-unification** — given two things that happened, the pattern they
already agree about. The dual of unification, and what *learning from
examples* is made of. [Chapter 29](../watching/29-learning.md)

**arbitration** — choosing which of the applicable rules to apply. A score
per rule, ties broken by declaration order; a loser is **deferred, not
rejected** — a run to quiescence applies it eventually unless something
forgoes or forbids it outright. [Chapter 17](../unsure/17-disagreement.md)

**at $m** — *retired.* A member used to be able to name which moment it sat
in. Refused at load now, with a message telling you why: there is no second
time left for a member to bind, because there is no moment for it to name. A
corpus that wants to talk about *when* writes it as an ordinary relation of
its own. [Chapter 5](../basic/05-the-read.md)

**@ grades** — *retired.* Uncertainty used to be a number annotating an
entry (`@0.7 likely(p)`). Refused at load now: uncertainty is an ordinary
proposition instead — `+likely(p)` — that a rule can read like anything else.
[Chapter 15](../unsure/15-how-strongly.md)

**belief** — presence. `believed(p)` holds or it doesn't; that is the whole
of what believing something means here. No confidence number, and — since an
earlier version of this engine — no record of how a belief was reached
attached to it. [Chapter 2](../basic/02-propositions-and-entries.md),
[Chapter 34](../horizon/34-not-built.md)

**boost / damp / reset** — *retired.* Postconditions that used to move a
*rule's* score. Retired because a rule id goes stale the moment the rule is
edited, composed or renamed — so a corpus of experience written against rule
names would stop *loading* rather than going quietly wrong. What replaced
them targets a **node**: see `attend`. [Chapter 28](../watching/28-the-table.md)

**causes** — *retired.* The second connective. Its consequent used to land
in a **later** moment, so it persisted once you stopped asking about the
cause — water you'd stopped heating stayed boiled. With no moments left to
land in, it did nothing `implies` didn't already do, so it was removed rather
than kept as a label. Refused at load with a message explaining why.
[Chapter 7](../rules/07-connectives.md)

**channel** — how something got here: a person, a sensor, a socket. What's
recorded is that *the channel said so*; whether to believe it is a rule's
business. [Chapter 21](../world/21-channels.md)

**computator** — a pure function given values and returning a value. Never
sees the graph, so it runs *during the match*, which keeps a whole change —
a purse transfer, say — in one application rather than caught half-done.
[Chapter 22](../world/22-tools.md)

**connective** — `implies`. There is exactly **one**: a second earns its
place only by licensing a different *(forward, backward)* reading pair, and
`causes` didn't — all it did was pick where the conclusion landed, and there
is nowhere left for it to land but here. [Chapter 7](../rules/07-connectives.md)

**consequent** — the *then* half of a rule: what a rule's postconditions
aside, applying it asserts or erases. [Chapter 6](../rules/06-a-rule-is-a-fact.md)

**corpus** — a text file of rules, facts and arrivals. What you teach the
machine. [Chapter 8](../rules/08-writing-a-corpus.md)

**delta** — the gap between where you are and where you want to be: computed
by a tool (the `<difference>` pattern), one `missing` or `extra` claim per
difference. A tool, because a rule matches one entry at a time and can't
speak about a set. [Chapter 12](../wanting/12-plans.md)

**dormant / due** — `dormant` is a claim that a rule is out of the running:
not considered at all until something claims `due` for it. The only thing
that removes a rule, and it is **per rule** — it does not carve out cases,
which is why an exception belongs in a premise instead (see *unless* in
`docs/authoring.md`). [Chapter 17](../unsure/17-disagreement.md)

**entity** — a labelless node: nothing but an id. Created by a rule, and
everything it answers to — including its name — is an ordinary claim about
it.

**entry / moment / locus / licence / chain** — *retired, as a family.* An
earlier version of this engine kept history as a chain of moments, each a
signed delta of entries, each entry carrying a licence recording what
produced it and a locus saying what it was about as against when it was
deposited. All of it — the chain, the walk that read it, the derivation
trail it carried — is gone. State is a single graph; belief is presence.
What this bought and what it cost is Chapter 34's subject, honestly, rather
than a single line here.

**frame** — a process node: what reasoning is running, where it's standing,
and where an answer is owed. Selectable, which is what a stack frame is not:
`push` opens one, suspending the current line of work; `pop` returns to the
one below, and everything the frame concluded stands.
[Chapter 25](../watching/25-own-state.md)

**generic** — containing variables. A pattern, as against something
*anchored*. [Chapter 30](../floor/30-the-floor.md)

**implies** — the one connective. `rule <name> = implies( { antecedent },
{ consequent } )` — braces and commas, or the terser line form (one member
per line, ending the antecedent with `->`, no braces or commas — the same
statement either way). [Chapter 7](../rules/07-connectives.md)

**lane** — a guaranteed turn every round, independent of whatever the
default (`main`) lane's arbitration selects that tick. `fact +lane(<R>,
watchdog)` puts `<R>` in its own lane — how a watchdog or referee rule stays
alive against a rule that always wins ordinary arbitration. See
`ugm/rules/circuit_breaker.ugm` for a complete worked pattern.
[Chapter 28](../watching/28-the-table.md)

**merge / unmerge / destroy / label / unlabel / forget** — postconditions
that act on the graph rather than on attention. `merge($a, $b)` and
`unmerge($a, $b)` decide two nodes are (or aren't) the same individual;
`destroy($x)` removes one; `label`/`unlabel` attach or remove a name;
`forget $x` erases a request and its answer together. See *postcondition*.

**no** — the absence keyword. See *absence*.

**norm** — a prohibition, written as a **trigger** that concludes `drop`.
Consulted on what a rule concluded, never proposed and never arbitrated.
[Chapter 18](../unsure/18-norms.md)

**occasion** — a fact the machinery deposits when something notable
happens, that a corpus can key a rule on: `bounded(ticks)` when a run hits
its tick limit, `pushed`/`popped` when a frame opens or closes.
[Chapter 27](../watching/27-recall.md)

**postcondition** — what a rule's `=> ...` tail, or a standalone `after <R>
{ query } => ...` trigger, spends once its query holds: `attend($x)` /
`attend($x, n)` (put a node at the front of what's considered next, weighted;
optionally negative), `unattend`, `stop` (ends the run), `push(...)` / `pop(...)`
(suspend a line of work for another), `merge(...)` / `unmerge(...)`,
`destroy(...)`, `label(...)` / `unlabel(...)`, `forget ...`.
[Chapter 28](../watching/28-the-table.md)

**proposition** — a relation instance. The *idea* of something. Claims
nothing on its own — believing it is a separate act, recorded as an anchor.
[Chapter 2](../basic/02-propositions-and-entries.md)

**? (unsure sign)** — *retired.* Used to mark a claim held before but not
now, with no replacement known — a third state next to assert and erase.
Gone: absence is ignorance, and there's nothing left for a third mark to
say. The parser also refuses `?name` outright now, as the old spelling of a
variable — write `$name`.

**quiescent** — applying anything further would change nothing.
**Exhaustion**, not satisfaction. [Chapter 26](../watching/26-stopping.md)

**recall** — which rules come to mind. A function rather than a search,
**incomplete by design** — so it returns a set *and* a state, and a dry
shortlist must widen. [Chapter 27](../watching/27-recall.md)

**reification** — a rule deposited as ordinary facts — `rule`, `ant`, `con`
— so other rules can read it. [Chapter 10](../rules/10-rules-are-subjects.md)

**relation instance** — a node with a relation and ordered members. What
would elsewhere be a labelled edge. Everything here is one.
[Chapter 1](../basic/01-the-substrate.md)

**sign** — `+` (assert) or `−` (erase). `no` is a third *mode* a member can
be in, in sign position, but it isn't a sign on an entry the way `+`/`−`
are — there's no entry left for it to be a member of. `−` only appears in a
**consequent**: there's no `−` in an antecedent any more, because there's no
denying claim left to match against. Say `no p` for absence, or `+not(p)`
for an explicit denial, instead. [Chapter 3](../basic/03-signs.md)

**stratum 0** — *retired.* Used to name a rule whose antecedent was entirely
structural — reading the chain's own skeleton (`anc`, `pred`, `in_delta`)
rather than an ordinary claim — applied without triggering the bootstrap
circle that reading anything else required. The skeleton went with the
chain, so nothing plays this role any more. [Chapter 31](../floor/31-bootstrap.md)

**supposing** — *the mechanism is removed.* It used to enter a hypothesis by
forking the chain into a frame, unwrapping the assumption on the way in and
re-wrapping conclusions on the way out. Nothing forks now, so a corpus holds
a hypothesis in the **proposition** instead — `given(h1, p)` — and the
wrapper is the containment. [Chapter 16](../unsure/16-supposing.md)

**table** — a score per rule, ordered, ties broken by declaration order. The
loop takes the highest-scoring rule in a window whose antecedent matches,
then spends its postconditions. [Chapter 28](../watching/28-the-table.md)

**table (of agents)** — several machines, each with its own scope and
corpus, wired channel to channel. Nothing is shared; what crosses is an
**utterance**. Two minds are two scopes, not two frames.
[Chapter 24](../world/24-several-agents.md)

**tool** — a request answered by a Python function rather than by search.
`kb.answerer` proposes an answer a **tick later** and never concludes
directly; `kb.computator` is pure and runs **during the match**, for
arithmetic and anything else with no side effect worth waiting a tick for.
[Chapter 22](../world/22-tools.md)

**trigger** — an ordinary rule marked `fact +intercepts(<T>, after)`,
consulted on what another rule is about to conclude before it lands. It
matches `producing(<R>, p)` — a fact that exists only while the question is
asked — and concludes an instruction: `instead(p, q)` replaces, `drop(p)`
refuses, anything else is added beside it. Norms and approval-gating are
both this one mechanism. `when`-triggers (ranking-time, no host rule) are
*retired* — hang a lesson off the rule that runs, with `after <R> { ... } =>
attend($x, n)`, instead. [Chapter 18](../unsure/18-norms.md)

**twin trap** — minting a fresh node for something the graph already
describes, so that everything said about the described thing goes to a node
nothing uses, and everything the machinery says about the live one names a
node nobody can reach. [Chapter 29](../watching/29-learning.md)

**utterance** — what crosses between two agents: **rendered text**, re-read
in the hearer's own name scope. A proposition survives the trip; anything
generic is refused at the hearer's parser. [Chapter 24](../world/24-several-agents.md)

**walker** — a **corpus pattern**, not engine machinery: a position in the
structure held as the ordinary fact `at(<w>, <node>)`, spawning rather than
moving, ending when that one fact is denied.
[Chapter 24](../world/24-several-agents.md)

---

## Four criteria, used everywhere

Every representation decision in this design is scored against these, in a
table, **before** the decision is taken — and the cost is written down even
when the choice is obvious.

| criterion | the question |
|---|---|
| **not leaking** | Can this shape state something the author did not intend? |
| **not lossy** | Is everything the author knew recoverable from what was stored — including what they *didn't* know? |
| **readable** | Can the obvious questions about this be asked as ordinary queries? |
| **composable** | Do two independently authored instances combine without either being rewritten? |

And a fifth thing, which is a method rather than a criterion, because it's a
property of two arcs of work **meeting**:

> **Two conventions that have never met are two conventions that have not
> been tested.**

---

## Standing lessons

Collected from throughout the book, because they transfer.

> **Something the machinery knows and no rule can ask about is a defect, and
> the repair is always to deposit the record.**

> **Index what was asserted. Never index what was derived.**

> **Nothing came to mind is not nothing is left to do.**

> **A corpus with no pathology cannot measure a detector for it.**

> **An agreement gate that agrees is worth nothing until it could have
> disagreed.**

> **Closed is a rate, not a kind.**

> **A claim with no measurement behind it is an opinion.**

> **Write your negatives.** An open-world engine believes only what's on
> record; a state block that lists only what's true won't drive a rule that
> asks what isn't.

> **Arbitration is scheduling, not decision.** A rule that loses a tick is
> deferred, not rejected.
