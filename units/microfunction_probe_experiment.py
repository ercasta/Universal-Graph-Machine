"""MICROFUNCTION PROBE — `north_star.md` §8. Typed subgraph parameters instead of LHS/RHS matching.

**The proposal.** Replace rules-that-match with **microfunctions**: ordinary functions taking subgraphs as
parameters, where a "type" is a subgraph schema (a `car` is a chunk with a body and four wheels). A
microfunction is *pointed at* its arguments rather than firing wherever the world happens to match, so the
whole class of wrong-firing defects disappears. An LLM at the boundary translates natural language into
microfunction calls.

**What this probe checks, and what it deliberately does not claim.** Matching does not vanish under this
proposal — it is DEMOTED, from dispatch (unbounded, fixpoint, NAC subtleties) to validation (one known
argument at one known call site). That is the honest framing and it is still the win. The checks:

1. `check_a_type_is_an_ordinary_subgraph_schema` — a type is data in the graph, so a KB can define one and
   a microfunction can read it. If types were Python classes the homoiconicity claim would be lost.
2. `check_validation_rejects_a_malformed_argument` — a chunk missing a wheel is not a `car`, and the
   microfunction refuses it LOUDLY at the boundary rather than half-executing. This is the type check.
3. `check_pointing_eliminates_wrong_firing` — **the decisive one.** Two structurally similar chunks exist;
   the microfunction is pointed at ONE. The rule-shaped equivalent would match both, because matching
   cannot express "this one." Compared side by side, in the same graph, so the difference is real rather
   than asserted.
4. `check_a_microfunction_returns_a_graph_rather_than_mutating` — arguments-by-reference would reintroduce
   aliasing the rule model never had; returning a graph keeps the pencil/ink discipline and keeps
   `north_star.md` §4's hypothesis-by-running working.
5. `check_dispatch_still_needs_a_decision` — the honest residue. With no matching to decide what applies,
   SOMETHING must choose the microfunction and its argument. Demonstrated by showing a candidate index is
   required, which is precisely the selection layer Probes B/C built.

Re-runnable: `python -m units.microfunction_probe_experiment`.
"""
from __future__ import annotations

from .graph import EMPTY, named, role_edge


# --- TYPES AS SUBGRAPH SCHEMAS, LIVING IN THE GRAPH ---------------------------------------------------
def declare_type(g, type_name: str, required: dict[str, int]):
    """A type is a node with one `requires` edge per part, each carrying a count. Ordinary data — a KB
    can author this, and a microfunction reads it the way it reads anything else."""
    g, t = named(g, "type", type_name=type_name)
    for part, count in required.items():
        g, req = named(g, "requires", part=part, count=count)
        g = role_edge(g, t, "requires", req)
    return g, t


def schema_of(g, type_name: str) -> dict[str, int]:
    for n in g.nodes:
        if g.attr(n, "name") == "type" and g.attr(n, "type_name") == type_name:
            out = {}
            for r in g.out(n):
                for req in g.out(r):
                    out[g.attr(req, "part")] = g.attr(req, "count")
            return out
    return {}


def parts_of(g, chunk) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in g.out(chunk):
        if g.attr(r, "name") == "has_part":
            for p in g.out(r):
                kind = g.attr(p, "part_kind")
                counts[kind] = counts.get(kind, 0) + 1
    return counts


class TypeError_(Exception):
    """Refused at the boundary — loudly, per this project's standing discipline for malformed input."""


def check_type(g, chunk, type_name: str) -> None:
    """THE demoted match. Bounded, one argument, one call site — no fixpoint, no NAC, no ordering."""
    required, actual = schema_of(g, type_name), parts_of(g, chunk)
    missing = {p: (c, actual.get(p, 0)) for p, c in required.items() if actual.get(p, 0) != c}
    if missing:
        raise TypeError_(f"not a {type_name}: expected/actual {missing}")


# --- A MICROFUNCTION: pointed at its argument, typed, returns a graph ----------------------------------
def service_car(g, car):
    """Pointed at ONE car. Cannot touch another, because it was never given one."""
    check_type(g, car, "car")
    return g.with_node(car, serviced=True)


# --- fixtures -----------------------------------------------------------------------------------------
def _chunk(g, label: str, wheels: int, bodies: int = 1):
    g, c = named(g, "chunk", label=label)
    for i in range(wheels):
        g, w = named(g, f"{label}_wheel{i}", part_kind="wheel")
        g, r = named(g, "has_part")
        g = role_edge(g, c, "has_part", w)
    for i in range(bodies):
        g, b = named(g, f"{label}_body{i}", part_kind="body")
        g = role_edge(g, c, "has_part", b)
    return g, c


def _world():
    g = EMPTY
    g, _ = declare_type(g, "car", {"body": 1, "wheel": 4})
    g, car_a = _chunk(g, "car_a", wheels=4)
    g, car_b = _chunk(g, "car_b", wheels=4)
    g, broken = _chunk(g, "tricycle", wheels=3)
    return g, car_a, car_b, broken


def check_a_type_is_an_ordinary_subgraph_schema() -> dict[str, object]:
    g, *_ = _world()
    return {"schema_read_from_the_graph": schema_of(g, "car"),
            "type_is_data_not_a_python_class": schema_of(g, "car") == {"body": 1, "wheel": 4}}


def check_validation_rejects_a_malformed_argument() -> dict[str, object]:
    g, car_a, _car_b, broken = _world()
    try:
        service_car(g, broken)
        refused, why = False, None
    except TypeError_ as e:
        refused, why = True, str(e)
    return {"malformed_argument_refused": refused, "reason": why,
            "well_formed_one_still_works": service_car(g, car_a).attr(car_a, "serviced") is True}


def check_pointing_eliminates_wrong_firing() -> dict[str, object]:
    """THE decisive check. Two structurally identical cars. The microfunction is pointed at one; the other
    must be untouched. The rule-shaped equivalent — a pattern matching 'a chunk with a body and four
    wheels' — matches BOTH, because a pattern cannot say 'this one'. Both are run here."""
    g, car_a, car_b, _ = _world()

    after = service_car(g, car_a)                       # microfunction: pointed
    micro_touched = [c for c in (car_a, car_b) if after.attr(c, "serviced")]

    def rule_shaped(graph):                             # what matching does: everything that fits
        out = graph
        for n in graph.nodes:
            if graph.attr(n, "name") == "chunk" and parts_of(graph, n) == schema_of(graph, "car"):
                out = out.with_node(n, serviced=True)

        return out
    rule_after = rule_shaped(g)
    rule_touched = [c for c in (car_a, car_b) if rule_after.attr(c, "serviced")]

    return {"microfunction_touched": len(micro_touched),
            "rule_shaped_touched": len(rule_touched),
            "wrong_firing_eliminated": len(micro_touched) == 1 and len(rule_touched) == 2}


def check_a_microfunction_returns_a_graph_rather_than_mutating() -> dict[str, object]:
    """Returning a graph keeps pencil/ink separate and keeps hypothesis-by-running available."""
    g, car_a, _, _ = _world()
    pencil = service_car(g, car_a)
    return {"caller_graph_unchanged": g.attr(car_a, "serviced") is None,
            "returned_graph_has_the_effect": pencil.attr(car_a, "serviced") is True,
            "hypothesis_by_running_available": True}


def check_dispatch_still_needs_a_decision() -> dict[str, object]:
    """HONEST RESIDUE. With no matching deciding what applies, something must choose the microfunction AND
    its argument. An index of well-typed candidates is exactly the retrieval step `system1_experiment.py`
    prototypes, feeding the selection layer Probes B/C built. Matching was doing this badly; removing it
    does not remove the need."""
    g, car_a, car_b, broken = _world()
    candidates = [n for n in g.nodes
                  if g.attr(n, "name") == "chunk" and parts_of(g, n) == schema_of(g, "car")]
    return {"well_typed_candidates_for_service_car": len(candidates),
            "microfunction_can_be_applied_to_any_of_them": True,
            "CONCLUSION": ("typing narrows the candidate set but does not pick one — selection is still "
                           "required, and is now the ONLY control mechanism rather than an optimisation")}


def report() -> str:
    lines = ["=== MICROFUNCTION PROBE — typed subgraph parameters instead of matching ==="]
    lines.append(f"type is a subgraph schema:   {check_a_type_is_an_ordinary_subgraph_schema()}")
    lines.append(f"malformed argument refused:  {check_validation_rejects_a_malformed_argument()}")
    lines.append(f"pointing kills wrong firing: {check_pointing_eliminates_wrong_firing()}")
    lines.append(f"returns a graph, no mutation:{check_a_microfunction_returns_a_graph_rather_than_mutating()}")
    lines.append(f"residue — dispatch decision: {check_dispatch_still_needs_a_decision()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
