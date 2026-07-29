# Glossary — terms actually agreed on, in plain language

**Status: living document, 2026-07-28.** Only terms that have actually come up and been explained in
conversation go here — this is not a bulk import of every word in the codebase. (`docs/reference/glossary.md`
is a different, older file for the retired engine — not this one.) Add a term here when it's been discussed and
you want to reuse it going forward; don't introduce a term casually before it's here.

---

- **closed class / open class** — the small, fixed set of building blocks the engine understands exactly
  (negation, degree, conditionals, roles like `agent:`) vs. the unbounded, ordinary vocabulary (nouns, verbs —
  "customer," "park") that the engine treats as an opaque name and never tries to define.

- **form** — one entry in the closed class — e.g. "negation" or "degree." Each form specifies what licenses
  writing it, what can be concluded from it, and what it must never allow to be concluded.

- **introduction rule / elimination rule (intro / elim)** — the two halves of a form. The introduction rule is
  what has to be true for you to be allowed to write the form down. The elimination rule is what you're allowed
  to conclude once it's there. A form should never have one without the other.

- **LHS / pattern / match conditions** — the conditions a rule checks before it's allowed to fire — literally
  what the rule is looking for in the graph. "Guard" (below) just means adding more conditions to this.

- **guard / guarded vs. naive** — a **guard** is an extra condition added to a rule's match conditions so it
  doesn't fire in cases it shouldn't. **Naive** means a rule only checks its own condition; **guarded** means it
  additionally checks a few specific other conditions (which force, which level, etc.) before firing. Guarding
  only protects against the specific things it was written to check — it doesn't automatically protect against
  everything.

- **harmony** — the idea that a form's introduction rule and elimination rule should match each other exactly:
  the elimination shouldn't let you conclude more than the introduction actually earned.

- **leak** — a rule concluding something it should never be allowed to conclude, once combined with another
  rule. Each is individually fine; put together, they produce a wrong result.

- **inert** — the opposite failure: a rule that's technically fine but doesn't conclude anything useful — it
  went silent instead of leaking. Not a success — just a different way of hiding a problem.

- **slot** — a group of forms that compete with each other (only one can hold at a time), discovered by testing
  which forms refuse to coexist, rather than by just declaring "these are the same category."

- **the sieve (`sieve.py`)** — a script that builds many combinations of forms, actually runs them through the
  real engine, and checks whether anything leaked. Its four results: **PASS** (composed correctly and concluded
  something new), **INERT** (nothing new, no leak), **REFUSED** (the forms correctly can't coexist), **LEAK**
  (something got concluded that should have been forbidden).

- **wire / unit / gate** — how the engine wires computations together. A **unit** is one standing rule/computation.
  A **wire** connects one unit's output to another's input. Units communicate only through wires, never by
  reaching into shared storage directly.

- **supposition / support** — a supposition is a hypothesis the engine is reasoning under ("suppose it rains").
  Anything concluded while that hypothesis is active carries that hypothesis as its **support** — a record of
  which assumption it depends on, so it can be kept separate from things known outright.

- **discharge** — the step, in ordinary logical reasoning, of taking something proven true *under* a hypothesis
  and turning it into an unconditional statement ("if it rains, I get wet") that no longer depends on the
  hypothesis actually being true. Currently has no working mechanism in this engine (`cnl_engine_goal_plan.md` §3).

- **SMT solver / Z3** — a program that takes a logical statement with unknowns in it (e.g. "is there a way to
  make X true and Y false at the same time?") and either finds a concrete example that satisfies it, or proves
  no such example exists. Z3 is the specific solver being used.

- **symbolic** — using a variable to stand for "any possible value," rather than picking one concrete value to
  test. E.g. instead of testing "polarity = negative" as one specific case, leave `polarity` as an unknown and
  ask the solver whether *any* value of it causes a problem — this is what lets one query stand in for testing
  every possible case at once.

- **SAT / UNSAT** — the solver's answer. **SAT** ("satisfiable") means yes, it found a concrete example where
  the statement holds — for us, that example is a leak. **UNSAT** ("unsatisfiable") means it proved no such
  example exists anywhere in the space it searched — for us, a proof that no leak is possible, not just "we
  didn't find one."

- **witness / model** — when the solver says SAT, it also hands back the actual concrete values that made it
  true — e.g. "polarity=negative, has_degree=true." That's the witness: a concrete leaking case, found by the
  solver rather than by us guessing it.

- **CONTENT / FORCE / LEVEL (the three axes)** — every form is classified along three independent questions.
  **CONTENT** asks *what is being claimed* — the payload itself (e.g. "the customer spent over $500," negated or
  not, to some degree). **FORCE** asks *what is being done with that claim* — asserting it, asking it,
  commanding it, denying it. The same content can carry different force: "you spent over $500" (assert) vs. "did
  you spend over $500?" (ask) share identical CONTENT but differ in FORCE. **LEVEL** asks *what the claim is
  about* — an ordinary fact about the world, or a claim about another claim/rule (e.g. "that rule is wrong" is
  LEVEL = language, not world). A "category" like negation or a question is a *point* in this three-way space,
  not a separate kind of thing.

- **field** — one concrete attribute a form writes onto a claim when it's used — e.g. `polarity` (written by
  `positive`/`negation`) or `strength` (written by `degree`). Two forms **compete** (occupy the same slot) when
  they write the same field; they can coexist when they write different fields.

- **SEED / CANDIDATES** — `SEED` is the small set of forms already trusted and locked in (the confirmed baseline
  the rest of the inventory is checked against). `CANDIDATES` is the larger, still-being-tested set that includes
  `SEED` plus every form proposed since — some confirmed, some still open hypotheses. A form graduates from
  `CANDIDATES` to `SEED` once the sieve has actually tested it.

- **bare vs. relational form** — a **bare** form decorates a single claim on its own (e.g. `negation`, `degree` —
  nothing else needs to exist for them to apply). A **relational** form links *two* occurrences together (e.g.
  `conditional` connects a hypothesis to its consequence) — it can't be checked by looking at one claim in
  isolation, and needs its own machinery to test.

- **tier 0 / tier 3** — a rough scale of how fundamental a piece of the system is. Tier 0 is the wiring
  substrate everything else runs on. Tier 3 (thematic roles — agent/patient/etc.) is corpus-derived surface
  detail, deliberately kept out of the closed-class sieve described in this document.
