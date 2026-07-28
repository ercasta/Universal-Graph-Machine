# 0040. The fact layout is edge-labelled; the semantics are path-faithful

**Status — current (2026-07-28): REPLACED.** `../../model.md` §3 — role nodes, not edge labels or positions.

**Status — as recorded:** Accepted — a deliberate, single exception to 0039
**Source:** user question, 2026-07-26; `units/value.py`

## Context

An earlier decision in this project rejected role-labelled (Davidsonian) edges: S-P-O is a
directed **path**, and direction carries the roles. The user asked directly whether `units/` had drifted from
that. It partly has, and the honest answer is worth recording rather than defending.

## Decision

**`Fact(s, p, o)` is stored ATOMICALLY** — a 3-tuple, not two adjacency links through an
intermediate node. Drawn on a whiteboard it is a labelled edge. **This is kept**, deliberately, and it is the
only such exception.

What survives of the original decision, in full:

- roles are carried by **position** — `s` and `o` are told apart by where they sit;
- the predicate is an **ordinary node** (`0017`), so there is no separate label namespace and `?p` is a plain
  variable;
- nothing hangs role-labelled edges on a fact about the world.

## Evidence

**The trade is for DECIDABILITY, and it is the one thing the whole design leans on.** A fact is a
single set member, so `Absent` is a **membership test** — exact, immediate, no fuel (`0011`). As a traversable
2-path, *"is P absent"* becomes *"is there no 2-path"*, which is a join, and the cheap exact negation would be
gone. Value equality and hashing are trivial for the same reason, and the fixpoint depends on that (`0004`).

**And the exception ships with its decomposition:** the inside of a fact is reachable as ordinary facts through
`reify` (`<of_s>/<of_p>/<of_o>`) whenever anything needs to compose with it. That escape hatch is what stops
this being the unreachable island `0039` warns about.

An earlier docstring claimed *"S-P-O as a directed path survives unchanged"*. That was too generous and has
been corrected in place.

## Consequences

- **The rule for any future exception:** if you break uniformity, ship the decomposition with
  it. Without the escape hatch this would be exactly the superstructure the principle forbids.
- A fact cannot be traversed as a path, so anything that must walk into a fact goes through reification. That is
  a real cost and it is small, because reification is idempotent and its handle is a pure function (`0015`).
