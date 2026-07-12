# Feedback from the pystrider spike — ugm bugs / limitations / surprises

Collected while building `pystrider` (a dynamic code analyzer on ugm) — the sibling
`../pystrider`. Each item has a minimal repro against the installed `ugm`. Ordered roughly by
how much time it cost / how surprising it was. Nothing here blocked the spike (workarounds
found), but each is a rough edge for a library consumer.

Environment: `ugm` editable install, Python 3.13, Windows.

---

> **FIXED (2026-07-12).** `load_machine_rules` now raises `ValueError` naming the offending clause(s)
> when a head/body clause doesn't fold to a full `S P O` triple — a swallowed `when`/`and` separator or a
> dropped short clause — with the hint to write `?g guard_open yes`. Detected from the FOLD result
> (`authoring.machine_rule_defects`), not a Python re-parse. Tests in `tests/test_feedback_fixes.py`.

## 1. Machine-rule CNL silently mis-parses a non-3-token clause  (footgun — cost the most time)

A head or body clause that is not a 3-token `S P O` triple is **silently corrupted** instead
of raising: the following keyword (`when` / `and`) is swallowed as the clause's object.

```python
from ugm import load_machine_rules
r = load_machine_rules("?e reached when ?e is_a attribute")[0]
print(r.rhs)   # [Pat(s='?e', p='reached', o='when')]   <-- 'when' eaten as object; body lost
```

Worse, a 2-token *body* clause silently drops out of the LHS, so the rule quietly means
something weaker:

```python
r = load_machine_rules("?e reached yes when ?e within_guard ?g and ?g guard_open")[0]
# the `?g guard_open` clause (2 tokens) vanishes from lhs; the rule fires unconditionally
print(r.lhs)   # only [Pat('?e','within_guard','?g')] — the guard condition is GONE
```

This produced a rule that fired when it shouldn't and took real debugging to localize.
**Ask:** raise (or at least warn) when a clause doesn't parse to a full triple, rather than
absorbing a keyword. A boolean-shaped predicate should be a hard error with a hint ("write
`?g guard_open yes`"), not a silent mangle.

> **PARTLY ADDRESSED (2026-07-12) — option A (reject loudly); genuine minting (C) deferred.** The behavior
> was worse than "optimistic docstring": forward chaining mints a fresh UNNAMED node every firing and never
> suppresses it (the rule re-fires, `derived_triples` hides the results), and the demand chain collapses the
> var onto the query goal. So the loaders now REJECT an RHS-only head var at authoring
> (`production_rule.rhs_only_head_vars` + `authoring.reject_rhs_only_head_vars`, run AFTER the malformed-
> clause check) with guidance toward the MINT-tool / pre-materialized-pool workaround; the `lowering.py`
> docstring is corrected. Bound-literal skolem binders (`<rule>?`/`<cond>?`) and NAC-bound head vars are
> untouched. Genuine per-match fresh minting (C) is deferred — pystrider's pre-materialized-pool workaround
> does not need it. Tests in `tests/test_feedback_fixes.py`.

## 2. Existential / Skolem head variables are not fresh-minted by the public drivers (and drivers disagree)

An RHS-only variable (a head var absent from the body) is documented in `lowering.py:226` as
"a skolem / RHS-only var mints ONE fresh node per firing". Observed behavior does not match,
and differs by driver:

```python
import ugm as h
from ugm import load_machine_rules, write_rule, AttrGraph, run_rules, run_bank, chain_sip

rule = load_machine_rules("?p succ ?s2 when ?p is_a state")[0]   # ?s2 is RHS-only

# (a) forward drivers: derive NOTHING (silent)
g = h.Graph(); p = g.add_node("p"); g.add_relation(p, "is_a", g.add_node("state"))
run_rules(g, [rule]);  print([t for t in h.derived_triples(g) if t[1] == "succ"])   # []
run_bank(g, [rule]);   print([t for t in h.derived_triples(g) if t[1] == "succ"])   # []

# (b) chain_sip: ?s2 is COLLAPSED onto the demand goal's object via SIP (no fresh node)
rg = AttrGraph(); write_rule(rg, rule)
g2 = h.Graph()
for nm in ("p1", "p2"):
    n = g2.add_node(nm); g2.add_relation(n, "is_a", g2.add_node("state"))
chain_sip(g2, rg, ("succ", "p1", "anything"))
chain_sip(g2, rg, ("succ", "p2", "anything"))
print([t for t in h.derived_triples(g2) if t[1] == "succ"])
# -> [('p2','succ','anything'), ('p1','succ','anything')]  BOTH point at the goal's object
#    'anything' — one shared node, not a fresh node per firing.
```

So there is no way, from the rule surface, to write "mint a fresh successor node per match"
(needed for symbolic-execution state threading). **Ask:** either wire genuine fresh minting
through `run_rules`/`chain` for RHS-only vars, or update the lowering docstring + user/dev
guides to say existential heads are unsupported and point to the intended mechanism (a §8 tool
that MINTs, or explicit ISA `MINT`). The current silence + the optimistic docstring is a trap.
(Workaround we used: pre-materialize the node pool in the intake tool and have rules only
*bind* pre-existing nodes — see pystrider `experiments/state_threading.py`.)

## 3. `ask_goal` / `ask` case-fold identifiers, silently failing to match mixed-case node names

CNL question parsing lowercases tokens, so a question about a node named `eB` becomes a query
for `eb` and returns a (false) negative rather than an error or a match:

```python
import ugm as h
from ugm import load_machine_rules, ask_goal
g = h.Graph(); e = g.add_node("eB"); g.add_relation(e, "is_a", g.add_node("attribute"))
print(ask_goal(g, "is eB a attribute", [] ))   # ['no']   (matches 'eb' != 'eB')
```

`suppose`/`chain_sip` use raw `(pred, subj, obj)` tuples and are case-preserving, so this only
bites the CNL query path — which makes it *inconsistent* within the library and easy to miss
(a materialized fact is invisible to `why`). **Ask:** document that node names must be
lower-case for CNL queries, or fold names on intake, or match case-insensitively — but make
the two paths agree.

> **FIXED (2026-07-12).** `apply_rule`/`apply_to_fixpoint` now validate `rule_node` at the call boundary
> (`apply._require_rule_node`): a `Rule` object raises a clear `TypeError` ("expect a rule-NODE id … got a
> Rule object; `rules_in_graph` returns Rules for inspection — pass `write_rule`'s return value") instead
> of the deep `unhashable type: 'Rule'`. Docstrings note `rule_node` is `write_rule`'s return.

## 4. `apply_rule` / `apply_to_fixpoint` want a rule-node id, but `rules_in_graph` hands back `Rule` objects → cryptic `TypeError`

```python
from ugm import load_machine_rules, write_rule, AttrGraph, apply_to_fixpoint, rules_in_graph
rule = load_machine_rules("?p made child when ?p is_a parent")[0]
rg = AttrGraph(); node = write_rule(rg, rule)     # returns 'n0' (the id you actually need)
apply_to_fixpoint(g, rg, rules_in_graph(rg)[0])   # TypeError: unhashable type: 'Rule'
#                         ^ returns Rule objects, not node ids
```

The failure surfaces deep in `attrgraph.relations_from` (`self._nodes[Rule(...)]`), not at the
call boundary. **Ask:** either have `apply_*` accept a `Rule`/reified node uniformly, or raise
a clear error ("expected a rule-node id; got a Rule — did you mean `write_rule`'s return
value?"). Also worth documenting that `write_rule` returns the id you feed to `apply_*`.

> **FIXED (2026-07-12).** `load_facts(graph, text, strict=True)` raises `ValueError` listing the line(s)
> that folded to no content fact (unknown/undeclared verb → raw tokens). Default `strict=False` keeps the
> lenient "unrecognized stays raw" behaviour. The detector `authoring.anchor_has_content_fact` is now
> shared with `intake.ingest`'s fact-vs-unrecognized routing (one implementation).

## 5. `load_facts` silently drops `S P O` lines whose verb isn't lexicon-known/declared

```python
import ugm as h
from ugm import load_facts
g = h.Graph(); load_facts(g, "stmt0 assigns y")
print([t for t in h.derived_triples(g) if t[1] == "assigns"])   # []  (silently no fact)
# 'alice wants vanilla' works (wants is known); 'assigns' is not, and there is no signal.
```

Declaring the relation needs a two-pass regeneration of surface forms, which isn't obvious for
programmatic loading. This is arguably the intended "unrecognized stays raw tokens" behavior,
but a **caller gets no signal** that a line was dropped. **Ask:** an opt-in strict mode or a
returned list of unrecognized lines from `load_facts`, so a data-loading caller can detect
silent loss. (Workaround: the design already reserves intake as a "§8 tool, not CNL", so we
materialize facts directly — but the silent drop surprised us first.)

## 6. (minor) `suppose()` mutates the KB (commits assumptions to ink on CONFIRM); no read-only verdict — ✅ FIXED 2026-07-12

**FIXED:** `suppose(..., commit=False)` is a READ-ONLY entry point — it inks NOTHING (even a CONFIRMED run
only reports the verdict) and returns the in-scope DERIVED consequences in `SupposeResult.derived` for
inspection, including after an INCONCLUSIVE run (the partial derivations that used to be swept unseen). So a
hypothesis-driven analyzer no longer copies/rebuilds the KB per query. Default `commit=True` is unchanged.
(`suppose.py` `_scope_derivations`; `tests/test_feedback_fixes.py`.) Note: a brand-new entity NAME in an
assumption still mints its node — pass `ById` for a fully pure call.



`suppose(fact_g, rule_g, ...)` commits the assumptions into the fact layer on CONFIRM and
sweeps everything on REFUTE/INCONCLUSIVE — so (a) an analyzer that asks "does X hold under this
hypothesis?" must copy/rebuild the KB per query to stay pure, and (b) after an INCONCLUSIVE
result the in-scope derivations are gone, so you can't inspect *why* it was inconclusive. Both
are consistent with the pencil/ink contract, but for a consumer a **non-committing "verdict +
in-scope trace only"** entry point would fit hypothesis-driven tools much better. **Ask:**
consider a `suppose(..., commit=False)` returning the in-scope derivations for inspection.

## 7. `suppose()` does not accept `focus_scope` (unlike `ask_goal`) — the outcome path can't be attention-bounded

`ask_goal(..., focus_scope=frozenset(...))` threads bounded attention into its internal
`chain_sip` (query.py). `suppose(...)` has no such parameter, yet it *also* calls `chain_sip`
internally (suppose.py) to propagate the hypothesis and check predictions. So a consumer whose
primary reasoning is hypothesis-driven (`suppose` = "does this outcome arise under this
assumption?") cannot bound reasoning to the working set the way a question can.

```python
import inspect
from ugm import ask_goal, suppose
print("focus_scope" in inspect.signature(ask_goal).parameters)   # True
print("focus_scope" in inspect.signature(suppose).parameters)    # False
```

For pystrider (a code analyzer whose graph accretes multiple functions across a session), focus
is the mechanism that keeps per-hypothesis cost tracking the function under analysis rather than
the whole accreted graph — but it only reaches the *trace* path (`ask_goal "why"`), not the
*outcome* path (`suppose`). **Ask:** thread `focus_scope` through `suppose` to its `chain_sip`
calls, exactly as `ask_goal` already does — a small, mechanical addition that makes the Session
focus story usable for hypothesis-driven consumers.

---

### Net

The spike succeeded and the model (SUPPOSE + CHAIN over reified semantics, RECORD as the
trace) fit beautifully. The friction was almost entirely **silent failure modes** (#1, #2, #3,
#5): ugm tends to quietly do less rather than error, which is costly when you're authoring
rules/facts programmatically. A strict/verbose mode that surfaces "I did not recognize / could
not mint / dropped this" would remove most of the pain.
