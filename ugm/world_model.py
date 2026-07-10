"""
The substrate — now the label-less `AttrGraph` (the re-host, `decision-attrgraph-rehost`).

This module used to define a name-based `Graph` (every node a NAME label + embedding +
confidence). As of the AttrGraph re-host it is a thin RE-EXPORT of the label-less substrate
`harneskills.isa.attrgraph.AttrGraph`, which absorbs the former `Graph` API as CONVENTIONS over
its attribute core (a former NAME is the reserved `name=` VALUED attr; a former CONFIDENCE the
`confidence=` attr; an embedding dim a GRADED attr). Every `from .world_model import Graph`
therefore transparently gets `AttrGraph`, so the whole system runs on ONE substrate while the
engine is migrated onto the ISA machine. The identity discipline is unchanged and stronger: a
node has an OPAQUE identity, names are non-unique (two "Paul"s stay two nids), and the lexical
`_by_name` index is a semantically-transparent MATCHING accelerator, never a value-as-identity
lookup. See `harneskills/isa/attrgraph.py` and `docs/handoff_attrgraph_rehost.md`.

`Graph`/`WorldModel`/`Node`/`_is_inert`/`_INERT_NAMES` are kept as names here so existing imports
keep resolving; the definitions live in `isa/attrgraph.py`.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, AttrNode, _INERT_NAMES, _is_inert

# The substrate is the label-less AttrGraph. These aliases keep every existing import resolving.
Graph = AttrGraph
WorldModel = AttrGraph
Node = AttrNode

__all__ = ["Graph", "WorldModel", "Node", "AttrGraph", "AttrNode", "_is_inert", "_INERT_NAMES"]
