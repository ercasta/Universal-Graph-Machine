"""SUBSTITUTION EXPERIMENT — does 'define X as Y' + `Identify` progressively substitute, the way solving
a small system of equations does?

`computation_units.md` §5 raised the question: can the engine itself, with no new closed-class form, be
used to chase down a chain of definitions to a concrete value? `Identify` (`overlay.py`) already merges
two nodes into one; a rule of the shape "if X is defined this way, identify X with what it resolves to"
needs nothing new to try. This is that experiment, checked against the real engine rather than argued
about.

## Scope, honestly

Chain: `customer_discount -defined_as-> holiday_rate -defined_as-> standard_rate -defined_as-> ten_percent`,
`ten_percent` carrying `value=0.10`. One rule, `Merge("x", "y")` on a `defined_as` pattern. Checks: does the
chain resolve in one revive regardless of construction order (confluence, measured not assumed); does a
circular definition stabilize safely instead of surging; does a second rule consuming the resolved value
need anything beyond ordinary wiring. Full writeup and what it means: `docs/units/computation_units.md`
§5. What this does **not** test: actual arithmetic (`2x + 3 = 7`) — that's a delegated tool-call, same
shape as the aggregation finding, and orthogonal to what's checked here.
"""
from __future__ import annotations

from .engine import Attribute, Merge, Network, StandingUnit
from .graph import EMPTY, named, role_edge
from .match import atom, role

_PAT = (atom("x", out=(role("defined_as", atom("y")),)),)


def _build_chain(order: list[str]) -> tuple:
    """`order`: names in the order their `defined_as` edge gets written into the graph — to test whether
    construction/match order changes the final answer."""
    g = EMPTY
    nodes = {}
    g, nodes["ten_percent"] = named(g, "ten_percent", value=0.10)
    g, nodes["standard_rate"] = named(g, "standard_rate")
    g, nodes["holiday_rate"] = named(g, "holiday_rate")
    g, nodes["customer_discount"] = named(g, "customer_discount")

    edges = {
        "standard_rate": "ten_percent",
        "holiday_rate": "standard_rate",
        "customer_discount": "holiday_rate",
    }
    for src_name in order:
        g = role_edge(g, nodes[src_name], "defined_as", nodes[edges[src_name]])
    return g, nodes


def _resolve(order: list[str]):
    g, nodes = _build_chain(order)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("substitute", _PAT, Merge("x", "y"), mutating=True)))
    n.revive()
    return n.world().attr(nodes["customer_discount"], "value")


def check_order_independence() -> dict[str, object]:
    """Same chain, three construction orders. Confluent iff all three agree."""
    orders = {
        "dependency_order": ["standard_rate", "holiday_rate", "customer_discount"],
        "reverse_order": ["customer_discount", "holiday_rate", "standard_rate"],
        "shuffled_order": ["holiday_rate", "customer_discount", "standard_rate"],
    }
    results = {name: _resolve(order) for name, order in orders.items()}
    results["confluent"] = len(set(results.values())) == 1
    return results


def check_circular_definition() -> dict[str, object]:
    """`a defined_as b`, `b defined_as a` — does it merge cleanly or surge?"""
    g = EMPTY
    g, a = named(g, "a")
    g, b = named(g, "b")
    g = role_edge(g, a, "defined_as", b)
    g = role_edge(g, b, "defined_as", a)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("substitute", _PAT, Merge("x", "y"), mutating=True)))
    n.revive()
    o = n.overlays()
    return {"surges": tuple(n.surges), "merged": o.resolve(a) is o.resolve(b)}


def check_downstream_consumption() -> dict[str, object]:
    """A second rule that should fire once the chain resolves to 0.10. Confirms the tunnel
    (`model.md` invariant 3): the consumer must be wired to *both* the substitution rule's output and the
    original axiom, not just the former."""
    order = ["standard_rate", "holiday_rate", "customer_discount"]
    g, nodes = _build_chain(order)
    n = Network()
    sub = n.add(StandingUnit("substitute", _PAT, Merge("x", "y"), mutating=True))
    axiom_cell = n.given(g)
    n.wire(axiom_cell, sub)

    downstream_pat = (atom("z", value=0.10),)
    downstream = n.add(StandingUnit("apply_ten_percent", downstream_pat,
                                     Attribute("z", "approved_discount", True), mutating=True))
    wired_to_axiom_only = Network()
    # rebuild fresh so the "wired to substitution output only" failure mode is shown honestly
    g2, nodes2 = _build_chain(order)
    sub2 = wired_to_axiom_only.add(StandingUnit("substitute", _PAT, Merge("x", "y"), mutating=True))
    axiom2 = wired_to_axiom_only.given(g2)
    wired_to_axiom_only.wire(axiom2, sub2)
    downstream2 = wired_to_axiom_only.add(StandingUnit(
        "apply_ten_percent", downstream_pat, Attribute("z", "approved_discount", True), mutating=True))
    wired_to_axiom_only.wire(sub2.cell, downstream2)
    wired_to_axiom_only.revive()
    under_wired = wired_to_axiom_only.world().attr(nodes2["customer_discount"], "approved_discount")

    n.wire(sub.cell, downstream)      # sees the identifications
    n.wire(axiom_cell, downstream)    # ALSO needs the base fact (value=0.10) to match against
    n.revive()
    fully_wired = n.world().attr(nodes["customer_discount"], "approved_discount")

    return {"wired_to_substitution_output_only": under_wired,
            "wired_to_both_substitution_and_axiom": fully_wired}


def report() -> str:
    lines = ["=== SUBSTITUTION EXPERIMENT: define + Identify as progressive substitution ==="]
    lines.append(f"order independence: {check_order_independence()}")
    lines.append(f"circular definition: {check_circular_definition()}")
    lines.append(f"downstream consumption (the tunnel, shown honestly): "
                 f"{check_downstream_consumption()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
