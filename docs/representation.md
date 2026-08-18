# The graph, and how to represent things in it

A reference. What the substrate is, and the representation strategies that have
been settled — each with the reason, because most of them look arbitrary until
you know what goes wrong the other way.

Companion documents: `rules-design.md` is the design and the argument;
`situations.md` is a design not yet built; `deposit-dont-decide.md` is the test
for what belongs in the engine.

---

## 1. The substrate

**Everything is a node.** An atom, a relation instance, a rule, a moment, an
entry, a frame — all nodes, so anything can be the subject of anything.

    g.atom("paul")            a fresh node with a name. DOES NOT INTERN.
    g.rel(r, a, b)            r(a, b) -- INTERNS: same members, same node
    g.instance(r, a, b)       r(a, b) -- MINTS: a new node every call

`rel` interns so that the same proposition spoken of twice is one node. `instance`
mints so that two things which are alike are still two — moments, frames, entries.

**Names are for printing. Nodes are identity.** `g.call_it(n, "<boil>")` gives a
node a name and *"cannot make two nodes one or tell two apart"*. Identity is
decided when a name is **read**, in a scope: documents loaded under the same
scope share one name table, so `kettle` means one node inside a corpus by
construction rather than by inference. Coreference does not arise in authored
knowledge, and `sameas(a, b)` is refused — congruence would be either machinery
nobody can argue with, or a rule per relation per position.

**Three indices, all insertion-ordered** so nothing downstream inherits a
tie-break from a hash: interned instances by `(rel, members)`, instances by
relation, and instances by `(relation, position, member)`. The third is what
makes a join a join rather than a scan.

---

## 2. Assertion

**An entry is the unit of assertion**, with exactly three members and never a
fourth:

    entry(locus, proposition, sign)          sign ∈ { + , - , ? }

Licence, source and what it consumed are ordinary facts *about* the entry, not
fields. That is what lets `why(p)` walk back to the die roll that caused it.

**An entry carries two times, and keeping them apart is load-bearing:**

    locus     what the claim is ABOUT
    deposit   the moment whose delta it sits in -- WHEN it was made

They coincide in the common case. They come apart when the agent learns
something about a time that has already passed, *"which is what makes belief
revision ordinary rather than a second mechanism."*

**A proposition claims nothing.** `healthy(paul)` existing in the graph says
nothing at all; only an entry says something. This is why interning propositions
is safe: it shares *nodes*, not *claims*.

---

## 3. Time

**A moment is a state of affairs** — a node with a predecessor, a licence, and a
**delta**: the entries deposited in it. Moments form a **tree**, because
supposing forks by construction.

Only `causes` advances the seat, so a moment accumulates the entries of many
applications — `ugm.dungeon` runs about **16 entries per moment**. "Moment"
names a state of affairs, not an instant.

**The register is a pair**, and it is the one irreducible part of the design:
*finding where to write requires a read, and a read requires somewhere to stand.*

    seat      where the agent STANDS -- what it can see
    topic     what it is reading and writing ABOUT
              invariant: seat.at_or_after(topic)

**A locus is a moment or a span.** Spans are loci but are **not comparable** —
*they took turns over M1..M4* and *over M2..M4* neither supersedes the other —
so the resolved state is keyed on `(proposition, scope_of(locus))`, never on the
proposition alone.

**The read is `resolve(p, locus, seat)`** — does `p` hold at `locus`, as believed
at `seat`? Two orderings, not interchangeable:

    latest locus first    the most recent claim about the world wins,
                          WHICH IS WHAT MAKES SILENCE MEAN INHERIT
    latest deposit next   among claims about the same time, the current view
                          beats what the agent used to think

**Visibility is ancestry, not depth.** Two moments on different branches can
share a depth, and a depth test would let a claim made inside one supposition
answer a question asked in its sibling.

**Inheritance is this design's answer to the frame problem.** Nothing has to
restate what did not change; silence carries forward. Give that up and you get
the textbook version of the problem back.

---

## 4. Two layers, and the difference decides everything

|  | entries | structure |
|---|---|---|
| made by | any rule | a stratum-0 rule, or the chain |
| carries | locus, sign, licence, source | nothing |
| deniable | yes | **no** |
| dated | yes | no |
| contained by a supposition | yes | **no — it leaks** |
| `-` on a member means | *something denies it* | *not derived* |

**Stratum 0 is derived, not assigned**: a rule every one of whose antecedent
members is structural concludes structure. `skeleton()` computes the fixpoint
from below and recomputes when a rule is adopted; `strata()` layers them and
**refuses loudly** if the set cannot be stratified.

**Negation as failure exists only on the structural side**, and that is the
single most consequential fact in this table. Over entries, `-p` means *someone
denied p* — open world, and correct. Over structure, `-p` can only mean *not
derived*, which is the universal you actually want. Every use of "for no x" in
this repo goes through that door: `agreement`'s `<best>`, `quiescence`'s
`<quiet>`, `interpret`'s `<unmet>`.

**The bridge**: a stratum-0 rule reading the chain (`asking`, `anc`, `in_delta`,
`entry_of`) can lift entry-level facts into structure, and then negate them.

**And structure leaks out of suppositions.** Probed: an entry concluded inside a
supposition is not believed outside; a *structural* fact concluded inside it is
in the graph and visible everywhere. That is the defect `situations.md` exists
to fix.

---

## 5. Representation strategies

**Identity is decided at intake, by construction, in a scope.** Not inferred,
not merged later. Identity discovered afterwards is a *revision of intake* —
re-read the document with the binding corrected.

**A term is a rigid designator; a premise is a description.** Put the changeable
part in the antecedent:

    {+person(?p), +lives(?p, rome), +stabbed(?p)} => {+wounded(?p)}

`?p` carries the individual, so Paul stays wounded after moving to Florence.
Build the description into the term instead — `wounded(paul_from(rome))` — and
you get a rigid name with a misleading spelling, and `paul_from(florence)` is a
different individual you can never relate to it.

**A rule may mint individuals, provided they are denoted.** A compound term over
**bound** variables is legal in a consequent; only a free variable is refused.

    {+room(?r)} => {+is_a(occupant(?r), orc), +inside(occupant(?r), ?r)}

Several of a kind need a discriminator (`orc(?r, ?s)` over slots), which is
honest: things alike in every stated respect have no description that separates
them.

**The identity term IS the deduplication policy**, and interning enforces it
with no guard and no negation. `walker(<node>, <purpose>)` is the general form:
drop the purpose and arrivals merge; make the purpose the path and they never
do. Measured on chained diamonds: `2^(n+2) − 3` walkers by path against `3n + 1`
by node.

**Deduplicating is not forgetting.** Identity is *where a thing is*; provenance
is *how it got there*, and provenance is plural — one walker at the join, both
routes recorded.

**Position is a fact, not a register.** `at(<w>, <node>)` moves by ordinary
deposit and denial, so every move carries a licence and `why` answers it. The
register does not: `_apply` reseats on every `causes` application and nothing
records that the register moved. **Position is where, and it is recorded; the
seat is when, and it is not.**

**Termination is a denial.** Every position-relative rule needs `at(?w, ?x)`, so
one `-at(?w, ?x)` removes the walker from all of them at once. No scheduler, no
registry. It is not retroactive: what the walker already did, it did.

**An expert is a premise, not a pool.** A pool is one rule set per *run*, so it
cannot say *this rule applies to walkers running E*. A premise can, and
multiple inheritance falls out of one ordinary rule over `extends`/`knows`.

**An action is a rule, its bindings, and a free marker.** The first two make the
action; the third makes context sayable, so two situations identical in the
world but different in what the agent was doing can be told apart. The marker is
**read** by rules and never **followed** by machinery — otherwise control flow
leaves the loop and phases are back. Author atoms until an atom stops being
enough; the engine treats atoms and compounds alike, so nothing has to change
when it does.

**Aggregates split three ways.** *Some* is free — an ordinary antecedent already
is an existential. *All* is a negated counterexample, and it must be asked where
the search is finished, so **an aggregate premise makes a rule a post-quiescence
rule**: you cannot know *all* until you have stopped looking. *How many* is the
only real leaf; bounded comparisons (*more than three*) are a join over a strict
order, not a count.

**Reading the past needs `holds_at`, not `at ?m`.** `at ?m` binds the locus of
the entry that *satisfied* a member, and the state keeps only the winner — so
*p held then and does not now* was unwritable. `holds_at(p, m, sign)` resolves at
a named moment, as believed *at* that moment.

**The clock is off by default.** A stamp is structural, so entries stay
byte-identical with it on; what diverges is a corpus that *reads* it. Inert
until asked for.

---

## 6. Competence levers, and what each can actually do

| lever | lifetime | can it bring a rule into consideration |
|---|---|---|
| `standing(<R>)` | permanent | yes — raises the floor |
| `overrides(A, B)` | per tick | not ranking at all; it is defeat |
| `after <R> {q} => boost/damp` | fades (`LIFE`), saturates (`MAX_LIFT`) | **yes** |
| `when {q} => boost` | ephemeral, one shortlist | **no** |
| `prefer(<R>, key, score)` | permanent, summed | yes, but *a key is not a query* |

Two rules with teeth:

**A postcondition cannot see what its own rule just concluded.** Its query is
matched against the state as of the *start* of the tick. Key it on what held
*before* the decision.

**Precedence only bites when the loser's premise can be destroyed.** With
monotone rules the loop reaches the same quiescent state whatever the order.
Once a rule denies, ordering decides the outcome — and the ordering that decides
it can be the order the rules were *declared in*.

---

## 7. Traps that have cost real time

**`atom` does not intern.** A relation registered without adding its name to the
machine's reserved-name table gives a corpus a *fresh* node of the same name:
the rule parses, `is_stratum0` quietly answers no, the member matches nothing,
and nothing raises. Five occurrences on record.

**A rule's own pattern is an instance of its relation.** `instances_of(said)`
returns `said(?p)` alongside the real ones. Filter with `has_var`, or a count is
wrong and a numeric read raises.

**A variable-bearing structure is not a value.** Reading one as an index pivot
asks for the bucket of the pattern node itself, which nothing is an instance
against — so the member matches nothing, silently. Fixed in `_narrowed`; the
suite was 518/0 with and without the fix, because a corpus that only writes
atoms in argument positions cannot reach it.

**Minting the answer interns it.** A harness that builds its question as a node
can afterwards find it as its own answer. Compute and bind by hand instead.

**The cheapest-looking run is often the broken one.** A walker design that lost
a branch finished in fewer ticks, with less work, no error and no diagnostic.
Assert the *absence* that the failure produces, not the presence you hope for.

**A homogeneous fixture cannot measure a discriminator**, and a check whose
sensitivity depends on a race reports green while the bug is there.
