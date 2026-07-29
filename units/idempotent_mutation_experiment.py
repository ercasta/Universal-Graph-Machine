"""IDEMPOTENT MUTATION EXPERIMENT — does avoiding double-firing need new engine machinery, or does it
just need the right choice of *existing* rule shape? Raised in conversation as a refinement of
`nac_verification_experiment.py`'s "skolem-keyed mint" proposal: instead of a new engine primitive, use
the mutating/non-mutating split that already exists, plus an ordinary **positive state flip** in place of
a NAC, wherever there's a node the triggering fact can be marked "already handled" on.

**Two things checked, both against the real engine:**

1. **A sticky state transition (`case: new -> handled`) needs no NAC at all** — a mutating rule's own
   positive premise (`status="new"`) simply stops matching once the same rule's effect flips it, because
   the flip is written to `self.asserted` (the true base) at write-back, and every later revive's
   reflective snapshot is always built fresh from that same base (`effects_of(n.asserted)`, exactly as
   every experiment this session already does). No accumulation, no duplicate firing, no `absent(...)`.

2. **⭐ Correction to the framing raised in conversation, found while building this — "it's an event, so
   duplication is fine" is not quite right.** The proposal drew a line between "standing state
   transitions" (need dedup discipline) and "fire-and-forget events" (a customer complaint — assumed
   exempt, since two complaints really are two things). Checked directly: a rule that mints a `complaint`
   from a `signal` node, with no discipline at all, does **not** produce one complaint per distinct
   signal — it produces a **new** complaint from the **same** signal on every subsequent revive, because
   the signal itself persists in `self.asserted` and the rule's positive premise never stops matching it.
   That's unbounded, not "two events, two complaints" — `check_unmarked_signal_duplicates_without_bound`
   demonstrates it concretely (2 signals, 3 idle settle turns -> 5 complaints, still growing). The fix is
   the *same* discipline as (1), just scoped to the trigger rather than a domain "case": the rule must
   also mark its own signal `logged=True` in the same firing that mints the complaint
   (`check_marking_the_trigger_produces_exactly_one_complaint_per_signal`) — two *distinct* signals still
   correctly produce two distinct complaints (independent bindings), but each individual signal is
   consumed by the same firing that reacts to it, so it can never re-trigger. There is no third,
   dedup-exempt category for "events" — only whether the thing doing the triggering has, or does not
   have, its own consumption marker.

**What this settles about the original proposal:** no new engine primitive (no skolem-keyed `Emit`) is
needed for either case. `mutating=False` (a computation unit) already gives idempotency for free, by
discarding and recomputing its overlay from current gate content every revive
(`StandingUnit.clear()`/`fire()`) — the right shape for a defeasible, recomputed verdict
(`goal_machinery.md` §9's `assumed_safe`). `mutating=True` with a positive consumption-marker on the
trigger is the right shape for anything that must happen at most once per trigger, whether the mint is a
bare status flip or a brand-new record — an ordinary composition of what already exists, not a new kind.
NAC-based interning (`absent(...)`, `goal_experiment.py`'s lineage guard) remains the fallback for the one
case neither of these covers: minting something from scratch with no pre-existing node to mark consumed
(nothing to flip *before* the subgoal exists) — still used sparingly, exactly as already agreed.

Re-runnable: `python -m units.idempotent_mutation_experiment`.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Network, StandingUnit, Value, effects_of
from .graph import EMPTY, named
from .match import atom

_HANDLE_PAT = (atom("c", name="case", status="new"),)

_LOG_GOOD_PAT = (atom("s", name="signal", logged=None),)
_LOG_BAD_PAT = (atom("s", name="signal"),)


def _settle(n: Network, reflect) -> None:
    reflect.held = Value(effects_of(n.asserted))
    n.revive()


def _count(g, name: str) -> int:
    return sum(1 for node in g.nodes if g.attrs.get(node, {}).get("name") == name)


def check_sticky_transition_fires_exactly_once() -> dict[str, object]:
    """A mutating rule flips `status: new -> handled` and mints one `handling_event`. No NAC. Checked
    across several idle settle turns with no new input — the flip alone is enough to stop it firing
    again, because the rule's own positive premise (`status="new"`) no longer holds.

    ⚠ **Found live, while building this: `given`'s axiom must be nulled once `reflect` takes over, or
    this check reads a false conflict, not a bug in the state-flip discipline itself.** `Network._live()`
    (`engine.py:967`) treats *every* axiom's current `.held` as a permanently live reading, unconditional
    on wiring — so an un-nulled `given` axiom keeps re-asserting `status="new"` as a read-level overlay
    forever, even after `self.asserted` itself correctly shows `"handled"`. `View.attr` returns `None` on
    a genuine two-reading conflict (`overlay.py:441`), so without the null, `n.world().attr(case,
    "status")` reads `None` — not because the mutation failed (`n.asserted` already shows `"handled"`
    directly), but because the stale axiom and the true base disagree at the *read* layer. This is
    exactly the "recompute from a properly-retired base, not a stale one" hazard raised in conversation —
    caught here mechanically rather than only reasoned about. Fixed the same way
    `goal_experiment.py`'s corrected lineage check already does it: null `given`'s `.held` the moment
    `reflect` becomes the ongoing channel."""
    g, case = named(EMPTY, "case", status="new")
    n = Network()
    ax = n.given(g)
    handle = n.add(StandingUnit(
        "handle_case", _HANDLE_PAT,
        Attribute("c", "status", "handled"), Emit("handling_event", roles=(("about", "c"),)),
        mutating=True))
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, handle)
    ax.held = None                                    # stop the stale "new" from staying permanently live

    n.revive()
    counts = [_count(n.asserted, "handling_event")]
    for _ in range(3):
        _settle(n, reflect)
        counts.append(_count(n.asserted, "handling_event"))
    return {"status": n.world().attr(case, "status"), "handling_event_count_per_turn": counts}


def check_unmarked_signal_duplicates_without_bound() -> dict[str, object]:
    """⚠ The bug case, built deliberately to demonstrate the risk, not to recommend it. Two distinct
    signals arrive; the rule mints a `complaint` per match but never marks its own trigger consumed.
    Each signal keeps matching on every subsequent revive, so the complaint count grows every idle
    settle turn — unbounded, not "one complaint per real-world event."""
    n = Network()
    n.given(EMPTY)
    log_bad = n.add(StandingUnit("log_complaint_bad", _LOG_BAD_PAT,
                                  Emit("complaint", roles=(("from", "s"),)), mutating=True))
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, log_bad)

    for sig_name in ("signal1", "signal2"):
        n.asserted = named(n.asserted, "signal")[0]
        _settle(n, reflect)
    counts = [_count(n.asserted, "complaint")]
    for _ in range(3):
        _settle(n, reflect)
        counts.append(_count(n.asserted, "complaint"))
    return {"complaint_count_per_idle_turn": counts}


def check_marking_the_trigger_produces_exactly_one_complaint_per_signal() -> dict[str, object]:
    """The fix: the rule also marks its own signal `logged=True` in the same firing. Two distinct
    signals still correctly produce two distinct complaints (independent bindings) — but each one stops
    matching the instant it's consumed, so idle settle turns never add more."""
    n = Network()
    n.given(EMPTY)
    log_good = n.add(StandingUnit(
        "log_complaint_good", _LOG_GOOD_PAT,
        Attribute("s", "logged", True), Emit("complaint", roles=(("from", "s"),)), mutating=True))
    reflect = n.axiom(*effects_of(n.asserted), name="reflect")
    n.wire(reflect, log_good)

    for sig_name in ("signal1", "signal2"):
        n.asserted = named(n.asserted, "signal")[0]
        _settle(n, reflect)
    counts = [_count(n.asserted, "complaint")]
    for _ in range(3):
        _settle(n, reflect)
        counts.append(_count(n.asserted, "complaint"))
    return {"complaint_count_per_idle_turn": counts}


def report() -> str:
    lines = ["=== IDEMPOTENT MUTATION EXPERIMENT: state-flip discipline vs. a new engine primitive ==="]
    lines.append(f"sticky transition, fires exactly once: {check_sticky_transition_fires_exactly_once()}")
    lines.append(f"unmarked trigger duplicates without bound (the bug): "
                 f"{check_unmarked_signal_duplicates_without_bound()}")
    lines.append(f"marked trigger -> exactly one complaint per signal: "
                 f"{check_marking_the_trigger_produces_exactly_one_complaint_per_signal()}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
