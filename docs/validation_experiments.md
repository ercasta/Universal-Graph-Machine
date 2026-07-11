# Validation Experiments — discovering the real value and risks, fast

> **Status: PROPOSED PLAN (2026-07-11, drafted by the assistant, not yet ratified).**
> Companion to `critique.md` (which argues WHY these are the right experiments — see its §3
> value proposition and §4 weaknesses; each experiment below cites the claim it tests).
> Ordering principle: **test the value claims (cheap, decisive, human-facing) before the
> feasibility claims (expensive, gradual)** — and run nothing that only re-demonstrates
> fragment coverage, which the in-repo suite already proves.

## The scoreboard

| # | Experiment | Claim tested (critique ref) | Cost | Decisive? |
|---|---|---|---|---|
| E1 | Stranger-authoring session | Habitability / SLM boundary (§4.4) | an afternoon, no code | yes — pass/fail on first contact |
| E2 | Audit head-to-head vs Drools/DMN | Faithful-explanation value prop (§3) | days | yes — third-party judgment |
| E3 | Conflict-lint on a real rule book | The Amendment-2 wedge (§3.3) | days + lint must exist | yes — count of real conflicts found |
| E4 | Cross-bank composition (candy shop × spec-writing) | Conventions-hold-everywhere (§4.2) | days–week | partially — yields a collision log |
| E5 | Performance cliff map | Performance risk, today's severity (§4.1) | a day, measurement only | calibrating, not pass/fail |
| E6 | Decision-table ingestion as in-graph rules | Homoiconicity payoff (§2) | days | yes — natural vs. fights-the-substrate |
| E7 | Performance feasibility spike | Performance risk, ceiling (§4.1) | ~a week, vertical prototype | yes — bounds the achievable speedup |

Recommended order: E1 → E5 (cheap calibration, tells you who E2 can be run with) → E2 →
E7 (if E5 says the cliff is close) → E4 → E3/E6 as the lint and Phase-3 authoring mature.

**On the performance risk specifically:** E5 and E7 split it deliberately. E5 answers *"how
bad is it right now"* (a measurement, one day, no design decisions). E7 answers *"is the
ceiling high enough"* (a feasibility bound on Phase 7's whole thesis) — because the critique's
§4.1 worry is not that the Python engine is slow (it certainly is), but that the substrate's
defining commitments (untyped edges, reified relations, graded attributes) might cap what ANY
implementation can reach, or that reaching it turns the AOT compiler into the de facto system.
Running E5 without E7 risks a false calm: a tolerable cliff today says nothing about whether
real workloads (E2's policy, E4's composed banks) stay on the good side of it.

---

## E1 — Stranger-authoring session (the habitability test)

**Tests:** the business-rules thesis's core premise and the load-bearing, deferred SLM/CNL
boundary (`critique.md` §4.4). Controlled languages historically die here — the
*habitability problem*: users cannot stay inside the fragment, and the frustration lands on
the first sentence, not the hundredth.

**Setup.** One non-author — ideally business-shaped, not a programmer — writes a small rule
book (a shop return policy, a discount scheme with exceptions) in CNL, with the linter,
**without the author in the room**. Record:

- every rejected sentence, and whether the named rejection redirected or frustrated;
- time to first working rule, and to a working 10-rule book;
- where they gave up or asked for help.

**Decides.** Whether the fragment boundary "feels like a feature" (the `logic_fragment.md`
authoring contract) or reproduces ACE's habitability failure. A failure here reprioritizes
everything: it says the linter's named-rejection contract and the prose sugar backlog are the
critical path, not the firmware.

## E2 — Audit head-to-head against Drools or DMN

**Tests:** the strongest value proposition directly (`critique.md` §3): explanations faithful
by construction, and honest negative answers.

**Setup.** One realistic layered policy (loan approval, discount stacking) implemented twice:
here and in Drools or DMN. Give both systems' answers **and explanations** for ~10 cases to a
third party; ask which they can verify and which they would sign off on. Include at least two
*negative* answers, to test whether "assumed no — here is where I looked within budget"
actually earns trust or reads as hedging.

**Decides.** Whether faithful CNL explanation is a real advantage or a nicety. This is the
experiment that turns the §3 value proposition from inference into measurement.

## E3 — Conflict-lint on a real, messy, public rule book

**Tests:** the `logic_fragment.md` Amendment-2 wedge — "beats Drools' silent salience and
formal logic's halt" on layered exceptions whose priority order was never stated.

**Setup.** Author a genuinely messy public policy (airline baggage rules, university
admission criteria, a municipal permit scheme) and count how many **real**
undeclared-priority conflicts the lint surfaces that the source document never resolved.

**Decides.** If it finds real ones, that is a demo-able moment no competitor has. If it finds
none, or only noise, the wedge claim weakens. **Prerequisite:** the conflict-lint must exist —
`consistency_design.md` is still a plan; this experiment is the reason to prioritize it.

## E4 — Cross-bank composition (candy shop × spec-writing)

**Tests:** the "conventions hold everywhere" claim (`critique.md` §4.2) and the one-substrate
composition story — the claims **no single-domain bench can touch**, because convention
collision (predicate vocabulary drift, coref conventions, normalization-tax mismatches) only
appears between *independently authored* banks.

**The idea (user, 2026-07-11).** Author rules for domain A (running a candy shop) and rules
for craft B (writing software specifications — or even Python code), then combine them to
generate a specification (or code) for a sample candy shop.

**Sharpened protocol.**

1. **Split composition from generation** — they are different risks, and a conflated failure
   is uninterpretable. Run the composition half first: a spec-writing bank whose rules are
   *about* specifications ("every priced item requires a pricing rule", "every process names
   an owner", "every irreversible action requires a confirmation step") applied to candy-shop
   facts, deriving **spec-item facts**. That is squarely inside the Horn+deontic fragment,
   and the output document is the provenance journal rendered — the system's home turf.
2. **Drop Python code generation as a first target.** Code has non-local syntactic and
   semantic constraints far outside the fragment; rules deriving code would really be
   templating, and a failure would say nothing about the substrate. The in-vision version:
   rules derive the *decisions* (entities, invariants, obligations), and the SLM/tool `<call>`
   seam renders them to code — which usefully doubles as a test of the tools boundary.
3. **Keep it honest:** the two banks must be authored in **separate sessions with no peeking
   at each other's vocabulary** — ideally by separate people, which merges this with E1.

**Decides / the real deliverable:** the **collision log** — how much bridging/normalization
was needed to make the banks compose, and whether the lint caught the mismatches or they
surfaced as silent non-matches. A smooth composition is evidence *for* the untyped substrate;
a pile of silent non-matches is the §4.2 fragility made concrete, and tells you what the
linter must learn to catch.

## E5 — Performance cliff map (before Phase 7, not as part of it)

**Tests:** how much of the performance risk (`critique.md` §4.1) is already biting — whether
Phase 7 is urgent or existential.

**Setup.** No optimization work; **measurement only**. The deployment model is an
**interactive session** — user utterances in CNL arriving one at a time, each adding to a
live KB — so the metric that matters is **per-utterance latency at KB size N** (tokenize +
form-recognition + incremental saturate + answer), NOT batch load+saturate throughput.
Measure the latency curve as the KB grows utterance by utterance (synthetic chains/joins plus
the largest available real bank), on the current Python engine. Find the knee where the
session stops feeling interactive (~1s per utterance is a reasonable line).

**Decides.** Whether the honest pitch today is "thousands of facts" or "hundreds" — which
determines which users E1/E2 can even be run with, and how loudly the Phase-7 clock is
ticking. Also reveals whether incremental cost is genuinely delta-driven (the semi-naive
`<fresh>` machinery doing its job) or secretly rescans — a per-utterance latency that grows
with total KB size rather than with the utterance's consequences is the failure signature.

## E6 — Homoiconicity payoff: decision-table ingestion as in-graph rules

**Tests:** whether rules-that-write-rules earns its keep — the vision-§2 claim that
self-modification is "ordinary graph rewriting", so far unexercised by any real task.

**Setup.** Implement the `logic_fragment.md` authoring consequence — decision-table rows
lower mechanically to Horn+priority rules — as **form rules in the graph**, not Python. This
is the smallest real task that exercises rule-writing-rules end to end, and it is
independently useful (the DMN lesson: tables are the natural bulk-authoring form).

**Decides.** If it is natural, the homoiconicity claim has its first working payoff. If it
fights the substrate, the quote/eval wall deferred in Phase 3 is closer to load-bearing than
the plan assumes.

## E7 — Performance feasibility spike (the ceiling, not the cliff)

**Tests:** the deep half of the performance risk (`critique.md` §4.1): whether the
substrate's defining commitments cap what any implementation can reach, and whether reaching
competitive speed forfeits the "no seam" claim. E5 measures where today's engine dies; E7
bounds where an optimized one could live.

**Setup.** A *vertical* prototype, not a rewrite — one week, one kernel, throwaway code:

1. Profile the current engine on E5's worst realistic workload; identify the hot kernel
   (expectation: `run_bank`'s seed + join loop).
2. Prototype exactly Phase 7(a) for that kernel only — interned keys/values to ints, CSR
   adjacency, bitset candidate sets — in isolation (a micro-benchmark harness is fine;
   differential-gate its answers against the real engine on the same inputs).
3. Separately, hand-write the AOT-compiled form of ONE hot rule (Phase 7(c), Soufflé-style
   partial evaluation of APPLY, done manually) and measure it against the interpreted APPLY
   on the same graph.

**The interactive constraint (user, 2026-07-11).** The system runs in interactive sessions:
CNL utterances continuously add facts AND rules to a live KB, so there is **no offline
compilation phase before usage**. Consequences for this spike:

- Whole-program Soufflé-style AOT is off the table as the primary path. The plan's Phase 7(d)
  already anticipates the right shape — **two-tier execution**: fresh rules interpret
  immediately (zero-latency availability), stable-hot rules compile in the background with
  version-stamp invalidation. E7 should validate that tier split, not a batch compiler.
- The relevant literature comparison shifts from batch Datalog (Soufflé) to **incremental
  engines**: Rete-family (whose entire point is incremental matching), RDFox's incremental
  maintenance, and differential-dataflow Datalog (DDlog). The substrate's semi-naive
  `<fresh>` delta is already the right primitive; the question is its constant factor.
- Step 3 below therefore measures the compiled rule's *background* compilation cost and
  hot-swap correctness (differential gate on swap), not just its steady-state speed.

**Reference points to beat or explain:** Soufflé and RDFox get their speed from typed
schemas, specialized joins, and columnar layouts — the seams this substrate abolished. The
reified-relation shape costs ~3× nodes, but the real question is join dispatch: whether the
graded-key index (`nodes_with_key`) can approximate a typed store's O(1) predicate dispatch
once interned, and whether graded/valued attributes break the bitset tricks or merely dilute
them. Note the interactive setting *softens* the bar, too: the engine must beat "a human
reads the answer" (sub-second on a session-sized KB), not RDFox on a billion triples —
E5 tells you how far today's engine is from that gentler bar.

**Decides.** Three outcomes, all informative:

- **Interning+CSR alone gives 1–2 orders of magnitude** → the risk is engineering, not
  architecture; Phase 7 proceeds as planned and the vision's claims stand.
- **Only the AOT-compiled rule is competitive** → the compiler becomes the real system and
  "no seam" survives only as reference semantics — the §4.1 outcome to have decided about
  *in advance*. Better to learn this from one week and one rule than after Phase 7(a)+(b).
- **Neither closes the gap** on realistic joins → the substrate commitments themselves are
  the bottleneck, and the honest scope becomes "small, auditable rule books" (which E1–E3
  may show is a perfectly good product) rather than "fast general reasoner."

---

## What NOT to run

More ProofWriter-style logic benchmarks. They are saturated (fine-tuned transformers
effectively solved them in 2021), they test the fragment's *coverage* — already demonstrated
by the in-repo suite — and every hour spent there is an hour not spent on E1–E3, which test
the claims that actually differentiate the system: authoring, audit, explanation.
