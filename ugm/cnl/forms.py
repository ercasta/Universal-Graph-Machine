"""
Forms — loading CNL as-is, with no compile seam (vision §3).

Two pieces, both living in the one substrate:

1. `tokenize` — the ONE mechanical, meaning-free step that stays outside the graph
   rules: a TOOL (vision §8) that turns a raw CNL sentence (an opaque string) into
   token NODES chained by 'next' relations. It assigns no meaning — just structure.

2. `FORM_RULES` — the acceptance grammar expressed as ordinary normalization
   rewrite rules (surface tokens → canonical nodes). Adding an accepted sentence
   shape is adding a `Rule`, not editing a parser. These are monotone: they
   annotate the token chain with canonical relations, never deleting the surface.

`load_text` tokenizes; the caller then runs `FORM_RULES` (plus any domain rules)
with `rewriter.run`. Tokenizing + normalizing + reasoning all interleave in one
engine — there is no parse phase separated from reasoning by a wall.
"""
from __future__ import annotations

from ..production_rule import Pat, Rule, binder, is_bound_literal, literal_name
from ..lowering import run_bank
from ..vocabulary import IS_A, MENTION
from ..world_model import Graph


# ---------------------------------------------------------------------------
# The tokenizer tool — opaque string -> token nodes + 'next' adjacency
# ---------------------------------------------------------------------------

def tokenize(graph: Graph, sentence: str, *, control: bool = False) -> str:
    """Emit token nodes for `sentence`, chained by 'next' relations.

    Returns the '<sentence>' anchor node id. Mechanical only: splits on
    whitespace, lowercased; a real tokenizer would handle punctuation/casing —
    that is still a tool, never a rule.

    CASE (handoff 1b): every sentence is lower-cased here, so CNL is
    case-insensitive and rule literals are lower-case. Code that builds graph
    nodes DIRECTLY (bypassing this tokenizer) MUST lower-case its names to match
    — else a proper-noun fact node `Gary` never matches a rule literal `gary`.

    `control=True` flags the token nodes as CONTROL (not just the chain edges): use it when the
    sentence is an INTERACTION recognized INTO a live KB rather than corpus content — a QUESTION
    (Phase 8.2, `query._recognize_query_live`), whose tokens must stay fact-invisible (skipped by every
    fact reader) and be GC-able, so asking never mutates the monotone fact layer even though it now lands
    in the one substrate instead of a throwaway graph."""
    anchor = graph.add_node("<sentence>", control=True)   # scaffolding hub, not a fact
    prev: str | None = None
    for word in sentence.lower().split():
        if word == "an":
            word = "a"          # article normalization ("an owl" ≡ "a owl") — mechanical and
                                # meaning-free like the lowercasing above, and the one chokepoint
                                # every path (facts, questions, rules, goals) shares, so every
                                # `a?`-anchored form handles `an` for free (gap closed 2026-07-16).
                                # Consequence: `an` is not a usable CNL entity name (like case).
        tok = graph.add_node(word, control=control)       # a token = potential CONTENT (fact) unless it
        if prev is None:                                  # is an interaction (question) -> control
            graph.add_relation(anchor, "first", tok, control=True)
        else:
            graph.add_relation(prev, "next", tok, control=True)   # chain links = ephemeral scaffolding
        prev = tok
    return anchor


def load_text(graph: Graph, text: str) -> list[str]:
    """Tokenize each non-empty line of `text`. Returns the sentence anchor ids."""
    return [tokenize(graph, line) for line in text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Surface normalization — determiners, multi-word NPs, pronouns, ALL AS FORMS
# ---------------------------------------------------------------------------
#
# Raw NL adds three things controlled single-word CNL lacks: DETERMINERS ("the bald eagle"),
# MULTI-WORD entity names ("bald eagle"), and PRONOUNS ("it"). All three are handled by
# NORMALIZATION FORMS (graph-rewrite rules on the token chain), NOT imperative Python — the
# grammar lives in the substrate (vision §3: "forms = acceptance grammar as rules"). The one
# concession is that these forms may `drop` surface `next`/`first` edges: the token chain is
# EPHEMERAL scaffolding (control, torn down by `_strip_surface`), so rewriting it is
# control-deletes-control (§5), never fact deletion.
#
#   1. DETERMINERS ("the"/demonstratives) are dropped: a form bridges the chain past the
#      determiner token. Articles "a"/"an" are dropped only when LEADING a subject (their
#      copula-article use `is a Y` is mid-clause, where the is_a form consumes them).
#   2. MULTI-WORD entities DECOMPOSE (not merge): a modifier before the noun-phrase HEAD becomes
#      a gradable ATTRIBUTE — "the bald eagle" -> head `eagle` + `eagle is bald`; "the big bald
#      eagle" -> `eagle is big`, `eagle is bald`. Structure is exposed to reasoning, not hidden
#      in an opaque "bald eagle" string. The HEAD is the content token before a keyword or the
#      chain end; decomposition peels modifiers rightward into it. A copula guard stops it
#      splitting the subject+predicate of a copula-state ("is alice happy").
#   3. PRONOUNS ("it"/"they"/…) resolve to the DISCOURSE SUBJECT (the subject of the most recent
#      line) — a content-blind recency policy (vision §14 metareasoning, like fuel/idf), so the
#      Session tracks it and `expand_pronouns_text` substitutes the pronoun with that name before
#      tokenizing. Anaphora is name-level coreference (the pronoun *is* that entity, one node),
#      which the path-language cannot compute — the same name-op category as `canonicalize`, kept
#      minimal and OUTSIDE the grammar rules.
#
# `surface_forms(...)` builds the determiner/decomposition banks from DATA (the active forms'
# keywords + declared relation/verb/determiner words); `normalize_surface` runs them in the
# necessary strata (tag -> strip determiners -> decompose). Indefinite existentials
# (`someone`/`something`, which quantify rather than refer) are deliberately out of scope.

# Closed-class function words, module DATA (declared_* unions any user `X is a determiner`, etc.)
DEFAULT_DETERMINERS: tuple[str, ...] = ("the", "this", "that", "these", "those")
DEFAULT_ARTICLES: tuple[str, ...] = ("a", "an")               # stripped only when LEADING
DEFAULT_PRONOUNS: tuple[str, ...] = ("it", "they", "he", "she", "him", "her", "them")

# Surface-only tag predicates the normalization forms accrete; `_strip_surface` removes them.
SURFACE_TAGS: tuple[str, ...] = ("kw", "copula", "np_head_kw", "np_head_end", "det_np", "if_ctx",
                                 "def_np")

# The full set of SCAFFOLDING predicates — the chain links + the surface tags. Their reified
# relations are CONTROL-layer (ephemeral, torn down by `_strip_surface`), so a normalization form
# may rewrite the chain (`drop`/re-bridge) without violating §5 fact-immutability. `run_bank` mints
# any head with one of these predicates as control (`control_preds=`), and `tokenize` marks the
# raw chain control; under `DROP_CTRL` that is what makes the determiner-strip / NP-decompose
# legal on the ISA engine (control-deletes-control), as the module note above always intended.
SCAFFOLD_PREDS: frozenset[str] = frozenset({"next", "first", *SURFACE_TAGS})

# Quantifier words that INTRODUCE a noun phrase (like a determiner) without being stripped.
DEFAULT_QUANTIFIERS: tuple[str, ...] = ("every", "all", "some", "any", "no")

# ---------------------------------------------------------------------------
# Rule variable words — the NL surface of a universal law's bound variable
# ---------------------------------------------------------------------------
#
# In a universal rule `if someone is rough then they are young`, the words `someone` and `they`
# are not entities — they QUANTIFY (decision_quantification_coreference): the law binds ALL
# witnesses. So in a RULE they denote a bound VARIABLE, not a coreferable mention. Two DATA
# classes, split by the natural person/thing + anaphor pairing of the controlled fragment:
# `someone`/`they` (person) -> `?x`, `something`/`it` (thing) -> `?y`. The mapping is applied by
# `expand_rules` (a §8 name-op, on the calculator side of the quote/eval wall) when it reflects a
# folded rule fragment into an executable `Rule`, so `someone` and `they` unify to one variable
# with no coreference. A word NOT in either class (a literal entity like `lion`) is left as-is, so
# a ground rule `if the lion eats the dog then the lion chases the cat` reflects with no variable.
# `people`/`things` are the PLURAL universal-noun surface: `Cold things are kind` = "all things
# that are cold are kind" -> `?x is kind when ?x is cold` (see authoring.PLURAL_UNIVERSAL_FORMS).
# They quantify exactly like `someone`/`something`, so they join the same variable classes.
PERSON_VARS: tuple[str, ...] = ("someone", "anyone", "everyone", "they", "them", "people")
THING_VARS: tuple[str, ...] = ("something", "anything", "everything", "it", "things")

# The plural universal-noun surface (`Cold things are kind`) and the do-support auxiliaries
# (`does not V O`), as DEFAULT closed-class words. Like DEFAULT_PRONOUNS/DEFAULT_DETERMINERS, these
# are grammar function words with a `declared_*` KB extension below (lexicon stays overridable-as-
# DATA): a domain may add its own (`critters is a variable`, `doth is an auxiliary`).
DEFAULT_UNIV_NOUNS: tuple[str, ...] = ("things", "people")
DEFAULT_AUX: tuple[str, ...] = ("does", "do", "did")


def rule_var_name(name: str, declared: tuple[str, ...] | set[str] = ()) -> str:
    """Map a rule-fragment token NAME to a bound variable. A built-in quantifier/anaphor word maps
    to its class variable (`someone`/`they` -> `?x`, `something`/`it` -> `?y`, so a quantifier and
    its anaphor UNIFY); a domain-`declared` variable word maps to a variable named after itself
    (`critters` -> `?critters`); any other name is returned unchanged. A §8 name-op used by
    `expand_rules` (which passes `declared_rule_variables(graph)`)."""
    if name in PERSON_VARS:
        return "?x"
    if name in THING_VARS:
        return "?y"
    if name in declared:
        return "?" + name
    return name


def declared_rule_variables(graph: Graph) -> set[str]:
    """Domain variable words declared `X is a variable` (opt-in extension of the built-in
    quantifier/anaphor classes). Each maps to `?<word>` in a rule and also gets a plural-universal
    form (`declared_univ_nouns`), so `Cold critters are kind` works once `critters is a variable`."""
    return _declared_as(graph, "variable")


def declared_auxiliaries(graph: Graph) -> set[str]:
    """Do-support auxiliaries for verb negation: DEFAULT_AUX + any user-declared `X is an
    auxiliary`. Each `<aux> not V O` folds to a NAC (authoring._verb_not_sugar)."""
    return set(DEFAULT_AUX) | _declared_as(graph, "auxiliary")


def declared_univ_nouns(graph: Graph) -> set[str]:
    """Plural universal-noun words (`Cold <noun> are <Pred>`): DEFAULT_UNIV_NOUNS + declared
    variable words (a declared variable doubles as a plural universal noun)."""
    return set(DEFAULT_UNIV_NOUNS) | declared_rule_variables(graph)


# Copula synonyms normalized to `is` before parsing — plural agreement (`they are young`) is
# lexical morphology, a mechanical tokenizer concern (§8), not reasoning; folding `are` to `is`
# lets one copula grammar handle `X is Y` and `they are Y` alike.
DEFAULT_COPULA_SYNONYMS: tuple[str, ...] = ("are",)


def normalize_lexical(line: str) -> str:
    """Normalize copula morphology in `line` (`are` -> `is`). Mechanical, meaning-free — the
    same category as the tokenizer's lowercasing; applied to NL-facing input before tokenizing."""
    return " ".join("is" if w.lower() in DEFAULT_COPULA_SYNONYMS else w for w in line.split())


def form_keywords(rules: list[Rule]) -> set[str]:
    """The grammar's FUNCTION WORDS, read as DATA from `rules`: every LHS bound-literal
    token name (`is?`->`is`, `a?`->`a`, a declared relation's `visits?`->`visits`, ...).
    A noun-phrase decomposition must not cross these. Derived from the active forms, never a
    hardcoded stop-list — add a form and its keywords are picked up automatically. `<...>`
    control tokens are excluded (they are RHS scaffolding, never surface words)."""
    kws: set[str] = set()
    for r in rules:
        for pat in r.lhs:
            for tok in pat.tokens():
                if is_bound_literal(tok):
                    nm = literal_name(tok)
                    if nm and not nm.startswith("<"):
                        kws.add(nm)
    return kws


def _chain_tokens(graph: Graph, anchor: str) -> list[str]:
    """The token node ids of a sentence, in order, following `first` then the `next` chain."""
    first = next((o for r, o in graph.relations_from(anchor)
                  if graph.has_key(r, "first")), None)
    toks: list[str] = []
    cur, seen = first, set()
    while cur is not None and cur not in seen:
        seen.add(cur)
        toks.append(cur)
        cur = next((o for r, o in graph.relations_from(cur)
                    if graph.has_key(r, "next")), None)
    return toks


def _tag_forms(words, tag: str) -> list[Rule]:
    """Per-word forms tagging every token named `w` with `tag yes`, from both `next` and `first`
    (a token may lead a sentence). A §8 form-generator over the word DATA, like `relation_forms`.
    Tagging is a prior stratum so a later form's NAC on the tag is never raced."""
    forms: list[Rule] = []
    for w in sorted(words):
        forms.append(Rule(key=f"surf.tag.{tag}.{w}.n",
                          lhs=[Pat("?p", "next", f"{w}?")], rhs=[Pat(f"{w}?", tag, "yes")]))
        forms.append(Rule(key=f"surf.tag.{tag}.{w}.f",
                          lhs=[Pat("?s", "first", f"{w}?")], rhs=[Pat(f"{w}?", tag, "yes")]))
    return forms


# `is` is a subject/predicate splitter wherever it sits (mid OR leading — the copula-state
# question `is S O` leads with it), tagged `copula` so decomposition won't cross it.
_COPULA_FORMS: list[Rule] = [
    Rule(key="surf.copula.n", lhs=[Pat("?p", "next", "is?")], rhs=[Pat("is?", "copula", "yes")]),
    Rule(key="surf.copula.f", lhs=[Pat("?s", "first", "is?")], rhs=[Pat("is?", "copula", "yes")]),
]


def _np_seed_forms(seeders) -> list[Rule]:
    """A NOUN PHRASE is a run of content words INTRODUCED by a determiner / article / quantifier —
    that is the linguistic signal that separates "the bald eagle" (an NP to decompose) from
    "alice sends parcel" (a sentence attempt: undeclared verb, left for the n-ary form to reject).
    Each seeder tags its immediate follower `det_np`; `_DET_NP_PROPAGATE` spreads it across the
    content run; decomposition fires only on a `det_np` modifier. Seeds from `next` AND `first`."""
    forms: list[Rule] = []
    for w in sorted(seeders):
        forms.append(Rule(key=f"surf.npseed.{w}.n",
            lhs=[Pat("?p", "next", f"{w}?"), Pat(f"{w}?", "next", "?x")],
            rhs=[Pat("?x", "det_np", "yes")]))
        forms.append(Rule(key=f"surf.npseed.{w}.f",
            lhs=[Pat("?s", "first", f"{w}?"), Pat(f"{w}?", "next", "?x")],
            rhs=[Pat("?x", "det_np", "yes")]))
    return forms


# Spread `det_np` rightward across the content run (stops at a keyword), so every modifier of a
# determiner-introduced NP is decomposable.
_DET_NP_PROPAGATE: Rule = Rule(
    key="surf.np.propagate",
    lhs=[Pat("?x", "det_np", "yes"), Pat("?x", "next", "?y")],
    nac=[Pat("?y", "kw", "yes")], rhs=[Pat("?y", "det_np", "yes")])


def _determiner_forms(determiners, articles, definites=()) -> list[Rule]:
    """Bridge the chain past a determiner (dropping its surface edges). A determiner is stripped
    only when it INTRODUCES an entity — i.e. its follower is a CONTENT word (NAC `?x kw`) — so a
    determiner inside a fixed keyword phrase (`is the same as`) is kept. Full determiners strip
    anywhere; articles `a`/`an` strip only when LEADING (mid `is a Y` is the is_a article the
    copula form consumes).

    DEFINITENESS (opt-in) is handled separately by `_definite_forms` (it marks the whole NP span
    `is_unique`, including a multi-word head), not here — this form only strips the determiner."""
    forms: list[Rule] = []
    for d in sorted(determiners):
        forms.append(Rule(key=f"surf.det.first.{d}",
            lhs=[Pat("?s", "first", f"{d}?"), Pat(f"{d}?", "next", "?x")],
            nac=[Pat("?x", "kw", "yes")],
            rhs=[Pat("?s", "first", "?x")],
            drop=[Pat("?s", "first", f"{d}?"), Pat(f"{d}?", "next", "?x")]))
        forms.append(Rule(key=f"surf.det.mid.{d}",
            lhs=[Pat("?p", "next", f"{d}?"), Pat(f"{d}?", "next", "?x")],
            nac=[Pat("?x", "kw", "yes")],
            rhs=[Pat("?p", "next", "?x")],
            drop=[Pat("?p", "next", f"{d}?"), Pat(f"{d}?", "next", "?x")]))
    for a in sorted(articles):
        forms.append(Rule(key=f"surf.art.first.{a}",
            lhs=[Pat("?s", "first", f"{a}?"), Pat(f"{a}?", "next", "?x")],
            nac=[Pat("?x", "kw", "yes")],
            rhs=[Pat("?s", "first", "?x")],
            drop=[Pat("?s", "first", f"{a}?"), Pat(f"{a}?", "next", "?x")]))
    return forms


# A content token is a noun-phrase HEAD if it is followed by a keyword (`np_head_kw`, a
# keyword-DELIMITED NP) or is the chain end (`np_head_end`, a trailing NP). The two are kept
# distinct so the copula guard applies only to a trailing bare predicate (see decomposition).
_HEAD_FORMS: list[Rule] = [
    Rule(key="surf.head.kw",
         lhs=[Pat("?h", "next", "?k"), Pat("?k", "kw", "yes")],
         nac=[Pat("?h", "kw", "yes")], rhs=[Pat("?h", "np_head_kw", "yes")]),
    Rule(key="surf.head.end.mid",
         lhs=[Pat("?p", "next", "?h")],
         nac=[Pat("?h", "kw", "yes"), Pat("?h", "next", "?z")], rhs=[Pat("?h", "np_head_end", "yes")]),
    Rule(key="surf.head.end.first",
         lhs=[Pat("?s", "first", "?h")],
         nac=[Pat("?h", "kw", "yes"), Pat("?h", "next", "?z")], rhs=[Pat("?h", "np_head_end", "yes")]),
]

# Decomposition: a content modifier `?m` immediately before a noun-phrase head `?h` becomes the
# attribute `?h is ?m`, bridging the chain past `?m` (so modifiers peel rightward into the head).
# NAC: `?m` is not a keyword. A trailing (`np_head_end`) head additionally carries the COPULA
# GUARD — a modifier right after `is` is the SUBJECT of a copula-state ("is alice happy"), not a
# modifier, so it is NOT decomposed. A keyword-delimited (`np_head_kw`) head has no such guard: it
# is a real NP ("is the bald eagle a bird" -> decompose `bald eagle`). A first-token modifier has
# no predecessor, so no guard applies.
def _decomp(key, head_tag, *, first, guard):
    m_pos = [Pat("?s", "first", "?m")] if first else [Pat("?p", "next", "?m")]
    bridge = Pat("?s", "first", "?h") if first else Pat("?p", "next", "?h")
    nac = [Pat("?m", "kw", "yes")] + ([Pat("?p", "copula", "yes")] if guard else [])
    # `?m det_np`: only a modifier inside a determiner/quantifier-introduced NP decomposes.
    return Rule(key=key, lhs=[*m_pos, Pat("?m", "det_np", "yes"),
                              Pat("?m", "next", "?h"), Pat("?h", head_tag, "yes")],
                nac=nac, rhs=[Pat("?h", "is", "?m"), bridge],
                drop=[m_pos[0], Pat("?m", "next", "?h")])


_DECOMP_FORMS: list[Rule] = [
    _decomp("surf.decomp.first.kw", "np_head_kw", first=True, guard=False),
    _decomp("surf.decomp.first.end", "np_head_end", first=True, guard=False),
    _decomp("surf.decomp.mid.kw", "np_head_kw", first=False, guard=False),
    _decomp("surf.decomp.mid.end", "np_head_end", first=False, guard=True),
]

def _definite_forms(definites) -> list[Rule]:
    """DEFINITENESS (opt-in): a definite determiner (`the is a definite`) marks its ENTIRE noun-
    phrase span `is_unique`. A definite reference denotes ONE individual, and its mentions MERGE
    (`Session._merge_unique`). Marking the whole SPAN — not just the first token — means a
    multi-word entity's HEAD is marked too (`the bald eagle` -> `bald`+`eagle` both unique, so the
    head `eagle` merges): the fix for the O(k²) coref HANG on a multi-word definite entity. Seed
    `def_np` on the token after each definite determiner (from `next` and `first`), propagate it
    rightward across the content run (stop at a keyword), and mark every `def_np` token unique.
    Inert when no definite is declared (nothing seeds `def_np`)."""
    forms: list[Rule] = []
    for d in sorted(set(definites)):
        forms.append(Rule(key=f"surf.defnp.seed.{d}.n",
            lhs=[Pat("?p", "next", f"{d}?"), Pat(f"{d}?", "next", "?x")],
            nac=[Pat("?x", "kw", "yes")], rhs=[Pat("?x", "def_np", "yes")]))
        forms.append(Rule(key=f"surf.defnp.seed.{d}.f",
            lhs=[Pat("?s", "first", f"{d}?"), Pat(f"{d}?", "next", "?x")],
            nac=[Pat("?x", "kw", "yes")], rhs=[Pat("?x", "def_np", "yes")]))
    if not forms:
        return []
    forms.append(Rule(key="surf.defnp.propagate",
        lhs=[Pat("?x", "def_np", "yes"), Pat("?x", "next", "?y")],
        nac=[Pat("?y", "kw", "yes")], rhs=[Pat("?y", "def_np", "yes")]))
    forms.append(Rule(key="surf.defnp.unique",
        lhs=[Pat("?x", "def_np", "yes")], rhs=[Pat("?x", "is_unique", "<yes>")]))
    return forms


# `if`-context tag: mark the `if` that leads a universal rule and PROPAGATE the tag rightward
# along the chain to every following token (including the `then` separator). Its ONLY consumer is
# a NAC on the `form.then` SEQUENCING rule (`X then Y -> X before Y`): inside `if BODY then HEAD`
# the `then` is a rule separator, not sequencing, so `form.then` must not fire on it. Because this
# runs as a surface-normalization stratum (to fixpoint, BEFORE the content forms), the tag is on
# `then` before `form.then` is ever evaluated — no race (the content forms run non-stratified).
_IF_CTX_FORMS: list[Rule] = [
    Rule(key="surf.ifctx.seed",
         lhs=[Pat("?s", "first", "if?")], rhs=[Pat("if?", "if_ctx", "yes")]),
    Rule(key="surf.ifctx.prop",
         lhs=[Pat("?x", "if_ctx", "yes"), Pat("?x", "next", "?y")],
         rhs=[Pat("?y", "if_ctx", "yes")]),
]


def surface_forms(keywords, determiners=DEFAULT_DETERMINERS, articles=DEFAULT_ARTICLES,
                  quantifiers=DEFAULT_QUANTIFIERS, definites=()) -> list[list[Rule]]:
    """The surface-normalization banks as ORDERED STRATA (each a list of forms run to fixpoint
    before the next — a hand-stratification the tag-then-use NACs and the strip-before-decompose
    dependency require). Strata: (1) tag keywords + copula, seed + propagate the `det_np` noun-
    phrase span; (2) strip determiners; (3) head-tag + decompose determiner-introduced multi-word
    NPs. `keywords` is the grammar's function words (DATA — `form_keywords` + declared
    relation/verb/prep words); determiners/articles/quantifiers default to the closed-class sets.
    `definites` (opt-in, `declared_definites`) marks entities introduced by a definite determiner
    `is_unique` (see `_determiner_forms`)."""
    kw = set(keywords) | set(determiners) | set(articles)
    seeders = set(determiners) | set(articles) | set(quantifiers)
    return [
        _tag_forms(kw, "kw") + _COPULA_FORMS + _IF_CTX_FORMS,  # 1. tag fn words + copula + if-ctx
        _np_seed_forms(seeders) + [_DET_NP_PROPAGATE]          # 2. mark the noun-phrase span
            + _definite_forms(definites),                      #    + definiteness -> is_unique (span)
        _determiner_forms(determiners, articles),       # 3. strip determiners
        _HEAD_FORMS + _DECOMP_FORMS,                     # 4. head-tag + decompose the NP
    ]


def normalize_surface(graph: Graph, anchor: str, strata: list[list[Rule]]) -> None:
    """Run the surface-normalization `strata` (from `surface_forms`) over the sentence at
    `anchor`, each stratum to fixpoint before the next (the ordering the tag-then-use NACs and
    the determiner-strip-before-decompose dependency require)."""
    for bank in strata:
        run_bank(graph, bank, control_preds=SCAFFOLD_PREDS)


def declared_determiners(graph: Graph) -> set[str]:
    """Determiners to strip: DEFAULT_DETERMINERS + any user-declared `X is a determiner`."""
    return set(DEFAULT_DETERMINERS) | _declared_as(graph, "determiner")


def declared_pronouns(graph: Graph) -> set[str]:
    """Anaphoric pronouns: DEFAULT_PRONOUNS + any user-declared `X is a pronoun`."""
    return set(DEFAULT_PRONOUNS) | _declared_as(graph, "pronoun")


def declared_definites(graph: Graph) -> set[str]:
    """Determiners declared DEFINITE via `the is a definite` (opt-in). A definite determiner marks
    the entity it introduces `is_unique` (definiteness→uniqueness); with none declared, the
    pure-§3 distinct-witness default holds. Data, per domain — not a universal engine rule."""
    return _declared_as(graph, "definite")


def subject_name(graph: Graph, anchor: str, keywords: set[str]) -> str | None:
    """The grammatical subject of a (normalized) sentence: the NAME of the first non-keyword token
    on the chain (skipping leading `goal`/`every`/`is`/`who`…). The Session tracks it as the
    discourse subject so a following pronoun resolves to it. None if the chain is all keywords."""
    for t in _chain_tokens(graph, anchor):
        nm = graph.name(t)
        if nm not in keywords:
            return nm
    return None


def expand_pronouns_text(line: str, pronouns: set[str], antecedent: str | None) -> str:
    """Replace whole-word pronoun tokens in `line` with `antecedent` (the discourse subject).
    Anaphora is name-level coreference — the pronoun denotes exactly that entity — which the
    path-language cannot compute; the same name-op category as `canonicalize`, kept minimal and
    outside the grammar. The recency choice of antecedent is a content-blind discourse policy
    (vision §14). No-op with no antecedent."""
    if not antecedent:
        return line
    return " ".join(antecedent if w.lower() in pronouns else w for w in line.split())


# ---------------------------------------------------------------------------
# Canonicalization — the coreference / normalization tax, as a tool (vision §3,§7,§8)
# ---------------------------------------------------------------------------

def _predicate_literals(rules: list[Rule]) -> set[str]:
    """Names used as literal predicates by `rules` — these are relation nodes."""
    names: set[str] = set()
    for r in rules:
        for pat in (*r.lhs, *r.rhs, *r.nac, *r.drop):
            if binder(pat.p) is None:
                names.add(literal_name(pat.p))
    return names


def mark_mentions(graph: Graph, rules: list[Rule]) -> Graph:
    """Tag every surface ENTITY mention with `is_a <mention>` — the universal coreference handle the
    declared same-name coref rule (`universal.same_name_coref_rules`) seeds BOTH variables from
    (coreference-as-rules Stage 4). The loader does not DECIDE coreference (same name ⇒ same node); it
    only marks WHAT COUNTS AS AN ENTITY, and the coreference DECISION becomes a declared value-match rule
    over the marker — a rule the author can keep, replace, or drop. The handle is position-agnostic (an
    entity is `is_a <mention>` whether it appeared as a path's subject or object), so untyped entities
    corefer without a per-domain type.

    Content filter: skip empty, `<…>`, `?vars`, predicate/structural names, so only real entity mentions
    are marked — never predicates or scaffolding. Additive + idempotent."""
    protect = {"next", "first", "proves", "uses"} | _predicate_literals(rules)
    marker: str | None = None
    for nid in list(graph.nodes()):
        nm = graph.name(nid)
        if nm == "" or nm.startswith("<") or nm.startswith("?") or nm in protect:
            continue
        if marker is None:
            named = graph.nodes_named(MENTION)
            marker = named[0] if named else graph.add_node(MENTION)
        if not any(graph.has_key(r, IS_A) and marker in graph.out(r) for r in graph.out(nid)):
            graph.add_relation(nid, IS_A, marker)
    return graph


def _fold_node(graph: Graph, rep: str, victim: str) -> None:
    """Fold `victim` into `rep`: rewire every relation node touching `victim` to `rep`, union graded
    embedding dims (rep wins on clash), then drop `victim`. Relations are reified nodes
    (subject -> relNode -> object), so victim's OUT edges are relations it subjects and its IN edges
    are relations it objects — rewire each endpoint. No provenance/split record: same-name interning is
    a hardcoded CNL-reader decision, not a defeasible coref judgement (see indexing_and_coalescing_design)."""
    for rid in graph.out(victim):                       # victim is SUBJECT of rid
        graph.remove_edge(victim, rid)
        graph.add_edge(rep, rid)
    for rid in graph.into(victim):                      # victim is OBJECT of rid
        graph.remove_edge(rid, victim)
        graph.add_edge(rid, rep)
    emb = graph.get_embedding(victim)
    if emb:
        merged = graph.get_embedding(rep)
        for dim, v in emb.items():
            merged.setdefault(dim, v)
        graph.set_embedding(rep, merged)
    graph.remove_node(victim)


def intern_mentions(graph: Graph) -> Graph:
    """Coalesce same-named ENTITY mentions into ONE node — the hardcoded "same name => same node"
    default that replaces the M^2 `same_name` coref rule + `same_as` propagation (see
    `docs/attic/indexing_and_coalescing_design.md`). Scoped to `<mention>`-marked nodes (run `mark_mentions`
    first), so `?vars`, `<control>` tokens and predicates are never merged — and rule variables stay
    distinct. Distinct same-name referents are disambiguated at authoring time by a distinct name
    (`other_alice`); programmatic producers mint distinct nodes directly and never reach this path."""
    named = graph.nodes_named(MENTION)
    if not named:
        return graph
    marker = named[0]
    groups: dict[str, list[str]] = {}
    for nid in list(graph.nodes()):
        if nid == marker:
            continue
        nm = graph.name(nid)
        if not nm:
            continue
        if any(graph.has_key(r, IS_A) and marker in graph.out(r) for r in graph.out(nid)):
            groups.setdefault(nm, []).append(nid)
    for members in groups.values():
        rep = members[0]
        for victim in members[1:]:
            _fold_node(graph, rep, victim)
    return graph


def propagate_embeddings(graph: Graph) -> Graph:
    """Union graded (embedding) attrs across each `same_as` equivalence class — the GRADED-layer
    counterpart of `universal.same_as_rules` for additive coreference. Embeddings are node ATTRS the
    path-based rule language cannot join on, so this is a §8 TOOL (same category as `graded_rules`'s
    write), run in the reasoning phase after the degree writes.

    A degree written by a graded rule lands on the ONE surface mention it fired for (`alice is very
    urgent`); without this, a sibling mention (`alice is a customer`) carries no degree. This spreads
    each class's degrees to every linked
    mention (crude union: on a dim clash, later wins), so any mention of the entity reads its degrees.
    Additive (only writes attrs, never deletes edges), so §5-safe."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Union coreferent mentions. Read links via `relations_from` (which skips provenance-inert
    # subjects/middles) — a same_as RELATION node also carries `proves`/`uses` provenance edges
    # INTO it, so reading raw `into(link)` would pick a justification node, not the true subject.
    for nid in graph.nodes():
        for rid, obj in graph.relations_from(nid):
            if graph.has_key(rid, "same_as"):
                parent[find(nid)] = find(obj)

    classes: dict[str, list[str]] = {}
    for node in list(parent):
        classes.setdefault(find(node), []).append(node)

    for members in classes.values():
        if len(members) < 2:
            continue
        merged: dict[str, float] = {}
        for m in members:
            merged.update(graph.get_embedding(m))
        if not merged:
            continue
        for m in members:
            if graph.get_embedding(m) != merged:
                graph.set_embedding(m, merged)
    return graph


def relation_predicates(graph: Graph) -> list[str]:
    """Every relation-predicate NAME present in the graph (a node that is a relation: it has
    both a subject and an object). Used to drive `same_as` propagation over exactly the
    relations in play. Excludes `same_as` itself (handled by the symmetric/transitive rules),
    scaffolding, and provenance."""
    skip = {"same_as", "next", "first", "proves", "uses"}
    preds: set[str] = set()
    for r in graph.nodes():
        nm = graph.predicate(r)
        if nm in skip or nm.startswith("?") or not nm:
            continue
        subj = next((n for n in graph.into(r) if not graph.is_inert(n)), None)
        if subj is not None and next(iter(graph.out(r)), None) is not None:
            preds.add(nm)
    return sorted(preds)


# ---------------------------------------------------------------------------
# The acceptance grammar — forms as normalization rules (surface -> canonical)
# ---------------------------------------------------------------------------
#
# A form matches a run of adjacent tokens (joined through 'next') and binds the
# keyword tokens as bound-literals ('is?', 'a?'), wiring a canonical relation
# between the content tokens. The content tokens are themselves the entity nodes,
# so canonical structure accretes on the same nodes the surface chain uses
# (homoiconic — the no-seam payoff).
#
# Subject-leading forms are ANCHORED to the sentence's 'first' token (?s first ?x)
# so they only fire at the start of a sentence. This disambiguates overlapping
# shapes: "goal paul is a mortal" must NOT also match the bare "X is a Y" on its
# "paul is a mortal" tail — anchoring prevents it, since the first token is 'goal'.

FORM_RULES: list[Rule] = [
    # "X is a Y"  ->  X is_a Y
    Rule(
        key="form.is_a",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "a?"), Pat("a?", "next", "?y")],
        rhs=[Pat("?x", "is_a", "?y")],
    ),
    # "X is an Y"  ->  X is_a Y   (the `an` variant for a vowel-initial category, e.g.
    # `doth is an auxiliary`; without it a vowel-initial `is a Y` declaration would not parse).
    Rule(
        key="form.is_an",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "an?"), Pat("an?", "next", "?y")],
        rhs=[Pat("?x", "is_a", "?y")],
    ),
    # "X has a Y"  ->  X has Y
    Rule(
        key="form.has",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "has?"), Pat("has?", "next", "a?"), Pat("a?", "next", "?y")],
        rhs=[Pat("?x", "has", "?y")],
    ),
    # "every X is a Y"  ->  X every_is_a Y   (a UNIVERSAL LAW, not a fact).
    # Quantification lives on the STATEMENT: a bare "X is a Y" is PARTICULAR (a witness),
    # but "every X is a Y" is a law binding ALL witnesses. We do NOT flatten it to the fact
    # `X is_a Y` (which only chains via is_a transitivity if the two `X` mentions are MERGED
    # — that merge is exactly what `canonicalize` was compensating for). Instead we record
    # the universal as a marker `X --every_is_a--> Y`, which `expand_universals` reflects into
    # the literal-predicate law `?u is_a X => ?u is_a Y`. A literal predicate matches witnesses
    # BY NAME across all mentions, so the law fires on every `?u is_a X` with no merge needed.
    Rule(
        key="form.every",
        lhs=[Pat("?s", "first", "every?"), Pat("every?", "next", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "a?"), Pat("a?", "next", "?y")],
        rhs=[Pat("?x", "every_is_a", "?y")],
    ),
    # "goal X is a Y"  ->  a fresh <goal> node wanting (X is_a Y)
    Rule(
        key="form.goal",
        lhs=[Pat("?s", "first", "goal?"), Pat("goal?", "next", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "a?"), Pat("a?", "next", "?y")],
        rhs=[Pat("<goal>?", "target", "?x"), Pat("<goal>?", "type", "?y")],
    ),
    # "X then Y"  ->  X before Y   (sequencing; not anchored — keyed on 'then')
    Rule(
        key="form.then",
        lhs=[Pat("?x", "next", "then?"), Pat("then?", "next", "?y")],
        nac=[Pat("then?", "if_ctx", "yes")],   # not the `then` of an `if BODY then HEAD` rule
        rhs=[Pat("?x", "before", "?y")],
    ),
    # In-statement context qualification: "X of C" -> X in C, ADDITIVELY (vision §3; a bare
    # reference is underspecified — `of` names the implicit context inline, e.g.
    # "monday OF week1 before tuesday"). These are pure normalization FORMS, not a tool: they
    # add `X in C` and BRIDGE X's `next` chain past the qualifier so the relation/fact forms
    # (which key on a literal predicate token like `before?`) still parse `X ... R Y`. Nothing
    # is deleted — the leftover `X next of` is harmless (no form keys on `of`) and the surface
    # tokens are dropped later by `_strip_surface`. Two cases: a qualifier mid-clause (bridge to
    # what follows C) and at clause end (no bridge).
    Rule(
        key="form.of.mid",
        lhs=[Pat("?x", "next", "of?"), Pat("of?", "next", "?c"), Pat("?c", "next", "?after")],
        rhs=[Pat("?x", "in", "?c"), Pat("?x", "next", "?after")],
    ),
    Rule(
        key="form.of.end",
        lhs=[Pat("?x", "next", "of?"), Pat("of?", "next", "?c")],
        nac=[Pat("?c", "next", "?z")],
        rhs=[Pat("?x", "in", "?c")],
    ),
]


# ---------------------------------------------------------------------------
# Generic binary relations — declare a relation, GENERATE a form for it
# ---------------------------------------------------------------------------
#
# A bare "X R Y" cannot be a single static form: `?x ?r ?y` would match ANY three-word
# line (and gibberish), defeating recognition reporting. CNL stays *controlled* by
# requiring the relation word to be DECLARED — `R is a relation` (recognized by the
# existing `form.is_a` -> `R is_a relation`). A §8 tool then GENERATES a concrete form
# per declared relation, exactly mirroring the relation-property meta-feature (declare ->
# expand). So only declared relations parse; `glorp the flarn` still does not.

def declared_relations(graph: Graph) -> set[str]:
    """Relation words declared via `R is a relation` (i.e. `R --is_a--> relation`).

    Candidates come from the KEY INDEX, not a whole-graph sweep: `grammar_intake.sync_vocabulary`
    calls this once per utterance, so a sweep would make a session quadratic in its own length — the
    defect family this codebase has recorded repeatedly. Small today (0.22 ms at 1445 nodes) and
    fixed before it is not."""
    rels: set[str] = set()
    candidates = (graph.nodes_with_key("is_a") if hasattr(graph, "nodes_with_key")
                  else graph.nodes())
    for r in candidates:
        if not graph.has_key(r, "is_a"):
            continue
        # skip provenance in-edges (a `proves` node points into this relation, vision §9)
        subj = next((n for n in graph.into(r) if not graph.is_inert(n)), None)
        obj = next(iter(graph.out(r)), None)
        if subj is not None and obj is not None and graph.name(obj) == "relation":
            rels.add(graph.name(subj))
    rels.discard("relation")                              # avoid a degenerate self-form
    return rels


def expand_universals(graph: Graph) -> list[Rule]:
    """Reflect each universal `every X is a Y` (a `X --every_is_a--> Y` marker) into the
    law `?u is_a X => ?u is_a Y` (a §8 tool, cf. `expand_relation_properties`).

    `X`/`Y` are LITERAL predicates in the emitted rule, so it matches every witness named
    `is_a X` by NAME — no coreference/merge of the `X` mentions is needed. This is what makes
    "all/every" a real law (binding all witnesses) rather than a flattened fact that only
    chains under a destructive merge.

    The law carries NO idempotency NAC: re-firing the same (rule, binding) is already
    suppressed by the engine's fired-set, so termination is guaranteed without one. A NAC on
    `is_a` would instead create a cross-rule negation cycle with `is_a.transitive` (which also
    produces and NACs `is_a`), which `stratify` cannot break — so the law stays a pure
    stratum-0 `is_a` producer."""
    rules: list[Rule] = []
    seen: set[tuple[str, str]] = set()
    for n in graph.nodes():
        for r, o in graph.relations_from(n):
            if not graph.has_key(r, "every_is_a"):
                continue
            X, Y = graph.name(n), graph.name(o)
            if (X, Y) in seen:
                continue
            seen.add((X, Y))
            rules.append(Rule(
                key=f"univ.{X}.is_a.{Y}",
                lhs=[Pat("?u", "is_a", X)],
                rhs=[Pat("?u", "is_a", Y)],
            ))
    return rules


def relation_forms(graph: Graph) -> list[Rule]:
    """A form `X R Y -> X --R--> Y` for each relation declared in `graph` (a §8 tool).

    Anchored to the sentence's first token (like the other subject-leading forms) so it
    only fires at the start, and keyed on the literal relation word `R?` so it never
    over-generalizes. Run these alongside `FORM_RULES` in the recognition phase."""
    return [
        Rule(
            key=f"form.rel.{r}",
            lhs=[Pat("?s", "first", "?x"),
                 Pat("?x", "next", f"{r}?"), Pat(f"{r}?", "next", "?y")],
            rhs=[Pat("?x", r, "?y")],
        )
        for r in sorted(declared_relations(graph))
    ]


# A binary-relation yes/no question (`does S V O`) needs NO per-relation form: it is GATED by its
# interrogative marker `does`, so a single GENERIC rule (`query.QUESTION_FORMS` `ask.yesno.does`)
# binds the predicate freely — exactly like the generic copula `is S P O`. Only the DECLARATIVE
# side (`relation_forms`) is per-relation, to stay controlled against gibberish.


# ---------------------------------------------------------------------------
# N-ary relations — reify a 3+-participant statement as an EVENT node (vision §1)
# ---------------------------------------------------------------------------
#
# A relation is already a NODE (`s -> [rel] -> o`); an n-ary statement generalizes that to
# an EVENT node every participant hangs off by a named role edge — the standard reification:
#
#     "alice gives book to bob"  ->  event --pred--> gives, --subj--> alice,
#                                    event --obj--> book,   --to--> bob
#
# Roles are POSITIONAL for the leading two (`subj`, the direct `obj`) and named by the
# PREPOSITION for the rest (`to`/`for`/...), exactly as English marks them. Like
# `relation_forms`, this stays CONTROLLED and FULLY DATA-DRIVEN: both the verb (`V is a verb`)
# AND the prepositions (`to is a preposition`) are DECLARED in CNL — nothing is a hardcoded
# lexical list. A §8 tool generates one form per declared verb x declared preposition
# (ditransitive, the canonical 3-participant case); the event node is a FRESH `event?`
# bound-literal (a distinct node per instance, never merged), so two gives are two events.
# FIRST SLICE limits: the surface verb form must match the declaration (no lemmatization),
# entities are single words (no determiner), and exactly one preposition.


def _declared_as(graph: Graph, kind: str) -> set[str]:
    """The words declared `W is a <kind>` (i.e. `W --is_a--> kind`). The shared reader behind
    declared_relations/verbs/prepositions — only DECLARED words drive form generation, so the
    lexicon is graph DATA, never a hardcoded list (the engine/grammar stays content-blind)."""
    out: set[str] = set()
    for r in graph.nodes():
        if not graph.has_key(r, "is_a"):
            continue
        subj = next((n for n in graph.into(r) if not graph.is_inert(n)), None)
        obj = next(iter(graph.out(r)), None)
        if subj is not None and obj is not None and graph.name(obj) == kind:
            out.add(graph.name(subj))
    out.discard(kind)
    return out


def declared_verbs(graph: Graph) -> set[str]:
    """Verbs declared n-ary via `V is a verb`. Disjoint from `declared_relations`
    (`is_a relation`) and `declared_prepositions` (`is_a preposition`)."""
    return _declared_as(graph, "verb")


def declared_prepositions(graph: Graph) -> set[str]:
    """Prepositions declared via `P is a preposition` — the role markers for n-ary events.
    Declared in CNL (not a frozen Python list), so n-ary roles are fully data-driven."""
    return _declared_as(graph, "preposition")


def nary_forms(graph: Graph) -> list[Rule]:
    """A reification form per declared verb x declared preposition (a §8 tool, like
    `relation_forms`).

    `SUBJ V OBJ P ARG` -> a fresh `event` node with `pred`=V and role edges `subj`/`obj`/`P`.
    Controlled by the `V is a verb` + `P is a preposition` declarations; keyed on the literal
    verb `V?` and preposition `P?` so only a declared ditransitive parses. The non-matching
    prepositions simply never fire (the sentence has only one)."""
    forms: list[Rule] = []
    preps = sorted(declared_prepositions(graph))
    for v in sorted(declared_verbs(graph)):
        for p in preps:
            forms.append(Rule(
                key=f"form.nary.{v}.{p}",
                lhs=[Pat("?s", "first", "?subj"), Pat("?subj", "next", f"{v}?"),
                     Pat(f"{v}?", "next", "?obj"), Pat("?obj", "next", f"{p}?"),
                     Pat(f"{p}?", "next", "?arg")],
                rhs=[Pat("event?", "pred", v), Pat("event?", "subj", "?subj"),
                     Pat("event?", "obj", "?obj"), Pat("event?", p, "?arg")],
            ))
    return forms


# The wh-marker that fills the QUERIED role of an n-ary question (see nary_question_forms).
WH = "<wh>"


def nary_question_forms(graph: Graph) -> list[Rule]:
    """Question forms for the n-ary events of each declared verb (a §8 tool, query side).

    A question is the DECLARATIVE n-ary surface with a wh-word in exactly the queried role:
        who gives book to bob     -> subj unknown
        alice gives what to bob   -> obj unknown
        alice gives book to who   -> prep-role unknown
    Each reifies into a `<qevent>` pattern (mirroring the `event` a declarative makes) with the
    `<wh>` marker in the unknown slot; the known slots carry their values. `query.ask` turns
    that pattern into a joined multi-`Pat` match over the KB's events. `who` marks subj/prep
    slots, `what` the direct object (the natural person/thing split); single wh per question."""
    forms: list[Rule] = []
    preps = sorted(declared_prepositions(graph))
    for v in sorted(declared_verbs(graph)):
        for p in preps:
            base = f"ask.nary.{v}.{p}"
            forms += [
                Rule(  # subj unknown:  who V OBJ P ARG
                    key=f"{base}.subj",
                    lhs=[Pat("?s", "first", "who?"), Pat("who?", "next", f"{v}?"),
                         Pat(f"{v}?", "next", "?obj"), Pat("?obj", "next", f"{p}?"),
                         Pat(f"{p}?", "next", "?arg")],
                    rhs=[Pat("<qevent>?", "pred", v), Pat("<qevent>?", "subj", WH),
                         Pat("<qevent>?", "obj", "?obj"), Pat("<qevent>?", p, "?arg")],
                ),
                Rule(  # obj unknown:  SUBJ V what P ARG
                    key=f"{base}.obj",
                    lhs=[Pat("?s", "first", "?subj"), Pat("?subj", "next", f"{v}?"),
                         Pat(f"{v}?", "next", "what?"), Pat("what?", "next", f"{p}?"),
                         Pat(f"{p}?", "next", "?arg")],
                    rhs=[Pat("<qevent>?", "pred", v), Pat("<qevent>?", "subj", "?subj"),
                         Pat("<qevent>?", "obj", WH), Pat("<qevent>?", p, "?arg")],
                ),
                Rule(  # prep-role unknown:  SUBJ V OBJ P who
                    key=f"{base}.{p}",
                    lhs=[Pat("?s", "first", "?subj"), Pat("?subj", "next", f"{v}?"),
                         Pat(f"{v}?", "next", "?obj"), Pat("?obj", "next", f"{p}?"),
                         Pat(f"{p}?", "next", "who?")],
                    rhs=[Pat("<qevent>?", "pred", v), Pat("<qevent>?", "subj", "?subj"),
                         Pat("<qevent>?", "obj", "?obj"), Pat("<qevent>?", p, WH)],
                ),
            ]
    return forms
