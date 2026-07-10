# Related Work — Harneskills vs. the Literature

> **Companion to `docs/vision.md`.** This document positions the one-substrate vision
> against existing systems. The short version: **no single system is the whole thing,
> but almost every individual mechanism has a well-developed precedent, and a few
> systems are strikingly close in overall spirit.** The vision is mostly a
> *recombination* of established ideas, with one genuinely unusual commitment.
>
> Section references (§) point at `docs/vision.md`.

---

## TL;DR — academic positioning

Harneskills is, in one line:

> *a homoiconic, untyped graph-rewriting production system with a semiring / weighted-
> parsing semantics, in which Controlled Natural Language is the **substrate** rather
> than a compiled-away surface.*

It sits at the intersection of **AtomSpace + Conceptual Graphs + CHR + Soar + semiring
parsing**. The part that is *not* already someone's system is the **no-seam
CNL-as-substrate** commitment (§3) — keeping raw text as first-class nodes and
relocating all parsing into in-graph rewrite rules on the same graph as reasoning.

---

## 1. The closest overall neighbors

These three are worth studying as a whole, not just for one mechanism.

### OpenCog / AtomSpace (Goertzel et al.) — the nearest single match

| Match | Detail |
|---|---|
| Uniform store | A hypergraph where **everything is an Atom** (Nodes + Links): knowledge, programs, and goals all live in the one store. Homoiconic-ish, like §2. |
| Graded layer | Every Atom carries a **TruthValue = (strength, confidence)** — almost exactly the §13 "probability prior + belief degree on a fact node." |
| Weighted reasoning | **PLN (Probabilistic Logic Networks)** does weighted forward / abductive inference; the **Pattern Matcher** is the §4 LHS-pattern-binds. |
| Effort knob | **ECAN attention allocation** is a cousin of the §11 "think harder = bigger radius." |

**Where it differs (and why we are not just AtomSpace):**
- AtomSpace **Links are typed** (there is an Atom-type hierarchy) — this violates §1
  (untyped edges).
- It has a distinct surface language (**Atomese**) plus an NL pipeline
  (link-grammar → Atoms) that **parses out** into the store — this is exactly the
  §3 compile seam we abolish.

### Conceptual Graphs (John Sowa) — relations-as-nodes, exactly

CG is a **bipartite graph of concept nodes and relation nodes** joined by plain arcs.
This *is* the §1 rule "a relation is a node, never an edge label" and the
"two directed edges through a fresh intermediate node" shape (shared with RDF
reification and hypergraphs).

### Soar (Laird, Newell, Rosenbloom) — control-is-data, the cognitive-architecture match

- Uniform working memory of triples; productions fire when preconditions match.
- Crucially, **subgoaling is data**: an *impasse* creates a substate *in working
  memory*, so planning is reified rather than handled by a separate planner. That is
  the §6 "control is data, the planner is stupid" stance, reached independently.

---

## 2. Per-mechanism precedents

| Vision mechanism | Established literature |
|---|---|
| §4 computation = graph rewriting | **Algebraic graph transformation** (DPO/SPO, Ehrig et al.); tools GROOVE, AGG, GrGen.NET, Henshin, PROGRES. **Interaction nets** (Lafont) for *local* rewriting. |
| §2 homoiconic, rules rewrite rules | **Maude / rewriting logic** (Meseguer) — reflective; the meta-level lets rules manipulate rules. Lisp, for code = data. |
| §5 two layers: monotone facts + consumable control | **Constraint Handling Rules (CHR)** is almost on-the-nose: *propagation* rules (monotone, never delete) vs *simplification* rules (consume the store). Also **linear logic**: persistent `!`-resources (facts) vs linear/consumable resources (control tokens). |
| §6 token-passing, program-counter-as-node | **Petri nets / Colored Petri nets** (cited in §6); **Gamma / CHAM** (Banâtre–Le Métayer) multiset rewriting with a "fire any enabled reaction" scheduler; **Linda tuple spaces** for control-as-shared-data. |
| §6 "stupid scheduler over enabled rules" | **Blackboard architectures** (Hearsay-II): knowledge sources fire opportunistically when their preconditions appear on the shared blackboard. |
| §11 semi-naive eval, lexical indexing, stratified negation | **Datalog** (cited). Locality-bounded Rete is a variant of **Rete** (Forgy) / OPS5 / CLIPS / Drools. |
| §13 semiring confidence chaining | **Semiring parsing** (Goodman 1999, cited); **Dyna** (Eisner) — weighted Datalog unifying parsing and inference; **ProbLog**, **Markov Logic Networks** (Richardson–Domingos), **PSL / Probabilistic Soft Logic** (continuous [0,1] truth, closest to the §13 fuzzy t-norm). |
| §1 untyped / uniform store, datum-is-a-node | RDF / hypergraph reification; **Cyc** (microtheories, heavy reification). |
| §9 append-only rewrite journal | Provenance semirings for Datalog (Green–Karvounarakis–Tannen); event-sourcing / append-only logs generally. |

---

## 3. The genuinely unusual part — no-seam CNL (§3)

The one move with **no clean named precedent** is: **CNL is loaded as-is and *stays* in
the substrate — parsing is relocated into in-graph rewrite rules on the same graph as
reasoning, with no parse-out seam.**

Almost every CNL system does the opposite:

- **Attempto Controlled English (ACE)** + the RACE reasoner, **PENG**, **Grammatical
  Framework** — all *compile* CNL into a logical IR (DRS / FOL) and reason there. That
  compile step is precisely the seam §3 abolishes.

The closest *conceptual* precedents for "parsing and reasoning interleave in one
deductive engine" are **parsing-as-deduction / chart parsing as logic programming**
(Pereira–Warren; Shieber–Schabes–Pereira) and **blackboard parsing** — but even those
do not keep the raw text as first-class nodes the way §3 does. This synthesis is the
novel seam.

---

## 4. What is borrowed vs. what is distinctive

**Borrowed (and we should borrow the theory too, not just the idea):**
- Confluence / termination results and the propagation-vs-simplification discipline
  from **CHR** map directly onto the §5 monotone/control partition — worth adopting
  their terminology and confluence checkers.
- Semi-naive evaluation, stratified negation, provenance semirings from **Datalog**.
- Semiring-parsing algebra (Goodman / Dyna) for the §13 graded layer.

**Distinctive combination (the bet):**
1. **Untyped edges + relations-as-nodes** (§1) held *without exception* — AtomSpace and
   CG each give up half of this.
2. **CNL as substrate with no compile seam** (§3) — the genuinely new commitment.
3. The **graded semiring layer over crisp graph rewriting** (§13) combined with 1 and 2
   — AtomSpace has the graded layer but not untyped edges or no-seam CNL; CHR/Datalog
   have the rule discipline but no graded embeddings; semiring parsing has the algebra
   but no homoiconic substrate.

No existing system holds all three at once. That intersection is the contribution.

---

## 5. Reading list (by relevance)

1. **OpenCog AtomSpace + PLN** — Goertzel, *Engineering General Intelligence* / PLN book. Nearest neighbor.
2. **Conceptual Graphs** — Sowa, *Conceptual Structures*. Relations-as-nodes.
3. **CHR** — Frühwirth, *Constraint Handling Rules*. The monotone/consumable split.
4. **Semiring parsing** — Goodman 1999; **Dyna** — Eisner & Filardo. The graded algebra.
5. **Soar** — Laird, *The Soar Cognitive Architecture*. Control-as-data / stupid planner.
6. **Rewriting logic / Maude** — Meseguer. Homoiconic, reflective rewriting.
7. **Algebraic graph transformation** — Ehrig et al., *Fundamentals of Algebraic Graph Transformation*. The formal backbone of §4.
8. **Attempto / ACE** — Fuchs et al. The CNL baseline we deliberately diverge from (§3).
