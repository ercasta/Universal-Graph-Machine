# Facts as nodes — the universal shape

**The design this arc is building toward.** Scored throughout against
[harmony.md](harmony.md)'s four criteria, which is the standing process rather than a flourish here:
two of the decisions below came out differently once they were scored.

## The shape

Everything that relates things is a **node with a type and members**:

```
on#7      --is--> on          the relation, as a node
on#7      --at-->  a, b       the participants, by POSITION
```

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
and `holds` is already 54% of Sussman merely by being interpreted. The answer is **settling** — the
concept exists (`query.settle`, `norm.settle`, and the standing claim that *reasoning that has been done
stays done*, which is half the benchmark against an LLM) — but what *settled* means, and what un-settles
it, has to be designed alongside this rather than bolted on. **Unbuilt and load-bearing.**

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
| constraints stored as members | ⚠ **swapped, 5 checks red, undiagnosed** |
| world relations as hubs | not started |
| ordered/unordered declared | not started |
| signed membership + `retract` | not started |
| `same_as` as a fact node | not started — `mapping` still uses `original` / `image` role labels |

**Resolved** — `before`/`after` are a **convention** with names declared per relation, not role labels;
a proposition is **not** an assertion; `participant` **stays above the horizon** (it embodies the
convention *position 1 is index 0*, which must remain an argument — the admissibility rule decides it,
not the call cost); **derived order is not built** — a consumer wanting chronology sorts by the scalar
explicitly, so the ordering key is named in the derivation instead of implied by storage.

## ⚠⚠⚠ Where this could be wrong

*"Too good to be true"* is the right reflex. Five places it is not yet earned:

1. ✅ **RESOLVED BY DECISION — attributes become propositions too.** `a.height = 2` and `a.clear = true`
   are node attributes today, outside everything above, so *when did `a` become clear, and who says so*
   was as unanswerable as under a labelled edge — and `require_attr` exists as a separate constraint
   sort because of that split. Attributes join the shape. ⚠ They far outnumber relations, so this is by
   far the largest cost item in the arc, and it is accepted deliberately: **performance is a separate
   concern**, addressable later with indexes and natives. ⚠ It does mean the census's read numbers
   understate the conversion by a wide margin, since `ATTR` reads are not in them.
2. ✅ **MEASURED — interning is a performance choice, not a correctness one.** *"Show me where it
   happens"*: over the whole suite, **61 of 3,194,178 assertions re-assert an existing `(src, label,
   dst)` — 0.002%**, of which 59 are `pending`. ⚠ The figure does not transfer, because the new shape
   *creates* the multi-minter situation: a goal requiring `a on b`, a rule asserting it and a query
   asking about it are three call sites, and if they mint different nodes then `holds` compares against
   the wrong one and **the goal is simply never satisfied** — a silent non-termination rather than an
   incoherent retraction. ⭐ But lookup by **content** rather than by node makes that a non-issue, and
   content-keyed lookup *is* interning done at read time. **A content index is needed either way; the
   only question is whether it dedupes on write.** So: not built, key recorded, revisit if it bites.
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
