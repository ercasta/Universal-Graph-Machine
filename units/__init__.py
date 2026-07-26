"""units — computation units as the substrate (`docs/design/substrate_inversion.md`).

The inversion: UGM's `ugm/` package is a data-only substrate (a graph) with computation bolted on. Here
**computation units ARE the substrate**, each holding a whole subgraph as its state, wired dynamically so
that the KB and the discourse physically modify the topology. A graph is not the store; it is the value
flowing on a wire.

**NO-IMPORT RULE.** This package must not import from `ugm/`. Anything it needs is copied, and what gets
copied is then evidence about what is genuinely shared versus what was a store-shaped assumption riding
along. Enforced by `tests/units/test_no_ugm_import.py`, not by good intentions.

`ugm/` stays working and untouched. Nothing is retired until this substrate answers a real question end to
end — at which point deletion is the honest move ([[delete-old-code-aggressively]]), not archiving.
"""
from . import band, trace
from .fuel import Budget, Verdict
from .match import Absent, Triple, UnsafePattern, Var, solve
from .net import Net
from .trace import explain, render
from .vocab import FORMS, Vocabulary, role
from .unit import Unit, branch, given, rule
from .value import EMPTY, Fact, Node, Subgraph, mint

__all__ = [
    "Budget", "Verdict",
    "Absent", "Triple", "UnsafePattern", "Var", "solve",
    "Net",
    "band", "trace", "explain", "render",
    "Unit", "branch", "given", "rule",
    "EMPTY", "Fact", "Node", "Subgraph", "mint",
    "FORMS", "Vocabulary", "role",
]
