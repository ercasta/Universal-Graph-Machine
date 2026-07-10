# UGM — Universal Graph Machine

**A substrate for performing computation over graphs.**

UGM is a self-contained Python library that provides a label-less attribute graph
substrate, a declarative instruction set architecture (ISA) for graph computation,
and an optional Controlled Natural Language (CNL) surface for authoring and rendering.
No external reasoning engines. No embeddings. No LLMs. Pure symbolic graph
computation.

---

## Core idea

The whole system is one idea applied without exception: **everything is in the graph**.
Knowledge, rules, goals, the control flow of computation, and the source language are
all nodes in the same graph. Computation is rewriting that graph.

**Edges are typeless.** An edge is a bare, untyped connection between two nodes. All
meaning lives in nodes. Where other systems write a typed relation, UGM writes a *node*
bearing that word, wired to its arguments by plain edges:

```
paul ── is_a ── person          (three nodes; two untyped edges)
```

`is_a` is not an edge type. It is an ordinary node, matchable and rewritable like any
other. A **relation** is always a node — never an edge label.

**Nodes carry attributes.** A node holds a bundle of `(key, value, comparator)`
attributes: crisp symbolic facts (`person: 1`), graded characters (`urgent: 0.9`), and
scalar valued attributes (`name = "Paul"`, `age = 42`). Reasoning happens on attributes;
opaque blobs stay as nodes for tools to open.

**Fact and control are segregated.** `<angle-bracket>` nodes are control tokens —
working state the engine creates and destroys. Ordinary nodes are the persistent fact
layer. A rule that creates a control token leaves facts untouched; teardown is DROP_CTRL,
never fact deletion. The fact layer is **monotone**: nothing is ever deleted from it.

---

## The ISA — nine processing modes

UGM exposes a closed inventory of nine computation modes, each corresponding to a
recognisable step in deliberate reasoning:

| Mode | What it computes | Analogue |
|------|-----------------|----------|
| **SATURATE** | forward closure within a demand scope | automatic association |
| **ITERATE** | cursor over a reified collection | walking a list |
| **CHAIN** | demand-driven rule application | deliberate inference |
| **CHECK** | bounded completion with CWA verdict | looking and possibly not finding |
| **CHOOSE** | graded α-cut selection over candidates | comparing and picking |
| **SUPPOSE** | pencil/ink hypothesis scope | "what if" reasoning |
| **WALK** | fueled variable-length traversal | scouting at distance |
| **CALL** | reified tool calls folded back | using a calculator |
| **RECORD** | provenance journaling woven through every mode | remembering what you did |

Every computation the system performs is one of these, or a KB-authored composition of
them (a *procedure*). There are no other moving parts.

**SATURATE / CHAIN** are the forward and backward engines respectively. Rules are
reified as graph structure (a `<rule>` node with `rl_lhs`, `rl_rhs` relations). APPLY
walks the rule body, emitting derivations into the graph. CHAIN is demand-driven
(magic-sets), so it never over-derives.

**CHECK** answers a yes/no/unknown question with four statuses: `POSITIVE` (proved),
`ENTAILED_NEG` (negation proved), `ASSUMED_NO` (CWA: no evidence), `UNKNOWN` (open
world). The CWA is opt-in per predicate.

**CHOOSE** selects the best option from a candidate set using graded α-cut: an option
wins if it satisfies the goal at a level no other option does. Ties are retained.
Graded attributes (`urgent: 0.9`) feed directly into the selection.

**SUPPOSE** enables safe hypothesis reasoning via a pencil/ink split. Assumed facts are
written as control-scoped (`pencil`) nodes; derivations run inside the scope. On
confirmation the assumptions are committed to the fact layer (`ink`); on refutation the
entire scope is dropped. The fact layer is never tentatively modified.

---

## The CNL layer (`ugm.cnl`)

The `ugm.cnl` subpackage provides a Controlled Natural Language surface over the ISA.
Rules and facts are authored as plain English-like text files:

```
alice wants vanilla
vanilla is in_stock
alice gets vanilla when alice wants vanilla and vanilla is in_stock
```

CNL is parsed into graph structure by `load_facts` / `load_rules`, which run the ISA
forward engine over the form-recognition grammar. There is no separate parser; parsing
IS graph rewriting. Explanations render back to CNL via `explain(graph, fact_id)`.

Key CNL concepts:
- **Facts**: subject–predicate–object triples (`alice wants vanilla`)
- **Rules**: `HEAD when BODY` with `and`, `not`, graded conditions (`is very urgent`)
- **Universals**: `if BODY then HEAD` and `ADJ things are PRED` laws
- **Gradable dimensions**: declared with `X is gradable`; used in rules as `?x is very X`
- **Closed-world declarations**: `P is closed world` opts a predicate into CWA

---

## What is expressible

UGM targets a deliberately small, well-understood logic fragment:

- **Definite Horn rules** with conjunctive bodies (Datalog; least-fixpoint semantics)
- **Stratified negation-as-completion** with CWA-default bounded enumeration
- **Defeasible rules with priorities** — defaults, exceptions, overrides (no contraposition)
- **Deontic statuses** as reified ranked predicates (`forbidden` … `obligatory`)
- **Declared congruence** (`same_as`) propagated over KB-declared predicates only
- **Graded attributes** in `[0,1]` unified with the rule matching layer (α-cut)
- **Scoped hypothetical reasoning** (SUPPOSE) without possible-worlds machinery

Formal anchors are kept for correctness; general theorem proving is not the goal.

---

## Usage

```python
import ugm as h

g = h.Graph()
h.load_facts(g, """
alice wants vanilla
vanilla is in_stock
""")
h.load_rules(g, """
alice gets vanilla when alice wants vanilla and vanilla is in_stock
""")
h.run_rules(g)

# Query
answer, status = h.ask(g, "alice gets vanilla")
print(answer)   # True

# Explanation
print(h.explain(g, next(iter(g.nodes_named("gets")))))
```

The ISA engine is available directly:

```python
from ugm import chain_sip, check, choose, suppose, Graph

g = Graph()
# ... populate g ...

result = chain_sip(g, rules, goal_pattern)
verdict = check(g, rules, "alice", "gets", "vanilla")
```

---

## The rewriter oracle (temporary)

`ugm.cnl.rewriter` is the reference engine from the previous generation of the system.
It is retained as a differential-test oracle during the ISA build and will be deleted in
Phase 6 once the firmware is fully self-consistent. Do not use it in new code.

---

## Installation

```bash
pip install ugm              # core (no mandatory deps)
pip install "ugm[asp]"       # + clingo for disjunction/model-enumeration calculators
```

Pure Python, requires Python ≥ 3.8.

---

## Design philosophy

> *The whole system is one idea applied without exception: there is a single substrate —
> a graph of nodes — and everything is in it. Computation is the rewriting of that graph.
> There are no other moving parts, and crucially, no seams.*
>
> — `docs/vision.md`

The design is informed by:
- Datalog / Prolog (definite clause engines)
- Defeasible logic (Nute, Governatori)
- Magic-sets demand-driven evaluation
- Attempto Controlled English (CNL as surface, not engine input)
- Provenance / truth-maintenance traditions

See `docs/vision.md`, `docs/logic_fragment.md`, and `docs/processing_modes.md` for the
canonical design rationale.
