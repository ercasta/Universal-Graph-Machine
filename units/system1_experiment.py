"""SYSTEM 1 EXPERIMENT — a first, minimal associative-retrieval prototype for `model.md` §7.

§7's outer loop is RETRIEVE / ASSEMBLE / RUN / WRITE BACK. Everything built so far in this project
(`units/goal_experiment.py`, `units/substitution_experiment.py`) hand-authors every wire. This is the
first attempt at RETRIEVE itself: given an **attended** region of the graph and a pool of **candidate**
units (already added to the `Network`, but dangling — wired to nothing), decide which candidates *come to
mind* and wire them in.

**Deliberately Python-level, and that is not a shortcut — `model.md` §7 says the outer driver does
retrieval, wiring, running and writing, and that "no semantics" means it never interprets *content*, not
that it can't touch the graph.** All the actual judgement (whether a fact is true, whether a rule's
conclusion holds) still lives inside a unit, matched exactly by `units/match.py`'s solver once wired.
Retrieval here only ever proposes a wire — it is `Network.wire()`'s own docstring, cashed: "the only way
a unit reaches anything," now decided by resemblance instead of by hand.

**Similarity is authored, not global** (`model.md` §4) — this file's `resemblance()` is *one* possible
scorer (attribute-key overlap between a candidate's pattern and the attended region), not *the* similarity
metric. It is allowed to be wrong in both directions, and that is not a flaw to fix: §7 says retrieval
"is allowed to be incomplete and allowed to be wrong; the cost of a wrong suggestion is a wasted step."

**Two things added after discussion, both about how retrieval should propose wirings without needing to
retract anything:**

1. **Fan-out, not swap.** Multiple candidates can be wired from the *same* attended-region snapshot at
   once — `Network.wires` is just a set of `(src, dst, gate)` triples, and nothing restricts how many
   consumers one source feeds. So there is no need to pick one "best" candidate and later unwire it for a
   better one: wire every candidate that clears `theta`, and leave the ones that don't fire standing —
   `model.md` §7's *"a dangling gate... is a standing trigger"* means an unfired, wired candidate is cheap
   and stays ready to fire later if the graph changes, exactly the behavior wanted.
2. **One reused reflective cell, not a fresh one per call.** The first version minted a brand-new
   `n.axiom(*effects_of(n.asserted), ...)` on every `retrieve()` call. Measured cost: because
   `Network.axiom()` also writes the axiom's own node into the graph (`_describe`), each new snapshot
   included descriptions of every earlier one — a real, linear-per-turn accumulation (axiom count and wire
   count both grew every turn), not a hypothetical. `retrieve()` now accepts an existing reflective `Cell`
   and mutates its `.held` in place on later calls — same `Cell`, same wire, fresh contents, flat cost.

**What this is not:** subgraph-embedding similarity, a learned retriever, or attention decay/leak handling
(`model.md` §7's Zeigarnik discussion, §13's attention leak). Those are real, later work.

Re-runnable: `python -m units.system1_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Cell, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, Graph, named
from .match import atom, atoms


def attention(g: Graph, seeds: tuple, hops: int) -> tuple:
    """Every node reachable from `seeds` within `hops` outward edges — `model.md` §7's *"System 1 recalls
    against the attended region of the graph, never the whole of it."* A BFS, not a similarity metric;
    the metric is what §7 calls the outer loop's job, applied next in `resemblance()`."""
    frontier = set(seeds)
    seen = set(seeds)
    for _ in range(hops):
        nxt = {d for n in frontier for d in g.out(n)} - seen
        if not nxt:
            break
        seen |= nxt
        frontier = nxt
    return tuple(seen)


def _pattern_keys(pattern) -> set:
    """Every crisp attribute key a pattern's atoms require — the candidate's own "topic," read off its
    authored `Pat`s via `match.atoms()` rather than anything new."""
    return {k for a in atoms(pattern) for k, _ in a.attrs}


def _attended_keys(g: Graph, attended: tuple) -> set:
    return {k for n in attended for k in g.attrs.get(n, {})}


def resemblance(unit: StandingUnit, attended_keys: set) -> float:
    """Jaccard overlap between a candidate's required attribute keys and what's attended. A crude,
    honest stand-in for *"this looks relevant"* — authored, inspectable, and wrong sometimes by
    construction, never a global metric (`model.md` §4)."""
    keys = _pattern_keys(unit.pattern)
    if not keys:
        return 0.0
    return len(keys & attended_keys) / len(keys | attended_keys)


def retrieve(n: Network, seeds: tuple, candidates: tuple, *, reflect: Cell | None = None,
             hops: int = 2, theta: float = 0.3) -> tuple[tuple, Cell]:
    """RETRIEVE, cashed. For each candidate not already wired, score it against the attended region; wire
    it in — alongside any other candidate that also clears `theta`, never in place of one — if the score
    clears `theta`. Returns `(names_wired_this_call, reflect)`: pass the same `reflect` back in on the next
    call so the *same* reflective `Cell` gets refreshed rather than a new one minted (see module docstring,
    point 2).

    ⚠ **Interning here is simpler than `goal_machinery.md` §3's, and worth contrasting.** A `StandingUnit`
    only ever sees its own gates — it has no ambient read of `self.asserted`, which is exactly why a
    rule-level interning guard needs an explicit reflective axiom, managed across turns. The **outer
    driver** has no such tunnel: it reads `n.wires` directly, so "is this candidate already wired" is an
    ordinary Python check, not a pattern-matching problem. The tunnel is a property of units, not of every
    reader of the graph."""
    if reflect is None:
        reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    else:
        reflect.held = Value(effects_of(n.asserted))       # same Cell, same wire — refreshed contents
    already = {dst.name for _src, dst, _gate in n.wires}
    attended_keys = _attended_keys(n.asserted, attention(n.asserted, seeds, hops))
    wired: list = []
    for c in candidates:
        if c.name in already:
            continue
        if resemblance(c, attended_keys) >= theta:
            n.wire(reflect, c)                              # fan-out: many candidates, one source
            wired.append(c.name)
    return tuple(wired), reflect


def _candidates() -> tuple:
    mortal = StandingUnit("mortal_rule", (atom("x", kind="man"),), Attribute("x", "mortal", True))
    flight = StandingUnit("flight_rule", (atom("x", kind="bird"),), Attribute("x", "can_fly", True))
    return mortal, flight


def check_relevant_candidate_gets_wired_and_fires() -> dict[str, object]:
    """Socrates (`kind="man"`) is attended. `mortal_rule` needs `kind`, `flight_rule` needs `kind` too —
    ⚠ **both share the key `"kind"`, so both resemble equally by this crude scorer** (a stated limitation,
    not hidden): the scorer looks at attribute *keys* a pattern needs, not their *values*. Wired
    regardless of whether the *value* actually matches; `flight_rule` gets wired but never fires, because
    firing still goes through the ordinary, exact matcher once wired (System 2 stays exact)."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.given(g)
    mortal, flight = _candidates()
    n.add(mortal)
    n.add(flight)
    wired, _reflect = retrieve(n, seeds=(soc,), candidates=(mortal, flight))
    n.revive()
    return {"wired_this_call": wired,
            "mortal_fired": n.world().attr(soc, "mortal"),
            "flight_fired": n.world().attr(soc, "can_fly")}


def check_fan_out_multiple_candidates_share_one_source() -> dict[str, object]:
    """Both candidates above are wired from the *same* reflective `Cell` — fan-out, not one-wire-per-turn.
    `model.md` §7's *"a dangling gate is a standing trigger"* is why `flight_rule` staying wired-but-inert
    (it never fires, see above) is not a defect to clean up: leaving it wired costs nothing and means a
    later change to the graph (e.g. something concluding `kind="bird"` on some node) could make it fire
    without retrieval ever having to reconsider it."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.given(g)
    mortal, flight = _candidates()
    n.add(mortal)
    n.add(flight)
    retrieve(n, seeds=(soc,), candidates=(mortal, flight))
    sources = {s.name for s, d, _g in n.wires if d.name in ("mortal_rule", "flight_rule")}
    return {"distinct_sources_feeding_both_candidates": sources}


def check_irrelevant_candidate_stays_unwired() -> dict[str, object]:
    """A candidate needing a key nothing attended has stays below theta and is never wired — the honest
    cost of retrieval being allowed to be wrong: a real rule that *would* have applied never comes to
    mind, because nothing in the attended region resembles it (`model.md` §7's "price: no completeness")."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.given(g)
    weather_rule = StandingUnit("weather_rule", (atom("x", humidity="high"),),
                                 Attribute("x", "rain_likely", True))
    n.add(weather_rule)
    wired, _reflect = retrieve(n, seeds=(soc,), candidates=(weather_rule,))
    return {"wired_this_call": wired, "score": resemblance(weather_rule, _attended_keys(n.asserted, (soc,)))}


def check_retrieval_does_not_rewire_on_a_second_call() -> dict[str, object]:
    """Two `retrieve()` calls, same `Network`, same candidates, same reused `reflect`. Unlike
    `goal_machinery.md`'s rule-level interning (which needed axiom-lifecycle management because a *unit*
    has no ambient read), the outer driver reads `n.wires` directly — no tunnel to cross, so plain
    deduplication is enough."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.given(g)
    mortal, _flight = _candidates()
    n.add(mortal)
    first, reflect = retrieve(n, seeds=(soc,), candidates=(mortal,))
    second, _reflect = retrieve(n, seeds=(soc,), candidates=(mortal,), reflect=reflect)
    wire_count = sum(1 for _s, d, _g in n.wires if d.name == "mortal_rule")
    return {"wired_first_call": first, "wired_second_call": second, "wire_count": wire_count}


def check_reusing_one_reflective_cell_stays_flat_across_turns() -> dict[str, object]:
    """Three retrieval calls across three simulated turns, passing the *same* `reflect` `Cell` back each
    time instead of minting a fresh one. `self.axioms` and the wire count both stay flat — contrast with
    the measurement in `cnl_engine_goal_plan.md` §7f / memory, where minting a fresh reflective axiom every
    turn grew both by one each time, because `Network.axiom()` also writes the axiom's own node into the
    graph, so each new snapshot captured descriptions of every earlier one."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.given(g)
    mortal, _flight = _candidates()
    n.add(mortal)

    reflect = None
    axiom_counts: list = []
    wire_counts: list = []
    for _ in range(3):
        _wired, reflect = retrieve(n, seeds=(soc,), candidates=(mortal,), reflect=reflect)
        n.revive()
        axiom_counts.append(len(n.axioms))
        wire_counts.append(sum(1 for _s, d, _g in n.wires if d.name == "mortal_rule"))
    return {"axiom_count_per_turn": axiom_counts, "wire_count_per_turn": wire_counts}


def report() -> str:
    lines = ["=== SYSTEM 1 EXPERIMENT: a first associative-retrieval prototype ==="]
    lines.append(f"relevant candidate wired and fires: {check_relevant_candidate_gets_wired_and_fires()}")
    lines.append(f"fan-out, multiple candidates share one source: "
                 f"{check_fan_out_multiple_candidates_share_one_source()}")
    lines.append(f"irrelevant candidate stays unwired: {check_irrelevant_candidate_stays_unwired()}")
    lines.append(f"retrieval does not rewire on a second call: "
                 f"{check_retrieval_does_not_rewire_on_a_second_call()}")
    lines.append(f"reusing one reflective cell stays flat across turns: "
                 f"{check_reusing_one_reflective_cell_stays_flat_across_turns()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
