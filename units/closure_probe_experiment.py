"""CLOSURE PROBE — Probe A of `graph_data_model.md` §7. Is the composition-to-unbounded-depth claim
actually true of the rules that exist, or only of the table someone wrote?

`the_data_model.md` argues that arbitrary nesting is safe because of a closure property: *every operation
reads structures built from this vocabulary, and produces structures built from this same vocabulary.*
That argument is only worth something if it is checked against the code rather than against the prose,
and there is an obvious way to check it badly — encode the document's own table as data and assert the
table matches itself. That proves nothing. This probe deliberately does not do that.

**The check, stated so it can fail.** Harvest every `StandingUnit` actually defined across `units/`.
For each, read off two things by introspection, never by hand:

* what it MINTS — `Emit.name` (node kinds), `Attribute.attr` (lifecycle/annotation marks), `Link.role`
  and `Emit.roles` (edge labels);
* what it READS — every `name=`/attribute key/role name appearing anywhere in its pattern, walked with
  `match.atoms()` (the same inspection helper `model.md` §12's invariant 1 is tested with).

Then assert the closure property directly: **every kind of thing any rule mints is a kind some rule can
match.** A minted kind nothing reads is a dead end — structure that leaves the vocabulary and can never be
composed with anything again, which is precisely what would break unbounded-depth nesting.

**One honest caveat, and it is why this reports rather than merely asserts.** Two categories of mint are
legitimately unread-by-name:

1. **Open-class content.** A goal's `wants:` target (`tier_known`, `routed`, `ticket_resolved`) is business
   content, matched positionally through its role edge and by its `true=` mark, never by its name — that is
   the whole point of the open class. Unread-by-name is correct for these.
2. **Terminal marks.** An attribute nothing further keys on (`from_force`, provenance-ish annotations) is a
   record, not a handle.

So the probe partitions the unread mints and reports them, and only *node kinds* that are neither content
nor terminal count as a genuine dead-end finding. The partition is declared explicitly below so that a
future reader can disagree with the classification rather than have it hidden inside a pass/fail.

Re-runnable: `python -m units.closure_probe_experiment`.
"""
from __future__ import annotations

import importlib

from .engine import Attribute, Emit, Link, StandingUnit
from .match import AttrVar, atoms

# Every module in `units/` that defines rules, whether a shared library or a probe script.
_RULE_MODULES = (
    "author_rules", "goal_rules", "identity_rules", "prohibition_rules",
    "goal_decomposition_experiment", "level_probe_experiment",
    "meta_concept_unification_experiment", "nac_verification_experiment",
    "quantification_cursor_experiment", "structural_choice_experiment",
)

# Declared, per `the_data_model.md`: node kinds minted as OPEN-CLASS CONTENT — a goal's satisfaction
# condition and friends. Matched through a role edge and a `true=` mark, never by name, by design.
_CONTENT_KINDS = frozenset({
    "tier_known", "routed", "ticket_resolved", "route_to_agent",
    "vip", "vip_known", "answered", "safe", "shipped",
    "danger_check",                       # nac_verification: the subgoal's own wanted claim
    "book_flight", "book_hotel",          # structural_choice: candidate actions, matched by role
})


def _collect_rules() -> dict[str, StandingUnit]:
    """Every `StandingUnit` any rule-defining module exposes, keyed `module.rule`."""
    found: dict[str, StandingUnit] = {}
    for mod_name in _RULE_MODULES:
        mod = importlib.import_module(f"units.{mod_name}")
        factory = getattr(mod, "rules", None) or getattr(mod, "_rules", None)
        if factory is None:
            continue
        produced = factory()
        items = produced.items() if isinstance(produced, dict) else enumerate(produced)
        for rule_name, rule in items:
            if isinstance(rule, StandingUnit):
                found[f"{mod_name}.{rule_name}"] = rule
    return found


def _minted(rule: StandingUnit) -> dict[str, set]:
    """What a rule PRODUCES, by introspecting its effect list — never by reading a doc."""
    kinds, attrs, roles = set(), set(), set()
    for e in rule.effects:
        if isinstance(e, Emit):
            kinds.add(e.name)
            roles.update(r for r, _ in e.roles)
        elif isinstance(e, Attribute):
            attrs.add(e.attr)
        elif isinstance(e, Link) and isinstance(e.role, str):
            roles.add(e.role)
    return {"kinds": kinds, "attrs": attrs, "roles": roles}


def _read(rule: StandingUnit) -> dict[str, set]:
    """What a rule CONSUMES: every `name=` value, attribute key, and role label in its pattern.

    A role node is `atom(name="wants", out=(target,))` — indistinguishable, structurally, from an ordinary
    atom matched by name. That ambiguity is inherent to the representation (a role IS a node), so a
    `name=` value is credited to BOTH sets; the closure question ("can anything match this?") is answered
    either way, and over-crediting here can only make the probe more forgiving, never less honest about a
    genuine dead end.
    """
    kinds, attrs, roles, variable_named = set(), set(), set(), set()
    if rule.pattern is None:
        return {"kinds": kinds, "attrs": attrs, "roles": roles}
    for pat in atoms(rule.pattern):
        for key, val in pat.attrs:
            attrs.add(key)
            if key == "name" and isinstance(val, str):
                kinds.add(val)
                roles.add(val)
            elif key == "name" and isinstance(val, AttrVar):
                # ⚠ NOT a wildcard reader, and the first draft of this probe wrongly treated it as one —
                # which made the whole closure check pass VACUOUSLY (a false green, worse than a red).
                # `identity_rules.py`'s `atom("a", kind="entity", name=AttrVar("nm"))` paired with
                # `atom("b", …, name=AttrVar("nm"))` is a CO-REFERENCE constraint — "two nodes whose names
                # are equal to each other" — not "any kind can be matched." It reads no specific kind, so
                # it contributes nothing to the read-vocabulary. Recorded, not credited.
                variable_named.add(key)
    return {"kinds": kinds, "attrs": attrs, "roles": roles}


def _union(per_rule: dict, axis: str) -> set:
    out: set = set()
    for sets in per_rule.values():
        out |= sets[axis]
    return out


def check_every_minted_kind_is_readable() -> dict[str, object]:
    """THE closure check. A node kind some rule mints, that no rule's pattern can match, is structure
    that has left the vocabulary — the one thing that would break unbounded nesting."""
    rules = _collect_rules()
    minted = {k: _minted(r) for k, r in rules.items()}
    read = {k: _read(r) for k, r in rules.items()}

    all_minted_kinds = _union(minted, "kinds")
    all_read_kinds = _union(read, "kinds")
    unread = all_minted_kinds - all_read_kinds
    dead_ends = sorted(unread - _CONTENT_KINDS)
    return {
        "rules_harvested": len(rules),
        "distinct_kinds_minted": len(all_minted_kinds),
        "unread_but_declared_open_content": sorted(unread & _CONTENT_KINDS),
        "GENUINE_DEAD_ENDS": dead_ends,
        "closed": not dead_ends,
    }


def check_every_minted_mark_is_readable() -> dict[str, object]:
    """The same question for lifecycle marks. A mark nothing keys on is weaker than a dead-end kind — it
    may be a deliberate terminal record — so this REPORTS rather than passing/failing, and the judgement
    is left to a reader who can see the names."""
    rules = _collect_rules()
    minted_attrs = _union({k: _minted(r) for k, r in rules.items()}, "attrs")
    read_attrs = _union({k: _read(r) for k, r in rules.items()}, "attrs")
    return {"minted_marks": len(minted_attrs),
            "marks_no_rule_keys_on": sorted(minted_attrs - read_attrs)}


def check_every_minted_role_is_walkable() -> dict[str, object]:
    """And for edges. A role label nothing walks means a part was attached that nothing can reach —
    the relational form of the same defect."""
    rules = _collect_rules()
    minted_roles = _union({k: _minted(r) for k, r in rules.items()}, "roles")
    read_roles = _union({k: _read(r) for k, r in rules.items()}, "roles")
    return {"minted_roles": sorted(minted_roles),
            "roles_no_rule_walks": sorted(minted_roles - read_roles)}


def check_reflexive_edge_is_present() -> dict[str, object]:
    """§5's one genuinely reflexive edge: some rule must mint RULE-shaped data, or the closure is merely
    over data and the homoiconicity claim — the thing `the_data_model.md` identifies as the ONE place the
    whole bet sits — is unsupported by anything running.

    **Finding, and it is a scope result rather than a refutation: no rule in any `units/` rule module mints
    rule-shaped data.** The reflexive edge is real and demonstrated — `tests/units/test_engine.py`'s
    `test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python` mints `pattern`/`atom`/`head`/`tail`
    exactly as claimed — but it lives in the TEST SUITE, in rules built inline, and has never been promoted
    into a shipped rule library the way `goal_rules.py` was promoted out of the force/level probes. So the
    capability is proven and the *library* does not use it. That is worth knowing precisely, because
    `graph_data_model.md` §6.3's payoff (compiling an episode into a reusable metaprocedure) would be the
    first real consumer of it outside a test."""
    rules = _collect_rules()
    rule_shaped = {"rule", "pattern", "atom", "effect", "unit", "premise", "absent", "head", "tail"}
    minting = sorted(k for k, r in rules.items() if _minted(r)["kinds"] & rule_shaped)
    return {"rule_modules_minting_rule_shaped_data": minting,
            "present_in_units_rule_libraries": bool(minting),
            "demonstrated_in_test_suite": "tests/units/test_engine.py:1211"}


def report() -> str:
    lines = ["=== CLOSURE PROBE (Probe A) — is the vocabulary actually closed, per the code? ==="]
    lines.append(f"minted kinds all readable:  {check_every_minted_kind_is_readable()}")
    lines.append(f"minted marks all keyed on:  {check_every_minted_mark_is_readable()}")
    lines.append(f"minted roles all walkable:  {check_every_minted_role_is_walkable()}")
    lines.append(f"reflexive edge present:     {check_reflexive_edge_is_present()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
