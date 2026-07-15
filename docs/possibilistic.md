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

## S6. THE open question a spike must settle — assumption-relative NAF

When a query does NOT take a stance, may a gated (uncertain) fact satisfy a rule body / trip a NAC
at all?
- `?p is a thief when ?p has ?motive` — if `motive` is reachable only through an unlikely edge, does
  the rule fire (conclusion marked "unlikely"), or stay silent until someone assumes the gate?
- Dually: does `not (x is male)` hold in the certain world when `male` sits behind a gate? (Proposed:
  yes — the certain-world NAC ignores gated facts; a NAC evaluated *under* a scope sees that scope's
  gated facts. Stratification must hold PER assumption-set.)

**Spike example** (exercises correlation AND assumption-relative NAF at once):
`either male and tall or female and short`, then a `not` inside one branch. Probe: (a) certain-world
verdicts for `male`/`tall`; (b) in-scope verdicts under each branch; (c) whether a NAC referencing a
gated fact fires certain-world vs in-scope.
