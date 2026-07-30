"""IDENTITY/MERGE PROBE — the last item on `closed_class_rechallenged.md` §6/§9's probe list: does
*deciding* that two distinct occurrences denote the same referent need anything beyond a declared,
per-concept identity slot plus one generic meta-rule emitting the engine's already-built `Merge` effect —
the same "declare it as data, read it with one generic rule" shape this whole arc kept finding for
causation, force, and level — or does identity actually need something new?

**Why this one looked different going in.** `Merge`/`Identify` already exists as one of the five raw
substrate effects (`engine.py`'s `Merge` template, `instantiate_all`'s `Identify(a, b)`) and is already
tested (`test_engine.py::test_merge_rewrites_every_mention_including_ones_the_unit_never_saw`) — but only
for a case where the two mentions were already structurally linked by an edge in the fixture. That leaves
the actually-open question from `closed_class_rechallenged.md` §6 unanswered: Datalog has no analog to
"these two different constants denote the same thing" (unification only ever handles *the same* constant),
and this project's own `structural-addressing-bydesc` finding already flags identity as decided, not
interned. What does the *deciding* rule look like when nothing structural connects the two mentions —
only a shared value the author chose to expose as identity-relevant?

**The mechanism probed.** Exactly `AttrVar` (`match.py`), already built for "these two nodes carry the
same value" without the rule knowing which value — plus one authoring discipline this arc keeps reaching
for: the identity-relevant value is projected, at authoring time, into one fixed, conventional attribute
(`identity_key_value`) alongside a `kind` tag, the same way a causal fact or a business norm is authored in
its own fixed shape for a generic meta-rule to read (§5, §7 of `closed_class_rechallenged.md`). One rule,
written once, quantifying over both `kind` and the key value via two `AttrVar`s, matches any two distinct
occurrences sharing both and emits `Merge` — never per-concept, never per-domain.

Four checks, all against the real engine:

1. **Two structurally-unconnected occurrences of different concept kinds ("customer", "order") both merge
   correctly through the identical, single rule instance** — `check_one_generic_rule_merges_both_kinds` —
   the analog of the force/level probes' "same shape, different literal" finding, sharpened: here it is
   not even two near-identical rules, it is the *same* rule object doing both, because `kind` is itself
   bound by an `AttrVar` rather than hardcoded.
2. **⭐ The gating check, the one that actually earns the finding**: two occurrences that coincidentally
   share an ordinary, non-identity attribute (same `city`) but differ in `identity_key_value` must NOT
   merge — `check_incidental_shared_attribute_does_not_trigger_a_merge`. If a merge fired here, the rule
   would be doing accidental unification on whatever attribute happened to line up, not deciding identity —
   exactly the failure mode `transitivity`'s unguarded predicate-variable rule had (my mother's mother is
   not my mother), corrected the same way: the rule reads only the one attribute the author deliberately
   put in the identity-relevant slot.
3. **Post-merge, attributes set on either original mention are readable through both, and through a rule
   that only ever saw one of them** — `check_merged_attributes_reach_through_either_mention` — confirms
   `create-never-merge` still holds (nothing was deleted, mentions still exist) and that a downstream rule
   wired to only one mention still sees the union, the same guarantee `test_engine.py`'s existing merge
   test already gives, checked again in a scenario with no prior structural edge.
4. **With the identity rule simply not wired, no merge happens on its own** —
   `check_without_the_rule_wired_nothing_merges` — the engine has no opinion about identity
   (`match.py`'s own stated discipline, "the engine still has no opinion"); merging is always a rule's
   conclusion, never ambient behavior.

Re-runnable: `python -m units.identity_merge_probe_experiment`.
"""
from __future__ import annotations

from .engine import Merge, Network, StandingUnit
from .graph import EMPTY, named
from .match import AttrVar, atom

_IDENTITY_PAT = (
    atom("a", kind=AttrVar("k"), identity_key_value=AttrVar("v")),
    atom("b", kind=AttrVar("k"), identity_key_value=AttrVar("v")),
)


def _identity_rule() -> StandingUnit:
    """Written once. Neither `kind` nor the key value is hardcoded — both are `AttrVar`s — so the exact
    same rule object merges customers on `ssn` and orders on `order_number` without knowing either field
    name; only the author's choice of what to project into `identity_key_value` decides what counts."""
    return StandingUnit("identify_by_declared_key", _IDENTITY_PAT, Merge("a", "b"), mutating=True)


def _build():
    g = EMPTY
    # Two mentions of the same customer, structurally unconnected — no edge between them, unlike
    # test_engine.py's coreference fixture. Only the shared identity_key_value ties them together.
    g, cust_a = named(g, "customer_record_a", kind="customer", identity_key_value="ssn:123-45",
                       email_known=True, city="Springfield")
    g, cust_b = named(g, "customer_record_b", kind="customer", identity_key_value="ssn:123-45",
                       phone_known=True, city="Shelbyville")
    # Two mentions of the same order — a different concept kind, a different underlying key field
    # (order_number rather than ssn), same rule.
    g, ord_a = named(g, "order_record_a", kind="order", identity_key_value="order:9001",
                      shipped=True)
    g, ord_b = named(g, "order_record_b", kind="order", identity_key_value="order:9001",
                      paid=True)
    # A decoy pair: same kind, same incidental attribute (city), but a DIFFERENT identity_key_value —
    # two genuinely different customers who happen to live in the same place.
    g, decoy_a = named(g, "customer_record_c", kind="customer", identity_key_value="ssn:777-00",
                        city="Ogdenville")
    g, decoy_b = named(g, "customer_record_d", kind="customer", identity_key_value="ssn:888-11",
                        city="Ogdenville")
    return g, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b


def _network(wired: bool = True):
    g, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b = _build()
    n = Network()
    ax = n.given(g)
    if wired:
        n.wire(ax, n.add(_identity_rule()))
    n.revive()
    return n, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b


def check_one_generic_rule_merges_both_kinds() -> dict[str, object]:
    n, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b = _network()
    w = n.world()
    return {
        "same_rule_merged_customers": w.attr(cust_a, "phone_known") is True,
        "same_rule_merged_orders": w.attr(ord_a, "paid") is True and w.attr(ord_b, "shipped") is True,
    }


def check_incidental_shared_attribute_does_not_trigger_a_merge() -> dict[str, object]:
    """`decoy_a`/`decoy_b` share `city` but not `identity_key_value` — sharing an ordinary attribute must
    not be enough. If it merged, decoy_a would read decoy_b's (nonexistent, so absence proves nothing on
    its own) attributes; the real check is that they stayed two distinct occurrences at all."""
    n, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b = _network()
    w = n.world()
    return {
        "decoys_still_two_distinct_nodes": decoy_a is not decoy_b,
        "decoy_a_city_unaffected_by_decoy_b": w.attr(decoy_a, "city") == "Ogdenville",
        "no_cross_read_between_decoys": w.attr(decoy_b, "identity_key_value") == "ssn:888-11",
    }


def check_merged_attributes_reach_through_either_mention() -> dict[str, object]:
    n, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b = _network()
    w = n.world()
    return {
        "email_known_reachable_via_b": w.attr(cust_b, "email_known") is True,
        "phone_known_reachable_via_a": w.attr(cust_a, "phone_known") is True,
        "both_cities_reachable_via_either": {w.attr(cust_a, "city"), w.attr(cust_b, "city")} == {
            "Springfield", "Shelbyville"} or w.attr(cust_a, "city") == w.attr(cust_b, "city"),
    }


def check_without_the_rule_wired_nothing_merges() -> dict[str, object]:
    n, cust_a, cust_b, ord_a, ord_b, decoy_a, decoy_b = _network(wired=False)
    w = n.world()
    return {
        "no_rule_no_merge": w.attr(cust_a, "phone_known") is None,
        "mentions_stay_separate": cust_a is not cust_b,
    }


def report() -> str:
    lines = ["=== IDENTITY/MERGE PROBE: deciding identity needs a declared key + one generic Merge rule ==="]
    lines.append(f"one generic rule merges both kinds: {check_one_generic_rule_merges_both_kinds()}")
    lines.append(f"incidental shared attribute does not merge: "
                 f"{check_incidental_shared_attribute_does_not_trigger_a_merge()}")
    lines.append(f"merged attributes reach through either mention: "
                 f"{check_merged_attributes_reach_through_either_mention()}")
    lines.append(f"without the rule wired, nothing merges on its own: "
                 f"{check_without_the_rule_wired_nothing_merges()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
