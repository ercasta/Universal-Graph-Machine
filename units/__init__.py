"""units — the computation model of `docs/units/model.md`.

**Data is the substrate; computation is a transient circuit** built over it, used, and thrown away. The
graph persists; the network does not.

**Status: a spike.** Two claims are tested, both load-bearing:

1. *The inner loop is a circuit, so no rule ever matches a scope* (§6) — the one difference the whole
   paradigm flip is justified by. Held, including two sibling hypotheses in one circuit with no
   world-comparability apparatus. `tests/units/test_tunnel.py`.
2. *The assembler wires only what is described in data, and never unrolls* (§11, `cnl.md` §4). Held: the
   same scenario assembles from a `Description` graph and the decoded pattern is **equal** to the
   hand-written one. `tests/units/test_described_assembly.py`.

**Deliberately not built**, so results are not over-read: System 1 retrieval (§7), the outer loop and its
budget (§7, §8), the four outcome facts on goals (§8), the boundary and the CNL transcriber (§9,
`cnl.md`), and write-back of derivations and deletions (§9). Above all, **`cnl.md` §4's actual claim —
that *rules* write the wiring register during comprehension — is untested**: the descriptions here are
hand-written, which is the honest edge of the spike.

**NO-IMPORT RULE** (§12 invariant 10): this package must not import from `ugm/`. Enforced by
`tests/units/test_no_ugm_import.py`, not by good intentions.
"""
from .assemble import Assembly, assemble
from .band import SCALE, meet, weaker
from .circuit import Circuit, Fuel, Port, Run, SealBreach, Statement
from .describe import Description
from .graph import EMPTY, Graph, Node, named, occurrence, role_edge
from .match import Match, Pat, atom, atoms, role, solve
from .unit import Emit, Miss, Stamp, Unit, rule, transform

__all__ = [
    "Assembly", "assemble", "Description",
    "SCALE", "meet", "weaker",
    "Circuit", "Fuel", "Port", "Run", "SealBreach", "Statement",
    "EMPTY", "Graph", "Node", "named", "occurrence", "role_edge",
    "Match", "Pat", "atom", "atoms", "role", "solve",
    "Emit", "Miss", "Stamp", "Unit", "rule", "transform",
]
