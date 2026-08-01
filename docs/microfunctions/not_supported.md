# What cannot be said — a catalog of capability gaps

**What this is for.** We will never understand all of a human language, and that is not the interesting
claim. The interesting claim is the small one underneath it: some expressions fail because a *parser* is
missing a form or a *KB* is missing a word, and some fail because there is **nothing in the engine that
represents or manipulates the thing at all**. Only the second kind is a gap in this sense. This file
catalogs those, and — just as importantly — records the expressions that *look* like gaps and are not.

**The method, which is the project's standing one.** `baroque-vs-fundamental`: *paraphrasable without
changing belief = baroque; the language model absorbs it.* So for each expression the question is never
"does the parser accept this English", it is:

> **Can the existing primitives express it after paraphrase, and does the paraphrase still track the world?**

Three verdicts, and only the last is a gap:

| verdict | means |
|---|---|
| **SUGAR** | expressible today, perhaps awkwardly, and it stays correct when the world moves |
| **KB** | needs vocabulary or a computed attribute, not machinery |
| **CAPABILITY** | no arrangement of what exists represents or manipulates it |

⚠⚠ **A paraphrase that merely PARSES is not a paraphrase.** Every SUGAR verdict below was made to answer
**before and after the world changed underneath it**; a form that is accepted and then means the wrong
thing is worse than a refusal, and this codebase has caught that exact failure four times.

⚠ **This catalog is measured where it says MEASURED, and argued where it says ARGUED.** The standing
lesson from §6e and `closed_class_rechallenged` is that *every claim in this project that got checked came
out weaker*, so an unmeasured entry should be read as a hypothesis about a gap, not as a gap. The probes
live in the session scratchpad (`probe_gaps.py`, over a real file KB that lists, stats and deletes actual
files); anything below marked MEASURED is that script's output.

---

## 1. NOT gaps — the things that look missing and are not

These matter more than the gaps, because each is a thing somebody would otherwise have built.

### ⭐⭐ Universal quantification over a named edge — **SUGAR** (MEASURED)

*"all the files are measured"* is refused directly, and is expressible today by the classical ¬∃¬ route:

```
type unmeasured_file:        type fully_measured_dir:      goal all measured:
    kind_of = "file"             is a dir                      d is a fully_measured_dir
    measured != true             has no file each a unmeasured_file
```

Measured: `False` with none measured, **`False` with all but one measured**, `True` when the last one is —
which is the key that makes it a universal rather than an existential, and it works as a goal, not merely
as a predicate. The mechanism was already there: `types.fails` **counts matching targets** against a range,
so `has no <label> each a <negated type>` says *no target is like that*, i.e. *every target is not*.

⚠ **Its real limits, which are the honest gap inside the non-gap:** the population must be the targets of
**one named edge from one node** — bounded, reachable, named. There is no universal over *"every file
anywhere"*, and the negated type has to be declarable, which is easy for an attribute (`!=` exists) and
not available for a negated *structure*.

⚠⚠ **AND IT IS SUGAR FOR CHECKING ONLY — the planning half is missing, measured.** Against
`d is a tidied_dir`, even a *singular* action that would close it scores **band 1**, where the same action
against the equivalent singular constraint scores **4**. `goal.unmet` can say *that* a universal is false
and never *which members* make it false — which is §5d's founding defect (*"a goal that can only answer
yes/no forces blind search"*) reappearing one level up. Same split §6h found for transitive reach. See
`plural_step.md` §1, and note the fix is independent of plurality.

### Cardinality and emptiness — **SUGAR** (MEASURED)

*"there are at most two files"*, *"there are none left"*. `has at most 2 file`, `has no file` in a `type`
block, then `d is a small_dir` as a goal. Measured to flip exactly when the count crosses.

### Comparing two named individuals — **SUGAR, at the cost of a minted node** (MEASURED)

*"report.txt is bigger than notes.md"* is refused in a goal, and works as a `Rel` inside a type once a node
is minted to hold the pair — measured true, then false when the pair is re-pointed. This is `HANDOFF.md`
§6's known limit stated from the other side: *a type constrains ONE subgraph, and two parameters are two
subgraphs with no node above them to hang the demand on.* The mint **is** that node.

⚠ Worth keeping as a middle category rather than filed under SUGAR without comment: the paraphrase changes
the graph. That is fine for a question asked once and wrong as a habit.

### *"if X then Y"* — **SUGAR for what to DO, CAPABILITY for what must be TRUE** (MEASURED)

A method's `when <type>` guard carries the condition, so *"if it has been listed, measure the files"* is
authorable today. What has no form is a **conditional goal** — *"make it so that if X then Y"* — because a
goal is a set of constraints that must all hold, and there is no way to make one contingent on another.
See §2.

### *"prefer the smaller files"* — **SUGAR via a threshold type, and the sugar is weaker than the phrase**
(MEASURED)

`prefer small ones: action measure / when small_file` is accepted, with `type small_file: size < 200`.
⚠ But that is a **band, not an order**: every file under the threshold ranks alike. *Smaller* — a
preference that reads a value and orders by it — is not expressible, and `guideline.py` is explicit that
what it composes is `band + offset` where the offset encodes *declaration order*. So the phrase is half
sugar and half gap, and lumping it in either direction would be wrong.

### *"was it bigger before?"* — **SUGAR for observed attributes only** (MEASURED)

`memory.sightings` answers it: measured `(120, 620)` across two real `stat` calls. ⚠ Two limits, both real:
only for an attribute **seen through `dispatch.service` with `record_on`**, and only for **attributes** —
an absent edge has nowhere to hang a sighting, which is `HANDOFF.md` §9 item 3.

### *"which files are big?"* — **SURFACE ONLY; the capability exists** (MEASURED)

`types.instances(g, "big_file")` answers it. No CNL verb reaches it — §6i shipped `what` / `where` / `when`
for *one named thing*, and the plural wh-question ("which") was not among them. That is a verb, not a
capability, and it is the cheapest item on this page.

### *"files ending in .tmp"* — **KB** (MEASURED)

There is no string operator (`VALUE_OPS` is `== != < <= > >=`). A microfunction that sets an `is_tmp`
attribute closes it with no engine change, which is what makes it KB rather than capability. Adding
`starts_with` / `ends_with` / `contains` to `VALUE_OPS` would be a convenience, and should be argued as one.

---

## 2. The real gaps

### ⭐⭐⭐ G0. THE ENGINE HAS *act* AND *check*, AND NO NOTION OF *find* (MEASURED)

**This supersedes the first version of G1 below, which was wrong in an instructive way.** It said there is
no way to denote a set. There is — a machine with in-graph control flow builds one today, with no new
opcode. Measured, on the file KB:

```
fn newest(d: dir) -> file:          # a loop over `file`, keeping the greatest mtime
fn big_ones(d: dir) -> selection:   # NEW a `selection` node, LINK each member into it
```

* `newest` returns **the right node** — a denotation, computed;
* `big_ones` returns **a set**, as an ordinary node with `member` edges;
* both are **provably pure** (`query.is_pure`), so a question may run them — while `list_dir` is not,
  because it dispatches.

So the computation is not missing. **Two other things are, and both follow from one cause.**

**⚠⚠ 1. A finder is INVISIBLE TO THE PLANNER, and confidently so.** `driver.establishes(g, "newest")`
returns `effects=()` with `unknown=frozenset()` — *"I read the whole body and it makes nothing true."*
That is correct and useless: `driver.relevance` scores a proposal by what it would make true, so a
function that makes nothing true can never be proposed as a step toward anything. Note this is **not** the
`unknown` case §5k fixed for navigating operators — there the reader could not see; here it sees clearly
and there is nothing of the right shape to see. Compare `big_ones`, which does report
`mint selection` + `link member` — because it *writes*. A pure selector writes nothing at all.

**⚠ 2. The surface cannot name what a machine yields.** `newest(d).measured = true`, `the newest…`, and a
reader body naming `newest` are all refused. So the machine exists and nothing can point at its result —
`composability-principle`'s unreachable island, exactly.

**⭐⭐ The cause, and it is one sentence.** This engine models **acting** (a function whose body changes
the world, read by `establishes`) and **checking** (a type, a constraint, a predicate). *Finding* — an
operation whose whole point is to yield a **referent** rather than to make something true — has no slot in
either. That is why the gaps cluster where they do: nearly everything this catalog files as CAPABILITY is
an expression that **identifies something**, and identification is the verb the engine does not have.

⚠ **And `find` sits astride the look/act boundary, which is why it cannot simply be a helper.** *Which
file is newest* is answerable from the graph only if the files have been stat'd; otherwise it is a
question about the **disk**, and answering it means planning a look. `require_known` (*go and look*) and
the unbuilt `SENSE` verb are the nearest existing things, and both are about **attributes**, not
referents. So a finder is sometimes pure and computable during planning, and sometimes a step that must
itself be planned — and nothing today distinguishes the two.

### ⭐⭐ G1. No way to describe rather than name (MEASURED — read G0 first)

Everything the surface can refer to is either a **named individual** (`intake.resolve`, which refuses
ambiguity — *a name is not an identity*) or **one node reached by a fixed path** (`path.node_at`, which
promises one node or `None`). There is no form for *"the files bigger than 1k"*, *"the newest one"*,
*"the first three"*.

* §6h refused set-valued references deliberately and said so: a reference denoting a set breaks `node_at`
  and every caller that assumes one node. `path.via` was shipped set-shaped and left unwired, "for a caller
  that has somewhere to put one".
* **Superlatives are the sharpest case and are MEASURED as a gap:** *"the newest file"* has no form and no
  paraphrase — any paraphrase has to name the population *inside* the demand, and a schema constrains one
  subgraph while a `Rel` relates two places inside it. Neither can say *"and no other"*.

⚠ **What §1's universal shows is that this is about DENOTATION, not about quantification.** Universal
*quantification* over a bounded named edge already works. What is missing is the ability to **denote the
set** so that something can be said about it, chosen from it, or done to each of it.

⭐ This is the single most connected item on the page: *"all the files"*, *"the newest"*, *"the three
biggest"*, *"most of them"*, *"total size"*, *"the second one"*, *"half empty"* are all downstream of it.

### ⭐ G2. Disjunction (MEASURED)

*"either A or B is gone"*, *"it is a file or a directory"*. No disjunctive constraint in a goal and no
disjunction in a schema. The nearest available form — `has 1 file each a gone_file` — is a **different
claim** (*some* file is gone, not *one of these two*), which is the kind of near-miss that must not be
allowed to pass as a paraphrase.

⚠ Note the asymmetry that makes this a genuine hole rather than an oversight: **alternatives exist in
plans** (workbench forks, sibling branches, mock outcomes, `execution.resume`) and nowhere in *statements*.
The engine can pursue *either* route and cannot say *either* fact.

### ⭐⭐ G3. Maintenance — nothing says *keep it that way* (MEASURED)

*"keep the directory empty"*, *"never let the queue exceed ten"*, *"stay logged in"*. Every goal here is an
**achievement** goal: `goal.unmet` is a snapshot, `close_goal` records that something *became* true, and a
closed goal is never re-opened. The achievement form parses (`d is a empty_dir`); the maintenance form has
no expression at all.

⚠ This is not the same as a *plan* constraint. `never unstack` constrains the route to an achievement
(§5e); a maintenance goal constrains the world *after* arrival, indefinitely. And it is not the same as
re-pursuing: re-running a goal is something a caller does, not something the goal says about itself.

⭐ It is also the gap most likely to be needed by the very domain that prompted this catalog — an agent
watching a directory is doing maintenance, not achievement — and it is the one that would give
`loop.py`'s slower clock something to schedule.

### G4. Conditional goals (MEASURED as absent; see §1 for the action-side sugar)

*"if the disk is full, then the log is rotated"*. A method guard conditions **what to do**; nothing
conditions **what must be true**.

### G5. Past states of anything but observed attributes (ARGUED)

The world graph is a **single mutable state**. Frames and workbenches are for *imagined futures*, not
recorded pasts, and `memory.py` records sightings of **attributes** only. So *"what did the directory
contain last week"*, *"was it ever a symlink"*, *"undo what you did at step 3"* have no representation.
⚠ Counterfactuals about the past (*"what if I hadn't deleted it"*) are downstream of this, not separate.

### G6. Degree, and belief that is not binary (ARGUED)

*"probably"*, *"almost empty"*, *"much bigger"*. A hypothesis is a node and an outcome is an assumption,
both binary. The old engine's possibilistic band layer was deleted deliberately and nothing replaced it,
which is a defensible choice — but it means every hedged statement is currently either dropped or
promoted to certainty, and dropping and promoting are very different errors.

### G7. Beliefs held by someone other than the system (ARGUED)

*"John thinks the file is missing"*, *"they told me it was deleted"*. `memory.attribute` distinguishes
**me** from **external** — a seed, and only a seed. There is no agent-indexed belief, so a claim's *source*
cannot be represented, and *"who said so"* is unanswerable.

### G8. Aggregation over a population (ARGUED — downstream of G1)

*"total size"*, *"the average"*, *"how many are there"*. `COUNT` exists for one edge label and `ADD`
exists, and the ISA can iterate (`INVOKE … as_iteration`), so a microfunction can compute these. What is
missing is any way for a **goal or a question** to speak of them, which is G1 again.

---

---

## 2b. ⭐⭐ The theory this catalog was tested against, and where it holds

**Stated by the user:** *any gap can be covered by a suitable machine with in-graph control flow like the
one we have for planning, seamlessly integrated — and most gaps are about expressions that identify
things.* Both halves came out well, and the probe sharpened them.

**The second half is confirmed and is now G0:** the gaps cluster on **identification**, and the reason is
structural — the engine has *act* and *check* and no *find*.

**The first half holds for a precise class, and the line is worth stating because it is the useful part:**

> **A machine closes a COMPUTATION gap. Only representation closes a DISTINCTION gap.**

| gap | machine-closable? | why |
|---|---|---|
| set denotation, superlative, aggregation | **yes** — measured above | it is a computation over what the graph already holds |
| maintenance (G3) | **yes, and cheaply** | a task on the agenda that re-checks; §6f already has a watcher judging a live computation |
| conditional goals (G4) | **probably** | evaluate the antecedent, install the consequent |
| disjunction (G2) | **only if its report has the right shape** | a machine can *check* a disjunction; means-ends needs to know **which disjunct is open**, the way `goal.unmet` does. §6h's lesson exactly: *the planning half is what a predicate alone does not give you* |
| degree / hedged belief (G6) | **no** | no machine derives *probably* from a graph with no place to record it |
| others' beliefs (G7) | **no** | likewise: nothing to compute it *from* |

⭐ The two that resist are precisely the two this catalog already recommends **not** building, which is
convergence from an independent direction rather than a coincidence.

⚠ **What "seamlessly integrated" costs, measured rather than assumed** — three things, none of them the
machine itself: a **surface** that can name what the machine yields; **visibility to the planner**, since
`establishes` reads *what becomes true* and a finder makes nothing true; and a decision about **purity**,
because some finds require looking and looking is a world crossing. `PLAN`/`STEP` (§5z) is the precedent
that makes the theory credible — deliberation was made reachable from the ISA and then given a CNL verb —
and it is also the measure of the work: that arc needed an opcode pair, a report shape, and a verb.

## 3. What this catalog says to do

1. **`find` as a first-class thing (G0)** — this is the arc, and the probe says it is three pieces, not
   one: a **surface** that names what a machine yields, a way for `establishes` to report *what a function
   FINDS* beside what it makes true, and the pure/impure split that decides whether a find can run during
   planning or must be planned. The machines themselves already work.
2. **The plural wh-question (`which`)** — a verb over `types.instances`, which already answers it. The
   cheapest possible down payment on G0: a set-shaped **answer**, with no set-shaped *reference* anywhere.
3. **G3 (maintenance)** — small to state, machine-closable, and it changes what the outer loop is *for*.

⚠ Deliberately not recommended: G6 and G7. Both are big, both were touched by the old engine, and neither
has a caller. `causation-core-was-sugar` is the warning — probe before believing either is fundamental.
