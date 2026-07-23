"""ACCUMULATOR PROBE — the governor's counter as SUBSTRATE, not a Python register.

Findings that shape it (probed 2026-07-23):
  - the rule surface exposes only `!=` (distinctness); there is NO native numeric `>=` in a rule, so a
    THRESHOLD COMPARISON goes through the §8 calculator/tool boundary (the `rank`-calculator precedent:
    "the tool only does the arithmetic", deriving FACTS the banks select on);
  - attribute-setting is non-monotone and fine (user) — so the ACCUMULATOR is a VALUED `flare_count`
    attribute on the reified goal node, incremented per event (mechanism, like the dirty set).

So the layering, vision-true:
  ACCUMULATOR   = `flare_count` VALUED attr on the goal node        (substrate data; non-monotone set)
  THRESHOLD     = a declared FACT `<g> flare_limit N`               (data — swappable, no code change)
  TALLY (tool)  = reads count + limit, derives `<g> reached_limit yes`  (the ARITHMETIC boundary, only)
  RECOVERY      = a RULE on `reached_limit` (composes w/ authoritativeness)  (data + rules)

Only the tally is Python, and only for arithmetic — every DECISION (threshold value, what to recover to,
whose advice wins) is data+rules, so it all composes.
"""
from __future__ import annotations

from ugm import AttrGraph
from ugm.attrgraph import valued
from ugm.machine import Machine, MINT, State
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal

YES = "yes"


def _goal_node(kb, name):
    got = kb.nodes_named(name)
    if got:
        return got[0]
    return Machine().apply(kb, [MINT("_g", attrs={"name": valued(name)})], State({})).regs["_g"]


# --- ACCUMULATOR: a non-monotone VALUED attribute, bumped per event (mechanism, à la mark_dirty) --------
def bump(kb, goal_name):
    g = _goal_node(kb, goal_name)
    a = kb.get_attr(g, "flare_count")
    n = (int(a.value) if a is not None else 0) + 1
    kb.set_attr(g, "flare_count", valued(n))          # non-monotone SET — the user's unblock
    return n


# --- TALLY: the ARITHMETIC boundary (a §8 calculator). Reads count + the DECLARED limit fact, derives the
#     crossing FACT `<g> reached_limit yes`. No threshold value baked in — it is read from data. ------------
def tally(kb):
    yes = kb.nodes_named(YES)[0] if kb.nodes_named(YES) else kb.add_node(YES)
    for g in list(kb.nodes()):
        cnt = kb.get_attr(g, "flare_count")
        if cnt is None:
            continue
        limit = next((int(kb.name(o)) for r, o in kb.relations_from(g)
                      if kb.predicate(r) == "flare_limit"), None)
        if limit is not None and int(cnt.value) >= limit \
                and not any(kb.predicate(r) == "reached_limit" for r in kb.out(g)):
            kb.add_relation(g, "reached_limit", yes)   # the crossing, derived as DATA a rule selects on


def _num_node(kb, n):
    got = kb.nodes_named(str(n))
    return got[0] if got else kb.add_node(str(n))


def run(threshold, *, acts):
    kb = AttrGraph()
    goal = "stuck_goal"
    g = _goal_node(kb, goal)
    kb.add_relation(g, "flare_limit", _num_node(kb, threshold))       # THRESHOLD declared as DATA
    # RECOVERY is a RULE (not Python): abandon a goal that reached its limit; don't re-attempt an abandoned one.
    recovery = load_machine_rules(f"?g abandoned {YES} when ?g reached_limit {YES}")

    attempts = 0
    for _ in range(acts):
        if ask_goal(kb, ("yesno", goal, "abandoned", YES), recovery) == ["yes"]:
            break                                                    # recovery fired -> loop terminates
        bump(kb, goal)                                               # the hard goal flares again
        attempts += 1
        tally(kb)                                                    # arithmetic boundary derives crossing
    final_count = int(kb.get_attr(g, "flare_count").value)
    abandoned = ask_goal(kb, ("yesno", goal, "abandoned", YES), recovery) == ["yes"]
    return attempts, abandoned, final_count


def main():
    a3, ab3, c3 = run(3, acts=10)
    a5, ab5, c5 = run(5, acts=10)                                    # SAME code, different DATA (the limit fact)
    print(f"  limit=3 : {a3} attempts, abandoned={ab3}, count peaked {c3}")
    print(f"  limit=5 : {a5} attempts, abandoned={ab5}, count peaked {c5}  (changed by DATA alone)")
    print("=" * 60)
    ok = (a3 == 3 and ab3) and (a5 == 5 and ab5)
    print(f"ACCUMULATOR: {'GO — counter is substrate data; threshold+recovery are data+rules; only arithmetic is a tool'
                          if ok else 'GAP'}")


if __name__ == "__main__":
    main()
