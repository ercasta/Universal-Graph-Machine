"""AUTHOR — routing `force="author"`, the same trivial pattern already checked for `ask`/`command`
(`units/goal_rules.py`), extended to a genuinely different destination: not a goal, but standing KB
content.

**Scoped deliberately narrow.** Authoring splits into two cases, named in `closed_class_rechallenged.md`
§5: minting more open, inert data (a plain fact), or compiling a genuinely new closed-class rule (a
standing policy watch, "a rule writes a rule" — `tests/units/test_engine.py::test_a_rule_writes_a_whole_
rule_with_nothing_authored_in_python`). Only the first is built here. The second needs a real compiler —
walking an arbitrary authored `when:`/`then:` shape into the low-level `PAT`/`ATOM`/`CONSTRAINT`/`EMIT`
primitives that test exercises by hand — and deserves its own pass, probed on its own rather than bundled
in. `AUTHOR_FACT_PAT`'s `absent(when:)` guard is the deliberate seam where that later rule plugs in,
without this one needing to change.

**Authoring a fact needs nothing beyond marking the utterance consumed.** Once `units/cnl.py` parses
`[utterance | force: author | content: [dangerous | target: production_database]]`, the `dangerous`
occurrence is already ordinary, persistent graph data — nesting is containment (`cnl.md` §3), not
something requiring activation. There is no "write it into the KB" step distinct from the utterance
having been parsed at all; the only real job left is bookkeeping (never mint two facts from one repeated
revive), which is exactly `idempotent_mutation_experiment.py`'s consumption-marker discipline, reused
unmodified.
"""
from __future__ import annotations

from .engine import Attribute, StandingUnit
from .match import absent, atom, role

AUTHOR_FACT_PAT = (
    atom("u", name="utterance", force="author", routed=None,
         out=(role("content", atom("c")),)),
    absent(atom("c", out=(role("when", atom()),))),
)


def author_fact_rule() -> StandingUnit:
    return StandingUnit("author_fact", AUTHOR_FACT_PAT, Attribute("u", "routed", True), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {"author_fact": author_fact_rule()}


__all__ = ["AUTHOR_FACT_PAT", "author_fact_rule", "rules"]
