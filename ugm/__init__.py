"""An agent that plans, acts, observes and explains itself, on one graph
substrate. The design is `docs/rules-design.md`; every module here cites it.

Slice one is the machine: channels, processes, frames and the gate, with basic
forward rules. Deliberately absent -- spans, shapes, backward reading, recall
learning, suppositions.
"""

from .core.chain import Chain, Entry, Moment, MINUS, PLUS, UNSURE
from .core.channels import Channels
from .core.gate import Frame, Gate
from .core.graph import Graph
from .core.machine import Machine, Step
from .core.rules import CAUSES, IMPLIES, Member, Rule, RuleSet

__all__ = [
    "Chain",
    "Channels",
    "Entry",
    "Frame",
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
