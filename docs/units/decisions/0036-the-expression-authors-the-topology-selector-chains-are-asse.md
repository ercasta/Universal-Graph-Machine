# 0036. The expression authors the topology; selector chains are assemblable

**Status:** Accepted
**Source:** substrate_inversion.md §31; `bench/spike_selector_chain.py` (21/21)

## Context

`0025` established that a pattern which declines to say what it reads cannot have its topology
inferred and must be authored. The open question was *by what*. The user's proposal: by the expression — the
syntactic nesting **is** the wiring, terminating in a tool call.

## Decision

**One unit per syntactic position, chained by the referent, terminating in a call request.** The
parse contributes ground **step nodes** and `<narrows>` links **as facts** — data, never wires.

## Evidence

- **The assembler wired all of it by itself.** Every selector received its predecessor *and* a
  world-carrying producer, with no authored merge and no hand wiring, because **every selector atom names its
  predicate.** That is the exact contrast with a wildcard rule.
- **The contrast is not an artifact of `0038`.** Re-measured after that fix: coreference substitution *still*
  needs an authored merge. The two obstructions have different causes — one is about what satisfies an atom, the
  other was about which units may be joined.
- **It is a TREE, not postfix.** *"the car and the truck that are parked at ⟨s3⟩"* gives one step with two
  consumers. "Postfix" would have implied a linear stack and foreclosed conjunction.
- **Gating, failure-location and ambiguity all come free**, and reuse `0027`/`0028`'s shapes exactly: a
  non-firing selector starves the chain; `<unresolved>` names *where* reference failed; `<step_ambiguous>` names
  the step with two referents and only that step. **Nothing new was required** — strong evidence that reference
  and selection are one problem, not two.
- **⚠ Surface-sensitivity does not leak into belief.** Permuting a selector's atoms gives the identical referent;
  only *re-attachment* changes meaning, because the chain **is** the attachment structure. So: **the expression
  fixes the topology, the topology computes a referent, and the referent is what is believed.**

## Consequences

- `0010`'s line is untouched: the expression supplies data, and the ordinary spawn policy does
  the wiring. Nothing gained the power to wire.
- **A grammar now has a concrete target** — ground step nodes, `<narrows>` links, one template per syntactic
  position — which is what `0020`'s contract was pinned for.
- The terminal call is a **request, as a fact**. Nothing executes it: suspend is not built, and building it
  reopens `0021` on its stated trigger.
- The duality is a **reflection, not an isomorphism**: instance identity carries scope and has no graph
  counterpart, so many networks produce one graph. The mirror is writable in one direction only.
