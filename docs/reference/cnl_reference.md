# The CNL — language reference

> **Status: AS-BUILT REFERENCE (2026-07-14, written at the docs reorganization).** The controlled
> natural language surface, form by form. This is the system boundary — the external NL→CNL SLM
> targets exactly this surface, so this page doubles as the SLM retraining spec (every change here
> is SLM surface debt; see the ledger in `harneskills`). The grammar is not a parser: every form is
> a normalization REWRITE RULE over the token chain (`ugm/cnl/forms.py`, `authoring.py`,
> `query.py`, `machine_rules.py` — vision §3, "forms = acceptance grammar as rules"). When this doc
> and the forms disagree, the forms + their tests win — update this doc.
>
> House rules of the surface: **one statement per line**; tokens split on whitespace and
> **lower-cased** (CNL is case-insensitive); `are` normalizes to `is` before tokenizing
> (`normalize_lexical`); an unrecognized line is a LOUD, actionable rejection at intake
> (habitability), never a silent skip. Only DECLARED words parse in the open slots — `glorp the
> flarn` never parses, which is what keeps the language controlled.

## 1. Fact statements

| Surface | Canonical result | Notes |
|---|---|---|
| `X is a Y` / `X is an Y` | `X is_a Y` | subsumption; composes with `is_a is transitive` |
| `X is Y` | `X is Y` (copula state) | Y must be the last token |
| `X has a Y` | `X has Y` | |
| `X wants Y` | `X wants Y` | |
| `X in Y` | `X in Y` | explicit placement; defeats the `not in` rule default |
| `X R Y` | `X R Y` | only for a DECLARED relation (`R is a relation`) |
| `SUBJ V OBJ P ARG` | a fresh `event` node: `pred`=V, `subj`, `obj`, `P`=ARG | n-ary reification; V and P must be declared (`V is a verb`, `P is a preposition`); one preposition, single-word entities |
| `X then Y` | `X before Y` | sequencing; suppressed inside `if … then …` |
| `X of C …` | adds `X in C`, bridges the chain | inline context qualification (`monday of week1 before tuesday`) |
| `X is <adverb> ADJ` | sets the graded degree `X.embedding[ADJ] = value` | needs `ADJ is gradable` + a degree adverb (§4); e.g. `alice is very urgent` |
| `goal X is a Y` | a fresh `<goal>` node with `target`=X, `type`=Y | goal statement, consumed by the planner banks |

## 2. Identity and coreference

- **Default: same name ⇒ same node** at ingest. Every entity mention is marked `is_a <mention>`
  (`mark_mentions`) and same-named mentions are INTERNED into one node (`intern_mentions`) — a
  hardcoded CNL-reader decision, not a defeasible judgment (`../attic/indexing_and_coalescing_design.md`).
  Distinct same-named referents are disambiguated at authoring time (`other_alice`).
- `X is one thing` → `X is_unique` — explicit single identity (all mentions of X denote ONE
  individual; a contradiction is then real, not a signal to split).
- `X is the same as Y` → `X same_as Y` (+ both unique) — explicit CROSS-NAME identity; facts
  compose across the `same_as` class (asserted identity is core reasoning, unlike same-name
  linking).
- Definiteness is opt-in: after `the is a definite`, a definite determiner marks its whole noun
  phrase `is_unique` (the multi-word-entity merge fix).

## 3. Rules

**Prose surface** (`load_rules`): a single-triple head, then the shared body spine —

```
HEAD_S HEAD_P HEAD_O when COND and COND and ...
if BODY and BODY then HEAD_S HEAD_P HEAD_O
Cold things are kind              # plural universal → "?y is kind when ?y is cold"
every X is a Y                    # universal law → "?u is_a Y when ?u is_a X"
```

**Body conditions** (the ONE shared spine, `authoring.BODY_SPINE_FORMS` — same grammar for prose
and machine rules):

| Condition | Meaning |
|---|---|
| `S P O` | positive triple pattern (any predicate — no fixed menu) |
| `not S P O` | negative condition (NAC → NAF at solve time) |
| `S is a O` | `is_a` sugar |
| `S is not O` | NAC on the copula |
| `S not in O` | NAC context (the defeasible-default idiom; a stated `X in Y` defeats it) |
| `S does not V O` | verb negation → NAC on `S V O` (aux set = `does/do/did` + declared) |
| `S is <adverb> O` | graded condition — an α-cut threshold from the adverb's degree |
| `S same DIM as O` | exact value-match join on attribute DIM (`ValueMatch`) |
| `S close DIM as O` | graded closeness on DIM (default threshold 0.8) |
| `?a != ?b` | distinctness (machine surface): both sides variables bound by a positive clause |
| `… is round and big and not sad` | copula ellipsis — chained modifiers share subject + copula |

**Variables**: in NL-flavored rules the quantifier/anaphor words ARE the variables —
`someone`/`anyone`/`everyone`/`they`/`them`/`people` → `?x`; `something`/`anything`/
`everything`/`it`/`things` → `?y` (quantifier and its anaphor unify with NO coreference). A domain
can declare more: `critters is a variable` → `?critters`, which also enables the plural universal
`Cold critters are kind`. Any other word is a literal.

**Machine surface** (`load_machine_rules` — the deliberately formal control grammar; memoized per
bank text, LOUD on any clause that doesn't fold to a full `S P O`):

```
H1 and H2 and drop S P O   when   B1 and not B2 and ?a != ?b
```

- Multi-clause head; `drop S P O` is a control deletion (control-deletes-control only).
- Tokens: variables `?x`; plain literals (`reached`, `is_a` as ONE token); **bound literals**
  `name?` — every `<walker>?` in a rule binds to the SAME node. A non-bracket bound literal in a
  head (`s2?`) is a **skolem**: mints one node per LHS match, anchored to LHS-bound endpoints
  (the only supported node invention; a bare RHS-only `?x` head variable is rejected at load).
- `not` clauses are partitioned into **independent NAC groups by their shared NAC-LOCAL FREE
  variables** (variables the positive body does not bind). Atoms sharing one are a single existential
  — `not ?x before ?c and not ?l has ?x` blocks only on a JOINED witness (`¬∃x. before(x,c) ∧
  has(l,x)`, "no predecessor *inside this body*"); atoms sharing none are independent negations, each
  blocking on its own (`¬∃x.A(x) ∧ ¬B`). So both forms are expressible, and which one you get is
  carried by the variables, not by clause order. Both engines apply the same partition
  (`lowering._nac_groups` forward, `chain._nac_atom_groups` on demand).

**Semantics reminders** (contract in `logic_fragment.md`): rule negation is stratified NAF —
a cyclic bank is rejected at load (`on_cycle="raise"`) or degraded to its monotone subset
(`"degrade"`); heads EMIT monotone facts; re-firing is suppressed by the engine, so no
idempotency NACs are needed.

## 4. Declarations (the meta-surface — all ordinary CNL lines)

| Declaration | Effect |
|---|---|
| `R is a relation` | generates the fact form `X R Y` (and lets R compose across coref) |
| `V is a verb` | enables n-ary event forms for V |
| `P is a preposition` | names an n-ary role marker |
| `R is transitive` (also `symmetric` / `irreflexive` / `asymmetric` / `acyclic`) | relation-property meta-rules: gap-filling closure or consistency check (`rule_graph.py`) |
| `A is 0.95` (number in (0,1]) | declares degree adverb A; default lexicon `very is 0.8`, `somewhat is 0.5`, `slightly is 0.3` |
| `ADJ is gradable` | makes ADJ a graded dimension (`X is very ADJ` writes a degree) |
| `X is closed world` | per-predicate CWA declaration (`X closes <closed_world>`) |
| `W is a determiner` / `W is a pronoun` / `the is a definite` | extends the closed-class function words |
| `W is a variable` | W becomes a rule variable word + plural-universal noun |
| `W is an auxiliary` | W joins do-support (`W not V O` folds to a NAC) |

Disjointness: `A is disjoint from B` → `A disjoint_from B` (`rule_graph.form.disjoint_from`); it
generates the entailed-negation rules (`x is A` + `A disjoint_from B` ⇒ `x is_not B` — the HARD
no, distinct from the defeasible assumed-no), both directions, copula and `is_a` forms.
Per-predicate OPEN-world is currently declared on the Python side (`FirmwarePolicy.open_preds`),
not as a CNL line.

## 5. Questions (`ask_goal`, `query.QUESTION_FORMS`)

| Surface | Kind |
|---|---|
| `is S a O` | yes/no on `is_a` |
| `is S P O` | yes/no on relation P |
| `is S O` | yes/no on the copula state |
| `does S P O` | yes/no on any relation (gated by `does`, so no declaration needed) |
| `who is a O` / `who P O` | wh-query (subject unknown) |
| `why S is a O` / `why S P O` | derivation request (renders the `<j:>` proof tree) |
| `who V OBJ P ARG` / `SUBJ V what P ARG` / `SUBJ V OBJ P who` | n-ary wh — the declarative surface with a wh-word in exactly the queried role |

Verdicts follow the stance (`firmware_reference.md` §6): yes (derived), no (entailed `is_not`),
assumed-no (CWA absence), unknown (open predicate or fuel exhausted → gather/ask).

## 6. Session control CNL (recognized as FORMS, never string-sniffed)

| Surface | Effect |
|---|---|
| `focus on X` | push a focus frame centered on X |
| `forget that` | pop the top focus frame (graph-neutral — focus is a register) |
| `back to X` | re-enter the frame whose centers include X |
| `forget that rule` / `disable that rule` | mark the last-authored rule `<disabled>` (additive; no deletion) |

`forget that rule` is checked before `forget that` — the trailing `rule` token disambiguates
(grammar precedence, not code order sniffing).

## 7. Raw-NL tolerance (surface normalization, before the forms)

- **Determiners** (`the/this/that/these/those`; extensible) are stripped when they introduce an
  entity; articles `a`/`an` only when leading (mid-clause they belong to `is a Y`).
- **Multi-word noun phrases DECOMPOSE, never merge**: `the bald eagle` → head `eagle` +
  `eagle is bald` (structure exposed to reasoning, not hidden in a string). Only
  determiner/quantifier-introduced NPs decompose.
- **Pronouns** (`it/they/he/she/…`; extensible) are substituted with the discourse subject before
  tokenizing — a content-blind recency policy owned by the Session; in-substrate anaphora is
  deliberately OFF the roadmap (the SLM owns it via `focus.top_centers`).

## 8. Entry points

`load_corpus(text)` → `(Graph, rules)` (facts + declarations + rules in one text);
`load_facts(graph, text, strict=False)`; `load_rules(text, policy=, lint=True)`;
`load_machine_rules(text)`; `ask_goal(graph, question, rules=, commit=, focus_scope=)`;
`ingest(kb, rules, utterance, …)` / `converse(…)` — the unified intake: routes
fact / rule / question / focus / rule-control / unrecognized **by which forms fired**, with
streaming events and ask suspend/resume (`../design/cnl_intake_design.md`).

## 9. Known limits (deliberate, or first-slice)

- Independent (non-conjunctive) NACs are not expressible in either rule surface.
- No disjunction, no general quantifier nesting (the logic fragment's scope).
- `if … then …` first slice: copula clauses, single trailing head triple.
- Plural universals: single leading adjective, single predicate (`All young, cold people …` stays
  unrecognized rather than mis-folded).
- N-ary events: declared verb + exactly one declared preposition, single-word entities, no
  lemmatization (the surface verb must match the declaration).
- Indefinite existentials (`someone owns a dog` as a FACT) are out of scope for surface
  normalization — existentials enter via rules (labelled-null skolems).
