# 0039. Guards yes, kinds no — the uniformity principle and its price

**Status — current (2026-07-28): SURVIVES.** in force, and load-bearing. `../../model.md` §14.

**Status — as recorded:** Accepted
**Source:** user, 2026-07-26; and every defect record in this directory

## Context

The user's standing requirement is a **uniform substrate**, and the reason given is composition:

> *"The moment we start creating superstructures — and labelled edges are one — we incur the risk of getting
> into things that do not compose."*

And the user raised the counter-objection themselves: **a uniform substrate risks MERGING things that should
stay separate.** Both risks are real, and this project has instances of both.

## Decision

**Keep the substrate uniform. When a distinction is needed, make it a FACT and assert it — never a
new KIND of thing.**

> **Guards yes, kinds no.** A guard is a check over the uniform substrate, so it composes with everything. A
> kind is a thing every other mechanism must be taught about, and does not.

## Evidence

**The conflation risk is real, and this codebase has seven instances of it.** Every silent
assembler defect was one mechanism answering two different questions:

- `comparable` answered both *"is there a lineage"* and *"is this the same world"* (`0038`);
- the projection answered both *"may this instantiate"* and *"what identifies this offer"* (`0023`);
- predicate where **atom** was meant; positive where **both polarities** were meant; reachability where
  **world** was meant; *"my chain derives it"* where *"my chain carries it"* was meant.
- Still open: **`Absent` conflates *unknown* with *denied*** (`0011`).

**But the two risks are not symmetric, and that is what decides it:**

| | how it fails | how you find it | cost to fix |
|---|---|---|---|
| superstructure | the new mechanism **cannot reach** the old one | when you try to compose — too late | rewrite |
| uniform conflation | the mis-asked question returns a **well-typed answer** | only if you write the probe | one predicate, one atom, one changed test |

**Seven silent defects, three or four answer-changing, and every fix was small.** `comparable` grew a carrier
test; the projection split in two; the join moved from predicates to atoms. None was a rewrite and none
invalidated work already built.

> **A superstructure makes a distinction *unstatable* in the substrate. Uniformity makes it *statable but
> unstated*.** The second is recoverable; the first is not.

**And uniformity has repeatedly paid, not merely broken even.** Making the predicate slot uniform dissolved
three recorded problems at once (`0017`); inequality dissolved into a derived fact with no new operator
(`0027`); selector chains needed **no new code**, and gating, failure-location and ambiguity all came free by
reusing the reference rules unchanged (`0036`); the retraction apparatus dissolved (`0019`).

## Consequences

- **The price is specific and must be paid:** every distinction relied on has to be *stated in
  the data and checkable*. Where that was done it held — the trace/object separation is asserted by a test, the
  band lattice is finite by construction, pattern safety is checked at construction. Where it was not, it bit.
- **Probes are not optional.** A uniform substrate degrades quietly, so the standing practice is to spike to
  break rather than to demonstrate.
- The one deliberate exception is `0040`, and it ships with its own decomposition.
