"""
Possibilistic CNL surface — SLICE 1 (docs/possibilistic.md S7.5). Two authoring forms lowered to
banded FORKS (`ugm.possibility.add_fork`), plus banded yes/no verdicts:

  1. HEDGE-ON-A-FACT   `SUBJ is <hedge> OBJ` / `SUBJ is <hedge> a OBJ`
       `cy is likely a thief`   -> a fork (band 0.6) holding `cy is_a thief`
       `x is very unlikely male` -> a fork (band 0.15) holding `x is male`
  2. CORRELATED DISJUNCTION (the FIRST disjunctive form this CNL has)
       `x is either male and tall or female and short`
       -> TWO forks, each holding a CONJUNCTION co-scoped (joints), mutually exclusive.

DISAMBIGUATION (S2 three-roles): likelihood hedges (`likely`/`unlikely`/`very likely`/`very
unlikely`) are a DISTINCT closed class from the membership degree adverbs (`very`/`somewhat`/
`slightly`). `x is likely urgent` -> a fork (epistemic); `x is very urgent` -> a membership degree
(unchanged, handled by the existing degree form). A degree adverb is never a hedge, so the word alone
routes the line — the crisp/degree surface is byte-for-byte untouched.

SLICE-1 limits (deliberate): single-token SUBJ/OBJ; disjunction is the copula-adjective shape and its
alternatives default to an even band (ranking `more likely than` is a later slice); mutual exclusion
rides the existing `disjoint_from` (not linted here); the hedge lexicon is a module default (making it
KB-declarable — `probable means 0.7`, mirroring `very is 0.8` — is a small follow-up); deep `ask_goal`
integration is a later slice (this module renders yes/no verdicts directly).
"""
from __future__ import annotations

from ..attrgraph import AttrGraph
from ..possibility import add_fork, verdict

# likelihood-hedge -> band. DISTINCT lexicon from the degree adverbs (three-roles). Ordinal; the exact
# scale is S7.7-open. Two single-word rungs + the two-word `very` compositions.
HEDGE_BAND: dict[str, float] = {"likely": 0.6, "unlikely": 0.3}
VERY_HEDGE_BAND: dict[str, float] = {"likely": 0.85, "unlikely": 0.15}
DEFAULT_ALT_BAND: float = 0.5           # an alternative of an unranked `either…or` (an "even" split)


def _norm(line: str) -> list[str]:
    """House-rule normalization for one line: lowercase, `are`->`is`, whitespace split."""
    return ["is" if t == "are" else t for t in line.strip().lower().split()]


# ---------------------------------------------------------------------------
# Form 1 — hedge on a fact
# ---------------------------------------------------------------------------

def parse_hedge_fact(line: str) -> tuple[str, str, str, float] | None:
    """`SUBJ is <hedge> [a|an] OBJ` -> (subj, pred, obj, band), else None. `pred` is `is_a` for the
    `a OBJ` shape, else the copula `is`. Single-token SUBJ/OBJ (slice-1)."""
    t = _norm(line)
    if len(t) < 4 or t[1] != "is":
        return None
    if t[2] == "very" and len(t) >= 5 and t[3] in VERY_HEDGE_BAND:      # "very likely" / "very unlikely"
        band, rest = VERY_HEDGE_BAND[t[3]], t[4:]
    elif t[2] in HEDGE_BAND:
        band, rest = HEDGE_BAND[t[2]], t[3:]
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

def parse_either(line: str) -> tuple[str, list[str], list[str]] | None:
    """`SUBJ is either A and B [and …] or C and D [and …]` -> (subj, [A,B,…], [C,D,…]), else None.
    Each side is a conjunction of copula objects that share SUBJ (so each fork is a joint)."""
    t = _norm(line)
    if len(t) < 6 or t[1] != "is" or t[2] != "either":
        return None
    try:
        or_i = t.index("or", 3)
    except ValueError:
        return None
    alt1 = [w for w in t[3:or_i] if w != "and"]
    alt2 = [w for w in t[or_i + 1:] if w != "and"]
    if not alt1 or not alt2:
        return None
    return (t[0], alt1, alt2)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_line(g: AttrGraph, line: str) -> bool:
    """Author `line` as fork(s) if it is a possibilistic form; return True iff it was consumed.
    Tries the disjunction first (it carries `either`), then the hedge fact."""
    either = parse_either(line)
    if either is not None:
        subj, alt1, alt2 = either
        choice = g.add_node("<choice>", control=True)                    # the mutually-exclusive CHOICE
        add_fork(g, DEFAULT_ALT_BAND, [(subj, "is", o) for o in alt1], choice=choice)   # fork per alt:
        add_fork(g, DEFAULT_ALT_BAND, [(subj, "is", o) for o in alt2], choice=choice)   # co-scoped join
        return True
    hedge = parse_hedge_fact(line)
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
