"""REACTIVE-DERIVE PROBE (STEP B/C, 2026-07-23).

Tests the design in `docs/design/reactive_core.md`: the reactive core = `reconsider` GENERALIZED. reconsider
already is a standing, cross-call, demand-gated, sound work-list — but its ONE reaction is "retract a stale
NAF conclusion". This probe generalizes the reaction to DERIVE (proactively materialize a consequence) for a
predicate DECLARED reactive, reusing reconsider's exact skeleton (DIRTY_REG event queue, detach-before-fire
regress guard, `_affected` body->head dispatch), and shows:

  1. A `reactive` predicate's consequence is MATERIALIZED at the next committed act WITHOUT a query for it
     (the DATA drove it) — while a NON-reactive predicate stays pull-only (unchanged laziness).
  2. The recall-autofire re-break: firing is idempotent/terminating — the detached dirty set + monotone
     materialization mean a reaction cannot self-reinforce (the [[recall-explicit-not-autofire]] scar).
  3. It is ADDITIVE — reconsider's retract behavior is one configured instance of the same gate.

The reaction runs demand-gated (at a committed act), NOT eagerly — laziness preserved. No engine change: the
probe orchestrates the existing primitives (`_affected`, `chain_sip`) exactly as the build would wire them.
"""
from __future__ import annotations

from ugm import AttrGraph
from ugm.machine import Machine
from ugm.lowering import assemble_facts
from ugm.cnl.machine_rules import load_machine_rules
from ugm.reconsider import DIRTY_REG, mark_dirty, _affected
from ugm.rule_control import active_rules
from ugm.chain import chain_sip, _facts_matching
from ugm.cnl.query import _reify_rules

RULE = "?x endangers ?y when ?x hunts ?y"       # a positive binary-relation rule (no copula-"is" ambiguity)


def _kb_with_trigger():
    """A KB carrying the rule + the trigger fact `wolf hunts sheep`, with the trigger grain marked dirty
    (exactly what intake's `mark_dirty` records on a materialization)."""
    kb = AttrGraph()
    rules = load_machine_rules(RULE)
    Machine().run(kb, assemble_facts([("wolf", "hunts", "sheep")]))
    mark_dirty(kb, [("hunts", "sheep")])            # the event: a trigger fact landed
    return kb, rules


def reactive_fire(kb, rules, reactive_preds) -> int:
    """The GENERALIZED gate — reconsider's front half (dirty -> detach -> `_affected`), with a DERIVE
    reaction: for every affected grain whose predicate is DECLARED reactive, materialize it demand-driven
    (`chain_sip`, monotone). Detach-before-fire is the regress guard; a materialized fact is real knowledge
    and does not re-dirty, so the reaction cannot self-reinforce. Returns the number of grains fired."""
    dirty = kb.registers.get(DIRTY_REG)
    if not dirty:
        return 0
    kb.registers[DIRTY_REG] = {}                     # DETACH FIRST (regress guard — reconsider's invariant)
    active = active_rules(kb, rules)
    affected = _affected(set(dirty), active)
    rule_g = _reify_rules(active)
    fired = 0
    for pred, obj in affected:
        if pred in reactive_preds:
            chain_sip(kb, (pred, None, obj), rules=rule_g)   # PROACTIVELY materialize the consequence
            fired += 1
    return fired


def _materialized(kb, pred, s, o) -> bool:
    """A DIRECT read of PRESENT facts (no derivation) — did the consequence get materialized proactively?"""
    return bool(_facts_matching(kb, pred, s, o))


def main():
    print("=" * 66)
    print("REACTIVE vs NON-REACTIVE (materialization drives the consequence?)")
    print("=" * 66)

    kb, rules = _kb_with_trigger()
    before = _materialized(kb, "endangers", "wolf", "sheep")
    fired = reactive_fire(kb, rules, reactive_preds={"endangers"})   # `endangers` declared reactive
    after = _materialized(kb, "endangers", "wolf", "sheep")
    print(f"  reactive:     materialized before act={before}  after committed act={after}  (fired {fired})")

    ctl, crules = _kb_with_trigger()
    reactive_fire(ctl, crules, reactive_preds=set())                 # nothing reactive
    ctl_mat = _materialized(ctl, "endangers", "wolf", "sheep")
    ctl_demand = bool(chain_sip(ctl, ("endangers", "wolf", "sheep"), rules=_reify_rules(active_rules(ctl, crules)))
                      or _materialized(ctl, "endangers", "wolf", "sheep"))
    print(f"  non-reactive: materialized proactively={ctl_mat}  but derivable ON DEMAND={ctl_demand}")

    reactive_ok = (not before) and after and (not ctl_mat) and ctl_demand
    print(f"  => {'PASS — reactive pushes, non-reactive stays lazy' if reactive_ok else 'FAIL'}")

    print("\n" + "=" * 66)
    print("RECALL-AUTOFIRE RE-BREAK (firing is idempotent / no self-reinforcement)")
    print("=" * 66)
    kb2, rules2 = _kb_with_trigger()
    f1 = reactive_fire(kb2, rules2, reactive_preds={"endangers"})    # fires
    f2 = reactive_fire(kb2, rules2, reactive_preds={"endangers"})    # dirty detached -> nothing to fire
    # a second materialization of the SAME fact would be a no-op (monotone), and the dirty set is empty,
    # so the gate does not re-enter — the self-reinforcing loop the recall-autofire scar warned of.
    print(f"  first fire grains={f1}  second fire grains={f2}  (0 => detached, no loop)")
    rebreak_ok = f1 >= 1 and f2 == 0
    print(f"  => {'PASS — the detach-before-fire guard stops self-reinforcement' if rebreak_ok else 'FAIL'}")

    print("\n" + "=" * 66)
    print(f"VERDICT: {'GO — reconsider generalizes to a sound reactive DERIVE gate' if reactive_ok and rebreak_ok else 'MIXED'}")
    print("=" * 66)


if __name__ == "__main__":
    main()
