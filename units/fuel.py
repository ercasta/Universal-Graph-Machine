"""FUEL — the bound on assembly (`docs/design/substrate_inversion.md` §6, §6b).

Why this is a module and not an integer. §6 splits negation in two, and the split is the whole reason fuel
exists here:

  **(a) NAF over the value on a wire** — `match.Absent`. The value that arrived is FINISHED, so absence is
  decidable immediately: no drain, no fixpoint, no fuel. This is the negation the substrate gets for free,
  and it should be preferred wherever a design can arrange it.

  **(b) NAF over the OPEN DERIVATION** — *"P is not derivable at all"*. Semi-decidable in any system. You
  are not done until you stop adding units, so the honest answer is a BUDGET, and an exhausted budget
  yields UNKNOWN rather than "no" ([[think-harder-chapter]], [[agent-not-theorem-prover]]). "Let me think
  again about it" is then literally *assemble more*.

**THE COST, DECLARED RATHER THAN DISCOVERED** (§6, and it is a real breach). Fuel-bounded NAF lets
SCHEDULING POLICY LEAK INTO SEMANTICS: how much fuel, spent in what order, determines what the system
believes. `execution_topology.md` §8 forbids exactly this in its own domain. It is defensible only because
(b) is irreducibly resource-bounded, and only if a (b)-conclusion is MARKED as provisional — which is why
`Verdict` exists and why `UNKNOWN` is not spelled `False`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(Enum):
    """The answer to an open question. `UNKNOWN` is a first-class outcome, never a synonym for NO."""
    YES = "yes"
    NO = "no"                    # sound only when reached WITHOUT exhausting the budget
    UNKNOWN = "unknown"          # the budget ran out — more fuel might change this

    def __bool__(self):          # refuse the truthiness that would silently collapse UNKNOWN into NO
        raise TypeError("a Verdict is three-valued — compare explicitly (UNKNOWN is not NO)")


@dataclass
class Budget:
    """A spend-down counter over ASSEMBLY and PROPAGATION steps.

    One budget covers both because they are the same resource from the caller's point of view: a network
    that will not settle and a network that keeps growing are indistinguishable from outside, and both
    must end in UNKNOWN rather than a hang."""
    limit: int = 1000
    spent: int = 0
    spawns: int = 0
    rounds: int = 0
    _reasons: list = field(default_factory=list)

    def spend(self, n: int = 1, why: str = "") -> bool:
        """Consume `n`. Returns False once exhausted — callers STOP, they do not raise, because running
        out of fuel is an ordinary outcome and not an error."""
        self.spent += n
        if why:
            self._reasons.append(why)
        return not self.exhausted

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.limit

    def verdict(self, found: bool) -> Verdict:
        """Turn a search outcome into an honest answer. **The only place NO is licensed is a search that
        finished with fuel to spare** — otherwise absence is ignorance, not evidence."""
        if found:
            return Verdict.YES
        return Verdict.UNKNOWN if self.exhausted else Verdict.NO

    def __repr__(self) -> str:
        return (f"<Budget {self.spent}/{self.limit} rounds={self.rounds} spawns={self.spawns}"
                f"{' EXHAUSTED' if self.exhausted else ''}>")
