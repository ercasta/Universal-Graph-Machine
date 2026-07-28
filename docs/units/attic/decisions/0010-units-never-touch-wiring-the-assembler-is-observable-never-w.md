# 0010. Units never touch wiring; the assembler is observable, never writable

**Status — current (2026-07-28): SURVIVES.** in force, as invariants 4 and 17. Amended: a wiring change is a mutating rule's conclusion applied at write-back.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §8, §20.4, §27

## Context

A dynamically-wired system cannot be statically checked, so introspection is the only safety
there is. The temptation is to let units reason about — and then modify — the topology.

## Decision

**Units never wire anything.** The assembler is fully *observable* (every decision, including every
refusal, is recorded as a fact — see `0029`) and never writable. An in-node ISA is deferred and an
assembler-level ISA is refused on this line, not on cost.

## Evidence

- `units/authoring.py` closes the loop from output to new computation and adds **zero wires** — the
  ordinary spawn policy still decides who feeds a derived template. Asserted behaviourally *and* by the absence
  of any `.wire(` call in the module.
- A rule over the journal can read *why* a wire exists exactly as it reads why a conclusion holds.

## Consequences

- **If routing must ever be learned**, the recorded safe shape is: units *propose* wirings as
  facts, and the assembler stays the only writer. A unit emits a proposal, never an edge.
- Deciding what *flows* on a wire is what every unit already does; deciding what wires *exist* is policy. These
  are different acts and only the second is behind this line.
