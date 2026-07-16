"""
Gradable COMPARATIVES — `x is more beautiful than y` (docs/possibilistic.md, decisions 1–3 + open
points G/H; built 2026-07-16). The OBJECT-LEVEL partial order, distinct from the meta-level
likelihood layer (`uncertainty.py`) — the two must never be conflated by role (S2), though they may
share structure.

DECISION 1 — a comparison is a DECOMPOSED relation, not a monolithic predicate:
  * the substrate already interposes a node for every relation; we reuse it with the DIMENSION as
    the predicate key (`x -[beautiful]-> y`) plus a `<comparison>` class marker on the rel node —
    `more_beautiful` as one welded string would sever the comparative from the graded degree
    forever, which is the bridge this module exists for;
  * DIRECTION carries more/less: `x -> cmp -> y` IS "x more beautiful than y"; "less" authors the
    REVERSED arrow. No `more=1` attribute;
  * "equally" is NOT a comparison node — it is a degree value-match (see `ask_comparative`).

DECISION 2 — hedges bridge comparative ↔ absolute degree: `x is very beautiful` (the EXISTING
degree form, `authoring.graded_rules` — nothing re-implemented here) puts x on a RUNG; two rung-ed
items are comparable even with no declared path between them. The bridge READS and COMPARES
(ordinal — never arithmetic).

DECISION 3 — incomparability is HONEST UNKNOWN: the partial order needs no completion; "can't say"
is a first-class answer, so comparative questions read absence as UNKNOWN, never a CWA assumed-no.

Transitivity (decision 1's cost) is a 2-body rule PER DIMENSION, generated from the KB like the
degree-adverb rules (§8 tools-from-data) and run DEMAND-DRIVEN (`query_goal` — read-only, SIP
prunes to the asked pair; open point G's perf posture). Conflicts — a comparison cycle, or a
declared comparison contradicting the degrees — are DEFEAT/LINT, never ⊥ (decision 7 / open point
H: `lint_comparisons`).
"""
from __future__ import annotations

from ..attrgraph import AttrGraph, graded
from ..production_rule import Rule, Pat

COMPARISON = "<comparison>"     # class marker on a comparison rel node (a `<…>` key: excluded from
                                # `predicate()`, so the rel's one domain key stays the DIMENSION)


def _norm(line: str) -> list[str]:
    """House-rule normalization for one line: lowercase, `are`->`is`, whitespace split."""
    return ["is" if t == "are" else t for t in line.strip().lower().split()]


def _entity(g: AttrGraph, name: str) -> str:
    found = [n for n in g.nodes_named(name) if not (g.is_control(n) or g.is_inert(n))]
    return min(found) if found else g.add_node(name)


# ---------------------------------------------------------------------------
# Authoring — `X is more D than Y` / `X is less D than Y`
# ---------------------------------------------------------------------------

def parse_comparative(line: str) -> tuple[str, str, str] | None:
    """`X is more D than Y` -> (X, D, Y); `X is less D than Y` -> (Y, D, X) — "less" IS the reversed
    arrow (decision 1: direction carries more/less), so the stored form is always "subject exceeds
    object on D". None for anything else. Single-token X/D/Y (slice-1)."""
    t = _norm(line)
    if len(t) != 6 or t[1] != "is" or t[4] != "than" or t[2] not in ("more", "less"):
        return None
    x, d, y = t[0], t[3], t[5]
    return (x, d, y) if t[2] == "more" else (y, d, x)


def add_comparison(g: AttrGraph, subj: str, dim: str, obj: str) -> str:
    """Write the decomposed comparison `subj exceeds obj on dim`: an ordinary INK relation whose
    predicate is the DIMENSION, class-marked `<comparison>` on the middle node. Returns the rel."""
    rel = g.add_relation(_entity(g, subj), dim, _entity(g, obj))
    g.set_attr(rel, COMPARISON, graded(1.0))
    return rel


def load_comparative(g: AttrGraph, text: str) -> list[str]:
    """Author every comparative line in `text`; RETURN the remaining lines for the ordinary loader
    (the same additive-loader contract as `uncertainty.load_uncertain`)."""
    rest: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parsed = parse_comparative(line)
        if parsed is None:
            rest.append(line)
        else:
            add_comparison(g, *parsed)
    return rest


# ---------------------------------------------------------------------------
# Transitivity — a 2-body rule per dimension, generated from the KB (§8)
# ---------------------------------------------------------------------------

def comparison_dims(g: AttrGraph) -> set[str]:
    """The dimensions with at least one authored comparison — read off the `<comparison>` marker
    index (the rel's one domain key IS the dimension)."""
    return {d for r in g.nodes_with_key(COMPARISON) if (d := g.predicate(r))}


def comparison_rules(g: AttrGraph) -> list[Rule]:
    """One transitivity rule per dimension IN the KB — generated from data, exactly like the
    degree-adverb rules (`authoring.graded_rules`): a newly compared dimension brings its rule with
    it, and the engine stays content-blind. The 2-body join on a shared middle variable is decision
    1's declared cost for keeping the dimension first-class."""
    return [Rule(key=f"cmp.trans.{d}",
                 lhs=[Pat("?x", d, "?y"), Pat("?y", d, "?z")],
                 rhs=[Pat("?x", d, "?z")])
            for d in sorted(comparison_dims(g))]


# ---------------------------------------------------------------------------
# Asking — path first, degree bridge second, honest UNKNOWN third
# ---------------------------------------------------------------------------

def _degree(g: AttrGraph, name: str, dim: str) -> float | None:
    """The absolute RUNG `name` holds on `dim` (the degree-adverb embedding, `x is very beautiful`
    -> 0.8) — max over same-named fact-layer mentions; None when no rung is declared."""
    best: float | None = None
    for n in g.nodes_named(name):
        if g.is_control(n) or g.is_inert(n):
            continue
        d = g.get_embedding(n).get(dim)
        if d is not None and (best is None or d > best):
            best = d
    return best


def _path(g: AttrGraph, dim: str, subj: str, obj: str) -> bool:
    """Is `subj exceeds obj on dim` DERIVABLE (direct or transitive)? Demand-driven and read-only:
    `query_goal` closes only the asked pair's chain in an ephemeral pencil scope (SIP — the magic
    set stays scoped to the goal, open point G's answer to the transitive-closure cost)."""
    from ..chain import query_goal
    return bool(query_goal(g, (dim, subj, obj), rules=comparison_rules(g)))


def parse_comparative_question(line: str) -> tuple[str, str, str, str] | None:
    """`is X more D than Y` / `is X less D than Y` -> (mode, X, D, Y); `is X as D as Y` ->
    ("as", X, D, Y). None for anything else."""
    t = _norm(line)
    if len(t) != 6 or t[0] != "is":
        return None
    if t[4] == "than" and t[2] in ("more", "less"):
        return (t[2], t[1], t[3], t[5])
    if t[2] == "as" and t[4] == "as":
        return ("as", t[1], t[3], t[5])
    return None


def ask_comparative(g: AttrGraph, question: str) -> str:
    """Answer `is X more/less D than Y` / `is X as D as Y` — `yes` / `no` / `unknown`.

    The order of appeal (decisions 1–3):
      1. the DECLARED partial order — a derivable path X⋯>Y is `yes`; the REVERSE path is `no`
         (the strict order's entailed opposite);
      2. the DEGREE BRIDGE — both on rungs (`very`/`somewhat`/`slightly`) compare ordinally:
         strictly higher rung `yes`, strictly lower `no`, EQUAL rungs `unknown` for a strict
         comparative (the rungs are coarse — same rung does not preclude a finer difference);
      3. otherwise honest UNKNOWN — incomparability is a first-class answer, never completed and
         never CWA-defaulted to `no` (decision 3).
    `as D as`: equal rungs `yes`, different rungs `no`, X==Y trivially `yes`, else `unknown`."""
    q = parse_comparative_question(question)
    if q is None:
        raise ValueError(f"unrecognized comparative question: {question!r}")
    mode, x, dim, y = q
    if mode == "less":
        mode, x, y = "more", y, x                          # less = the reversed strict question
    dx, dy = _degree(g, x, dim), _degree(g, y, dim)
    if mode == "as":
        if x == y:
            return "yes"
        if dx is not None and dy is not None:
            return "yes" if dx == dy else "no"
        return "unknown"
    if _path(g, dim, x, y):
        return "yes"
    if _path(g, dim, y, x):
        return "no"                                        # the reverse is declared: strictly not more
    if dx is not None and dy is not None:
        if dx > dy:
            return "yes"                                   # rung-degrees make them comparable (dec. 2)
        if dx < dy:
            return "no"
    return "unknown"                                       # incomparable: honest, not a gap to fill


# ---------------------------------------------------------------------------
# H — the consistency linter: conflicts are DEFEAT/LINT, never ⊥ (decision 7)
# ---------------------------------------------------------------------------

def _comparison_edges(g: AttrGraph, dim: str) -> list[tuple[str, str]]:
    """The AUTHORED comparison edges of `dim`, as `(subj_name, obj_name)` — marker-carrying rels
    only (derived transitives are consequences; the lint speaks about what was declared)."""
    out: list[tuple[str, str]] = []
    for r in g.nodes_with_key(COMPARISON):
        if g.predicate(r) != dim:
            continue
        s = next(iter(g.into(r)), None)
        o = next(iter(g.out(r)), None)
        if s is not None and o is not None:
            out.append((g.name(s), g.name(o)))
    return out


def lint_comparisons(g: AttrGraph) -> list[str]:
    """Report the two comparative defects as WARNINGS (never a derived falsum — the monotone core
    stays untouched, decision 7 / Amendment 2):
      * a CYCLE in a dimension's declared order (`x > y > … > x` — a strict order cannot loop);
      * a declared comparison CONTRADICTING the rungs (`x more D than y` but x's degree is
        STRICTLY BELOW y's — equal rungs do NOT conflict: the comparative may refine within a rung).
    Returns human-readable lines; empty = clean."""
    out: list[str] = []
    for dim in sorted(comparison_dims(g)):
        edges = _comparison_edges(g, dim)
        succ: dict[str, set[str]] = {}
        for s, o in edges:
            succ.setdefault(s, set()).add(o)
        # cycle sweep: DFS with an on-path set, over the declared edges only (small by construction)
        state: dict[str, int] = {}                          # 1 = on path, 2 = done

        def cyclic(n: str, path: list[str]) -> list[str] | None:
            state[n] = 1
            for m in sorted(succ.get(n, ())):
                if state.get(m) == 1:
                    return path[path.index(m):] + [m] if m in path else [n, m, n]
                if state.get(m, 0) == 0:
                    found = cyclic(m, path + [m])
                    if found:
                        return found
            state[n] = 2
            return None

        for n in sorted(succ):
            if state.get(n, 0) == 0:
                loop = cyclic(n, [n])
                if loop:
                    out.append(f"comparison cycle on '{dim}': {' > '.join(loop)}")
                    break                                   # one report per dimension is enough
        for s, o in edges:
            ds, do = _degree(g, s, dim), _degree(g, o, dim)
            if ds is not None and do is not None and ds < do:
                out.append(f"comparative-vs-degree conflict on '{dim}': "
                           f"declared {s} more {dim} than {o}, but degrees say {s}={ds} < {o}={do}")
    return out
