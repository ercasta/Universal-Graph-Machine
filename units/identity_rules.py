"""CROSS-STATEMENT IDENTITY — the narrow, first-cut version of the mechanism
`units/identity_merge_probe_experiment.py` already validated, applied to a real, load-bearing need rather
than a probe scenario.

**The gap this closes.** `units/cnl.py` mints a fresh node per bare word per statement — correctly,
per `cnl.md` §1's create-never-merge — so two separate utterances mentioning "production_database" produce
two distinct nodes. Nothing merges them automatically, and nothing should: `cnl.md` §3 is explicit that
*"within a statement, identity is syntax [`x/`/`x`]; across statements, identity is a graded rule
decision."* This is that rule, for the simplest possible case.

**Scoped deliberately narrower than `identity_merge_probe_experiment.py`'s own generic version.** That
probe quantified over *both* concept kind and key value via two `AttrVar`s, because it needed to merge
several different kinds of record (customers on `ssn`, orders on `order_number`) with one rule. Here there
is only one kind worth declaring so far — `kind="entity"`, which `units/cnl.py` now tags on every bare-word
filler — and the identity key is simply the word itself (`name`), so `kind` is a literal and only `name`
needs to vary. Extend this the way the probe did (quantify over `kind` too) the moment a second entity
class with a different identity key actually shows up; don't build that generality ahead of a need.

**What this deliberately does not attempt.** Real coreference (definite descriptions, pronouns, "the
database" referring back to "production_database") is `cnl.md` §3's harder, still-unbuilt problem, gated
behind the surge detector for some cases (`forms_discourse.md` §10.3). This rule only merges two mentions
that are *lexically identical* — the coarsest possible stand-in, good enough for a KB where an author
names the same thing the same way twice, wrong the moment two different words are meant to corefer or the
same word is meant to denote two different things. Both failure directions are real; this is a first slice,
not a general solution.
"""
from __future__ import annotations

from .engine import Merge, StandingUnit
from .match import AttrVar, atom

SAME_ENTITY_PAT = (
    atom("a", kind="entity", name=AttrVar("nm")),
    atom("b", kind="entity", name=AttrVar("nm")),
)


def same_entity_rule() -> StandingUnit:
    return StandingUnit("same_entity", SAME_ENTITY_PAT, Merge("a", "b"), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {"same_entity": same_entity_rule()}


__all__ = ["SAME_ENTITY_PAT", "same_entity_rule", "rules"]
