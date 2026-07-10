# Design — universal consistency: constraint schemas, an upper layer, a rule-linter (2026-06-29)

> **Status: SKETCH / PLAN — importance PROMOTED by `logic_fragment.md` Amendment 2 (the
> fragment's hard part is exception/priority CONSISTENCY, which this lint addresses).** Read
> `docs/vision.md` (§5 two layers, §7 conventions, §2 homoiconic) and
> `docs/implementation_plan.md` first. This plans the "general rules for
> detecting inconsistencies / filling gaps, applicable to any domain" thread. It is NOT
> an upper-ontology megaproject (that is the Cyc tar pit — see Limits); it is a **small,
> sharp universal layer** plus a **static rule-linter**, both extensions of code that
> already exists (`rule_graph.py`'s relation-property meta-feature; `authoring.stratify`).

## 0. The one discipline everything rests on

A monotone forward-chaining layer cannot *reject*; it can only *add*. So:

> **Inconsistency detection = deriving an explicit `<contradiction>` marker node** on the
> offending configuration, never blocking or deleting. A guard / linter / human / tool
> then reads the markers and decides what to do.

This is the §5 discipline (truth/violations are marker nodes read through a guarded
filter) and it is a feature, not a workaround: it is **paraconsistent** — a local
contradiction marks itself without exploding the rest of the KB. The split mirrors the
standing guardrail: **detecting** a contradiction is fact-layer (derive the marker);
**acting** on it (retract a default, flag a human, invoke a tool) is control/policy.

Convention (proposed): `<contradiction> --about--> X`, `<contradiction> --because--> R`
(the relation/category that was violated). Domains/tools read `nodes_named("<contradiction>")`.

## 1. Prerequisite (cross-cutting): a DISTINCTNESS primitive

Matching is **homomorphic** — distinct pattern keys may co-bind the same node — and there
is no inequality. So any constraint of the form "two *different* X" cannot be stated:
`?x R ?a, ?x R ?b` matches with `?a == ?b`. This is the *same* gap that bit ranked
commitment (Pat couldn't say `?o ≠ ?x`).

It cleanly partitions every schema below into **buildable now** vs **blocked on
distinctness**, so it is the first thing to settle. Options (pick later):

- **(D1) `distinct` facts** — author/derive `A --distinct--> B`; constraints add a
  `?a distinct ?b` premise. Pure-substrate, but O(n²) to populate and needs a tool to
  derive distinctness (two differently-named nodes are distinct → a §8 calculator, like
  `rank_by_cost` emitting `cheaper_than`). **Recommended** — consistent with everything else.
- **(D2) injective-match option on a rule** — an engine flag marking certain keys as
  must-bind-distinct. Smallest engine change, but it *is* an engine change (we have held
  the engine fixed for many sessions) and is less uniform.
- **(D3) an identity tool** — a §8 tool that, given a binding set, filters out
  equal-bound matches. Keeps the engine fixed; awkward to compose with forward chaining.

D1 is the most in-grain (distinctness is just knowledge; a tool computes it from names,
exactly as the cost comparator does). Note many useful schemas need NO distinctness
(below) — so the universal layer can ship a strong first cut *before* this is decided.

## 2. (a) Constraint-schema catalogue — extend the relation-property meta-feature (IMPLEMENTED 2026-06-29, no-inequality set)

> **DONE** — `rule_graph.py`: `_property_rule` extended (`irreflexive`, `asymmetric`,
> `acyclic`) + `_disjoint_rule`/`DISJOINT_REL` + forms (`RELATION_PROPERTY_FORMS` grown,
> `DISJOINT_FORMS`, `CONSTRAINT_FORMS`) + `expand_relation_properties` handles both kinds +
> readers `contradictions`/`is_consistent`. Detection derives a `<contradiction>` marker
> (`_contradiction_rhs`: a fresh bound-literal node `--about--> X`, `--violates-->` the
> constraint). `examples/consistency.py` + 5 tests (64 green); generated rules lint clean.
> Composes with `is_a` transitivity (a disjoint clash via a sub-category is caught).
> The inequality-blocked set (`functional`/`injective`/cardinality) remains for after the
> distinctness primitive.

`rule_graph.py` already turns `R is transitive` / `R is symmetric` declarations into
concrete rule-nodes via `_property_rule` (dispatch on property name) + `expand_relation_
properties` (the §8 tool) + `RELATION_PROPERTY_FORMS` (the CNL acceptance forms). This IS
the mechanism the question asks for: a domain-independent property *declared* on a
relation, expanded into rules that fire for anything. Grow the catalogue:

**Buildable NOW (no distinctness needed):**

| Declaration | Emitted rule (schema) | Kind |
|---|---|---|
| `R transitive` | `?a R ?b, ?b R ?c ⇒ ?a R ?c` *(exists)* | gap-fill |
| `R symmetric` | `?a R ?b ⇒ ?b R ?a` *(exists)* | gap-fill |
| `R irreflexive` | `?a R ?a ⇒ <contradiction> about ?a` | detect |
| `R asymmetric` | `?a R ?b, ?b R ?a ⇒ <contradiction>` (subsumes irreflexive) | detect |
| `R acyclic` | declare `R transitive` **and** `R irreflexive` — a cycle surfaces as `?a R ?a` after closure | detect (composed!) |
| `A disjoint_from B` | `?x is_a A, ?x is_a B ⇒ <contradiction> about ?x` | detect |
| `R inverse_of S` | `?a R ?b ⇒ ?b S ?a` | gap-fill |

`acyclic` is the elegant one: it needs no inequality because transitive *closure* turns a
cycle into a self-loop, which `irreflexive` then flags. `disjoint_from` needs none because
`A`/`B` are distinct *literal* category nodes.

**Blocked on distinctness (§1):**

| Declaration | Emitted rule | Why blocked |
|---|---|---|
| `R functional` | `?x R ?a, ?x R ?b, ?a distinct ?b ⇒ <contradiction>` | needs `?a ≠ ?b` |
| `R injective` | `?a R ?y, ?b R ?y, ?a distinct ?b ⇒ <contradiction>` | needs `?a ≠ ?b` |
| `R has cardinality k` | counting | needs distinctness **and** datum arithmetic (a tool) |

Work = add cases to `_property_rule`, add forms to `RELATION_PROPERTY_FORMS`, and (for the
detect kind) point the RHS at `<contradiction>`. Engine unchanged; same two-phase
(declare → expand → `rules_in_graph` → run) pipeline.

## 3. (b) Upper-category bank — a few categories as is_a anchors

A small bank `UPPER_RULES` of genuinely domain-independent categories that domains hook
into with one `X is_a <category>` line, inheriting axioms via the existing `is_a`
transitivity. Keep it TINY (see Limits):

- **Location / Container** — `contained_in` transitive + acyclic; "a located thing has a
  location" (gap-fill); optionally `contained_in` functional (one place) — distinctness-gated.
- **Object / Endurant** — persists; identity over time.
- **Event / Process** — has a time; `before` transitive + acyclic (no time travel).
- **Agent** — can act / hold goals.
- **Quantity** — comparable (the `cheaper_than`/cost machinery is the first instance).

Each category is a node; its axioms are relation-property declarations on the relations it
introduces, so (b) is mostly (a) plus is_a anchoring. Example end-to-end:
`ice_cream_shop is_a location` + `location has contained_in (transitive, acyclic)` ⇒ free
containment reasoning + cycle detection for shops, with no shop-specific rules.

## 4. (c) The rule-linter — check the RULES, not the situation (IMPLEMENTED 2026-06-29)

> **DONE** — `harneskills/lint.py` (`lint_rules`, `lint_graph`, `emit_smells`,
> `format_smells`, `Smell`, `is_control_token`) + 5 tests (56 green). Checks: `ungated-delete`
> (§5), `unbound-drop`, `no-op`, `negation-cycle` (reusing `stratify`); `dead-predicate?`
> opt-in. **All 12 shipped banks lint clean.** The sweep immediately earned its keep: it
> first flagged `GRADED_RULES` as `no-op` — correctly exposing a gap in the *linter*, not
> the rules (a graded rule's only effect is `propagate`, an embedding write, which the
> no-op check now accounts for). The sketch below matches the implementation.

Because rules are data (`Rule` dataclasses; `rule_graph.py` round-trips them), a **static
§8 analysis tool** can check a rule bank against the system's OWN invariants and emit
findings. Self-contained, needs no ontology, immediately useful. Sketch:

```python
# harneskills/lint.py
@dataclass(frozen=True)
class Smell:
    rule_key: str
    kind: str        # see checks below
    detail: str

def lint_rules(rules: list[Rule], *, base_predicates: frozenset[str] = frozenset()) -> list[Smell]:
    smells = []
    produced = {p for r in rules for pat in r.rhs for p in [pat.p] if not is_var(pat.p)}
    for r in rules:
        # 1. §5: a deleting rule MUST be gated by a control token in its LHS (vision §5/§12.3)
        if r.drop and not any(_is_control(t) for pat in r.lhs for t in pat.tokens()):
            smells.append(Smell(r.key, "ungated-delete",
                                "drops an edge but no <control> token gates the LHS"))
        # 2. drop must reference only LHS-bound nodes (you can't delete what you didn't match)
        if r.drop and not r._drops_only_bound():
            smells.append(Smell(r.key, "unbound-drop", "drop references an unbound node"))
        # 3. possibly-dead: an LHS plain-literal predicate nothing produces (heuristic; needs
        #    base_predicates allowlist for fact/form predicates to avoid false positives)
        for pat in r.lhs:
            p = pat.p
            if (not is_var(p) and not is_bound_literal(p) and not _is_control(p)
                    and p not in produced and p not in base_predicates):
                smells.append(Smell(r.key, "dead-predicate?",
                                    f"LHS predicate '{p}' is produced by no rule/base set"))
    # 4. negation cycle (not stratifiable) — reuse the existing analyzer
    try:
        stratify(rules)
    except ValueError as e:
        smells.append(Smell("<bank>", "negation-cycle", str(e)))
    return smells

def _is_control(tok: str) -> bool:        # a control token is a <...>-named node
    name = literal_name(tok)
    return name.startswith("<") and name.endswith(">")
```

**Verified against the current banks** (by hand): every legitimate deleter — `plan.unblock`,
`plan.teardown.*`, `exec.clear_unmet` — has a `<yes>`/`<now>`/`<replan>` token in its LHS,
so check 1 yields **no false positives**; relation-property rules use NAC not drop, so
they are clean. Check 3 is a heuristic and ships as a *warning* requiring an allowlist.

Output: `lint_rules` returns `Smell`s (a developer tool); a thin `emit_smells(graph, smells)`
can also drop `<rule-smell>` nodes into the substrate for the in-graph view (cf.
`surface.explain` as a reader). It can lint a `list[Rule]` or, via `rules_in_graph`, a
rule-graph.

**Honest scope.** This catches *structural/static* defects (§5 violations, unbound drops,
dead predicates, negation cycles). It does **not** catch the *dynamic* commit-timing race
we hit (commitment firing before a tool supplied costs) — that is a tool/rule **dataflow
ordering** issue, a more advanced check (see roadmap). Don't oversell the linter as a
catch-all; it enforces the invariants that ARE statically checkable.

## 5. Roadmap (proposed order)

1. ~~**(c) rule-linter, first slice**~~ — **DONE 2026-06-29** (`harneskills/lint.py`, 5 tests,
   all banks clean). Still open: wire into a `:lint` REPL command / bank-construction path.
1b. ~~**(a) no-inequality constraint schemas + `<contradiction>` reader**~~ — **DONE 2026-06-29**
   (`rule_graph.py`: irreflexive/asymmetric/acyclic/disjoint_from; `contradictions`/`is_consistent`;
   `examples/consistency.py`; 5 tests). Open: a `:check` reader in the REPL; act-on-contradiction policy.
2. **(a) no-inequality constraint schemas** — `irreflexive`, `asymmetric`, `disjoint_from`,
   `acyclic` (composed), `inverse_of`; RHS → `<contradiction>`. Extends `_property_rule` +
   `RELATION_PROPERTY_FORMS`. Plus a tiny guarded reader for `<contradiction>` markers.
3. **(§1) distinctness primitive** — decide D1/D2/D3 (lean D1: a `distinct` tool from
   names, like the cost comparator). Unlocks ranked-commitment ties too.
4. **(a′) inequality schemas** — `functional`, `injective` once distinctness lands.
5. **(b) upper-category bank** — `UPPER_RULES` (Location/Container, Event/before, …) as
   is_a anchors carrying the (a) declarations. Keep tiny.
6. **(advanced linter) tool/rule dataflow ordering** — flag a rule consuming a predicate
   produced only by a tool the driver runs *after* the rule pass (the commit-timing class).
   Also head-conflict detection (two rules, overlapping LHS, heads disjoint per (a)).

## 6. Honest limits (don't chase "most")

- **Upper ontology is a tar pit.** Cyc: 40 years, tens of millions of assertions;
  SUMO/DOLCE/BFO disagree on fundamentals. The genuinely universal core is *small and
  abstract* (identity, parthood, location, time, quantity). Past that, "universal" axioms
  smuggle domain assumptions. Target a small sharp core + *declarable* schemas domains
  instantiate, NOT completeness.
- **Universal layer catches only LOGICAL/STRUCTURAL errors** (P ∧ ¬P, functional/disjoint
  violation, is_a cycle, type mismatch). DOMAIN inconsistency needs domain-declared
  constraints — which the universal *schemas* then enforce generically. That split is the
  whole leverage.
- **Gap-fill ⟂ detect, in tension.** Aggressive gap-filling INVENTS facts that create
  phantom contradictions or mask real ones (cf. the multi-shop context default
  over-applying). Every gap-filler must be defeasible (tier-a, done) and provenance-marked
  (`derived-by-default` vs `asserted`), or the checker polices its own fabrications.
- **Open world.** Absence ≠ falsity; "missing" is not automatically an error. Constraints
  must be *positive* configurations (something present that shouldn't be), not "X not stated."
```
