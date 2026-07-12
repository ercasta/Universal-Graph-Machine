"""
The firmware STANCE, as declared data (`docs/architecture.md`, the engine developer guide).

The substrate (`attrgraph.py`) and the engine (`machine.py` / `lowering.run_bank` / `chain.chain_sip`)
are GENERIC and stance-free: they know no domain and take no position on how to read absence or what
to do with a negation cycle. Those are FIRMWARE opinions — the layer that turns the generic reasoner
into an opinionated one. This module makes those opinions DECLARED DATA rather than forked Python, so a
DIFFERENT firmware activates by swapping a `FirmwarePolicy`, the same way per-predicate openness was
already data (`open_preds`). It is the "stance" extension point in the layering: generic substrate →
generic engine → tools → rule banks → **stance**.

Two opinions live here today:

  - `negation_default` — how CHECK / `ask_goal` read an UNPROVABLE goal's absence (vision §6a,
    memory `decision-cwa-default`). `"closed"` (CWA, the default) reads absence as a defeasible
    ASSUMED_NO; `open_preds` are the per-concept OWA exceptions (there absence is UNKNOWN — gather
    evidence). `"open"` (OWA) flips the default to UNKNOWN; `closed_preds` are the CWA exceptions.

  - `on_cycle` — what a LOADER does when a bank's negation is NON-stratifiable (vision §11). `"raise"`
    (the default) rejects at load (`lint_stratifiable`) — a static defect the author should see at
    once. `"degrade"` skips the load-time raise so the FORWARD path (`run_rules`, which already
    degrades) drops the NAF rules and reasons with the monotone subset. NOTE: the demand-driven chain
    (`chain_sip`) assumes stratification for soundness (see `chain.py`'s module note), so `"degrade"`
    is a forward-path graceful fallback, not a licence to answer a cyclic bank on demand.
"""
from __future__ import annotations

from dataclasses import dataclass

# The allowed values (kept as named constants so a linter/guide can enumerate them).
CLOSED, OPEN = "closed", "open"          # negation_default
RAISE, DEGRADE = "raise", "degrade"      # on_cycle


@dataclass(frozen=True)
class FirmwarePolicy:
    """A reasoning firmware's opinionated stances as one immutable, declared object. Default
    construction == the shipped stance (closed-world default, reject negation cycles at load), so a
    caller that passes nothing gets exactly today's behaviour."""
    negation_default: str = CLOSED
    open_preds: frozenset[str] = frozenset()      # OWA exceptions when the default is closed
    closed_preds: frozenset[str] = frozenset()    # CWA exceptions when the default is open
    on_cycle: str = RAISE

    def is_open(self, concept: str) -> bool:
        """Is `concept` OPEN-world under this policy — i.e. does absence read as UNKNOWN (gather) rather
        than a decided ASSUMED_NO? Closed-default: only the `open_preds` exceptions are open. Open-
        default: everything except the `closed_preds` exceptions is open."""
        if self.negation_default == OPEN:
            return concept not in self.closed_preds
        return concept in self.open_preds


# The shipped default stance — importable so entry points can default to it and a `replace()` can
# tweak one field without restating the rest.
DEFAULT_POLICY = FirmwarePolicy()
