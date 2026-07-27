"""`units` — the standing-circuit model.

Implements `docs/units/model.md` as revised by `docs/units/revision-01-standing-circuits.md`.

Four modules, and that is the whole system:

| | |
|---|---|
| `graph` | nameless nodes, directed nameless edges, crisp and gradable attributes. Immutable |
| `band` | the finite degree scale and its meet |
| `match` | graded matching of topology and attributes; nothing matches by name implicitly |
| `standing` | contributions, standing units, wiring, and the revive |

**What was deleted on 2026-07-27, and why.** The previous engine — an assembler, a per-step circuit, a
demand loop, a visibility projection, a scope pointer and a cooldown table — is gone. Every one of those
mechanisms existed to answer a question that standing circuits answer structurally:

| deleted | replaced by |
|---|---|
| `assemble.py`, `circuit.py` | units stand; nothing is rebuilt per step |
| `loop.py` | `Network.revive()` — fire from the axioms, stabilize |
| `graph.visible_at` | a unit sees only what is wired to its gates |
| `unit.ScopePointer` | a contribution is attributed to the unit that made it |
| `cooldown.py` | nothing accretes, so nothing needs suppressing |
| `recall.py`, `describe.py` | retrieval is unbuilt under the new model |

**The one asymmetry to keep in mind.** Everything a unit does is a **revertable mutation of the graph** —
minting a node, adding an edge, setting an attribute, merging two nodes. It stands while its unit is
powered and is gone when it is not. Only the boundary writes the asserted layer, and only with what came
from outside. That asymmetry is what makes hypothesis exploration safe with no checkpoint, no copy and
no merge-back.

**NO-IMPORT RULE** (`model.md` §12 invariant 10): this package must not import from `ugm/`. Enforced by
`tests/units/test_no_ugm_import.py`, not by good intentions.
"""
from .band import CERTAIN, SCALE, THETA, at_least, meet, weaker
from .graph import EMPTY, Graph, Node, named, occurrence, role_edge
from .match import Absent, AttrVar, Match, Pat, absent, atom, atoms, role, solve
from .standing import (SURGE_AT, Cell, Emit, Link, Merge, Network, Overlay, Same, StandingUnit,
                       Stamp, Surge, Value, holds)

__all__ = [
    "EMPTY", "Graph", "Node", "named", "occurrence", "role_edge",
    "SCALE", "CERTAIN", "THETA", "at_least", "meet", "weaker",
    "Absent", "AttrVar", "Match", "Pat", "absent", "atom", "atoms", "role", "solve",
    "Cell", "Network", "StandingUnit", "Surge", "Value", "SURGE_AT", "holds",
    "Emit", "Stamp", "Same", "Overlay", "Link", "Merge",
]
