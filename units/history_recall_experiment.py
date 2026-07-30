"""HISTORY RECALL EXPERIMENT — does multi-turn conversational context need a new "breadcrumb" structure
and a dedicated walking metaprocedure, or does `model.md` §7 already cover it?

**The question this probes, stated precisely.** A prior turn's content is already never thrown away
(`model.md` §1: data is the substrate). So "remembering the conversation" is not a storage problem. The
open question was whether *reaching back into it on demand* — a subgoal like "what did we say about the
wiper kit?" — needs new machinery: a materialized pointer-chain ("breadcrumb") plus a bespoke procedure
that walks it, auto-triggered by a recognised subgoal shape.

**What this probe finds:** no. Three ordinary pieces already licensed by `model.md`, combined, are enough:

1. **Turns are ordinary standing nodes**, linked by an ordinary `follows` edge to the previous turn's root
   — declared graph structure, not a new kind (§11 "guards yes, kinds no"). `attention()`'s BFS
   (`units/system1_experiment.py`) already walks any edge, so a `follows` chain costs nothing new — see
   `check_follows_chain_reaches_history_with_only_more_hops` below.
2. **A recall subgoal is an ordinary act of attention** (§7: *"a rule can conclude attend to X, and a
   retrieval hint is just an act of attention"*). It does not need to be auto-recognised by a new trigger
   type; it just needs to widen the seed set System 1 already uses.
3. **Which prior turn to jump to is a *second*, differently-authored resemblance score** (§4: "similarity
   is authored, not global" — there is no single similarity metric, only ones a rule chooses). Candidate
   *rule* retrieval scores attribute-*key* overlap against the attended region (`system1_experiment.py`'s
   `resemblance()`). Picking a *prior turn* by topic is a different job and gets its own scorer,
   `topic_match()` below: value-equality on a `topic` tag, over a small **turn-root index** (one node per
   turn, not the whole graph) — so a long conversation costs the scorer O(turns), never O(graph). This
   directly answers the earlier growth worry: the index that must be scanned to find the right turn does
   not grow with turn *content*, only with turn *count*.

**What this is not:** a working-set/decay policy for when a turn should stop being a candidate at all
(`model.md` §7's attention-leak, §13) — deliberately out of scope here, same discipline as
`system1_experiment.py`'s own "what this is not."

Re-runnable: `python -m units.history_recall_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Network, StandingUnit
from .graph import EMPTY, Graph, named
from .match import atom
from .system1_experiment import _attended_keys, attention, resemblance, retrieve


def _three_turns() -> tuple[Graph, dict[str, object]]:
    """Turn 1: the wiper kit. Turn 2: the weather — unrelated, and more recent. Turn 3 (current): a recall
    subgoal about the wiper kit — topically close to turn 1, not turn 2, so a recency-based walk and a
    topic-based jump would disagree, which is the point: this data is built so the two strategies can be
    told apart, not so they agree by accident."""
    g = EMPTY
    g, turn1 = named(g, "turn1", is_turn_root=True, topic="wiper_kit")
    g, kit = named(g, "kit_a", kind="wiper_kit", compatible="modelX")
    g = g.with_edge(turn1, kit)

    g, turn2 = named(g, "turn2", is_turn_root=True, topic="weather")
    g, sky = named(g, "sky", kind="weather", humidity="high")
    g = g.with_edge(turn2, sky)
    g = g.with_edge(turn2, turn1)                              # follows: turn2 -> turn1

    g, turn3 = named(g, "turn3", is_turn_root=True, topic="query")
    g, query = named(g, "recall_query", kind="recall", about="wiper_kit")
    g = g.with_edge(turn3, query)
    g = g.with_edge(turn3, turn2)                              # follows: turn3 -> turn2

    nodes = {"turn1": turn1, "kit": kit, "turn2": turn2, "sky": sky, "turn3": turn3, "query": query}
    return g, nodes


def turn_root_index(g: Graph) -> tuple:
    """The small, turn-count-sized set a topic jump scores against — never the whole graph. Bounded by
    however many turns happened, which is what keeps a long conversation's *recall* cost flat even as its
    *content* grows."""
    return tuple(n for n in g.nodes if g.attr(n, "is_turn_root"))


def topic_match(query: object, turn_root: object, g: Graph) -> float:
    """A second, differently-authored resemblance score (`model.md` §4) — not `system1_experiment.resemblance`
    reused, a deliberately different one for a deliberately different job. Candidate-rule retrieval asks
    "does this rule's *shape* overlap the attended keys"; this asks "is this turn *about* what the query is
    about" — value-equality on a `topic` tag, crude and honest exactly the way `resemblance()` is."""
    about = g.attr(query, "about")
    topic = g.attr(turn_root, "topic")
    return 1.0 if about is not None and about == topic else 0.0


def select_turn(query: object, roots: tuple, g: Graph, *, theta: float = 0.5) -> object | None:
    scored = [(r, topic_match(query, r, g)) for r in roots]
    best = max(scored, key=lambda pair: pair[1], default=(None, 0.0))
    return best[0] if best[1] >= theta else None


def _kit_rule() -> StandingUnit:
    return StandingUnit("kit_lookup_rule", (atom("x", kind="wiper_kit"),), Attribute("x", "recalled", True))


def check_prior_turn_content_persists_untouched() -> dict[str, object]:
    """Nothing about turn 1 is retracted or archived once turn 2 and turn 3 happen — `model.md` §1's "data
    is the substrate" needs no confirmation really, but the multi-turn framing makes it worth stating
    plainly: this is not a storage feature to build, it is what not deleting anything already gives you."""
    g, nd = _three_turns()
    return {"kit_kind_after_three_turns": g.attr(nd["kit"], "kind"),
            "sky_kind_after_three_turns": g.attr(nd["sky"], "kind")}


def check_default_local_attention_does_not_reach_history() -> dict[str, object]:
    """Seeded only from the *current* turn's own nodes, with an ordinarily-small hop count, retrieval never
    reaches turn 1's content — `model.md` §7's "price: no completeness" applies to conversation history
    exactly the way it applies to anything else attention doesn't reach. This is not a bug to fix; it is
    what keeps a long conversation's retrieval cost from scaling with its length by default."""
    g, nd = _three_turns()
    n = Network()
    n.given(g)
    n.add(_kit_rule())
    wired, _reflect = retrieve(n, seeds=(nd["turn3"], nd["query"]), candidates=(_kit_rule(),), hops=1)
    attended = attention(n.asserted, (nd["turn3"], nd["query"]), hops=1)
    return {"wired_this_call": wired, "kit_node_in_attended_region": nd["kit"] in attended}


def check_recall_subgoal_selects_by_topic_not_recency() -> dict[str, object]:
    """Turn 2 (weather) is more recent than turn 1 (wiper kit); the query is about the wiper kit. A
    recency-based walk (just follow `follows` one hop back) would land on turn 2 and miss. The topic
    scorer, run over the small turn-root index rather than a walk, lands on turn 1 directly — confirming
    the earlier design point that this should be *topic-driven*, not *"walk back N turns."*"""
    g, nd = _three_turns()
    roots = turn_root_index(g)
    selected = select_turn(nd["query"], roots, g)
    return {"turn_roots_considered": len(roots), "selected_is_turn1": selected is nd["turn1"],
            "selected_is_turn2": selected is nd["turn2"]}


def check_widening_the_seed_lets_the_candidate_wire_and_fire() -> dict[str, object]:
    """The recall subgoal's only effect on retrieval is an extra seed — exactly `model.md` §7's "a
    retrieval hint is just an act of attention," nothing auto-triggered by recognising the subgoal's shape.
    Once turn 1 is in the seed set, ordinary System 1 (`system1_experiment.retrieve`) reaches `kit_a`'s
    real attributes, the candidate clears theta, wires, and — System 2 staying exact — actually fires."""
    g, nd = _three_turns()
    n = Network()
    n.given(g)
    rule = _kit_rule()
    n.add(rule)
    roots = turn_root_index(n.asserted)
    selected = select_turn(nd["query"], roots, n.asserted)
    seeds = (nd["turn3"], nd["query"], selected)
    # theta lowered from system1_experiment's default 0.3: a turn's own bookkeeping keys (is_turn_root,
    # topic, name) dilute the Jaccard score once several turn-roots are in the seed set at once — an
    # honest tuning knob (`model.md` §4: theta is authored, never global), not a special case for history.
    wired, _reflect = retrieve(n, seeds=seeds, candidates=(rule,), hops=1, theta=0.15)
    n.revive()
    return {"selected_turn_is_turn1": selected is nd["turn1"],
            "wired_this_call": wired,
            "kit_recalled": n.world().attr(nd["kit"], "recalled")}


def check_follows_chain_reaches_history_with_only_more_hops() -> dict[str, object]:
    """The complementary, recency-style strategy — "what did we just say" rather than "what did we say
    about X" — needs no separate mechanism either: `follows` is an ordinary edge, so plain BFS with a
    larger hop count reaches all the way back to turn 1 with zero new machinery. Both retrieval styles
    (topic-jump via the small index, recency-walk via `follows`) are the *same* `attention()` function,
    seeded or bounded differently — never two mechanisms."""
    g, nd = _three_turns()
    shallow = attention(g, (nd["turn3"],), hops=2)
    deep = attention(g, (nd["turn3"],), hops=5)
    return {"turn1_reachable_at_hops_2": nd["turn1"] in shallow,
            "turn1_reachable_at_hops_5": nd["turn1"] in deep,
            "kit_reachable_at_hops_5": nd["kit"] in deep}


def report() -> str:
    lines = ["=== HISTORY RECALL EXPERIMENT: multi-turn context needs no new kind ==="]
    lines.append(f"prior turn content persists untouched: {check_prior_turn_content_persists_untouched()}")
    lines.append(f"default local attention does not reach history: "
                 f"{check_default_local_attention_does_not_reach_history()}")
    lines.append(f"recall subgoal selects by topic, not recency: "
                 f"{check_recall_subgoal_selects_by_topic_not_recency()}")
    lines.append(f"widening the seed lets the candidate wire and fire: "
                 f"{check_widening_the_seed_lets_the_candidate_wire_and_fire()}")
    lines.append(f"follows chain reaches history with only more hops: "
                 f"{check_follows_chain_reaches_history_with_only_more_hops()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
