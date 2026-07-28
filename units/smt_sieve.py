"""SMT SIEVE — proving composition safety symbolically, instead of sampling it.

`sieve.py` checks composition by BUILDING a concrete cell, RUNNING the actual engine, and READING the
result. That finds a leak only in the cells it happens to construct. Zave's feature-interaction
detection work in telecom (starting 1993) takes the other route: encode each feature as a declarative
constraint over the call state, and ask a decision procedure whether ANY assignment violates it — a
proof over the whole symbolic domain in one query, not a sample from it.

This is the same move as lifting a circle's boundary into z = x^2 + y^2 so a straight cut separates
what a straight line never could in the original plane: "does this composition leak" is hard to answer
by inspecting instances one at a time, easy once restated as "is this boolean formula satisfiable" and
handed to a solver that searches the whole space at once.

## Scope, honestly

This reproduces THREE known results from `sieve.py`'s live run against `SEED` — the `degree ∘ negation`
leak (`forms_discourse.md` §4.2) and the `ask`/`language` leaks from `forms_discourse.md` §8's worked
failure ("map the question perfectly, then assert it") — symbolically, as a validation that the
encoding is faithful to what `units/forms.py` actually does, and that guarding fixes all three by
proof rather than by sample. It does **not** yet prove anything past what exhaustive enumeration
already covers for a domain this small — the payoff is the INFRASTRUCTURE this sets up, not a new
result yet. Extending to `conditional` (relational, touches a second node) needs uninterpreted
functions; extending to genuine n-ary/unbounded composition needs an inductive argument over this
encoding, not just more enumeration — neither attempted here.
"""
from __future__ import annotations

import z3

# -- the symbolic claim: one claim's attributes, as free variables, not one concrete instance ----

Polarity, (POS, NEG) = z3.EnumSort("Polarity", ["POS", "NEG"])
Force, (ASSERT, ASK) = z3.EnumSort("Force", ["ASSERT", "ASK"])
Level, (WORLD, LANGUAGE) = z3.EnumSort("Level", ["WORLD", "LANGUAGE"])

polarity = z3.Const("polarity", Polarity)
force = z3.Const("force", Force)
level = z3.Const("level", Level)
has_degree = z3.Bool("has_degree")     # degree/hedge decorate the claim with a band; presence only


def fires(guarded: bool) -> dict:
    """Does this elimination fire, for this symbolic (unconstrained) claim?

    Mirrors `claim_pattern` + each `_X_elim`'s pattern in `units/forms.py` exactly: naive asks about
    its own field only; guarded additionally requires force=assert, level=world, and — for degree —
    polarity=pos, straight off `_positive_elim` / `_negation_elim` / `_degree_elim`."""
    base = z3.And(force == ASSERT, level == WORLD) if guarded else z3.BoolVal(True)
    return {
        "positive": z3.And(polarity == POS, base),
        "negation": z3.And(polarity == NEG, base),
        "degree": z3.And(has_degree, base, polarity == POS) if guarded
                  else z3.And(has_degree, base),
    }


def conclusions(guarded: bool) -> dict:
    """What the SUBJECT ends up bearing. `dangerous`/`not_dangerous` mirror `PREDICATE`/
    `not_{PREDICATE}` in `units/forms.py`."""
    f = fires(guarded)
    return {"dangerous": z3.Or(f["positive"], f["degree"]), "not_dangerous": f["negation"]}


def forbids_violated(guarded: bool) -> dict:
    """Each form's `forbids`, restated as a formula over the free variables above."""
    c = conclusions(guarded)
    says_anything = z3.Or(c["dangerous"], c["not_dangerous"])
    return {
        # NEGATION.forbids: "{PREDICATE} still reads True under a denial"
        "negation": z3.And(polarity == NEG, c["dangerous"]),
        # ASK.forbids: "asking it committed the system: ..." (forms_discourse.md §8's worked failure)
        "ask": z3.And(force == ASK, says_anything),
        # LANGUAGE.forbids: "a claim about the WORD committed the system: ..."
        "language": z3.And(level == LANGUAGE, says_anything),
    }


def check(guarded: bool) -> list[tuple[str, str, dict | None]]:
    """Returns (name, sat/unsat, witness-or-None) for every forbids in this mode."""
    out = []
    for name, formula in forbids_violated(guarded).items():
        solver = z3.Solver()
        solver.add(formula)
        result = solver.check()
        witness = None
        if result == z3.sat:
            m = solver.model()
            witness = {"polarity": str(m[polarity]), "force": str(m[force]),
                       "level": str(m[level]), "has_degree": m.eval(has_degree)}
        out.append((name, str(result), witness))
    return out


def report() -> str:
    lines = []
    for guarded in (False, True):
        label = "GUARDED" if guarded else "NAIVE"
        lines.append(f"=== {label} ===")
        for name, result, witness in check(guarded):
            lines.append(f"  {name}.forbids violated, exists? {result}")
            if witness is not None:
                lines.append(f"    witness: {witness}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
