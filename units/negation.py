"""EXPLICIT NEGATION — *"probably not P"* as data (user, 2026-07-26; §22.7a, §22.8).

§22.7a found a hole and pointed at the wrong layer. *"Probably not P"* was inexpressible: `band.grade`
asserts the fact it grades, so banding `P` put `P` in the value and the `Absent` atom flipped. Grade `P`
and `P` becomes true; say nothing and `P` is certainly absent. There was no third state.

> **The user's fix, and it is in the DATA subgraph rather than in the computation units:** two nodes — a
> `not` node carrying a grade, pointing at `P`.

**It needed NO new construct.** §22.6 made a fact able to occupy a node slot, and `reify.py` already held
the vocabulary because §22.7 needed the same thing to attach a band. Talking ABOUT a fact and CLAIMING it
finally come apart, which is all the fix ever was.

**THE SUBSTRATE NOW HAS THREE STATES WHERE IT HAD TWO:**

    P present                     P holds
    P absent, no denial           nothing is known about P
    P absent, denial at band b    P is believed false, to degree b

**⚠ AND §6a's `Absent` CANNOT TELL THE LAST TWO APART** (measured). This is the classical
negation-as-failure vs strong-negation split, and the honest statement is that the proposal RELOCATES the
ambiguity rather than removing it: `Absent(P)` remains a syntactic test over the value, and a rule that
means *"actively denied"* must ASK for the denial — which is an ordinary pattern, needing no new atom
kind. Two negations, both sayable, and the rule author now has to choose. That choice is the price.

**WHAT IT BUYS BEYOND THE FIX:**

* a unit can REASON over a denial, and over how sure the denial is — the user's standing requirement,
  satisfied for negation as §22.7 satisfied it for degree;
* `P` and `not P` in one value are no longer a representational impossibility — **and with bands they are
  not a contradiction either, but a DISTRIBUTION** ([[possibilistic-layer]]'s ranked hypotheses, arriving
  for free). Nothing reconciles them yet: that is a RECONCILIATION unit, and it does not exist;
* §16.2's gate gets sharper — a unit can EMIT A DENIAL instead of falling silent, so *"I have nothing"*
  and *"I deny"* stop being the same act.

**⚠ A DERIVED DENIAL NEEDS A KEY.** `deny` mints a `not` node, so two denials of the same fact are
different values and a re-derived denial never converges — §20.1(a)'s trap for the third time. Asserted
denials are safe; a rule that DERIVES one must pass `key=` so the node is minted once per (fact, denier)
rather than once per run.
"""
from __future__ import annotations

from .band import BAND
from .reify import handle_for, reify
from .value import Fact, Node, Subgraph, mint
from .vocab import role

DENIES = role("<denies>")        # a negation node -> the reified handle of the fact it denies


def deny(view: Subgraph, f: Fact, band: Node | None = None, key: Node | None = None) -> Subgraph:
    """*"(probably) not f"*. **`f` is NOT asserted** — that is the whole point.

    `key` names the negation node instead of minting one, and a DERIVED denial must supply it or the
    fixpoint never closes (see the module docstring)."""
    view, h = reify(view, f, key=None if key is None else _handle_key(key))
    n = key if key is not None else mint("not")
    view = view.with_facts([Fact(n, DENIES, h)])
    return view if band is None else view.with_facts([Fact(n, BAND, band)])


def _handle_key(key: Node) -> Node:
    """A stable handle derived from a stable denial key — so a keyed denial reifies stably too."""
    return Node(-key.nid, f"h:{key.name}")


def denial_of(view: Subgraph, f: Fact) -> Node | None:
    """The negation node denying `f`, if the value carries one."""
    h = handle_for(view, f)
    if h is None:
        return None
    return next((t.s for t in view.by_pred(DENIES) if t.o == h), None)


def denial_band(view: Subgraph, f: Fact) -> Node | None:
    """How sure the denial is, or None. **None means an UNGRADED denial, not a certain one** — the same
    control as `band.band_of`: absence of a degree is not a degree."""
    n = denial_of(view, f)
    if n is None:
        return None
    return next((t.o for t in view.by_pred(BAND) if t.s == n), None)


def denied(view: Subgraph, f: Fact) -> bool:
    """Is `f` ACTIVELY DENIED, as opposed to merely absent? The distinction `Absent` cannot make."""
    return denial_of(view, f) is not None


__all__ = ["DENIES", "deny", "denial_of", "denial_band", "denied"]
