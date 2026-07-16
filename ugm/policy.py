"""
The firmware STANCE, as declared data (`docs/architecture.md`, the engine developer guide).

The substrate (`attrgraph.py`) and the engine (`machine.py` / `lowering.run_bank` / `chain.chain_sip`)
are GENERIC and stance-free: they know no domain and take no position on how to read absence or what
to do with a negation cycle. Those are FIRMWARE opinions — the layer that turns the generic reasoner
into an opinionated one. This module makes those opinions DECLARED DATA rather than forked Python, so a
DIFFERENT firmware activates by swapping a `FirmwarePolicy`, the same way per-predicate openness was
already data (`open_preds`). It is the "stance" extension point in the layering: generic substrate →
generic engine → tools → rule banks → **stance**.

Four opinions live here today:

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

  - `uncertainty` — how reasoning READS the possibilistic forks (docs/possibilistic.md S6/S7): the
    GLOBAL opt-in for banded reasoning, a firmware stance flipped once per session, never per call
    (ratified 2026-07-16). `"silent"` (the default) is silent-until-assumed: a fork is INVISIBLE to
    certain-world reasoning unless its scope is entered (today's behaviour, byte-identical).
    `"banded"` is marker mode: every read sees ink at CERTAIN plus EVERY fork's pencil at its
    `<likeliness>` band; derivations min-accumulate the weakest link, carry their assumption
    ENVIRONMENT, NAF becomes the θ-cut below, and uncertain conclusions are emitted as derived
    forks. It cannot be automatic-on-forks: silent-until-assumed is load-bearing (uncertainty must
    not leak into crisp queries just because the graph contains forks).

  - `theta` — the possibilistic NAF α-cut, the BIAS-vs-DECISIVENESS dial (docs/possibilistic.md
    S7.3; open-point I cashed out). In marker-mode reasoning (`possibility.py`) `not P` blocks iff P
    is reachable at band ≥ θ: HIGH θ ignores low-possibility alternatives (decisive, bias-prone);
    LOW θ refuses to lean on an absence while the positive is even slightly possible (cautious).
    Range (0, 1]; the default 0.5 blocks a negation exactly when the counter-evidence is at least
    `likely` — so an even `either…or` alternative (band 0.5) blocks, a merely `unlikely` one (0.3)
    does not. Crisp reasoning never reads it (no forks ⇒ every Π is 0 or 1, and any θ in range
    behaves classically).
"""
from __future__ import annotations

from dataclasses import dataclass

# The allowed values (kept as named constants so a linter/guide can enumerate them).
CLOSED, OPEN = "closed", "open"          # negation_default
RAISE, DEGRADE = "raise", "degrade"      # on_cycle
SILENT, BANDED = "silent", "banded"      # uncertainty


@dataclass(frozen=True)
class FirmwarePolicy:
    """A reasoning firmware's opinionated stances as one immutable, declared object. Default
    construction == the shipped stance (closed-world default, reject negation cycles at load), so a
    caller that passes nothing gets exactly today's behaviour."""
    negation_default: str = CLOSED
    open_preds: frozenset[str] = frozenset()      # OWA exceptions when the default is closed
    closed_preds: frozenset[str] = frozenset()    # CWA exceptions when the default is open
    on_cycle: str = RAISE
    uncertainty: str = SILENT                     # fork read: silent-until-assumed | banded marker mode
    theta: float = 0.5                            # possibilistic NAF α-cut (bias dial), range (0, 1]

    def __post_init__(self):
        if self.uncertainty not in (SILENT, BANDED):
            raise ValueError(f"uncertainty must be {SILENT!r} or {BANDED!r}, got {self.uncertainty!r}")
        if not (0.0 < self.theta <= 1.0):
            raise ValueError(f"theta must be in (0, 1], got {self.theta!r}")

    @property
    def banded(self) -> bool:
        """Is marker-mode (banded) reading on under this policy? The one flag the engine branches on."""
        return self.uncertainty == BANDED

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


# --- the stance meta-lines (docs/possibilistic.md polish item, built 2026-07-16) -----------------
#
# `be cautious` / `be decisive` — the θ dial as CNL, the same dial the book/playground expose as a
# checkbox. The words are DECLARED DATA (this table), never engine sniffing: intake recognizes the
# `be <word>` FORM (§D.2, like the focus ops) and resolves the word here; an unknown word is simply
# not a stance line and routing continues. Both stances opt into the BANDED reading — asking for a
# jump attitude only means something in the world of shades (and its verdicts then honestly wear
# their kind, e.g. `no (assumed)`).
STANCES: dict[str, FirmwarePolicy] = {
    "cautious": FirmwarePolicy(uncertainty=BANDED, theta=0.2),
    "decisive": FirmwarePolicy(uncertainty=BANDED, theta=0.5),
}


def recognize_stance(utterance: str) -> FirmwarePolicy | None:
    """If `utterance` is a stance meta-line (`be cautious` / `be decisive`), the `FirmwarePolicy` it
    declares — else None. Recognized by which FORM fires over the token chain (never a string sniff),
    with the word resolved through the declared `STANCES` table."""
    from .production_rule import Pat, Rule
    from .cnl.forms import tokenize
    from .lowering import run_bank
    from .world_model import Graph
    form = Rule(key="stance.be",
                lhs=[Pat("?s", "first", "be?"), Pat("be?", "next", "?w")],
                rhs=[Pat("<stance>?", "word", "?w")])
    tmp = Graph()
    tokenize(tmp, utterance)
    run_bank(tmp, [form])
    for nid in tmp.nodes():
        if tmp.name(nid) == "<stance>":
            for rel, obj in tmp.relations_from(nid):
                if tmp.has_key(rel, "word"):
                    return STANCES.get(tmp.name(obj))
    return None
