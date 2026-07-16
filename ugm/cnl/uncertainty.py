"""
Possibilistic CNL surface — SLICE 1 (docs/possibilistic.md S7.5). Two authoring forms lowered to
banded FORKS (`ugm.possibility.add_fork`), plus banded yes/no verdicts:

  1. HEDGE-ON-A-FACT   `SUBJ is <hedge> OBJ` / `SUBJ is <hedge> a OBJ`
       `cy is likely a thief`   -> a fork (band 0.6) holding `cy is_a thief`
       `x is very unlikely male` -> a fork (band 0.15) holding `x is male`
  2. CORRELATED DISJUNCTION (the FIRST disjunctive form this CNL has)
       `x is either male and tall or female and short`
       -> TWO forks, each holding a CONJUNCTION co-scoped (joints), mutually exclusive.
       RANKED variant (the doc's opening motivation — alternatives need not be even):
       `x is either male and tall or more likely female and short`  (also `or less likely`)
       -> the favoured alternative carries the `likely` rung, the other the `unlikely` rung
       (both from the lexicon in scope — ordinal, so only the ORDER and the θ-cut matter).

DISAMBIGUATION (S2 three-roles): likelihood hedges (`likely`/`unlikely`/`very likely`/`very
unlikely`) are a DISTINCT closed class from the membership degree adverbs (`very`/`somewhat`/
`slightly`). `x is likely urgent` -> a fork (epistemic); `x is very urgent` -> a membership degree
(unchanged, handled by the existing degree form). A degree adverb is never a hedge, so the word alone
routes the line — the crisp/degree surface is byte-for-byte untouched.

SLICE-1 limits (deliberate): single-token SUBJ/OBJ; disjunction is the copula-adjective shape;
mutual exclusion rides the existing `disjoint_from` (not linted here); deep `ask_goal` integration
is a later slice (this module renders yes/no verdicts directly).

The hedge lexicon is KB DATA, not engine config (the degree-adverb doctrine, `authoring.py` §"The
degree scale is KB DATA"): `probable means 0.7` declares a new hedge as an ordinary ink fact, read
back by `hedge_bands`. It deliberately uses `means`, NOT the degree form `A is <number>` — the same
surface would silently make every declared hedge a degree adverb, collapsing the two roles the
three-roles invariant (S2) keeps apart. `HEDGE_BAND` is only the shipped default scale.
"""
from __future__ import annotations

from ..attrgraph import AttrGraph
from ..possibility import add_fork, facts_matching_banded, verdict, CERTAIN

# likelihood-hedge -> band, the SHIPPED defaults. DISTINCT lexicon from the degree adverbs
# (three-roles). Ordinal; the exact scale is S7.7-open. A key may be one or two words (the `very`
# compositions are plain two-word entries — no special-cased modifier).
HEDGE_BAND: dict[str, float] = {"likely": 0.6, "unlikely": 0.3,
                                "very likely": 0.85, "very unlikely": 0.15}
HEDGE_DECL_PRED = "means"               # `probable means 0.7` — the KB hedge-declaration predicate
DEFAULT_ALT_BAND: float = 0.5           # an alternative of an unranked `either…or` (an "even" split)


def _norm(line: str) -> list[str]:
    """House-rule normalization for one line: lowercase, `are`->`is`, whitespace split."""
    return ["is" if t == "are" else t for t in line.strip().lower().split()]


# ---------------------------------------------------------------------------
# The hedge lexicon — KB-declarable, defaults overlaid (mirrors `authoring._degrees`)
# ---------------------------------------------------------------------------

def parse_hedge_decl(line: str) -> tuple[str, float] | None:
    """`HEDGE means NUMBER` -> (hedge, band), else None. HEDGE is one or two words (the shapes
    `parse_hedge_fact` looks up); NUMBER must be a band in (0, 1]. `probable means 0.7` adds a rung;
    `likely means 0.8` overrides a default."""
    t = _norm(line)
    if HEDGE_DECL_PRED not in t:
        return None
    i = t.index(HEDGE_DECL_PRED)
    if not (1 <= i <= 2) or len(t) != i + 2:
        return None
    try:
        v = float(t[i + 1])
    except ValueError:
        return None
    if not (0.0 < v <= 1.0):
        return None
    return (" ".join(t[:i]), v)


def hedge_bands(g: AttrGraph) -> dict[str, float]:
    """The hedge lexicon in scope: the shipped defaults, overlaid with every `HEDGE means NUMBER`
    declared as an INK fact in `g` — the scale is KB data an author extends, exactly like the degree
    adverbs (`authoring.degree_thresholds`). Read back through the one banded reader (a declaration
    is an ordinary fact; only certain ones count — a hedged hedge-declaration would be a category
    error)."""
    out = dict(HEDGE_BAND)
    for s, o, band, _ in facts_matching_banded(g, HEDGE_DECL_PRED, None, None):
        if band < CERTAIN:
            continue
        try:
            v = float(o)
        except ValueError:
            continue
        if 0.0 < v <= 1.0:
            out[s] = v
    return out


# ---------------------------------------------------------------------------
# Form 1 — hedge on a fact
# ---------------------------------------------------------------------------

def parse_hedge_fact(line: str, hedges: dict[str, float] | None = None
                     ) -> tuple[str, str, str, float] | None:
    """`SUBJ is <hedge> [a|an] OBJ` -> (subj, pred, obj, band), else None. `pred` is `is_a` for the
    `a OBJ` shape, else the copula `is`. Single-token SUBJ/OBJ (slice-1). `hedges` is the lexicon in
    scope (`hedge_bands`); default = the shipped scale. A two-word hedge wins over a one-word prefix
    (`very likely male` is the 0.85 rung, not `very` + a hedge `likely`)."""
    if hedges is None:
        hedges = HEDGE_BAND
    t = _norm(line)
    if len(t) < 4 or t[1] != "is":
        return None
    if len(t) >= 5 and f"{t[2]} {t[3]}" in hedges:                     # two-word hedge first
        band, rest = hedges[f"{t[2]} {t[3]}"], t[4:]
    elif t[2] in hedges:
        band, rest = hedges[t[2]], t[3:]
    else:
        return None                                                    # not a hedge (e.g. a degree adverb)
    if rest and rest[0] in ("a", "an"):
        pred, rest = "is_a", rest[1:]
    else:
        pred = "is"
    if len(rest) != 1:
        return None
    return (t[0], pred, rest[0], band)


# ---------------------------------------------------------------------------
# Form 2 — correlated disjunction (the first disjunctive form)
# ---------------------------------------------------------------------------

def parse_either(line: str) -> tuple[str, list[str], list[str], str | None] | None:
    """`SUBJ is either A and B [and …] or [more|less likely] C and D [and …]`
    -> (subj, [A,B,…], [C,D,…], rank), else None. Each side is a conjunction of copula objects that
    share SUBJ (so each fork is a joint). `rank` says how the SECOND alternative compares to the
    first: `"more"` / `"less"` for the ranked variant, None for the even one."""
    t = _norm(line)
    if len(t) < 6 or t[1] != "is" or t[2] != "either":
        return None
    try:
        or_i = t.index("or", 3)
    except ValueError:
        return None
    rest, rank = t[or_i + 1:], None
    if len(rest) >= 3 and rest[0] in ("more", "less") and rest[1] == "likely":
        rank, rest = rest[0], rest[2:]
    alt1 = [w for w in t[3:or_i] if w != "and"]
    alt2 = [w for w in rest if w != "and"]
    if not alt1 or not alt2:
        return None
    return (t[0], alt1, alt2, rank)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_line(g: AttrGraph, line: str) -> bool:
    """Author `line` as fork(s) if it is a possibilistic form; return True iff it was consumed.
    Tries the hedge DECLARATION first (it carries `means` — written as an ink fact, so the lexicon
    lives in the KB), then the disjunction (it carries `either`), then the hedge fact (against the
    lexicon in scope, so a hedge declared earlier in the same text already parses)."""
    decl = parse_hedge_decl(line)
    if decl is not None:
        from ..lowering import load_fact_triples
        hedge, band = decl
        load_fact_triples(g, [(hedge, HEDGE_DECL_PRED, repr(band))])     # the scale is KB data
        return True
    either = parse_either(line)
    if either is not None:
        subj, alt1, alt2, rank = either
        if rank is None:
            b1 = b2 = DEFAULT_ALT_BAND                                   # even (equally likely)
        else:
            hedges = hedge_bands(g)                                      # ranked: distribute the
            hi, lo = hedges["likely"], hedges["unlikely"]                # likely/unlikely rungs
            b1, b2 = (lo, hi) if rank == "more" else (hi, lo)
        choice = g.add_node("<choice>", control=True)                    # the mutually-exclusive CHOICE
        add_fork(g, b1, [(subj, "is", o) for o in alt1], choice=choice)   # fork per alternative:
        add_fork(g, b2, [(subj, "is", o) for o in alt2], choice=choice)   # co-scoped join
        return True
    hedge = parse_hedge_fact(line, hedge_bands(g))
    if hedge is not None:
        subj, pred, obj, band = hedge
        add_fork(g, band, [(subj, pred, obj)])
        return True
    return False


def load_uncertain(g: AttrGraph, text: str) -> list[str]:
    """Author every possibilistic line in `text` as fork(s); RETURN the remaining lines for the caller
    to hand to ordinary `load_facts`. Additive over the crisp loader — the possibilistic surface never
    intercepts a plain fact."""
    rest: list[str] = []
    for line in text.splitlines():
        if line.strip() and not load_line(g, line):
            rest.append(line)
    return rest


# ---------------------------------------------------------------------------
# Banded verdicts
# ---------------------------------------------------------------------------

def parse_question(line: str) -> tuple[str, str, str] | None:
    """`is SUBJ [a|an] OBJ` -> (pred, subj, obj), else None."""
    t = _norm(line)
    if len(t) < 3 or t[0] != "is":
        return None
    rest = t[2:]
    pred = "is"
    if rest[0] in ("a", "an"):
        pred, rest = "is_a", rest[1:]
    if len(rest) != 1:
        return None
    return (pred, t[1], rest[0])


def ask(g: AttrGraph, question: str, *, closed: bool = True) -> str:
    """A banded yes/no verdict for `is SUBJ [a] OBJ`: `certain` / `very likely` … `very unlikely` /
    `assumed-no` / `unknown` (`ugm.possibility.verdict`). Raises on an unrecognized question shape."""
    q = parse_question(question)
    if q is None:
        raise ValueError(f"unrecognized yes/no question: {question!r}")
    pred, subj, obj = q
    return verdict(g, pred, subj, obj, closed=closed)
