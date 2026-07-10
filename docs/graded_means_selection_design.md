# Graded means-selection — design (the first slice of the agentic loop)

> **Status: DESIGN, decisions LOCKED (2026-07-04). Not yet implemented.** The next
> implementation step. Read `docs/vision_agentic.md` §8 (possibilistic gradedness) and §9
> (the agentic loop — this is **step 3**, "plan / decompose", picking among competing means
> for a subgoal). Companion memory: `decision_agentic_loop_inversion`.

## What this is

When more than one authored **means** could satisfy a subgoal (e.g. a *complex-page* rule
and a *simple-page* rule both fire for the same client), the substrate must pick one. This
slice builds that picking as **graded preference**: rank the candidates by their authored
degree and select the best fit — the concrete "which means wins" mechanism the whole
subgoal loop needs.

It is built **isolated but non-throwaway**: authored in the *exact CNL forms the loop will
use*, exercised with hand-asserted candidates. Wiring it into the full loop later is just
wrapping a trigger + procedure around an already-correct core (additive, not rework).

## The hard constraint (do not violate)

**NEVER encode selection logic in Python.** What competes, how strongly each candidate fits,
and that the strongest wins are **all KB data / rules**. The domain author must be able to
change how selection behaves by *authoring knowledge*, never by editing Python. The moment
selection logic lives in Python it becomes a "python-driven tunnel" that kills flexibility
(user, re-emphasized 2026-07-04; see `feedback_no_python_for_banks`). The **only** new Python
allowed is a *generic* `compare` calculator behind a `<call>` (a §8 tool on opaque nodes),
because comparing two number-*named* nodes needs a tool to parse them — that is a calculator,
not logic.

## Locked decisions

1. **Mechanism = 1b, RETAINED / RANKED** (`preferred_over` / `satisfied_by`), **MONOTONE — no
   retraction.** Chosen over graded-defeat (retract losers) because: monotone (sidesteps the
   known retraction-vs-propagation fight, cf. the 74→1830-node blowup in
   `decision_coref_as_rules`); more auditable (losing candidates *and the reason* stay in the
   graph for the why-trace); fallback is a fact-assertion, not a cascade. Graded-defeat can be
   added later if a domain genuinely needs losers *gone*.
2. **Grouping = Style A, `is_a` (EMERGENT).** `complex_page is a page` / `simple_page is a
   page`; any two `page`-kinds chosen for the same subject compete automatically via the
   generic rule binding `?goal`. Zero new grammar; the competition is emergent from `is_a`.
   The user explicitly wants this emergent behavior. (Style B — procedures declaring their
   alternatives with an `or` — is sugar that *generates* this grouping; add it when procedures
   land.)
3. **Ungraded-means baseline = EXPLICIT authored `has_fit`.** A means with no graded condition
   (e.g. the default `simple_page`) gets an author-declared `simple_page has_fit 0.3`, not an
   implicit Python floor — keeps the number authored and visible.
4. **Staging = ISOLATED but NON-THROWAWAY** (see above).

## The design, concrete

Shared scenario (this is the test fixture):

```
demanding is gradable          # very=0.8, somewhat=0.5, slightly=0.3 (degrees are KB facts)

acme is a client
acme wants a page
acme is very demanding         # -> fit 0.8 via the existing alpha-cut/embedding machinery

# two authored MEANS for the subgoal, each with its graded (or default) condition:
build ?x a complex_page when ?x is a client and ?x wants a page and ?x is very demanding
build ?x a simple_page  when ?x is a client and ?x wants a page

# Style A grouping (emergent competition) + explicit baseline for the ungraded means:
complex_page is a page
simple_page  is a page
simple_page  has_fit 0.3
```

For `acme` both means fire → two candidates, `complex_page` (fit 0.8) and `simple_page`
(fit 0.3). Selection picks `complex_page`.

**Generic MACHINERY rules** — authored ONCE, domain-independent, in machine-rule CNL, loaded
like the planner rules in `corpus/planning*.cnl` (candidate surface `?x chose ?c for ?goal`,
`?c has_fit ?d`):

```
# Y beats X when both are candidates for the same goal and Y fits strictly better:
?c1 beaten when ?x chose ?c1 for ?goal
            and ?x chose ?c2 for ?goal
            and ?c1 has_fit ?d1 and ?c2 has_fit ?d2
            and <compare ?d2 ?d1 gt>

# the winner is the candidate nothing beats (the argmax, via a NAC):
?goal satisfied_by ?c when ?x chose ?c for ?goal and not ?c beaten
```

`<compare ?d2 ?d1 gt>` is the generic `<call>` calculator: opaque number-nodes parsed ONLY
inside the tool, returns a truth marker. Consumers read `satisfied_by`. The winner is
emergent (nothing beats it) — no Python argmax, no per-domain code. The author tunes
selection purely by authoring graded conditions / `has_fit`.

## The only new primitive

A generic **`compare` / `gt` calculator** registered as a `dispatch.py` tool (`run(...,
tools=...)`). Opaque-node discipline: it reads the two candidate number-node *names*, parses
them to floats *inside the tool*, and materializes a truth marker — it never lets a rule see
a parsed number. This is the aggregation/arithmetic seam already on the roadmap
(first-class CALL calculators — `logic_fragment.md` §8, `processing_modes.md`).

## Open sub-questions (flag during implementation; none blocks the design)

- **Candidate materialization.** How `?x chose ?c for ?goal` + `?c has_fit ?d` get produced
  from a firing means. Graded means: the degree comes from the matched graded condition (the
  existing α-cut/embedding `propagate` writes it — see `authoring.py`). Ungraded means: the
  explicit `has_fit`. Decide whether the `chose … for …` wrapper is authored per-means or
  generated by a form; prefer generated so the author just writes the `build …` rule.
- **Ties (equal fit).** `gt` is strict, so two equal-fit candidates neither beats the other →
  both are `satisfied_by`. For v1 that is acceptable (a genuine tie → both offered); document
  it. Add an authored tiebreak only if a real case needs it.
- **`beaten` re-derivation / the NAC.** Confirm the stratification: `beaten` must be computed
  before `satisfied_by`'s NAC reads it (a standard stratified-negation ordering, like the
  existing NAC paths). `<compare>` is serviced at rule-fixpoint, so `beaten` settles, then the
  NAC fires — verify no false-cycle through the shared vocabulary.
- **Where the machinery rules live.** A new corpus file (e.g. `corpus/select.cnl`) loaded like
  `corpus/planning*.cnl` — authored CNL, inspectable — preferred over a Python generator.

## Build steps (isolated, non-throwaway)

1. **`compare`/`gt` calculator tool** — smallest new Python, a pure generic calculator
   (`dispatch.py`-registered). Test it in isolation first.
2. **Generic selection machinery** — author `beaten` / `satisfied_by` in `corpus/select.cnl`,
   loaded like the planner rules.
3. **Candidate-materialization convention** — the `chose … for … has_fit …` surface, plus the
   explicit-`has_fit` baseline for ungraded means.
4. **Test via the PUBLIC surface** (contract-style, `tests/test_contract.py` idiom): assert the
   scenario, run, `ask` "what satisfies the page goal for acme" → `complex_page` (0.8 > 0.3).
   Add: the equal-fit tie case; the single-candidate case (no `beaten`, trivially satisfied);
   a `somewhat demanding` client where the α-cut prunes `complex_page` before selection even
   runs (shows α-cut and selection are two distinct, composing filters).
5. **Lint: NO domain logic in Python** — the only Python touched is the generic `compare` tool.

## How it wires into the loop later (additive — do not build now)

- The `chose … for …` candidate facts come from means firing inside a procedure's subgoal
  (loop **step 3**).
- `satisfied_by` is exactly what loop **step 6** (decide-next) reads to know a subgoal is met.
- **Fallback on effectful failure** (step 4/5): when the selected means' effectful `<call>`
  fails, assert `?winner beaten` (or a `<failed>`-driven beat) → the NAC promotes the
  next-best candidate. No rework of the selection core — this is why 1b was chosen.

## Cross-references

- `docs/vision_agentic.md` §8 (possibilistic gradedness, hedges, means-ranking), §9 (the
  agentic loop; this is step 3), §13 #9 (correctness-for-flexibility).
- `harneskills/authoring.py` — the LIVE graded machinery (`degree_thresholds`, `graded_rules`,
  `degree_grammar_forms`, α-cut); degrees are KB facts (`very is 0.8`).
- `harneskills/dispatch.py` — the `<call>` calculator seam.
- Memory: `decision_agentic_loop_inversion`, `feedback_no_python_for_banks`,
  `decision_metareasoning_layer` (the content-blind *effort* dial, distinct from this
  content-*ful* authored *preference*).
