"""The GRAMMAR intake route — integration step 2, built toward the interpretation-node target.

This is a FORK of the shipped fact route, not a replacement (user decision 2026-07-19: the target is
interpretation nodes, and going red for a while beats entrenching the token/entity duality). A KB
that DECLARES a grammar sends its FACT/UNRECOGNIZED tail through here; everything else — questions,
rules, focus moves, forms, procedures — stays on the shipped path untouched. Two intake paths coexist
on purpose until slice 4 converges them.

THE DUALITY, AND WHY THIS PATH EXISTS. On the shipped path the token node IS the entity: facts hang
off the tokens, and `intern_mentions` folds same-named mentions DESTRUCTIVELY, so the coreference
judgement can never be revised. Here the surface (tokens, chains, `cat`/`begin`/`end`) is a permanent
monotone record, and every judgement about what it MEANS lives in a discardable SCOPE of copies
reached through `denotes`. That is what makes contradiction -> ask -> re-interpret possible without
re-parsing (`design/surface_interpretation.md`).

CONSEQUENCE FOR DOWNSTREAM READERS: `focus.utterance_subjects` and
`authoring.anchor_has_content_fact` both walk the token chain and read content relations ON THE
TOKENS. That assumption is false here — the relations are on the entities, one `denotes` hop away.
The entity-aware counterparts live below rather than as edits to the originals, so the shipped path
keeps working while this one moves.
"""
from __future__ import annotations

import os

from ..interpretation import (DENOTES, SURFACE_PREDS, close_scope, contradictions, culprits,
                              describe, discard_scope, interpret, open_scope, scope_members)
from ..lowering import run_bank
from .grammar import (AMBIGUOUS, PARSED, REFUSED, REMINT, Grammar, compile_grammar, load_grammar,
                      load_grammar_file, mark_all_spans, parse)

#: Mechanism state, so it lives in a register beside `forms`/`policy` — not as a graph node.
GRAMMAR_REGISTER = "grammar"
#: The ONE live interpretation of the session's standing surface (a scope node id).
SCOPE_REGISTER = "interpretation"


def _looks_like_a_path(grammar: str) -> bool:
    """A one-line string with a separator or a `.cnl` suffix was MEANT as a path."""
    return "\n" not in grammar and (os.sep in grammar or "/" in grammar
                                    or grammar.endswith(".cnl"))


def declare_grammar(kb, grammar) -> None:
    """Give `kb` a grammar, compiling its banks ONCE. `grammar` is a `Grammar`, CNL text, or a path.

    Compilation is per-grammar, not per-utterance: `compile_grammar` generates ~200 rules and the
    banks are reused across every parse in the session.

    LOUD ON A BAD PATH. This used to fall through to `load_grammar(str(grammar))`, so a mistyped or
    non-existent path was parsed AS GRAMMAR TEXT: every line failed to match a declaration form, the
    result was an empty grammar, and the KB then silently refused every sentence. Cost a bogus
    benchmark run before it was noticed — the failure looked like "the grammar is fast" rather than
    "there is no grammar". A path that does not resolve now raises, and so does a grammar with no
    lexicon and no productions, whatever it was built from — the backstop that also catches text
    which parsed to nothing."""
    if isinstance(grammar, Grammar):
        gram = grammar
    elif isinstance(grammar, os.PathLike) or (isinstance(grammar, str)
                                              and _looks_like_a_path(grammar)):
        if not os.path.exists(grammar):
            raise FileNotFoundError(
                f"grammar file not found: {os.fspath(grammar)!r} — pass an existing path, a "
                f"`Grammar`, or multi-line CNL declaration text")
        gram = load_grammar_file(grammar)
    else:
        gram = load_grammar(str(grammar))
    if not (gram.lexicon or gram.binary or gram.unary):
        raise ValueError(
            "grammar declares no lexicon and no productions — nothing would ever parse. "
            "Check the declaration forms (`X is a noun`, `np expands to determiner plus np`).")
    kb.registers[GRAMMAR_REGISTER] = compile_grammar(gram)


def session_banks(kb):
    """The declared `GrammarBanks`, or None if this KB has no grammar (=> the shipped route)."""
    return kb.registers.get(GRAMMAR_REGISTER)


def live_scope(kb) -> str:
    """The session's ONE live interpretation scope, opened on first use.

    ONE, not one per utterance: enforcing a single live interpretation is what keeps branch selection
    out (`surface_interpretation.md`). Re-interpretation replaces this scope rather than adding one.
    """
    scope = kb.registers.get(SCOPE_REGISTER)
    if scope is None or scope not in kb.nodes():
        scope = open_scope(kb)
        kb.registers[SCOPE_REGISTER] = scope
    return scope


# ---------------------------------------------------------------------------
# Entity-aware counterparts of the token-chain readers
# ---------------------------------------------------------------------------

def denotata(kb, toks) -> list[str]:
    """The entities this utterance's tokens are taken to denote — the `denotes` hop.

    The counterpart of "the content tokens of the chain": on the shipped path those two sets are the
    same nodes, which is exactly the duality this route splits apart."""
    seen: dict[str, None] = {}
    for t in toks:
        for r, o in kb.relations_from(t):
            if kb.has_key(r, DENOTES):
                seen.setdefault(o, None)
    return list(seen)


def _content_relations(kb, n, *, since: set[str] | None = None):
    for r, o in kb.relations_from(n):
        p = kb.predicate(r)
        if kb.is_control(r) or kb.is_inert(r) or not p:
            continue
        if p in SURFACE_PREDS or p in ("head", "about", "because"):
            continue
        if since is not None and r in since:
            continue                                 # not minted by THIS utterance
        yield r, o


def has_content_fact(kb, toks, *, since: set[str] | None = None) -> bool:
    """Did interpreting this utterance put a CONTENT relation on any entity it mentions?

    The entity-side answer to `authoring.anchor_has_content_fact`. `since` plays the same role it
    does there — a pre-utterance node snapshot, so an utterance that merely MENTIONS already-related
    entities does not misroute as a fact.

    ⚠ ORDER-DEPENDENT AND WRONG IN BOTH DIRECTIONS ON THIS ROUTE — kept only for the callers that
    still pass a snapshot. Use `asserts_content` instead; see its docstring for the measurements."""
    return any(True for e in denotata(kb, toks)
               for _ in _content_relations(kb, e, since=since))


def asserting_categories(gram) -> set[str]:
    """The categories whose declared assertions PREDICATE rather than DESCRIBE.

    Exactly `assert_bank(defining=False)`'s selection, read off the same declarations: a category
    that MINTS is settling what an entity IS (`np asserts head is attr` describing a subkind), and
    saying `the african lion` is referring, not asserting. A non-minting category's assertion is
    predication (`clause asserts subj pred obj`) — that is content."""
    minting = {d["mcat"] for d in gram.mints}
    return {d["acat"] for d in gram.assertions
            if d.get("aobj") is not None and d["acat"] not in minting}


def asserts_content(kb, toks, banks) -> bool:
    """Does THIS utterance's parse predicate anything? A question about the SURFACE and the GRAMMAR.

    WHY THIS REPLACED THE SNAPSHOT (measured 2026-07-19, 24-order permutation sweep). `route` used
    to answer this with `has_content_fact(since=<pre-utterance node ids>)` — "does any entity this
    utterance mentions carry a content relation that did not exist before". Two independent defects,
    both of the quietly-does-something-wrong class:

    * **False negative.** `denotata` reaches entities by the `denotes` hop from tokens, i.e. the
      LEXICAL entities. A MINTED subkind hangs off the span's `head` slot and is reachable from no
      token at all, so `the african lion has a mane` wrote three facts and reported `unrecognized`.
    * **False positive, and the order dependence.** `lion` is in that sentence's denotata, so once
      any earlier utterance gave `lion` a fact, the same sentence reports `fact` — for someone
      else's content. The `since` snapshot does not filter it, because `reinterpret` re-mints the
      WHOLE interpretation every utterance: a re-derived relation is a NEW NODE ID, so rebuild makes
      everything look new. 22 of 24 orders disagreed on the verdict while the FACTS agreed in all 24.

    The repair is to stop asking a question about node identity. Whether an utterance asserts is
    decided by its parse: does it contain a span in a category that DECLARES a predication
    (`asserting_categories`)? That reads the surface and the grammar only — it never enters the
    interpretation layer, so it cannot be perturbed by rebuilding, re-minting, or what other
    sentences happened to say. Order-independent by construction, and it routes by WHICH FORMS FIRED
    rather than by inspecting results (intake discipline §D.1)."""
    cats = asserting_categories(banks.grammar)
    if not cats:
        return False
    toks = set(toks)
    for t in toks:
        for r in kb.into(t):                          # a `begin` relation lands on its token ...
            if not kb.has_key(r, "begin"):
                continue
            for span in kb.into(r):                   # ... and its subject is the span
                for cr, co in kb.relations_from(span):
                    if kb.has_key(cr, "cat") and kb.name(co) in cats:
                        return True
    return False


def utterance_centers(kb, toks) -> set[str]:
    """The entities this utterance PREDICATES ABOUT, as focus centers.

    Rendered by `describe`, so a minted subkind enters focus by its DESCRIPTION rather than by a name
    it does not have (`ByDesc` — a minted node has no name, only its defining relations)."""
    out: set[str] = set()
    for e in denotata(kb, toks):
        if any(True for _ in _content_relations(kb, e)):
            out.add(describe(kb, e))
    return out


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------

def route(kb, utterance: str, banks) -> tuple[str, dict]:
    """Parse and interpret ONE utterance. Returns `(kind, data)`.

    `kind` is `fact` / `ambiguous` / `unrecognized`, mirroring the shipped route's vocabulary plus
    the one genuinely new outcome. AMBIGUOUS is its OWN kind, not a flavour of unrecognized: "I
    cannot parse this" and "I parsed it two ways" call for different responses, and only the second
    can become a discriminating question (`can_ask`) — which is where this is headed.

    An ambiguous or refused utterance writes NO facts. The surface it did produce STAYS: it is the
    permanent record, and a later re-interpretation (or a discriminating answer) reads it without
    re-parsing."""
    outcome, toks, _eos = parse(kb, utterance, banks)
    if outcome == REFUSED:
        return "unrecognized", {"tokens": toks}
    if outcome == AMBIGUOUS:
        from .grammar import ambiguous_spans
        spans = ambiguous_spans(kb, toks)
        return "ambiguous", {"tokens": toks,
                             "spans": [(kb.name(a), kb.name(b)) for a, b in spans]}

    scope = extend(kb, banks)
    return ("fact" if asserts_content(kb, toks, banks) else "unrecognized",
            {"tokens": toks, "scope": scope, "centers": utterance_centers(kb, toks)})


def _discard_live(kb, banks) -> None:
    """Take down the live interpretation, leaving the surface (and any re-minting marks) standing."""
    scope = kb.registers.get(SCOPE_REGISTER)
    if scope is not None and scope in kb.nodes():
        discard_scope(kb, scope, banks.reinterp_slot_preds)
    kb.registers.pop(SCOPE_REGISTER, None)


def _fold(kb, banks, scope) -> str:
    """Run the fold over whatever is currently marked `UNINTERPRETED`. Returns the scope.

    Always on `reinterp_slots`, never the plain slot bank — with no span marked for RE-MINTING the
    two are equivalent (the percolation NAC and the mint premise both test a marker that is not
    there), so one bank covers both readings and the re-minting marks alone decide. That is also
    what makes a re-minting judgement DURABLE: those marks live on the SURFACE, so they survive the
    discard that clears the entities, and every later utterance is read under them."""
    interpret(kb, banks, scope,
              slots=banks.reinterp_slots, slot_preds=banks.reinterp_slot_preds)
    return scope


def extend(kb, banks) -> str:
    """Fold the NEW spans into the standing interpretation. The per-utterance path.

    ONE live interpretation, GROWN — not torn down and rebuilt. The banks are seeded on the
    `UNINTERPRETED` mark that `span_bank` writes, so this reads only what this utterance parsed while
    reaching entities earlier utterances already established.

    EQUIVALENT TO `rebuild`, and that is a tested property, not an assumption
    (`test_extending_the_scope_equals_rebuilding_it`). It was NOT true at first: keeping the scope
    exposed two latent idempotency defects that discard-first had been paying for — a bound-literal
    `<contradiction>?` duplicating its marker, and `interpret_mentions` minting a parallel entity per
    name on every pass. Both are fixed at the source, so the equivalence belongs to the banks."""
    return _fold(kb, banks, live_scope(kb))


def rebuild(kb, banks) -> str:
    """Discard the live interpretation and re-read the WHOLE standing surface. The revision path.

    What `reconsider` needs after a contradiction: the re-minting marks changed, so every earlier
    utterance must be re-read under them. Expressed in the SAME vocabulary as `extend` — mark all
    the spans, then fold — so the two paths run identical banks and differ only in how much they
    mark. Nothing here can drift from the common path, because there is no separate code path."""
    _discard_live(kb, banks)
    mark_all_spans(kb)
    return _fold(kb, banks, live_scope(kb))


#: Back-compat alias — `reinterpret` was the only mode before the split, and it was a rebuild.
reinterpret = rebuild


# ---------------------------------------------------------------------------
# The revision loop — contradiction -> re-interpret -> ask (slice 3)
# ---------------------------------------------------------------------------

#: What `reconsider` concluded. `clean` = nothing to revise. `revised` = re-interpretation cleared
#: the contradiction. `ask` = it did not, so the human decides. `rule` = no interpretation is at
#: fault, so this is a RULE problem (the learning arc's defeasible-exception model), not ours.
CLEAN, REVISED, ASK, RULE = "clean", "revised", "ask", "rule"


def reconsider(kb, banks) -> tuple[str, list]:
    """Try to REVISE the live interpretation in the light of any contradiction it derived.

    THE DISCRIMINATOR (`surface_interpretation.md`): one derived contradiction is the same signal for
    two very different faults — "you merged two entities that are not the same" and "your rule needs
    an exception" — and they live in different layers with different persistence. The support tells
    them apart. If a coreference JUDGEMENT is load-bearing (the entity was interpreted from more than
    one surface mention), the cheap revisable thing is at fault: discard and re-derive, costing
    nothing and leaving the surface intact. If not, no interpretation is to blame and this is a
    durable knowledge problem — return `RULE` and do NOT touch anything.

    Try the revisable thing first, because being wrong about it is free.

    Re-interpretation is EVIDENCE-DRIVEN: it mints only at the spans a contradiction actually
    implicated, which is what stops minting from being the unconditional (and for a non-restrictive
    modifier, wrong) move it is when a grammar simply declares it."""
    scope = kb.registers.get(SCOPE_REGISTER)
    if scope is None or scope not in kb.nodes():
        return CLEAN, []
    cs = contradictions(kb)
    if not cs:
        return CLEAN, []
    if not any(len(culprits(kb, about)) > 1 for about, _because in cs):
        return RULE, cs                              # no judgement in the support — not ours to fix

    run_bank(kb, banks.remint_marks, control_preds=banks.remint_preds)
    if not any(kb.has_key(r, REMINT) for n in kb.nodes() for r, _o in kb.relations_from(n)):
        return ASK, cs                               # a judgement is at fault but no site to re-read

    rebuild(kb, banks)
    remaining = contradictions(kb)
    return (REVISED, []) if not remaining else (ASK, remaining)


def facts(kb) -> list[tuple[str, str, str]]:
    """The facts the live interpretation commits to — the entity-side `derived_triples`."""
    from ..interpretation import scope_facts
    scope = kb.registers.get(SCOPE_REGISTER)
    return scope_facts(kb, scope) if scope is not None and scope in kb.nodes() else []


__all__ = ["GRAMMAR_REGISTER", "SCOPE_REGISTER", "declare_grammar", "session_banks", "live_scope",
           "denotata", "has_content_fact", "utterance_centers", "route", "facts",
           "close_scope", "scope_members", "PARSED", "AMBIGUOUS", "REFUSED"]
