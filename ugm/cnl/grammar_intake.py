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
#: L0 — the words this session has declared to BE part of the language (user decision 2026-07-20,
#: option C). A REGISTER and not graph facts; see `VOCABULARY_FORMS` for the full argument.
VOCABULARY_REGISTER = "vocabulary"


# ---------------------------------------------------------------------------
# L0 — the METALANGUAGE. Declarations ABOUT the language, not about the world.
# ---------------------------------------------------------------------------
#
# ⭐ LEVEL IS A THIRD AXIS, beside CONTENT and FORCE (`design/form_inventory.md`; user proposal
# 2026-07-20, confirmed by probe). A claim is about the WORLD (L2), the THEORY (L1), or the LANGUAGE
# itself (L0). `produces is a relation` is L0: it does not describe anything, it constitutes what can
# be said next.
#
# WHY L0 IS RECOGNIZED BY A FIXED FORM AND NEVER BY THE OBJECT GRAMMAR — this is the defect being
# fixed, not a style choice. Read by the object grammar, a declaration is destroyed by its own
# effect: `produces is a relation` parses while `produces` is unknown and REFUSES once it is a
# `transitive`, because a verb-category word can no longer head an np. Measured through real
# `ingest`, the same line twice routed `fact` then `unrecognized`. A fixed recognizer cannot be
# perturbed by what it declares.
#
# WHY A REGISTER AND NOT GRAPH FACTS (the mechanism/policy split: GRAPH = reasoned-over facts +
# explanation, REGISTERS = stepping state). Three measured reasons:
#   1. **It LEAKED.** As a graph fact, `produces is_a relation` is ordinary content and any domain
#      rule matches it — confirmed: `?y is meta when ?y is a relation` derives `produces is meta`.
#      A meta scope would only make the leak avoidable BY DISCIPLINE, in every present and future
#      reader; a register makes it impossible.
#   2. **The duality reached the meta level** — after intake, `produces` resolved to TWO nodes, so a
#      join over it silently derived nothing (the `UserWarning` was the only trace).
#   3. **Re-declaration is the NORMAL case** under the multi-KB-file model, and it was not
#      idempotent. A dict assignment is.
# Precedent, not invention: `forms` (authored recognition forms) and `grammar` (compiled banks)
# already live in registers for the same reason — they are not claims about the world.
#
# WHAT IS LOST, STATED HONESTLY: `is produces a relation` no longer answers. Nothing else — the
# grammar itself was never in the graph (`load_grammar` returns a `Grammar`; `declare_grammar` parks
# banks in a register), and the parse surface, the interpretation, its facts and all provenance are
# untouched. If querying the language is wanted back, it belongs as a deliberate §8 READER over this
# register — not as a side effect of leaving L0 in the reasoning graph.
#
# THE SCHEMA IS HARDCODED AND THAT IS THE POINT (user, 2026-07-20). These forms are Python, not CNL,
# exactly like `grammar.DECLARATION_FORMS` — so the meta level cannot be extended from inside the
# object language and the tower terminates at two. Same constraint the plan reached from the other
# direction: "the target language must be FIXED AND KNOWN for a translator to aim at it." What grows
# at runtime is L0 INSTANCES (which words are relations), never the L0 SCHEMA (what kinds of
# declaration exist).
VOCABULARY_FORMS = None          # built lazily below, after Pat/Rule are importable


def _vocabulary_forms():
    from ..production_rule import Pat, Rule
    return [
        # `W is a K` — bare, nothing before the word and nothing after the kind. The KIND IS BOUND,
        # not literal, so ONE form covers `produces is a relation` and `wolf is a noun`. Whether `K`
        # actually names something declarable is decided by `resolve_vocabulary` against the live
        # grammar — data, not a keyword list — so `lion is a cat` falls through to the fact route.
        Rule(key="vocab.declare",
             lhs=[Pat("?s", "first", "?w"), Pat("?w", "next", "is?"),
                  Pat("is?", "next", "a?"), Pat("a?", "next", "?k")],
             nac=[Pat("?k", "next", "?more")],
             rhs=[Pat("<vocab>?", "word", "?w"), Pat("<vocab>?", "kind", "?k")]),
    ]


def recognize_vocabulary(utterance: str) -> tuple[str, str] | None:
    """If `utterance` has the shape `W is a K`, the pair `(W, K)` — else None.

    SHAPE ONLY. Whether `K` names a declarable category is a question about the live grammar and is
    answered by `resolve_vocabulary`; splitting the two is what keeps this a pure, fixed recognizer.

    Recognized in a SCRATCH graph, exactly as `focus.recognize_focus_op` and
    `rule_control.recognize_rule_op` are. The scratch graph is what keeps an L0 declaration out of
    the KB entirely: nothing about it is ever a fact."""
    global VOCABULARY_FORMS
    if VOCABULARY_FORMS is None:
        VOCABULARY_FORMS = _vocabulary_forms()
    from ..world_model import Graph
    from .forms import tokenize
    tmp = Graph()
    tokenize(tmp, utterance)
    run_bank(tmp, VOCABULARY_FORMS)
    for nid in tmp.nodes():
        if tmp.name(nid) == "<vocab>":
            slots = {tmp.predicate(rel): tmp.name(obj) for rel, obj in tmp.relations_from(nid)}
            if slots.get("word") and slots.get("kind"):
                return slots["word"], slots["kind"]
    return None


def vocabulary_categories(gram) -> set[str]:
    """The category names a runtime declaration may name — READ OFF THE GRAMMAR, never a list.

    Both halves matter: `categories` covers everything the productions mention (`noun`, `adj`,
    `transitive`), and the lexicon's own values cover a class declared but not yet used in any
    production. A word the grammar has never heard of is not a category, so `lion is a cat` is an
    ordinary fact rather than a declaration."""
    return set(gram.categories) | {c for cs in gram.lexicon.values() for c in cs}


def resolve_vocabulary(banks, kind: str) -> str | None:
    """The LEXICON CATEGORY a declared `kind` word means, or None if it declares nothing.

    `relation` is the one word that is not itself a category: it is the KB-level spelling that the
    shipped route has always used (`R is a relation`), and it means a transitive verb. Everything
    else must name a category the grammar actually has."""
    if kind == "relation":
        return RELATION_CATEGORY
    return kind if kind in vocabulary_categories(banks.grammar) else None


def declare_vocabulary(kb, word: str, category: str) -> None:
    """Record an L0 declaration in the register. Idempotent BY CONSTRUCTION — a dict assignment."""
    kb.registers.setdefault(VOCABULARY_REGISTER, {})[word] = category


def declared_vocabulary(kb) -> dict[str, str]:
    """The words declared to THIS session at L0, as `{word: category}` (register-side only).

    Deliberately NOT merged with `forms.declared_relations` here: that reader walks the GRAPH and
    serves the shipped route, whose corpora still land `R is_a relation` as a fact via `load_corpus`
    (which bypasses intake entirely). `sync_vocabulary` unions the two; keeping the readers separate
    is what lets the graph half be retired later without touching this one."""
    return dict(kb.registers.get(VOCABULARY_REGISTER, {}))


def _looks_like_a_path(grammar: str) -> bool:
    """A one-line string with a separator or a `.cnl` suffix was MEANT as a path."""
    return "\n" not in grammar and (os.sep in grammar or "/" in grammar
                                    or grammar.endswith(".cnl"))


def declare_grammar(kb, grammar, *, open_class: str | None = None) -> None:
    """Give `kb` a grammar, compiling its banks ONCE. `grammar` is a `Grammar`, CNL text, or a path.

    `open_class`: the category an UNDECLARED word defaults to (`"noun"`), i.e. open vocabulary. Off by
    default, which is why this route required every word declared. Safe to switch on since
    `chart_bank`'s default was narrowed to words the grammar says nothing about — before that, opening
    the vocabulary made every declared content word ALSO a noun and quietly ambiguous.

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
    kb.registers[GRAMMAR_REGISTER] = compile_grammar(gram, open_class=open_class)
    sync_vocabulary(kb)                    # a KB may already have declared relations before this


#: The grammar category a KB's declared relation (`R is a relation`) contributes to the lexicon.
#: MEASURED, not assumed: all 9 distinct predicates across every shipped corpus (`acts_on`, `costs`,
#: `have`, `needs`, `outranks`, `produces`, `want`, `wants`) are used in `S P O` position, and the
#: derived grammar parses 69 of 76 corpus fact lines with ZERO mis-mappings. The 7 refusals are two
#: genuinely-absent constructions (degree adverbs `very risky`, imperatives `don't sell …`), not
#: mis-categorised relations.
RELATION_CATEGORY = "transitive"


def sync_vocabulary(kb) -> bool:
    """Extend the live grammar's lexicon with relations the KB has DECLARED. Returns True if it grew.

    ⭐ THE MIGRATION COST OF MAKING THIS ROUTE THE DEFAULT IS ~ZERO, AND THIS IS WHY. A predicate has
    always needed a declaration: the SHIPPED route refuses `get_beans produces beans` outright until
    the KB says `produces is a relation` (measured). So the grammar route's `produces is a transitive`
    was never a NEW burden — it is the SAME declaration in a different spelling, and therefore it can
    be DERIVED rather than written twice. An existing KB migrates without editing its corpus.

    RUNTIME GROWTH IS THE REAL REQUIREMENT, not a one-off read at declaration time. A corpus declares
    its relations in its own text, so on this route `produces is a relation` is itself parsed by the
    grammar (as `clause asserts subj is_a kind`) — the vocabulary therefore arrives DURING ingestion,
    after the banks were compiled. Hence a sync per utterance rather than a single pass.

    CHEAP BECAUSE IT RECOMPILES, NEVER RE-READS. Measured: `compile_grammar` is 13 ms while
    `load_grammar` is 1678 ms (126×) — the text-to-`Grammar` parse is the expensive half. This mutates
    the already-parsed `Grammar` and recompiles, so growth costs ~13 ms and only when the vocabulary
    actually changed. Re-reading the source text per utterance would have cost 1.7 s each.

    A relation already declared in the grammar is LEFT ALONE — an explicit `R is a intransitive`
    beats the derived default, so a grammar can always override what this infers."""
    banks = kb.registers.get(GRAMMAR_REGISTER)
    if banks is None:
        return False
    from .forms import declared_relations
    gram = banks.grammar
    # TWO SOURCES, and the split is the L0 migration in progress (option C, 2026-07-20). The
    # REGISTER is the new home — an L0 declaration reaching intake never becomes a fact. The GRAPH
    # read stays for the shipped route: `load_corpus` bypasses intake entirely (`_recognize` over
    # `_ALL_FORMS`), so a corpus's `R is a relation` still lands as `R is_a relation`, and
    # `forms.relation_forms` rebuilds from the graph per batch. Union means a KB that was loaded
    # from a corpus AND then talked to keeps both halves of its vocabulary.
    known = {**{r: RELATION_CATEGORY for r in declared_relations(kb)}, **declared_vocabulary(kb)}
    fresh = sorted(w for w, _c in known.items() if w and w not in gram.lexicon)
    if not fresh:
        return False
    for r in fresh:
        gram.lexicon[r] = [known[r]]
    kb.registers[GRAMMAR_REGISTER] = compile_grammar(gram, open_class=banks.open_class)
    return True


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


def question_of(kb, toks, banks):
    """The triple this utterance ASKS about, or None. See `force_triple`."""
    return force_triple(kb, toks, banks, "ask")


def goal_of(kb, toks, banks):
    """The `(target, _, type)` this utterance sets as a GOAL, or None.

    The `goal` force. Like `ask` it commits no FACT — `gclause` declares no `asserts` — but unlike a
    question it LEAVES SOMETHING BEHIND: a `<goal>` node the act loop runs on. The router therefore
    REIFIES it (via the shipped goal path, so the node is structurally identical to the one the form
    route mints) rather than just answering and forgetting."""
    return force_triple(kb, toks, banks, "goal")


def command_of(kb, toks, banks):
    """The `(imperative_word, _, target)` this utterance COMMANDS, or None.

    The `command` force — the speech acts (`focus on lion`, `be cautious`, `run build`). Like `ask`
    and `goal` it commits no fact; what separates it is that it changes STEPPING state (a focus
    frame, the policy register, a `<run>` request) rather than anything the KB believes.

    THE OP IS THE IMPERATIVE WORD ITSELF, and the router maps it to a handler through a declared
    table. That keeps the grammar saying only what it can see — this utterance is a command, and
    this is the verb — while what a given verb DOES stays where it already lives (`focus`,
    `policy.STANCES`, `procedure_surface`). The alternative, declaring one force verb per act, would
    put domain behaviour in the grammar file."""
    return force_triple(kb, toks, banks, "command")


def mint_goal(kb, target: str, gtype: str) -> str:
    """Mint the `<goal>` node the act loop runs on — the `goal` force's reification.

    PARITY WITH THE SHIPPED FORM IS THE ACCEPTANCE CRITERION, exactly as it was for `Band` vs
    `possibility.add_fork`: the node must be structurally identical to the one `form.goal` mints
    (`<goal> -[target]-> X`, `<goal> -[type]-> Y`), so `intake`'s `nodes_named(GOAL)` diff and the act
    loop cannot tell the two routes apart. A parallel-but-different encoding would be worse than no
    feature.

    THE GOAL NODE IS MINTED FRESH, ITS ENDPOINTS ARE INTERNED, and the asymmetry is load-bearing:
    interning the `<goal>` too would make a second goal REUSE the first node and hang a second
    `target` on it — one goal with two targets, rather than two goals. The endpoints must intern for
    the opposite reason: the goal has to be ABOUT the entity everything else is about.

    Authored as an ISA program through the interpreter rather than by poking the substrate — the same
    discipline `assemble_facts` follows (`machine_semantics_are_isa_programs`)."""
    from ..attrgraph import graded as graded_attr, valued
    from ..focus import GOAL
    from ..machine import MINT, Machine
    prog = [
        MINT("_g", attrs={"name": valued(GOAL)}, control=True),
        MINT("_t", attrs={"name": valued(target)}, intern=True),
        MINT("_k", attrs={"name": valued(gtype)}, intern=True),
        MINT("_r1", attrs={"target": graded_attr(1.0)}, in_edges=["_g"], edges=["_t"], dedup=True),
        MINT("_r2", attrs={"type": graded_attr(1.0)}, in_edges=["_g"], edges=["_k"], dedup=True),
    ]
    states = Machine().run(kb, prog)          # `run` returns the post-apply state STREAM
    return states[0].regs["_g"]


def _utterance_spans(kb, toks):
    """(span, category-name) for every span this utterance's tokens begin. The walk `asserts_content`
    does, factored out so the force readers share one traversal."""
    for t in set(toks):
        for r in kb.into(t):
            if not kb.has_key(r, "begin"):
                continue
            for span in kb.into(r):
                for cr, co in kb.relations_from(span):
                    if kb.has_key(cr, "cat"):
                        yield span, kb.name(co)


def _slot_filler(kb, span, slot: str) -> str | None:
    for r, o in kb.relations_from(span):
        if kb.predicate(r) == slot:
            return o
    return None


def force_triple(kb, toks, banks, mode: str) -> tuple[str, str, str] | None:
    """The `(subject, predicate, object)` this utterance ASKS about, or None if it asks nothing.

    ⭐ THE `ask` FORCE, read off the parse (`design/form_inventory.md` §4b). A question is not a
    weaker assertion — it COMMITS NOTHING and changes no beliefs — so `<cat> asks subj pred obj`
    generates no fold rule at all. The declaration records only WHICH SLOTS carry the asked triple,
    and this reads them.

    WHY A READER RATHER THAN A REIFIED `<question>` NODE, for now: the answer is not graph state, it
    is a value returned to the caller, and reading the parse is exactly what `asserts_content` already
    does for the assert force — surface plus grammar, never the interpretation layer. A reified intent
    node is the right shape for forces that leave something behind (`run NAME` seeds `<run> proc NAME`
    for precisely that reason); ASK leaves nothing.

    Guards are honoured exactly as `assert_bank` honours them, so one declaration surface means one
    reading of it: `when G` requires slot G present, `unless G` requires it absent."""
    gram = banks.grammar
    asks = [d for d in gram.assertions if d.get("amode") == mode and d.get("aobj") is not None]
    if not asks:
        return None
    names = gram.slot_names
    for span, cat in _utterance_spans(kb, toks):
        for d in asks:
            if d["acat"] != cat:
                continue
            if "awhen" in d and _slot_filler(kb, span, d["awhen"]) is None:
                continue
            if "aunless" in d and _slot_filler(kb, span, d["aunless"]) is not None:
                continue
            subj = _slot_filler(kb, span, d["asubj"])
            obj = (_slot_filler(kb, span, d["aobj"]) if d["aobj"] in names else None)
            pred = (_slot_filler(kb, span, d["apred"]) if d["apred"] in names else None)
            if subj is None or (d["aobj"] in names and obj is None):
                continue
            return (kb.name(subj),
                    kb.name(pred) if pred is not None else d["apred"],
                    kb.name(obj) if obj is not None else d["aobj"])
    return None


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
    re-parsing.

    THE REGISTER IS THE LIVE SOURCE OF TRUTH FOR THE BANKS, and vocabulary is synced AFTER the fold.
    A KB declares its relations in its own text (`produces is a relation`), so on this route that
    declaration is itself parsed here — the vocabulary therefore arrives DURING ingestion. Syncing
    after the fold means the register reflects everything declared SO FAR the instant this call
    returns; syncing only before it would leave the register lying about what the KB knows until some
    later utterance happened to run. Reading the register first is what keeps a caller's stale
    `banks` reference harmless, since a sync RECOMPILES and replaces them."""
    banks = kb.registers.get(GRAMMAR_REGISTER, banks)

    # ⭐ L0 FIRST — a declaration ABOUT the language, recognized by a FIXED form and never by the
    # object grammar (see `VOCABULARY_FORMS`). It must precede the parse for the reason the whole
    # level axis exists: parsing it with the grammar it modifies is what made it self-destroying.
    # Nothing here touches the KB graph, so it cannot leak into reasoning or collide with an entity.
    declaration = recognize_vocabulary(utterance)
    if declaration is not None:
        word, kind = declaration
        category = resolve_vocabulary(banks, kind)
        if category is not None:
            declare_vocabulary(kb, word, category)
            sync_vocabulary(kb)                  # the word is usable by the VERY NEXT utterance
            return "vocabulary", {"word": word, "category": category}
        # `K` names no category, so this is not a declaration at all — `lion is a cat`. Fall
        # through to the ordinary parse; the SHAPE matching is not the decision, the grammar is.

    outcome, toks, _eos = parse(kb, utterance, banks)
    if outcome == REFUSED:
        return "unrecognized", {"tokens": toks}
    if outcome == AMBIGUOUS:
        from .grammar import ambiguous_spans
        spans = ambiguous_spans(kb, toks)
        return "ambiguous", {"tokens": toks,
                             "spans": [(kb.name(a), kb.name(b)) for a, b in spans]}

    # ⭐ WHAT THIS UTTERANCE COMMITTED, as a CONTENT diff around the fold — the entity-side input to
    # `reconsider`'s dirty grains (a grain is `(predicate, object-name)`, never a node id).
    #
    # A CONTENT DIFF RATHER THAN A NODE SNAPSHOT, and that is the whole design. The shipped route
    # selects "relations not in `nodes_before`", which is the proxy already measured DEFECTIVE on this
    # route: a re-derived relation is a NEW NODE ID, so any rebuild makes everything look new (see
    # `asserts_content`). Grains are content, so diffing content is stable under re-minting,
    # re-interpretation and `reconsider`'s rebuild alike — the same repair, applied to the second
    # reader that was leaning on identity.
    committed_before = set(facts(kb))
    scope = extend(kb, banks)
    committed = set(facts(kb)) - committed_before

    # ⭐ FORCE, decided from the folded parse. A question COMMITS NOTHING — `qclause` declares no
    # `asserts`, so folding one writes no fact — but it IS folded, and that is deliberate rather than
    # a compromise: `interpret_mentions` resolves the question's words to the SAME entities the facts
    # were written on, which is what makes the question REFER. Reading slots before the fold was the
    # first attempt and found nothing, because slot percolation runs in `interpret`, not `parse`.
    # What a question must not do is change beliefs, and it does not (asserted by test).
    asked = question_of(kb, toks, banks)
    if asked is not None:
        return "question", {"tokens": toks, "query": asked, "scope": scope}

    wanted = goal_of(kb, toks, banks)
    if wanted is not None:
        return "goal", {"tokens": toks, "goal": (wanted[0], wanted[2]), "scope": scope}

    ordered = command_of(kb, toks, banks)
    if ordered is not None:
        return "command", {"tokens": toks, "command": (ordered[0], ordered[2]), "scope": scope}

    verdict = "fact" if asserts_content(kb, toks, banks) else "unrecognized"
    sync_vocabulary(kb)                # this utterance may have DECLARED a relation — see above
    return (verdict,
            {"tokens": toks, "scope": scope, "centers": utterance_centers(kb, toks),
             "committed": committed})


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
