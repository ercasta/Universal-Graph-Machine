# Critique — an external-eye assessment of the UGM

> **Status: CURRENT-STATE ASSESSMENT, 2026-07-17** (written by the assistant at the user's
> request). Reads the system as it stands today against its own claims and against the
> literature. Companion to `related_work.md` (positioning) and `README.md` (what the claims
> are). This is deliberately an outside voice: where it disagrees with the vision docs, that
> is the point of the document, not an error to reconcile. A reviewer starting cold should
> read this, then `vision.md`, then the design docs it cites.
>
> State at time of writing: full suite **569 passed in 22s** (verified, not quoted);
> ~12ms/utterance ingest; bit-for-bit deterministic runs; a public tutorial book with an
> in-browser (Pyodide) playground; zero non-author users to date.

## 1. Overall rating

As a research prototype: **strong — coherent, disciplined, unusually well-governed; but
under-evidenced, and the gap between internal quality and external evidence is now the
headline risk.** By dimension:

| Dimension | Rating | Basis |
|---|---|---|
| Conceptual coherence / internal consistency | Very high | One idea (single substrate) applied without exception and now enforced structurally, not just by discipline (§2.1) |
| Engineering discipline | Top-tier | Ratified-decision stack; differential gating of every fast path; a demonstrated track record of rejecting *working* features on principle (§5); measured, accepted costs (e.g. always-on provenance at +15% on the heaviest ask) |
| Novelty | Moderate, with one real spike | Mostly recombination of well-understood mechanisms; one genuinely unusual commitment (§2.2), plus a distinctive answer *surface* (§3) |
| External evidence of value | Low, and now compounding | Many capability claims (uncertainty, revision, procedures, grammar extensibility), each internally tested, none externally evidenced; no comparison against deployed alternatives; no non-author user has touched it |
| Performance viability | Favorable at the ratified scope | Session-scale numbers hold (~12ms/utterance); the known superlinear edges are mapped and fenced; cross-bank composition at real scale unmeasured (§4.1) |

## 2. Novelty — the honest ledger

The system's own positioning (`related_work.md`) is unusually honest: this is a
**recombination with one genuinely unusual commitment**. The headline claims, individually
judged against the literature — they are *not* equally strong:

### 2.1 "One substrate" — a structure, not just a commitment

Rules live in the same graph as facts (a separate rule bank is an opt-in keyword, not a
requirement); there are **no privileged partitions**: no kind-flags, no matcher modes — what
a node "is" (fact, rule, mention, provenance, pattern) is an ordinary attribute plus which
rules select it, and visibility is enforced by compiler-emitted guard instructions in the
lowered programs, not by hardcoded matcher behavior. No neighbor holds this: AtomSpace keeps
a typed Atom hierarchy, CHR keeps the constraint store apart from the rules, Maude's
reflection is a meta-level tower rather than one flat store. One honest re-phrasing is
required, though: the substrate is kind-less *because the lowering compiler is kind-aware*.
The conventions did not vanish; they moved into uniformly-emitted guards in the
authoring/lowering surface. That is the right place for them — an author cannot forget a
guard the compiler emits — but the accurate claim is "no seam in the substrate; the seams
live in the surface compilers, uniformly emitted." Say it that way first.

### 2.2 "No seam" between language and computation — the one real spike

CNL is loaded as-is and *stays* in the substrate: tokens are first-class nodes, parsing is
in-graph rewrite rules on the same graph as reasoning, and there is no caller-side fork —
a question lands as a live `<query>` control node, so asking, asserting, commanding, and
*teaching grammar* are one motion, routed by which forms fired, never by sniffing the
string. ACE/PENG/GF all compile out to a logical IR; parsing-as-deduction interleaves but
discards the text. Keeping the text is real novelty of commitment. Two things sharpen it:

- **The grammar itself is user-space.** A domain KB file can declare a new sentence shape in
  CNL (`form KEY : HEAD when BODY`), and facts and questions in that shape parse, answer,
  feed the nearest-forms rejection, and can be disabled — no Python edited. In-language
  syntax extension has precedents (Lisp reader macros, Prolog `term_expansion`/`op`, Racket
  `#lang`); extensibility per se is not the novelty. Doing it in a CNL whose sentences are
  graph data, with habitability lint covering authored shapes and strict, loud
  declare-before-use, has no named precedent I can find. Scope honesty: this is "extensible
  from outside, in the language" — the fundamental shipped banks are deliberately frozen
  Python, and full grammar reification was considered and cut. Not self-hosting.
- **Caveat unchanged:** this is novelty of *commitment*, not yet of *demonstrated payoff* —
  the claim that keeping the text in the graph buys something (faithful explanation, no IR
  drift) is plausible and central to §3, but has not been measured against a compiled
  baseline.

### 2.3 The "low-level machine" — well-executed, and the least novel headline claim

The engine's semantics are ISA programs run by one interpreter: a register machine with a
data path and a control path (PC, branches, CALL/RET, SUSPEND/RESUME continuations), the
demand solver and the round loops included — Python drivers reduced to thin loops over
machine programs. As an idea this is a forty-year tradition and should be positioned inside
it: the WAM compiled Prolog to a register machine in 1983, Soufflé lowers Datalog to its
RAM, Rete compiles match into a discrimination network, SECD/CEK/CAM did
control-as-instructions before that. Pitching the machine itself as novel would invite the
wrong fight and lose it. What *is* distinctive and worth claiming:

- the machine runs **over the homoiconic graph itself** — registers hold node-pointers, a
  value operand is a regular node carrying an ordinary attribute, focus and scope are
  register-pointed live-sets — so machine state is graph-adjacent rather than a foreign
  store, which is what lets "machine semantics are ISA programs" hold without a
  serialization boundary;
- the tool/ask boundary is a machine **SUSPEND/RESUME continuation** — the world is an
  effect the machine suspends on; the nearest literature is algebraic effect handlers, not
  agent frameworks;
- **firmware-as-reference-semantics with mandatory differential gating** of every
  accelerator — compiler-engineering discipline imported into a reasoning system.

Standing watch item: `PRIM` is an escape hatch — a PRIM wrapping arbitrary Python is Python
in a costume — and the "name the irreducible primitives" list (skolem re-finding and
sub-demand raising are still Python helpers) is the discipline that keeps the ISA a
contract. It should be finished.

### 2.4 "Think harder" — a distinguishing honesty, not a novelty

Effort is a content-blind budget and exhaustion is an honest UNKNOWN — answers are the best
of current knowledge under a budget, not theorems. This stance has named thirty-year
precedents: it is nearly verbatim NARS's *Assumption of Insufficient Knowledge and
Resources*; anytime algorithms (Dean–Boddy) and bounded-rationality metareasoning
(Russell–Wefald) are the other neighbors. None are cited in `related_work.md`; they should
be. The genuinely nice local cut is the ratified **decoupling of effort from likelihood**:
fuel says how hard to look, possibility says which branch first, and they meet only as
ordering under a shared budget — a clean separation many systems muddle. Warning: the knob
inventory is growing (fuel, θ, stance words like `be cautious`, a proposed
propagation-strength knob, focus size). Each is individually content-blind and defensible;
jointly they are becoming a tuning surface with no stated policy for setting them, which is
how metareasoning layers historically rot into config soup.

### 2.5 "Likeliness and gradedness" — borrowed logic, distinctive answer surface

The uncertain layer runs inside the one engine as a policy stance: qualitative, ordinal
possibility bands (min t-norm, weakest link), ATMS-style environment pruning across
exclusive worlds, a θ dial gating graded absence. As logic this is Dubois–Prade
possibilistic logic plus de Kleer's ATMS — both correctly named in the system's own design
doc, which is better positioning hygiene than the rest of the doc set. PLN, ProbLog, PSL
all do graded inference; the logic is not the contribution. What no deployed neighbor
offers is the **epistemic provenance of the answer surface**: "no (assumed)" versus a hard
"no"; "likely" as a verdict word; a defeasible guess that records its basis (clear-max vs
tie) and *every competitor with its band*; a `why` that renders "assumed not: X (the
counter-evidence is only unlikely)" and names the assumption-world a derived fact stands
on. ProbLog returns a number; this returns the audit. Two limitations to own out loud
rather than have discovered: ordinal min-chain semantics has the known possibilistic
**drowning problem** — two independent weak signals never accumulate into a stronger
conclusion, ever; the deliberate no-arithmetic stance buys honesty at the price of never
learning from converging evidence. And banded derivations **materialize** — change stance,
fresh session — a documented footgun of exactly the convention-fragility class in §4.2.

### 2.6 Belief revision — a JTMS by another road

Stale materialized conclusions are revised demand-driven: new knowledge only *marks* (a
dirty set of predicates), a committed ask sweeps affected assumption records, re-asks each
assumption's positive, and withdraws broken conclusions by an over-forget-and-re-derive
cascade, stamping the history so `why` can answer *"withdrawn because X became derivable."*
Positioning honesty: delete-and-rederive is Gupta–Mumick's DRed; justification-based
withdrawal is Doyle's TMS (1979); assumption contexts are de Kleer's ATMS. The local
contributions are the *policy* (revise at question time, never eagerly at intake — nothing
else in the TMS tradition is demand-driven in this sense) and the honest cost accounting
(always-on provenance measured and accepted). The tradition should be cited.

### 2.7 The closed mode inventory — the underrated contribution

Nine processing verbs, closed, with an acceptance test designed to block new mechanisms.
Individually the verbs all have precedents; a *closed* inventory held under pressure is
rare. The evidence is no longer aspirational: the uncertain layer, gradable comparatives,
belief revision, procedures, and grammar authoring **all landed as compositions of the
existing modes — zero new mechanisms** (revision = CHECK + retract; procedures = ITERATE ×
CALL × CHECK; banded = a policy stance on the one engine). Most cognitive architectures
accrete mechanisms; this one built an immune system against accretion, and §5 records it
rejecting *working* code. This is quietly becoming the strongest evidence the architecture
has, and it is the paper-worthy claim.

### Missing neighbors in `related_work.md` (reviewers will raise these)

Still absent and now overdue, since the mechanisms that need them are built: **NARS** (the
AIKR stance, §2.4); **ATMS/TMS — de Kleer, Doyle — and DRed** (assumption records,
environments, revision, §2.5–2.6); **possibilistic logic — Dubois–Prade** (cited in a
design doc but not in the positioning doc); **local closed-world assumption** (Etzioni;
Knowledge Vault) for CWA-default-with-per-predicate-OWA; **algebraic effects** for the
suspend boundary (§2.3); **anytime/metareasoning** (Dean–Boddy; Russell–Wefald).

## 3. Strongest value proposition

Not the homoiconic substrate itself — that is the means. The sellable end is: **an
auditable, bounded, defeasible business-rules reasoner whose explanations — including its
assumptions, its guesses, and its retractions — are the author's own sentences.** Four
things compose into something no deployed system offers together:

1. **Journal-as-proof rendered from CNL nodes** — the explanation is *faithful by
   construction*, not a template re-rendering. Drools/ODM cannot do this at all.
2. **Honest, explainable negative and uncertain answers** — bounded CHECK yields "assumed
   no — I looked and found nothing within budget"; the graded layer yields "likely," "no
   (assumed)," and guesses that name their competitors. Neither exhaustive provers (a claim
   about the universe) nor Prolog NAF (silent failure) nor probabilistic engines (a number
   without an audit) offer this. It is the single most distinctive *user-facing* property.
3. **Revision with receipts** — a withdrawn conclusion can say what new fact broke it.
   Production rule engines silently re-fire; this explains the change.
4. **Conflict-lint at authoring time** — surfacing undeclared priority conflicts as
   questions targets exactly where real rule books rot, where Drools silently uses salience
   and formal logic just halts.

Secondary but real: the substrate is text-native, so an LLM reads and writes it without a
serialization layer; the pending tool call is an inspectable graph node with provenance
(where agent frameworks hold it in opaque Python); and runs are bit-for-bit deterministic —
an underrated property for a system whose pitch is auditability.

The caveat that governs all of §3: every one of these is an *inference from design*, not a
measurement. No head-to-head against Drools/DMN on authoring and audit, ACE+RACE on CNL
fidelity, or SPINdle on the defeasible fragment has been run.

## 4. Main weaknesses

1. **Performance — favorable at the ratified scope, with named open edges.** The system is
   explicitly scoped to session-sized work (2–3 domain banks, per-utterance latency, not
   billion-triple batch): at that scope the numbers hold (~12ms/utterance; the accretion
   cliff answered *in-substrate* by bounded attention — a `<focus>` working set — rather
   than by background compilation, which substantially defuses the "AOT compiler becomes
   the real system" scenario at this scope). The honest open edges: (a) **cross-bank join
   selectivity** — combining banks is the stated core use case; one small in-house
   composition (the procedures bank riding the planner banks end-to-end) exists, but the
   experiment at real scale (E4) has not run; (b) **known superlinear shapes** — transitive
   comparative chains measured 0.07s at 10 links → 10.5s at 40 (the demand round-loop
   re-serves standing demands); fine at session size, mapped, fenced by fuel, unfixed;
   (c) per-query combinatorics (elimination walks, SUPPOSE cascades) — fuel-fenced,
   constant-factor, not a cliff.
2. **Convention fragility.** The untyped substrate's flexibility is its liability:
   correctness in several places depends on discipline the type system cannot enforce. The
   compiler-emitted guards (§2.1) answered the worst class (a forgotten visibility guard).
   But the class keeps producing instances, most recently the **stratification race**: the
   unstratified forward loop can fire an act's `ready` before the `unmet` that should block
   it is derived (NAC-over-derived-facts — textbook stratified negation), so correctness
   depends on the driver choosing the stratified loop; the in-repo intake act loop is
   currently the unstratified one, flagged in the system's own design notes. Every instance
   so far has been self-caught by one careful author; multiply by external KB authors and
   the exposure grows. The standing verdict: **the linter needs to be as central as the
   engine, and it is not** — conflict-lint, recognition-safety lint, and comparison-lint
   exist, but the general convention lint over the substrate remains documented discipline,
   not enforcement.
3. **The evaluation gap, now compounding.** The benches and 569 tests demonstrate
   *coverage*, not *advantage* — and the claim surface has grown much faster than the
   evidence: uncertainty, comparatives, revision, procedures, and grammar extensibility are
   each tested internally and evidenced externally not at all. The ratio of claims to
   outside evidence is moving the wrong way even as internal quality stays exceptional.
   §3 remains an inference, not a measurement.
4. **The habitability question is load-bearing, unanswered, and cheaper than ever to
   answer.** User-intent→CNL is where controlled languages historically die: users cannot
   stay inside the fragment, and the frustration lands on the first sentence. The design
   answers exist (unified intake, named rejection with nearest-forms, authorable forms) and
   the instrument now exists too — the tutorial book with an in-browser playground collapses
   the cost of a stranger test from "clone a repo" to "open a URL." Yet no non-author human
   has authored or audited a rule book in it. The surface a stranger must inhabit (facts,
   rules, questions, hedges, comparisons, stances, forms, procedures) is large and growing,
   which raises both the stakes and the information value of the test (E1).
5. **The purity boundary — honest, but keep auditing it.** Disjunction now lives
   in-substrate (ranked either/or forks; the elimination/SUPPOSE loop is its semantics),
   with the external solver demoted to an optional accelerator — the price, openly paid, is
   that a genuinely hard instance yields "couldn't solve within budget → UNKNOWN" plus a
   proof object. The remaining exit is the `<call>` seam for tools and arithmetic, which is
   the right boundary ("no seam except tools") — but the more business workloads lean on
   aggregation/temporal calls, the more computation lives on the wrong side of the abolished
   wall. Re-audit when a business-shaped bank lands.

## 5. Governance track record (why the discipline rating is earned)

For a reviewer calibrating how much to trust the self-assessments: this project has a
demonstrated record of killing its own work on principle, which is rare enough to be
evidence. Documented cases: in-substrate anaphora resolution — built, working, **backed
out** because reasoning was byte-identical with and without it (the feature bought nothing
structural; relocated to the boundary); demand-driven coreference — built, measured
*correct*, **abandoned** as 3–6× slower with the findings archived as the deliverable and
the branch deleted; full grammar reification — **cut** when its benefits decomposed to
things already delivered plus one capability the user ruled out; the external-solver home
for disjunction — **dropped** in favor of an honest in-substrate semantics that accepts
UNKNOWN on hard instances. Costs are measured and stated (+15% for always-on provenance;
the superlinear chain curve published in its own design doc). The risk this discipline does
not cover: it is one author's discipline, exercised on one author's code, with no external
reviewer yet.

## 6. Bottom line

A genuinely good research system whose distinctive strengths are *discipline* (§5) and one
architectural spike (§2.2) — and whose composition claim (§2.7: five capability layers,
zero new mechanisms, one substrate) is now its most defensible headline, ahead of any
individual mechanism. The intersection claim also stands: untyped edges + no-seam CNL +
graded possibilistic layer + demand-driven revision, held simultaneously in one store, has
no existing system holding all of it at once.

Two questions decide whether any of it matters beyond this repo, and they are unchanged in
kind: **can the substrate stay fast where its own use case stresses it (cross-bank
composition)**, and **can one non-author human actually author and audit a rule book in
it**. The first needs E4. The second needs E1, has needed it longest, is the cheapest to
run — the playground reduced it to sending a URL to a stranger — and currently blocks more
claims than anything else in the project. Run E1.

## 7. De-risking experiments

Tracked in **`design/validation_experiments.md`** — seven experiments (E1–E7), ordered by
information per unit of effort, each citing the claim in this document it tests. In one
line each: E1 stranger-authoring (habitability, §4.4 — **the highest-information action on
the board**); E2 audit head-to-head vs Drools/DMN (§3); E3 conflict-lint on a real rule
book (§3.4); E4 cross-bank composition at real scale (§4.1a); E5 performance cliff map
(§4.1); E6 decision-table ingestion as in-graph rules (homoiconicity, §2); E7 performance
feasibility spike (§4.1 — the ceiling question). Anti-recommendation: no more
ProofWriter-style benchmarks — they test coverage, which is already demonstrated, not
advantage.
