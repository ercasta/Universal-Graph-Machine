"""
SPIKE — §7 of `design/homoiconic_grammar.md`: should composition MINT a distinct entity?

THE PROBLEM, restated from real data. `forms.py` §2 decomposes a modified noun phrase onto its
HEAD — `the african lion` -> head `lion` + `lion is african`, never an opaque `african_lion` —
because "structure is exposed to reasoning, not hidden in an opaque string". On a taxonomy corpus
that merges every subspecies onto ONE `lion` node, so the fold slice wrote BOTH

    lion has     mane        (from the Bengal lion)
    lion has_not mane        (from the Guzerat lion)

onto the same entity: a contradiction manufactured by the grammar, not asserted by the source.

THE FALSE DICHOTOMY. The choice was never "decompose onto the head" vs "mint an opaque string".
There is a third option that keeps decomposition COMPLETELY intact — mint a distinct node and
write the decomposition AS ITS DESCRIPTION:

    <e> is_a lion            <- the head, still exposed as subsumption
    <e> is   guzerat         <- the modifier, still exposed as an attribute
    <e> has_not mane         <- the exception, on its own entity

Nothing is hidden in a string; you can still ask "is it a lion?" and "what is guzerat about it?".
What changes is only WHICH NODE carries it. And the node is NAMELESS, per the precedent the user
set in feedback #15 ("the substrate is supposed to be nameless" — no fabricated `guzerat_lion`
skolem names): identity is the DEFINING RELATIONS, which is exactly `ByDesc`/`_find_skolem_witness`'s
existing identity law, not a new concept.

This also produces the structure the defeasible-exception arc needs and never had: a generalization
on the superkind, an exception on the subkind, and an `is_a` edge linking them so the exception is
REACHABLE from the generalization.

One new declaration carries it, and the rest of the semantics is unchanged:

    mint head in np from modifier plus np under right head

Run: python bench/spike_grammar_subkind.py
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, Pat, Rule, run_bank
from ugm.cnl.authoring import load_facts
from ugm.cnl.forms import _fold_node

from spike_homoiconic_grammar import ROOT, ambiguity_bank, chart_bank, read_grammar
from spike_grammar_fold import (ASSERT_FORMS, GRAMMAR_CNL, SLOT_FORMS, assert_bank, fold,
                                mint_bank, read_semantics, slot_bank, today)
import spike_grammar_fold as F


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# The one new declaration form
# ---------------------------------------------------------------------------
#
# `mint <slot> in <cat> from <X> plus <Y> under <left|right> <childslot>`
#
# "the <slot> of this span is a FRESH entity, subsumed by the named child slot". Everything else —
# the `attr` slot, the `np asserts head is attr` assertion — is untouched, so the decomposition
# still happens; it just lands on the minted node.

MINT_FORM: list[Rule] = [
    Rule(
        key="gram.mint",
        lhs=[Pat("?s", "first", "mint?"), Pat("mint?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "plus?"), Pat("plus?", "next", "?y"),
             Pat("?y", "next", "under?"), Pat("under?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<mint>?", "mname", "?name"), Pat("<mint>?", "mcat", "?z"),
             Pat("<mint>?", "mleft", "?x"), Pat("<mint>?", "mright", "?y"),
             Pat("<mint>?", "mside", "?side"), Pat("<mint>?", "mcslot", "?cslot")],
    ),
]


# The grammar, with ONE line changed: the modified-NP head is minted, not percolated.
SUBKIND_CNL = GRAMMAR_CNL.replace(
    "slot head in np from modifier plus np is right head",
    "mint head in np from modifier plus np under right head")


def read_mints(text: str):
    g = AttrGraph()
    load_facts(g, text, extra_forms=F.DECL_FORMS + MINT_FORM)
    out = []
    for n in g.nodes():
        d = {}
        for r, o in g.relations_from(n):
            for k in ("mname", "mcat", "mleft", "mright", "mside", "mcslot"):
                if g.has_key(r, k):
                    d[k] = g.name(o)
        if "mname" in d:
            out.append(d)
    return out


def mint_slot_bank(mint_decls) -> list[Rule]:
    """A rule per `mint` declaration: the parent's slot becomes a FRESH NAMELESS node, subsumed by
    the child slot it was declared under.

    The minted node is an RHS-only variable, which is what makes it nameless — `lower_rhs` gives a
    bound-literal a name and a plain literal graph-wide interning, but a bare `?e` mints an unnamed
    node per firing. That is the ByDesc identity law: no name to be addressed by, always the
    defining relations it was minted with."""
    rules: list[Rule] = []
    for i, d in enumerate(mint_decls):
        z, x, y = d["mcat"], d["mleft"], d["mright"]
        src = "?l" if d["mside"] == "left" else "?r"
        rules.append(Rule(
            key=f"fold.mint_entity.{i}.{z}",
            lhs=[Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?l", "cat", x), Pat("?l", "begin", "?a"), Pat("?l", "end", "?m"),
                 Pat("?r", "cat", y), Pat("?r", "begin", "?m"), Pat("?r", "end", "?b"),
                 Pat(src, d["mcslot"], "?v")],
            rhs=[Pat("?e", "is_a", "?v"), Pat("?p", d["mname"], "?e")]))
    return rules


# ---------------------------------------------------------------------------
# Reading a nameless entity back: description, not name
# ---------------------------------------------------------------------------

DEFINING = ("is_a", "is")          # the relations a minted entity's identity consists of


def describe(g, n: str) -> str:
    """Render a node: its name, or — for a minted entity — its defining description."""
    nm = g.name(n)
    if nm:
        return nm
    parts = sorted({f"{g.predicate(r)} {g.name(o)}" for r, o in g.relations_from(n)
                    if g.predicate(r) in DEFINING and g.name(o)})
    return f"<{' & '.join(parts)}>" if parts else "<anon>"


def facts_of(g, new_only=None) -> list[tuple[str, str, str]]:
    out = []
    for s in g.nodes():
        if g.is_control(s) or g.is_inert(s):
            continue
        for r, o in g.relations_from(s):
            if g.is_control(r) or g.is_inert(r) or (new_only is not None and r in new_only):
                continue
            if g.predicate(r) in ("cat", "begin", "end", "head", "next", "first"):
                continue
            if not (g.name(o) or describe(g, o) != "<anon>"):
                continue
            out.append((describe(g, s), g.predicate(r), describe(g, o)))
    return sorted(set(out))


def intern_described(g, defining=DEFINING) -> int:
    """Coalesce NAMELESS entities that share a description — the description-keyed counterpart of
    `intern_mentions` (which is name-keyed and therefore blind to these).

    Keyed on the DEFINING relations only, not on everything the node has since acquired: two
    mentions of the same subkind must intern even when each has learned different facts. Returns
    the number of nodes folded away."""
    groups: dict[frozenset, list[str]] = {}
    for n in list(g.nodes()):
        if g.name(n) or g.is_control(n) or g.is_inert(n):
            continue
        desc = frozenset((g.predicate(r), g.name(o)) for r, o in g.relations_from(n)
                         if g.predicate(r) in defining and g.name(o))
        if desc:
            groups.setdefault(desc, []).append(n)
    folded = 0
    for members in groups.values():
        for victim in members[1:]:
            _fold_node(g, members[0], victim)
            folded += 1
    return folded


def build(cnl: str):
    lex, unary, binary = read_grammar(cnl)
    slot_decls, assertions = read_semantics(cnl)
    mints = read_mints(cnl)
    chart, cpreds = chart_bank(lex, unary, binary)
    amb, apreds = ambiguity_bank(unary, binary)
    cats = {z for z, _ in unary} | {z for z, *_ in binary} \
        | {x for _, x, y in binary for x in (x, y)} | {x for _, x in unary} | {ROOT}
    mint, mpreds = mint_bank(cats)
    slots, spreds = slot_bank(slot_decls)
    slots = slots + mint_slot_bank(mints)
    asserts = assert_bank(assertions, set(spreds) | {"head"}, set(lex))
    return (chart, cpreds, amb, apreds, mint, mpreds | {"head"}, slots, spreds, asserts), mints


CORPUS = [
    "the lion has a mane",                     # the generalization, on the superkind
    "the guzerat lion has no mane",            # the exception, on the subkind
    "the guzerat lion is smaller than the tiger",   # a SECOND mention of the same subkind
]


def main() -> None:
    hdr("0  THE CHANGE — one declaration line")
    stages_old, _ = build(GRAMMAR_CNL)
    stages_new, mints = build(SUBKIND_CNL)
    print("  before: slot head in np from modifier plus np is right head")
    print("  after : mint head in np from modifier plus np under right head")
    print(f"\n  mint declarations read back: {mints}")
    if not mints:
        print("  !! the mint form did not read back — nothing below is meaningful")
        return

    hdr("1  THE MANUFACTURED CONTRADICTION, BEFORE AND AFTER")
    for label, stages in (("BEFORE (decompose onto head)", stages_old),
                          ("AFTER  (mint a described subkind)", stages_new)):
        g = AttrGraph()
        for line in CORPUS[:2]:
            fold(line, stages, g)
        print(f"\n    {label}")
        for t in facts_of(g):
            print(f"        {t}")

    hdr("2  IS THE EXCEPTION REACHABLE FROM THE GENERALIZATION?")
    print("  The point of minting is not tidiness — it is that `<e> is_a lion` makes the exception")
    print("  a WITNESS of the generalization, so it can refute it. Under decomposition there was")
    print("  no second entity to be a counterexample at all.\n")
    g = AttrGraph()
    for line in CORPUS[:2]:
        fold(line, stages_new, g)
    law = Rule(key="gen.mane", lhs=[Pat("?x", "is_a", "lion")], rhs=[Pat("?x", "has", "mane")])
    witnesses = [n for n in g.nodes()
                 for r, o in g.relations_from(n)
                 if g.predicate(r) == "is_a" and g.name(o) == "lion"]
    print(f"    candidate law      : ?x has mane when ?x is_a lion")
    print(f"    witnesses of is_a lion : {[describe(g, w) for w in witnesses]}")
    for w in witnesses:
        neg = [g.name(o) for r, o in g.relations_from(w) if g.predicate(r) == "has_not"]
        if neg:
            print(f"    COUNTEREXAMPLE     : {describe(g, w)} has_not {neg}")
    print("\n    -> the generalization and its counterexample now stand on DIFFERENT nodes,")
    print("       linked by is_a. That is the shape the defeasible-exception arc needs.")

    hdr("3  CROSS-SENTENCE IDENTITY — description-keyed interning")
    print("  A nameless node is minted PER FIRING, so two mentions of `the guzerat lion` are two")
    print("  nodes. Name-keyed `intern_mentions` cannot see them. The counterpart tool interns on")
    print("  the DEFINING relations instead — ByDesc's identity law, applied as a loader pass.\n")
    g = AttrGraph()
    for line in CORPUS:
        fold(line, stages_new, g)
    anon = [n for n in g.nodes() if not g.name(n) and not g.is_control(n) and not g.is_inert(n)
            and any(g.predicate(r) in DEFINING for r, _o in g.relations_from(n))]
    print(f"    nameless entities before interning: {len(anon)}   (2 mentions in the corpus —")
    print("      the excess is VALUE INVENTION RE-FIRING: this spike re-runs the banks over the")
    print("      whole accumulating graph per sentence, and an RHS-only `?e` mints a fresh node")
    print("      every run. That is the finding, not an artifact to wave away: minting is not")
    print("      idempotent across runs, so description-interning is REQUIRED for correctness in")
    print("      an accumulating KB, not merely a tidy-up.)")
    folded = intern_described(g)
    anon2 = [n for n in g.nodes() if not g.name(n) and not g.is_control(n) and not g.is_inert(n)
             and any(g.predicate(r) in DEFINING for r, _o in g.relations_from(n))]
    print(f"    folded away                       : {folded}")
    print(f"    nameless entities after           : {len(anon2)}")
    print("\n    the KB, after the whole 3-sentence corpus:")
    for t in facts_of(g):
        print(f"        {t}")

    hdr("4  WHAT THE SHIPPED BANK DOES WITH THE SAME CORPUS")
    for line in CORPUS:
        print(f"    {line:44} -> {today(line)}")


if __name__ == "__main__":
    main()
