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
3. *The tight outer loop is the mechanism of one thought leading to another* (§7), with outcomes as
   positive facts (§8). Held: a rule that cannot match until another has fired becomes relevant on the
   next step, with no scheduler and no dependency analysis. `tests/units/test_loop.py`.

**Deliberately not built**, so results are not over-read: the boundary and the CNL transcriber (§9,
`cnl.md`), suspension and resume (§9 — `awaiting` is recorded but nothing services it), derivations and
deletions at write-back (§9), and attention (§7 — retrieval currently sees the whole world). System 1 is
a **crude stand-in**, not a decision (§13). Above all, **`cnl.md` §4's actual claim — that *rules* write
the wiring register during comprehension — is untested**: descriptions are hand-written, which is the
honest edge of the spike.

⚠ **One known gap is pinned rather than fixed**: conclusions accrete superlinearly across steps, because
every step re-mints them and duplicated premises multiply matches. See
`test_conclusions_accrete_superlinearly_across_steps`.

**NO-IMPORT RULE** (§12 invariant 10): this package must not import from `ugm/`. Enforced by
`tests/units/test_no_ugm_import.py`, not by good intentions.
"""
from .assemble import Assembly, assemble
from .band import SCALE, meet, weaker
from .circuit import Circuit, Fuel, Port, Run, SealBreach, Statement
from .describe import Description
from .graph import EMPTY, Graph, Node, named, occurrence, role_edge
from .loop import (AWAITING, OUT_OF_FUEL, SATISFIED, STARVED, STOPPED, StepResult, TurnResult,
                   goals, outcomes_of, settled, step, turn)
from .match import Match, Pat, atom, atoms, role, solve
from .recall import resemblance, vocabulary
from .unit import Emit, Miss, ScopePointer, Stamp, Same, Unit, rule, transform

__all__ = [
    "Assembly", "assemble", "Description",
    "step", "turn", "StepResult", "TurnResult", "goals", "outcomes_of", "settled",
    "SATISFIED", "STARVED", "OUT_OF_FUEL", "AWAITING", "STOPPED",
    "resemblance", "vocabulary",
    "SCALE", "meet", "weaker",
    "Circuit", "Fuel", "Port", "Run", "SealBreach", "Statement",
    "EMPTY", "Graph", "Node", "named", "occurrence", "role_edge",
    "Match", "Pat", "atom", "atoms", "role", "solve",
    "Emit", "Miss", "ScopePointer", "Stamp", "Same", "Unit", "rule", "transform",
]
