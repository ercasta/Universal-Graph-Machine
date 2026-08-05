# Facts as nodes — the universal shape

**The design this arc is building toward.** Scored throughout against
[harmony.md](harmony.md)'s four criteria, which is the standing process rather than a flourish here:
two of the decisions below came out differently once they were scored.

## The shape

Everything that relates things is a **node with a type and members**: a per-fact node, one edge to the
relation concept, and positional edges to the members, numbered **from 0**.

```
f1 = on(a, b)                 the reading form — see harmony.md §Notation

#7 --is--> on                 the storage form
#7 --at--> a                  position 0
#7 --at--> b                  position 1
```

⚠ **The relation is the node's TYPE, not its member 0.** `[predicate, subject, object]` was considered
and dropped: it puts a thing of a different kind at position 0 from the ones at 1 and 2, which is the
*one shape, several membership semantics* hazard reappearing **inside a single fact**, and it buys
nothing — the relation concept is a shared node under either, reachable by reverse lookup either way.
⚠ `ugm/fact.py` still says S-P-O and numbers positions from 1; that is the module, not the design.

One member label. The type on the node, never on the edge. Roles carried by **position**, never by a
role name — `subject` / `object` / `agent` / `patient` are all rejected, and the reason is not taste:
a label is a name, a name is where meaning lives, and this engine already carries *one relation under
four names* (`before` / `then` / `after` / `next`) and *one name over three relations* (`next`, on
frames, mappings and tokens). Position commits to nothing.

⭐ **And it is one construct, not a family.** A fact, a constraint, a moment, a frame, a
transformation and the identity bridge are the same shape at different addresses:

| | type | members |
|---|---|---|
| a world fact | `on` | the participants |
| **an attribute** | `attribute` | **the subject, the property, the value** |
| a goal's constraint | `link` | what must relate |
| a moment | `moment` | what it dates |
| a frame | `frame` | its delta |
| the identity bridge | `same_as` | the identity and the version |

⚠ **One shape, several membership semantics** — positional and fixed-arity for a fact, an unordered
delta for a frame, an unordered set for a moment. **Sharing the shape must not become sharing the
meaning**; that is the same discipline the five orders are held to, one level down.

## ⭐⭐⭐ Entities have no outgoing edges

This is the load-bearing consequence and the reason the shape is worth the conversion.

If every relation hangs off a hub, then a domain node is a pure **referent**: nothing points out of it,
and every relation about it is found by reverse lookup. Three things follow, and the third is the one
that matters.

* **A relation forming does not touch its participants.** No version of `a` is minted when a relation
  about `a` changes, so a frame's delta grows by exactly one node per change.
* **The relation has an identity**, so it can be dated, caused, questioned and retracted. *When did
  this become true* becomes askable — which is the **not lossy** criterion, and the thing a labelled
  edge can never satisfy because there is no node to point at.
* ⭐⭐⭐ **Path composition cannot fabricate a fact**, structurally rather than by discipline. There are
  no entity→entity paths to compose. Contrast the shape this rules out — a 2-hop path through a
  **shared** predicate node, where `a --> on --> b` and `c --> on --> d` put `a --> on --> d` in the
  graph, which nobody asserted. That is the canonical leak, and it looks harmless.

### And isolation between hypotheses falls out of it

The engine already relies on exactly this, in `workbench.reachable`:

> *Metadata is not reached, by the direction invariant — mappings, applications, hypotheses and plans
> all point at domain nodes and are never pointed at by them.*

A `same_as` hub points at both the real node and the imagined one and is pointed at by neither, so a
forward traversal from `a` **cannot** reach the version in a hypothesis — no matter how label-agnostic
the walk is, and there are eight label-agnostic walkers in the engine. Crossing requires a reverse
lookup, which is deliberate and names what it wants.

⚠ **So the guarantee is the direction invariant, not the node-ness.** Anything that adds a back-pointer
"for convenience" breaks isolation silently. `workbench_copies_are_structurally_unreachable` is the
standing tripwire.

⭐ The bridge is a **star, not a pairing**: H1's `a` and H2's `a` are not linked to each other, both
point back to one identity. `n` bridges rather than `n²`, and an imagined node *is its own original* so
later versions have an identity to share.

## Roles are a convention, declared once per relation

Position order follows how the relation is said — `a above b` is `[a, b]`. ⚠ The alternative, an
interposed role node (`on --above--> a`), was rejected for a specific reason: `above` would then name
both *the role `a` plays here* and *a relation in its own right*, which is the one-name-over-several-
relations defect the census already caught the engine committing with `next`.

What the convention needs to stay **readable**: the relation type declares its **arity**, so a fact with
the wrong number of participants is catchable rather than silently short, and role *names* may ride
along as documentation — readable, not load-bearing, and declared **once per relation** rather than as a
label on every instance. Precedent: a method already declares its drawn roles (`M.roles_of`).

⚠ **Converses must be declared, not stored twice.** *a above b* and *b below a* are one fact; two
records of it can drift. One canonical relation plus `above --converse--> below`, so the converse is
derived and the derivation can cite why.

## ⭐⭐⭐ Attributes are the same shape, and the substrate stops having attributes

`a.height = 2` and `a.clear = true` are node attributes today — outside everything above, so *when did
`a` become clear, and who says so* was as unanswerable as under a labelled edge, and `require_attr`
exists as a separate constraint sort **because** of that split. They take the shape:

```
attribute(a, clear, 1.0)          subject, property, value
attribute(a, red, 1.0)
attribute(a, height, 2)
```

⭐ **Values are nodes, and the saving is that qualifiers are SHARED.** One `red`, one `fast`, one `1.0`,
pointed at by every attribute node that says so — so *what else is red* is an ordinary reverse lookup,
and a qualifier is a thing two KBs can be said to mean the same by.

⚠⚠⚠ **And the per-fact node is what makes sharing safe rather than the leak it looks like.** `a --red-->
red` and `b --red--> red` is encoding (ii), the canonical shared middle: the path `a → red → b` is in the
graph and nobody asserted it. With the bridge there is no such path, because **entities have no outgoing
edges** — `red` is reached only from the attribute nodes, and getting from `a` to `b` requires two
deliberate reverse lookups that name what they want. **Sharing is licensed by the shape, not tolerated
by discipline.**

⭐ **Which property vocabulary a domain uses is a KB decision, not an engine one.** `attribute(a, red,
1.0)` and `attribute(a, color, "red")` may both be available, and choosing is authoring. ⚠ Two KBs
choosing differently is not a defect in the shape — it is exactly the cross-domain case
[harmonization.md](harmonization.md) owns, settled by an **authored bridge with a speaker**, which is
the one form of alignment that leaves a residue.

### ⭐⭐ The consequence: nothing in the substrate carries attributes

If attributes are nodes, the attribute *mechanism* has no remaining job. Three things live in
`Graph.attrs` today and each has to go somewhere:

| today | after |
|---|---|
| `kind`, set at mint, indexed by `of_kind`, refused by `put` | the **type edge** — one of the two floor relations, doing the job it already names |
| a scalar's payload | **identity by content** — a scalar node does not *carry* `1.0`, it **is** it |
| edge properties (`eprops`, `NEPROPS` / `EPROP_AT` / `SETEPROP`) | gone with the rest — they exist only because an edge could not carry a fact, which is the problem this arc dissolves |

⭐⭐⭐ **Identity by content is where the regress stops, and it is the same move as the meta-level
floor.** *Not a logician's blackboard* is true of the domain and false of the substrate (§*Where this
could be wrong*, item 3); the same shape one level down is **at the bottom, existence is the value.** A
scalar node is not asserted to be `1.0` by anything — being that node is what `1.0` means here.

⚠ **This is forced rather than chosen**: with no attributes there is nowhere for a scalar to *carry* its
payload, so its **id is its content**. That dedupes by construction, and it is **not** the interning
declined in §*No settling, no interning* — there is no index, no write-time lookup and nothing to
invalidate.

⭐ **`require_attr` disappears.** `attribute(a, red, 1.0)` is a proposition, so *"a must be red"* is
`requires(goal, that proposition)` — the same collapse `link` gets. ⚠ Only the non-equality comparisons
(`<`, `>`) still need a constraint node carrying `op`, so this is a shrink rather than a unification,
which is the honest version of the same note about `link`.

### ✅ MEASURED — `python -m ugm.labels attrs`

This was recorded as *unmeasured, and by far the largest item in the arc*. It is now measured, and
**the expectation was wrong in a useful direction.**

| | |
|---|---|
| attribute **writes**, over the selftest | **12,113,386** across 1,573 keys — against 2.6M edges, so **attributes are ~4.7× the edge traffic** |
| of which `kind` | 2,246,210 — **18%**, and `kind` is settled to become the type edge |
| keys only ever written by a **rule** | 36 keys, **141 writes** |
| **reads**, over one Sussman search | 2,130,088 graph reads: **attributes 84.1%**, edges 15.9% |
| whose attributes they are | `register` 33.2%, `activation` 29.6%, `arg` 20.0%, `function` 8.2%, `instr` 5.8% — **~97% is the interpreter reading itself** |
| ⭐⭐⭐ `block` — **the world's own nodes, which is what converts** | **1,038 reads: 0.06%** of attribute reads, 0.05% of all reads |
| **bulk** reads — the whole attribute dict of a node, at once | **772, from exactly two call sites**: `isa._keys` (521) and `driver.state_of` (250) |

⭐⭐⭐ **So attributes are the largest POPULATION and the smallest TRAFFIC.** The prediction above was
that the published figures *understate* the conversion; measured, total attribute traffic is five times
the edge traffic **and the conversion target is 0.06%** — smaller than the world-relation figure
(0.09–1.72%) it was supposed to dwarf. The 84% is `register`, `activation`, `arg` and `instr`: the
interpreter reading its own state, which is below the floor and does not convert.

⭐⭐ **And the read shape that was supposed to hurt barely exists.** A bulk read is the one that becomes
*every attribute fact about this node* — a reverse-index walk under a hub, where `attr(n, k)` is one
lookup. There are **two call sites in the engine**, and knowing which two is worth more than the
percentage: `isa._keys` (the `NKEYS` / `KEY_AT` reflection pair) and `driver.state_of`.

⚠ **The caveat is the one the read census already carries**: this is a *Sussman* workload, which is
planning-shaped and interpreter-heavy. It bounds the cost of converting the world's attributes; it says
nothing about a workload that mostly reads domain state. ⚠ And it is not a clearance for item 4 —
performance stays a separate concern, but *measured and small* is now the honest description rather
than *unmeasured and largest*.

## ⭐⭐⭐ A proposition is not an assertion

**`a on b` is the representation of a concept.** Whether it holds, who said so, when, and whether they
are reliable are *separate facts to be reasoned over*. **This is not a logician's blackboard where
something becomes true by being written on it.**

So a fact node is a **proposition**, and holding is a claim about it:

```
on#7      --is--> on          the proposition — that a is on b
on#7      --at-->  a, b
claimed#3 --is--> claimed     the assertion — Anna said so, at m5
claimed#3 --at-->  on#7, anna
```

⭐ **The decisive argument against the cheap alternative.** If existence *were* assertion, retracting a
fact would mean deleting the node — and the node is the thing carrying the relation's identity, its time
and its cause. *When did this stop being true* and *what made it stop* would be unanswerable exactly
when they matter. That grants datability only to facts that never change, which is the uninteresting
half, and it defeats the arc.

Three further things follow:

* **Negatives are first class.** *"a is not on b"* becomes an assertion about a proposition, rather than
  the absence of an edge plus a stance over silence.
* **A goal can point at an unasserted proposition** — `goal --requires--> on#7`. ⚠ Which collapses the
  `link` constraint into a proposition plus a `requires` edge; `attr`, `type` and `known` carry `op`,
  `value` and `key` and do not reduce, so this is a simplification of the commonest sort, not a
  unification.
* ⭐ **The harmony instrument generalises.** *Every entry in a frame's delta must be attributable to
  that frame's transformation* becomes **every fact that holds must be attributable to an assertion** —
  an unattributed fact being precisely one the blackboard made true. Same instrument, wider scope.

**Some of this exists and applies only to utterances**: `discourse.py` has `speaker`, `authority`,
`retract`, `is_withdrawn`, `live`, and `unknown_is_not_no_unless_you_say_so` already holds that *no
derivation means UNKNOWN, the stance is what makes it NO, an absent edge refutes nothing*. A fact in the
world has none of it.

⚠⚠ **The cost has to be designed, not discovered.** Reading stops being a lookup and becomes a weighing,
and `holds` is already 54% of Sussman merely by being interpreted. **Settling is not the answer** — see
the next section.

## ⭐⭐⭐ Decided: no settling, no interning

Both were on the table as answers to the cost above — cache the weighed read, dedupe the minted fact —
and **both are declined, for one reason: a cache of a derived value has to be invalidated, and
invalidation is a TMS.** This codebase has priced that commitment twice already and put it down both
times (§*Pattern matching becomes a join*: *a materialised view needs invalidation, and invalidation is
a TMS, which is a larger commitment than RETE*).

⭐ **The line, and it is the useful form of the decision:**

> **An index over what was ASSERTED is storage. A cache of what was DERIVED is a TMS.**

`workbench.index` is the first kind, and it is already load-bearing — a key-to-node map the substrate
maintains, knowing nothing about what it means. Settling and write-time dedupe are the second.

⭐⭐ **What replaces them: equality is BY CONTENT, computed where it is needed, never by node identity.**
That is what disposes of the multi-minter hazard in item 2 rather than deferring it — a goal's
`on(a, b)` and a rule's `on(a, b)` being different nodes stops mattering the moment nothing compares
nodes. ⚠ It also means `holds` must compare content, which is a real cost on the hot path and is the
one this decision accepts in exchange for having nothing to invalidate.

⚠ **What this gives up, said plainly**: *reasoning that has been done stays done* is half the benchmark
against an LLM, and declining settling declines the read-level version of it. What survives is the
structural version, which is the stronger one anyway — a frame's delta and the transformation beside it
**are** work that stays done, persisted without an invalidation obligation because nothing derived is
stored as though it were asserted.

⭐ It also makes the **force/deontic** row's discrimination pair trivial to construct — the same
proposition asserted by two speakers of different authority, and the agent should plan differently. That
row is ❌ for *recognise* and ⚠ for *check* in the matrix, and it has been blocked on having nothing to
vary.

## Ordered and unordered are declared, not assumed

Position is meaning for a fact's participants and storage noise for a moment's dated things. Reading
insertion order off the second yields *which thing this moment dated first* — information nobody
asserted, manufactured by the storage. **That is a leak**, by the same criterion as the shared-middle
path, and this project has been bitten by it twice already (*a deterministic computation ending in a
`set` has an undeclared tie-break*; `visible` having to answer in layout order because insertion order
had silently become the search's last tie-break).

So the property is **declared on the relation node**, which is only expressible because relations are
becoming nodes — under a bare edge label there is nowhere to hang it but a side table in Python:

```
at    --is--> ordered        position is asserted; reading it is licensed
dates --is--> unordered      order is storage; reading it is a leak
```

⚠ **Not two classes of edge in the kernel.** *Something may be a primitive iff every decision it
embodies can be an argument* — and whether a relation has order is a knowledge claim about that
relation, authored per domain, and exactly the kind two independently authored KBs must agree on in
order to compose. It belongs above the horizon. A set-backed store would also still hand back *some*
iteration order, replacing a declared artefact with an undeclared one.

**Enforcement has exactly one door**, and it falls out of the instruction set having no `iterate`:

| read | exposes order? | on an unordered relation |
|---|---|---|
| `relations` / `COUNT` | no — cardinality is asserted | fine |
| `related` / `GET` | hands back a collection | fine as a collection |
| `relation_at` / `GET_AT` | **yes, the only one** | **`REFUSE`, with a reason** |

⚠ **Refuse rather than reorder.** Canonicalising an unordered read — sorting by id — is worse and there
is a recorded instance: `g.sources` answers sorted by node id, *"cannot answer the most recent"*, and
three successive guards passed with the defect planted. A deterministic arbitrary order looks like an
answer.

Alongside: a **shuffle mode for checks only**, so accidental order-dependence fails loudly rather than
silently (Go's randomised map iteration, for the same reason) — test-only, because *the search was once
irreproducible* and that cost a session. And a **census-shaped audit** for the Python side, since the
refusal governs only mediated reads.

## The floor

A hub's pointers to its members cannot themselves be hubs, or the storage regresses. So the floor is
**the membership relation and the type relation**, plus what the frame chain needs — and essentially
nothing else. All 147 labels in the census (`python -m ugm.labels`) are candidates above it.

⚠ **Metadata is a hub but is not a world fact**, and the distinction is the direction invariant rather
than convenience. A constraint *requires* a relation rather than asserting it; putting it on the path
between `a` and `b` would make `a` point at metadata, while *a goal points at the world and is never
pointed at by it*.

## Frames

⚠⚠⚠ **A technical frame is not a logical frame, and the word is overloaded four ways in the literature
before this engine adds a fifth** (Minsky/Barsalou schemas, Fillmore frame semantics, stack frames, the
frame problem). The engine's `frame` is a **technical** device: a delta and a chain that make successive
states cheap. A **hypothesis** or a **scope** is a *logical* context — claims held under an assumption,
an epistemic fact with a why. They may share a mechanism; they are not the same thing, and collapsing
them makes *what is assumed here* and *what changed here* one question with two answers. ✅ The code
already keeps them apart: `hypothesis.py` has its own vocabulary and is not a frame.

**Frames are Memento** — they hold the transformation (`via` → `applies` / `ran` / `assumes`) *and* the
delta. Not a duplication, two jobs: the transformation is the residue that answers *why is the state
this way*, the delta is the O(1) answer to *what is the state*. Pure Memento replays from the root and
makes reads O(history); the delta alone is speed with no explanation.

⭐⭐⭐ **And the pairing hands over the harmony invariant for free:**

> **Every entry in a frame's delta must be attributable to that frame's transformation.**

An entry nothing accounts for *is* information no operation licensed. Built: `python -m ugm.leak`,
containment form, green over a full Sussman search with a planted-leak control and a reported *slack*
figure (2.0×) saying how loose the net is — because a containment satisfied by an over-broad licence is
a green light that means nothing.

⚠⚠⚠ **Frame membership must be SIGNED, not a list.** An additive delta inherits its parent's
connections: `f0` holds `on(a,table)`, `f1` adds `on(a,b)`, and `f1` now says `a` is on the table *and*
on `b` — the leak this arc exists to stop, reappearing inside the mechanism meant to prevent it. Three
states, and they are the ones this engine already insists on distinguishing:

* an entry saying **present** — it holds here
* an entry saying **absent** — retracted here; shadows the parent
* **no entry** — inherit; and if nothing in the chain has one, the honest answer is **UNKNOWN**

Which means `retract` is a first-class operation, not `unrelate`: in a chained frame, deleting an edge
either removes it from the parent or silently does nothing.

⚠⚠⚠ **`absent` is the frame mechanism and nothing else — it is how you DELETE something that was
present in a previous frame.** It is not *"a is not on b"*, and the two must not be collapsed even
though both would be called negation. `unstack` in a child frame records `on(a, b)` **absent**; Anna
saying the block is not on the table is a **claim about the proposition**, at the epistemic layer, and
it stays where it is when the frame chain moves. The distinction is the frame-vs-hypothesis one again
(*a technical frame is not a logical frame*), one level down, and it decides the cost: signing is O(1)
shadowing on the search's hottest path, while weighing claims is what §*A proposition is not an
assertion* has to design **settling** for.

⭐ **Which leaves three layers, and naming them is what keeps the earlier sections consistent:**

| | |
|---|---|
| **existence** | the proposition node — `on(a, b)` is a concept; minting it asserts nothing |
| **holding** | signed membership in a frame — present / absent / inherit, per world |
| **attribution** | claims about the proposition — who said so, when, with what authority |

*Not a logician's blackboard* is the first line; **signed membership is the second**; and the third is
the one `discourse.py` already has for utterances and the world has none of.

## What this buys that is not obvious

**The relation's own algebra becomes data.** `then --is--> transitive` is assertable, so a derivation
that walks a chain has a **premise to cite** — *A is before C because of these turn nodes, and because
`then` is transitive, which Anna declared.* Under labelled edges, transitivity can only live in Python,
where the residue cannot cite it and where walking the chain and inventing the conclusion are
indistinguishable. **A leak that only becomes visible after the representation improves.**

**`[i+1]` stops being a literal.** The recorded blocker on *taking turns* is that
`step[i].agent is not step[i+1].agent` is unsayable because `path.Hop.index` is an `int`. With the order
reified, the successor is a **node reached by an edge**, and the sentence becomes an ordinary constraint
over two related nodes. Reifying the order is what makes relative position sayable.

⚠ **But meaning is dynamical, so *taking turns* must not be stored.** It is a reading a rule attributes
to a chain — the **recognition** column — and harmony applies there too: attributing the label may add
nothing to the graph beyond *I read it this way, on these nodes*. A recognizer that writes
`taking_turns` as a plain fact has laundered an interpretation into an observation, which is the same
error as deriving transitivity without licensing it.

## ⚠ Consequences that are not translations of existing code

Two pieces change shape rather than move, and both sit directly under planning.

* **`reachable` inverts.** *"Everything reachable from `start` by outgoing edges"* is the workbench's
  copy boundary — and if entities have no outgoing edges it returns **just `start`**. The boundary must
  become a **reverse closure**: the facts mentioning these entities, then the entities those mention,
  transitively. Different termination properties, and it needs an explicit bound where the forward walk
  needed none.
* **`path.adjacent`** — *"the one hop everything traverses through"* — stops being an edge and becomes
  reverse-index → hub → forward, with a predicate filter. It is load-bearing for `reaches`, containment,
  discourse authority and norms.

**Cost is not the risk.** The read census (`python -m ugm.labels reads`) measured world-relation reads
at 0.09% / 0.45% / 1.72% of all reads at 3 / 23 / 103 blocks, against interpreter plumbing that never
converts holding two thirds. ⚠ The curve is the result, not the first row — but even at the top the
labels this arc converts are under 2% of reads. The read-path objection was raised three times in
design and did not survive measurement.

## State

| | |
|---|---|
| `python -m ugm.labels` | ✅ the write census, and `reads` for the read census |
| `python -m ugm.leak` | ✅ the harmony invariant for frames, containment form |
| `ugm/fact.py` | ✅ positional members; `goal`, `conflict`, `criterion`, `driver` and `rules/holds.mf` all on it |
| constraints stored as members | ✅ **green** — `266 checks, 0 FAILED`. The five reds were real and were closed by `fe0d754` (`rules/holds.mf`) |
| the ATTR census | ✅ `python -m ugm.labels attrs` — and it **reversed the expectation**: the conversion target is **0.06%** of attribute reads |
| world relations as hubs | not started |
| attributes as `attribute(s, p, v)` | not started — shape settled, cost unmeasured |
| attributes out of the substrate | not started — `kind` → type edge, scalars by content, `eprops` gone |
| ordered/unordered declared | not started |
| signed membership + `retract` | not started |
| `same_as` as a fact node | not started — `mapping` still uses `original` / `image` role labels |

**Resolved** — the encoding is **(iv), the hub**, decided on **nested reification** and recorded in
[harmony.md](harmony.md) along with the flip from (iii); the relation is the node's **type**, not member
0, and positions number **from 0**; **attributes take the same shape** and the substrate therefore keeps
**no attributes at all**; **values are nodes** and qualifiers are shared, with the per-fact node the
thing that keeps sharing from being the (ii) leak; **which property vocabulary a domain uses is a KB
decision**, and two KBs disagreeing is harmonization's authored bridge rather than a defect in the
shape; **no settling and no interning** — a cache of a derived value is a TMS, and *an index over what
was asserted is storage while a cache of what was derived is not*, so **equality is by content,
computed**, never by node identity; **`absent` is the frame mechanism** (deleting what a previous frame
held), never a claim that something is false; `before`/`after` are a **convention** with names declared per relation, not role labels; a
proposition is **not** an assertion; `participant` **stays above the horizon** (it embodies a positional
convention, which must remain an argument — the admissibility rule decides it, not the call cost);
**derived order is not built** — a consumer wanting chronology sorts by the scalar explicitly, so the
ordering key is named in the derivation instead of implied by storage.

## ⚠⚠⚠ Where this could be wrong

*"Too good to be true"* is the right reflex. Five places it is not yet earned:

1. ✅ **RESOLVED, AND THE SHAPE IS NOW WRITTEN — attributes become propositions too**, as
   `attribute(subject, property, value)` with values as shared nodes. See §*Attributes are the same
   shape*, which also carries the consequence that follows from it: the **substrate keeps no attributes
   at all**. ✅ The cost was recorded here as the largest in the arc and unmeasured; it is now measured
   (`python -m ugm.labels attrs`) and **the expectation reversed** — attributes are the largest
   population and the smallest traffic, with the conversion target at **0.06%** of attribute reads.
2. ✅ **MEASURED, and then settled structurally.** *"Show me where it happens"*: over the whole suite,
   **61 of 3,194,178 assertions re-assert an existing `(src, label, dst)` — 0.002%**, of which 59 are
   `pending`. ⚠ The figure does not transfer, because the new shape *creates* the multi-minter
   situation: a goal requiring `a on b`, a rule asserting it and a query asking about it are three call
   sites, and if they mint different nodes then `holds` compares against the wrong one and **the goal is
   simply never satisfied** — a silent non-termination rather than an incoherent retraction. ✅ **Closed
   by deciding against interning**: comparison is **by content, computed**, never by node identity, so
   two mints of one proposition are harmless rather than incoherent. See §*No settling, no interning* —
   the alternative was a write-time dedupe index, which is a cache that has to be invalidated.
   ⚠ Scalars are content-*identified*, but that is forced by having no attributes and maintains nothing.
3. ✅ **RESOLVED — all machinery traverses "who said that", uniformly.** No special case, no separate
   path for asserted-versus-derived. ⚠ The regress still needs a stated floor: at the meta level
   existence *is* assertion, because the journal records who wrote what and that record is claimed by
   nobody. **So *not a logician's blackboard* is true of the domain and false of the substrate** — the
   same shape as `precedence.seal_rule`'s *the last stage must be total*, and better said out loud.
4. ⚠ **Deliberately deferred: performance is a separate concern.** World-relation reads measured under
   2% of a *Sussman* run, but that is planning-shaped and attributes are not counted. Natives and
   indexes are the levers if it ever bites. ⚠ Recorded so the number is not later quoted as a clearance.
5. ⚠ **None of the shape is novel, and that is not a defect but it bounds the claim.** Reified relations are
   RDF reification, Davidsonian event semantics, n-ary relationship nodes, hypergraphs, and Datomic's
   datom-plus-transaction. Each rediscovery meets the same three walls — read cost, query complexity,
   and the *n*-ary role problem. What would be new here is not the shape but the **residue** carried on
   it, and per [comparison.md](comparison.md) that remains a hypothesis until the system reasons
   differently *through ordinary reasoning*.

## ⚠ Pattern matching becomes a join

*All blocks on the table* is `g.sources(table, "on")` today; under hubs it is *facts mentioning the
table*, filtered by relation and position. `fn.select` is already noted as quadratic in applicable
bodies, and rule matching runs on the search's hot path.

**Index first, and it is probably enough.** A join is only expensive if you scan. A maintained index
keyed by `(relation, position, participant) → facts` turns it back into a lookup plus a small
intersection — the `workbench.index` pattern verbatim, *an index above the horizon and the mechanism
below it*, which took one check from 155 s to 5.1 s the last time it was applied.

⭐ **RETE fits this engine unusually well, architecturally.** Its premise is that change is small
relative to working memory, which is exactly what sparse frames established (*cost follows change, not
the size of the world*). Rule conditions are patterns, the world arrives as deltas, and persisted
partial matches are *reasoning that has been done stays done* in its strongest form.

⚠ **Two reasons not to reach for it.** RETE assumes **one** working memory and this engine branches —
a network per frame is expensive precisely where frames are cheap, and a network carrying context on
every token is the alternative; the prior art is ATMS-integrated RETE, with TREAT and LEAPS trading
memory back for recomputation. And **the evidence says matching is not hot**: the last time it was
suspected, the `_covers` probe measured it at **0.6 ms across the whole suite** and cancelled the
precompute it was meant to de-risk.

So: **index → measure → RETE only if a measurement demands it**, and if it does, start from the
ATMS-integrated variants, because branching is the hard part rather than matching.

⚠ Background/incremental maintenance is architecturally available — one outer loop, *nothing
uninterruptible* — but a materialised view needs invalidation, and invalidation is a TMS, which is a
larger commitment than RETE.
