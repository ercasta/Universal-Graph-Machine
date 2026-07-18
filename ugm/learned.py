"""
Learned rules and the PROVISIONAL support query (learning arc, docs/design/learning_design.md §6.1a).

A rule the system LEARNED is not a rule somebody authored, and a conclusion standing on one should
say so. This module is the query-side half of that: given a goal, which learned rules did the
answer actually lean on?

WHY NOT A CONFIDENCE NUMBER. The design first proposed "born hedged" via `Rule.probability`. That
field is DEAD — measured package-wide, nothing reads it, and setting it changes no graph; `CONF`
is likewise written by `add_relation` and read by nothing. The whole numeric channel is inert, and
reviving it would re-introduce exactly the opaque per-rule quantity the project rejected for
grammar induction (vision §10) and rejected again when k>=2 licensing was settled on ELIMINATION
rather than counting.

WHAT REPLACES IT. Provenance already records which rule proved what. So "is this conclusion
provisional?" is answerable after the fact, exactly, with a reason in the author's vocabulary:
walk the support of the answer and report the learned rules in it. No new channel, nothing stored
per fact, and a conclusion that leaned on a learned rule can be rendered wearing its kind — the
same move the possibilistic surface already makes with `no (assumed)` vs a hard `no`.

THE VERDICT VOCABULARY IS UNCHANGED. `check` still returns POSITIVE / ENTAILED_NEG / ASSUMED_NO /
UNKNOWN, so every existing caller is untouched. Provisionality is EXPLANATION, and explanation is
a separate question you ask when you care — the two-homes discipline (graph = explanation,
registers = stepping), not a fifth verdict every comparison would have to learn about.
"""
from __future__ import annotations

from .attrgraph import AttrGraph
from . import provenance as prov


# The flat-schema role that marks a rule as learned (`<rule> --rl_learned--> …`). Presence is the
# marker; the object is not read. A learner marks its own output with this, so the mark survives
# the graph round-trip exactly like `rl_key` does.
LEARNED_ROLE = "rl_learned"


def learned_keys(rules) -> set[str]:
    """The keys of the rules in `rules` that were LEARNED rather than authored."""
    return {r.key for r in rules if getattr(r, "learned", False)}


def _goal_relations(g: AttrGraph, goal: tuple[str, str | None, str | None]) -> list[str]:
    """Relation nodes matching a `(pred, subj|None, obj|None)` goal — the answer's own facts."""
    pred, subj, obj = goal
    out: list[str] = []
    for nid in g.nodes():
        if g.is_inert(nid) or g.predicate(nid) != pred:
            continue
        subs = [g.name(s) for s in g.into(nid)]
        objs = [g.name(o) for o in g.out(nid)]
        if subj is not None and subj not in subs:
            continue
        if obj is not None and obj not in objs:
            continue
        out.append(nid)
    return out


def rules_supporting(g: AttrGraph, rel: str) -> set[str]:
    """Every rule key in the TRANSITIVE support of fact `rel`.

    A conclusion is provisional if ANY step of its derivation used a learned rule, not merely the
    last one — so this follows `premises_of` down rather than reading the top justification alone."""
    seen_rels: set[str] = set()
    keys: set[str] = set()
    frontier = [rel]
    while frontier:
        r = frontier.pop()
        if r in seen_rels or not g.has(r):
            continue
        seen_rels.add(r)
        for j in prov.support_js(g, r):
            key = prov.rule_of_j(g, j)
            if key:
                keys.add(key)
            frontier.extend(prov.premises_of(g, j))
    return keys


def learned_support(fact_g: AttrGraph, goal: tuple[str, str | None, str | None], *,
                    learned: set[str], rules: AttrGraph | None = None,
                    max_rounds: int = 1000, policy=None) -> list[str]:
    """The LEARNED rule keys the answer to `goal` stands on, best-effort, sorted.

    Empty means the conclusion rests only on facts and authored rules — it is as good as anything
    the user asserted. Non-empty names exactly which learned rules to hedge the answer with.

    Runs the demand chain with provenance ON (provenance is what makes this answerable at all), so
    call it when you intend to render the support, not on every question."""
    if not learned:
        return []
    from .chain import chain_sip
    chain_sip(fact_g, goal, rules=rules, provenance=True,
              max_rounds=max_rounds, policy=policy)
    used: set[str] = set()
    for rel in _goal_relations(fact_g, goal):
        used |= rules_supporting(fact_g, rel)
    return sorted(used & learned)


def render_provisional(verdict: str, learned_used: list[str]) -> str:
    """A verdict wearing its kind: `positive (assuming 2 learned rule(s): …)`.

    Mirrors the possibilistic surface's `no (assumed)` — the answer is not downgraded, it is
    LABELLED, and the label names what would have to be wrong."""
    if not learned_used:
        return verdict
    return (f"{verdict} (assuming {len(learned_used)} learned rule(s): "
            f"{', '.join(learned_used)})")
