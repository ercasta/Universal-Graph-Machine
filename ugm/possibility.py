"""
Possibilistic layer — the FORK vocabulary and the banded verdict surface (docs/possibilistic.md S7).

A FORK is a `<hypothesis>` scope carrying a `<likeliness>` band — that band is what distinguishes a
persisted possibilistic alternative from a transient SUPPOSE hypothesis (which has no band and is not
overlaid in marker mode). Likeliness lives on the scope, not on the edge primitive (S7.0, ratified
2026-07-15).

THE ENGINE IS THE FOLD (2026-07-16): banded reasoning runs INSIDE `chain_sip` under a
`FirmwarePolicy(uncertainty="banded")` — the marker-mode read (`OVERLAY_BAND`, band = match score),
min-band joins with ATMS environments, θ-NAF with graded necessity, and derived-fork EMITs are all
`chain.py`. The standalone forward reasoner this module used to carry (`facts_matching_banded`'s own
ISA programs, `apply_rule_banded`, `run_banded`) was DELETED with the fold — one engine, not two.
What remains here is the fork VOCABULARY (authoring, bands, environments, exclusivity) and the
name-level verdict reads (`possibility` / `verdict` / `naf_holds`), thin wrappers over the one
matcher.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, graded, valued
from .apply import SCOPE
from .policy import FirmwarePolicy, DEFAULT_POLICY
from .suppose import HYPOTHESIS, _pencil, scope_members
from .vocabulary import DISJOINT, COPULA, IS_A

LIKELINESS = "<likeliness>"      # graded band on a fork's <hypothesis> scope node; absent ⇒ CERTAIN
CHOICE = "<choice>"              # valued attr grouping MUTUALLY-EXCLUSIVE fork alternatives (an `either…or`)
DERIVED_ENV = "<derived-env>"    # valued attr: a DERIVED fork's environment (the assumption-set it rests on)
CERTAIN = 1.0

# Provisional band → word scale (S7.7 is OPEN: reuse the degree-adverb lexicon very=0.8/somewhat=0.5/
# slightly=0.3, vs a dedicated 5-rung enum). Ordered high→low; interpreted ORDINALLY (decision F).
_BANDS = [(1.0, "certain"), (0.8, "very likely"), (0.5, "likely"),
          (0.3, "unlikely"), (0.0, "very unlikely")]


def band_word(b: float) -> str:
    for thr, word in _BANDS:
        if b >= thr:
            return word
    return "very unlikely"


def _entity(g: AttrGraph, name: str) -> str:
    """Reuse an existing same-named entity node or mint one (so a fork's `x` is the ink `x`)."""
    found = g.nodes_named(name)
    return min(found) if found else g.add_node(name)


def set_band(g: AttrGraph, scope: str, degree: float) -> None:
    g.set_attr(scope, LIKELINESS, graded(degree))


def band_of_scope(g: AttrGraph, scope: str) -> float:
    a = g.get_attr(scope, LIKELINESS)
    return float(a.value) if a is not None else CERTAIN


def _new_fork_scope(g: AttrGraph, degree: float, *, choice: str | None = None,
                    derived_env: frozenset | None = None) -> str:
    scope = g.add_node(HYPOTHESIS, control=True)
    set_band(g, scope, degree)
    if choice is not None:
        g.set_attr(scope, CHOICE, valued(choice))
    if derived_env:
        g.set_attr(scope, DERIVED_ENV, valued(frozenset(derived_env)))
    return scope


def fork_fact(g: AttrGraph, degree: float, s_id: str, pred: str, o_id: str,
              *, derived_env: frozenset | None = None) -> str:
    """Pen ONE fact `s -[pred]-> o` (node ids) behind a fresh fork at `degree` — the NODE-GRAIN
    authoring the banded chain EMIT uses for a derived conclusion. `derived_env` records the
    assumption-set the conclusion rests on (its parents' forks), so a rule chaining off it inherits
    them (transitive ATMS, S7.2). Returns the pencil REL node (the fact — its fork is its SCOPE tag)."""
    return _pencil(g, _new_fork_scope(g, degree, derived_env=derived_env), s_id, pred, o_id)


def add_fork(g: AttrGraph, degree: float, triples: list[tuple[str, str, str]],
             *, choice: str | None = None, derived_env: frozenset | None = None) -> str:
    """Author a possibilistic FORK: a `<hypothesis>` scope with band `degree`, holding `triples`
    (name triples) as CO-SCOPED pencil facts — a correlated alternative lives behind ONE fork
    (S1: joints via co-scoping). Returns the scope id. `choice` (optional) tags the fork as one
    ALTERNATIVE of a mutually-exclusive choice (an `either…or`): two forks sharing a choice can never
    both hold, so a derivation combining them is an impossible environment (S7.2 — `_env_consistent`).
    `derived_env` (optional) marks the fork as DERIVED and records the assumption-set it rests on. A
    BASE fork (no `derived_env`) is its own assumption; a derived fork's assumptions are its stored env."""
    scope = _new_fork_scope(g, degree, choice=choice, derived_env=derived_env)
    for s, p, o in triples:
        _pencil(g, scope, _entity(g, s), p, _entity(g, o))
    return scope


def _fork_scope_of(g: AttrGraph, rel: str) -> str | None:
    """The fork-scope a matched rel belongs to (its `SCOPE` tag), or None for an ink rel."""
    a = g.get_attr(rel, SCOPE)
    return a.value if a is not None else None


def _scope_env(g: AttrGraph, scope: str) -> frozenset:
    """The ENVIRONMENT a fork-scope represents: a DERIVED fork's stored assumption-set (so a fact built
    from it carries its parents' forks, not itself), else a BASE fork is its own singleton assumption."""
    a = g.get_attr(scope, DERIVED_ENV)
    return a.value if a is not None else frozenset((scope,))


def _choice_of(g: AttrGraph, scope: str) -> object | None:
    a = g.get_attr(scope, CHOICE)
    return a.value if a is not None else None


def _disjoint_pairs(g: AttrGraph) -> set[frozenset[str]]:
    """The INK-declared `disjoint_from` name pairs (symmetric): `male disjoint_from female` ⇒
    {male, female}. Read directly off the key index (a declaration is an ordinary crisp fact)."""
    out: set[frozenset[str]] = set()
    for r in g.nodes_with_key(DISJOINT):
        if g.is_control(r) or g.is_inert(r):
            continue
        s = next((n for n in g.into(r) if not g.is_inert(n)), None)
        o = next(iter(g.out(r)), None)
        if s is not None and o is not None:
            out.add(frozenset((g.name(s), g.name(o))))
    return out


def _fork_claims(g: AttrGraph, scope: str) -> set[tuple[str, str]]:
    """The COPULA claims a fork pens, as `(subject-name, object-name)` — what the fork says its
    subjects ARE. Only `is`/`is_a` count: `x knows female` predicates nothing of x, so it can never
    trip a declared disjointness."""
    out: set[tuple[str, str]] = set()
    for rel in scope_members(g, scope):
        if not g.has(rel) or g.predicate(rel) not in (COPULA, IS_A):
            continue
        s = next(iter(g.into(rel)), None)
        o = next(iter(g.out(rel)), None)
        if s is not None and o is not None:
            out.add((g.name(s), g.name(o)))
    return out


def _env_consistent(g: AttrGraph, env: frozenset[str]) -> bool:
    """An ENVIRONMENT (the set of fork-scopes a derivation used) is consistent unless it combines
    mutually-exclusive alternatives (S7.2, ATMS) — by either route:
    - TWO DISTINCT forks of the SAME `<choice>` (an `either…or`'s alternatives), or
    - two INDEPENDENTLY-AUTHORED forks whose copula claims about one subject are DECLARED
      `disjoint_from` (`x is male` in one fork, `x is female` in another, `male disjoint_from
      female` in ink) — the existing disjointness vocabulary wired into world-exclusion."""
    by_choice: dict[object, str] = {}
    for scope in env:
        c = _choice_of(g, scope)
        if c is None:
            continue
        if by_choice.setdefault(c, scope) != scope:
            return False
    if len(env) >= 2:
        pairs = _disjoint_pairs(g)
        if pairs:
            claims = {scope: _fork_claims(g, scope) for scope in env}
            scopes = sorted(env)
            for i, a in enumerate(scopes):
                for b in scopes[i + 1:]:
                    for s1, o1 in claims[a]:
                        for s2, o2 in claims[b]:
                            if s1 == s2 and frozenset((o1, o2)) in pairs:
                                return False
    return True


def all_fork_bands(g: AttrGraph) -> dict[str, float]:
    """`rel_id -> band` for every pencil rel whose scope is a FORK (carries `<likeliness>`). Transient
    SUPPOSE scopes (no band) are excluded — they are not overlaid in marker mode. This is the overlay
    map the banded read op reads (`chain._band_overlay` merges in the active SUPPOSE scope's pencils
    at CERTAIN)."""
    out: dict[str, float] = {}
    for r in g.nodes_with_key(SCOPE):
        a = g.get_attr(r, SCOPE)
        if a is None or not g.has(a.value):
            continue
        b = g.get_attr(a.value, LIKELINESS)
        if b is not None:
            out[r] = float(b.value)
    return out


def facts_matching_banded(g: AttrGraph, pred: str, s_name: str | None, o_name: str | None
                          ) -> list[tuple[str, str, float, frozenset]]:
    """The NAME-LEVEL marker-mode read: `(s, o, band, env)` for every `s pred o` visible as INK
    (band CERTAIN, env ∅) or any fork's pencil (band = its scope band; env = the assumption-set,
    transitive for a derived fork). Either endpoint may be None (a wildcard). A thin wrapper over
    the ONE matcher — `chain._facts_matching(bands=True)` (the fold); this module no longer carries
    its own ISA programs."""
    from .chain import _facts_matching, ById

    def nm(x) -> str:
        return g.name(x.node_id) if isinstance(x, ById) else x

    return [(nm(s), nm(o), band, env)
            for s, o, band, env in _facts_matching(g, pred, s_name, o_name, bands=True)]


def possibility(g: AttrGraph, pred: str, s: str, o: str) -> float:
    """The possibility of `s pred o`: the BEST (max) band over the derivations reaching it —
    qualitative max-of-min. 0.0 if unreachable. (A READ of what is present; to also derive on demand,
    run `chain_sip` with a banded policy first, or ask through `check`.)"""
    return max((band for _, _, band, _ in facts_matching_banded(g, pred, s, o)), default=0.0)


def _theta(theta: float | None, policy: FirmwarePolicy) -> float:
    """Resolve the NAF α-cut: θ is a SESSION dial living on `FirmwarePolicy` (`policy.theta`,
    default + range there); an explicit `theta=` is a per-call convenience override (the same shape
    as `check`'s `open_preds=` folding into the policy)."""
    return policy.theta if theta is None else theta


def naf_holds(g: AttrGraph, pred: str, s: str, o: str, theta: float | None = None,
              *, policy: FirmwarePolicy = DEFAULT_POLICY) -> bool:
    """θ-crisp NAF: `not (s pred o)` HOLDS unless the positive is reachable at band ≥ θ.
    θ is the BIAS-vs-DECISIVENESS dial (S7.3): high θ ignores unlikely alternatives (decisive,
    bias-prone); low θ refuses to lean on an absence when the positive is even slightly possible.
    It lives on `policy` (session dial); `theta=` overrides per call."""
    return possibility(g, pred, s, o) < _theta(theta, policy)


def verdict(g: AttrGraph, pred: str, s: str, o: str, *, closed: bool = True) -> str:
    """The possibilistic verdict: `certain` (ink) / `very likely` … `very unlikely` (only gated
    derivations) / `assumed-no` (unreachable, closed) / `unknown` (unreachable, open). Subsumes the
    crisp four-verdict space — no forks present ⇒ `certain` or `assumed-no`, as today."""
    p = possibility(g, pred, s, o)
    if p <= 0.0:
        return "assumed-no" if closed else "unknown"
    return band_word(p)
