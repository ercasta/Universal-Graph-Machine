"""units — the computation model of `docs/units/model.md`.

**Data is the substrate; computation is a transient circuit** built over it, used, and thrown away. The
graph persists; the network does not.

**Status: a spike.** What is here tests exactly one claim — the one the whole paradigm flip is justified
by: *the inner loop is a circuit, so no rule ever matches a scope.* Everything else is deliberately
stubbed. Not built: System 1 retrieval (§7), the outer loop and its budget (§8), the boundary and the CNL
transcriber (§9, `cnl.md`), write-back of derivations and deletions (§9), and the wiring register that
would let rules describe a chain instead of it being hand-assembled (`cnl.md` §4).

**NO-IMPORT RULE** (§12 invariant 10): this package must not import from `ugm/`. Enforced by
`tests/units/test_no_ugm_import.py`, not by good intentions.
"""
from .band import SCALE, meet, weaker
from .circuit import Circuit, Fuel, Port, Run, SealBreach, Statement
from .graph import EMPTY, Graph, Node, named, occurrence, role_edge
from .match import Match, Pat, atom, atoms, role, solve
from .unit import Emit, Miss, Unit, rule, transform

__all__ = [
    "SCALE", "meet", "weaker",
    "Circuit", "Fuel", "Port", "Run", "SealBreach", "Statement",
    "EMPTY", "Graph", "Node", "named", "occurrence", "role_edge",
    "Match", "Pat", "atom", "atoms", "role", "solve",
    "Emit", "Miss", "Unit", "rule", "transform",
]
