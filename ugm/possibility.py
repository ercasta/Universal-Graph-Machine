"""
Possibilistic layer — SLICE 1 (docs/possibilistic.md S7): banded forks + marker-mode read + θ-NAF.

Additive and OUT of the crisp hot path (chain.py untouched): a standalone MARKER-MODE reader that
sees ink at CERTAIN plus EVERY fork's pencil at its scope band, so a fact can be read `likely` /
`unlikely` WITHOUT taking a stance (the opposite of the binary in/out SUPPOSE scope read).

A FORK is a `<hypothesis>` scope carrying a `<likeliness>` band — that band is what distinguishes a
persisted possibilistic alternative from a transient SUPPOSE hypothesis (which has no band and is NOT
overlaid here). Likeliness lives on the scope, not on the edge primitive (S7.0, ratified 2026-07-15).

Later slices fold this into the ISA OVERLAY read op (`OVERLAY_BAND`) and add cross-fork environments
(combined assumption-sets, min band) + graded negation. This module is the SLICE-1 vertical.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, graded, valued, NAME, CONTROL_MARK, INERT_MARK
from .apply import SCOPE
from .suppose import HYPOTHESIS, _pencil
from .machine import Machine, SET, SEED, FOLLOW, TEST, OVERLAY_BAND

LIKELINESS = "<likeliness>"      # graded band on a fork's <hypothesis> scope node; absent ⇒ CERTAIN
CHOICE = "<choice>"              # valued attr grouping MUTUALLY-EXCLUSIVE fork alternatives (an `either…or`)
DERIVED_ENV = "<derived-env>"    # valued attr: a DERIVED fork's environment (the assumption-set it rests on)
CERTAIN = 1.0

_READER = Machine()              # T_MIN t-norm: the score min-accumulates fork bands (S7.2)
_FORK_BANDS = "<fork-bands>"     # register the OVERLAY_BAND read op reads the {rel_id -> band} map from

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


def add_fork(g: AttrGraph, degree: float, triples: list[tuple[str, str, str]],
             *, choice: str | None = None, derived_env: frozenset | None = None) -> str:
    """Author a possibilistic FORK: a `<hypothesis>` scope with band `degree`, holding `triples`
    (name triples) as CO-SCOPED pencil facts — a correlated alternative lives behind ONE fork
    (S1: joints via co-scoping). Returns the scope id. `choice` (optional) tags the fork as one
    ALTERNATIVE of a mutually-exclusive choice (an `either…or`): two forks sharing a choice can never
    both hold, so a derivation combining them is an impossible environment (S7.2 — `_env_consistent`).
    `derived_env` (optional) marks the fork as DERIVED and records the assumption-set it rests on, so a
    rule chaining off it inherits those assumptions (transitive impossibility is then caught). A BASE
    fork (no `derived_env`) is its own assumption; a derived fork's assumptions are its stored env."""
    scope = g.add_node(HYPOTHESIS, control=True)
    set_band(g, scope, degree)
    if choice is not None:
        g.set_attr(scope, CHOICE, valued(choice))
    if derived_env is not None:
        g.set_attr(scope, DERIVED_ENV, valued(frozenset(derived_env)))
    for s, p, o in triples:
        _pencil(g, scope, _entity(g, s), p, _entity(g, o))
    return scope


def _fork_scope_of(g: AttrGraph, rel: str) -> str | None:
    """The fork-scope a matched rel belongs to (its `SCOPE` tag), or None for an ink rel. OVERLAY_BAND
    only ever admits ink or a FORK pencil, so a tagged rel's scope is a fork."""
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


def _env_consistent(g: AttrGraph, env: frozenset[str]) -> bool:
    """An ENVIRONMENT (the set of fork-scopes a derivation used) is consistent unless it contains TWO
    DISTINCT forks of the SAME choice — mutually-exclusive alternatives can't both hold (S7.2, ATMS)."""
    by_choice: dict[object, str] = {}
    for scope in env:
        c = _choice_of(g, scope)
        if c is None:
            continue
        if by_choice.setdefault(c, scope) != scope:
            return False
    return True


def all_fork_bands(g: AttrGraph) -> dict[str, float]:
    """`rel_id -> band` for every pencil rel whose scope is a FORK (carries `<likeliness>`). Transient
    SUPPOSE scopes (no band) are excluded — they are not overlaid in marker mode. This is the
    marker-mode sibling of `chain._scope_pencils` (which returns ONE scope's set, binary)."""
    out: dict[str, float] = {}
    for r in g.nodes_with_key(SCOPE):
        a = g.get_attr(r, SCOPE)
        if a is None or not g.has(a.value):
            continue
        b = g.get_attr(a.value, LIKELINESS)
        if b is not None:
            out[r] = float(b.value)
    return out


def _guard(reg: str) -> list:
    """The fact-read guard (chain._guard): an entity endpoint carries NEITHER marker (not control,
    not inert). Only the REL is a fork pencil (control) — OVERLAY_BAND handles it; endpoints are
    ordinary nodes."""
    return [TEST(reg, CONTROL_MARK, absent=True), TEST(reg, INERT_MARK, absent=True)]


def facts_matching_banded(g: AttrGraph, pred: str, s_name: str | None, o_name: str | None
                          ) -> list[tuple[str, str, float, frozenset]]:
    """MARKER-MODE read through the ONE ISA matcher (S7.1): `(s, o, band, env)` for every `s pred o`
    visible as INK (band CERTAIN, env ∅) or any fork's pencil (band = its scope band, folded into the
    match `score` by OVERLAY_BAND's min t-norm — so the read is uniform with crisp matching AND multi-hop
    derivations min-accumulate for free, S7.2; `env` = the singleton fork the fact depends on, so a join
    can track and reject impossible cross-fork combinations). EITHER endpoint may be None (a WILDCARD),
    so a rule body atom with a free variable reads too; a bound endpoint is a name."""
    g.registers[_FORK_BANDS] = all_fork_bands(g)     # {rel_id -> band}: the overlay the read op reads
    rg = [TEST("r", pred), TEST("r", INERT_MARK, absent=True),
          OVERLAY_BAND("r", CONTROL_MARK, _FORK_BANDS)]     # the banded rel-guard
    out: list[tuple[str, str, float, frozenset]] = []

    def env_of(st) -> frozenset:
        fork = _fork_scope_of(g, st.regs["r"])            # the rel's fork (None for ink)
        return _scope_env(g, fork) if fork is not None else frozenset()   # transitive for a derived fork

    try:
        if s_name is not None:                            # walk OUT of the bound subject
            prog = [SET("s", ""), *_guard("s"), FOLLOW("r", "s", "out"), *rg,
                    FOLLOW("o", "r", "out"), *_guard("o")]
            if o_name is not None:
                prog.append(TEST("o", NAME, cmp="=", value=o_name))
            for s_id in g.nodes_named(s_name):
                prog[0] = SET("s", s_id)
                for st in _READER.match(g, prog):
                    on = o_name if o_name is not None else g.name(st.regs["o"])
                    out.append((s_name, on, st.score, env_of(st)))
        elif o_name is not None:                          # walk INTO the bound object
            prog = [SET("o", ""), *_guard("o"), FOLLOW("r", "o", "in"), *rg,
                    FOLLOW("s", "r", "in"), *_guard("s")]
            for o_id in g.nodes_named(o_name):
                prog[0] = SET("o", o_id)
                for st in _READER.match(g, prog):
                    out.append((g.name(st.regs["s"]), o_name, st.score, env_of(st)))
        else:                                             # both wildcard: SEED the predicate class
            prog = [SEED("r", pred, cmp=None), *rg, FOLLOW("s", "r", "in"), *_guard("s"),
                    FOLLOW("o", "r", "out"), *_guard("o")]
            for st in _READER.match(g, prog):
                out.append((g.name(st.regs["s"]), g.name(st.regs["o"]), st.score, env_of(st)))
        return out
    finally:
        g.registers.pop(_FORK_BANDS, None)


def possibility(g: AttrGraph, pred: str, s: str, o: str) -> float:
    """The possibility of `s pred o`: the BEST (max) band over the derivations reaching it —
    qualitative max-of-min (here single-hop, so just max). 0.0 if unreachable."""
    return max((band for _, _, band, _ in facts_matching_banded(g, pred, s, o)), default=0.0)


def naf_holds(g: AttrGraph, pred: str, s: str, o: str, theta: float) -> bool:
    """θ-crisp NAF: `not (s pred o)` HOLDS unless the positive is reachable at band ≥ `theta`.
    `theta` is the BIAS-vs-DECISIVENESS dial (S7.3): high θ ignores unlikely alternatives (decisive,
    bias-prone); low θ refuses to lean on an absence when the positive is even slightly possible."""
    return possibility(g, pred, s, o) < theta


Atom = tuple[str, str, str]     # (subj, pred, obj); a `?`-prefixed subj/obj is a rule variable


def _is_var(tok: str) -> bool:
    return isinstance(tok, str) and tok.startswith("?")


def _bind(binding: dict[str, str], tok: str) -> str | None:
    """The name a body/head token reads as: a bound variable's value, an unbound variable's None
    (a WILDCARD), or a literal itself."""
    return binding.get(tok) if _is_var(tok) else tok


def _match_body(g: AttrGraph, atoms: list[Atom], binding: dict[str, str], band: float,
                env: frozenset):
    """Yield `(binding, band, env)` for the conjunction `atoms`, marker-mode. A nested-loop join
    threading `binding` (var->name), MIN-composing `band` (weakest link — a body atom reaching through a
    fork bands the whole rule), and UNIONING `env` (the fork-scopes used). A combination that unions two
    exclusive forks of one choice is an IMPOSSIBLE environment and is pruned (S7.2, ATMS). A shared
    variable joins by equality of the bound name."""
    if not atoms:
        yield (binding, band, env)
        return
    (s, p, o), rest = atoms[0], atoms[1:]
    for sn, on, b, e in facts_matching_banded(g, p, _bind(binding, s), _bind(binding, o)):
        new_env = env | e
        if not _env_consistent(g, new_env):
            continue                                     # combines mutually-exclusive forks → impossible
        nb = dict(binding)
        if _is_var(s):
            nb[s] = sn
        if _is_var(o):
            nb[o] = on
        yield from _match_body(g, rest, nb, min(band, b), new_env)


def _nac_necessity(g: AttrGraph, nac: list[Atom], binding: dict[str, str], theta: float) -> float | None:
    """The NECESSITY a NAC conjunction contributes to the conclusion's band (GRADED negation, S7.3) —
    or None when it BLOCKS. For each `not P`: its possibility `Π(P)` is the best band it is reachable
    at; if `Π(P) ≥ theta` the firing is blocked (the θ hard gate — the bias-vs-decisiveness dial);
    otherwise it contributes `N(¬P) = 1 − Π(P)` (the possibility/necessity duality, Dubois–Prade — the
    scale involution, not probability arithmetic). The conjunction's contribution is the MIN (weakest
    link). An absent P (Π=0) contributes CERTAIN, so a NAC over genuinely-absent evidence never weakens
    the conclusion. `theta` still gates; the necessity is what makes the SURVIVING conclusion honest."""
    band = CERTAIN
    for s, p, o in nac:
        pi = max((b for _, _, b, _ in facts_matching_banded(g, p, _bind(binding, s), _bind(binding, o))),
                 default=0.0)
        if pi >= theta:
            return None                                          # blocked: P is too possible to negate
        band = min(band, 1.0 - pi)                               # N(¬P) = 1 − Π(P)
    return band


def apply_rule_banded(g: AttrGraph, body: list[Atom], nac: list[Atom], head: Atom,
                      *, theta: float) -> list[tuple[Atom, float]]:
    """Marker-mode application of a (multi-variable) rule (S7.3/S7.6): JOIN the body with min-band,
    drop firings a NAC clears θ (the bias-vs-decisiveness hard gate), fold in the NAC's NECESSITY
    `N(¬P)=1−Π(P)` (GRADED negation — the conclusion is only as strong as its counter-evidence is
    unlikely), and EMIT the head — INK for a CERTAIN band (crisp behaviour preserved), a FORK at the
    band for an uncertain one (a conclusion inherits its evidence's likeliness). Across alternative
    derivations the BEST band wins (possibility = max-of-min). Reads fully BEFORE writing (an emitted
    head can't perturb the join). Returns the deduped `((s,pred,o), band)`. `possibility`/OVERLAY_BAND
    only — chain_sip untouched."""
    best: dict[Atom, tuple[float, frozenset]] = {}                # READ phase: join + NAC; best (band, env) per head
    for binding, body_band, env in list(_match_body(g, body, {}, CERTAIN, frozenset())):
        nec = _nac_necessity(g, nac, binding, theta)
        if nec is None:                                          # a NAC cleared θ → blocked
            continue
        band = min(body_band, nec)                               # conclusion = weakest of body ∧ ¬-necessity
        s, p, o = head
        triple = (_bind(binding, s), p, _bind(binding, o))
        if triple[0] is None or triple[2] is None:               # head var not bound by the body → skip
            continue
        if triple not in best or band > best[triple][0]:
            best[triple] = (band, env)                           # keep the best derivation's env too
    results: list[tuple[Atom, float]] = []
    for triple, (band, env) in sorted(best.items()):             # WRITE phase
        if band >= CERTAIN and not env:
            from .lowering import load_fact_triples
            load_fact_triples(g, [triple])                        # certain, assumption-free → ink (as crisp)
        else:
            add_fork(g, band, [triple], derived_env=env)          # derived → a fork carrying its assumptions
        results.append((triple, band))
    return results


def verdict(g: AttrGraph, pred: str, s: str, o: str, *, closed: bool = True) -> str:
    """The possibilistic verdict: `certain` (ink) / `very likely` … `very unlikely` (only gated
    derivations) / `assumed-no` (unreachable, closed) / `unknown` (unreachable, open). Subsumes the
    crisp four-verdict space — no forks present ⇒ `certain` or `assumed-no`, as today."""
    p = possibility(g, pred, s, o)
    if p <= 0.0:
        return "assumed-no" if closed else "unknown"
    return band_word(p)
