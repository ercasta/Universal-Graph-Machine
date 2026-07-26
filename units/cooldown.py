"""COOLDOWN — a bounded suppression of re-derivation (a deliberate approximation).

**The problem it answers.** Every step re-mints its conclusions as fresh nodes, and the duplicated
premises then multiply the matches, so the persistent graph grows faster than the step count
(`tests/units/test_loop.py::test_conclusions_accrete_superlinearly_across_steps`). `model.md` §5's
*"a repeat arrival is a firing… no notion of quiescence"* is right inside one circuit run and wrong
across steps.

**Why this shape rather than keyed minting.** `ugm` solved the same problem with `0014` (*anything
minted per run must be keyed*), which makes a conclusion's identity a function of its content. That is
in direct tension with `cnl.md` §1: identity is supposed to be a **rule's graded decision**, never
something the machinery performs behind the rules' backs. A cooldown avoids the tension because it
never says two things are the same — it just **declines to fire again**. Nothing is merged, nothing is
identified, and the conclusion that already exists stays exactly as it was.

**It is approximate, and the approximations are the point:**

- **Bounded.** Old entries evict, so a suppressed derivation *can* reappear later. Growth is slowed,
  not stopped.
- **Order-dependent.** What is suppressed depends on what fired first and on the list's size.

⚠ **The declared cost: scheduling policy leaks into semantics.** How big the list is, and in what order
things fired, changes what the system concludes. `units/fuel.py` (deleted) flagged the identical breach
for fuel-bounded negation, and `execution_topology.md` §8 forbids it in its own domain. It is accepted
here for the same reason: the alternative is unbounded growth. It is defensible only while it stays
**declared** rather than discovered — hence this docstring, and hence `Cooldown.evictions`, so that a
run can *tell you* it dropped something.
"""
from __future__ import annotations

from collections import OrderedDict


def _state(g, n) -> tuple:
    """A fingerprint of everything the graph currently says about one node.

    Attributes and degrees only — **not** edges. A node's edges are how the rest of the graph reaches
    it, and including them would make almost every firing look novel (anything minted nearby touches
    some neighbour), which would defeat the cooldown entirely. Attributes are what a pattern actually
    reads, so this is the state a match depended on."""
    return (tuple(sorted(g.attrs.get(n, {}).items(), key=lambda kv: kv[0])),
            tuple(sorted(g.degrees.get(n, {}).items(), key=lambda kv: kv[0])))


class Cooldown:
    """A bounded set of recently-fired `(rule, bound nodes)` keys, oldest evicted first.

    Central by design: one list for a whole turn, rather than one per node or per unit. Simpler, and it
    means the budget is a single number you can reason about."""

    __slots__ = ("size", "_seen", "evictions", "suppressed")

    def __init__(self, size: int = 512) -> None:
        self.size = size
        self._seen: OrderedDict = OrderedDict()
        self.evictions = 0
        self.suppressed = 0

    def key(self, rule_name: str, match, g) -> tuple:
        """Identity of a firing: the rule, **which nodes it bound**, and **the state those nodes were
        in** — by node identity (§4, §12 invariant 7), never by name and never by content similarity.

        **This is a physical cooldown of a specific instance, not a similarity test.** The analogy is a
        refractory period: this rule just fired on *these* nodes, so it is briefly spent on them.

        **A change to any bound node cancels the cooldown.** The state fingerprint is part of the key,
        so if anything about a bound node's attributes or degrees differs, this is a *different*
        situation and the rule fires again. That is what makes it a cooldown on a *thing* rather than a
        timer: the thing is spent only while it stays as it was.

        It also removes the wart the first version had. A rule re-run inside a supposition binds the
        same nodes, because a supposition changes a degree and not an identity — so a state-blind key
        suppressed the hypothetical conclusion and lost it. Fingerprinting fixes that as a
        *consequence* rather than by special-casing bands, which is the sign it was the right cut.

        Still clear of `cnl.md` §1: nothing here compares two *things* for sameness. It compares one
        thing against its own recent past, which is not an identity judgement."""
        return (rule_name,
                tuple(sorted((n.nid, _state(g, n)) for n in match.bindings.values())))

    def fired(self, key: tuple) -> bool:
        """Record `key` and report whether it had already fired. Returns True to suppress."""
        if key in self._seen:
            self._seen.move_to_end(key)
            self.suppressed += 1
            return True
        self._seen[key] = None
        while len(self._seen) > self.size:
            self._seen.popitem(last=False)
            self.evictions += 1
        return False

    def clear(self) -> None:
        self._seen.clear()

    def __len__(self) -> int:
        return len(self._seen)

    def __repr__(self) -> str:
        return (f"<Cooldown {len(self._seen)}/{self.size} "
                f"suppressed={self.suppressed} evicted={self.evictions}>")


__all__ = ["Cooldown"]
