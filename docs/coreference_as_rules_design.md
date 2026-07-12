# Coreference as declared rules — a reassessment of Phase 8 "D"

> **Status: ACTIVE. Sequence 1→2→3→4→5 approved by the user (2026-07-12); Stages 1–4 DONE (Stage 4 core;
> `canonicalize` deletion is optional follow-up), Stage 5 (docs/boundary) next.**
> This supersedes
> the mechanical-rebind framing of "D" in `implementation_plan.md`. Written after C (id-addressed goal path,
> `ById`) landed and a design conversation redirected D away from a mechanical ingest merge toward
> **coreference as declared rules**. Graded-closeness semantics (open question #2) settled as per-dim
> `1 - |Δ| >= threshold` for Stage 1; multi-dim embedding cosine is a later refinement.

## The doubt that started this

D was originally "id-address the CNL boundary + relocate same-name binding to ingest (one node per name)."
The user rejected the mechanical half: **deciding coreference by a fixed "same name ⇒ same node" ingest
policy bakes an NLP judgment into the engine.** In real language two "ada"s may or may not be one person;
only context/domain knowledge decides. This is the same principle the whole project rests on — *domain
logic lives in banks, as declared data, never engine sniffing* — applied to identity.

So: **every mention stays a separate node. Coreference becomes DECLARED, defeasible, domain-authored
data**, not an ingest default.

## The chosen mechanism — a value-equality / closeness match primitive

Coreference-as-a-tool (`wire_same_as`, `canonicalize`) exists *because the path-based rule language cannot
join on names* (`forms.py:464`): the matcher binds variables to **nodes** and joins on shared **topology**;
there is no "these two nodes have equal name" predicate. To make coref a genuine rule we add exactly that
missing capability:

> **A match-time value-EQUALITY (and graded "close-enough") condition** that compares an ATTRIBUTE VALUE
> across two bound variables — the substrate's first declared VALUE-join, added deliberately alongside the
> default topological join.

It has a natural home: it mirrors the existing **graded α-cut** (`GradedCondition` →
`rule_graph.write_rule` reifies `<graded>` → `chain._read_graded`/`_graded_ok` checks it during matching).
The graded α-cut is already a match-time value TEST on *one* var's attributes; this is the *two*-var
sibling.

With it, coreference is ordinary bank data the author writes (or doesn't):

```
?x same_as ?y  when  ?x is a person and ?y is a person and  <same-value ?x ?y name>
?x same_as ?y  when  ?x is a star   and ?y is a star   and  <close-value ?x ?y embedding 0.9>
```

`same_as_rules` (already present) then propagate facts across the derived `same_as` — the (2) "asserted /
derived identity" half stays exactly as-is. Only the *automatic same-name* default (1) is removed.

## The load-bearing finding — same-name coref needs the id-addressed core

The matcher's env binds each variable to a node's **name**, not its id (`chain._facts_matching` returns
names; `_bind` binds tokens to names). Consequence:

- Two distinct nodes both named "ada" **collapse to the same binding** (`?x="ada"`, `?y="ada"`). A rule
  `?x is a person and ?y is a person` sees ONE person, and `same_value ?x ?y name` would emit
  `ada same_as ada` (a self-loop) — it can never *relate the two distinct nodes*.
- To distinguish them the env must bind **node ids** (`?x=n5`, `?y=n7`, both name-value "ada" →
  `same_as(n5,n7)`). **That env-binds-by-id change *is* D's original id-addressed-core rewrite.**

So the capability splits cleanly by dependency:

| coref rule uses…                          | works in… | why |
|-------------------------------------------|-----------|-----|
| **graded/embedding closeness**, or equality across **different** names (morning≈evening star) | **today's core** | differently-named vars are already distinct bindings |
| **same-name** equality (two "ada"s)       | **id-core only** | name-keyed env collapses same-named nodes |

**C already paved part of the id-core:** `_facts_matching` can bind/return `ById` in bound slots and walk
from an id; the remaining step is binding ids in the FREE slots too. So the id-core is more reachable
post-C than the original plan assumed.

## What C already delivered (Stage 0 — DONE)

`ById` endpoints + `resolve_write_node` + `validate_ids`; the matcher walks from a pinned id; the three
write points route through one site. The boundary primitives the id-core needs already exist.

## Staged roadmap (effort / risk)

- **Stage 1 — value-equality/closeness match primitive. ✅ DONE 2026-07-12** (331 passed;
  `tests/test_isa_value_match.py`). `ValueMatch` on `Rule` (`var_a, var_b, dim, threshold?`), reified like
  `GradedCondition` (`rule_graph.write_rule` → `<value_match>` node), read + checked in the demand chain
  (`chain._read_value_matches`/`_value_matches_ok`, beside `_graded_ok`). Exact equality for a VALUED `dim`;
  graded closeness `1 - |Δ| >= threshold` when set. Forward path REFUSES loudly (`Unlowerable`) rather than
  fire unconstrained — the forward-APPLY value-JOIN op is a later companion (mirrors the graded α-cut, whose
  APPLY half is likewise a residual). Reflexive self-pairs + same-NAME distinction await the id-core (Stage
  3). **Was: medium effort, low risk — held.**
- **Stage 2 — coref-as-rules, validated on the current core. ✅ DONE 2026-07-12** (335 passed). CNL surface
  `?x same DIM as ?y` (exact) / `?x close DIM as ?y` (graded; `DEFAULT_CLOSENESS=0.8`), folded by
  `authoring._value_match_form` into `Rule.value_matches`. End-to-end demo: two bodies with close `bright`
  embeddings derive `same_as` via the rule, and `same_as_rules` compose a fact across it (`is eveningstar
  visible` → yes; far `pluto` → no; no-rule → no). *Proved the direction with no engine rewrite.* **Was:
  medium effort, low risk — held.**
- **Stage 3 — id-addressed core (env binds ids). ✅ DONE 2026-07-12** (339 passed;
  `tests/test_isa_idcore.py`). The matcher binds node ids in FREE slots (`chain._facts_matching` returns a
  `ById` for a discovered node, not its name); a head LITERAL meeting a `ById` demand endpoint is matched
  against the id's NAME (`_unify_head_with_demand`/`_endpoint_name`); `_graded_ok` reads a `ById`-bound var
  through `_bound_entity_nodes`; EMIT already used the bound id (via `resolve_write_node`, C). The predicted
  "high effort / high risk touching every reasoning path" was OVER-estimated: because C had made every
  downstream consumer `ById`-aware, the change reduced to "free slots return `ById`" + two small
  read-side fixes. One user-boundary fix followed: `gather_open_premises` resolves demand endpoints id→NAME
  (the ask speaks names) and dedups the id/name form of a premise. Bonus: full suite ~161s→~74s (pinning one
  id beats iterating same-named candidates). *Unlocks same-name value-coref* — two distinct nodes both named
  "ada" now relate via a same-name `ValueMatch`. **Was: high effort, high risk — came in far lighter.**
- **Stage 4 — same-name coref as rules + retire mechanical coref. ✅ DONE 2026-07-12 (core; 340 passed).**
  Two decisions settled it. (a) **User chose the declared-value-match-bank direction** over the ingest
  naming policy — which surfaced a HARD dependency: value-match rules refused in the FORWARD engine (Stage 1
  residual), but `load_corpus` composes coref forward, so the residual had to land first → **forward
  value-JOIN op `machine.VMATCH`** (mirrors `GRADE`; `lowering.lower_value_matches`). (b) **Per-type coref
  hit the untyped-entity wall** (an entity in subject vs object position has no shared type handle — broke 16
  tests). Resolved with a **universal surface-mention marker**: `forms.mark_mentions` tags every entity
  `is_a <mention>`, and `same_name_coref_rules()` is ONE rule binding both vars from that marker + a `name`
  value-match. This SEPARATES marking ("what is an entity", policy-neutral) from the coref DECISION (a
  CNL-authorable rule) — the clean win over `wire_same_as`, which fused them. Position-agnostic, so untyped
  entities corefer; decidable via CNL (scope the body, swap the criterion, assert identity, or drop). Marker
  filtered from `derived_triples`/`focus.utterance_subjects`. `load_corpus`/`load_facts` retired
  `wire_same_as` as the default. **Was: medium/medium — the VMATCH prerequisite made it heavier.** FOLLOW-UP
  (optional): delete the retired `canonicalize` merge + rewrite its `test_new_core` users; `wire_same_as`/
  `coref_in_context` kept as opt-in tools. OPEN: auto-inject the universal rule (current) vs silent default.
- **Stage 5 — finalize boundary migration + docs.** `ask_goal`/`check`/`suppose` resolve names→ids at the
  surface (Half A); update `CHANGELOG`, `engine_user_guide`, `implementation_plan` (D done; coref rewritten
  as data). **Effort: low–medium. Risk: low.**

## Recommendation

**Do Stages 1→2 first** (the value-equality primitive + coref-as-rules on the current core). They are
low-risk, additive, independently valuable, and *validate the user's whole direction* with a runnable
demo — before committing to the high-risk id-core rewrite. Then **Stage 3** (id-core) as its own focused,
suite-gated effort, followed by **4→5**. Each stage keeps the suite green.

This also lets the id-core rewrite (Stage 3) be justified by a *working* coref-as-rules story pulling on
it, rather than done speculatively.

## Open questions for sign-off

1. **Sequencing:** accept 1→2→3→4→5, or front-load Stage 3 (id-core) because same-name coref is the
   headline case?
2. **Graded "close enough" semantics:** closeness as `|deg_a − deg_b| ≤ tol`, or cosine/t-norm alignment of
   the two nodes' embeddings ≥ threshold? (Stage 1 detail; exact-valued equality is unambiguous.)
3. **CNL surface** for the condition (Stage 2) — a new keyword vs reusing an existing relation form.
4. **`wire_same_as` retirement** (Stage 4): delete outright, or keep as an author-selectable "same-name
   coref" standard bank for back-compat/convenience?
