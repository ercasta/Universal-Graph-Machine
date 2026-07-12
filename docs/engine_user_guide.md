# Engine user guide — building on UGM as a library

> **Audience.** You are CONSUMING the engine — building a system on top of it (the way `harneskills`
> does): load a knowledge base, ask it questions, plug in your own tools, choose a reasoning stance. You
> do not need to touch the engine internals; if you find you do, read the **developer guide**. For the
> big picture read `architecture.md`.

UGM gives you a demand-driven reasoner over a controlled natural language. You bring the domain
knowledge (as CNL text or `Rule` data) and any domain tools; UGM does the reasoning and renders answers
as CNL.

---

## 1. Load a knowledge base

Write facts and rules as CNL and load them into one graph. `load_corpus` returns `(kb, rules)`: the
substrate graph and the executable rules reflected out of it.

```python
import ugm as h

CORPUS = """
ada is a suspect
bo is a suspect
cy is a suspect
bo in library
ada is alibied
?x is innocent when ?x in library
?x is cleared when ?x is innocent
?x is cleared when ?x is alibied
?x is thief when ?x is a suspect and ?x is not cleared
"""

kb, rules = h.load_corpus(CORPUS)
```

- Facts are `S P O` (`bo in library`), `S is a O`, `S is O`. Rules are `HEAD when COND and COND …`; a
  `?x` token is a variable. `not ?x is cleared` is a NAC — decided on demand by negation-as-failure.
- A line that matches no form stays raw tokens (nothing is silently misread). Lines starting with `#`
  are comments.
- Loading does NOT forward-derive everything — reasoning is demand-driven, done when you ask.

## 2. Ask questions

`ask_goal(kb, question, rules)` recognizes the question and answers it demand-driven, materializing only
the facts the goal needs (monotone — it never deletes; pass `kb.copy()` if the KB must stay untouched).

```python
h.ask_goal(kb, "who is thief", rules)     # ['cy is thief']         — cy is the only uncleared suspect
h.ask_goal(kb, "is cy thief", rules)      # ['yes']
h.ask_goal(kb, "is ada thief", rules)     # ['no']  (ada is alibied -> cleared)
h.ask_goal(kb, "why cy is thief", rules)  # a derivation trace, rendered as CNL
```

Question shapes: `is S P O` (yes/no), `is S a O`, `does S P O`, `who P O`, `who is a O`, `why S P O`. An
existential subject (`is anyone happy`) is answered by any witness.

**The three answers an agent distinguishes** (`decision-cwa-default`): a derivable goal is `yes`; a
derivable *negative* is a hard `no`; an unprovable goal on a closed-world concept is a *defeasible* `no`
(the CWA default); an unprovable goal on an *open* concept is `unknown`. If you need the finer kind
(hard-no vs assumed-no) for an escalation policy, call `check(...)` directly — it returns the 4-status
verdict (`POSITIVE` / `ENTAILED_NEG` / `ASSUMED_NO` / `UNKNOWN`) instead of collapsing to yes/no/unknown.

## 3. Choose a reasoning stance (`FirmwarePolicy`)

The default is closed-world (absence of proof reads as `no`). Override per call — or once, threaded
through your app — with a policy:

```python
from ugm import FirmwarePolicy

# open-world by default: absence reads as `unknown` (gather evidence), not `no`
owa = FirmwarePolicy(negation_default="open")
h.ask_goal(kb, "is bo thief", rules, policy=owa)          # ['unknown'] where CWA said ['no']

# closed-world, but a few concepts are open (per-concept exception)
mixed = FirmwarePolicy(open_preds=frozenset({"mice", "bug"}))

# on a non-stratifiable bank: reject at load (default) vs degrade gracefully
strict     = FirmwarePolicy(on_cycle="raise")             # load_corpus raises on a negation cycle
forgiving  = FirmwarePolicy(on_cycle="degrade")           # drops NAF rules, warns, reasons positively
kb2, rules2 = h.load_corpus(CORPUS, policy=forgiving)
```

The legacy `open_preds=frozenset({...})` kwarg on `ask_goal`/`check` still works — it is the same as a
closed-world policy with those OWA exceptions.

## 4. Gather evidence for open questions (`ask_user`)

When a yes/no goal needs a fact on an *open* concept that is `unknown`, `ask_goal` can call a handler to
gather evidence (a human, a sensor, a tool). `True` materializes the fact (monotone — it persists) →
`yes`; `False` → `no`; `None` → stays `unknown`.

```python
def gather(subj, rel, obj):
    return input(f"Is it true that {subj} {rel} {obj}? [y/n] ").startswith("y") or None

open_pol = FirmwarePolicy(negation_default="open")
h.ask_goal(kb, "is cellar has mice", rules, policy=open_pol, ask_user=gather)
```

`ask_user` also gathers **mid-chain**: not only the top goal, but any *open premise a rule needs* to reach
the conclusion. If `safe when cleared` and `cleared` is open, then `is bo safe` (with `bo` not yet known
cleared) asks `("bo", "is", "cleared")` — the reasoner requests the premise it is missing, materializes
your answer, and fires the rule, instead of silently assuming `no`. Which premises get asked is *derived*
from the demand frontier the reasoning raises (never a fixed predicate list): the open, unmet, fully-bound
sub-goals the closure needed. Several distinct premises in one derivation are each asked in turn.

## 5. Drive an interactive session (`ingest` / `converse`)

For a multi-turn agent or TUI, `ingest` is the ONE entry: hand it an utterance and it routes *itself* by
which CNL forms fire (no caller-side classifier) — a fact lands, a question is answered, a `HEAD when …`
line adds a rule, `focus on X` moves attention. It returns an `Outcome(kind, …)`; `rules` is mutated in
place when a rule is added, so later turns reason with it.

```python
kb, rules = h.load_corpus("")
h.ingest(kb, rules, "ada is a suspect")                       # Outcome(kind="fact")
h.ingest(kb, rules, "?x is watched when ?x is a suspect")     # kind="rule" — effective immediately
h.ingest(kb, rules, "is ada watched").answer                 # ["yes"]
```

`Outcome.kind` is one of `fact | answer | rule | rule-disable | focus | unrecognized`. An unrecognized
utterance is a clean rejection (`kind="unrecognized"`), not a crash — the habitability signal.

**Stream a turn (`on_event`, `trace`).** Pass `on_event` to watch a turn unfold live (a TUI renders each
event as it happens); `trace=True` adds one `derive` event per rule firing — the reasoning trace, read from
the provenance substrate. (A `derive` fires when a fact is *newly* derived; a conclusion already
materialized by an earlier query is not re-derived — reasoning is monotone.)

```python
h.ingest(kb, rules, "bo is a suspect")
h.ingest(kb, rules, "is bo watched", on_event=print, trace=True)
# Event("question", …) -> Event("derive", {"rule":…, "fact":"bo is watched"}) -> Event("answer", {"answer":["yes"]})
```

Event kinds: `focus, question, ask, derive, answer, fact, rule, rule-conflict, rule-disable, unrecognized`.

**Non-blocking, human-in-the-loop (`converse`).** `ingest` *blocks* (it calls `ask_user` / `on_conflict`
synchronously). For a UI that cannot block, `converse` is a generator you pump: it yields events and you
`.send()` the verdict at an `ask` (or `rule-conflict`). Suspend/resume is threadless — the graph is the
continuation, so the reasoner pauses at an ask and resumes when you send the answer, whether it is the top
goal or a mid-chain premise (§4).

```python
gen, send = h.converse(kb, rules, "is cellar has mice", policy=owa), None
try:
    while True:
        ev = gen.send(send); send = None
        if ev.kind == "ask":
            send = my_ui_yes_no(ev.data)        # {"subj","rel","obj"} -> True / False / None
except StopIteration as done:
    outcome = done.value
```

**Author rules at runtime.** A `HEAD when …` utterance adds a rule that reasons immediately. If it forms a
negation cycle with the live theory, `ingest` does not crash — it ASKS: supply `on_conflict(detail) -> bool`
(blocking) or handle the `rule-conflict` event (converse). Accept → the engine degrades the NAF rules;
reject → the rule is discarded. `forget that rule` disables the last-added rule via an additive `<disabled>`
marker (never a deletion — the rule object stays; only the marker excludes it from reasoning).

```python
h.ingest(kb, rules, "?x is q when ?x is not p")
h.ingest(kb, rules, "?x is p when ?x is not q", on_conflict=lambda detail: False)   # cycle -> rejected
h.ingest(kb, rules, "forget that rule")                                             # kind="rule-disable"
```

**Bound attention to the working set (focus).** A long session's graph grows with the transcript. A focus
stack tracks what the conversation is about (`focus on X`, `forget that`, `back to X`); `attention="focus"`
scopes reasoning to that set, so per-utterance cost tracks the focus, not the whole accreted session.

```python
h.ingest(kb, rules, "focus on bo")                        # explicit topic move (a recognized form)
h.ingest(kb, rules, "is bo thief", attention="focus")     # reason within the focus closure only
h.focus.top_centers(kb)                                   # the entities currently in play
```

Off-focus facts are outside attention *by design* (an agent reasons about what is in play), so a `"focus"`
answer can differ from the whole-KB `"global"` default — you choose the mode per call.

## 6. Plug in your own tools

A tool is a calculator the rules invoke by materializing a `<call>` node — this is how you extend the
engine with domain computation (arithmetic, an external lookup, a service). A tool is
`Tool = Callable[[graph, call_id], set[str]]`: read the call's opaque arg-slots, emit nodes, return the
touched ids (see the developer guide for the full contract).

```python
from ugm import call_arg, merge_tools, mode_registry, run_rules

def price_tool(graph, call_id):
    item = call_arg(graph, call_id, "arg")
    cents = lookup_price(graph.name(item))              # your external calculation
    out = graph.add_node(str(cents))
    graph.add_relation(call_id, "result", out)
    return {out}

# compose your tools with the firmware's mode tools (collision-safe)
tools = merge_tools(mode_registry(reified_rules), {"price": price_tool})
run_rules(kb, my_rules, tools=tools)
```

Rules decide *when* a tool fires by emitting its call at the point a value is needed; the engine services
pending calls at each fixpoint and folds the results back into reasoning. Use `merge_tools` to combine
registries — it raises on a name collision so two subsystems never silently clash.

## 7. Forward materialization (when you need a full snapshot)

Demand-driven answering only derives what a goal needs. If you need a *complete* forward snapshot — for
inspection, export, or a bulk pass — run the rules forward:

```python
h.run_rules(kb, rules)                     # stratified forward chaining to fixpoint
# now a raw graph read is complete; render with h.ask(kb, question) or the surface renderers
```

`run_rules` is also where the `on_cycle="degrade"` stance takes effect (it drops NAF rules on a cycle
and warns, rather than raising).

---

## Cheat-sheet

| You want to… | Call |
|---|---|
| Load CNL facts + rules | `load_corpus(text, policy=…) -> (kb, rules)` |
| Load only rules / only facts | `load_rules(text, policy=…)` / `load_facts(graph, text, strict=…)` — `strict=True` raises on an unrecognized line |
| Ask (demand-driven) | `ask_goal(kb, question, rules, policy=…, ask_user=…)` |
| Drive one session turn (any utterance) | `ingest(kb, rules, utterance, on_event=…, ask_user=…, on_conflict=…, attention=…, trace=…) -> Outcome` |
| Non-blocking session turn (generator) | `converse(kb, rules, utterance, …)` — yield events, `.send()` the ask verdict |
| Disable / re-focus mid-session | `"forget that rule"` / `"focus on X"` / `"forget that"` / `"back to X"` (utterances to `ingest`) |
| Get the 4-status verdict | `check(kb, reified_rules, (pred, subj, obj), policy=…)` |
| Pick a maximal option (graded) | `choose(graph, goal, alpha=…)` |
| Reason under an assumption | `suppose(...)` |
| Register domain tools | `merge_tools(mode_registry(rr), {name: tool})`, pass `tools=` to `run_bank`/`run_rules` |
| Full forward snapshot | `run_rules(kb, rules, tools=…)` |
| Render the graph as CNL | `ask(kb, question)`, `surface.render_relation`, `narrate`, `explain` |

Everything you pass in — rules, tools, policy — is data on the generic engine. You never fork the engine
to add a domain; if you need a *different reasoning model*, that is the stance (`FirmwarePolicy`) or, at
most, a thin firmware module (developer guide).
