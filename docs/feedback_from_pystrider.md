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
>
> **UPDATE (2026-07-13): (C) is no longer deferred — done.** Genuine per-match minting IS supported, via the
> bound-literal skolem `<foo>?` (a skolem FUNCTION keyed on the LHS match), now convergent on the demand
> chain too. See the RESOLVED note under #2. The rejection of the bare `?x` case stays — it is unsound, not
> merely unimplemented.

> **RESOLVED (2026-07-13).** Two distinct cases, now distinguished. (a) A bare RHS-only VARIABLE (`?x` from
> nowhere) is genuinely unsound — forward mints an unnamed node the name surfaces can't see, and the demand
> chain SELF-FULFILS a ground goal (`chain_sip(('succ','p1','moon_cheese'))` returned yes AND wrote it). It
> stays REJECTED at authoring, on principle (not deferred). (b) The SUPPORTED minting path is the bound-
> literal skolem `<foo>?` anchored to LHS-bound endpoints — a skolem FUNCTION of the match ("the successor
> of ?p"). Forward already minted one node per firing; the demand chain used to BLOW UP (a fresh node every
> round, fuel-capped at ~1000/2000) because the bracket-named skolem is control and the reuse-by-name lookup
> skipped it, so check-before-derive never tripped. `chain._resolve_skolems` now re-finds the skolem
> STRUCTURALLY by its defining relation, keyed on the firing's LHS args, so forward and demand AGREE (one
> node per argument) and a re-served demand converges (idempotent). This retires the pre-materialized-pool
> workaround. Docstrings (`lower_rhs`, `rhs_only_head_vars`, the rejection message) corrected. Tests in
> `tests/test_feedback_fixes.py` (`test_demand_skolem_*`).

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

## 8. Name-addressing on the retrieval/CHOOSE path: silent name-split joins + no get-or-create, and focus doesn't reach it either

Collected while building the **synthesis** probes (`experiments/spec_synthesis.py`,
`codegen_understand.py`, `controlflow_synthesis.py`), which drive the *retrieval + CHOOSE* firmware
(`ask_goal "who realizes …"` / `set_candidate` / `choose`) hard, over many small authored graphs.
Two related rough edges, both in the same "attention / addressing" family as #7.

**(a) A name that resolves to two nodes fails a rule join — signalled only at write time, never at
query time.** `add_node(name)` is (correctly, by design) *fresh per call* — a name is a label, not
an identity, and `nodes_named` returns a candidate *set*. But that means a consumer who mentions the
same intended entity twice while building a graph silently splits its facts across two nodes, and a
rule that must join those facts then derives nothing:

```python
import ugm as h
from ugm import load_machine_rules, ask_goal
g = h.Graph()
a1 = g.add_node("plan"); a2 = g.add_node("plan")   # two DISTINCT nodes, both named "plan"
g.add_relation(a1, "is_a", g.add_node("thing"))
g.add_relation(a2, "flag", g.add_node("yes"))
rules = load_machine_rules("?p ok yes when ?p is_a thing and ?p flag yes")
print(ask_goal(g, "who ok yes", rules))            # ['(no answer)']  — is_a and flag are on diff nodes
```

The only signal ugm emits is a `UserWarning` at rule **EMIT** time when a rule tries to *write* to a
name resolving to >1 node ("name 'plan' resolves to 2 distinct nodes; writing to the first …") — a
read-only join like the above gets **no** signal at all. This cost real time on the
`codegen_understand` round-trip link (a plan node built by the graph-builder, then re-`add_node`d
when attaching `emitted_as`, split the join so recognition silently returned nothing). It is the
same silent-does-less theme as #1/#2/#5, on the query path. **Ask:** at goal/`chain_sip` time, when a
body or goal pattern references a name that resolves to multiple nodes, surface it (strict-mode raise
or a warning) — "goal names `plan`, which is 2 nodes; did you mean one?" — so a split entity is
caught where it bites, not only where it's written.

**(b) No sanctioned get-or-create-by-name, so every graph-building consumer hand-rolls an id cache.**
Because `add_node` is fresh-per-call and there is no `get_or_add(name)` / by-name write helper, all
three synthesis probes (and the two tests that build ad-hoc graphs) carry the identical boilerplate —
a local `ids: dict[str,str]` with `def n(x): ids.setdefault(x, g.add_node(x)); return ids[x]` — purely
to keep one name mapped to one node. **Ask:** a first-class "intern this name to a stable node"
helper (or an id-addressed authoring API), so consumers don't reinvent the cache and (a) stops being
easy to trip.

**(c) The synthesis retrieval path wants focus/attention just as `suppose` does (#7 generalizes).**
The probes spin up a *fresh isolated `Graph` per goal / per CHOOSE iteration* — not for cleanliness
but to keep each `ask_goal "who realizes …"` scoped to that layer's candidates and collision-free.
That is a manual stand-in for exactly the `focus_scope` / id-addressed-goal mechanism #7 asks for on
`suppose`. Once synthesis accretes many candidate + emitted nodes in one persistent graph (the
demand-driven pool, or a Session that both analyzes and synthesizes), retrieval + CHOOSE will need
the same attention-bounding the trace path already has. **Ask:** treat #7's `focus_scope` as covering
the retrieval/CHOOSE entry points too (`ask_goal`/`choose` over a scoped candidate set by id), not
just `suppose` — and an **id-addressed goal API** (seed/query by node id, names as labels) would
retire (a) and (b) at the same time. This is the ugm-side of the "addressing" follow-on pystrider's
own `docs/spike_findings.md` flags for a shared multi-function graph.

---

### Net

The spike succeeded and the model (SUPPOSE + CHAIN over reified semantics, RECORD as the
trace) fit beautifully. The friction was almost entirely **silent failure modes** (#1, #2, #3,
#5, and #8a — a name-split join that quietly returns nothing): ugm tends to quietly do less
rather than error, which is costly when you're authoring rules/facts programmatically. A
strict/verbose mode that surfaces "I did not recognize / could not mint / dropped this / joined
across a split name" would remove most of the pain. The synthesis probes (retrieval + CHOOSE over
many small authored graphs) add an **addressing/attention** ask on top (#8): a get-or-create-by-name
helper and an id-addressed goal API, with focus reaching the retrieval path, not just `suppose`.
