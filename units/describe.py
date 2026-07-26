"""THE WIRING REGISTER — a chain described as data (`cnl.md` §4).

`model.md` §11 pins two constraints that together decide this module's existence:

> the front end targets **data, never an engine API** — otherwise the system can *say* things it cannot
> *learn*; and a statement's **chain and markers are described in the data**, because if the assembler
> had to *unroll* a statement it would have to know what statements are.

So a statement's structure is written into an ordinary `Graph`, using the same nodes/edges/roles as
everything else (§3), and `assemble.py` reads it. Nothing here is a special representation: a unit
description is an occurrence node with roles, exactly like *"Paul went to the park"*.

**These builders stand in for the front end.** `cnl.md` §4 says rules write this register at write-back
and the bundled interpretation rules ship pre-written in it. Neither exists yet — so these are the
hand-written equivalent, and they are the honest boundary of what this spike has shown. What is being
tested is that the **assembler** can work from data alone, not that a rule can produce it.

⚠ The verbosity is real and is the point. `cnl.md` §5 flags it as a cost: a human is not meant to author
this.
"""
from __future__ import annotations

from .graph import EMPTY, Graph, Node


class Description:
    """A wiring-register graph under construction. Every method returns the node it minted."""

    def __init__(self) -> None:
        self.g: Graph = EMPTY

    # -- primitives ------------------------------------------------------------------------

    def _occ(self, kind: str, **attrs) -> Node:
        n = Node(kind)
        self.g = self.g.with_node(n, name=kind, **{k: v for k, v in attrs.items() if v is not None})
        return n

    def _role(self, occ: Node, role_name: str, target: Node, index: int | None = None) -> None:
        """One participant through its own fresh role node (§3). `index` rides on the **role node**,
        which is where per-occurrence information belongs — it is what makes `step` ordered without a
        list construct."""
        r = Node(role_name)
        self.g = self.g.with_node(r, name=role_name, **({} if index is None else {"index": index}))
        self.g = self.g.with_edge(occ, r).with_edge(r, target)

    # -- patterns --------------------------------------------------------------------------

    def atom(self, var: str | None = None, *, out=(), graded=(), **constraints) -> Node:
        """One pattern atom. Constraints are `(key, value)` pairs written as their own nodes, so a
        pattern is inspectable by an ordinary rule — which is where homoiconicity would come in if it is
        ever wanted (`model.md` §13, deliberately deferred).

        A constraint's value may be an `AttrVar`, which is written as a `var` on the constraint node
        rather than a `value` — *"carries the same name as that one"*, without saying which name."""
        from .match import AttrVar
        a = self._occ("atom", var=var)
        for k, v in constraints.items():
            if isinstance(v, AttrVar):
                self._role(a, "constraint", self._occ("constraint", key=k, var=v.name))
            else:
                self._role(a, "constraint", self._occ("constraint", key=k, value=v))
        for key in ((graded,) if isinstance(graded, str) else graded):
            self._role(a, "graded", self._occ("graded", key=key))
        for i, child in enumerate(out):
            self._role(a, "out", child, index=i)
        return a

    def role(self, name: str, target: Node) -> Node:
        """A role node in a *pattern* — identified the only way the engine allows, by matching its
        `name` attribute explicitly (§4). This is `cnl.md`'s `destination:` expanded."""
        return self.atom(out=(target,), name=name)

    # -- effects ---------------------------------------------------------------------------

    def mint(self, occurrence: str, *, args=(), graded: str | None = None) -> Node:
        e = self._occ("mint", occurrence=occurrence, graded=graded)
        for i, (role_name, var) in enumerate(args):
            self._role(e, "arg", self._occ("argument", role=role_name, var=var), index=i)
        return e

    def stamp(self, target: str, attr: str, band: str) -> Node:
        """A supposition's effect. Data, not a Python callable — see `unit.Stamp`."""
        return self._occ("stamp", target=target, attr=attr, band=band)

    def same(self, left: str, right: str) -> Node:
        """Conclude two bound nodes are the same. Applied at write-back, never here."""
        return self._occ("same", left=left, right=right)

    def absent(self, *atoms: Node) -> Node:
        """A negative conjunct — *"nothing here matched"*, not *"this is underivable"* (§4).

        Written as an ordinary occurrence with `atom` roles, so a guard is as inspectable as anything
        else. Order does not matter, so the roles are unindexed."""
        a = self._occ("absent")
        for at in atoms:
            self._role(a, "atom", at)
        return a

    # -- structure -------------------------------------------------------------------------

    def unit(self, label: str, pattern, effects, *, theta: str | None = None) -> Node:
        u = self._occ("unit", label=label, theta=theta)
        for i, p in enumerate(pattern):
            self._role(u, "pattern", p, index=i)
        for i, e in enumerate(effects):
            self._role(u, "effect", e, index=i)
        return u

    def statement(self, label: str, *steps: Node, scope: str | None = None) -> Node:
        """A sealed statement. Its steps are ordered by the index on each `step` role node, and a step
        may itself be a statement — **nesting is physical** (§6) and here that is just an edge.

        `scope` names the containment this statement **establishes in the graph**. A statement that
        declares one — a supposition, an attributed belief, an embedded clause — has its conclusions
        placed under a node of that name rather than asserted flatly, and statements nested inside it
        inherit it (`unit.ScopePointer`). Omitting it means *"this reasons in whatever context it was
        reached in"*, which is what an ordinary rule wants."""
        s = self._occ("statement", label=label, scope=scope)
        for i, step in enumerate(steps):
            self._role(s, "step", step, index=i)
        return s

    # -- goals -----------------------------------------------------------------------------

    def goal(self, label: str, satisfied_by: Node, *, parent: Node | None = None) -> Node:
        """A goal: a node carrying **a description of what would satisfy it** (§8).

        It has to be data — it persists across a suspension, and rules must be able to produce
        subgoals. The satisfaction condition is an ordinary `atom`, the same encoding a rule's pattern
        uses, so *checking whether a goal is satisfied is an ordinary rule match* with no new machinery.

        `parent` is the lineage §8 needs: a goal with no parent is just a goal with no parent, not a
        different kind of thing. It is what lets *"I couldn't read it"* be distinguished from *"I
        understood you; nothing came to mind"* by chain position alone."""
        g = self._occ("goal", label=label)
        self._role(g, "satisfied-by", satisfied_by)
        if parent is not None:
            self._role(g, "parent", parent)
        return g

    # -- structure, continued --------------------------------------------------------------

    def wire(self, src_statement: Node, dst: Node) -> Node:
        """A crossing (§6). The description names the **statement**, and the assembler resolves that to
        its end marker — there is no way to describe a wire out of an interior, because the description
        has no name for one."""
        w = self._occ("wire")
        self._role(w, "from", src_statement)
        self._role(w, "to", dst)
        return w

    def write_back(self, statement: Node) -> Node:
        w = self._occ("write-back")
        self._role(w, "port", statement)
        return w

    def feeds(self, statement: Node) -> Node:
        """Mark where an external value enters. §1: *nothing happens unbidden* — but something outside
        must say where the turn's data arrives."""
        f = self._occ("entry")
        self._role(f, "at", statement)
        return f


__all__ = ["Description"]
