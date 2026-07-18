We are not using gradable and possibilistic enough..

I'd like to express the following (composing):

when x then y equally likely (or more likely than, less likely than) z   - this would also mean there are disjoint possibilities
when x is very y then ....


Immediate implications (more to think about):
- different "fuel consumption" in chain
- alternative derivations (multiple possible universes)

allowing partial ordering:

x is more beautiful than y
y is more beautiful than z
t is more beautiful than z

-> can't say whether y is more beautiful than t (so we can't just "bump" up or down gradable attributes and compare them - but if we use expression such as very, little we can e.g. x is very beautiful, y is beautiful, z is little beautiful => i CAN compare)

Pretty sure we can express all of this with little or no change to lower levels of the system, touching only the CNL, my fear is what would happen to consistency and soundness of the system

---

# Recap — decisions & open questions (design discussion, 2026-07-15)

Consolidates the discussion. Status: **notes**, not yet ratified into `logic_fragment.md`.

## Framing: two orders that must not be conflated by ROLE (but may share structure)

- **Object-level gradable order** — `x more beautiful than y`. Genuinely PARTIAL. Object *content*.
- **Meta-level likelihood/possibility** — `y more likely than z`. An *inference weight* on
  derivations (§7 graded layer, Dubois–Prade possibilistic — "preference among matches; truth
  does not live here").

They mean different things and are READ in different places. That is the separation that matters.
It turns out (see B) they can nonetheless share the SAME representation, because *neither* needs to
be total.

## Decided

1. **`more_beautiful` is a DECOMPOSED comparison node, not a monolithic predicate.**
   The substrate already interposes a node for every relation (`add_relation`, `attrgraph.py`).
   We reuse that, keeping the *dimension* first-class:
   - middle node carries `{<comparison>:1.0, beautiful:1.0}`;
   - **direction carries more/less** — `x→cmp→y` *is* "x more beautiful than y"; the reverse arrow
     *is* "less". No `more=1` attribute needed.
   - **"equally" is NOT a comparison node** — it is the existing `x same beautiful as y`
     value-match (`ValueMatch` on the dimension).
   - Rationale: a monolithic `more_beautiful` predicate welds the dimension into a string and
     permanently severs the comparative from the graded degree. Decomposed keeps the bridge, which
     is the whole point of this doc.
   - Cost: transitivity is no longer the one-word `R is transitive` declaration; it becomes a
     2-body rule joining two comparison nodes **on matching dimension**. Still pure CNL, no engine
     change. (Perf caveat: open point G.)

2. **Hedges (`very`/`little`) bridge comparative ↔ absolute degree.** Half-built already:
   `X is very ADJ` → `x.beautiful = 0.8`. Rung-degrees make otherwise-incomparable items
   comparable — the "if I use very/little I CAN compare" insight.

3. **Incomparability = no derivable path = honest UNKNOWN.** The partial order needs no completion;
   "can't say whether y is more beautiful than t" is a first-class answer, not a gap to fill.

4. **Forward disjunction only lives where CWA isn't looking**, in exactly three shapes:
   - **closed-set constraint** → the elimination/riddle mechanism (the ONE genuinely
     CWA-compatible forward disjunction: entailed as a whole, no disjunct individually derivable,
     candidate set closed — Sudoku cell, "exactly one guilty suspect", pigeonhole);
   - **local OWA** (future / unobserved / other minds — CWA switched off on that predicate);
   - **abduction** — the chain of causes behind an observation. CWA closes the *effects*, not the
     *causes*. This is "only the chain of possibilities leading to what we see is correct":
     forward = determinate, backward = disjunctive (differential diagnosis, debugging, the
     detective).

5. **Two human behaviors = two mechanisms.**
   - *Make hypotheses* (explore explanations) → abduction via demand-driven, possibility-ordered
     SUPPOSE; prune worlds inconsistent with observation.
   - *Jump to a conclusion that might be wrong* (e.g. gender bias) → defeasible collapse to the
     most-possible disjunct, WITHOUT opening branches.

6. **Bias mitigation = a new `defeasible-guess` provenance verdict** — the positive-assumption
   sibling of `assumed-no`. "Picked *y* because it's the most-possible; alternatives *z,w* exist and
   were not ruled out — an assumption, not a derivation." Makes the prior an inspectable, defeasible
   object rather than a hidden weight. (Mechanics = open point D.)

7. **All conflicts are DEFEAT + LINT, never ⊥.** Comparative-vs-degree contradictions
   (`x more beautiful than y` but `x slightly beautiful`, `y very beautiful`) and transitivity
   cycles route to defeat/linter (`logic_fragment.md` Amendment 2), never to a derived falsum.
   Monotone core untouched; branching quarantined to SUPPOSE.

8. **No unique max required — lean on the `assumed` provenance instead. (answers B & C)**
   We do NOT require the likelihood order to be a lattice/total. Selection = *pick one and flag it
   `defeasible-guess`*. When there is a clear most-possible disjunct, pick it. When there is a **tie**
   ("equally likely") or an **incomparability** (partial order), we still pick (or surface), and the
   `assumed` flag simply does heavier lifting — the provenance honestly records "guessed among
   equals/incomparables". Consequence: the likelihood layer can stay a PARTIAL order exactly like
   the object layer, so both can share the decomposed-comparison-node representation (over a
   `<likelihood>` dimension) — the earlier "likelihood wants a lattice" worry dissolves, because we
   never take an argmax we can't justify. Ties and incomparability collapse into the same mechanism.

9. **Effort and possibility are DECOUPLED axes. (answers E)**
   Do NOT scale fuel by likelihood — that would conflate *intensity of thought* (effort/depth) with
   *likelihood* (possibility). Likelihood affects only **which disjunct we pick as the assumption**
   and the **order** we explore in; fuel is its own independent metareasoning dial bounding **how
   hard we look**. (They meet only indirectly: under a shared global budget you spend fuel on the
   most-possible branch first, so low-possibility branches may go unexplored — that is ordering
   under a budget, not likelihood-scaling-cost.)

10. **Possibility is QUALITATIVE/ordinal, not a weight calculus. (answers F)**
    Humans don't run probability calculus; when genuine numeric combination is needed, that is the
    tool's job (`<call>` seam). No min-along-chain / max-across-derivations arithmetic in the core —
    the order is used for selection and ranking only.

11. **Drop clingo as the HOME of disjunction; keep it only as an optional accelerator.**
    The elimination/SUPPOSE loop *is* the semantics of disjunction (constraint propagation + guess +
    backtrack + honest give-up). Reverting to clingo would (a) re-import the complete theorem-prover
    the system deliberately declined to be, and (b) break the machine-that-explains-itself (clingo
    returns an unexplainable black-box answer, no journal). Price: a genuinely hard instance yields
    "couldn't solve within budget → UNKNOWN" — already the ratified stance, and it still leaves a
    SUPPOSE-tree proof object behind. clingo demotes to an optional `<call>` for big instances that
    need completeness/speed.

## Open

- **A. Author/store form for the likelihood ranking.** Where does `y more likely than z` live and
  how does an author write it? Emerging answer (from decisions 8 & 10): reuse the decomposed
  comparison-node structure over a `<likelihood>`/`<possibility>` dimension — same machinery as
  beauty, qualitative, partial order OK. Feeds selection-of-assumption (decision 6/8), not a weight
  calculus. *Needs confirming as the concrete surface form.*
- **D. `defeasible-guess` mechanics — ✅ BUILT 2026-07-16** (`possibility.guess` / `retract_guess` /
  `render_guess`; `tests/test_possibility_guess.py`, 8 green). A guess is an EPISTEMIC ACT, not a
  derivation, in four moves: (1) the PICK — argmax possibility over the open object slot
  (marker-mode read), deterministic (band then name) so a tie is reproducible; (2) the RECORD — a
  visible `<guess>` control node carrying the picked triple, band, BASIS (`clear-max`/`tie` — the
  tie case honestly says "guessed among equals", decision 8) and every COMPETITOR with its band.
  A competitor is a value from an INCOMPATIBLE world only (exclusive fork via `<choice>` or
  `disjoint_from`) — a co-scoped JOINT (`tall` riding the male-world) or an independently-compatible
  fork can co-hold and is NOT an alternative; (3) the ADOPTION — the guess node doubles as a pencil
  SCOPE: the picked world's contents (joints included — correlation comes along) are penned under
  it, so DOWNSTREAM reasoning is plain CRISP in-scope `chain_sip(scope=guess_node)` — one world,
  binary visibility, NO branch opened (decision 5's "collapse without opening branches", realized
  on the existing scope machinery); (4) the RETRACTION — sweep the pencils, KEEP the record marked
  `[RETRACTED]` (the machine remembers the jumps it took back); ink was never touched, so nothing
  else to undo. A CERTAIN answer returns basis `certain` (a read, not a guess — nothing minted);
  an unreachable slot returns None (that is `check`'s assumed-no/unknown territory). `render_guess`
  is the `why` line: "x is male — guessed as the most possible (likely); alternatives not ruled
  out: female (unlikely). An assumption, not a derivation."
- **E'. Where the effort dial lives** now that it is decoupled from likelihood (decision 9) — is it
  the existing fuel budget, exposed as an explicit metareasoning control?
- **G. Transitivity-as-a-rule performance.** Decomposed comparisons make transitivity a 2-body rule
  joining comparison nodes on a matching dimension. `demand-coref-perf-wall` warns dense relational
  closures can go super-linear — needs a perf check, not just a correctness one.
- **H. Consistency linter** for comparative-vs-degree conflicts (Amendment 2 territory) — deferred
  build.
- **I. Propagation-strength KNOB. (answers I — yes)**
  A tunable metareasoning dial: how much constraint propagation (forced eliminations / naked
  singles) to run before falling back to hypothesize-and-backtrack. Too little → exponential SUPPOSE
  blowup on easy instances; too much → wasted effort. This is the knob that decides whether dropping
  clingo (decision 11) is comfortable. *Needs a default and a range.*

---

# ⇢ HANDOFF STATUS (2026-07-16) — read this first

**Where it stands: THE ARC IS COMPLETE.** Possibilistic reasoning now runs INSIDE the one
demand-driven engine (`chain_sip`) as a firmware stance — `FirmwarePolicy(uncertainty="banded")` —
and the whole design is built: banded facts, correlated + RANKED `either…or`, multi-hop min,
multi-variable rules, the θ bias dial (a `FirmwarePolicy` session dial), graded negation,
cross-fork + transitive ENVIRONMENT soundness (env-aware NAC; `disjoint_from` world-exclusion), a
KB-declarable hedge lexicon, the `check`/`ask_goal` band-word verdicts, and the book. Full suite
**487 green** (`.venv/Scripts/python.exe -m pytest tests/ -q`). Backlog items 1–5 landed
2026-07-16 (see below); **item 6 — the `chain_sip` fold — landed 2026-07-16 too**, and the
standalone forward reasoner (`apply_rule_banded`/`run_banded` + `possibility.py`'s own ISA matcher
programs) was DELETED with it (user-ratified: one engine, not two; `tests/test_possibility_rules.py`
now drives the fold; `test_possibility_fixpoint.py` deleted, its guarantees folded in).

**The fold in one paragraph:** banded is a GLOBAL firmware stance (user-ratified 2026-07-16: a
session dial on `FirmwarePolicy` — never a per-call switch; and never automatic-on-forks, because
silent-until-assumed is load-bearing). Under it, `chain_sip(policy=…)` swaps the read's binary
`OVERLAY` for `OVERLAY_BAND` over a merged map (every fork's pencils at their band + the active
SUPPOSE scope's pencils at CERTAIN — so banded composes with SUPPOSE for free); the band IS the
match score (min t-norm ⇒ weakest link, multi-hop free); the body join threads `(state, band, env)`
and prunes inconsistent environments (shared `<choice>` or declared `disjoint_from` — ATMS);
`_nac_blocks` grades absence (Π over body-env-compatible worlds ≥ θ blocks; a survivor folds
`N(¬P)=1−Π` into the band); EMIT is graded (CERTAIN+env-free → ink/scope-pencil exactly as today;
uncertain → a DERIVED FORK via `possibility.fork_fact` carrying its env, re-emitted only at a
STRICTLY better band ⇒ the rounds converge); fuel semantics unchanged (exhaustion → UNKNOWN even at
a partial band). `check` grows the band words between POSITIVE and ASSUMED_NO (S7.4), `collapse`
passes them through (no premature defeasible collapse), so `ask_goal` answers `likely` with the
question forms untouched. Silent mode is byte-identical (the 450+ crisp tests are the differential
gate).

**DEFEASIBLE-GUESS BUILT 2026-07-16** (open point D — see its entry in the Open list below for the
full mechanics): `possibility.guess/retract_guess/render_guess`, suite 495 green.

**GRADABLE-COMPARATIVE ARC BUILT 2026-07-16** (decisions 1–3 + open points G/H; suite 513 green) —
`ugm/cnl/comparative.py` + `tests/test_comparative.py` (12):
- Decision 1: a comparison is the DECOMPOSED relation `x -[dim]-> y` + a `<comparison>` class marker
  on the rel (a `<…>` key, so `predicate()` still reads the DIMENSION); direction carries more/less
  (`less` authors the reversed arrow); transitivity = a 2-body rule PER DIMENSION generated from the
  KB (`comparison_rules`, the §8 tools-from-data pattern), run DEMAND-DRIVEN and READ-ONLY
  (`query_goal` — asking leaks no facts).
- Decision 2: the degree BRIDGE — `ask_comparative` falls back to the rung embeddings (the EXISTING
  `very`/`slightly` surface, nothing re-implemented): strictly higher rung `yes`, lower `no`,
  EQUAL rungs honest `unknown` for the strict question (rungs are coarse). A declared path beats
  the bridge (it refines within a rung).
- Decision 3: incomparability = honest UNKNOWN, never completed, never CWA'd to no; the reverse
  path is the entailed `no` of the strict order.
- H: `lint_comparisons` — cycles (`ada > bo > cy > ada`) and comparative-vs-degree conflicts
  (declared more but strictly lower rung; equal rungs do NOT conflict) as WARNINGS, never ⊥.
- G MEASURED 2026-07-16: end-to-end transitive ask over an n-link chain = 0.07s @10 / 0.7s @20 /
  3.3s @30 / 10.5s @40 — SUPERLINEAR (the demand round-loop re-serves every standing demand; the
  `demand-coref-perf-wall` shape). Session-sized chains are comfortably sub-second; revisit with
  the focus/Rust work, not with a bespoke closure.

**COMPOSITE SURFACE + BOOK/PLAYGROUND SURFACED 2026-07-16** — `ugm/cnl/world.py`
(`load_world`/`ask_world`: one CNL text mixing plain facts, rules, hedges, `either…or`, and
comparisons; questions route to comparative / `guess X` / banded `ask_goal`;
`tests/test_world.py`). The demo world is the UNCERTAIN DETECTIVE (the book's fil rouge, per user):
cy's shaky alibi (`cy is unlikely alibied`) makes `is cy thief` → **likely** (N(¬cleared)=0.7);
"be cautious" (θ=0.2) flips it to `no`; `guess culprit` collapses the ranked `either…or` glimpse;
suspicion is the comparative order (transitive yes + honest unknown). Book: new Part-3 chapter
`book/docs/advanced/more-or-less.md` (detective-flavoured comparatives; Next-chain rerouted
uncertain-world → more-or-less → identity); new playground page `book/docs/playground/uncertain.md`
(`data-mode="world"` → `_ugm_run_world` bootstrap in `playground.js`, banded policy + cautious
checkbox, graded verdict chips in `extra.css`); wheel rebuilt (CI rebuilds on deploy). The remaining
open threads *(updated 2026-07-16 — the polish batch landed)*: abduction/possibility-ordered
SUPPOSE (decision 5's first behaviour), the propagation-strength knob (open point I beyond θ), and
the band scale S7.7. DONE from the old polish list: why renders band **and env** (a derived fork
names the whole assumption-world it stands on — `standing on the likely world where: intruder is
tall; intruder is quiet` — `surface._env_lines`); the `be cautious`/`be decisive` CNL meta-line
(intake `stance` route → `kb.registers["policy"]`; explicit `policy=` still wins; words are the
declared `policy.STANCES` table).

**Slice edges left open (deliberate, small)** *(updated 2026-07-16: the who/existential branches
and `query_goal` are NOW BANDED — see below)*: the ENTAILED_NEG closure in `check` stays crisp (no
graded hard-negative); the `why` branch renders crisp provenance (band+env rendering is the open
polish item); an `ask_goal(commit=False)`/`query_goal` banded run sweeps its `<query>` pencils but
leaves derived FORKS behind (monotone + idempotent, but a leak worth revisiting); banded+scope EMIT
writes uncertain heads as forks (not scope pencils) — fine for `<query>` scopes, unexamined for
user SUPPOSE scopes. *(2026-07-16: the fork LEAK is FIXED — a `commit=False` banded `ask_goal`/
`query_goal` now snapshots the fork scopes and sweeps the ones it derived in its finally, so
repeated read-only queries neither accrete forks nor answer from their own leftovers.)*

**CNL GRAMMAR FIX 2026-07-16 — `is not a X` NACs:** the rule grammar silently mis-lowered
`… and ?p is not a woman` to `NAC (?p, is, a)` (the article swallowed the noun — the NAC never
blocked). Fixed in `authoring.py`: article tokens are `is_art`-tagged, the 4-token `is not ?o`
sugar DEFERS on an article, and a new 5-token `rule.cond.is_not_a` form lowers to a NAC on `is_a`.
(Surfaced because the book's surgeon example used exactly this shape. The matched `an` half was
closed the same day: `tokenize` folds `an` → `a` — mechanical like its lowercasing, at the one
chokepoint every path shares — so `is an X` / `is not an X` now work in facts, questions, rules,
and goals with no duplicated forms; `tests/test_cnl_articles.py`.)

**BOOK IN THE DETECTIVE LINE + README 2026-07-16 (user-requested):** every uncertain-world example
rewritten to the fil rouge — hedge = `cy is likely nervous`, doubt-travels = nervous→jumpy→
suspicious, the honest jump = the SHAKY ALIBI (`cy is unlikely alibied` ⇒ decisive `likely` /
cautious `no`, replacing the surgeon world; the riddle stays as a one-line allusion), paired
scenarios = the glimpsed INTRUDER, plus the banded `who`/`is anyone` beat; internals chapter +
appendix references aligned; new appendix entry "Comparisons — more, less, and honest gaps".
Root README: comparatives + possibilistic bullets in "Key CNL concepts" and "What is expressible",
plus a verified `load_world`/`ask_world` uncertain-detective snippet. NOTED SUBTLETY (in the
snippet): banded derivations MATERIALIZE (commit=True), so a later ask under a STRICTER θ on the
same kb still reads the earlier jump's fork — a stance is a session choice; change stance, fresh
session (consistent with crisp derived facts persisting, but worth remembering).

**BANDED WHY + ASSUMPTION PROVENANCE 2026-07-16 (suite 519 green)** — the explanation side (user
report: comparative `why` unparseable; step cards said yes/no not likely; nothing showed what was
assumed). Four pieces:
1. **Ink-leak FIX:** `ask_goal`'s why-branch ran its provenance closure WITHOUT the policy — in a
   banded session `why cy is thief` derived the θ-gated jump into INK (later asks read plain
   certain). Now threads `policy=policy_`.
2. **Assumption provenance:** `_nac_blocks` (banded) returns `(necessity, assumed)` — one
   `(pred, subj, obj, Π)` per surviving NAC; the banded EMIT journals them as inert `<assumed>`
   nodes wired `J --assumes--> <assumed>` (new `provenance.ASSUMES`/`ASSUMED` + reader
   `assumptions_of`); banded premises are found through the forks (`_find_banded_relnode`) so the
   tree can descend into pencil facts.
3. **Rendering:** `surface._explain_rel` shows each fact's band (`cy is thief (likely) <- rule…`,
   fork premises `cy is alibied (unlikely) (given)`) and, after the premises, `assumed not: cy is
   cleared (the counter-evidence is only unlikely)`. The `on_subgoal` resolve records carry `band`,
   so the playground's "asked itself" cards read "found something — but it's only unlikely" (this
   IS the what-was-assumed story at trace grain). This essentially closes the "why shows band+env"
   polish item (the assumption lines + banded premises show the worlds crossed; a literal
   environment listing is not rendered).
4. **Comparative `why`:** `comparative.explain_comparative` — declared-chain render
   (`cy > ada > bo → more-than chains — yes`), reverse-path `no`, rung-bridge compare, same-rung
   honest unknown, and the gap message ("the order is partial: this gap is the answer"); routed in
   `ask_world` (`why is X more D than Y`); playground quick buttons added (`why cy is thief`,
   `why is cy more suspicious than bo`).

**ASK/QUERY SURFACE COMPLETED 2026-07-16 (suite 516 green):** `ask_goal`'s WHO branch is banded —
each witness answers at its best band, a fork-only one wearing its band word (`who is thief` →
`cy is thief (likely)`; certain witnesses read as today); the EXISTENTIAL branch (`is anyone …`)
verdicts at the best witness's band; `query_goal(policy=banded)` returns `(subj, pred, obj, band)`
4-tuples (opt-in shape — a crisp call keeps triples). The playground's uncertain case regained the
`who is thief` quick button.

**Code surface (post-fold, 2026-07-16):**
- `ugm/chain.py` — THE banded engine (the fold): `_facts_matching(bands=True)` (OVERLAY_BAND read,
  `(s,o,band,env)`), `_band_overlay` (fork map + scope pencils at CERTAIN), `(state,band,env)` join
  threading with env pruning, graded `_nac_blocks` (θ gate + necessity), graded EMIT
  (`possibility.fork_fact`, strictly-better idempotence). All gated on `policy.banded`.
- `ugm/policy.py` — `uncertainty: "silent"|"banded"` (the GLOBAL stance) + `theta` (the α-cut dial).
- `ugm/possibility.py` — the fork VOCABULARY + verdict reads only: `add_fork`/`fork_fact`, bands,
  environments (`_env_consistent`, `<choice>`/`disjoint_from` exclusivity), `all_fork_bands`, and
  name-level `facts_matching_banded`/`possibility`/`naf_holds`/`verdict` (thin wrappers over the one
  matcher). The standalone applier/fixpoint is GONE.
- `ugm/check.py` — band-word verdicts between POSITIVE and ASSUMED_NO; `collapse` passes them through.
- `ugm/machine.py` — the one ISA op `OVERLAY_BAND` (dims the match `score` by a fork's band; min
  t-norm ⇒ weakest-link + multi-hop for free).
- `ugm/cnl/uncertainty.py` — CNL surface: hedges (KB-declarable, `probable means 0.7`), ranked
  `either…or`, `load_uncertain`, banded `ask`. Hedge lexicon DISJOINT from the degree adverbs.
- Tests: `tests/test_possibility_{band,cnl,rules}.py` + `tests/test_possibilistic_naf.py` (rules =
  the fold end-to-end through `chain_sip`/`check`/`ask_goal`).
- Book: `book/docs/advanced/uncertain-world.md`, `book/docs/deep/uncertain-world-internals.md`,
  appendix entries (see S7.8). Builds clean.

**INVARIANTS to keep (do not break):** (1) additive — the 480 crisp tests must stay green, never
touch the hot path; (2) QUALITATIVE/ordinal only — compare bands, no probability arithmetic (the one
sanctioned numeric is the necessity complement `1−Π`); (3) the THREE roles stay distinct (membership
≠ likelihood ≠ world-identity, S2); (4) likeliness lives on the SCOPE, not the edge primitive (S7.0).

**Polish backlog — 1–5 BUILT 2026-07-16, 6 remains:**
1. ✅ **θ into `FirmwarePolicy`** — `FirmwarePolicy.theta` (default **0.5**, range **(0, 1]**,
   validated in `__post_init__`; rationale: blocks a negation exactly when the counter-evidence is
   at least `likely`, so an even `either…or` alternative blocks and a merely-`unlikely` one doesn't).
   `naf_holds` / `apply_rule_banded` / `run_banded` take `policy=` (session dial); an explicit
   `theta=` stays as the per-call convenience override (the `check`/`open_preds=` shape).
   `test_theta_lives_on_policy`.
2. ✅ **KB-declarable hedge lexicon** — `probable means 0.7` parses (`parse_hedge_decl`) and is stored
   as an ORDINARY INK FACT; `hedge_bands(g)` reads defaults + declarations back through the one banded
   reader (the degree-adverb doctrine: the scale is KB data). Deliberately `means`, NOT the degree
   form `A is <number>` — the same surface would collapse hedge into degree adverb (three-roles).
   One-or-two-word hedges (`almost certain means 0.9`); `VERY_HEDGE_BAND` deleted — the `very`
   compositions are plain two-word entries in `HEDGE_BAND`. Declarations override defaults
   (`likely means 0.8`). Tests: `test_hedge_decl_parse` / `test_declared_hedge_*`.
3. ✅ **Ranked `either…or…`** — `x is either male and tall or more likely female and short` (also
   `or less likely`): the favoured alternative carries the `likely` rung, the other the `unlikely`
   rung, both from the lexicon IN SCOPE (so a declared `likely means 0.8` re-scales it) — ordinal,
   only the order + θ-cut matter. `parse_either` now returns `(subj, alt1, alt2, rank)`.
   Tests: `test_ranked_either_*`.
4. ✅ **Env-aware NAC** — `_nac_necessity` takes the BODY's env and skips any P-derivation whose fork
   is incompatible with it (Π counts only compatible worlds): `manly ← male ∧ not female` over
   `either male or female` now fires — within the male-worlds `not female` genuinely holds.
   Independent (compatible) forks still block. `test_nac_is_env_aware`.
5. ✅ **`disjoint_from`-declared exclusivity** — `_env_consistent` gains a second route: two forks
   whose COPULA claims (`is`/`is_a` only — `x knows female` predicates nothing) about one subject
   are ink-declared `disjoint_from` can't share an environment. Two independently-authored hedged
   facts (`x is likely male` + `x is likely female` + `male is disjoint from female`) now exclude
   each other in both the join and the NAC. `test_disjoint_from_makes_independent_forks_exclusive`.
6. ✅ **Fold banded reasoning INTO `chain_sip`** — BUILT 2026-07-16 (see "The fold in one paragraph"
   in the handoff header). Ratified at build time: (a) banded is a GLOBAL `FirmwarePolicy` stance
   (`uncertainty="silent"|"banded"`), never per-call, never automatic-on-forks; (b) the standalone
   forward layer was DELETED with the fold (one engine); (c) the `check`/`ask_goal` verdict surface
   shipped in the same increment.

Everything below is the full design record (unchanged); the BUILT markers in S7 track what shipped.

---

# Settled architecture (2026-07-15) — likeliness on edges + pencil-scopes for write-through

This supersedes the "reified disjunction node" / "phantom gate node" explorations above: both were
rejected because a matchable node forces **every** rule form and **every** traversal to route around
it (the `inert` mechanism already shows the disease — scattered, non-uniform skip-checks). The
chosen direction alters the substrate instead.

## S1. Likeliness is an orthogonal EPISTEMIC scalar on EDGES (substrate change)

- Edges gain one reserved scalar — **likeliness** — defaulting to *certain*. It is NOT a
  discriminating label (it never says WHAT a relation is — that stays reified on the middle node),
  so it does not resurrect typed edges; it is a modality on the *connection*. This is the invariant
  that keeps the change principled: **one reserved scalar, never an open label space.**
- **Uncertainty is expressed POSITIONALLY, never as a per-fact number.** A fact's likeliness is the
  **min-likeliness of the best path that reaches it** (weakest link; ordinal/qualitative — decision
  F, no probability arithmetic). The "certain core" is reached by certain edges; uncertain facts sit
  behind likeliness edges.
- This resolves the "each attribute needs its own likeliness" worry (marginals problem): attributes
  and relations INSIDE a branch stay **crisp**; likeliness lives on the edge that reaches the branch.
  Correlation (`male∧tall` vs `female∧short`) = co-location of the correlated facts behind ONE edge;
  disjoint alternatives = two edges from the same anchor, made exclusive by the EXISTING
  `disjoint_from` machinery (crossing both yields `male∧female`, which the linter already catches).
- Why edges beat a gate node: the property rides structure that already exists (no extra hop, no
  new skip-check), and it is invisible to rule *syntax* by construction — a rule matches predicates
  and attributes exactly as today; only the *traversal* accumulates min-likeliness. Rule syntax
  untouched; rule *execution* gains one min-accumulate step.

## S2. The THREE roles that must never collapse

1. **Membership** (fuzzy) — `very beautiful`. Object content, stays on the node.
2. **Likelihood** (epistemic) — now a property of the reaching EDGE / the scope, not the fact.
3. **World-identity** (structural) — which correlated scenario a fact belongs to = the scope tag.

Collapsing membership into likelihood gives the "likely male" = "somewhat male" error; collapsing
likelihood into world-identity loses correlation. Keep all three distinct.

## S3. Write-through is solved — by PENCIL/INK (SUPPOSE), NOT copy-on-write or time-machine

The hazard: crossing a likely edge and WRITING consequences permanently alters a node, which
defeasibility can't unroll. `suppose.py` already confronts this and names copy-on-write / graph-fork
as **SUPPOSE's TRAP** (backtrackable fact writes / TMS-by-deletion). The resolution, already built:

- **Two crossing modes** (mapping the earlier marker-vs-assume split):
  - **Marker mode** ("cy is *unlikely* a thief") writes NOTHING — a read that propagates
    min-likeliness to the *answer*. Trivially monotone-safe.
  - **Assume mode** (explore ramifications) = enter a **pencil scope keyed by the crossing
    assumption** (`suppose`): consequences are written in PENCIL (control rel nodes tagged
    `scope=…`, invisible to ink, visible only in-scope). Wrong → sweep the scope (`DROP_CTRL`);
    right → promote to ink. `The fact layer stays MONOTONE throughout — nothing unconfirmed ever
    became a fact.`
- **Coexisting ranked alternatives = multiple simultaneous pencil scopes.** Scope is a value and
  matching is scope-parametrized (`scope_members`, `_fact_relnodes(scope=…)`), so `scope=male-world`
  and `scope=female-world` coexist in the one graph, none touching ink. This IS the ATMS
  assumption-labelling — already built and monotone-safe.
- **THE DESIGN RULE:** *an uncertain write goes to PENCIL, keyed by the crossing assumption — never
  to ink.* Obey it → monotonicity is free and the time-machine is never built. Violate it (likely
  edge writes straight to ink) → you manufacture the TMS-by-deletion mess pencil/ink exists to avoid.
- The separate `retraction.py` (copy-on-**delete**: DECIDE-cascade → RECORD pre-image to inert
  `<history>` → privileged RETIRE, with `resurrect`/re-derivation) handles withdrawing a fact that
  DID reach ink — also without in-place undo. So both directions are covered.

## S4. Does it bite the current implementation? No.

Current uncertainty never writes to ink: defeasible/negative conclusions are demand-computed at
query time (not materialized), hypotheticals are pencil, and the one withdrawal path is
copy-on-delete. The write-through bite would appear ONLY for a naïve edge-likeliness that inks
directly — which S3's design rule forbids.

## S5. The single new build

SUPPOSE gives the write-safety for free but is currently **binary** (confirm/refute; pencil facts
crisp-in-scope). The increment:
1. substrate: likeliness scalar on edges (+ copy/serialize/traversal plumbing);
2. matcher: **min-accumulate** likeliness along a traversal (ordinal);
3. pencil facts + scopes carry the accumulated likeliness **band**;
4. verdicts gain the **likely / very-likely / unlikely / very-unlikely** band between `yes` and
   `assumed-no` — SUBSUMING today's four-verdict space (no gates ⇒ byte-identical crisp behavior).

## S6. Assumption-relative NAF — SPIKED & RESOLVED (2026-07-15)

Spike (`scratchpad/naf_spike.py`) modelled `either male∧tall or female∧short` as two pencil scopes
and probed `_facts_matching` (the exact primitive `_nac_blocks` calls, chain.py:758) under
scope=None / male-world / female-world. Result (`not-holds` = NAF holds; `BLOCKED` = present):

| target | certain(None) | male-world | female-world |
|---|---|---|---|
| male   | not-holds | BLOCKED   | not-holds |
| female | not-holds | not-holds | BLOCKED   |
| tall   | not-holds | BLOCKED   | not-holds |
| short  | not-holds | not-holds | BLOCKED   |

**Findings:**
1. **Assumption-relative NAF already works** — no new mechanism. `_nac_blocks` evaluates each NAC
   via `_facts_matching(..., scope=scope)`, the SAME scope as the positive body; pencil is visible
   only within its scope. Each world computes NAF over *ink + its own pencil*.
   Stratification-per-assumption-set = the existing per-run stratification (each scope is its own
   `chain_sip` pass).
2. **The open question resolves to "SILENT UNTIL ASSUMED."** Visibility is BINARY (in-scope /
   invisible-out), so a gated fact is *absent* in the certain world — it neither satisfies a body
   nor trips a NAC there; it acts only under its scope. "Fire-but-marked-unlikely" is NOT in the
   machinery today.
3. **Correlation & exclusivity are free** — `male∧tall` joint by co-scoping (both or neither);
   forks don't cross-contaminate; ink stays certain under every scope.
4. **Certain world is honestly agnostic** — `not male` AND `not female` both hold there (an unentered
   fork; incomplete, not contradictory).

**Consequence — the remaining build is localized to ONE thing (the graded band, S5.3–4).** NAF,
correlation, monotone safety: done/free. The architecture is TWO layered modes; only the second is
new:
- **Silent-until-assumed** (default) — already works; safe by construction (uncertain facts never
  touch certain reasoning unless a scope is entered).
- **Marker mode** (opt-in, NEW) — a fact visible *with a likeliness band* instead of
  invisible-out-of-scope, so a body can fire "unlikely" without committing. = min-accumulate along
  the traversal + band-on-visibility. This is the sole remaining increment.

---

# S7. Graded band — design (2026-07-15)

## S7.0 The simplification the spike bought: likeliness lives on the SCOPE, not the edge primitive

Entering a fork *is* crossing "the uncertain edge," and every uncertain fact already lives in a
scope (a singleton scope for a lone uncertain relation). So **the likeliness of "the edge into a
fork" = a band on that fork's `<hypothesis>` scope node** — a reserved graded attr `<likeliness>`,
reusing the existing degree-adverb lexicon (`very`=0.8 / `somewhat`=0.5 / `slightly`=0.3),
interpreted ORDINALLY (compare only, never arithmetic — decision F). Absent ⇒ CERTAIN (ink = 1.0).

**Consequence: S1's "scalar on the edge primitive" is NOT required.** It is realized positionally as
*scope-membership + scope-band*, reusing pencil + graded attrs. Altering the edge representation
remains available as optional ergonomics, but it is not load-bearing and would still need the same
read-program band-threading below. The honest "alter the substrate" turns out to be **a band attr on
scope nodes + one read op**, not a change to edges.

> **DECIDED (user, 2026-07-15): scope-band, not the edge primitive.** The edge-primitive version is
> shelved as unneeded. (Aside the user noted: the reason the scope/pencil mechanism wasn't front of
> mind is that the tutorial book under-describes it — see S7.8.)

## S7.1 The seam: the OVERLAY read op (chain.py:540)

Today `OVERLAY("r", CONTROL_MARK, _SCOPE_OVERLAY)` admits rel `r` iff it lacks the control marker
(ink) OR is in `registers[_SCOPE_OVERLAY]` = the ONE active scope's pencils (`_scope_pencils`).
Boolean. Two overlay shapes, only the second is new:

- **Silent/assumed (today):** overlay = one scope's pencils (or None). Binary. Unchanged, byte-for-byte.
- **Marker mode (new):** overlay = the UNION of ALL forks' pencils, plus a band map `{rel_id: band}`
  (each rel → its scope's `<likeliness>`; ink → CERTAIN). A read op variant `OVERLAY_BAND` admits a
  union-overlay rel AND annotates the match with its band. `_facts_matching` return extends
  `(subj,obj)` → `(subj,obj,band)` in marker mode; silent mode stays `(subj,obj)` (band ≡ CERTAIN).

## S7.2 Min-accumulate = environments (ATMS), qualitative

A derivation using facts of bands b₁..bₙ yields a head of band **min(b₁..bₙ)** (weakest link,
ordinal). It carries an ENVIRONMENT = the union of the used facts' fork-scopes. Verdict over
alternative derivations = **max band** (possibility = qualitative max-of-min).

**Environment consistency BUILT 2026-07-15** — `facts_matching_banded` returns `(s,o,band,env)` (env =
the singleton fork a fact depends on, read from the matched rel's `SCOPE`); `_match_body` UNIONs env
across the join and PRUNES any environment that combines two distinct forks of the same `<choice>`
(mutually-exclusive `either…or` alternatives can't both hold). So `?p is male ∧ ?p is short` (two
alternatives of one choice) is correctly IMPOSSIBLE, while `?p is male ∧ ?p is tall` (one fork) derives
at the fork band. `_env_consistent`; `test_cross_exclusive_fork_derivation_is_impossible`.
**Head-environment propagation BUILT 2026-07-15** — a derived head fork stores its assumption-set
(`<derived-env>`); the read returns that TRANSITIVE env (`_scope_env`), so a rule chaining off a
derived fact inherits its parents' forks. A two-step chain `manly ← male` then `puzzling ← manly ∧
short` correctly finds `{forkA, forkB}` impossible → `puzzling` not derived
(`test_head_environment_propagates_across_a_chain`). This closes the ATMS soundness loop for forward
chaining.
~~Remaining (minor)~~ all closed since: the NAC is ENV-AWARE (2026-07-16 — Π counts only worlds
compatible with the body's env), declared `disjoint_from` IS wired into `_env_consistent`
(2026-07-16), and `run_banded` drives a bank to a fixpoint (2026-07-15).

## S7.3 NAF with a band — the α-cut θ IS the bias dial (the key decision)

Marker-mode NAF: `not P` **blocks iff P is reachable at band ≥ θ**, where θ is a metareasoning dial
(this is open-point I, the propagation/decisiveness knob, cashed out). This θ is exactly the
**bias-vs-decisiveness control**:
- **high θ** → ignore low-possibility alternatives → decisive, more bias-prone (concludes from
  `not female` even when female is merely unlikely);
- **low θ** → refuse to conclude from `not P` when P is even slightly possible → cautious,
  bias-averse.

The `test_possibilistic_naf` gender case becomes θ-controlled: with all forks overlaid, `female` is
visible at its band; whether the biased rule fires is precisely whether female's band clears θ. This
is the concrete, tunable mitigation of the "premature jump" (decision 6): the prior is a visible
band, and θ is the dial that says how sure you must be of an absence before you lean on it.

*Graded negation band* (the necessity side — a NAF-derived conclusion is only as strong as the
counter-evidence is unlikely) **BUILT 2026-07-15**: θ stays the hard gate (`Π(P) ≥ θ` blocks), and a
surviving NAC folds `N(¬P) = 1 − Π(P)` (possibility/necessity duality, Dubois–Prade) into the head
band, so `flagged` in the surgeon case is emitted at `min(body, 1−Π(female))` — e.g. female 0.3 ⇒
flagged "likely" (0.7), NOT "certain". `possibility._nac_necessity`;
`test_graded_negation_scales_with_counter_evidence`.

## S7.4 Verdict space (subsumes today's four)

`band=CERTAIN` → **yes** · `0<band<1` (only gated derivations) → **very-likely/likely/unlikely/
very-unlikely** (band→word) · no derivation, closed → **assumed-no** · open/fuel → **unknown**. The
band ranks strictly between `yes` and `assumed-no`. No gates present ⇒ byte-identical to today.

## S7.5 Change surface (small, additive, differential-gated)

0. **CNL surface (the authoring half — new forms in `ugm/cnl/`):**
   - hedge-on-a-fact → banded scope: `x is likely male`, `cy is unlikely a thief`
     (`likely`/`unlikely`/`very likely`/`very unlikely` reuse the degree-adverb lexicon; the fact is
     penned into a scope whose `<likeliness>` = the hedge's degree);
   - correlated disjoint alternatives → two forks: `either male and tall or female and short`
     (each conjunction co-scoped behind one fork; mutual exclusion via existing `disjoint_from`);
   - verdict rendering gains the band words (the question forms are unchanged — only the answer
     surface grows `likely`/`unlikely`);
   - (optional) a meta-line for θ: `be cautious` / `be decisive` sets the NAF α-cut dial.
1. `<hypothesis>` scope nodes carry a `<likeliness>` graded attr (authoring sets it from the hedge).
2. `_scope_pencils` gains a marker-mode sibling `_all_fork_bands(fact_g) -> dict[rel_id, band]`.
3. new `OVERLAY_BAND` read op (or OVERLAY extension) admitting union-overlay + annotating band;
   `_facts_matching` marker-mode returns `(s,o,band)`.
4. `_nac_blocks` marker-mode: block iff any match band ≥ θ (θ from `FirmwarePolicy`).
5. `chain_sip` EMIT: head band = min(positive-body bands); emit into the environment (SLICE 1: one
   scope; SLICE 2: combined).
6. verdict rendering: band → word; `why` shows the band + the environment (assumption-set) crossed.

The positive/crisp core is untouched: marker mode is opt-in, silent mode keeps the binary OVERLAY,
and forward/demand parity is gated by `tests/test_forward_demand_parity.py`.

## S7.6 Two slices

- **SLICE 1** — single-fork marker mode, θ-crisp NAF, conclusions carry min positive-body band.
  Delivers "cy is unlikely a thief" and the θ-tunable bias mitigation. No environments.
  - **ENGINE CORE BUILT 2026-07-15** — `ugm/possibility.py` (`add_fork` / `facts_matching_banded` /
    `possibility` / `naf_holds(θ)` / `verdict`), standalone & additive (chain.py untouched), the band
    on the fork's `<hypothesis>` scope (`<likeliness>`). Tests: `tests/test_possibility_band.py`
    (10 green) + `tests/test_possibilistic_naf.py` (the binary silent-until-assumed default).
    θ-as-bias-dial demonstrated (`test_theta_is_the_bias_dial`).
  - **CNL SURFACE BUILT 2026-07-15** — `ugm/cnl/uncertainty.py`: (1) hedge-on-a-fact
    `SUBJ is <hedge> [a] OBJ` → `add_fork` (`likely`/`unlikely`/`very likely`/`very unlikely`, a
    lexicon DISJOINT from the degree adverbs so `x is very urgent` stays a membership degree —
    proven by `test_degree_adverb_is_not_a_hedge`); (2) the FIRST disjunctive form
    `SUBJ is either A and B or C and D` → two correlated forks (co-scoping proven,
    `test_either_or_makes_two_correlated_forks`); (3) banded yes/no verdicts (`ask`). Loader is
    additive (`load_uncertain` returns non-possibilistic lines for the ordinary loader).
    Tests: `tests/test_possibility_cnl.py` (6 green).
  - **ISA FOLD BUILT 2026-07-15** — `OVERLAY_BAND` op added to `machine.py` (the graded sibling of
    `OVERLAY`: `live` holds a `{rel_id -> band}` map; admitting a fork rel SCALES the match `score`
    by its band via the min t-norm). `possibility.facts_matching_banded` now runs through
    `Machine.match` (uniform with crisp reads) and the band IS the match `score`. KEY WIN: because
    `State.score` already composes by `T_MIN`, **multi-hop min-accumulate comes for free** —
    `test_overlay_band_min_accumulates_multi_hop` proves a 2-hop banded path = min(0.6,0.5)=0.5
    through the real matcher. Full suite 468 green (no core regression).
  - **BANDED RULES BUILT 2026-07-15** — `possibility.apply_rule_banded`: marker-mode application of a
    single-variable rule. Body band = min over body atoms (a body atom reaching through a fork bands
    the whole rule); NAC gated by θ-crisp NAF (the bias dial); a CERTAIN body writes INK (crisp
    behaviour), an uncertain body writes the head as a FORK at the body band. Reuses `possibility`
    (the OVERLAY_BAND read), so chain_sip is UNTOUCHED. Tests `tests/test_possibility_rules.py` (3):
    θ gates the surgeon biased-jump; a fork-body bands the conclusion end-to-end (CNL → banded
    verdict); a certain body stays ink. Full suite 471 green.
  - **MULTI-VARIABLE BANDED RULES BUILT 2026-07-15** — `facts_matching_banded` now takes WILDCARD
    endpoints (either end None), so a body atom with a free variable reads (three ISA programs: subj/
    obj/neither-bound, all with the OVERLAY_BAND rel-guard). `apply_rule_banded` is now a general
    nested-loop JOIN (`_match_body`) threading bindings + min-band across atoms; NAC is θ-crisp
    (`_nac_blocks`), and across alternative derivations the BEST band wins (possibility = max-of-min).
    Tests `tests/test_possibility_rules.py` (6): θ-gated bias, fork-body bands the head, certain body
    → ink, a 2-variable join `?p knows ?q ∧ ?q is spy` through a fork, and max-of-min. Full suite 473
    green. Single-var `_entity_names`/`_ground` DELETED (superseded).
  - **REMAINING in Slice 1 — NONE** *(updated 2026-07-16: (a) θ-in-policy, (b) KB hedge lexicon,
    (c) ranked `either…or…` + `disjoint_from` exclusivity, and (d) the `chain_sip` fold are ALL
    BUILT — see the handoff header)*. Graded negation band and cross-fork ENVIRONMENT consistency +
    forward HEAD-environment propagation are DONE (see S7.3, S7.2).
  - **BANDED FIXPOINT DRIVER BUILT 2026-07-15** — `possibility.run_banded(g, rules, theta=)`
    forward-chains a whole bank to a fixpoint (the banded analogue of `run_bank`, standalone/additive).
    `apply_rule_banded` is now idempotent (a head is (re-)emitted only at a STRICTLY better band), so it
    terminates (finite band lattice, monotone-up); head-env propagation keeps a multi-step chain sound.
    Tests `tests/test_possibility_fixpoint.py` (4): a 3-rule chain carries the band to the transitive
    conclusion; idempotence (a re-run emits 0); an all-ink chain stays CERTAIN/ink; an exclusive-fork
    chain never fires `puzzling`. Full suite 480 green.
  - ~~Remaining Slice 2 (minor): env-aware NAC + `disjoint_from`-declared exclusivity~~ — BOTH BUILT
    2026-07-16 (backlog items 4 & 5 above).
- **SLICE 2** — cross-fork environments (combined assumption-sets, min band) + graded negation band
  (necessity via ordinal complement). Full ATMS. **COMPLETE 2026-07-16** (env-aware NAC and declared
  exclusivity were the last pieces).

## S7.7 Still-open (non-blocking)

- exact ordinal band scale + word mapping (reuse adverb lexicon vs a dedicated 5-rung enum);
- default θ and its range (open-point I);
- SLICE-2 combined-environment representation (a scope whose members are other scopes?) + its perf
  (the `demand-coref-perf-wall` caution applies to cross-fork fan-out).

## S7.8 Documentation — BUILT 2026-07-15

Three book pieces landed (book builds clean, no broken links):
- **Part 3 (concept):** `book/docs/advanced/uncertain-world.md` — "Living in an uncertain world":
  hedged facts, doubt-travels (weakest link), the honest surgeon jump + the θ dial, correlated
  `either…or`, impossible worlds, all still pencil. Uses GENUINE engine output. Rerouted Supposing's
  "Next" → this chapter → Identity.
- **Part 4 (mechanism):** `book/docs/deep/uncertain-world-internals.md` — "Shades of maybe": bands on
  pencil scopes, `OVERLAY_BAND` dimming the match score (min = weakest link), θ as an α-cut on NAF,
  necessity `1−Π` for graded negation, environments/ATMS — and framed as NOT a tenth mode (a
  composition of Suppose + graded matching + Check, respecting the closed inventory). Rerouted Modes'
  "Next" → this chapter → Firmware.
- **Appendix:** two concept entries ("Possibility — likely and unlikely"; "Environments — worlds that
  can't both be true") + an `OVERLAY_BAND` row in the instruction-set data-path table.
