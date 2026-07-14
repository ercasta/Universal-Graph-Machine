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

> **FIXED.** `suppose(..., focus_scope=frozenset(...))` now threads bounded attention into its in-scope
> `chain_sip`/`_facts_matching` calls exactly as `ask_goal` does (`suppose.py`), so a hypothesis-driven
> consumer can bound the outcome path to the working set. Test: `test_suppose_accepts_focus_scope`.

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

> **ADDRESSED (2026-07-13) — (a) + (b) done the VISION-ALIGNED way; (c) mostly already supported.** (a) A CNL
> query that NAMES a name resolving to >1 genuinely-distinct fact entity now WARNS at query time
> (`query._warn_name_split_join`, sibling of the #3 case-fold warning; reuses `_one_identity` so coref'd
> mentions stay quiet). Limit: this catches a query that *names* the split entity; the flagship example (the
> split entity bound to a rule's JOIN VARIABLE, never named in the query) is a build-time smell best
> PREVENTED — see (b).
>
> (b) **The machine is a MACHINE: capabilities/semantics are ISA PROGRAMS, not Python helpers** (ratified
> with the user). An earlier pass added a public `intern_node` get-or-create helper; that was a Python TWIN of
> `MINT(intern=True)` — a semantic that is already an instruction — so it was KILLED. Fact authoring now goes
> through `lowering.assemble_facts(triples)` → a `MINT` program (each endpoint `MINT(intern=True)`, each
> relation `MINT(dedup=True)`) → `Machine.run` (`load_fact_triples`). A re-mentioned entity interns to one
> node VIA THE ISA, so a built graph never splits a name across duplicate nodes — retiring the hand-rolled
> `ids.setdefault(x, add_node(x))` cache, with the get-or-create living where it belongs (the interpreter),
> not in a substrate-poking helper. `add_node`/`add_relation` stay the dumb loader/RAM; interning is the
> instruction. (Internal get-or-create plumbing — `dispatch`/`mode_calls._ensure`, `focus._entity_node` — is
> tagged `TODO(vision-cleanup)` and flagged in `implementation_plan.md`: same principle, lower priority.)
>
> (c) mostly ALREADY supported: `ask_goal`/`suppose` have `focus_scope` (#7 done); `choose` is already fully
> id-addressed (operates on node ids, and doesn't reason, so nothing to attention-bound); and id-addressed
> GOALS work today via `chain_sip` + `ById` — verified collision-free (`realizes ? ById(s1)` returns only
> s1's realizer though two specs share a name). A vision-aligned id-addressed RETRIEVE surface would be a
> `<call>` mode (like CHECK/CHOOSE), not a `who()` helper — deferred. Tests:
> `tests/test_feedback_fixes.py` (`test_name_split_join_*`, `test_assemble_facts_*`).

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

> **FIXED (2026-07-14).** `load_machine_rules` is MEMOIZED on the normalized bank text: the fold-validate
> is a pure function of the text, so reloading a static bank costs a dict hit (measured ~19ms first load →
> ~6µs repeat), with no API change — this is the "validated-once handle keyed on the bank text" fitting the
> ISA §10 rule-set-version direction, chosen over a `validate=False` flag (which would skip the very check
> feedback #1 asked for; here nothing is skipped, just never re-paid). The returned LIST is fresh per call
> but the `Rule` objects are shared — treat them as immutable (every engine path does). Comment/whitespace
> variants hit the same entry (keyed on the normalized body); a defective bank re-raises on EVERY call
> (failures are not cached). Tests in `tests/test_feedback_fixes.py` (`test_load_machine_rules_*`).

## 9. `load_machine_rules` VALIDATES by running the bank on every call — a 65% hidden cost for a consumer that reloads rules

`load_machine_rules(text)` doesn't just parse — it *validates the bank by executing it*
(`authoring.machine_rule_defects` → `run_bank`/`machine.run`). That is the right default for a
one-time load, but it is **surprisingly expensive** and there is no way to skip it or to reuse a
validated result. A consumer that reasons over one static bank pays the full parse+validate cost on
every reload.

pystrider reifies its semantics bank fresh for each detect (a fresh rule graph is the clean way to
avoid shared graph-state across hypotheses). Profiling `repair_all` on a 3-line function:

```
repair_all -> _detect ×7 -> build_rule_graph/rule_list -> load_machine_rules ×15
load_machine_rules cumulative: 28.9s of a 28.7s* profiled run   (*profiler overhead)
```

`load_machine_rules` was **~65% of every `analyze`** and ran 7× per `repair_all` — the bank never
changes, so it was 100% redundant re-validation. Memoizing the parse on our side (parse once, still
build a fresh graph per call) took **`repair_all` 8.2s → 0.21s (~39×)** and our **test suite 376s →
31s (~12×)**, with no behaviour change (138/138 green). Repro:

```python
import time
from ugm import load_machine_rules
text = open("pystrider/semantics.cnl").read()   # ~a dozen machine rules
t = time.perf_counter()
for _ in range(10):
    load_machine_rules(text)                     # each call re-parses AND re-validates
print((time.perf_counter() - t) / 10, "s per load")   # ~2s, dominated by machine_rule_defects
```

**Ask:** give consumers a way to not pay validation on every load — e.g. `load_machine_rules(text,
validate=False)` (parse only), or a compiled/validated bank handle that reuses the check across
reloads (validation is a pure function of the text, so it's cacheable on a text hash). Since the ISA
control-machine work makes rule-set-versioned compilation a first-class idea (isa doc §10, "keyed on
a rule-set version"), a validated-once handle keyed on the bank text fits that direction cleanly. At
minimum, the docstring should note that this call *runs the bank*, so consumers know to load once and
reuse rather than reload per query. (Not a blocker — the one-line memoization on our side fixed it —
but it's a footgun for any library consumer that treats rule-loading as cheap.)

> **APPEARS RESOLVED (2026-07-14), concurrent ugm work.** The cold path below now works with no prime;
> the `import pystrider` workaround was removed and the pystrider suite is green (194) without it. Kept as
> a fingerprint in case it recurs. It was never minimizable to a standalone repro (see below), so this is
> a record + confirmation, not an open bug.
>
> **DIAGNOSED + HARDENED (2026-07-14).** The fingerprint matches EDITABLE-INSTALL VERSION SKEW during the
> concurrent (X) migration: `env` was being converted to the machine's `State` register file that same day,
> and an import that landed mid-edit could pair the NEW `_unify_head_with_demand` (returns a `State`) with
> STALE bytecode for `_solve_demand_rule` (still `set(env0)`) — exactly this traceback, import-order
> sensitive, impossible to reproduce against a coherent tree. Both asks are now satisfied structurally:
> (a) the dict/State seam no longer exists — bindings are `State.regs` end-to-end, and `set(env0)` is gone
> (`_sideways_order(body, set(st0.regs))`); (b) the one genuinely order-sensitive global in the demand path
> was found and REMOVED — `Machine._inert_cache`, a per-machine inertness memo keyed by nid alone, which a
> machine shared across graphs could poison (nids collide across graphs: every graph mints `n0, n1, …`).
> No demand-path global now depends on prior imports/queries; cold == warm.

## 10. `ask_goal` raised `TypeError: 'State' object is not iterable` on a COLD ugm import — order-sensitive, un-minimizable

Collected while building the **app-synthesis** probe (`experiments/app_synthesis.py`, the grammapy-
convergence Phase 2). Removing an incidental `from pystrider.emit import …` line (retiring an ad-hoc
selector) made a previously-green `ask_goal` start raising:

```
File ".../ugm/chain.py", line 811, in _solve_demand_rule
    for s_tok, bp, o_tok in _sideways_order(body, set(env0)):   # SIP: each atom demanded under env
                                                  ~~~^^^^^^
TypeError: 'State' object is not iterable
```

i.e. `env0` (from `_unify_head_with_demand`) was a `State`, not the `dict` `set(env0)` expects. The
failing goal (`who needed_by <spec>`) is a plain multi-atom join with **no negation**, so it was not a
stratified-negation issue.

**What localized it: an import-order dependency, not the query.** The exact same call *did not* raise if
`pystrider.analysis`/`semantics` (which imports `ugm` and builds a rule bank) had been imported first —
so some ugm global that the analysis import primes was load-bearing. Phase 1 got that prime for free via
`pystrider.emit`; Phase 2 dropped it and exposed the raw path.

**Why there is no minimal repro.** Every standalone reconstruction — the same fact set + the same 5-rule
bank (incl. the `not …` preference rules), built inline against a fresh `ugm` — ran **clean cold**. The
fault only surfaced through the full `experiments/app_synthesis` import chain, so it was sensitive to
some accumulated import/global state I could not isolate before the concurrent ugm change made it
disappear. **Ask (if it recurs):** `_solve_demand_rule` should assert/normalize `env0` to a mapping (or
fail with a message naming the rule) rather than iterating a `State`, and the demand path should not
depend on a prior unrelated import having warmed a global — a cold `ask_goal` should behave identically
to a warm one.

> **FIXED (2026-07-14).** A body clause `?a != ?b` is now a DISTINCTNESS condition honoured by the join on
> BOTH engines. It lifts at load (`machine_rules._lift_distinct`) to a DECLARED condition
> (`production_rule.Distinct` on `Rule.distinct`, reified as `<rule> -[distinct]-> <distinct>`) executed by
> the ONE `DISTINCT` op — the forward path lowers to it (`lowering.lower_distinct`), the demand chain runs
> it as an ephemeral program (`chain._distincts_pass`) — the exact `ValueMatch`/`VMATCH` pattern, so
> distinctness is rule DATA the machine runs, not a Python special case. Semantics: disjoint denotations —
> node IDENTITY, so two same-named nodes ARE two writers (a name is a label), and a head-seeded name
> overlapping a body-bound node correctly fails; `same_as` coref is deliberately not consulted (identity-
> as-rules stays bank data). Unsupported shapes are LOUD at load: `!=` in a head or under `not`, a literal
> side, or a side not bound by a positive body clause all raise. The `write_conflict` repro returns
> `['submit']` with zero hand-authored facts — the frame-rule family ports to CNL. (The deferred
> `functional`/`injective` relation properties can now be built on this; still open.) Tests in
> `tests/test_feedback_fixes.py` (`test_neq_*`, `test_distinct_*`).

## 11. No distinctness / inequality primitive — "no two DISTINCT S share an O" cannot be expressed as a rule

Collected while spiking the grammapy-convergence question *"can a composition-soundness check be authored
as a CNL rule-module over ugm, instead of Python?"* Reachability ported **perfectly** — a recursive
closure + stratified negation reproduced grammapy's `Scope` verdict exactly:

```python
# a control tree as facts: ?parent parent_of ?child ; ?node emits ?sig ; ?node handles ?sig
SCOPE = """
?a ancestor_of ?n when ?a parent_of ?n
?a ancestor_of ?n when ?a parent_of ?m and ?m ancestor_of ?n      # recursive closure — works
?n handled ?sig  when ?n emits ?sig and ?a ancestor_of ?n and ?a handles ?sig
?n unhandled ?sig when ?n emits ?sig and not ?n handled ?sig      # stratified negation — works
"""
```

But the *disjointness*-shaped check (the frame rule: **"no two DISTINCT items write the same channel"**)
cannot be written, because there is no way to say `?a ≠ ?b`:

```python
import ugm as h
from ugm import load_machine_rules, ask_goal
def g():                                   # ok & yes BOTH write confirm.submit (a real conflict);
    G=h.Graph(); i={}                      # cancel writes only its own slot (NOT a conflict)
    n=lambda x:i.setdefault(x, i.get(x) or G.add_node(x))
    for s,o in [("ok","submit"),("yes","submit"),("cancel","cancel.slot")]:
        G.add_relation(n(s),"writes",n(o))
    return G,n
def conflicts(rule, extra=()):
    G,n=g()
    for s,p,o in extra: G.add_relation(n(s),p,n(o))
    return sorted({a.split(" ",1)[0] for a in ask_goal(G,"who write_conflict yes",load_machine_rules(rule))
                   if a.split(" ",1)[0] in {"submit","cancel.slot"}})

print(conflicts("?c write_conflict yes when ?a writes ?c and ?b writes ?c"))
#   -> ['cancel.slot', 'submit']   FALSE POSITIVE: cancel.slot has ONE writer but self-joins
print(conflicts("?c write_conflict yes when ?a writes ?c and ?b writes ?c and ?a != ?b"))
#   -> []   '!=' is read as a predicate literal needing a fact '?a != ?b'; the rule goes INERT
print(conflicts("?c write_conflict yes when ?a writes ?c and ?b writes ?c and ?a distinct_from ?b"))
#   -> []   the clause IS enforced (needs a distinct_from fact) — but distinctness is never DERIVED
d=[(a,"distinct_from",b) for a in ("ok","yes","cancel") for b in ("ok","yes","cancel") if a!=b]
print(conflicts("?c write_conflict yes when ?a writes ?c and ?b writes ?c and ?a distinct_from ?b", d))
#   -> ['submit']   CORRECT — but ONLY after materializing O(n²) hand-authored distinctness facts
```

This matches your own scoping: `rule_graph._property_rule` notes `functional`/`injective` "**DO need
distinctness and are deferred** — see docs/design/consistency_design.md". So it is a known gap; this is the
concrete consumer cost. The only faithful workaround today is to author O(n²) `distinct_from` facts,
which defeats the point (the check exists to *scale* composition).

**Ask:** a distinctness primitive honoured by the join — either a body builtin (`?a != ?b` / a reserved
`distinct_from` that the engine satisfies for any two non-unifiable nodes), or the deferred
`functional`/`injective` relation property (flag "≥2 distinct S for one O" without materializing pairs).
With it, disjoint-writes — the shared frame rule behind a whole family of "no two distinct X share a Y"
constraints — becomes a one-line CNL rule; without it, that entire class can't move out of Python.
**Positive:** recursion + stratified negation are strong enough that the *reachability* half ported
verdict-identically, so this one primitive is the single gate to porting the disjointness half too.

> **FIXED (2026-07-14).** `ask_goal(..., commit=False)` is a READ-ONLY query, mirroring
> `suppose(commit=False)`: reasoning runs inside an ephemeral PENCIL scope (the SUPPOSE mechanism —
> derivations are scope-tagged control relations, never a `graph.copy()`), the answer is read in-scope,
> and the scope is swept in a `finally`. The repro's poison test now holds: derive `c contested yes`
> read-only, re-query with an EMPTY rulebank → `['no']`. Supported for yes/no (incl. existential) and
> who questions; a why-question exists to MATERIALIZE the derivation it renders and n-ary renders through
> the forward reader, so both RAISE under `commit=False` (loud, never silently committing). Two deliberate
> boundaries: an `ask_user`-confirmed fact still inks (user-asserted EVIDENCE is new knowledge, not a
> derivation), and a skolem-minting rule (`<foo>?`) still mints its witness entity node (only derived
> RELATIONS are pencil). `check()` gained the underlying `scope=` parameter (threaded to its
> `chain_sip`/`_facts_matching`), so the firmware verdict itself can run penciled. Tests in
> `tests/test_feedback_fixes.py` (`test_ask_goal_commit_false_*`, `test_ask_goal_default_still_commits`).

## 12. `ask_goal` COMMITS derived facts to the graph — no read-only mode, surprising for a "query" verb

`ask_goal` materializes what it derives *onto the input graph*. Deriving a fact, then re-querying with an
**empty** rulebank, still returns it:

```python
import ugm as h
from ugm import load_machine_rules, ask_goal
G=h.Graph(); i={}
n=lambda x:i.setdefault(x, i.get(x) or G.add_node(x))
G.add_relation(n("a"),"writes",n("c")); G.add_relation(n("b"),"writes",n("c"))
ask_goal(G,"is c contested yes", load_machine_rules("?c contested yes when ?a writes ?c and ?b writes ?c"))
print(ask_goal(G,"is c contested yes", load_machine_rules("")))   # -> ['yes']  (EMPTY rulebank!)
```

`suppose` has an explicit `commit=` (default-`True`) knob for exactly this; `ask_goal` has none, so it
always inks. It bit me twice: (a) reusing one graph across several check-queries, an earlier rule's
derived conflict *stood* and poisoned the next query (I had to build a fresh graph per query); (b) it is
the reason pystrider's own detection goes through `suppose(commit=False)`, never `ask_goal`, against a
shared/persistent graph. If composition checks were authored as CNL and run via `ask_goal`, each check
would **mutate the very graph it is checking**.

**Ask:** a read-only path for `ask_goal` — an `ask_goal(..., commit=False)` (or a `query`/`derive_readonly`
sibling) that returns the derived answers without inking them, mirroring `suppose(commit=False)`. At
minimum, document that `ask_goal` materializes, so consumers querying a persistent graph know to snapshot.

---

### Net

The spike succeeded and the model (SUPPOSE + CHAIN over reified semantics, RECORD as the
trace) fit beautifully. The friction was almost entirely **silent failure modes** (#1, #2, #3,
#5, and #8a — a name-split join that quietly returns nothing): ugm tends to quietly do less
rather than error, which is costly when you're authoring rules/facts programmatically. A
strict/verbose mode that surfaces "I did not recognize / could not mint / dropped this / joined
across a split name" would remove most of the pain. The synthesis probes (retrieval + CHOOSE over
many small authored graphs) add an **addressing/attention** ask on top (#8): a get-or-create-by-name
helper and an id-addressed goal API, with focus reaching the retrieval path, not just `suppose`. And
#9 adds a **performance** ask distinct from the correctness ones: `load_machine_rules` validates by
running the bank on every call, so a consumer that reloads a static bank pays it repeatedly — a
load-without-revalidate / validated-once handle would remove a 65%-of-runtime footgun.

The newest asks (#11, #12) come from a different direction — trying to **author soundness checks AS CNL
rule-modules** rather than in Python (the grammapy convergence). The encouraging half: *reachability*
ported verdict-identically on recursion + stratified negation, so a real static-analysis check lives
happily in the rule language. The two gaps that stop the rest: **#11** no distinctness primitive, so any
"no two distinct X share a Y" constraint (disjointness / a frame rule) can't be expressed without O(n²)
hand-authored `distinct_from` facts — the single gate to porting that whole family; and **#12** `ask_goal`
inks its derivations, so a CNL-authored check run over a persistent graph mutates what it checks — a
read-only `ask_goal` (mirroring `suppose(commit=False)`) is wanted before checks can safely share a graph.
