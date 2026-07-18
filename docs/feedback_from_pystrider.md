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

> **FIXED (2026-07-14) — both asks.** (1) `ugm.query_goal(fact_g, goal, rules=…)` is the first-class
> TUPLE-GOAL query: read-only by DEFAULT (the #12 pencil-scope mechanism), no question parse / answer
> render, returns the goal-matching facts as `(s, p, o)` data — a bound endpoint echoes the goal's, a
> free slot comes back as a `ById` pin (`g.name(pin.node_id)` renders it). `rules=` takes the
> `load_machine_rules` list (reified fresh per call, `ask_goal`'s discipline) or an already-reified
> graph; `commit=True` opts back into materialization. (2) The compile-once half: `_lower_bank_rule` is
> memoized per `Rule` instance (lowering is a pure function of (rule, control_preds, guard) and the #9
> memo already shares Rule objects), so a static bank's ISA programs — including the QUESTION-FORM banks
> the CNL layer runs per question — are lowered once per process; and question RECOGNITION
> (`_parse_question`) is memoized on the question text (callers get isolated copies). Measured on the
> repro below: `ask_goal(commit=False)` 3.5ms → **1.1ms** per call (~3.2×), `query_goal` ~**1.0ms** —
> the remaining floor is the genuine demand-solving firmware (per-goal ISA fact lookups), not redundant
> setup; its constant-factor home is the Rust port (rust-engine-plan). Tests in
> `tests/test_feedback_fixes.py` (`test_query_goal_*`, `test_lower_bank_rule_is_memoized_per_rule`,
> `test_parse_question_memo_returns_isolated_copies`).

## 13. `ask_goal` has a large FIXED per-call cost (~2.8 ms) — dominated by the CNL question-string layer

Collected while porting grammapy's composition-soundness checks to CNL rule-modules (the convergence).
Each check builds a tiny graph and asks one `who …` question read-only. It *works* and is verdict-correct
— but routing four small combinator checks through `ask_goal` inflated the pystrider suite **55 s → 255 s**
(the app-synthesis tests call the checks many times). Profiling a single `who write_conflict yes` over a
**5-fact** graph (`?c write_conflict yes when ?a writes ?c and ?b writes ?c and ?a != ?b`):

```
per-call microseconds (avg 500)
  Accumulate.check (full)         : 3228 us
  - graph build only              :   56 us
  - load_machine_rules (memoized) :    2 us   (thanks to #9)
  - ask_goal(commit=False)        : 3240 us   <- effectively the whole cost
  - ask_goal(commit=True)         : 3191 us   <- commit=False adds ~nothing
  [ref] old Python owner-scan     :  2.8 us   <- the check this replaced (~1150x)
```

Two things localize it (avg 300):

```
minimal 1-fact / 1-rule / one 'is' question : 2764 us   <- ~2.8ms is FIXED, size-independent
chain_sip tuple goal, SAME derivation       : 1179 us   <- the firmware path is ~2.7x faster
ask_goal scaling: 2 facts=3153us  12=4665us  102=18670us  502=84370us
```

So: (a) there is a **~2.8 ms fixed floor** paid on every call regardless of problem size, and (b) roughly
half of it is the **CNL question layer** — `chain_sip` with a *tuple* goal does the identical derivation in
~1.2 ms, so parsing the `"who … yes"` string + rendering answers costs ~1.6 ms/call on top of the firmware.
(The fixed ~1.2 ms in `chain_sip` itself looks like per-call machine/rule setup — `load_machine_rules` is
memoized, but the lowered ISA program may be rebuilt per query.) The graph-size scaling is partly my rule's
`writes`×`writes` self-join, but the fixed floor is the dominant cost for the small graphs a per-composition
check uses.

**Ask (a performance one, like #9):** a low-fixed-overhead query path for consumers that run *many small*
queries. Concretely, either (1) a first-class **tuple-goal read-only query returning variable bindings**
(what `ask_goal` gives, but skipping the question-string parse/render — today `chain_sip` returns a count and
mutates the graph, so it isn't a drop-in), and/or (2) a **compile-once / cached lowered-program** handle so
the ISA program for a static rule bank isn't rebuilt per call (the analogue of #9 one level down). Either
would let a soundness check authored in CNL run at a cost comparable to the hand-written Python it replaced.
**Workaround available:** we can switch grammapy's `_cnl.derive` from `ask_goal` to the `chain_sip` tuple
path for the ~2.7x, but the fixed firmware floor remains.

> **FIXED (2026-07-14).** The read-side split-join DIAGNOSTIC (`_warn_name_split_join` → `chain._is_fact_entity`,
> feedback #8a) walks a query node's EDGE endpoints, and an endpoint is NOT guaranteed to be a minted node —
> a shared literal like `yes` reused across triples, or (the reproducible trigger) a consumer that passes a
> raw label where a node id is expected (`add_relation(a, "premium", "yes")`) wires an edge to an unregistered
> id. The guard now skips a phantom endpoint (`fact_g.has(other)`) — a non-node cannot be a fact entity a write
> competes for — instead of crashing on `is_control`'s `self._nodes[nid]` KeyError; a read-only warning helper
> must never abort the query. The originally-filed shape (a WELL-FORMED interned graph whose decision object
> `yes` is one shared node — the yes/no-policy case) already renders an identical correct trace on both the
> plain and `provenance=True` paths in the current build (a concurrent-work RECORD fix; the crash now
> reproduces only against a genuinely malformed graph). A malformed graph — a raw label as a node id — still
> SIGNALS, but past the guard and deeper, as a clearer `ProgramError: TEST referenced unbound register 'yes'`
> naming the phantom, not a `KeyError` inside a warning helper. Tests in `tests/test_feedback_fixes.py`
> (`test_why_provenance_over_shared_literal_object`, `test_split_join_guard_tolerates_phantom_endpoint`).

## 14. `ask_goal(..., provenance=True)` raises `KeyError` on a shared object node (before deriving anything)

Found building rulestrider (Phase 2 Track B — anomaly-checking a CNL rule bank). Asking a plain
`why …` renders a correct multi-hop trace; asking the *same* question with `provenance=True` raises
inside the read-side name-split-join guard, before any derivation runs:

```python
POLICY = "?m gets_discount yes when ?m premium yes and ?m big_spender yes"
g = graph([("alice","premium","yes"), ("alice","big_spender","yes")])   # 'yes' is one shared object node
ask_goal(g, "why alice gets_discount yes", load_machine_rules(POLICY))                    # OK -> real trace
ask_goal(g, "why alice gets_discount yes", load_machine_rules(POLICY), provenance=True)   # KeyError: 'yes'
```

```
File ugm/cnl/query.py:419  in ask_goal ->  _warn_name_split_join(graph, q)
File ugm/cnl/query.py:342  in _warn_name_split_join ->  ... _is_fact_entity(graph, n)
File ugm/chain.py:168      in _is_fact_entity ->  if other != n and not fact_g.is_control(other) ...
File ugm/attrgraph.py:316  in is_control ->  return self._nodes[nid].control      # KeyError: 'yes'
```

`_is_fact_entity` iterates neighbours of a query node and calls `is_control(other)` on a neighbour id
`'yes'` that isn't in `self._nodes` — looks like it's handing `is_control` a *name*/label where a node id
is expected, or a shared literal object (`yes`, reused across many triples) isn't registered the way the
guard assumes. It only fires on the `provenance=True` path (the plain `why` path is fine), and only when
the object is a shared/reused node. **Not blocking** — read-only `commit=False` for detection + a
fresh-graph plain `why` for the trace is the working pattern (a prior `commit=True` query otherwise
materializes the derived fact, so a later `why` collapses to `(given)` instead of threading the rule —
worth a doc note too). But `provenance=True` is unusable for the trace whenever a decision object is a
shared literal, which for a yes/no policy is always.

---

> **FIXED (2026-07-18) — both asks built, and the headline symptom turned out to be a THIRD bug.** Your
> reframing is the right one and we took it: the substrate and the mint behaviour stay exactly as they are;
> the addressing VOCABULARY was what was missing. (An earlier draft's fabricated-name ask would have re-seated
> identity in the label — the move the #8 arc spent itself undoing — so rejecting it was correct.)
>
> **(1) Definite-description addressing — the preferred ask, built.** `ByDesc(name, ((pred, obj), …))` is a
> goal endpoint that identifies a node BY ITS RELATIONS: `ByDesc("c", (("for_step", "s2"),))` is *the* `c`
> whose `for_step` is `s2`. It is `_find_skolem_witness`'s identity law promoted to the query surface, so it
> adds no substrate concept — `chain.resolve_description` filters the candidates by the described relations
> and RAISES unless exactly one survives (naming the count, so you know what constraint to add). Never a
> silent `[0]`-pick.
>
> **Enumeration is well-defined again, and it feeds (1).** `who` now answers per WITNESS NODE, not per
> witness NAME (`query._witness_answers`), disambiguating genuinely-distinct same-named nodes by the
> outgoing facts their siblings lack: `c (ast_arg world, for_step s2) is_a ast_call`. Each answer is thus
> *described* though none can be *named* — exactly your (1) — and the parenthetical round-trips straight back
> in as the `ByDesc`. Enumerate, then ask about one, with no id ever surfacing. Co-named nodes that are ONE
> coref identity (`_one_identity`) still render as a single line, so no ordinary CNL answer changed shape.
>
> **(2) `ById` through the tuple path — also built**, for the programmatic case. `ask_goal` accepts a
> structured goal `(qtype, s, p, o)` whose endpoints may be names, `ById` pins, `ByDesc` descriptions, or
> `None` (`query._tuple_query`), and `surface.explain` addresses `ById` endpoints instead of iterating
> `nodes_named`. Malformed tuples RAISE (arity, unknown qtype, empty predicate, non-endpoint, and a `why`
> with a free slot — which would otherwise explain whichever fact was found first).
>
> **(3) The headline loss was a separate bug, and it is fixed.** `why … (given)` was NOT the name-degeneracy
> it was filed under — the demand chain threads that rule correctly on a fresh graph. The real cause:
> check-before-derive suppresses the EMIT for an already-materialized fact (right for the FACT), but the
> firing's SUPPORT was never recorded either — so anything built by a PRIOR pass (a forward `run_bank`, an
> earlier committing query) was *permanently* unexplainable. Since you build AST structure with `run_bank`
> and then ask about it, you would have hit `(given)` no matter how the node was addressed.
> `chain._solve_demand_rule` now BACKFILLS provenance under `provenance=True`: it records the justification
> onto the EXISTING rel node, guarded by "has no rule support yet" (additive, inert, no duplicate
> justifications). This also generalizes the doc-note flagged under #14. *"Why is this line here?"* is now
> answerable about generated code, including structure built forward.
>
> Tests in `tests/test_feedback_fixes.py` (`test_who_enumerates_each_minted_witness`,
> `test_who_coref_mentions_still_render_once`, `test_tuple_why_over_byid_threads_the_rule`,
> `test_tuple_goal_supports_who_and_yesno`, `test_tuple_goal_rejects_malformed_loudly`,
> `test_bydesc_addresses_a_minted_node_structurally`, `test_bydesc_round_trips_from_the_enumeration`,
> `test_bydesc_that_is_not_definite_raises`). Suite 591 green.
>
> **BANDED PARITY (also 2026-07-18).** The possibilistic `who` fold keyed answers by name too, so a banded
> session collapsed minted witnesses exactly as the crisp path had — and worse, it MERGED their bands,
> reporting one verdict for several different things. It now keys by node and renders each witness with its
> OWN band (`c (for_step s1) is_a ast_call` / `c (for_step s2) is_a ast_call (likely)`). That exposed a
> second layer: a derived FORK fact is carried as a CONTROL-tagged rel, so the discriminator's control
> filter hid precisely the relations an uncertain witness was built from — two forked witnesses got empty
> discriminators and collapsed again. Under a banded read a genuine fork rel (`possibility._fork_scope_of`)
> now counts as a defining fact, while ordinary scaffolding still does not. A fully-certain graph answers
> identically under both stances (asserted directly). Tests:
> `test_banded_who_enumerates_witnesses_with_their_own_bands`, `test_banded_discriminator_sees_fork_facts`,
> `test_banded_and_crisp_who_agree_on_certain_facts`. Suite 604 green.
>
> One known edge remains, not blocking: `ByDesc` constrains on OUTGOING relations only (an
> inbound-constraint form is easy to add if you need it).

## 15. The QUESTION surface is name-addressed, but minted nodes are (correctly) nameless-by-design

**The most significant open ask** — it comes from the good news that #2 is fixed. Now that `name?`
skolem heads mint, we build real AST structure with rules (`experiments/ast_representation.py` in
pystrider: ordered statements, loop bodies, versioned repairs).

To be clear about where the problem is *not*: the substrate is supposed to be made of **nameless
nodes**, and `_find_skolem_witness` already states the law — *"a minted node is identified by how it
relates to the LHS match, not by a raw id or a fabricated name."* We agree with that, and the mint
behaviour follows it correctly. The gap is one layer up: **the CNL question surface is name-addressed**,
so it cannot ask about a node whose identity is structural. N minted nodes share one literal name, and
the question layer has no other handle to offer.

```python
RULES = "c? is_a ast_call and c? for_step ?s and c? ast_arg ?m when ?s says ?m"
FACTS = [("s1","says","hello"), ("s2","says","world"), ("s3","says","bye")]
# ... build g, run_bank(g, rules) ...

g.nodes_named("c")                      # ['n9', 'n14', 'n18']  -- three real, distinct nodes
ask_goal(g, "who is_a ast_call", rules) # ['c is_a ast_call']   <-- ONE answer for three nodes
ask_goal(g, "why c ast_arg world", rules)
                                        # ['c ast_arg world  (given)']  <-- not the derivation
ask_goal(g, ("why", ById('n14'), "ast_arg", "world"), rules)
                                        # AttributeError: 'tuple' object has no attribute 'lower'
```

Three separate problems fall out of the one cause:

- **Enumeration collapses.** `who is_a ast_call` reports a single answer for three nodes, because the
  answers are rendered by name. There is no CNL-level way to see that three things were built.
- **No provenance over generated code.** `why c ast_arg world` answers `(given)` rather than threading
  the rule that minted it. For this project that is the headline loss: the whole value proposition is
  *derived code you can ask "why is this line here?"* about, and that question is currently unaskable
  about anything a rule built.
- **`ById` doesn't reach this path.** It's the documented escape hatch for id-addressing, but
  `ask_goal` wants a question *string* here, so there's no way to say "why THIS node".

To be fair: ugm is **loud**, not silent — it emits a clear `UserWarning` ("names 'c', which resolves to
3 distinct nodes… address the intended node by id"). The warning is right, but it points at a remedy
(intern the name / address by id) that the query API doesn't currently offer for minted nodes.

**Asks, in preference order.** We deliberately are *not* asking for fabricated per-node names (an
earlier draft of this item did; it contradicts the nameless-substrate law above). The substrate is
right — the addressing vocabulary is what's missing:

1. **Structural / definite-description addressing in questions.** Let a question identify a node the
   same way the engine already does — by its relations rather than by a name. Something with the force
   of *"why does the `emit_call` whose `for_step` is `s2` have `ast_arg world`"*. This is exactly
   `_find_skolem_witness`'s own identity rule promoted to the query surface, so it needs no new
   substrate concept, and it makes enumeration (`who is_a ast_call` collapsing to one answer)
   well-defined again because each answer can be *described* even though none can be *named*.
2. **`why` / n-ary render over a `ById` endpoint**, so the tuple path can at least address a specific
   minted node programmatically. Lower-level and less pleasant than (1) — ids are the "raw id" the law
   warns against — but it would unblock us immediately.

Either unblocks provenance over generated code; (1) is the one we'd build on, and we think it's the
one consistent with the design.

> **FIXED (2026-07-18) — and the premise was INVERTED: independent NACs already worked; the CONJUNCTIVE
> form (the one you said "works") was silently broken on the demand engine.** Thank you for filing this —
> chasing it turned up a real correctness bug, not the feature gap it was filed as.
>
> **What was actually true.** The FORWARD engine has always partitioned `not` clauses into independent
> groups by their shared NAC-LOCAL FREE variables (`lowering._nac_groups`): atoms sharing one are a single
> existential (`¬∃x. A(x) ∧ B(x)`), atoms sharing none are independent negations that each block alone. So
> `run_bank` could express BOTH forms all along, and the "all `not` clauses fold into ONE conjunctive NAC"
> line in `cnl_reference.md` was simply wrong (now corrected). The DEMAND chain, however, decided every NAC
> atom SEPARATELY — which collapses the conjunctive form into the independent one.
>
> **So the two engines disagreed, on your exact rule.** With `?c body_first ?l when ?l body_has ?c and not
> ?x stmt_before ?c and not ?l body_has ?x` and a statement `z` that precedes `c1` but lives in ANOTHER
> body: `run_bank` derives `c1 body_first l1` (correct — the scoping works, as you observed), while
> `ask_goal` returned `(no answer)` — it blocked on `∃?x stmt_before(?x, c1)` alone, ignoring the `?l`
> constraint. Your report says the scoped form works; that held on the forward path you were exercising,
> and would have silently failed the moment you asked it as a question.
>
> **Fixed** by giving the demand chain the same partition (`chain._nac_atom_groups`, the twin of
> `lowering._nac_groups`) and deciding each group by a JOINED witness (`_nac_group_witnesses` — a small
> backtracking join over the group's atoms; a free slot's discovered node binds that var by `ById`, so
> identity is preserved across atoms). Boundness is read from the register file at decision time, so the
> partition reflects what this firing's SIP actually bound. A single-atom group is byte-for-byte the old
> path, so the blast radius is exactly the conjunctive case. Banded mode folds in: Π(group) is the best band
> its joined pattern is witnessed at, θ gates on that, and `N(¬group) = 1 − Π`.
>
> **Explanation fidelity, which the fix exposed.** A conjunctive NAC's atoms are assumed absent JOINTLY, so
> rendering them separately states a falsehood — "assumed not: l1 has anything" about an `l1` that
> demonstrably has something. Assumption records now carry an `a_group` tag (both engines), and `why`
> renders a group as one clause: `assumed not: l1 has anything and anyone before c1  (together)`. Additive —
> `assumptions_of` is unchanged, so RECONSIDER's per-atom dirty grains keep working (conservative, still
> correct); the new `provenance.assumption_groups` is what the renderer uses.
>
> **Gated differentially.** Forward vs demand over every subset of a small fact pool, across 7 NAC shapes
> (conjunctive, single existential, ground, independent pair, chained free vars, self-loop): **1792
> (rule, world) pairs, 0 divergences**. The same sweep against the pre-fix decision reports **560**
> divergences, so the gate is not vacuous. Tests in `tests/test_feedback_fixes.py`
> (`test_conjunctive_nac_agrees_across_engines`, `test_independent_nacs_each_block_alone`,
> `test_nac_engines_agree_differentially`, `test_conjunctive_nac_explains_jointly_not_per_atom`,
> `test_assumption_groups_recorded_by_both_engines`). Suite 601 green.
>
> **What this means for your navigate/check/recover loop:** the shape you expected to be the next wall — a
> guard on progress plus a guard on scope — works today on both engines, and is covered by
> `test_independent_nacs_each_block_alone`. Which form you get is carried by the VARIABLES, not by clause
> order or syntax: share a free var for a joint negation, use disjoint ones for independent negations.

## 16. Independent NACs — not blocking yet, but the next expected wall

Documented limit: all `not` clauses fold into ONE conjunctive NAC. That happened to be exactly right
for us — "the first statement of THIS body" needs the conjunction, and the scoped form works:

```
?c body_first ?l when ?l body_has ?c and not ?x stmt_before ?c and not ?l body_has ?x
```

(correctly ignoring a statement that precedes `?c` but lives in another scope). But two *independent*
negations — "is the body head" AND "has not already been emitted" — aren't expressible, and the
navigate/check/recover loop we're building will want exactly that shape (a guard on progress plus a
guard on scope). Filing it now as a known-limit heads-up rather than a request; if independent NACs are
cheap, they'd be welcome.

> **FIXED (2026-07-18).** `run_to_fixpoint`'s docstring now says it takes a lowered ISA program, names the
> arity failure as the misleading symptom, and points rule-bank callers at `run_bank(ag, rules)`.

## 17. (minor) `run_to_fixpoint` vs `run_bank` — the names invite the wrong call

`run_to_fixpoint(ag, program, keys)` takes a lowered ISA program; running a *rule bank* to fixpoint is
`run_bank(ag, rules)`. The obvious-sounding call fails on arity, not on type:

```python
h.run_to_fixpoint(g, h.load_machine_rules(RULES))
# TypeError: run_to_fixpoint() missing 1 required positional argument: 'keys'
```

which reads as "you forgot an argument" rather than "you want the other function". A line in the
docstring pointing rule-bank users at `run_bank` would save the detour.

> **FIXED (2026-07-18) — and fixing it uncovered a second, opposite bug in `stratify` itself.** You
> asked for option 1 (stratify inside `run_bank`), which is now what happens. Getting there was not
> mechanical, and the detour is the interesting part.
>
> **First attempt failed loudly, which was lucky.** Simply calling `stratify` inside `run_bank` broke CNL
> RECOGNITION — `load_machine_rules` started rejecting valid banks, because the recognition forms were
> being scheduled differently. Cause: **`stratify` ranked rules by NEGATED dependencies only.** Standard
> stratification also requires a rule to sit at or above its POSITIVE dependencies; without that, a
> PRODUCER can be pushed into a later stratum than its positive CONSUMER, and the consumer reaches
> fixpoint before the fact it needs exists — with nothing to re-run it. Minimal repro, where `out` is
> derived flat and LOST when stratified:
>
> ```
> D:  ?y z yes      when ?y is_a other
> B:  ?x tag yes    when ?x is_a seed and not ?x z yes     # NAC over D's head -> B is pushed later
> A:  ?x out yes    when ?x tag yes                        # no NAC -> stratum 1, runs BEFORE B
> ```
>
> So `run_bank` was unsound for derived negation (your #18) and `run_rules` was unsound for positive
> dependencies crossing a stratum boundary — the two forward entry points were wrong in opposite
> directions. `stratify` now builds the full dependency graph (every head atom registers as a producer,
> not just `rhs[0]`) and relaxes strata with positive edges at +0 and negated edges at +1.
>
> **One deliberate concession.** The sound ordering makes cycles through a negated edge detectable, and
> real ugm banks contain them (a recursively-derived predicate that is also negated somewhere) — banks
> both engines handle fine today. Newly REJECTING them would have been a regression dressed up as
> rigour, so `stratify` falls back to the historical NAC-only ordering for exactly those banks
> (`_stratify_nac_only`) and applies the sound ordering everywhere else. Nothing that worked stops
> working; everything without such a cycle gets correct scheduling.
>
> **Result on your repro:** `unmet_at -> ['i0']`, `satisfied -> []`. The forward and demand engines now
> agree (the demand chain was always right here — its NAF subgoal closes the negative's positive first),
> which is the same forward/demand parity theme as #16. `run_bank(..., stratified=False)` keeps the raw
> one-stratum primitive for a caller that has already stratified. `stratify` moved from
> `cnl/authoring.py` down to `production_rule.py` (it is pure rule analysis, and `run_bank` must call it
> without importing the CNL layer — recognition banks are built at import time); `authoring` re-exports
> it, so every existing import is unaffected.
>
> Tests: `test_run_bank_stratifies_negation_over_a_derived_fact`,
> `test_run_bank_and_demand_engine_agree_on_derived_negation`,
> `test_stratify_orders_a_producer_before_its_positive_consumer`,
> `test_stratify_falls_back_rather_than_rejecting_a_cyclic_bank`,
> `test_run_bank_stratified_false_keeps_the_raw_primitive`. Suite 610 green.

## 18. `run_bank` does not stratify, so negation over a DERIVED fact is silently wrong — and permanent

Cost a real bug: a build loop reported a demonstrably wrong program as OK. `run_bank` applies a
match-time NAC filter but evaluates rules in whatever order the round reaches them, so a rule whose
`not` ranges over a predicate ANOTHER rule in the same bank produces can be decided before that rule has
fired. Because the graph is monotone, the wrong answer is then **permanent** — nothing retracts it.

```python
BANK = ("?st unmet_at ?i when ?st is_a step and ?st at ?i and ?st wants ?x "
        "and not ?o is_a observation and not ?o at ?i and not ?o text ?x\n"
        "?p satisfied yes when ?p is_a procedure "
        "and not ?st unmet_at ?i and not ?st of_procedure ?p")
# facts: report is_a procedure; st0 is_a step, of_procedure report, at i0, wants hello_bob;
#        o0 is_a observation, at i0, text bob        <- the expectation is NOT met

run_bank(g, load_machine_rules(BANK))
#   unmet_at  -> ['i0']      (correct)
#   satisfied -> ['yes']     (WRONG — and it sticks)

for stratum in stratify(load_machine_rules(BANK)):    # the cure
    run_bank(g, stratum)
#   satisfied -> []          (correct)
```

`stratify` exists, is documented, and does exactly the right thing — it just is not applied by
`run_bank`, and nothing warns. The `run_bank` docstring mentions the NAC filter but not the stratum
requirement, so the natural reading ("forward-chain these rules to fixpoint") is a trap for any bank
with derived negation. **Ask:** either stratify inside `run_bank` by default (it is a static property of
the bank, and `load_machine_rules` already validates), or raise/warn when a bank contains a NAC over a
predicate the same bank derives, with the fix in the message. A silent wrong answer that then becomes
unretractable is the worst shape this could take. Pinned our side in
`tests/test_build_procedure.py::test_a_bank_with_negation_over_a_DERIVED_fact_must_be_stratified`.

> **DOCUMENTED + PINNED (2026-07-18).** Agreed on all counts — nothing to fix in the engine, and your
> diagnosis is exactly right: the backfill can only record what the chain can RE-DERIVE, and a rule whose
> effect falsifies its own body cannot be. It is now stated where each audience will meet it: in
> `docs/reference/firmware_reference.md` §7 (the provenance section, as a rule for choosing the capture
> mode) and at the backfill itself in `chain._solve_demand_rule`, so the next reader of that code sees the
> limit next to the mechanism. Pinned as behaviour by
> `test_self_extinguishing_rule_needs_forward_provenance`, which asserts BOTH halves — forward
> `provenance=True` records the justification, and the backfill alone leaves `(given)` — so the limit
> cannot silently drift into looking like a bug later. Thanks for writing it up rather than filing it as
> one; "self-extinguishing rule" is the right name for the class and we have adopted it.

## 19. (not a bug — a note) Provenance must be captured FORWARD for self-extinguishing rules

The #15 backfill works well, but it necessarily depends on the demand chain being able to RE-DERIVE the
fact. A large and interesting class of rule cannot be: one whose own effect destroys its firing
condition. Repair rules are exactly this shape —

```
gc? is_a ast_call and gc? callee greet and ... and ?pr version arg_v2
  when ?pr is_a emit_print and ?pr arg_v1 ?v
       and <no observation at ?i shows the wanted text>      <- unmet
```

— fires *because* a line is wrong, and its effect makes the line right, so the NAC no longer holds and
`why` collapses to `(given)`. Running the bank with `run_bank(..., provenance=True)` records the
justification at firing time and the trace is then complete, threading back through the minted structure
to the original spec fact, with the conjunctive NAC rendered jointly (`assumed not: … (together)` — the
#16 explanation fix, which reads very well here).

Worth a line in the docs: *if a rule's effect can falsify its own body, capture provenance forward; the
demand path cannot reconstruct it.* Nothing to fix in the engine as far as we can tell — but it took a
failing `why` to notice, and it is the audit trail for the most interesting facts in our system.

> **ANSWERED + FIXED (2026-07-18). You were not holding it wrong, and the symptom was worse than you
> measured: replan did not pick in staging order — it picked ALL of them.** Your three repairs did not
> race and lose; every one of them was committed and every one of them ran. So the pin you wrote is
> true but under-states it, and it will now fail — please update it.
>
> **(1) Is cost-ranking intended to govern replan?** It is intended to govern COMMITMENT, and replan is
> commitment, so yes. Worth stating plainly because it is the load-bearing fact behind all three of your
> questions: `dominated`/`best` — i.e. the `cheaper_than` facts your `rank` tool derives — is the banks'
> **only** narrowing criterion. Nothing else in `planning.cnl` picks one op over another. (The
> "conjunctive NAC keeps it to ONE per need" comment on the commit rule was wrong and is corrected: a
> forward round collects all its matches before any fires, so two equally-cheap *or* two unpriced `best`
> ops both commit and both act. Your `rank` should impose a TOTAL order — break ties deterministically —
> which is the §8 calculator's job, not the bank's.)
>
> **(2) Were you missing an authoring step?** No. `add` + `pre` + `cost` is exactly right. The gap was
> ours: REPLAN deliberately bypasses the planner's `<need>`/commit path (`procedure.cnl` documents why —
> routing recovery through commitment pushes INVOKE's `chosen` past `ready` in the stratifier and
> re-opens the ready-before-unmet race), and `cost_settled` — hence the whole rank call — lives only on
> that path. So the alternatives were never priced at all. That is precisely what your trace shows: rank
> fired for `['expand','lower','emit','repair_greet']` because those reached commitment through
> `<need>`; the DISCREPANCY-selected ones never could. With no `cheaper_than` between them, the sole
> criterion was absent and the REPLAN rule matched every untried producer at once.
>
> **(3) "Try the smallest edit first" — now authorable, and it is just the costs you already stage.**
> `corpus/procedure.cnl` gained three things: the same `rank` call emitted for the untried producers of
> an unmet effect; an `outranked_by` block per cheaper untried rival (Phase B's block/unblock idiom); and
> the REPLAN rule gated on having no such block. Verified by INVERTING the declared costs — the choice
> inverts, and only the chosen alternative runs. The two `drop ?alt outranked_by ?x` rules are
> load-bearing, and cost us a wrong first cut: the block is monotone, so without them a cheaper
> alternative that ITSELF fails strands the next-cheapest forever and the effect stays silently
> unachieved — the exact shape of failure this arc exists to prevent. Cascade is now covered.
>
> **What still holds, pinned honestly:** with no cost staged, nothing is `cheaper_than` anything and
> every untried producer still commits. We did not invent a tiebreak for that case — the bank has no
> basis for one, and a total-order `rank` supplies it where it belongs.
> `test_replan_without_cost_knowledge_commits_every_untried_producer` states the limit so it cannot
> drift into looking like a bug.
>
> Tests in `tests/test_procedures.py` (`test_replan_tries_the_cheapest_alternative_not_the_first_staged`,
> `test_replan_falls_through_to_the_next_cheapest_when_the_cheapest_also_fails`, and the limit pin
> above); design note in `docs/design/procedures_design.md` §Slice 3. Suite 613 green.

## 20. (question) Are replan-selected ALTERNATIVE PRODUCERS meant to be cost-ranked? They are not today

Not filed as a bug — we may be holding it wrong, and the answer changes how we author repair operators.

`planning.cnl` makes ranking the §8 comparison-as-calculator boundary: the `rank` tool derives
`cheaper_than`, and `dominated`/`best`/`chosen` select on it. We built a real `rank` tool (costs staged
as `?o cost ?c` knowledge; the tool only does the arithmetic) expecting it to order the repair attempts
in a navigate/check/recover loop, where several operators all `add` the same effect (`output_ok`) and
differ only in how invasive the edit is.

It does not order them. Verified by INVERTING the declared costs and observing the attempt order
unchanged — worth stressing, because the costs initially agreed with staging order, so the first
"working" run proved nothing. Tracing the tool shows it is invoked for the ordinary plan steps and the
FIRST repair, and never for the later alternatives:

```
rank tool invoked for: ['expand', 'lower', 'emit', 'repair_greet']
repairs actually run:  ['repair_greet', 'repair_shout', 'repair_audit']    # staging order, not cost
```

So the alternatives reached through DISCREPANCY -> REPLAN never reach `cost_settled` and are never
ranked; their order is whatever order they were staged in. `planning_teardown.cnl` does drop `ranked` /
`cost_settled` / `best` / `chosen` / `done` on `<replan> active`, which reads as "re-plan from scratch,
so re-rank" — but in our runs the ops do not appear to come back round through Phase C.

**Questions:** (1) is cost-ranking intended to govern which alternative producer replan picks, or only
the initial plan? (2) if intended, is there an authoring step we are missing — do alternatives need to
become `candidate`s of the need in some way our staging (`add` + `pre` + `cost`) does not establish?
(3) if not intended, is there a supported way to express "try the smallest edit first" over a set of
operators that all achieve the same effect? That preference is real knowledge in a repair loop, and we
would rather author it than hardcode an order.

Our side is pinned either way (`test_rank_is_a_real_calculator_but_does_NOT_order_replan_alternatives`),
so if this gains cost-ordering the pin fails loudly and we update.

> **BUILT (2026-07-18) — the primary ask; the STRONGER form measured and deliberately NOT shipped as a
> warning.** `describe_rules(rules)` returns exactly the line you specified, and `mint_keys(rule)` returns
> it as data (`MintKey(rule, head, key, unused_in_head)`). Your two repros:
>
> ```
> rule '…': mints `n?` — one node per (?x)
> rule '…': mints `n?` — one node per (?x, ?y)   [?y appears in no head atom — multiplies the mint
>                                                 without distinguishing it]
> ```
>
> No semantic change; the key is computed from the rule's positive LHS variables in first-appearance
> order, which is what "keyed on the whole match" means operationally. Lives in `production_rule.py`
> (pure rule analysis, where `stratify` moved for the same reason), exported from the package root.
>
> **On the optional warning — we measured before wiring it, and the measurement said don't.** Your
> stronger form ("warn when a mint head's key includes a variable that appears in no head atom") fires
> **24 times on ugm's own recognition banks** — `RULE_FORMS` 6, `QUESTION_FORMS` 10/10,
> `MACHINE_RULE_FORMS` 7, `FORM_RULES` 1 — all of them believed correct. The reason is a legitimate
> pattern your own note anticipates: the **anchor idiom**, where a body variable binds the
> sentence/statement the mint belongs to and is deliberately absent from the head (`ask.yesno.is_a`
> mints `<query>?` per `(?s, ?qs, ?qo)` with `?s` the sentence anchor). So `unused_in_head` does not
> separate the accidental case from the intentional one, and as a default warning it would train people
> to ignore it. It is reported in the line when you go looking, which is where it is useful.
>
> If you want it as a gate on YOUR banks, `mint_keys` gives you the datum:
> `[mk for r in rules for mk in mint_keys(r) if mk.unused_in_head]` — a one-line assertion in your suite,
> where you know the anchor idiom isn't in play. That seemed better than us guessing a heuristic that
> distinguishes the two, since we don't think a reliable one exists.
>
> Tests in `tests/test_feedback_fixes.py` (`test_mint_key_reports_what_a_skolem_head_is_a_function_of`,
> `test_an_unrelated_body_atom_multiplies_the_mint_key`,
> `test_mint_keys_are_empty_for_a_rule_that_mints_nothing`,
> `test_unused_in_head_is_reported_but_never_warned_on` — which pins the no-warning decision so nobody
> promotes it without re-measuring). Suite 632 green.
>
> ---
>
> **A calibration note, now that there are four instances of it.** Your reports are consistently
> excellent at locating *where* the problem is and consistently unreliable about *which direction* it
> runs — and the second half is worth you knowing, because it changes how much weight to put on your
> own diagnosis when you file.
>
> - **#16.** You filed independent NACs as the gap and said the conjunctive form "works". Inverted:
>   independent NACs already worked on both engines; the CONJUNCTIVE form — the one you reported
>   working — was silently broken on the demand chain. It held on the forward path you happened to be
>   exercising and would have failed the moment you asked it as a question.
> - **#18.** You filed `run_bank` as failing to stratify. True, but fixing it exposed the opposite bug
>   in `stratify` itself: it ranked by NEGATED dependencies only, so a producer could be scheduled
>   after its positive consumer. The two forward entry points were wrong in opposite directions, and
>   only one of those directions was the one you saw.
> - **#15.** You filed the `why … (given)` loss under name-degeneracy. The addressing gap was real and
>   we built for it, but it was not the cause: provenance was never recorded for facts built by a prior
>   pass, so you would have hit `(given)` however the node was addressed.
> - **#21.** "Almost always accidental" is confidently wrong against our own banks — 24 correct uses of
>   exactly that shape.
>
> The pattern isn't carelessness; it's structural. You are reasoning from one engine's observed
> behaviour, and this codebase has two engines — a forward driver (`run_bank`) and a demand chain
> (`chain_sip`) — with a parity contract between them. So "X works, Y doesn't" is very often "X and Y
> disagree, and the one you tested is either the wrong one or accidentally right." You cannot see that
> from outside, and frankly we did not see it from inside either.
>
> **The ask is NOT to omit the diagnosis — keep making it, but mark it as a hypothesis.** We want to
> be precise here, because the obvious lesson ("just report symptoms") is the wrong one and we nearly
> wrote it: your wrong premise in #16 is exactly what found that bug. Saying "the conjunctive form
> works" is what sent us to look at the conjunctive form; falsifying it is where the parity bug was.
> A bare symptom would probably have left it buried. Same in #18 — the mechanism you named was right
> enough to make us look at `stratify`, which is where the *opposite* bug was sitting.
>
> So the diagnoses are load-bearing even when inverted. What costs time is when they arrive stated as
> fact, because we then start from your model instead of testing it. **#20 is the format that works
> best** ("we may be holding it wrong… (1) is this intended? (2) are we missing an authoring step?") —
> it was the easiest item in the batch to answer well, and it still carried your full analysis. Your
> `not-a-bug` notes (#19) are the same shape and equally valuable. One sentence of hedging is the whole
> difference; you lose nothing by adding it.
>
> None of this is a request to file less. The four inversions above are four real correctness bugs that
> exist in ugm only because you went looking — the parity bug in #16 in particular was invisible from
> inside this repo and is the most serious thing found in the whole arc.

## 21. (question) Is a mint head's SKOLEM KEY meant to be discoverable at authoring time?

REWRITTEN after your note above, and the note was right about this item specifically — see the
retraction at the end. Filed in the #20 shape: here is our model, we may be holding it wrong.

Not a bug: the semantics are right, documented, and we depend on them. What we are asking about is
**discoverability**, because this is the one mistake we keep making, it never errors, and the symptom
appears far from the cause. It cost us three bugs in one day.

A skolem is keyed on the **whole match**, not on the head. That is correct — it is what makes the minted
node a genuine Skolem function of the variables it depends on, and `_find_skolem_witness` says so ("a
minted node is identified by how it relates to the LHS match"). But nothing about a rule's *text* makes
its arity visible, and a body atom added for a completely unrelated reason silently multiplies the mint:

```
n? is_a made and n? of ?x when ?x is_a thing                       -> 1 node
n? is_a made and n? of ?x when ?x is_a thing and ?x tag ?y         -> 1 node PER TAG
```

`?y` is not in the head and is not used for anything; it still multiplies. In our case the body atom was
`?st wants ?x` inside a shared "is this line unmet?" condition, composed into a repair rule. A statement
with one expectation minted one node; a statement inside a `for` loop wants one text per element, so the
same rule minted N structurally-identical nodes and gave one statement N `arg_v2` values. Nothing failed
— the duplicates were interchangeable because the head names no `?y`, so the emitted program was correct
while the graph was quietly wrong, and a later rule that *did* mention `?y` would have made it
nondeterministic.

**The ask:** at `load_machine_rules` time (or behind a flag / a `describe_rules` helper), report each
mint head's key — the tuple of variables the skolem is a function of:

```
rule '…': mints `n?` — one node per (?x, ?y)
```

**RETRACTED — the part of this we stated as fact.** An earlier draft proposed a stronger form: warn
when a mint key includes a variable appearing in no head atom, "since that is the shape that is almost
always accidental". You have 24 correct uses of exactly that shape, so that claim is simply false, and
a warning built on it would have been noise you would rightly have ignored. We had a sample of two —
both of them our own bugs — and generalized from it. Withdrawn; please do not build the warning.

**What survives, as a question rather than a request:** (1) is a mint head's key meant to be something
an author reasons about explicitly, or is it meant to stay implicit because in practice the body IS the
intended scope and our two cases were just wrong rules? (2) if the former, is there an existing way to
inspect it that we have missed — something already in the CNL tooling or a debugging entry point? (3)
if it is genuinely absent and you think it is worth having, we would use it, but we no longer have a
basis for saying how often it would fire on real banks. Ours is not a representative sample.

Related, and offered only as an observation: `reject_rhs_only_head_vars` refuses an *ill-founded* head
and that check is genuinely useful — we tripped it while perturbing a pattern and it was right to stop
us. Whether the same spirit extends one step earlier ("this head means more than you may think") is
your call, not ours; we cannot see the false-positive rate from out here, which is precisely the thing
we got wrong above.

---

## 22. (question) Should an untried-but-INAPPLICABLE alternative be able to OUTRANK a costlier one?

We may well be holding this wrong, so this is a question rather than a report — and given how #20 went
(our confident causal story was inverted and yours was the right one), please read the diagnosis below as
our current hypothesis, not as a claim about your engine.

**What we hit.** We added a fourth recovery operator to the build loop in `experiments/build_procedure.py`
— it restructures the program (wraps statements in a missing guard) rather than editing a payload, so
under our "how much does this edit disturb" pricing it is the most expensive at `cost 4`. It never runs.
The planner stops after the two cheaper repairs that do not apply, and the build refuses.

    repair_greet  cost 1   ran, did not apply
    repair_audit  cost 2   ran, did not apply
    repair_shout  cost 3   NEVER RAN - its `payload_greeted` precondition cannot hold on this spec
    repair_guard  cost 4   never reached

**Our hypothesis.** `procedure.cnl` derives exclusion from having FAILED:

    ?o excluded <yes> when ?o discrepancy ?e

`repair_shout` never runs, so it is never `done`; it never fails, so it is never `excluded`. Both drop
rules for `?alt outranked_by ?x` are therefore never satisfied, and the block it places on `repair_guard`
is permanent. The cascade seems to assume every cheaper rival will eventually be TRIED — which holds when
alternatives differ only in cost, and stops holding once one of them declares a precondition that the
current world cannot satisfy.

**Why we think it is the cost and not our rule.** Varying that one number and changing nothing else: at
`cost 3` or below `repair_guard` runs and the build verifies; at `4` it is stranded. The operator itself
is fine — applied directly it produces the intended program and both our oracles pass.

**What we are unsure about, i.e. where we may be holding it wrong:**

1. Is an operator whose precondition cannot currently hold meant to be `excluded` (or simply not to
   participate in `outranked_by` at all)? A clause like `?x applicable` on the `outranked_by` rule would
   do it, but we cannot tell whether "applicable" is a notion the planner deliberately keeps out of the
   ranking layer.
2. Is declaring `needs=("payload_greeted",)` on an alternative producer the intended way to order two
   repairs at all? We introduced it in the compose slice so that `repair_shout` could not run before
   `repair_greet`. If preconditions on ALTERNATIVES are not really meant to gate replan candidates, the
   authoring fix is ours and the ranking layer is innocent.
3. We have only exercised this forward (`run_bank`); we have not checked whether the demand engine agrees
   about `outranked_by` here, and per #16 that is exactly where our reasoning has been wrong before.

**What we did on our side, for now:** kept `cost 4` (it is the honest number under our stated principle)
and pinned the stranding, so if this ever gains a fix the pin fails loudly and we come back to it. We
deliberately did not re-price to 3 — that would only work by winning an alphabetical tiebreak, and our own
notes say the tiebreak carries no meaning.

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
With #11 and #12 both shipped, **all four** grammapy combinators now run as CNL rule-modules — which
surfaced **#13**, the second **performance** ask (after #9): `ask_goal` carries a ~2.8 ms fixed per-call
floor (about half of it the CNL question-string layer — the `chain_sip` tuple path is ~2.7x faster), so a
soundness check called O(many) times pays dearly (suite 55 s → 255 s). A low-fixed-overhead query path
(tuple-goal bindings, and/or a compile-once lowered program) would let CNL-authored checks run near the
cost of the Python they replaced. Correctness is not in question — this is purely the price of running a
hot inner check through the full CNL question interface.
