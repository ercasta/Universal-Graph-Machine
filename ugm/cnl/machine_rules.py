"""
Machine rule CNL — a uniform triple-grammar for control/machinery rules (vision §3/§4).

Control machinery — walkers, dispatch, planning — needs a multi-clause head and `drop`
that prose doesn't express, and is honestly not prose anyway. So this module adds a
deliberately-formal HEAD surface, but the BODY / condition grammar is now the SHARED spine
(`authoring.BODY_SPINE_FORMS`) that the prose surface uses too — grammar unification, so
there is ONE condition grammar and the two surfaces differ only in the head:

    H1 and H2 and ... and Hk   when   B1 and B2 and ... and Bm

  - every clause is a bare triple `S P O` (G1: ANY predicate, not a fixed menu);
  - the HEAD is a CONJUNCTION of clauses (G2: multi-triple consequent);
  - a head clause `drop S P O` is a control deletion (G3);
  - a body clause `not S P O` is a negative condition / NAC (G4, shared spine);
  - S/P/O are any tokens: variables `?x`, bound-literal control tokens `<walker>?`
    (the `?` suffix makes it BIND — every `<walker>?` in the rule is the same node, §G5),
    or plain literals (`reached`, `is_a`, `refuel`). `is_a` is written as ONE token.

The fold is pure graph rewriting (no Python parser), region-aware so a head clause and a
body clause with the same shape don't collide: a deterministic clause-to-clause domino
flows a `head_subj`/`body_subj` marker through the separators (`and` stays in-region,
`when` switches head->body, seeding the first `body_subj` where the shared spine takes over),
and each clause is recognized LOCALLY from its subject marker. The only NACs distinguish a
`drop`/`not`-led clause from a plain one (keyed on a keyword tag); the shared body clause also
NACs `is_kw`, which is INERT here (the machine bank emits no `is_kw` tag), so machine behaviour
is unchanged. The grammar stratifies cleanly (tags first, then the clause/flow forms).

NOTE on multiple `not` clauses: like the prose grammar, all negative conditions fold into
the rule's SINGLE `nac` list — a CONJUNCTIVE negated subgraph joined by shared variables
(`not ?w subj ?a and not ?w obj ?c` = "block if some ?w has BOTH"), NOT independent
negations. That is the intended reading for the rules here; independent NACs are not
expressible (a known limit shared with the prose grammar).
"""
from __future__ import annotations

from .authoring import BODY_SPINE_FORMS, expand_rules
from .forms import load_text
from ..lowering import run_bank
from ..production_rule import Pat, Rule
from ..world_model import Graph


def _kw_tags(kw: str, tag: str) -> list[Rule]:
    """Tag every token named `kw` with `tag yes`, so a clause form can NAC it to tell a
    `drop`/`not`-led clause from a plain one. TWO forms, because a keyword can be reached
    either by `next` (mid-line, e.g. `... and drop ...`) OR by `first` (a rule that STARTS
    with a drop clause — planning's `drop M when ...`); a `first`-only tag is what a
    next-keyed rule would miss, mis-reading the leading `drop` as a clause subject."""
    return [
        Rule(key=f"mrule.kw.{kw}.next", lhs=[Pat("?t", "next", f"{kw}?")],
             rhs=[Pat(f"{kw}?", tag, "yes")]),
        Rule(key=f"mrule.kw.{kw}.first", lhs=[Pat("?s", "first", f"{kw}?")],
             rhs=[Pat(f"{kw}?", tag, "yes")]),
    ]


def _clause(subj_marker: str, role_rel: str, end_rel: str) -> Rule:
    """A plain triple clause `S P O` whose subject carries `subj_marker`: fold it onto the
    rule under `role_rel` (rl_head / rl_lhs) and mark its object with `end_rel` so the
    separator domino can continue to the next clause. NAC excludes keyword-led clauses."""
    nac = [Pat("?cs", "kw_drop", "yes")] if role_rel == "rl_head" else [Pat("?cs", "kw_not", "yes")]
    return Rule(
        key=f"mrule.clause.{role_rel}",
        lhs=[Pat("?cs", subj_marker, "?r"), Pat("?cs", "next", "?cp"), Pat("?cp", "next", "?co")],
        nac=nac,
        rhs=[Pat("?r", role_rel, "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
             Pat("<cond>?", "k_pred", "?cp"), Pat("<cond>?", "k_obj", "?co"),
             Pat("?co", end_rel, "?r")],
    )


def _keyword_clause(kw: str, subj_marker: str, role_rel: str, end_rel: str) -> Rule:
    """A keyword-led clause `<kw> S P O` (drop/not): the role-marker sits on the `<kw>`
    token; fold the FOLLOWING triple onto the rule under `role_rel`."""
    return Rule(
        key=f"mrule.clause.{kw}.{role_rel}",
        lhs=[Pat("?d", subj_marker, "?r"), Pat("?d", f"kw_{kw}", "yes"),
             Pat("?d", "next", "?cs"), Pat("?cs", "next", "?cp"), Pat("?cp", "next", "?co")],
        rhs=[Pat("?r", role_rel, "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
             Pat("<cond>?", "k_pred", "?cp"), Pat("<cond>?", "k_obj", "?co"),
             Pat("?co", end_rel, "?r")],
    )


MACHINE_RULE_FORMS: list[Rule] = [
    # The machine-specific HEAD forms (a `and`-conjunction of clauses, with `drop`). The BODY is
    # the SHARED spine (`BODY_SPINE_FORMS` from authoring) — the same generic `S P O` / `not S P O`
    # / `and`-domino grammar the prose surface uses (grammar unification). Only the head differs.

    # Create the rule node; the sentence's first token is the first HEAD clause's subject.
    Rule(key="mrule.start",
         lhs=[Pat("?s", "first", "?cs")],
         rhs=[Pat("<rule>?", "owns", "?cs"), Pat("?cs", "head_subj", "<rule>?")]),

    # Keyword tag — distinguish a `drop`-led head clause (set at step 1, before the flow). The
    # `not` tag (`kw_not`) is provided by the shared body spine.
    *_kw_tags("drop", "kw_drop"),

    # HEAD clauses: a plain create triple, or a `drop S P O` control deletion.
    _clause("head_subj", "rl_head", "head_end"),
    _keyword_clause("drop", "head_subj", "rl_drop", "head_end"),

    # Separators in the HEAD region: `and` continues the head, `when` switches to the body (seeding
    # the first `body_subj`, where the shared spine takes over).
    Rule(key="mrule.head.and",
         lhs=[Pat("?co", "head_end", "?r"), Pat("?co", "next", "and?"), Pat("and?", "next", "?ns")],
         rhs=[Pat("?ns", "head_subj", "?r")]),
    Rule(key="mrule.switch",
         lhs=[Pat("?co", "head_end", "?r"), Pat("?co", "next", "when?"), Pat("when?", "next", "?bs")],
         rhs=[Pat("?bs", "body_subj", "?r")]),

    # The shared body/condition grammar (generic `S P O`, `not S P O`, `and` domino).
    *BODY_SPINE_FORMS,
]


def load_machine_rules(text: str) -> list[Rule]:
    """Parse machine rule CNL into executable `Rule`s (tokenize -> fold -> expand).

    Runs in a private rule-source graph (NOT canonicalized — a rule's repeated `?x` must
    stay the variable `?x`, and its `<walker>?` tokens the bound-literal `<walker>`).

    Recognition runs on the ISA forward driver `run_bank` (NOT stratified): the keyword tags
    (`kw_drop`/`kw_not`) only need a token's predecessor, so they are set at the first step — long
    before the clause-by-clause flow domino reaches a `drop`/`not` token — so the clause forms' NAC
    on them is never raced. Stratifying would instead split the mutually-recursive clause/separator
    dominoes into different strata (the clause forms NAC the tags), starving the flow. Blank/`#`
    skipped.

    Recognition is on `run_bank` (the ISA forward Machine), NOT the forward `rewriter` — the "one
    engine" move (`implementation_plan.md` Phase 0.2). The PERFORMANCE blocker that kept it on
    `rewriter` was lifted by Phase 0.1 (`run_bank`'s df-seeding + bound-endpoint join driving took
    `planning.cnl` from ~89× slower to 2.6×), every output differential-proven IDENTICAL
    (`test_isa_runbank.py`)."""
    body = "\n".join(s for line in text.splitlines()
                     if (s := line.strip()) and not s.startswith("#"))
    rg = Graph()
    load_text(rg, body)
    run_bank(rg, MACHINE_RULE_FORMS)   # recognition on the ISA forward driver (Phase 0.2)
    return expand_rules(rg)
