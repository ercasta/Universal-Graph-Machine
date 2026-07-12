# Engine developer guide — extending and forking UGM

> **Audience.** You are working ON the engine: adding an ISA instruction, a tool, a reasoning firmware,
> or a new stance — not just consuming it (that is the **user guide**). Read `architecture.md` first for
> the layering; this guide walks each **extension point** in that stack, generic → opinionated, with a
> worked example and the discipline that keeps the extension faithful to `vision.md`.

The golden rule: **push new behaviour to the highest layer that can express it.** A new capability is
almost always a rule bank (data), sometimes a tool, occasionally a firmware stance, and only rarely a
new ISA instruction. Reaching for a lower layer than you need is how domain logic leaks into Python —
the one thing the vision forbids (§2, §10, §12).

Decision order when you want to add something:

1. Can a **rule bank** express it? → author `Rule` data. (Most things.)
2. Does it need an **external calculation** (arithmetic, a blob, a service, a firmware mode)? → a
   **tool**.
3. Is it a **reasoning-model opinion** (how to read absence, what to do on a cycle)? → the **stance**
   (`FirmwarePolicy`), or a new firmware module composing the existing modes.
4. Does the ISA genuinely lack a **primitive operation** every rule would need? → a new **instruction**.
   This is the last resort.

---

## Extension point: a rule bank (data — start here)

A `Rule` is `key`, `lhs` (body `Pat`s), optional `nac`, optional `rhs` (head), optional `graded`
conditions, optional `drop` (control-edge deletions), and flags (`meta`, `coref_prop`, …). A `Pat` is
`Pat(subject, predicate, object)` where a `?x` token is a variable and a bare word is a literal.

```python
from ugm import Pat, Rule, AttrGraph, run_rules
GRANDPARENT = Rule(key="grandparent",
                   lhs=[Pat("?x", "parent", "?y"), Pat("?y", "parent", "?z")],
                   rhs=[Pat("?x", "grandparent", "?z")])
run_rules(graph, [GRANDPARENT])          # forward, stratified
```

- A **strategy is declared data, never engine sniffing.** A transitive/symmetric/… relation is a
  declared property (`R is transitive`) that `cnl/rule_graph.py` turns into the rule schema — you never
  write Python that special-cases a predicate name. Coreference propagation is `same_as_rules(preds)`.
- **Reasoning rules never delete** (vision §5). Express a change of truth by adding a marker
  (`<retracted>`), read through a guarded filter — not by removing a fact.
- A **NAC over a *derived* predicate** must be stratifiable (the negated predicate's producers sit in a
  lower stratum). `stratify`/`lint_stratifiable` check this at load; a genuine cycle is rejected (or
  degraded — the stance). Author within the stratified fragment (vision §11).

To author in CNL instead of Python literals, write the bank as text and `load_rules(text)` /
`load_corpus(text)` — same result, recognized by the in-graph forms.

## Extension point: a tool (a §8 calculator)

Use a tool when reasoning must reach outside graph rewriting — arithmetic, cracking an opaque blob, an
external lookup, or invoking a firmware mode. A tool is `Tool = Callable[[Graph, call_id], set[str]]`.

```python
from ugm import call_arg, run_rules

def double_tool(graph, call_id):
    n = call_arg(graph, call_id, "arg")          # read an opaque slot (a node id)
    val = int(graph.name(n))                      # the calculator cracks it open
    out = graph.add_node(str(val * 2))
    graph.add_relation(call_id, "result", out)    # EMIT a node; never rewrite/reason
    return {out}                                  # return the touched ids so the engine re-seeds

# a rule MATERIALIZES the call:  <call> --tool--> double --arg--> ?n
CALL_DOUBLE = Rule(key="want.double",
                   lhs=[Pat("?n", "needs", "doubling")],
                   rhs=[Pat("<call>?", "tool", "double"), Pat("<call>?", "arg", "?n")])

run_rules(graph, [CALL_DOUBLE], tools={"double": double_tool})
```

The contract (vision §8/§12.5 — do not break it):

- A tool **reads opaque slots, emits nodes, returns touched ids.** It must NOT apply a rewrite or do
  domain reasoning — that belongs in rules. The engine auto-consumes the call afterwards.
- Rules decide **which** tool fires and **when** (by emitting the call at the point a value is needed);
  the dispatcher stays dumb. An unregistered tool's call is simply left for another registry.
- **Compose registries with `merge_tools(*regs)`** — it raises on a name collision, so two subsystems
  can never silently claim the same tool name. Never hand-merge with `{**a, **b}`.

The firmware itself is just a tool provider here: `mode_calls.mode_registry(rule_g, policy=…)` returns
the CHECK/CHOOSE/SUPPOSE tools, and you compose your domain tools onto it:

```python
from ugm import mode_registry, merge_tools, service_calls
tools = merge_tools(mode_registry(rule_g), {"double": double_tool})
```

## Extension point: the stance (`FirmwarePolicy`)

The firmware's *opinions* are declared data, so you can change the reasoning model without editing
`check`/`ask_goal`:

```python
from ugm import FirmwarePolicy, check, ask_goal

owa = FirmwarePolicy(negation_default="open")          # absence => UNKNOWN, not a decided no
check(fact_g, rule_g, ("has", "cellar", "mice"), policy=owa)         # -> UNKNOWN
strict_cwa = FirmwarePolicy(negation_default="closed",
                            open_preds=frozenset({"mice"}))          # per-concept OWA exception
degrading = FirmwarePolicy(on_cycle="degrade")                       # loaders won't raise on a cycle
rules = load_corpus(text, policy=degrading)
```

- `negation_default`: `"closed"` (CWA — the shipped default; `open_preds` are exceptions) vs `"open"`
  (OWA; `closed_preds` are exceptions). Read by CHECK / `ask_goal` / the CHECK mode.
- `on_cycle`: `"raise"` (reject a non-stratifiable bank at load) vs `"degrade"` (defer to `run_rules`,
  which drops the NAF rules and warns). Read by `load_rules` / `load_corpus`.

`DEFAULT_POLICY` is the shipped stance; passing nothing preserves it. Keep the stance *content-blind*:
it decides how to read absence and cycles, never *which conclusion* to prefer (that would be the
rejected smart planner, vision §6a/§12.9).

## Extension point: a whole new firmware

A "firmware" is a set of reasoning capabilities over the generic engine + reified rules. To build an
alternative one, you compose (or replace) the pieces in `chain.py`/`check.py`/`choose.py`/`suppose.py`:

- **Reuse `chain_sip`** (the demand-driven prover) — it is generic over the bank. Most alternative
  firmwares are a different *answering policy* on top of the same prover: a different verdict model, a
  different negation reading (do this via `FirmwarePolicy` if it fits the two knobs), a different
  composition of modes.
- **A new answering entry** (your analog of `ask_goal`) consumes `chain_sip` + `check`, applies your
  stance, and renders. It is a thin module — `check.py` is ~110 lines — not an engine fork.
- **Do NOT** re-derive a second matching engine or scheduler. The lesson of Phase 6.1 (two engines were
  deleted) and the standing rule: one engine, opinions on top. If you find yourself sniffing a
  predicate name in Python to pick a strategy, stop — declare it as data and read the declaration.

## Extension point: a new ISA instruction (last resort)

Only when the ISA genuinely lacks a primitive every rule would need. The opcodes live in
`ugm/machine.py` (matching core: `SEED`, `FOLLOW`, `TEST`, `JOIN`, `GRADE`, `FUZZY`, `SET`, `DUP`,
`SAME`; effects: `MINT`, `EMIT`, `DROP_CTRL`, `INTERPOSE`, `RESTORE`). To add one:

1. Define an `Instr` subclass (a dataclass of its operands). Set `is_effect = True` if it mutates the
   graph — the machine runs matching before effects, and this flag is the split.
2. Implement its execution in `Machine.run` / `run_program`: a matching op maps the incoming `State`s to
   outgoing ones (bind registers, scale the graded score via the t-norm); an effect op mutates the graph
   and returns the touched nodes.
3. Lower to it: in `ugm/lowering.py`, emit the new opcode where a `Rule` (or a reified-rule pattern)
   should use it. If it is a control primitive, make sure it respects the fact/control partition
   (`DROP_CTRL` refuses a fact edge; a new deleting op must too).
4. **Differentially gate it.** Add a test asserting the new op produces the same derivations as the
   equivalent existing lowering on a bank that exercises it. An ISA change is the highest-blast-radius
   extension — it must not perturb existing lowerings.

Respect the invariants: edges stay untyped (no op may add an edge label); the matching core stays purely
positive (negation is a match-time filter + stratification, not an opcode that searches-and-fails);
values are never indexed as identity.

---

## Discipline checklist (before you commit an extension)

- [ ] Domain logic is in **banks/data**, not Python branching on a predicate name.
- [ ] Any Python you added is **mechanism** (engine/tool/stance), not a strategy that scores *content*.
- [ ] Reasoning rules are **monotone**; only control rules delete, only control edges, token-gated.
- [ ] Tools **only emit nodes**; rules **only couple through nodes**; you used `merge_tools`.
- [ ] Negation stays **stratified**; a new bank passes `lint_stratifiable` (or the stance degrades it).
- [ ] New surface forms are **rules**, not a Python parser; unrecognized input stays raw tokens.
- [ ] You added a **test** (differential for an ISA/lowering change; a behaviour pin otherwise).
- [ ] You did **not** resurrect a deleted engine or a shape-sniffer (see `implementation_plan.md`).
