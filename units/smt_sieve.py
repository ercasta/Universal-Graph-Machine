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

Reproduces four known results from `sieve.py`'s live runs — the `degree ∘ negation` leak
(`forms_discourse.md` §4.2), the `ask`/`language` leaks from `forms_discourse.md` §8's worked failure
("map the question perfectly, then assert it"), and `conditional`'s detachment leak, which guarding
does **not** fix (found here first, then confirmed empirically — `closed_class_inventory.md` §5).

## What "checking every combination at once" actually means here

Each attribute below (`polarity`, `force`, `level`, `has_degree`, `has_conditional`,
`antecedent_satisfied`) is left as a genuinely free/unknown variable, never fixed to one concrete
value. That already means every `check()` call asks about **every possible combination of every form
that can affect it, of any size, in one query** — there is no separate "now check triples" step needed
on top, because nothing here was ever pinned to a specific pair to begin with. What this does NOT cover:
forms not yet given a variable (extending to `conditional` needed `has_conditional`/
`antecedent_satisfied` to be added by hand; `command` needed a third `Force` value), and forms not yet
invented at all — Z3 can only reason about variables that exist in this file, never about a form nobody
has designed yet. That second limit is a design-discipline question, not something any solver query
answers.
"""
from __future__ import annotations

import z3

# -- the symbolic claim: one claim's attributes, as free variables, not one concrete instance ----

Polarity, (POS, NEG) = z3.EnumSort("Polarity", ["POS", "NEG"])
Force, (ASSERT, ASK, COMMAND) = z3.EnumSort("Force", ["ASSERT", "ASK", "COMMAND"])
Level, (WORLD, LANGUAGE) = z3.EnumSort("Level", ["WORLD", "LANGUAGE"])

polarity = z3.Const("polarity", Polarity)
force = z3.Const("force", Force)
level = z3.Const("level", Level)
has_degree = z3.Bool("has_degree")     # degree/hedge decorate the claim with a band; presence only

# -- CONDITIONAL, added after the empirical sieve found guarding does NOT fix it ------------------
#
# `has_conditional`/`antecedent_satisfied` mirror `add_antecedent` + the `when:` role. Unlike the
# forms above, `_conditional_elim`'s pattern requires `antecedent satisfied=True` in BOTH naive and
# guarded modes — the guarded/naive difference for `conditional` is only the extra polarity/force/
# level check, exactly mirroring `_conditional_elim`'s `if ctx.guarded` branch.
has_conditional = z3.Bool("has_conditional")
antecedent_satisfied = z3.Bool("antecedent_satisfied")


def fires(guarded: bool) -> dict:
    """Does this elimination fire, for this symbolic (unconstrained) claim?

    Mirrors `claim_pattern` + each `_X_elim`'s pattern in `units/forms.py` exactly: naive asks about
    its own field only; guarded additionally requires force=assert, level=world, and — for degree and
    conditional — polarity=pos, straight off `_positive_elim` / `_negation_elim` / `_degree_elim` /
    `_conditional_elim`."""
    base = z3.And(force == ASSERT, level == WORLD) if guarded else z3.BoolVal(True)
    return {
        "positive": z3.And(polarity == POS, base),
        "negation": z3.And(polarity == NEG, base),
        "degree": z3.And(has_degree, base, polarity == POS) if guarded
                  else z3.And(has_degree, base),
        "conditional": z3.And(has_conditional, antecedent_satisfied, base, polarity == POS) if guarded
                       else z3.And(has_conditional, antecedent_satisfied),
    }


def conclusions(guarded: bool) -> dict:
    """What the SUBJECT ends up bearing. `dangerous`/`not_dangerous` mirror `PREDICATE`/
    `not_{PREDICATE}` in `units/forms.py`."""
    f = fires(guarded)
    return {"dangerous": z3.Or(f["positive"], f["degree"], f["conditional"]),
            "not_dangerous": f["negation"]}


def forbids_violated(guarded: bool) -> dict:
    """Each form's `forbids`, restated as a formula over the free variables above."""
    c = conclusions(guarded)
    says_anything = z3.Or(c["dangerous"], c["not_dangerous"])
    return {
        # NEGATION.forbids: "{PREDICATE} still reads True under a denial"
        "negation": z3.And(polarity == NEG, c["dangerous"]),
        # ASK.forbids: "asking it committed the system: ..." (forms_discourse.md §8's worked failure)
        "ask": z3.And(force == ASK, says_anything),
        # COMMAND.forbids: same shape as ASK's — "commanding it committed the system: ..."
        "command": z3.And(force == COMMAND, says_anything),
        # LANGUAGE.forbids: "a claim about the WORD committed the system: ..."
        "language": z3.And(level == LANGUAGE, says_anything),
        # UNMET/CONDITIONAL.forbids: "consequent detached from an unsatisfied antecedent" — note this
        # can be triggered by ANY other form making `dangerous` true, not only by `conditional`'s own
        # (correctly gated) elimination — that is exactly the leak this predicts and the empirical
        # sieve confirms: guarding `positive`/`degree`/etc. never checks for a co-present antecedent.
        "conditional_detachment": z3.And(has_conditional, z3.Not(antecedent_satisfied), c["dangerous"]),
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
                       "level": str(m[level]), "has_degree": m.eval(has_degree),
                       "has_conditional": m.eval(has_conditional),
                       "antecedent_satisfied": m.eval(antecedent_satisfied)}
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


# -- THE INDUCTIVE STEP: does nesting one conditional inside another stay safe at ANY depth? -------
#
# `composition_grammar.md` proposes `Claim := BareClaim | RelationalClaim`, where a `RelationalClaim`'s
# `then` is itself a full `Claim` — so a conditional's consequent can be another conditional, to
# unbounded depth. Proving this safe at every depth needs an INDUCTION, not more sampling:
#
#   BASE CASE   — a BareClaim alone is safe.                    ALREADY PROVEN above (`check(True)`).
#   INDUCTIVE STEP — IF whatever sits inside `then` is already known-safe, does wrapping ONE more
#                    conditional around it stay safe?
#
# The trick: don't unroll depth 1, 2, 3 — state "the inner claim is already safe" as a plain
# ASSUMPTION (the induction hypothesis, `IH` below), and ask the solver about adding just one more
# layer on top of that assumption. If that comes back UNSAT, the argument "safe-so-far implies
# safe-one-step-further" covers every depth at once, the same way ordinary counting induction does.

outer_has_conditional = z3.Bool("outer_has_conditional")
outer_antecedent_satisfied = z3.Bool("outer_antecedent_satisfied")
inner_has_conditional = z3.Bool("inner_has_conditional")     # is `then` itself a conditional?
inner_antecedent_satisfied = z3.Bool("inner_antecedent_satisfied")
inner_dangerous = z3.Bool("inner_dangerous")   # stands for "whatever the inner claim concludes" —
                                                 # left abstract on purpose: the induction hypothesis
                                                 # constrains it below, without needing to model HOW
                                                 # the inner claim reaches that conclusion.

# The induction hypothesis: assume the inner claim, on its own, already obeys the no-detachment
# property — "if it concludes dangerous, either it isn't gated by a conditional at all, or its own
# antecedent held." This is literally the property being proven, ASSUMED one level in — the standard
# shape of an inductive hypothesis.
INDUCTION_HYPOTHESIS = z3.Implies(inner_dangerous,
                                  z3.Or(z3.Not(inner_has_conditional), inner_antecedent_satisfied))


def nested_detachment(wiring: str) -> "z3.BoolRef":
    """Two candidate ways an outer conditional's elimination could combine with an inner one.

    `"naive"` — the outer fires on its OWN antecedent and concludes the final predicate directly,
    never checking whether `then` is itself a conditional with its own unmet antecedent. This is
    the nested version of exactly the bug already found: detaching a consequent from an antecedent
    that never held.

    `"gated"` — the outer fires on its own antecedent, but what it concludes is whatever the INNER
    claim concludes (`inner_dangerous`), which — BY THE INDUCTION HYPOTHESIS above — is already
    constrained to respect the inner antecedent. The outer never bypasses the inner's own gating;
    it only "unlocks" it.
    """
    if wiring == "naive":
        dangerous_concluded = z3.And(outer_has_conditional, outer_antecedent_satisfied)
    elif wiring == "gated":
        dangerous_concluded = z3.And(outer_has_conditional, outer_antecedent_satisfied, inner_dangerous)
    else:
        raise ValueError(wiring)
    return z3.And(outer_has_conditional, outer_antecedent_satisfied,
                   inner_has_conditional, z3.Not(inner_antecedent_satisfied),
                   dangerous_concluded)


def check_inductive_step() -> str:
    lines = ["=== INDUCTIVE STEP: does nesting stay safe? ==="]
    for wiring in ("naive", "gated"):
        solver = z3.Solver()
        solver.add(INDUCTION_HYPOTHESIS)
        solver.add(nested_detachment(wiring))
        result = solver.check()
        lines.append(f"  {wiring} wiring: nested detachment exists, even assuming the inner claim "
                     f"is already safe? {result}")
        if result == z3.sat:
            m = solver.model()
            lines.append(f"    witness: outer_ante_sat={m.eval(outer_antecedent_satisfied)}, "
                         f"inner_ante_sat={m.eval(inner_antecedent_satisfied)}, "
                         f"inner_dangerous={m.eval(inner_dangerous)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
    print()
    print(check_inductive_step())
