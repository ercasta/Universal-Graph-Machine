"""An agent that reasons on one graph substrate. The design is
`docs/rules-design.md`; every module here cites it. `docs/guide.md` is the
practical one: how to write a corpus and run it.

There is ONE graph and it is the state -- a scratchpad. What the agent believes
is what is anchored in it right now; a retraction is a deletion rather than a
later claim that outvotes an earlier one, and nothing anywhere remembers what
was believed before. That is the whole architecture, and most of what used to
be here went with the chain it replaced: entries, moments, signs, licences,
support trails, goal management, vetoes, expectations, the premise economy, and
credit assignment.

The engine is `ugm.core`; nothing outside it is needed to run an agent.
`ugm.gates` are release criteria and `ugm.probes` are measured questions.
Learning is deliberately absent, and will come back on a memory system rather
than on a history the engine keeps by accident.
"""

from .core.channels import Channels
from .core.gate import Gate
from .core.graph import Graph
from .core.machine import Machine, Step
from .core.rules import ABSENT, ASSERT, ERASE, IMPLIES, Member, Rule, RuleSet
from .core.scratchpad import Scratchpad

__all__ = [
    "Channels",
    "Gate",
    "Graph",
    "Machine",
    "Member",
    "Rule",
    "RuleSet",
    "Scratchpad",
    "Step",
    "ABSENT",
    "ASSERT",
    "ERASE",
    "IMPLIES",
]
