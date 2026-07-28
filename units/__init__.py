"""`units` — the standing-circuit model.

Implements `docs/units/model.md` as revised by `revision-01-standing-circuits.md` and
`revision-02-two-planes.md`.

Five modules, and that is the whole system:

| | |
|---|---|
| `graph` | nameless nodes, directed nameless edges, crisp and gradable attributes. Immutable |
| `band` | the finite degree scale and its meet |
| `match` | graded matching of topology and attributes; nothing matches by name implicitly |
| `overlay` | what a unit's output *is* — revertable mutations, composed lazily at read time |
| `engine` | standing units, wiring, gate energy, the revive, and write-back |

**Consolidated 2026-07-27.** Three partial machines had accumulated while the design converged —
`standing.py` (propagating, but reading by unioning graph fragments, with `Cell.within`/`Cell.scope`
containment), `overlay.py` driven directly with no units, and `turn.py` (fixpoint iteration, no
matching). They did not compose. `engine.py` is the one machine; the other two are deleted.

What the consolidation joined, beyond removing the fork:

| | |
|---|---|
| **scope is support** | `revision-02` §3 had both halves built and never connected: `overlay.py` took a configuration as *declared*, `standing.py` computed one by *walking wiring*. `Network.powering()` now computes it and the read uses it |
| **a unit needs no configuration** | it sees only what its gates delivered, and a supposition reaches exactly what is wired downstream of it. Scope is not read — it is wiring |
| **the matcher reads through overlays** | `match.solve()` needed no change: `Overlays.view()` exposes the same four members `Graph` does |
| `Cell.within`, `Cell.scope` | **deleted.** Containment was a second axis of *position*, where scope is support |
| `Value.graph` + `merges` | **deleted.** A value carries *effects*; the side channel existed only because `Merge` did not fit the fragment |
| `Value.path` | **deleted.** Energy lives at the gate, as a count of input changes |

**The one asymmetry to keep in mind.** Everything a computation unit does is a **revertable mutation** —
minting a node, adding an edge, setting an attribute, identifying two nodes, removing something. It
stands while its unit is powered and is gone when it is not. Only a **mutating rule** reaches the
asserted layer, and only at write-back. That asymmetry is what makes hypothesis exploration safe with no
checkpoint, no copy and no merge-back.

**NO-IMPORT RULE** (`model.md` §12 invariant 10): this package must not import from `ugm/`. Enforced by
`tests/units/test_no_ugm_import.py`, not by good intentions.
"""
from .band import CERTAIN, SCALE, THETA, at_least, meet, weaker
from .engine import (ENGINE, SILENCED, SURGE_AT, SURGED, Attribute, Cell, Drop, Emit, Link, Merge,
                     Network, StandingUnit, Stamp, Surge, Value, bundled_silence_rule, effects_of,
                     instantiate, instantiate_all, read_effect, read_pattern, write_effect,
                     write_pattern)
from .graph import EMPTY, Graph, Node, named, occurrence, role_edge
from .match import Absent, AttrVar, Match, Pat, absent, atom, atoms, role, solve
from .overlay import (AddEdge, Conflict, Grade, Identify, Mint, Overlays, Reading, Retract, SetAttr,
                      View)

__all__ = [
    "EMPTY", "Graph", "Node", "named", "occurrence", "role_edge",
    "SCALE", "CERTAIN", "THETA", "at_least", "meet", "weaker",
    "Absent", "AttrVar", "Match", "Pat", "absent", "atom", "atoms", "role", "solve",
    # overlay — what a unit's output is
    "Mint", "AddEdge", "SetAttr", "Grade", "Identify", "Retract",
    "Overlays", "View", "Reading", "Conflict",
    # engine — the circuit
    "Cell", "Network", "StandingUnit", "Surge", "Value", "effects_of",
    "instantiate", "instantiate_all", "read_pattern", "write_pattern",
    "read_effect", "write_effect",
    "Emit", "Attribute", "Stamp", "Link", "Merge", "Drop",
    "bundled_silence_rule", "SURGE_AT", "SILENCED", "SURGED", "ENGINE",
]
