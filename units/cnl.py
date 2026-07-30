"""THE CNL SURFACE — first real slice, 2026-07-30.

Until now `docs/units/cnl.md`/`forms_cnl.md` were 100% design and 0% built: every probe in this project
(`force_probe_experiment.py`, `identity_merge_probe_experiment.py`, ...) constructs graph data directly in
Python. This module is the first thing that turns actual CNL *text* into the same graph data those probes
build by hand — the missing piece between "we've checked the meta-rule pattern five times" and "an LLM can
actually drive this."

**Grammar, deliberately minimal — grow it, don't front-load it:**

    statement := '[' WORD ('|' WORD ':' filler)* ']'
    filler    := WORD | statement

A bracketed statement mints one occurrence node named after its head word (`cnl.md` §5's `bare word ⟹
name` rule). Each `role: filler` is one of two things, and the CNL text does not distinguish them
syntactically — the *role name* decides, against a small, closed, named set:

- **`force:` / `level:` — a crisp attribute set directly on the occurrence**, never a separate role node.
  This is `closed_class_rechallenged.md`'s single-claim-modifier side of the dividing line, and it is
  **marked at the boundary, not concluded by a rule** — the correction made to `cnl.md` §2 on 2026-07-30
  after finding that document contradicted `forms_cnl.md`'s own entry-format table (force carrier: "marked
  at the boundary") and the already-checked probes, which all assume force arrives pre-tagged. Recognizing
  "is this phrased as a question" is exactly the small, bounded, closed-class judgement `forms_llm.md`
  argues an LLM can make reliably; deciding what that mark *leads to* stays a rule's job, entirely — see
  `units/goal_rules.py`, unmodified by anything in this file.
- **Every other role name — a fresh role node, the multi-occurrence-relation side** (`units/graph.py`'s
  `role_edge`, already the mechanical realization `cnl.md` §5's table describes: "one fresh role node with
  `name = role`, edge from occurrence to it; a filler: one fresh node, edge from the role node to it").
  A bare-word filler mints a fresh node carrying `name = word`; a bracketed filler recurses, and
  containment in the text is containment in the graph (`cnl.md` §3, `model.md` §6 — nesting is physical).

**What this deliberately does not do yet, so the gaps are named rather than silently missing:**

- **No begin/end marker nodes.** `cnl.md` §3 describes them, but `model.md`'s later revision (`revision-02`,
  consolidated into `model.md` §6) deleted markers and the seal outright — nothing in the current engine
  reads them. This parser follows the *current* model, not `cnl.md`'s stale description of it. (A second,
  smaller inconsistency found the same way the force-marking one was — not fixed in the doc yet, just not
  built here.)
- **No labels or `x/`/`x` coindexing** (`cnl.md` §3) — cross-statement and within-statement identity both
  wait for a real scenario that needs them, the same "don't build machinery ahead of a use case" discipline
  `computation_units.md` names for SUPPOSE's discharge.
- **No degree bands, no negation marking, no refusal mechanism.** Each is a real, designed piece of the
  surface (`cnl.md` §2, `forms_cnl.md` §4.3) that this slice simply hasn't needed yet.
- **No validation that a role name outside some declared inventory should be refused** (`cnl.md` §2's "a
  translator emitting a role outside the set must refuse rather than invent"). Right now any bare word is
  accepted as a role name. Worth building once there's a real inventory to check against, not before.

Re-runnable: `python -m units.cnl` runs the worked examples in `report()`.
"""
from __future__ import annotations

import re

from .graph import EMPTY, Graph, Node, role_edge

# The single-claim-modifier roles: marked directly as a crisp attribute on the occurrence, never as a
# relational role node. Kept as a small, closed, named set — exactly the kind of fact this project keeps
# choosing to declare rather than infer (`composability-principle`: a needed distinction is a fact, never a
# new kind).
ATTRIBUTE_ROLES = frozenset({"force", "level"})

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PUNCT = "[]|:"


class CNLSyntaxError(ValueError):
    """A translator emitting this shape should refuse (`cnl.md` §2) rather than have it silently accepted
    — raised, never swallowed, so a caller can turn it into a refusal instead of guessing."""


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    pos, n = 0, len(text)
    while pos < n:
        c = text[pos]
        if c.isspace():
            pos += 1
            continue
        if c in _PUNCT:
            tokens.append(c)
            pos += 1
            continue
        m = _WORD_RE.match(text, pos)
        if not m:
            raise CNLSyntaxError(f"unrecognized character {c!r} at position {pos}")
        tokens.append(m.group(0))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.i = 0

    def _peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _next(self) -> str:
        tok = self._peek()
        if tok is None:
            raise CNLSyntaxError("unexpected end of input")
        self.i += 1
        return tok

    def _expect(self, tok: str) -> None:
        got = self._next()
        if got != tok:
            raise CNLSyntaxError(f"expected {tok!r}, got {got!r}")

    def parse_statement(self, g: Graph) -> tuple[Graph, Node]:
        self._expect("[")
        head = self._next()
        if head in _PUNCT:
            raise CNLSyntaxError(f"expected a head word, got {head!r}")
        occ = Node(head)
        g = g.with_node(occ, name=head)
        while self._peek() == "|":
            self._next()
            role_name = self._next()
            if role_name in _PUNCT:
                raise CNLSyntaxError(f"expected a role name, got {role_name!r}")
            self._expect(":")
            g, occ = self._parse_role(g, occ, role_name)
        self._expect("]")
        return g, occ

    def _parse_role(self, g: Graph, occ: Node, role_name: str) -> tuple[Graph, Node]:
        if role_name in ATTRIBUTE_ROLES:
            if self._peek() == "[":
                raise CNLSyntaxError(f"{role_name!r} must be a bare word, not a nested statement")
            value = self._next()
            g = g.with_node(occ, **{role_name: value})
            return g, occ
        if self._peek() == "[":
            g, filler = self.parse_statement(g)
        else:
            word = self._next()
            filler = Node(word)
            g = g.with_node(filler, name=word)
        g = role_edge(g, occ, role_name, filler)
        return g, occ


def parse(text: str, into: Graph = EMPTY) -> tuple[Graph, Node]:
    """One CNL statement, transcribed. Returns `(graph, the top-level occurrence node)`.

    `into` lets several statements share one growing graph — a turn's whole utterance batch, or a KB's
    several declared facts — the same way `units/graph.py`'s other builders compose."""
    tokens = _tokenize(text)
    parser = _Parser(tokens)
    g, occ = parser.parse_statement(into)
    if parser.i != len(tokens):
        raise CNLSyntaxError(f"unexpected trailing tokens: {tokens[parser.i:]}")
    return g, occ


def report() -> str:
    lines = ["=== CNL SURFACE: first real slice ==="]
    g, occ = parse("[utterance | force: ask | content: [eligible | agent: paul]]")
    lines.append(f"parsed occurrence: name={g.attr(occ, 'name')!r}, force={g.attr(occ, 'force')!r}")
    (content_role,) = g.out(occ)
    (content,) = g.out(content_role)
    lines.append(f"content occurrence: name={g.attr(content, 'name')!r}")
    (agent_role,) = g.out(content)
    (agent,) = g.out(agent_role)
    lines.append(f"agent filler: name={g.attr(agent, 'name')!r}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
