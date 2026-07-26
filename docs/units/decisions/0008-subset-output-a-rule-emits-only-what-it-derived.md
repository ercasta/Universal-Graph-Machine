# 0008. Subset output — a rule emits only what it derived

**Status:** Accepted
**Source:** substrate_inversion.md §16 (user proposal), `bench/spike_subset_output.py`

## Context

Originally every unit passed its whole view through, so a rule's output contained its inputs'
predicates. Two guards had to be invented to contain the consequences, and the chain's natural guard — scope by
deactivation — was decorative, because a rule that matched nothing still passed everything on.

## Decision

**A rule emits only what it derived. Everything else emits its view.**

## Evidence

- **Cycles stop being the default.** Under accretion the assembler mistakes a consumer for a
  producer of its own premises and closes a loop; measured at 121 spawns and fuel exhausted, versus 2.
- **A non-firing unit becomes a real gate.** It emits nothing and downstream is genuinely starved — so
  bypassing a unit is a semantic change, not a shortcut, and that is now checkable.
- **Branch accretion survives**, which is what `0006` needs: a carrier passes its view through.

## Consequences

- The assembler must now actively **join** a multi-premise pattern, because one producer no
  longer carries everything (`0009`, `0023`).
- **Every "my chain has it" heuristic became wrong**, and two guards had to be re-derived: a unit was read as a
  bypass of itself, and facts a carrier never received were counted as facts it dropped (`0025`).
- Provenance can no longer ride the object wire, because a rule does not carry it (`0012`).
