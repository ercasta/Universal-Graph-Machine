"""The DEFINITION surface — `define H as B` / `define H iff B`
(docs/design/meaning_surfaces_audit.md §4; the "define meaning and use it" capability).

A definition is a rule; this is its NAMED, prose-adjacent surface, and the one place the two directions
of meaning are authored together:

  * `define  H  as  B`   — the SUFFICIENT direction only: `H when B` (an ordinary rule). The definiens
    entails the definiendum.
        define ?x grandparent ?z as ?x parent ?y and ?y parent ?z
  * `define  H  iff  B`  — the BICONDITIONAL: the sufficient rule PLUS the NECESSARY direction
    `H ⇒ B`, with every body variable NOT in the head existentially witnessed by a SHARED skolem (one
    witness satisfying all the body atoms — `parent(x,w) ∧ parent(w,z)`, not two separate w's). This is
    the genuinely new ergonomic: both directions from one statement, the necessary side riding the
    bound-literal skolem the engine already resolves on demand (binder spike E1/E2).

WHY REUSE `load_machine_rules`. The body/head grammar is exactly the rule grammar (`S P O`, `and`,
`not S P O`); a definition differs only in the CONNECTIVE (`as`/`iff` vs `when`) and the extra
necessary rule. So `define H as B` is rewritten to `H when B` and parsed by the one rule parser — no
second grammar. The necessary rule is built structurally from the parsed sufficient rule.

The QUOTE token (`'?a`, production_rule §QUOTE) is what would let a `define` author a META-PATTERN
(`define transitive R …`, a rule that writes a rule) in this same surface — enabled at the engine
level, left as a follow-on surface here so the first slice stays the ordinary/`iff` definition.
"""
from __future__ import annotations

from ..production_rule import Pat, Rule, is_var
from .machine_rules import load_machine_rules


def _split_on(tokens: list[str], connective: str) -> tuple[str, str] | None:
    """`H <connective> B` split at the FIRST standalone `connective` token → (H_text, B_text), or None
    if the connective is absent. Whitespace-joined back to text for the rule parser."""
    for i, t in enumerate(tokens):
        if t == connective:
            if i == 0 or i == len(tokens) - 1:
                return None                                # `define as …` / `… iff` — malformed
            return " ".join(tokens[1:i]), " ".join(tokens[i + 1:])
    return None


def _necessary(fwd: Rule) -> Rule:
    """The NECESSARY-direction rule of a biconditional: `H ⇒ B`, with each body variable NOT in the
    head turned into a SHARED bound-literal skolem (`?y → y?`) — one witness across all body atoms,
    anchored to the head-bound endpoints so it is a sound skolem FUNCTION of the match. `fwd` is the
    sufficient rule (`lhs = B`, `rhs = H`)."""
    head_vars = {t for p in fwd.rhs for t in p.tokens() if is_var(t)}

    def witness(tok: str) -> str:
        return (tok[1:] + "?") if (is_var(tok) and tok not in head_vars) else tok

    rhs = [Pat(witness(p.s), p.p, witness(p.o)) for p in fwd.lhs]
    return Rule(key=f"{fwd.key}.necessary", lhs=list(fwd.rhs), rhs=rhs)


def parse_definition(text: str) -> list[Rule] | None:
    """`define H as B` → `[sufficient]`; `define H iff B` → `[sufficient, necessary]`. `None` if the
    line is not a `define …` at all (so intake falls through). Raises `ValueError` on a `define` line
    whose head/body will not parse — a definition that silently does nothing is worse than a loud one."""
    tokens = text.strip().split()
    if not tokens or tokens[0] != "define":
        return None

    for connective, biconditional in (("iff", True), ("as", False)):
        parts = _split_on(tokens, connective)
        if parts is None:
            continue
        head_text, body_text = parts
        rules = load_machine_rules(f"{head_text} when {body_text}")
        if not rules:
            raise ValueError(f"define: could not parse the definition body of {text!r} "
                             f"(head {head_text!r}, body {body_text!r})")
        out: list[Rule] = []
        for fwd in rules:
            suff = Rule(key=f"def.{fwd.key}", lhs=fwd.lhs, rhs=fwd.rhs, nac=fwd.nac,
                        graded=fwd.graded, value_matches=fwd.value_matches, distinct=fwd.distinct)
            out.append(suff)
            if biconditional:
                out.append(_necessary(suff))
        return out

    return None                                            # `define` with no `as`/`iff` connective is
                                                          # not a well-formed definition — fall through
                                                          # (intake reports it `unrecognized` with hints),
                                                          # rather than hijack every line starting "define".
