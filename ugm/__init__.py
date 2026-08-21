"""An agent that plans, acts, observes and explains itself, on one graph
substrate. The design is `docs/rules-design.md`; every module here cites it.
`docs/guide.md` is the practical one: how to write a corpus and run it.

⚠ This docstring used to end *deliberately absent -- spans, shapes, backward
reading, recall learning, suppositions*, which described a first slice and
outlived it by a long way: all of those were built except spans, which were
built and then REMOVED with the locus. A roadmap in a package docstring is a
claim that goes stale in one direction only.

The engine is `ugm.core`; nothing outside it is needed to run an agent.
`ugm.gates` are release criteria, `ugm.probes` are measured questions, and
`ugm.learning` is what an episode teaches the next one.
"""

from .core.chain import Chain, Entry, Moment, MINUS, PLUS, UNSURE
from .core.channels import Channels
from .core.gate import Gate
from .core.graph import Graph
from .core.machine import Machine, Step
from .core.rules import CAUSES, IMPLIES, Member, Rule, RuleSet

__all__ = [
    "Chain",
    "Channels",
    "Entry",
    "Gate",
    "Graph",
    "Machine",
    "Member",
    "Moment",
    "Rule",
    "RuleSet",
    "Step",
    "CAUSES",
    "IMPLIES",
    "PLUS",
    "MINUS",
    "UNSURE",
]
