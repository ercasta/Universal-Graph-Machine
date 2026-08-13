"""An agent that plans, acts, observes and explains itself, on one graph
substrate. The design is `docs/rules-design.md`; every module here cites it.

Slice one is the machine: channels, processes, frames and the gate, with basic
forward rules. Deliberately absent -- spans, shapes, backward reading, recall
learning, suppositions.
"""

from .chain import Chain, Entry, Moment, MINUS, PLUS, UNSURE
from .channels import Channels
from .gate import Frame, Gate
from .graph import Graph
from .machine import Machine, Step
from .rules import CAUSES, IMPLIES, Member, Rule, RuleSet

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
