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

from ..production_rule import Pat, Rule, is_var, QUOTE
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


# ---------------------------------------------------------------------------
# META-PATTERN: `define schema <trigger> : <template>` — a rule that WRITES a rule
# ---------------------------------------------------------------------------
# The deepest form of "define meaning": a user DEFINES what a relation-property MEANS — `transitive`,
# `symmetric`, … — as a rule TEMPLATE parameterised over a relation, in the language itself. Enabled by
# the QUOTE token (production_rule §QUOTE): the meta-rule's RHS writes the template's flat-schema with
# every template-only variable QUOTED (so the WRITTEN rule reads it back as a variable) and every
# TRIGGER variable bound (so it flows the matched relation into the written rule). The in-language
# replacement for the Python relation-property expanders (`rule_graph._property_rule`).
#
#   define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c
#
# then `ancestor is transitive` (an ordinary fact) makes the meta-rule write the concrete transitivity
# rule for `ancestor`. The PRINCIPLE that decides quote-vs-bind: a template variable that appears in the
# TRIGGER is BOUND (the parameter, e.g. `?r`); one that does not is QUOTED (a variable of the written
# rule, e.g. `?a`/`?b`/`?c`).

def _parse_trigger(text: str) -> Pat:
    """A schema TRIGGER is a single `S P O` atom (`?r is transitive`), collapsing `is a` → `is_a`."""
    toks, out, i = text.split(), [], 0
    while i < len(toks):
        if toks[i] == "is" and i + 1 < len(toks) and toks[i + 1] == "a":
            out.append("is_a"); i += 2
        else:
            out.append(toks[i]); i += 1
    if len(out) != 3:
        raise ValueError(f"schema trigger must be a single 'S P O' atom (e.g. '?r is transitive'), "
                         f"got {text!r}")
    return Pat(out[0], out[1], out[2])


def compile_schema(trigger_text: str, template_text: str) -> Rule:
    """Compile `<trigger> : <template>` into the META-RULE that, run forward, WRITES the concrete rule
    for each relation the trigger matches. `template_text` is an ordinary `H when B` rule using the
    trigger's parameter variable(s) as its predicate; the meta-rule reifies it as the flat `<cond>`
    schema (`learner.py` / `authoring.expand_rules`), quoting every template-only variable."""
    trig = _parse_trigger(trigger_text)
    template = load_machine_rules(template_text)
    if not template:
        raise ValueError(f"schema template must be a rule 'H when B', got {template_text!r}")
    T = template[0]
    params = {t for t in trig.tokens() if is_var(t)}       # trigger vars = bound parameters

    def slot(tok: str) -> str:
        if tok in params:
            return tok                                     # a parameter: bound, flows the match through
        return (QUOTE + tok) if is_var(tok) else tok       # template-only var → quoted; literal → itself

    rhs: list[Pat] = [Pat("<mr>?", "rl_key", trig.s)]      # key the written rule by the matched relation
    for i, a in enumerate(T.lhs):
        c = f"<c{i}>?"
        rhs += [Pat("<mr>?", "rl_lhs", c), Pat(c, "k_subj", slot(a.s)),
                Pat(c, "k_pred", slot(a.p)), Pat(c, "k_obj", slot(a.o))]
    for j, a in enumerate(T.rhs):
        h = f"<ch{j}>?"
        rhs += [Pat("<mr>?", "rl_head", h), Pat(h, "k_subj", slot(a.s)),
                Pat(h, "k_pred", slot(a.p)), Pat(h, "k_obj", slot(a.o))]
    return Rule(key=f"schema.{trig.p}.{trig.o}", lhs=[trig], rhs=rhs)


def parse_schema(text: str) -> Rule | None:
    """`define schema <trigger> : <template>` → the meta-rule; `None` if not a schema line. Raises on a
    `define schema …` whose trigger/template will not parse (clear intent, loud failure)."""
    stripped = text.strip()
    if not stripped.startswith("define schema "):
        return None
    body = stripped[len("define schema "):]
    if ":" not in body:
        raise ValueError(f"define schema needs a ':' between trigger and template — "
                         f"`define schema <trigger> : <template>` (got {text!r})")
    trigger_text, template_text = body.split(":", 1)
    return compile_schema(trigger_text.strip(), template_text.strip())


SCHEMAS = "<schemas>"                # register: the stored schema meta-rules
_HARVESTED = "<schema-harvested>"    # register: keys of concrete rules already harvested


def store_schema(kb, meta: Rule) -> None:
    """Remember a schema meta-rule on the KB (a register, not a graph fact — a meta-rule is machinery,
    never reasoned over as a fact). It is RE-run against every later triggering declaration."""
    kb.registers.setdefault(SCHEMAS, []).append(meta)


def apply_schemas(kb, rules: list[Rule]) -> list[Rule]:
    """Run every stored schema meta-rule forward over `kb` and harvest the concrete rules they wrote,
    adding each new one (once) to `rules` so the demand chain reasons with it. Called after a fact
    assertion: a `?r is transitive` fact fires the matching schema, materialising the transitivity rule
    for that relation. The harvest is exact — on a live intake KB `expand_rules` sees ONLY the schemas'
    flat-`<cond>` output (nothing else writes that schema), and `_HARVESTED` dedups across turns."""
    schemas = kb.registers.get(SCHEMAS)
    if not schemas:
        return []
    from .authoring import expand_rules
    from ..lowering import run_bank
    run_bank(kb, list(schemas))
    harvested = kb.registers.setdefault(_HARVESTED, set())
    known = harvested | {r.key for r in rules}
    new = [r for r in expand_rules(kb) if r.key not in known]
    for r in new:
        harvested.add(r.key)
    rules.extend(new)
    return new
