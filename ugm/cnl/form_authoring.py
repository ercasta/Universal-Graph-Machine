"""
Form authoring — extending the acceptance grammar in CNL (Phase 9,
docs/design/form_authoring_design.md).

A recognition FORM is an ordinary `Rule` over the token-chain vocabulary (`first`/`next` +
bound-literal keyword tokens), and rule-source CNL already spans that language (the machine
grammar accepts `is?` / `<query>?` in any S/P/O slot — the design's §1 enabling finding). So
authoring a form needs no new rule language, only:

  1. a NAMING surface — `form KEY : HEAD when BODY` — because forms carry load-bearing stable
     keys (`ask.yesno.is_a`: rule_control disable, nearest-forms, tests) where machine rules
     mint digest keys. The `form KEY :` header folds `rl_key` onto the rule node
     (`FORM_HEADER_FORMS`); `expand_rules` uses it when present.
  2. a RECOGNITION-SAFETY lint — a form's conditions read the utterance's token chain, never
     fact structure. An LHS/NAC pattern over a non-scaffolding predicate would be a domain rule
     firing at recognition time; reject it loudly (`lint_recognition_safe`).
  3. KEY-MERGE semantics — under multi-KB-file loading, re-declaring a form is the NORMAL case:
     same key + identical rule = idempotent no-op; same key + different rule = loud conflict
     (`merge_forms`).

The header runs as a PRIOR STRATUM (its own `run_bank`, to fixpoint, before the machine
grammar): `mrule.start` fires on any sentence's first token, so on a `form …` line it would
mint a spurious rule for the `form` token itself. The header stratum tags that token
(`form_hdr`), and `mrule.start`'s NAC on the tag defers — race-free because strata are
sequential fixpoints, the same tag-then-use discipline as every other grammar.

Surface notes (same tokenizer contract as all CNL): the `:` must be whitespace-separated
(`form KEY : …`); keys are lowercased like every token. A line in a form bank that is NOT a
recognized `form KEY :` declaration is a loud error, never a silently-keyless rule.
"""
from __future__ import annotations

from .forms import SCAFFOLD_PREDS, load_text
from .authoring import expand_rules, machine_rule_defects, reject_rhs_only_head_vars
from .machine_rules import MACHINE_RULE_FORMS, _lift_distinct
from ..production_rule import Pat, Rule, binder, is_var, literal_name
from ..lowering import run_bank
from ..world_model import Graph


# ---------------------------------------------------------------------------
# The naming surface — `form KEY : HEAD when BODY`
# ---------------------------------------------------------------------------

FORM_HEADER_FORMS: list[Rule] = [
    # `form KEY : <first head token> …` — fold the key onto a fresh rule node and hand the
    # token after `:` to the machine head grammar (`head_subj`, exactly where `mrule.start`
    # would have started). Tag the leading `form` token so `mrule.start` defers (its NAC).
    Rule(
        key="form.header",
        lhs=[Pat("?s", "first", "form?"), Pat("form?", "next", "?k"),
             Pat("?k", "next", ":?"), Pat(":?", "next", "?cs")],
        rhs=[Pat("form?", "form_hdr", "yes"),
             Pat("<rule>?", "rl_key", "?k"), Pat("?cs", "head_subj", "<rule>?")],
    ),
]


# ---------------------------------------------------------------------------
# The recognition-safety lint
# ---------------------------------------------------------------------------

# What a form's CONDITIONS may read: the token chain and the recognition-time tags — the
# scaffolding predicates (`first`/`next` + the surface tags) plus the question grammar's
# keyword tag. All ephemeral utterance structure, never facts.
ALLOWED_LHS_PREDS: frozenset[str] = frozenset(SCAFFOLD_PREDS) | {"is_kw"}


def lint_recognition_safe(rules: list[Rule], *, source: str = "form authoring") -> None:
    """Raise unless every LHS/NAC pattern of every rule reads ONLY token-chain scaffolding.

    A recognition form's conditions must read the utterance (the `next`/`first` chain and its
    surface tags), never the KB: a condition over a content predicate (`?x likes ?y`) or a
    VARIABLE predicate (`?x ?p ?y`) is a domain rule wearing a form's clothes — it would fire
    against fact structure at recognition time. Reject loudly, naming the pattern. (The RHS is
    unrestricted: writing canonical relations onto content tokens IS what a form does.)"""
    for r in rules:
        for where, pats in (("condition", r.lhs), ("`not` condition", r.nac)):
            for pat in pats:
                if is_var(pat.p):
                    raise ValueError(
                        f"{source}: form '{r.key}' has a {where} with a VARIABLE predicate "
                        f"(`{pat.s} {pat.p} {pat.o}`) — a form's conditions read the token "
                        "chain, and a free-predicate pattern reads arbitrary structure. Bind "
                        "the predicate slot as a chain OBJECT (`?qs next ?qp`), not as a "
                        "pattern predicate.")
                name = literal_name(pat.p)
                if name not in ALLOWED_LHS_PREDS:
                    raise ValueError(
                        f"{source}: form '{r.key}' has a {where} reading predicate '{name}' "
                        f"(`{pat.s} {pat.p} {pat.o}`), which is not token-chain scaffolding "
                        f"({sorted(ALLOWED_LHS_PREDS)}). A recognition form reads the "
                        "utterance's token chain, never fact structure — a condition over a "
                        "content predicate belongs in a domain RULE, not a form.")


# ---------------------------------------------------------------------------
# Key-merge semantics — idempotent on identity, loud on conflict
# ---------------------------------------------------------------------------

def _same_form(a: Rule, b: Rule) -> bool:
    """Structural identity for idempotent re-declaration (dataclass equality covers every
    field; keys are already equal when this is asked)."""
    return a == b


def merge_forms(existing: list[Rule], new: list[Rule], *,
                source: str = "form authoring") -> list[Rule]:
    """`existing` + the genuinely-new rules of `new` (design D5).

    Same key + identical rule -> skipped (idempotent — under multi-KB-file loading,
    re-declaring a shared form is the NORMAL case, not an error). Same key + a DIFFERENT rule
    -> loud `ValueError` (two meanings for one key would make disable/nearest-forms/provenance
    ambiguous). Duplicates WITHIN `new` are folded by the same semantics."""
    by_key: dict[str, Rule] = {r.key: r for r in existing}
    out = list(existing)
    for r in new:
        prev = by_key.get(r.key)
        if prev is None:
            by_key[r.key] = r
            out.append(r)
        elif not _same_form(prev, r):
            raise ValueError(
                f"{source}: form key '{r.key}' is already declared with a DIFFERENT rule — "
                "re-declaring a key is only allowed with the identical form (idempotent "
                "reload). Pick a new key, or `disable` the existing form first.")
    return out


# ---------------------------------------------------------------------------
# The loader
# ---------------------------------------------------------------------------

def load_forms(text: str) -> list[Rule]:
    """Parse a form bank (`form KEY : HEAD when BODY` lines) into executable recognition
    `Rule`s (tokenize -> header stratum -> machine grammar -> expand -> lints).

    Every line must be a recognized `form KEY :` declaration — a line that folds to a rule
    WITHOUT an authored key was not one (e.g. the `:` not whitespace-separated) and is a loud
    error, never a silently digest-keyed rule. Duplicate keys within one text fold by the
    `merge_forms` semantics (identical -> one; different -> conflict). Blank/`#` lines skipped.

    The returned rules are ordinary recognition forms: pass them where forms already flow —
    `recognize`/`ask`/`ask_goal` `extra_forms=` today; the intake bank assembly in Slice B."""
    body = "\n".join(s for line in text.splitlines()
                     if (s := line.strip()) and not s.startswith("#"))
    rg = Graph()
    load_text(rg, body)
    run_bank(rg, FORM_HEADER_FORMS)      # prior stratum: fold keys + tag `form` leads
    run_bank(rg, MACHINE_RULE_FORMS)     # the ordinary rule-source grammar does the rest
    defects = machine_rule_defects(rg)   # report a non-triple clause, never silently mangle
    if defects:
        raise ValueError(
            "form grammar could not fold these clause(s) to a full `S P O` triple: "
            + "; ".join(f"'{c}'" for c in defects)
            + ". Every head and body clause must be exactly `S P O` (or `drop S P O` / "
            "`not S P O`).")
    rules = _lift_distinct(expand_rules(rg))
    reject_rhs_only_head_vars(rules, source="load_forms")
    authored = _authored_keys(rg)
    unkeyed = [r.key for r in rules if r.key not in authored]
    if unkeyed:
        raise ValueError(
            f"load_forms: line(s) folded without a `form KEY :` header (got digest key(s) "
            f"{unkeyed}). Every line of a form bank must be a `form KEY : HEAD when BODY` "
            "declaration — check that the `:` is whitespace-separated.")
    merged: list[Rule] = merge_forms([], rules, source="load_forms")
    lint_recognition_safe(merged, source="load_forms")
    return merged


def _authored_keys(rg: Graph) -> set[str]:
    """The key names the header stratum folded (`<rule> --rl_key--> KEY-token`)."""
    keys: set[str] = set()
    for n in rg.nodes():
        for rel, obj in rg.relations_from(n):
            if rg.has_key(rel, "rl_key"):
                keys.add(rg.name(obj))
    return keys


# ---------------------------------------------------------------------------
# Slice B plumbing — the intake route discriminator, D3 placement, the session grammar
# ---------------------------------------------------------------------------

def parse_form_line(text: str) -> list[Rule] | None:
    """None unless the `form KEY :` HEADER form fires on `text` — the intake route
    discriminator (§D.2: routed by which form fired, never a string sniff); the fully parsed
    form(s) otherwise. A fired header with a malformed body RAISES loudly (`load_forms`),
    exactly like the rule route's loader — never a silent fall-through to the fact route."""
    tmp = Graph()
    load_text(tmp, text)
    run_bank(tmp, FORM_HEADER_FORMS)
    if not _authored_keys(tmp):
        return None
    return load_forms(text)


def is_question_form(rule: Rule) -> bool:
    """Does this form mint a question pattern (`<query>`/`<qevent>` head)? The D3
    bank-placement discriminator, read from the form's OWN RHS structure (never a keyword
    list): a question form joins recognition/answering as `extra_forms`; a declarative form
    joins the fact-recognition bank (`load_facts(extra_forms=…)`)."""
    return any(literal_name(p.s) in ("<query>", "<qevent>") for p in rule.rhs)


# The session-grammar register: the authored forms of a live KB, a plain register value like
# `kb.registers["policy"]` (mechanism side — stepping state, not explanation). Persistence is
# the CNL lines themselves (design D4): replaying the transcript rebuilds this register.
FORMS_REGISTER = "forms"


def session_forms(kb) -> list[Rule]:
    """The forms this session has authored (`form KEY : …` utterances / loaded KB-file lines),
    in declaration order. Callers filter through `rule_control.active_rules` so a disabled
    form neither recognizes nor suggests."""
    return list(kb.registers.get(FORMS_REGISTER, []))
