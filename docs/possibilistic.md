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
- **D. `defeasible-guess` mechanics.** How it threads the provenance journal; how `why` renders it;
  what it records in the tie/incomparable case (competitors + "guessed among equals"). **First one
  to sketch.**
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
ordinal). The head is emitted into an ENVIRONMENT = the union of the used facts' scopes, whose band =
min. Single-fork derivations stay in one scope (SLICE 1); cross-fork derivations mint a *combined*
environment (SLICE 2 — the general ATMS assumption-set). Verdict over alternative derivations =
**max band** (possibility = qualitative max-of-min).

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
counter-evidence is unlikely, an ordinal complement) is a SLICE-2 refinement; SLICE 1 uses θ-crisp
NAF and carries the min band of the POSITIVE body only.

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
and the `_CROSSCHECK` differential gate still guards the shared matcher.

## S7.6 Two slices

- **SLICE 1** — single-fork marker mode, θ-crisp NAF, conclusions carry min positive-body band.
  Delivers "cy is unlikely a thief" and the θ-tunable bias mitigation. No environments.
  - **ENGINE CORE BUILT 2026-07-15** — `ugm/possibility.py` (`add_fork` / `facts_matching_banded` /
    `possibility` / `naf_holds(θ)` / `verdict`), standalone & additive (chain.py untouched), the band
    on the fork's `<hypothesis>` scope (`<likeliness>`). Tests: `tests/test_possibility_band.py`
    (10 green) + `tests/test_possibilistic_naf.py` (the binary silent-until-assumed default).
    θ-as-bias-dial demonstrated (`test_theta_is_the_bias_dial`).
  - **REMAINING in Slice 1:** (a) CNL surface (S7.5 item 0 — hedge-on-fact, `either…or…` forks, band
    words in verdicts); (b) FOLD the standalone reader into the ISA `OVERLAY_BAND` read op so marker
    mode runs through the one matcher (chain.py:540) and multi-hop derivations min-accumulate; (c)
    wire `θ` into `FirmwarePolicy`.
- **SLICE 2** — cross-fork environments (combined assumption-sets, min band) + graded negation band
  (necessity via ordinal complement). Full ATMS.

## S7.7 Still-open (non-blocking)

- exact ordinal band scale + word mapping (reuse adverb lexicon vs a dedicated 5-rung enum);
- default θ and its range (open-point I);
- SLICE-2 combined-environment representation (a scope whose members are other scopes?) + its perf
  (the `demand-coref-perf-wall` caution applies to cross-fork fan-out).

## S7.8 Documentation follow-up (AFTER the build)

- The tutorial book under-describes the SUPPOSE/pencil/scope mechanism (only `09-supposing.md`),
  which is WHY the scope-band realization (S7.0) wasn't obvious — worth a pass to surface that
  scopes are reusable, coexisting world-labels, not just a one-shot hypothesis test.
- New book chapter (working title **"Living in an uncertain world"**) once SLICE 1 lands: authoring
  banded facts, the two crossing modes (marker vs assume), reading `likely`/`unlikely` verdicts, and
  the θ dial as the bias-vs-decisiveness control. Belongs in the advanced track near supposing.
