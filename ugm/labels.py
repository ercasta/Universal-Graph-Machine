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

#: Handed back when a read names a node that has none. Shared and never written to, so the read half
#: allocates nothing per call — it runs 1.8M times in one search.
_NO_ATTRS: dict = {}


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


class _Bulk(dict):
    """The node → attributes map, counting reads of it made from **outside** `graph.py`.

    A bulk read is `g.attrs.get(n, {})` — the whole attribute dict of a node, taken in one go and then
    iterated, membership-tested or diffed. It is counted apart from `attr` because the two convert
    differently: `attr(n, k)` becomes one lookup of one attribute fact, while a bulk read becomes *every
    attribute fact about this node*, which under a hub is a reverse-index walk and is the shape that
    hurts. ⚠ `Graph.attr` itself goes through this dict, so the filter is not decoration: without it
    every ordinary read would be counted as a bulk one and the number would be meaningless."""

    n = 0
    where = Counter()
    _external = {}            # code object -> (is it outside graph.py?, writer name)

    def __getitem__(self, k):
        _Bulk._tally()
        return dict.__getitem__(self, k)

    def get(self, k, d=None):
        _Bulk._tally()
        return dict.get(self, k, d)

    @staticmethod
    def _tally():
        code = sys._getframe(2).f_code
        got = _Bulk._external.get(code)
        if got is None:
            path = code.co_filename.replace("\\", "/")
            mod = path.rsplit("/", 1)[-1][:-3]
            got = (mod not in ("graph", "labels"), f"{mod}.{code.co_name}")
            _Bulk._external[code] = got
        if got[0]:
            _Bulk.n += 1
            _Bulk.where[got[1]] += 1


class AttrCensus(Census):
    """Attribute *writes*, by key and by writer. Reuses `Census.writer`, so the floor is drawn on the
    same evidence for attributes as for edges: a key only Python writes is engine bookkeeping until
    shown otherwise, a key a rule's `SET` writes is something the authored layer talks about."""

    def __init__(self):
        super().__init__()
        self.writes = Counter()
        self.wwriters = defaultdict(Counter)

    def record_attr(self, key):
        self.writes[key] += 1
        self.wwriters[key][self.writer()] += 1


def _classify_attr(census: AttrCensus, key: str) -> str:
    # ⚠ A key that is a NODE ID is an index entry, not a slot. `workbench.index` stores identity →
    # version as an attribute keyed by the identity, which is *an index above the horizon and the
    # mechanism below it* doing exactly what it was built to do — and without this line it lands in
    # SLOT and buries the domain attributes under one key per block in the world.
    if "#" in key:
        return "index"
    w = set(census.wwriters[key])
    if w == {SURFACE}:
        return "SLOT"           # only ever written by a rule — a domain attribute
    if SURFACE in w:
        return "both"
    return "kernel?"


def attrs() -> str:
    """The ATTR census — the number the arc has been quoting around.

    ⚠ Attributes are the largest item in the edges-as-nodes conversion and the only one with no figure
    at all: the read census above counts **edges**, so every percentage published about the conversion
    excludes `a.height` and `a.clear` entirely. `docs/facts-as-nodes.md` says so and then quotes the
    numbers anyway, which is exactly how an understated figure becomes a clearance.

    Two halves, matching the two above. Writes over the **selftest**, because that is the widest
    exercise of the engine; reads over one **Sussman search**, because that is the shape of a real
    search and where a per-read cost would land. The read half counts edge reads in the *same run*, so
    the headline — what share of all graph reads is an attribute — is measured rather than assembled
    from two numbers taken at different times."""
    census = AttrCensus()
    put, mint = Graph.put, Graph.mint

    def _put(self, node, **kw):
        for k in kw:
            census.record_attr(k)
        return put(self, node, **kw)

    def _mint(self, kind, **kw):
        census.record_attr("kind")
        for k in kw:
            census.record_attr(k)
        return mint(self, kind, **kw)

    Graph.put, Graph.mint = _put, _mint
    try:
        from . import selftest
        selftest.report()

        # The controls, in the shape `report` uses and for the reason recorded there: a pass that sees
        # nothing and a pass that finds nothing print the same table. The probe is compiled under
        # another filename because this module is skipped by the writer walk on purpose.
        g = Graph()
        probe = {}
        exec(compile("def probe(g):\n    n = g.mint('probe')\n    g.put(n, _attr_control=1)\n",
                     "_attr_probe.py", "exec"), probe)
        probe["probe"](g)
        w_seen = census.writes.get("_attr_control") == 1
        w_attributed = set(census.wwriters.get("_attr_control", ())) == {"_attr_probe.probe"}
        w_spread = len({who for k in census.wwriters for who in census.wwriters[k]}) > 20
    finally:
        Graph.put, Graph.mint = put, mint

    # --- the read half ---------------------------------------------------------------------------
    r = Counter()
    keys = Counter()
    kinds = Counter()
    init = Graph.__init__
    reads_ = {n: getattr(Graph, n) for n in
              ("attr", "kind", "deref", "targets", "target", "sources", "at", "count")}
    ATTR_SIDE = ("attr", "kind", "deref")

    def _wrap(name, fn):
        if name == "attr":
            def w(self, node, key, default=None):
                r["attr"] += 1
                keys[key] += 1
                # ⚠ The kind of the node READ is the discriminator the writer-based classes cannot be:
                # `clear` and `height` are written from rules *and* from fixtures, so they land in
                # `both` beside `name` and `value` and the domain traffic disappears into the plumbing.
                # What separates them is whose attribute it is — an `activation`'s or a `block`'s.
                # ⚠ Read through `dict.get` on purpose: `self.attr` would recurse and `self.attrs.get`
                # would count itself as a bulk read.
                kinds[dict.get(self.attrs, node, _NO_ATTRS).get("kind")] += 1
                return fn(self, node, key, default)
            return w

        def w(self, *a, **kw):
            r[name] += 1
            return fn(self, *a, **kw)
        return w

    def _init(self, *a, **kw):
        init(self, *a, **kw)
        self.attrs = _Bulk(self.attrs)

    Graph.__init__ = _init
    for name, fn in reads_.items():
        setattr(Graph, name, _wrap(name, fn))
    _Bulk.n, _Bulk.where = 0, Counter()
    try:
        from . import driver as D, selftest as S, thread as T
        g, world = S._blocks()
        goal, _abc = S._sussman(g, world)
        D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=5)
        ran = r["attr"] > 0 and r["targets"] > 0

        bulk_before = _Bulk.n
        bulk = {}
        exec(compile("def probe(g, n):\n    return dict(g.attrs.get(n, {}))\n",
                     "_bulk_probe.py", "exec"), bulk)
        bulk["probe"](g, g.mint("probe"))
        b_seen = _Bulk.n == bulk_before + 1
        b_attributed = _Bulk.where.get("_bulk_probe.probe") == 1
        # ⚠ And the control that says the filter is doing its job rather than counting everything:
        # a read through `Graph.attr` goes through the same dict and must NOT be counted as bulk.
        before = _Bulk.n
        g.attr(world, "kind")
        b_filtered = _Bulk.n == before
    finally:
        Graph.__init__ = init
        for name, fn in reads_.items():
            setattr(Graph, name, fn)

    attr_reads = sum(r[n] for n in ATTR_SIDE)
    edge_reads = sum(r[n] for n in r if n not in ATTR_SIDE)
    total = attr_reads + edge_reads

    out = [f"WRITES — over the selftest: {sum(census.writes.values())} attribute writes "
           f"across {len(census.writes)} keys",
           f"control — sees a write: {'yes' if w_seen else 'BLIND, the table means nothing'}",
           f"control — attributes it: {'yes' if w_attributed else 'NO, the writer column is worthless'}",
           f"control — many distinct writers: {'yes' if w_spread else 'NO, the walk lands on one frame'}",
           ""]
    groups = defaultdict(list)
    for key, n in census.writes.most_common():
        groups[_classify_attr(census, key)].append((key, n))
    for side in ("SLOT", "both", "index", "kernel?"):
        rows = groups.get(side, ())
        out.append(f"--- {side} ({len(rows)} keys, {sum(n for _, n in rows)} writes) ---")
        for key, n in rows[:20]:
            who = ", ".join(f"{k}×{v}" for k, v in census.wwriters[key].most_common(3))
            out.append(f"  {key:<22} {n:>7}  [{who}]")
        if len(rows) > 20:
            out.append(f"  … {len(rows) - 20} more")
        out.append("")

    out += [f"READS — over one Sussman search: {total} graph reads",
            f"control — the search ran: {'yes' if ran else 'NO, the read table is empty'}",
            f"control — sees a bulk read: {'yes' if b_seen else 'BLIND to bulk reads'}",
            f"control — attributes it: {'yes' if b_attributed else 'NO, the call-site column is worthless'}",
            f"control — an ordinary attr read is NOT counted as bulk: "
            f"{'yes' if b_filtered else 'NO, the filter is off and the bulk figure is every read'}",
            "",
            f"  attributes  {attr_reads:>9}  {100 * attr_reads / max(total, 1):>5.1f}%   "
            + ", ".join(f"{n}×{r[n]}" for n in ATTR_SIDE),
            f"  edges       {edge_reads:>9}  {100 * edge_reads / max(total, 1):>5.1f}%",
            "",
            f"  of the attribute reads, {_Bulk.n} are BULK — the whole dict of one node, taken at once",
            ""]
    for who, n in _Bulk.where.most_common(10):
        out.append(f"    {who:<34} {n:>8}")
    # ⭐ The number the conversion actually turns on, and it is not the 84%: how much of the attribute
    # traffic is a DOMAIN slot. Classified by the write census, since a key's class is a property of who
    # writes it and does not depend on which run it was read in — ⚠ but a key never written in the
    # selftest lands in `unseen` rather than being quietly counted as kernel.
    out += ["", "  attribute reads by the KIND OF NODE read — the cut that separates the domain from",
            "  the interpreter, which the writer-based classes above cannot:"]
    shown = kinds.most_common(12)
    for kind, n in shown:
        out.append(f"    {str(kind):<22} {n:>9}  {100 * n / max(attr_reads, 1):>5.1f}% of attribute "
                   f"reads  {100 * n / max(total, 1):>5.1f}% of all reads")
    rest = sum(kinds.values()) - sum(n for _, n in shown)
    out.append(f"    {f'({len(kinds) - len(shown)} more kinds)':<22} {rest:>9}  "
               f"{100 * rest / max(attr_reads, 1):>5.1f}% of attribute reads  "
               f"{100 * rest / max(total, 1):>5.1f}% of all reads")
    out.append(f"    of which kind={'block':<16} {kinds.get('block', 0):>9}  "
               f"{100 * kinds.get('block', 0) / max(attr_reads, 1):>5.2f}% — the world's own nodes, "
               f"which is what converts")

    out += ["", "  most-read keys:"]
    for key, n in keys.most_common(15):
        cls = "unseen" if key not in census.writes else _classify_attr(census, key)
        out.append(f"    {key:<22} {n:>9}  {100 * n / max(attr_reads, 1):>5.1f}% of attribute reads"
                   f"   [{cls}]")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    print(attrs() if "attrs" in sys.argv else reads() if "reads" in sys.argv else report())
