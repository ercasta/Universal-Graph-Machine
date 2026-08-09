# Defining terms — what the representation and the syntax still need

**Status: a design thread. Nothing built, and two probes come first.** Companion to
[expressiveness-and-uniformity.md](expressiveness-and-uniformity.md), which asks *can we say it at all*;
this one asks *what exactly is missing*, and answers it from worked examples rather than from a survey.

⭐ **Every item below is forced by an example**, and the examples are the ones in
[language-semantics-reasoning.md](language-semantics-reasoning.md) — *top*, *fast*, *authority*, *taking
turns*, plus *friends*. Nothing here was proposed because it seemed generally useful. That is the property
worth preserving if the list grows: **an entry earns its place by naming the sentence that cannot be
written without it.**

## The list, in dependency order

| | need | forced by | today |
|---|---|---|---|
| **1** | **a shared ORDER core** — orders as first-class named things, with their algebra stated | *taking turns*, and everything in §3 of the companion | ❌ six unrelated orders |
| **2** | **relative index over a NAMED order** — `step[i+1] by <order>` | *taking turns* | ❌ `Hop.index` is a literal into storage order |
| **3** | **the PLAN as a constrainable subject** — ⚠ preserving **prefix-monotonicity** (`SAFETY_SORTS`), and ⚠ **needs bindings on the step first** | *taking turns* | ❌ a step records `function` + `touched`, **not who filled which role** |
| **4** | **declared relation properties** — symmetric, inverse, transitive, … | *friends* | ❌ backward traversal only |
| **5** | **a reference set** — ⚠ **not** the comparator P3 owes; see the probes | *fast* | ❌ |
| ~~6~~ | ~~quantified / negative conditions~~ | *top* | ✅ **CLOSED — `has 0 above` already parses and checks.** Probed, not scheduled |

## 1–2. Order, and the semantics of indexing

### ⚠⚠⚠ Indexing today means nothing, and that is worse than it sounds

`path.Hop.index` indexes into the substrate's `(src, label) -> [dst, …]`, which is in **insertion
order**. So `step[i+1]` is a claim about *storage*, not about the world. `method.py` states it without
noticing: *"steps are an ordered edge, so declaration order is the `then` order, **free**."* ⭐ **It is
free because it means nothing** — you get an order whether or not you have one.

**So the substrate's ordered targets are a sixth unrelated order, and the only one with no name.** Worse
than the five in the companion, which at least announce themselves.

⚠⚠ **Reading an accidental order as meaningful has already caused two recorded defects here**, and a
third would be writing *taking turns* against a bare index:

* `visible` walked nearest-first, so the world's order differed in every frame — and that order is
  `proposals` order, the search's last tie-break. *Deterministic, and worse.*
* `g.sources` returns its answer **sorted by node id**, an id is a string, so the reverse index could not
  answer *the most recent*. A benchmark caught it; three checks had passed with it planted.

### The semantics an index needs — three parts

```cnl
step[i] by plan          # the order the plan lists them in
step[i] by time          # the order they actually happened in
```

1. **Which order.** Unnamed means insertion order, which is a storage artefact.
2. **What kind of order it is.** ⭐⭐⭐ **`i+1` presupposes a DISCRETE, TOTAL order with a successor
   function.** `clock.py`'s moments are explicitly a **partial** order — *"a moment may carry no scalar at
   all and be placed only by `before` edges"* — so there is no *the next moment*, and `[i+1] by time` is
   undefined in general.
3. **If it is not total, how it was linearised.** ⚠ **An unstated linearisation is exactly the `visible`
   bug**, rebuilt with better syntax.

⭐⭐ **And then `i+1` needs no semantics of its own — it inherits the named order's.** That is the
economical result: indexing is not a new design axis, it is the **first concrete consumer of the shared
order core**, which is why the core moves ahead of it in the list.

⚠ **Space is the case that shows why the syntax must force the choice.** *Next to* is a graph, not a
line; containment is a tree. Space yields an index only once a path or an axis is picked, so for space
there is no default to fall back on.

### ⭐⭐⭐ The discrimination pair that settles it

A plan whose steps alternate A, B, A, B **as listed**, executed with the two B steps reordered or
concurrent:

| indexed | verdict |
|---|---|
| `by plan` | ✅ takes turns |
| `by time` | ❌ does not |

**Same steps, same graph, different verdict** — and the behavioural form, which is the one that counts:
**the agent accepts a plan it should have rejected, and hammers twice in a row.** By the
discrimination-pair test ([expressiveness-and-uniformity.md](expressiveness-and-uniformity.md) §7) that
settles it, and note it is stated as *what the agent does*, not as *what the representation can tell
apart*. It is also the prescriptive/descriptive split of the five successors, arriving somewhere it can
be measured.

## 3. ⭐⭐⭐ Where "taking turns" lives: it is a TYPE, and its subject is the PLAN

A type is a schema over a subgraph. A plan **is** a subgraph — a node with ordered steps. So:

```cnl
type taking_turns:
    step[i].agent is not step[i+1].agent by plan
```

...and a goal says `plan is a taking_turns`. **No new machinery is required**: types already check
subgraphs, goals already carry `a is a serviced_car`, specificity ordering already exists, and
`wheel[0].rim is not wheel[1].rim` is the same shape one index short.

⚠ **The syntax above is a sketch and its one real question is where `by <order>` attaches** — to the
line, as written, or to each index (`step[i by plan]`). The second is more honest, since two paths in one
line could in principle be indexed by different orders; the first reads better. **Not settled here.**

**Why it cannot be written today** is two things, and only one is the index:

1. the relative index (§2), and
2. ⭐ **the plan is not a constrainable subject.** A goal constraint's subject is a *domain* node.
   Constraints about the plan do exist, but they are a closed set of sorts —
   `PLAN_SORTS = {never, eventually, at_most}` in `goal.py` — not *the plan is a node you can say things
   about*. Taking-turns would be a fourth, and adding a fourth is the wrong way to grow.

⭐⭐⭐ **The move is to collapse the three into one: the plan as a subject, constrained like anything
else.** `never unstack` becomes a type over the plan, `at most 3 steps` a cardinality over it,
taking-turns another type — *decompose before believing something is primitive*, and the same result as
*a construction is a criterion with a different address*.

### ⚠⚠⚠ But the three sorts are not arbitrary, and a naive collapse loses the search

Found by reading `goal.py` rather than by reasoning about it, which is the only reason it was found:

```python
PLAN_SORTS   = frozenset({"never", "eventually", "at_most"})
SAFETY_SORTS = frozenset({"never", "at_most"})   # prunable: a breach cannot be repaired later
```

⭐⭐ **That is the safety/liveness distinction, discovered independently and with its operational
consequence attached.** A safety constraint is **prefix-monotone** — *violated by a prefix ⇒ violated by
every extension* — so the search can **prune** on it. `eventually` cannot be pruned on, because an
unfinished plan has not failed it yet.

An arbitrary authored type over the plan has **no such guarantee**, so collapsing the sorts naively would
turn every plan constraint into an unprunable one and quietly cost the search what
`SAFETY_SORTS` buys. ⚠ This is the *"when a safety property is implemented by looking at the argument,
ask what it is really about"* lesson pointed the other way: here the property is real and the sort is
carrying it.

⭐ **The requirement this adds is small and the good news is that the flagship example passes it**:
taking-turns *is* a safety property — once a plan contains A,A no extension repairs the alternation. So
the collapse must let an authored plan-type **declare that it is prefix-monotone** (and ideally be
refused, or merely not pruned on, when it does not hold). That is one attribute plus an argument, not a
mechanism — but it must be in the design from the start, because retrofitting it means auditing every
authored plan type after the fact.

✅ **It pays a debt already recorded.**

[advice-over-sequences.md](advice-over-sequences.md) §4 names the
one real gap as *"a place to be said"* — this is the place. Its §3 says *"recognition and prescription
are the same predicate read two ways"* — **the type is that predicate**, read over a finished trajectory
(recognition) or over a candidate plan (checking, prescription). They are not built separately; the
*subject* is built once.

## 4. Relation properties — what *friends* actually needs

*"Paul and Bob are friends"* is **symmetry**, not coinduction: a declared algebraic property of a
relation, from a small closed family (essentially OWL's property characteristics).

| property | example | what it buys |
|---|---|---|
| symmetric | `friend_of` | assert once, read both ways |
| inverse pair | `parent_of` / `child_of` | two names, one fact |
| transitive | `before`, `contains`, `outranks` | closure without materialising |
| reflexive / irreflexive | — | refuses a degenerate answer |
| antisymmetric | `part_of` | catches a cycle that must not exist |
| functional | *exactly one father* | cardinality as definition, not check |

⭐ **This is the five-successors problem one level down.** The engine has **backward traversal** —
`^label`, `by ^next` — which is syntactic (*walk this edge the other way*). It has **no declared
inverse**: nothing states that `child_of` is the converse of `parent_of`, so a rule about one cannot see
the other. Mechanism uniformity without representation uniformity, again.

⚠⚠ **One distinction to insist on before building it.** Is `friend_of` symmetric **by definition**, or are
*Paul thinks so* and *Bob thinks so* two facts that happen to agree? Unrequited friendship exists, and the
discourse layer already represents *who says so*. Stamping symmetry on the relation makes that unsayable.
**Symmetric-by-definition and mutual-by-fact are different claims**, and the surface must make you say
which — *a synonym is a knowledge claim*, applied to relation properties.

## 5–6. The two that are not about order

**Comparison to a reference class — *fast*.** *Less time than what?* The type language compares **within
one subgraph** (`wheel[0] == wheel[1]`) and **against constants** (`>= 2.0`), never against anything
else. This is the recognition column's real blocker.

⚠⚠ **But "than a population" is the database framing, and it is the wrong one for an agent.** An agent
does not compute a statistic over all trips; it compares against **what it remembers and what it
expected**, so the reference class is agent-sized: *the trips I have made*, not *all trips*. See
[memory.md](memory.md) on sightings and attribution.

⚠⚠⚠ **This section first proposed that *fast* is the `by experience` comparator P3 already owes. The
probe says no** — that one ranks *rules by how they have fared*, this one summarises *past measurements
of an attribute*, and they read different records. See the probe results at the end.

**Quantified / negative conditions — *top*.** ✅ **Closed by probe: `has 0 above` already parses and
checks.** A cardinality of zero over a relation was expressible all along, because types take counts as
ranges. Nothing to build.

## ⭐⭐⭐ 7. Could all of this be constraints over relationships?

Mostly yes, and the exception is the interesting part.

| | as constraints over relations? |
|---|---|
| relation properties (§4) | ✅ **definitionally** — symmetry *is* a constraint on a relation |
| structure (`has 4 wheel`) | ✅ cardinality over a relation |
| *top* (§6) | ✅ cardinality **zero** over a relation |
| **order and its algebra (§1)** | ✅ ⭐ an order **is** a relation, and *transitive + irreflexive* = strict partial order; *+ total* = linear; *+ discrete successor* = indexable. **"State the algebra" turns out to mean "constrain the relation"** |
| *taking turns* (§3) | ✅ a constraint over a **composition** — `agent` after `successor` |
| cause–effect | ✅ if the event is **reified**, so pre-state and post-state hang off one node (the Davidsonian move) |
| **comparison class (§5)** | ❌ **needs a reference SET** — *less than the ones I have seen* is not a relation between two individuals, whatever the set is drawn from |

⭐⭐ **The payoff is large and structural: if everything is constraints over relations, requirement 2 is
satisfied BY CONSTRUCTION rather than by discipline.** Two representations built from the same relations
share nodes automatically; there is nothing to keep uniform because there is only one kind of thing. That
is a much stronger position than *keep the five successors related by hand*.

Three warnings, in the order they bite:

* ⚠⚠⚠ **"Everything is constraints over relations" is trivially true if you may invent relations.** That
  is the **encoding** failure from the companion's §1 arriving in its most tempting form — you can always
  add an auxiliary relation and satisfy the letter of it while building an island. The discipline is:
  **the relations must be the domain's, not minted for the encoding.** *Without encoding* is the whole
  criterion, and it applies to this proposal too.
* ⚠ **Path composition is where classical KR lost decidability** — Brachman & Levesque's role value maps.
  ⭐⭐ **The reason it does not bite is not that this engine stays inside a decidable fragment. It is that
  it is an AGENT**: it asks *does this thing satisfy this, here, now*, against a concrete finite graph and
  a budget. **Subsumption — is concept A necessarily below concept B in every model — is a question a
  theorem prover has and an agent does not.** `wheel[0].pressure == wheel[1].pressure` shows the line was
  already crossed and nothing broke. ⚠ The advice that survives is therefore not *stay decidable* but
  **do not acquire the subsumption question**, because that is what would make the fragment matter.
* ⚠⚠ **Constraints say what holds; an agent mostly needs to know what to DO — and force is not a
  constraint.** They serve **check** and **recognise** directly, **plan** only with operators alongside,
  **why** only with the derivation record. ⭐ And this project has already refused the flattening once:
  `prefer` / `avoid` can **never exclude**, deliberately; `criterion` names an action; three families
  differ **only in force**, and the surface makes you say the word *because force is about failure and
  cannot be inferred from what is written*. So the honest scope of the unification is:
  **the world can be constraints over relations; the agent's knowledge of what to do cannot**, and that
  boundary is a decision already taken rather than an open question.
* ⚠ **Declare the properties; do not compute the closures.** Transitivity for a theorem prover is a
  saturation step. For this agent it is a **walk taken when something asks** — reasoning here is
  demand-driven and *a reader records nothing*. A relation property is a licence to answer a question,
  not an instruction to materialise facts.

⭐ **And the exception earns its keep — but read it in the agent's shape, not the database's.** What
*fast* needs is a **reference set and a summary of it**, and that is not a relation between two
individuals however small the set is. ⚠ It does **not** follow that a statistics vocabulary is wanted:
per §5 the set is *the trips I remember*, and the summary is what `by experience` is already owed for. So
the two honest options are **materialise the reference as a node** — the constraint then becomes ordinary
and the *derivation* of that node is an operation that must explain itself — or admit a bounded
comparison vocabulary. ⭐ The first is the pattern this project prefers everywhere else, and it keeps the
representation answer clean: **constraints over relations, plus operations that produce the nodes those
constraints are about.**

## ✅ The three probes have been run, and they went three different ways

*Test the claim before building the fix for it.* One row of the list closed, one turned out to need a
representation change before any syntax, and one claim in this document was wrong.

### ✅ 2. *top* is FREE — `has 0 <label>` already works, so §6 is closed

All three spellings parse (`has 0 above`, `has at most 0 above`, `has 0 above each a thing`), and — the
part that mattered, since parsing is not checking — it **discriminates**:

```
a (nothing above)   is_a solo : True
b (has something above) is_a solo : False        # and gather_violations returns the node
```

**Row 6 is deleted from the list, not scheduled.** *Top means there is nothing higher* is expressible
today, and the design list is five items rather than six.

### ❌ 1. A plan step does NOT reach its agent — §3 needs representation before syntax

`extend_trace` mints a `trace_step` carrying exactly three things: `function` as an attribute, `touched`
as a set of nodes, and `after` to the previous step. **The bindings are not on it.** They live one node
away, on the *candidate*: `offer` mints a `candidate_arg` per parameter with `param` and `mapping`.

⭐ So the plan-so-far records **what ran and what it touched, never who filled which role** — and
`step[i].agent` has nothing to bind. §3's requirement is therefore bigger than the index and smaller than
a mechanism: **carry the bindings onto the step**, which already exist one hop away on the candidate that
produced it.

⚠ **A second defect found on the way, and it is on the path to taking-turns rather than beside it.**
`trace_tuple` reads the plan back as `(function, frozenset(nodes))` **tuples** — which fails *could a rule
have produced this value?* exactly as `ran` and `unbound` did in `execution.step`. Anything reasoning
about a trajectory from the surface meets this first.

⭐⭐ **And the strongest evidence for §1–2 turned up here, unlooked for.** Two comments in `search.py`,
written for other reasons:

```python
for n in sorted(touched):      # sorted: `touched` is a set, and order must not leak
for param in sorted(bindings): # sorted: a dict's order must not reach the graph
```

**The engine already defends, by hand and in two places, against an accidental order reaching the
graph** — which is precisely the argument for naming orders rather than inheriting storage order. The
discipline exists; it has no representation.

### ❌ 3. `by experience` is NOT what *fast* wants — this document was over-optimistic

§5 suggested *fast* might be the comparator P3 already owes. Reading it, that is wrong.

* `EXPERIENCE` is a **source** — `speaker(g, EXPERIENCE)` — so *experience says so* is attributed and
  ranked by ordinary discourse authority. The comparator stages are `_by_authority`, `_by_force`,
  `_by_specificity`, `_by_random` and `_by_function`; there is indeed **no `_by_experience`**, so P3's
  item is real.
* But it would rank **rules by how they have fared**, reading `application.py`'s record of what ran.
  *Fast* needs a **summary of past measurements of an attribute**, which lives in sightings and dated
  moments — `memory.py`, not `application.py`.

⭐ **Same instinct, different records, different mechanism: one comparator does not serve both.** What
they genuinely share is the premise that *the reference class is the agent's own history*, which is the
part of §5 that survives.

### What is left, in order

1. **The order core** (§1), then **the index** (§2) — which cannot be specified without it.
2. **Bindings on the plan step** (§3), before the plan-as-subject syntax is worth designing, and
   preserving prefix-monotonicity per the `SAFETY_SORTS` finding above.
3. **Relation properties** (§4) — unprobed, and the least entangled of the five.
4. **The reference set for *fast*** (§5) — now known to be its own thing.
