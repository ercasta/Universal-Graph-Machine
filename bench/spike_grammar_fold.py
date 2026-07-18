"""
SPIKE — slice 1 of the homoiconic grammar arc: THE FOLD (parse -> facts).

`spike_homoiconic_grammar.py` settled ACCEPTANCE: a CNL-declared grammar generates chart rules
that parse the residual Loudon failures and REFUSE gibberish, with ambiguity detectable in-engine.
It deliberately stopped short of semantics. This slice does the fold, against the question the
design doc left open (§5.4): does this SUBSUME `FACT_FORMS`, or sit alongside it as a second
system? Semantics attached in Python would BE that second system, so the fold is declared in CNL
too — two more form families, and nothing else:

    slot head in np from determiner plus np is right head     -- how a parent's slot is filled
    slot pred in vp from intransitive is only head            -- (unary: `only`)
    clause asserts subj pred obj unless neg                   -- which slots become a FACT
    clause denies  subj pred obj when   neg                   -- ... and which become a NEGATIVE one

THE ONE ARCHITECTURAL MOVE. Slots need something to hang on, and a packed span is a relation
triple with no node a rule can bind. Minting a node per DERIVATION is the unpacked forest the
first spike measured at 5.2 s/11 tokens. So: **the chart stays packed while parsing, and identity
is minted only for the spans that survive.** The usefulness pass (built for ambiguity detection)
already names exactly the spans a complete parse uses — O(n) of them, not the whole chart — so
minting after it is linear-ish. Parsing and denotation are separated by which spans EXIST as
nodes, not by a phase wall.

Pipeline, each stage a bank run to fixpoint (the `normalize_surface` strata shape):
    tokenize -> chart -> useful + ambiguity -> [REFUSE | ASK] -> mint useful spans -> slots -> assert

Run: python bench/spike_grammar_fold.py
"""
from __future__ import annotations

import time

import ugm as h
from ugm import AttrGraph, Pat, Rule, derived_triples, neg_pred, run_bank
from ugm.cnl.authoring import load_facts
from ugm.cnl.forms import tokenize

from spike_homoiconic_grammar import (CLOSED_CLASSES, PRODUCTION_FORMS, ROOT, _chain,
                                      ambiguity_bank, chart_bank, sp)


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# The two new declaration surfaces
# ---------------------------------------------------------------------------
#
# SLOT: `slot <name> in <cat> from <X> plus <Y> is <left|right> <childslot>`
#       `slot <name> in <cat> from <X> is only <childslot>`
# The binary and unary shapes need no NAC to tell apart: after the left child, a binary line has
# `plus` and a unary line has `is`.

SLOT_FORMS: list[Rule] = [
    Rule(
        key="gram.slot.binary",
        lhs=[Pat("?s", "first", "slot?"), Pat("slot?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "plus?"), Pat("plus?", "next", "?y"),
             Pat("?y", "next", "is?"), Pat("is?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<slot>?", "sname", "?name"), Pat("<slot>?", "scat", "?z"),
             Pat("<slot>?", "sleft", "?x"), Pat("<slot>?", "sright", "?y"),
             Pat("<slot>?", "sside", "?side"), Pat("<slot>?", "scslot", "?cslot")],
    ),
    Rule(
        key="gram.slot.unary",
        lhs=[Pat("?s", "first", "slot?"), Pat("slot?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<slot>?", "sname", "?name"), Pat("<slot>?", "scat", "?z"),
             Pat("<slot>?", "sonly", "?x"), Pat("<slot>?", "sside", "?side"),
             Pat("<slot>?", "scslot", "?cslot")],
    ),
]


def _assert_forms() -> list[Rule]:
    """`<cat> asserts|denies A B C [when|unless G]` — six shapes, generated over the two verbs
    and the three guard shapes rather than written out."""
    forms: list[Rule] = []
    for verb, mode in (("asserts", "assert"), ("denies", "deny")):
        head = [Pat("?s", "first", "?z"), Pat("?z", "next", f"{verb}?"),
                Pat(f"{verb}?", "next", "?a"), Pat("?a", "next", "?b"), Pat("?b", "next", "?c")]
        core = [Pat("<ass>?", "acat", "?z"), Pat("<ass>?", "amode", mode),
                Pat("<ass>?", "asubj", "?a"), Pat("<ass>?", "apred", "?b"),
                Pat("<ass>?", "aobj", "?c")]
        forms.append(Rule(key=f"gram.{verb}.bare", lhs=head,
                          nac=[Pat("?c", "next", "?more")], rhs=core))
        for guard, key in (("when", "awhen"), ("unless", "aunless")):
            forms.append(Rule(
                key=f"gram.{verb}.{guard}",
                lhs=[*head, Pat("?c", "next", f"{guard}?"), Pat(f"{guard}?", "next", "?g")],
                rhs=[*core, Pat("<ass>?", key, "?g")]))
    return forms


ASSERT_FORMS: list[Rule] = _assert_forms()
DECL_FORMS: list[Rule] = PRODUCTION_FORMS + SLOT_FORMS + ASSERT_FORMS


# ---------------------------------------------------------------------------
# The grammar, now with its semantics — still entirely CNL
# ---------------------------------------------------------------------------

GRAMMAR_CNL = """
the is a determiner
a is a determiner
no is a negator
guzerat is a modifier
lion is a noun
mane is a noun
tiger is a noun
africa is a noun
fish is a noun
has is a transitive
eats is a transitive
roars is a intransitive
lives is a intransitive
is is a copula
smaller is a comparative
than is a comparator
in is a preposition
np expands to noun
np expands to determiner plus np
np expands to modifier plus np
np expands to negator plus np
np expands to np plus pp
pp expands to preposition plus np
vp expands to intransitive
vp expands to transitive plus np
vp expands to vp plus pp
cp expands to comparator plus np
ap expands to comparative plus cp
vp expands to copula plus ap
clause expands to np plus vp
slot head in np from noun is only head
slot head in np from determiner plus np is right head
slot head in np from modifier plus np is right head
slot attr in np from modifier plus np is left head
slot head in np from negator plus np is right head
slot neg in np from negator plus np is left head
slot head in np from np plus pp is left head
slot prep in np from np plus pp is right prep
slot pobj in np from np plus pp is right pobj
slot prep in pp from preposition plus np is left head
slot pobj in pp from preposition plus np is right head
slot pred in vp from intransitive is only head
slot pred in vp from transitive plus np is left head
slot obj in vp from transitive plus np is right head
slot neg in vp from transitive plus np is right neg
slot pred in vp from vp plus pp is left pred
slot obj in vp from vp plus pp is left obj
slot prep in vp from vp plus pp is right prep
slot pobj in vp from vp plus pp is right pobj
slot cobj in cp from comparator plus np is right head
slot comp in ap from comparative plus cp is left head
slot cobj in ap from comparative plus cp is right cobj
slot comp in vp from copula plus ap is right comp
slot cobj in vp from copula plus ap is right cobj
slot subj in clause from np plus vp is left head
slot pred in clause from np plus vp is right pred
slot obj in clause from np plus vp is right obj
slot neg in clause from np plus vp is right neg
slot prep in clause from np plus vp is right prep
slot pobj in clause from np plus vp is right pobj
slot comp in clause from np plus vp is right comp
slot cobj in clause from np plus vp is right cobj
np asserts head is attr
clause asserts subj pred obj unless neg
clause denies subj pred obj when neg
clause asserts subj pred true unless obj
clause asserts subj prep pobj when pobj
clause asserts subj comp cobj when cobj
"""


def read_semantics(text: str):
    """Read the slot + assertion declarations back out of CNL (a §8 reader)."""
    g = AttrGraph()
    load_facts(g, text, extra_forms=DECL_FORMS)

    def slots_of(n):
        out = {}
        for r, o in g.relations_from(n):
            for k in ("sname", "scat", "sleft", "sright", "sonly", "sside", "scslot",
                      "acat", "amode", "asubj", "apred", "aobj", "awhen", "aunless"):
                if g.has_key(r, k):
                    out[k] = g.name(o)
        return out

    slot_decls, assertions = [], []
    for n in g.nodes():
        d = slots_of(n)
        if "sname" in d:
            slot_decls.append(d)
        elif "acat" in d:
            assertions.append(d)
    return slot_decls, assertions


# ---------------------------------------------------------------------------
# Generated banks: mint useful spans -> fill slots -> assert facts
# ---------------------------------------------------------------------------

def mint_bank(cats) -> tuple[list[Rule], frozenset[str]]:
    """One `<span>` node per USEFUL span. The usefulness pass has already thrown away every
    constituent no complete parse uses, so this is the parse, not the chart."""
    rules = [Rule(key=f"fold.mint.{c}",
                  lhs=[Pat("?a", f"useful_{c}", "?b")],
                  rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", "?a"),
                       Pat("<span>?", "end", "?b")])
             for c in sorted(cats)]
    # The base case: a span exactly one token wide denotes that token. Generic — no per-category
    # rule, and it is what makes `head` bottom out.
    rules.append(Rule(key="fold.lexhead",
                      lhs=[Pat("?p", "cat", "?c"), Pat("?p", "begin", "?t"),
                           Pat("?p", "end", "?u"), Pat("?t", "next", "?u")],
                      rhs=[Pat("?p", "head", "?t")]))
    return rules, frozenset({"cat", "begin", "end", "head"})


def slot_bank(slot_decls) -> tuple[list[Rule], frozenset[str]]:
    """A percolation rule per declared slot."""
    rules: list[Rule] = []
    names: set[str] = set()
    for i, d in enumerate(slot_decls):
        s, z, side, cs = d["sname"], d["scat"], d["sside"], d["scslot"]
        names.add(s)
        parent = [Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b")]
        if "sonly" in d:
            kids = [Pat("?q", "cat", d["sonly"]), Pat("?q", "begin", "?a"), Pat("?q", "end", "?b")]
            src = "?q"
        else:
            kids = [Pat("?l", "cat", d["sleft"]), Pat("?l", "begin", "?a"), Pat("?l", "end", "?m"),
                    Pat("?r", "cat", d["sright"]), Pat("?r", "begin", "?m"), Pat("?r", "end", "?b")]
            src = "?l" if side == "left" else "?r"
        rules.append(Rule(key=f"fold.slot.{i}.{z}.{s}",
                          lhs=[*parent, *kids, Pat(src, cs, "?v")],
                          rhs=[Pat("?p", s, "?v")]))
    return rules, frozenset(names)


def assert_bank(assertions, slot_names, lexicon) -> list[Rule]:
    """A fact-emitting rule per assertion declaration.

    The PREDICATE position is read as a SLOT if it names a declared slot, else as a literal word.
    A slot predicate is dynamic — and the ISA rejects a non-plain RHS predicate — so it generates
    one rule per lexicon word, exactly the `relation_forms` discipline ("declare the relation, and
    a form is generated for it"). The fold reproduces that rule on its own; see the findings."""
    rules: list[Rule] = []
    for i, d in enumerate(assertions):
        z, mode = d["acat"], d["amode"]
        subj, pred, obj = d["asubj"], d["apred"], d["aobj"]
        guards = [Pat("?p", d["awhen"], "?gw")] if "awhen" in d else []
        nacs = [Pat("?p", d["aunless"], "?gu")] if "aunless" in d else []
        base = [Pat("?p", "cat", z), Pat("?p", subj, "?s"), *guards]
        if obj in slot_names:
            obj_prem, obj_tok = [Pat("?p", obj, "?o")], "?o"
        else:
            obj_prem, obj_tok = [], obj              # a literal object, e.g. `yes`
        if pred in slot_names:
            for w in sorted(lexicon):
                p = neg_pred(w) if mode == "deny" else w
                rules.append(Rule(key=f"fold.assert.{i}.{z}.{w}",
                                  lhs=[*base, Pat("?p", pred, f"{w}?"), *obj_prem],
                                  nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
        else:
            p = neg_pred(pred) if mode == "deny" else pred
            rules.append(Rule(key=f"fold.assert.{i}.{z}.{p}",
                              lhs=[*base, *obj_prem], nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
    return rules


# ---------------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------------

def fold(sentence: str, stages, g=None) -> tuple[str, list[tuple[str, str, str]], object]:
    """Run the full pipeline. Returns (outcome, facts, graph); outcome is one of
    `refused` / `ambiguous` / `folded`. `g` accumulates across sentences when supplied."""
    chart, cpreds, amb, apreds, mint, mpreds, slots, spreds, asserts = stages
    g = AttrGraph() if g is None else g
    anchor = tokenize(g, sentence)
    toks = _chain(g, anchor)
    eos = g.add_node("<eos>", control=True)
    g.add_relation(toks[-1], "next", eos, control=True)
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)

    run_bank(g, chart, control_preds=cpreds)
    if not any(g.has_key(r, sp(ROOT)) and o == eos for r, o in g.relations_from(toks[0])):
        return "refused", [], g
    run_bank(g, amb, control_preds=apreds)
    if any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t)):
        return "ambiguous", [], g

    before = {n for n in g.nodes()}
    run_bank(g, mint, control_preds=mpreds)
    run_bank(g, slots, control_preds=spreds)
    run_bank(g, asserts)
    facts = [(g.name(s), g.predicate(r), g.name(o))
             for s in g.nodes() if s in before and not g.is_control(s)
             for r, o in g.relations_from(s)
             if r not in before and not g.is_control(r) and not g.is_inert(r)]
    return "folded", sorted(set(facts)), g


CASES = [
    "the lion has a mane",
    "the lion roars",
    "the guzerat lion has no mane",
    "the lion lives in africa",
    "the lion is smaller than the tiger",
    "glorp the flarn",
    "the lion eats the fish in africa",
]


def today(line: str) -> str:
    try:
        kb = AttrGraph()
        out = h.ingest(kb, [], line)
        facts = sorted(h.derived_triples(kb))
        return f"{out.kind}: {facts}" if facts else out.kind
    except Exception as e:                              # noqa: BLE001 — reporting a bench result
        return f"error:{type(e).__name__}"


def main() -> None:
    from spike_homoiconic_grammar import read_grammar

    hdr("0  THE GRAMMAR + ITS SEMANTICS, READ BACK OUT OF CNL")
    lex, unary, binary = read_grammar(GRAMMAR_CNL)
    slot_decls, assertions = read_semantics(GRAMMAR_CNL)
    print(f"  lexicon {len(lex)}   productions {len(unary) + len(binary)}"
          f"   slot rules {len(slot_decls)}   assertions {len(assertions)}")
    if not slot_decls or not assertions:
        print("  !! the slot/assert forms did not read back — nothing below is meaningful")
        return
    for d in assertions:
        g = (f" when {d['awhen']}" if "awhen" in d else
             f" unless {d['aunless']}" if "aunless" in d else "")
        verb = "asserts" if d["amode"] == "assert" else "denies"
        print(f"      {d['acat']} {verb} {d['asubj']} {d['apred']} {d['aobj']}{g}")

    chart, cpreds = chart_bank(lex, unary, binary)
    amb, apreds = ambiguity_bank(unary, binary)
    cats = {z for z, _ in unary} | {z for z, *_ in binary} \
        | {x for _, x, y in binary for x in (x, y)} | {x for _, x in unary} | {ROOT}
    mint, mpreds = mint_bank(cats)
    slots, spreds = slot_bank(slot_decls)
    slot_names = set(spreds) | {"head"}
    asserts = assert_bank(assertions, slot_names, set(lex))
    stages = (chart, cpreds, amb, apreds, mint, mpreds | {"head"}, slots, spreds, asserts)
    print(f"\n  generated: chart {len(chart)}  useful/amb {len(amb)}  mint {len(mint)}"
          f"  slots {len(slots)}  assert {len(asserts)}")

    hdr("1  THE FOLD — what the grammar now WRITES")
    for line in CASES:
        outcome, facts, _g = fold(line, stages)
        print(f"\n    {line}")
        print(f"      grammar : {outcome:9} {facts if facts else ''}")
        print(f"      today   : {today(line)}")

    hdr("2  SUBSUMPTION (§5.4) — does it do what FACT_FORMS does?")
    print("  The shipped shapes, run through the grammar. A `second system` shows up here as a")
    print("  shape the grammar cannot express, or expresses differently.\n")
    for line in ("the lion has a mane", "the lion is smaller than the tiger"):
        outcome, facts, _g = fold(line, stages)
        print(f"    {line:38} -> {outcome}: {facts}")
        print(f"    {'':38}    today: {today(line)}")

    hdr("3  COST")
    times = []
    for line in CASES:
        t0 = time.perf_counter()
        fold(line, stages)
        times.append((time.perf_counter() - t0) * 1000)
    print(f"    full pipeline: mean {sum(times) / len(times):6.1f} ms   max {max(times):6.1f} ms")
    for line, ms in zip(CASES, times):
        print(f"      {ms:6.1f} ms  {line}")


if __name__ == "__main__":
    main()
