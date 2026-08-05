"""Label census — every edge the engine actually writes, and who writes it.

This is step 0 of the edges-as-nodes arc. *Whatever is an edge becomes a node* is not uniform: a
fact node points at its participants, and those pointers cannot themselves be facts or the storage
regresses. So there is a **floor** — kernel structure stays edges, world relations become fact nodes
— and deciding where it sits needs an inventory.

⚠ The inventory must be **derived, not written down**, which is the standing discipline here:
`reach.py` and `horizon.py` both derive theirs so they cannot drift, and `access.VOCABULARY`'s own
provenance says how — *measured across the corpus, not imagined*. A grep cannot do it: only 22 labels
are declared as constants and the rest are inline literals, so a reader sees engine structure and test
fixtures side by side with no way to tell them apart.

**What separates the two is who writes them.** A label written only from Python is engine structure
until proven otherwise; a label written through the `LINK` opcode was written by a **rule**, which
makes it something the authored layer talks about. That distinction is free here because
`Graph._insert` is the only place an edge is created and `isa.py` is the only route a rule reaches it
through, so the census reads the call stack once per writing code object and caches it.

Run it with `python -m ugm.labels`. It runs the selftest for its corpus, because that is the widest
exercise of the engine that exists.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict

from .graph import Graph

#: Where a write came from, by the module of the innermost frame outside `graph.py`. `isa` is called
#: out because a write from there is a rule's `LINK`, not the engine's own bookkeeping — which is the
#: distinction the floor is drawn on.
SURFACE = "surface (rule LINK)"


class Census:
    """Counts of every (label, src kind, dst kind) written, and the writers responsible."""

    def __init__(self):
        self.by_label = Counter()
        self.writers = defaultdict(Counter)      # label -> writer -> count
        self.endpoints = defaultdict(set)        # label -> {(src kind, dst kind)}
        self.kinds = Counter()                   # minted kinds, for the node side
        self._where = {}                         # code object -> writer name, cached

    def writer(self) -> str:
        """The module that asked for this edge. Cached per code object, so the walk is paid once."""
        f = sys._getframe(2)
        # ⚠ The instrument's own frames must be skipped too. Skipping only `graph.py` attributes every
        # edge in the engine to this module's wrapper, and the table still prints — a whole census of
        # one writer, which reads as a finding rather than as a broken pass.
        while f is not None and f.f_code.co_filename.endswith(("graph.py", "labels.py")):
            f = f.f_back
        if f is None:
            return "?"
        code = f.f_code
        got = self._where.get(code)
        if got is None:
            mod = code.co_filename.replace("\\", "/").rsplit("/", 1)[-1][:-3]
            got = SURFACE if mod == "isa" else f"{mod}.{code.co_name}"
            self._where[code] = got
        return got

    def record(self, g, src, label, dst):
        self.by_label[label] += 1
        self.writers[label][self.writer()] += 1
        if len(self.endpoints[label]) < 12:       # a sample is enough to see the shape
            self.endpoints[label].add((g.attrs.get(src, {}).get("kind"),
                                       g.attrs.get(dst, {}).get("kind")))


def instrument(census: Census):
    """Wrap the two places structure is created. Returns the undo, so a caller can measure a phase."""
    insert, mint = Graph._insert, Graph.mint

    def _insert(self, src, label, index, dst, props):
        census.record(self, src, label, dst)
        return insert(self, src, label, index, dst, props)

    def _mint(self, kind, **attrs):
        census.kinds[kind] += 1
        return mint(self, kind, **attrs)

    Graph._insert, Graph.mint = _insert, _mint

    def undo():
        Graph._insert, Graph.mint = insert, mint
    return undo


def _classify(census: Census, label: str) -> str:
    """Which side of the floor this label sits on, on the evidence of who writes it.

    ⚠ This is a **reading of the census, not a verdict**. A label only Python writes may still be a
    world relation nothing has had reason to author yet, and the point of printing the writers beside
    it is that the call can be checked rather than taken."""
    w = set(census.writers[label])
    if w == {SURFACE}:
        return "WORLD"          # only ever written by a rule
    if SURFACE in w:
        return "both"           # written from both sides — look at these first
    return "structure?"         # Python only


def report() -> str:
    census = Census()
    undo = instrument(census)
    try:
        from . import selftest
        selftest.report()

        # Positive control, in the same graph and through the same call: a pass that reports an
        # inventory and a pass that cannot see one produce the same table. `reach.py`'s lesson, and
        # the one that left `EVERY_TEACHING_RULE_IS_MEDIATED` green with its instrument stubbed.
        g = Graph()
        a, b = g.mint("probe"), g.mint("probe")
        # ⚠ Three controls, because the first one alone passed while attribution was broken — the walk
        # landed on this module's own wrapper and named it the writer of all 147 labels, which prints
        # as a finding rather than as a fault. Seeing a write and attributing it are separate
        # capabilities and the table is built out of the second.
        #
        # ⚠ And the control for the second one has to come from *another file*: this module is skipped
        # by the walk on purpose, so an edge written from `report` can never be attributed to `report`.
        # The first attempt asserted exactly that and could not have passed either way.
        probe = {}
        exec(compile("def probe(g, a, b):\n    g.link(a, '_census_control', b)\n",
                     "_census_probe.py", "exec"), probe)
        probe["probe"](g, a, b)

        seen = census.by_label.get("_census_control") == 1
        attributed = set(census.writers.get("_census_control", ())) == {"_census_probe.probe"}
        spread = len({w for lbl in census.writers for w in census.writers[lbl]}) > 20
        uninstrumented = not any(w.startswith("labels.")
                                 for lbl in census.writers for w in census.writers[lbl])
    finally:
        undo()

    out = [f"{len(census.by_label)} labels, {sum(census.by_label.values())} edges written, "
           f"{len(census.kinds)} node kinds minted",
           f"control — sees a write: {'yes' if seen else 'BLIND, the table means nothing'}",
           f"control — attributes it to its writer: {'yes' if attributed else 'NO, the writer column is worthless'}",
           f"control — many distinct writers: {'yes' if spread else 'NO, the walk is landing on one frame'}",
           f"control — none attributed to the instrument: {'yes' if uninstrumented else 'NO, the walk is landing on itself'}",
           ""]
    groups = defaultdict(list)
    for label, n in census.by_label.most_common():
        groups[_classify(census, label)].append((label, n))

    for side in ("WORLD", "both", "structure?"):
        rows = groups.get(side, ())
        out.append(f"--- {side} ({len(rows)} labels, {sum(n for _, n in rows)} edges) ---")
        for label, n in rows:
            who = ", ".join(f"{k}×{v}" for k, v in census.writers[label].most_common(3))
            ends = ", ".join(f"{s}->{d}" for s, d in sorted(census.endpoints[label], key=str)[:3])
            out.append(f"  {label:<22} {n:>7}  [{who}]  {ends}")
        out.append("")
    return "\n".join(out)


def reads() -> str:
    """The other half, and the half that decides the cost: which labels are **read**, and how often.

    ⚠ The write census bounds *how much has to be converted*; it says nothing about *what the conversion
    costs*, because a relation is written once and read throughout the search. `on` is written 4,789
    times across the whole suite and read far more than that inside a single plan.

    Measured over Sussman rather than the selftest, deliberately: the suite's reads are dominated by
    fixture setup and by checks that exercise a path once, while the benchmark is the shape of a real
    search — which is where a per-read cost would actually land."""
    counts, by_dir = Counter(), Counter()
    targets, sources = Graph.targets, Graph.sources

    def _targets(self, src, label):
        counts[label] += 1
        by_dir["forward"] += 1
        return targets(self, src, label)

    def _sources(self, dst, label=None):
        counts[label if label is not None else "*any*"] += 1
        by_dir["reverse"] += 1
        return sources(self, dst, label)

    Graph.targets, Graph.sources = _targets, _sources
    try:
        from . import driver as D, selftest as S, thread as T
        g, world = S._blocks()
        goal, _abc = S._sussman(g, world)
        D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=5)
    finally:
        Graph.targets, Graph.sources = targets, sources

    total = sum(counts.values())
    out = [f"{total} reads over one Sussman search across {len(counts)} labels "
           f"({by_dir['forward']} forward, {by_dir['reverse']} reverse)", ""]
    for label, n in counts.most_common(25):
        out.append(f"  {label:<22} {n:>9}  {100 * n / total:>5.1f}%")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    print(reads() if "reads" in sys.argv else report())
