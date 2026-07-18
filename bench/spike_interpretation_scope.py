"""
SPIKE — the SURFACE / INTERPRETATION split (user proposal, 2026-07-18).

THE PROPOSAL. The nodes representing the SENTENCE are never touched — they are the permanent,
monotone record of what was said. Everything that is a JUDGEMENT about what the sentence MEANS —
which entity a mention denotes, whether two mentions corefer, whether a modified noun phrase is a
subkind or the thing we were already discussing — lives in a SCOPE holding COPIES, with provenance
back to the surface. Inside the scope the merge may be destructive (one node per entity, the fast
representation), because reversal is never needed: you discard the scope and re-derive.

WHY IT MATTERS. It is the answer to the coreference/minting question that does NOT require the
domain author to know the right reading in advance. `design/homoiconic_grammar.md` §10 made
mint-vs-percolate a per-production declaration; this makes it a defeasible COMMITMENT that a
contradiction can defeat. The system discovers it was wrong instead of being told.

It is also a STRATIFICATION with a principled basis — observation vs inference — rather than an
engineering coloring (control vs fact). "What the sentence said" never changes; "what it means" is
always revisable, and that tells you unambiguously which layer anything belongs to.

THE LOOP THIS DEMONSTRATES:

    surface (immutable)
      -> interpretation A: `the guzerat lion` IS the lion we were discussing   [percolate]
      -> `lion has mane` AND `lion has_not mane`  ->  <contradiction>
      -> walk provenance to the interpretation choices in its support
      -> ASK (do not pick): "one entity, or a kind of it?"
      -> discard scope, interpretation B: a distinct subkind                   [mint]
      -> no contradiction; the surface never moved

Run: python bench/spike_interpretation_scope.py
"""
from __future__ import annotations

from ugm import AttrGraph, Pat, Rule, neg_pred, run_bank
from ugm.cnl.forms import tokenize

from spike_homoiconic_grammar import ROOT, _chain, ambiguity_bank, chart_bank, read_grammar, sp
from spike_grammar_fold import GRAMMAR_CNL, assert_bank, read_semantics, slot_bank
from spike_grammar_subkind import SUBKIND_CNL, describe, mint_slot_bank, read_mints

SCOPE = "<interpretation>"
DENOTES = "denotes"          # surface token -> the entity it is taken to denote (the JUDGEMENT)
INTERPRETS = "interprets"    # entity -> every surface mention it was derived from (provenance)


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# STAGE A — the surface. Structure only: no entity, no denotation, never revised.
# ---------------------------------------------------------------------------

def span_bank(cats) -> tuple[list[Rule], frozenset[str]]:
    """Mint a span node per USEFUL span. Pure structure — deliberately NO `head`, because a head
    is already a denotation and denotation is the interpretation's business."""
    return ([Rule(key=f"surf.span.{c}",
                  lhs=[Pat("?a", f"useful_{c}", "?b")],
                  rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", "?a"),
                       Pat("<span>?", "end", "?b")])
             for c in sorted(cats)], frozenset({"cat", "begin", "end"}))


def read_surface(g, sentence: str, chart, cpreds, amb, apreds, spans, spreds) -> str:
    """Tokenize and parse `sentence` into `g`. Returns `parsed` / `refused` / `ambiguous`."""
    anchor = tokenize(g, sentence)
    toks = _chain(g, anchor)
    eos = g.add_node("<eos>", control=True)
    g.add_relation(toks[-1], "next", eos, control=True)
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)
    run_bank(g, chart, control_preds=cpreds)
    if not any(g.has_key(r, sp(ROOT)) and o == eos for r, o in g.relations_from(toks[0])):
        return "refused"
    run_bank(g, amb, control_preds=apreds)
    if any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t)):
        return "ambiguous"
    run_bank(g, spans, control_preds=spreds)
    return "parsed"


# ---------------------------------------------------------------------------
# STAGE B — the interpretation scope: copies, with provenance
# ---------------------------------------------------------------------------

def interpret_mentions(g, scope: str) -> dict[str, str]:
    """THE COREFERENCE JUDGEMENT, as a scoped copy rather than a destructive fold.

    One entity node per distinct mention NAME, marked into `scope`, with `interprets` provenance to
    every surface token it was derived from, and `denotes` from each token to it. The surface
    tokens keep their identity and their chain — nothing about the sentence is touched.

    This is where today's `intern_mentions` differs: it FOLDS the surface mentions together and
    deletes the victims, which is why the decision can never be revised. Here the merge is just as
    destructive INSIDE the scope (one node per name — the fast representation, no `same_as` clique,
    no representative hop) and costs nothing to undo, because undoing is discarding."""
    lex_heads: dict[str, list[str]] = {}
    for p in list(g.nodes()):
        if not g.has_key_out(p, "cat"):
            continue
        beg = _slot(g, p, "begin")
        end = _slot(g, p, "end")
        if beg is None or end is None:
            continue
        nxt = next((o for r, o in g.relations_from(beg) if g.has_key(r, "next")), None)
        if nxt == end:                                    # a one-token span: it denotes its token
            lex_heads.setdefault(g.name(beg), []).append(beg)
    ents: dict[str, str] = {}
    for nm, dups in sorted(lex_heads.items()):
        toks = list(dict.fromkeys(dups))       # one token may head spans of several categories
        e = g.add_node(nm)
        g.add_relation(scope, "member", e, control=True)
        for t in toks:
            g.add_relation(e, INTERPRETS, t, control=True)     # provenance: copy -> surface
            g.add_relation(t, DENOTES, e, control=True)        # the judgement itself
        ents[nm] = e
    return ents


def _slot(g, n, key):
    return next((o for r, o in g.relations_from(n) if g.has_key(r, key)), None)


def has_key_out(g, n, key) -> bool:
    return any(g.has_key(r, key) for r, _o in g.relations_from(n))


AttrGraph.has_key_out = lambda self, n, key: has_key_out(self, n, key)   # spike convenience


def head_bank() -> list[Rule]:
    """The bridge from surface to interpretation: a one-token span's `head` is the ENTITY its token
    is taken to denote, not the token. Every slot downstream therefore carries entities, and the
    whole fold writes into the scope without knowing it."""
    return [Rule(key="interp.lexhead",
                 lhs=[Pat("?p", "cat", "?c"), Pat("?p", "begin", "?t"), Pat("?p", "end", "?u"),
                      Pat("?t", "next", "?u"), Pat("?t", DENOTES, "?e")],
                 rhs=[Pat("?p", "head", "?e")])]


def close_scope(g, scope: str, before: set) -> int:
    """The scope IS everything this interpretation created. Taking the delta against a
    pre-interpretation snapshot needs no per-category bookkeeping and cannot miss a node — which
    matters, because the first attempt marked scope membership with a RULE and silently marked
    nothing: `Pat(scope_id, "member", "?e")` reads its subject as a NAME, so it interned a node
    named `n417` instead of pointing at the scope. A scope node has no name to be addressed by;
    addressing it from inside a rule would need `ByDesc`."""
    n = 0
    for node in g.nodes():
        if node not in before and node != scope and not g.is_inert(node):
            g.add_relation(scope, "member", node, control=True)
            n += 1
    return n


def discard_scope(g, scope: str, interp_preds) -> int:
    """Throw the interpretation away. Legal precisely because it is scoped: the surface record is
    untouched, so nothing is lost that cannot be re-derived.

    FINDING (this cost a bug): the interpretation is not only the ENTITIES. Every derived
    denotation edge — `denotes`, and every slot (`head`, `subj`, `pred`, …) — is a judgement too,
    even though it is written ONTO a surface span node. Leaving them behind left the spans holding
    stale heads pointing at deleted entities, and the second interpretation silently inherited the
    first one's decisions. The line between the layers is not "which node it hangs on", it is
    "structure vs denotation"; the surface is tokens, chains, and `cat`/`begin`/`end` — nothing
    else."""
    members = [o for r, o in g.relations_from(scope) if g.has_key(r, "member")]
    gone = 0
    for m in members:
        if m in g.nodes():
            g.remove_node(m)
            gone += 1
    preds = set(interp_preds) | {DENOTES, "head"}
    for t in list(g.nodes()):
        for r, _o in list(g.relations_from(t)):
            if g.predicate(r) in preds and r in g.nodes():
                g.remove_node(r)
                gone += 1
    return gone


# ---------------------------------------------------------------------------
# STAGE D — contradiction, as a derived marker (consistency_design §0)
# ---------------------------------------------------------------------------

def contradiction_bank(lexicon) -> list[Rule]:
    """`X p Y` and `X not-p Y` on ONE entity derives a `<contradiction>` marker. Monotone and
    PARACONSISTENT — it marks itself and does not explode the KB (consistency_design.md §0)."""
    return [Rule(key=f"contra.{w}",
                 lhs=[Pat("?e", w, "?x"), Pat("?e", neg_pred(w), "?x")],
                 rhs=[Pat("<contradiction>?", "about", "?e"),
                      Pat("<contradiction>?", "because", "?x")])
            for w in sorted(lexicon)]


def contradictions(g) -> list[tuple[str, str]]:
    out = []
    for n in g.nodes():
        if g.name(n) != "<contradiction>":
            continue
        about = _slot(g, n, "about")
        because = _slot(g, n, "because")
        if about is not None:
            out.append((about, because))
    return out


def culprits(g, entity: str) -> list[str]:
    """The surface mentions this entity was interpreted FROM. More than one means a coreference
    JUDGEMENT is in the contradiction's support — which is the thing to ask about, not to guess."""
    return [o for r, o in g.relations_from(entity) if g.has_key(r, INTERPRETS)]


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def banks(cnl: str):
    lex, unary, binary = read_grammar(cnl)
    slot_decls, assertions = read_semantics(cnl)
    mints = read_mints(cnl)
    chart, cpreds = chart_bank(lex, unary, binary)
    amb, apreds = ambiguity_bank(unary, binary)
    cats = {z for z, _ in unary} | {z for z, *_ in binary} \
        | {x for _, x, y in binary for x in (x, y)} | {x for _, x in unary} | {ROOT}
    spans, sppreds = span_bank(cats)
    slots, spreds = slot_bank(slot_decls)
    slots = head_bank() + slots + mint_slot_bank(mints)
    asserts = assert_bank(assertions, set(spreds) | {"head"}, set(lex))
    return dict(lex=lex, cats=cats, chart=chart, cpreds=cpreds, amb=amb, apreds=apreds,
                spans=spans, sppreds=sppreds, slots=slots,
                spreds=spreds | {"head", DENOTES}, asserts=asserts)


CORPUS = ["the lion has a mane", "the guzerat lion has no mane"]


def interpret(g, B, scope: str) -> list[tuple[str, str, str]]:
    """Run one interpretation over the standing surface. Returns the facts it commits to."""
    before = set(g.nodes())
    interpret_mentions(g, scope)
    run_bank(g, B["slots"], control_preds=B["spreds"])
    run_bank(g, B["asserts"])
    run_bank(g, contradiction_bank(set(B["lex"])))
    close_scope(g, scope, before)
    members = {o for r, o in g.relations_from(scope) if g.has_key(r, "member")}
    out = []
    for s in members:
        for r, o in g.relations_from(s):
            p = g.predicate(r)
            if g.is_control(r) or g.is_inert(r) or not p:
                continue
            if p in ("cat", "begin", "end", "head", "about", "because"):
                continue
            if o in members or g.name(o):
                out.append((describe(g, s), g.predicate(r), describe(g, o)))
    return sorted(set(out))


def main() -> None:
    B_perc = banks(GRAMMAR_CNL)       # interpretation A: a modified NP is the SAME entity
    B_mint = banks(SUBKIND_CNL)       # interpretation B: a modified NP is a DISTINCT subkind

    hdr("A  THE SURFACE — parsed once, and never touched again")
    g = AttrGraph()
    for line in CORPUS:
        st = read_surface(g, line, B_perc["chart"], B_perc["cpreds"], B_perc["amb"],
                          B_perc["apreds"], B_perc["spans"], B_perc["sppreds"])
        print(f"    {st:9} {line}")
    surface_nodes = set(g.nodes())
    print(f"\n    surface nodes: {len(surface_nodes)}  (tokens, chains, spans — structure only;")
    print("    no entity and no denotation, because a denotation is already a judgement)")

    hdr("B  INTERPRETATION A — `the guzerat lion` is the lion we were discussing")
    scope_a = g.add_node(SCOPE, control=True)
    facts_a = interpret(g, B_perc, scope_a)
    for t in facts_a:
        print(f"        {t}")

    hdr("C  CONTRADICTION — derived, not detected by a checker")
    cs = contradictions(g)
    if not cs:
        print("    none — the demo does not hold")
        return
    for about, because in cs:
        print(f"    <contradiction> about {describe(g, about)!r} because {describe(g, because)!r}")
        mentions = culprits(g, about)
        print(f"    the entity was interpreted from {len(mentions)} surface mentions:")
        for m in mentions:
            print(f"        token {m} {g.name(m)!r}")

    hdr("D  THE QUESTION — the support names a JUDGEMENT, so ask; do not pick")
    print("    Two surface mentions were committed to ONE entity, and that commitment is in the")
    print("    contradiction's support. Nothing about the sentences is in doubt; the reading is.\n")
    print('        "You said lions have manes, and that the guzerat lion has none.')
    print('         Is the guzerat lion the same lion, or a kind of lion?"\n')
    print("    That is a question a person answers instantly and a solver cannot. It is the same")
    print("    refuse-and-ask shape the ambiguity crux already took.")

    hdr("E  DEFEAT THE INTERPRETATION — discard the scope, re-derive")
    before = set(g.nodes())
    gone = discard_scope(g, scope_a, B_perc["spreds"])
    after = set(g.nodes())
    print(f"    scope members discarded : {gone}")
    print(f"    surface still intact    : {surface_nodes <= after}  "
          f"({len(surface_nodes & after)}/{len(surface_nodes)} surface nodes present)")
    print(f"    contradictions remaining: {len(contradictions(g))}")

    hdr("F  INTERPRETATION B — a distinct subkind, over the SAME untouched surface")
    scope_b = g.add_node(SCOPE, control=True)
    facts_b = interpret(g, B_mint, scope_b)
    for t in facts_b:
        print(f"        {t}")
    print(f"\n    contradictions: {len(contradictions(g))}")
    print("\n    The surface was parsed ONCE. Two different readings were built over it and one was")
    print("    thrown away, with no re-parse, no un-merge, and nothing lost — which is the whole")
    print("    claim: the merge can stay destructive because it is destructive only inside a copy.")


if __name__ == "__main__":
    main()
