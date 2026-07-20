"""
Phase 8.6 — runtime rule DISABLE (docs/design/cnl_intake_design.md §6).

The rule-authoring lifecycle is add / conflict-negotiate / DISABLE. Disable is the §5-safe "no, forget
that rule": NEVER a deletion — an additive `<disabled>` MARKER in the control layer that reasoning skips.
The rule object stays in the theory list (monotone); only the marker changes which rules are ACTIVE.

Mirrors `focus.py`: control-node markers in the KB (`<disabled>`, `<last-rule>` hubs pointing at nodes
NAMED by rule key), and the explicit control-CNL recognized as a FORM (`RULE_FORMS`), never string-sniffed
(§D.2). "that rule" is the LAST-ADDED rule — the discourse referent of the just-authored rule, the exact
parallel of focus's `forget that` = the current frame. Content-blind: no predicate/domain strings here (§D).
"""
from __future__ import annotations

from .production_rule import Pat, Rule

DISABLED = "<disabled>"
LAST_RULE = "<last-rule>"
RULE_OP = "<rule-op>"
KEY = "key"


# ---------------------------------------------------------------------------
# The markers (control-layer structure)
# ---------------------------------------------------------------------------

def _hub(kb, label: str) -> str:
    """The single control hub node for `label` (`<disabled>` / `<last-rule>`), minted once and reused."""
    for n in kb.nodes_named(label):
        if kb.is_control(n):
            return n
    return kb.add_node(label, control=True)


def _key_node(kb, key: str) -> str:
    """A control node NAMED by a rule key — the thing a marker hub points at. Keys are engine identifiers,
    not content, so the node is control (never a fact subject) and minted if absent."""
    for n in kb.nodes_named(key):
        if kb.is_control(n):
            return n
    return kb.add_node(key, control=True)


def _hub_keys(kb, label: str) -> list[str]:
    """The rule-key names a marker hub currently points at (via `key` edges), or []."""
    out: list[str] = []
    for n in kb.nodes_named(label):
        if not kb.is_control(n):
            continue
        for rel, obj in kb.relations_from(n):
            if kb.has_key(rel, KEY):
                out.append(kb.name(obj))
    return out


def _clear_hub(kb, label: str) -> None:
    from .machine import Machine, SWEEP, State
    doomed = [rel for n in kb.nodes_named(label) if kb.is_control(n)
              for rel, _o in kb.relations_from(n) if kb.has_key(rel, KEY)]
    if doomed:                                       # cut the pointers only (control-layer op, §5-safe;
        Machine().apply(kb, [SWEEP(f"_n{i}") for i in range(len(doomed))],   # SWEEP refuses a fact)
                        State({f"_n{i}": r for i, r in enumerate(doomed)}))


def mark_last_added(kb, keys) -> None:
    """Record `keys` as the just-added rule batch, so a following `forget that rule` knows its referent.
    Replaces the previous `<last-rule>` pointer (only the LAST add is 'that rule')."""
    _clear_hub(kb, LAST_RULE)
    hub = _hub(kb, LAST_RULE)
    for k in keys:
        kb.add_relation(hub, KEY, _key_node(kb, k), control=True)


def last_added_keys(kb) -> list[str]:
    return _hub_keys(kb, LAST_RULE)


def disabled_keys(kb) -> set[str]:
    """The rule keys currently marked `<disabled>` — the set reasoning excludes."""
    return set(_hub_keys(kb, DISABLED))


def disable_last(kb) -> list[str]:
    """`forget that rule` — mark the last-added rule batch `<disabled>` (additive, no deletion §5). Returns
    the disabled keys (empty if no rule has been authored this session — nothing to forget)."""
    keys = last_added_keys(kb)
    hub = _hub(kb, DISABLED)
    have = disabled_keys(kb)
    for k in keys:
        if k not in have:
            kb.add_relation(hub, KEY, _key_node(kb, k), control=True)
    return keys


def active_rules(kb, rules) -> list[Rule]:
    """The theory reasoning should actually run: `rules` minus the `<disabled>` ones. Called wherever the
    engine reasons/lints (question answering, conflict trial), so a disabled rule neither fires nor cycles."""
    dis = disabled_keys(kb)
    return [r for r in rules if r.key not in dis] if dis else list(rules)


# ---------------------------------------------------------------------------
# The explicit rule control-CNL — recognized as FORMS, never string-sniffed (§D.2)
# ---------------------------------------------------------------------------

RULE_FORMS: list[Rule] = [
    # "forget that rule" / "disable that rule"  -> disable the last-authored rule
    Rule(key="rule.disable.forget",
         lhs=[Pat("?s", "first", "forget?"), Pat("forget?", "next", "that?"),
              Pat("that?", "next", "rule?")],
         rhs=[Pat(RULE_OP + "?", "op", "disable")]),
    Rule(key="rule.disable.disable",
         lhs=[Pat("?s", "first", "disable?"), Pat("disable?", "next", "that?"),
              Pat("that?", "next", "rule?")],
         rhs=[Pat(RULE_OP + "?", "op", "disable")]),
]


def _slot(graph, node: str, role: str) -> str | None:
    for rel, obj in graph.relations_from(node):
        if graph.has_key(rel, role):
            return graph.name(obj)
    return None


def recognize_rule_op(utterance: str) -> str | None:
    """If `utterance` is an explicit rule-control move, its `op` (`"disable"`) — else None. Recognized by
    which RULE_FORM fires in a scratch scope, NOT a Python word list.

    MUTUALLY EXCLUSIVE WITH THE FOCUS FORMS BY STRUCTURE (2026-07-20). This used to rely on intake
    checking it BEFORE `focus.drop`, since `forget that rule` fired both and only ladder position
    picked the winner — a routing decision made by ordering rather than by declaration. `focus.drop`
    now carries a NAC saying nothing follows `that`, so the two forms genuinely disagree and either
    check order gives the same answer. Pinned by
    `test_the_disable_and_focus_forms_are_mutually_exclusive`."""
    from .cnl.forms import tokenize
    from .lowering import run_bank
    from .world_model import Graph
    tmp = Graph()
    tokenize(tmp, utterance)
    run_bank(tmp, RULE_FORMS)
    for nid in tmp.nodes():
        if tmp.name(nid) == RULE_OP:
            return _slot(tmp, nid, "op")
    return None
