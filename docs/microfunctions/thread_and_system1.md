# Thread, System 1, and bottom-up type recognition — design

**Status:** §1 **BUILT** (`thread.py`); §6 steps 1–4 **BUILT** — the outer loop runs **end to end**
(`goal.py`, `driver.py`, `intake.py`; suite at 116/0); §5 **BUILT** (`types.recognize`) and its recorded
drift defect **FIXED** (`types.tagged_as`). Only **§§2–4, System 1 itself, remain designed-only.**
See `HANDOFF.md` §5b–§5i.

⚠ **The threshold has been MEASURED, 2026-07-31, and it has not arrived — see `HANDOFF.md` §5l.**
`proposals` runs `is_a` over every mapping × every parameter, so world content that can bind to nothing
still costs: 200 inert nodes bought a **57× enumeration cost and zero extra proposals**. That is genuinely
the shape System 1 addresses (bounded neighbourhood instead of whole-frame scan) — but §5b below already
names a cheaper lever for exactly it (**index declared types by their required labels**), and that should
be tried and re-measured first. ⚠ The measurement also found the search was **irreproducible** — the copy
order fell out of a `set` of node ids — which had made an *apparent* capability wall at 5 blocks. With that
fixed the guidance is optimal (n blocks → n−1 imagined states), so the case for System 1 got weaker, not
stronger.

⚠ **And System 1 turned out to be an OPTIMISATION, not a capability** — at this scale. The loop plans,
acts, detects divergence and replans without it; `driver.relevance` does the candidate ordering this design
imagined System 1 doing, and needs none of the neighbourhood/radius question resolved. It becomes
load-bearing only when the world is too large for `driver.proposals` to enumerate at all — a real threshold,
but a long way from the toy. §6's ordering was right for the wrong reason.

⚠ **One thing the end-to-end changed about §6's ordering:** System 1 was to come last because of its
unresolved measurement question, and that held — but the loop turned out **not to need it at all** to work.
The driver tries proposals in declaration order and still solves a three-block tower. So System 1 is an
*ordering* improvement over a working loop, not a prerequisite for one, which is a much safer place to
build it from. Also learned: backward chaining cannot express *repetition* (one declared return type per
function), so repetition comes from the loop — `plan.py` and `driver.py` answer different questions.

Written 2026-07-31, after the replanning-on-divergence work (`HANDOFF.md` §5a). Every quantitative claim
below was measured; the probe is reproduced in §7.

**What building §1 confirmed, and the one thing it corrected.** The design argued for backward-linking on
the grounds that `reachable` is outgoing-only, so world nodes would not drag history into a workbench copy.
⚠ **That argument does not actually discriminate** — nothing in the world points at the thread either way,
so both link directions are safe for the copy boundary. The real justifications are the two that survived
contact: stepping back from an entry is O(1) rather than an index lookup, and **the reason a step followed
another is a property of the transition**, which only the `prev` edge can carry. The container's ordered
edge and the `prev` chain being two views of one order is a genuine redundancy, accepted deliberately and
guarded by `check_the_two_orderings_cannot_disagree` — a test guarding a discipline a *human* must follow
(only `_append` appends), which is the kind that earns its place.

---

## 0. What this actually answers

`microfunctions/` has `plan.py` (chains), `workbench.py` (imagines), `execution.py` (replays) and
`selection.py` (ranks) — and **nothing that invokes any of them.** There is no outer loop. The `ugm/`-era
decision was to replace `run_bank`'s blind fixpoint with an outer-loop metaprocedure, and that was never
carried across. So this is not a feature on top of the engine; it is the driver the engine has been missing
since it started, and it should land ahead of everything in `HANDOFF.md` §5.

Three pieces, in dependency order: **the thread** (materialised short-term memory), **System 1** (bounded
associative lookup, tapped during planning), and **recognition** (types found bottom-up rather than
asserted).

---

## 1. The thread

**What it is:** a materialised, navigable record of *what we just did* — short-term memory as ordinary graph
data. This closes a real gap: `Focus` is a Python object whose own docstring says it "holds no graph state
itself", created fresh per call and discarded. So attention is currently the one thing in this system that
is **not** homoiconic. In a project whose claim is that a rule can reason about a rule, a system that cannot
reason about where it has been looking has a hole in exactly the place it advertises.

### 1a. What goes on it, and what does not

Two entry kinds only:

* an **attention shift** — attention was deliberately placed somewhere;
* a **microfunction application** — a function was applied.

⚠ **Not every instruction.** `Focus.move` executes inside every microfunction body; logging those would
record ISA-level navigation, which is machine noise rather than reasoning, and would swamp any walker. The
grain is *deliberate placement*, not *pointer arithmetic*.

### 1b. An application entry IS the `application` node

`application.py` already mints a node carrying function + bindings, and `episode` already holds them on an
**ordered** `step` edge (the turn counter was deliberately deleted when ordering became native). If the
thread mints its own record of the same event there are two records of it, and every reflective function has
to consult both — the failure the composability principle names.

So **the thread is `episode` extended**, not a new mechanism beside it: same node, plus attention-shift
entries, plus `prev` links, plus cross-links. This has a side payoff — `compile_episode` already learns
procedures by reading episodes, so a richer record feeds learning at no cost. Its recorded limit
(multi-argument replay, "a real question about *analogy*") is *plausibly* helped by attention shifts, since
the shifts record how the system moved between the arguments. Marked speculative on purpose; check it, do
not assume it.

### 1c. Backward-linked, and the direction is load-bearing

Step N points at step N−1. Walking forward is then a reverse-index query (`g.sources(step, "prev")`), which
is O(1) — so both directions are cheap and only one is stored, per the standing discipline against asserting
what the structure entails.

The direction is not arbitrary. `reachable` traverses **outgoing** edges, so backward-linking means
`reachable(world_node)` never drags history into a copy, while `reachable(step_N)` deliberately yields the
whole past. The other direction would make every workbench copy unbounded.

⚠ **Nothing in the world may point at the thread.** A thread entry points *at* the nodes it concerns and is
never pointed at by them — the metadata direction invariant, already enforced by
`check_metadata_is_never_pointed_at_by_structure`. A single convenience edge the other way turns every
workbench copy into a copy of all history.

### 1d. Edge attributes carry the *why*, and one of them cannot be pointed at

Edges here are labelled **and** carry a sparse attribute set — `graph.link(src, label, dst, **props)`,
stored in `eprops` only when props are actually passed, exactly as node attributes are sparse. Three
consequences for this design, one of them a constraint:

* **An attention shift records its reason on the `prev` edge**, not as a separate node and not as a second
  log entry. This is what keeps §1a's granularity rule affordable: "why attention moved" is a property of
  the *move*, so recording it costs nothing structurally and does not tempt anyone into a second entry kind.
* **Association strength / decay, if ever needed, is free.** §3 argues the region rule makes weighting
  unnecessary and says not to add it before measuring. Worth knowing that if measurement does demand it, the
  substrate already carries it — the lever exists and costs no substrate change.
* **⚠ An edge property is not addressable.** `eprops` is keyed by `(src, label, index)`, and indices shift
  when edges are inserted or removed (`_reindex`, guarded by `check_insert_shifts_edge_properties`). The
  properties correctly follow their edge, but there is no stable *address* for one. So anything that must be
  **pointed at** — a hypothesis about a link, a conflict between two links — cannot live as an edge
  property. That is the same reasoning `application.record` already gives for making a binding its own node
  ("so that a binding can itself be pointed at"), and it draws the line cleanly:

> **Ride on the edge what merely describes it; mint a node for what something else must point at.**

### 1e. Cross-links are the point

Episodes today are ordered but **flat**: nothing can say "this step is here because of that goal forty steps
back." Linking distant thread points is what makes reflective microfunctions writable, and it is the missing
piece behind the recorded regression in `HANDOFF.md` §5 item 2 — conflict detection was said to need "no new
mechanism, only writing them", which was slightly optimistic: it needs the record to be *addressable*, and
it is not yet.

Thread-walking microfunctions are **pointed at the thread** like any other microfunction is pointed at its
arguments. Attention is *recorded on* the thread; it is not *read from* it by ordinary functions. That
distinction is what keeps `function.invoke`'s fresh-focus isolation intact — a global cursor that functions
read would reintroduce the ambient-context defect the whole repoint exists to remove.

---

## 2. Three regions, not two — measured

The exploration feeding System 1 must skip scaffolding. It cannot do so by marker (labelling error) or by
node kind (the composability principle's "guards yes, kinds no"). It turns out not to need either: the
boundary is **already structural**, and the probe measured exactly where it falls.

`reachable(g, "root")` on a graph holding a car, a workbench with one step, and an episode with one
application:

| region | kinds | how it is identified |
|---|---|---|
| **world** | `root`, `chunk`, `body`, `wheel` | forward-reachable from `root` |
| **library** | `function`, `type`, `instr`, `param`, `requires`, `requires_attr` | not root-reachable, but not scaffolding either |
| **scaffolding** | `workbench`, `frame`, `mapping`, `transformation`, `episode`, `application`, `binding`, `arg` | not root-reachable |

**⭐ The finding that changes the design: there are three regions, not two.** "Not root-reachable" is not the
same as "scaffolding" — the *library* is outside too. That is right for association over world content
(you associate over things, then separately match type specs against them), but a rule written as
"root-reachable = legitimate" would silently make functions and types invisible to System 1, which is wrong
for any policy that wants to associate towards *what could be done here*.

**Backward steps genuinely leak, measured.** One backward step from the car reaches
`binding`, `mapping` ×2 and `workbench` — via `mapping.original → car` and `workbench.subject → car`. So the
rule is needed rather than merely prudent. Forward steps need no rule at all: by the direction invariant,
metadata points inward, so **outgoing traversal cannot reach scaffolding**. The whole region rule is
therefore a rule about *backward steps only*, which is a much smaller thing to get right.

**Cost:** one `reachable(g, "root")` per System-1 invocation, cached for the duration of that walk. Sessions
are session-sized by design, and this is measurable rather than guessed.

---

## 3. The radius

The tension, stated plainly so the resolution is not mistaken for an arbitrary choice:

* **Outgoing-only is bounded but too weak.** From a car you reach its wheels, never another car. Association
  *is* the sideways move; without backward steps there is no System 1, only structural descent.
* **Backward steps break the bound.** "Real things hang off `root`" makes `root` a high-degree hub: one
  backward step from most world nodes reaches it, one forward step from it reaches everything, and radius 3
  becomes the whole world. "Think harder = expand the radius" stops being a dial.

**Resolution:** backward steps are permitted only into the **world** region, and `root` itself is not
traversable — it is a container, not a fact about anything. That keeps association real (sibling cars are
two steps apart via their shared parent) while keeping the neighbourhood bounded, and it needs no decay
function, no edge weights, and no tuning. If measurement later shows hub nodes other than `root` causing the
same blow-up, degree-aware refusal is the next lever — **not before measuring.**

Radius is the **think-harder dial**, per the precedent already in the book chapter on `max_rounds`: a wider
radius is more candidates and more time, and exhausting it is an honest `UNKNOWN` rather than a wrong answer.

---

## 4. System 1: a privileged *primitive* plus a declared *policy*

The proposal was a "special function that does not follow the normal rules of microfunctions." It should be
split, and the reason is recorded rather than aesthetic.

⚠ **It must not be Python.** `metaprocedure_model.md` records this exact mistake being made and corrected:
a mechanism deriving reasoned-over state was moved into Python, and that broke `suppose()`'s ability to
reach it hypothetically. If System 1's exploration is a Python special case, then no microfunction can
suppose a different radius, inspect why an association was made, or learn a better strategy — and "think
harder = expand the radius" is precisely a dial the system should be able to turn on *itself*.

The split follows the recorded mechanism/policy separation and the three-way rule classification:

* **Primitive (fixed, like `SPREAD`):** one ISA op doing the bounded, region-respecting walk. The ISA
  already has `BACK` and `SPREAD`, so the vocabulary mostly exists; what it lacks is the region rule and the
  radius bound. Building the allowed-region set is a set computation, which is why this half is a primitive
  rather than an ISA program.
* **Policy (declared, privileged data):** what to do with the candidates, how wide to go, when to widen.
  Privileged in that it may invoke the primitive; still ordinary data, so it can be inspected, supposed
  about, and rewritten by a rule.

**When it is tapped.** During **planning** only, invoked explicitly by a microfunction, like a tool. During
**execution** the system follows the plan and does not consult it. This is what keeps the repoint intact:
a function you *call* is not a trigger loop, and candidate generation feeding `selection.py` is exactly the
role that module was left holding when planning became the control flow.

⚠ **One place this will bite.** During planning the thread head points at *workbench* nodes. Expansion from
there reaches mappings, frames and copies unless the region rule holds — which is the bug
`types.instances` records in its own docstring ("planning about the products of planning"), reappearing
where its fix does not apply, because that fix was "enumerate from root" and here we deliberately do not
start from root. The region rule of §2 is what has to carry it.

---

## 5. Types are recognised, not declared

### 5a. ⭐ It is already free — measured, not assumed — **BUILT 2026-07-31** as `types.recognize`

Typing here is *already* structural and dynamic: `is_a` is `not violations(...)`, computed from current
structure, and `declare_type`'s docstring already states the consequence ("checkable at any moment rather
than being a historical claim"). What is missing is only the **direction**. Every existing entry point is
top-down — `is_a(node, name)` asks about a *named* type, `instances(name)` enumerates for a *named* type.
Nothing asks the bottom-up question.

That question is five lines, and the probe confirms the interesting properties fall out rather than needing
mechanism:

```
recognize(car)       -> ('car',)
after service        -> ('car', 'serviced_car')
after wash           -> ('car', 'serviced_car', 'washed_car')     multi-type, free
after losing a wheel -> ()                                        de-recognition, free
```

Multi-type is not a feature to add — it is what a set of independent structural predicates already does.
De-recognition needs no invalidation because nothing was stored.

### 5b. ⚠ The cache already exists, and it already drifts — **FIXED 2026-07-31**, see `HANDOFF.md` §5i

`types.tag` stamps `is_a` on the node, and `application.generalise` reads that attribute as **authoritative**
when choosing parameter names and types. Measured:

```
cached tag says: car | structure says: ()      <- after removing a wheel
```

So the proposed cache is not a new risk; it is a live one. And an uninvalidated type cache is the labelling
error the handoff already records under a different name: it asserts what the structure entails, so it
drifts, and it converts "satisfies the schema *now*" back into a historical claim — the exact thing the cast
model was designed to eliminate.

**The rule that makes a cache legitimate here.** Measured costs: one `violations` check against a *named*
type is ~25µs; `recognize` scales linearly in the number of declared types. So **the search over all types
is the cost, and the individual check is not.** Therefore:

> Cache the *candidate set* — which types are worth testing — and **re-validate on read**. Never let the
> cached name be the answer.

That keeps recognition cheap (skip the search), keeps it honest (the structure still decides), and drift
becomes impossible rather than merely unlikely. The `type` edge to a named node is the right shape for the
cache; what must change is that nothing treats it as authoritative — including `generalise`, which is a
**bug to fix while doing this**, not a new concern.

The second lever, if measurement demands one: index declared types by their required labels, so a node
without a `wheel` edge never gets tested against `car`. Not before measuring — the current type counts make
it irrelevant.

### 5c. Open class, and that is correct

Recognition offers no guarantee of finding everything, and should not pretend to. That matches how this is
supposed to work — realising that what you are looking at *is* a car is an event that may or may not happen,
and may happen late. A background pass recognising regions near attention is the right home for it, and the
honest failure mode is "did not notice", not "concluded wrongly".

---

## 6. Order of work

1. **The thread**, as an extension of `episode`: the two entry kinds, `prev` links, cursor microfunctions,
   cross-links. Everything else stands on it.
2. **Fix the live drift** in `generalise`/`tag` while the reasoning is fresh (§5b) — it is a small change and
   it is a real defect today, independent of any of this.
3. **`recognize`**, bottom-up, uncached, with the re-validate-on-read cache only once something measures slow.
4. **The outer loop**: intake mints a goal → thread grows → planning drives.
5. **System 1**: the region-respecting primitive, then the declared policy — last, because it is the only
   piece with an unresolved measurement question.

## 7. Open questions, stated rather than buried

* **Does the thread interleave imagined and real work?** Planning is itself something the system *did*, so
  workbench steps presumably appear on the thread as ordinary entries pointing at frames. That keeps one
  record and keeps the thread linear while the workbench stays the branching structure. Believed, not
  checked.
* ~~What does an attention-shift entry point at — the node, or a (node, reason) pair?~~ **Answered by §1d:**
  the reason rides on the `prev` edge as an edge property, so it is neither a second entry kind nor a
  separate node. What remains open is only whether a reason is *always* available to record, or whether some
  shifts are honestly reasonless.
* **Which cross-links need to be nodes.** §1d gives the rule (point-at-able ⇒ node), but not the census.
  `because` is probably a node — conflict detection will want to dispute one. Cheap ones may stay edges.
* **Hub nodes other than `root`.** The radius rule assumes `root` is the only pathological hub. Unmeasured.
* **Whether radius is even the right dial**, versus number-of-candidates or time. Radius is the most
  legible; it is not obviously the most useful.

## Appendix: the probe

`docs/microfunctions/probe_thread_and_system1.py` — bottom-up recognition, the three-region measurement,
backward-step leakage, and the cost figures above. Run it from the repo root:

```
PYTHONPATH=. python docs/microfunctions/probe_thread_and_system1.py
```

Every number in this document came from it; nothing here is estimated. These findings should become
`selftest.py` checks as the corresponding pieces get built — in particular the drift in §5b, which is a
defect in the code *today* and deserves a check of its own regardless of whether any of this design lands.
