"""
Authoring a whole domain in CNL — facts AND rules, no Python domain logic.

This module is the bridge that lets a demo like the ice-cream shop live entirely
in a `.cnl` file (see `corpus/icecream.cnl`). It adds three things on top of the
core grammar in `forms.py`, all following the established two-phase pattern of
`expand_relation_properties` (vision §3/§7/§8):

1. **Fact forms + graded rules** — the SCENARIO in CNL.
   `FACT_FORMS` recognize `X wants Y` and the copula `X is Y` (stock status and the
   gradable-attribute vocabulary). Gradedness is DATA: a line `urgent is gradable`
   declares `urgent` a gradable dimension. `GRADED_RULES` is then a single generic
   rule (per degree adverb) that fires for ANY declared-gradable word: matching the
   surface `X is very ADJ` together with `ADJ is gradable`, it SETS `X.embedding[ADJ]`
   via the rule's declarative `propagate` effect (vision §13) — no bolt-on tool, no
   seam. Writing an embedding is a rule effect exactly as reading one (graded
   conditions) is.

2. **Native rule forms + `expand_rules`** — the RULES in CNL (Stage 2).

3. **Translation forms + a lexicon** — a *looser* rule phrasing rewritten into the
   native form by ordinary normalization rules (Stage 3).

The dimension name is the adjective word itself (`urgent`), so a fact (`alice is
very urgent`) and a rule condition (`?c is very urgent`) speak the same vocabulary.
"""
from __future__ import annotations

import warnings
import zlib

from .forms import (
    FORM_RULES, _predicate_literals, declared_auxiliaries, declared_prepositions,
    declared_relations, declared_rule_variables, declared_univ_nouns, load_text, normalize_lexical,
    propagate_embeddings, relation_predicates, rule_var_name, tokenize, wire_same_as,
)
from .universal import same_as_rules
from ..vocabulary import SUBSTRATE_COREF_PREDS, CLOSES, CWA
from ..production_rule import (
    GradedCondition, Pat, Rule, is_var as _is_var, literal_name,
)
from ..lowering import run_bank
from ..world_model import Graph


# ---------------------------------------------------------------------------
# Stage 1 — fact forms (the scenario as CNL)
# ---------------------------------------------------------------------------

FACT_FORMS: list[Rule] = [
    # "X wants Y"  ->  X wants Y
    Rule(
        key="form.fact.wants",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "wants?"), Pat("wants?", "next", "?y")],
        rhs=[Pat("?x", "wants", "?y")],
    ),
    # "X is Y"  ->  X is Y   (copula; covers "vanilla is in_stock" AND "urgent is gradable")
    # NAC: Y must be the LAST token. "is a Y", "is very ADJ", "is not ADJ" all leave
    # a successor after the keyword, so this single guard excludes every variant.
    Rule(
        key="form.fact.is_state",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "?y")],
        nac=[Pat("?y", "next", "?z")],
        rhs=[Pat("?x", "is", "?y")],
    ),
    # "X in Y"  ->  X in Y   (explicit placement, e.g. "bob in shop2"). This is the
    # defeating evidence for the defeasible context default (the `?c not in ?other`
    # NAC below). NAC: Y must be the LAST token, so a rule HEAD "?c in ?shop when ..."
    # (whose ?shop is followed by `when`) self-excludes, exactly like form.fact.is_state.
    Rule(
        key="form.fact.in",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "in?"), Pat("in?", "next", "?y")],
        nac=[Pat("?y", "next", "?z")],
        rhs=[Pat("?x", "in", "?y")],
    ),
    # "X is one thing"  ->  X is_unique <yes>   (EXPLICIT SINGLE IDENTITY).
    # Under the pure-§3 model (decision_quantification_coreference) a bare repeated mention is
    # a DISTINCT witness, so `ice is a solid` + `ice is a liquid` is two ices, NOT a
    # contradiction. This declaration overrides that default for one name: it asserts that all
    # mentions of X denote ONE individual, so the Session force-coreferences them (kept even
    # when contradictory — the user stated one identity, so an inconsistency is a REAL
    # contradiction to report, not a signal to split). It needs NO new keyword machinery: the
    # two-word object `one thing` means the copula `X is Y` (which fires only when Y is the
    # LAST token) self-excludes, so this is a purely additive, linter-clean form.
    Rule(
        key="form.fact.unique",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "one?"),
             Pat("one?", "next", "thing?")],
        rhs=[Pat("?x", "is_unique", "<yes>")],
    ),
    # "X is the same as Y"  ->  X is_unique <yes>, Y is_unique <yes>, X same_as Y
    # (EXPLICIT CROSS-NAME COREFERENCE — the dual of `X is one thing`). It declares that two
    # DIFFERENT names denote the SAME individual. The desugaring reuses the single-identity
    # machinery: each name becomes a single identity (so its own mentions force-coref together)
    # and an asserted `same_as` BRIDGES the two — `_derive`'s `same_as` propagation then composes
    # facts stated under either name across the whole connected class, and the detection pass
    # catches any incompatibility the identification introduces. Disjoint from the copula (`is`
    # is followed by `the same as Y`, not a last-token object) and from `X is one thing` (`is`
    # is followed by `the`, not `one`), so it is again purely additive + linter-clean.
    Rule(
        key="form.fact.same_as",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "the?"),
             Pat("the?", "next", "same?"), Pat("same?", "next", "as?"),
             Pat("as?", "next", "?y")],
        rhs=[Pat("?x", "is_unique", "<yes>"), Pat("?y", "is_unique", "<yes>"),
             Pat("?x", "same_as", "?y")],
    ),
    # "X is closed world"  ->  X closes <closed_world>   (the per-predicate CWA DECLARATION,
    # authored in CNL — decision_forcing_a_decision / handoff step 1). It records that property X
    # is CLOSED-WORLD, so `decide.complete` may license `is_not X`, and the CNL reflection
    # (`expand_rules`) upgrades a rule's `is not X` clause from a NAC into a decided negation. The
    # two-word object `closed world` self-excludes the copula (`form.fact.is_state` fires only when
    # the object is the LAST token) — the same additive, linter-clean idiom as `X is one thing`.
    Rule(
        key="form.fact.closed_world",
        lhs=[Pat("?s", "first", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "closed?"),
             Pat("closed?", "next", "world?")],
        rhs=[Pat("?x", CLOSES, CWA)],
    ),
]


# ---------------------------------------------------------------------------
# The degree scale is KB DATA, not engine config (vision §13).
# ---------------------------------------------------------------------------
#
# The adverb->degree mapping (very=0.8, ...) is KNOWLEDGE — how strong "very" is — so it
# lives in the KB as CNL facts (`very is 0.8`), NOT a Python dict the rule layer indexes.
# `degree_thresholds` reads them back; the write rule, the rule-grammar graded-condition
# forms, and the α-cut thresholds are all GENERATED from the declared degrees (a §8 tool,
# exactly like declared relations/verbs/prepositions). DEGREE_CNL is the default lexicon,
# expressed as data and seeded into a KB; a user can add or override (`extremely is 0.95`),
# and the engine stays content-blind — it only ever compares the threshold a rule carries.
DEGREE_CNL = "very is 0.8\nsomewhat is 0.5\nslightly is 0.3\n"


def degree_thresholds(graph: Graph) -> dict[str, float]:
    """Degree adverbs declared `A is <number>` (number in (0, 1]) -> their α-cut/degree.

    Reads the graded scale from the KB as DATA. A copula fact `very is 0.8` whose object name
    parses as a number in (0, 1] is a degree declaration; anything else is an ordinary fact."""
    out: dict[str, float] = {}
    for r in graph.nodes():
        if not graph.has_key(r, "is"):
            continue
        subj = next((n for n in graph.into(r) if not graph.is_inert(n)), None)
        obj = next(iter(graph.out(r)), None)
        if subj is None or obj is None:
            continue
        try:
            v = float(graph.name(obj))
        except ValueError:
            continue
        if 0.0 < v <= 1.0:
            out[graph.name(subj)] = v
    return out


_DEFAULT_DEGREE_GRAPH: Graph | None = None


def _default_degree_graph() -> Graph:
    """A cached graph holding the DEFAULT degree declarations (DEGREE_CNL) as facts."""
    global _DEFAULT_DEGREE_GRAPH
    if _DEFAULT_DEGREE_GRAPH is None:
        g = Graph()
        load_text(g, DEGREE_CNL)
        run_bank(g, FORM_RULES + FACT_FORMS)
        _DEFAULT_DEGREE_GRAPH = g
    return _DEFAULT_DEGREE_GRAPH


def _degrees(graph: Graph) -> dict[str, float]:
    """The degrees in scope: the defaults, overlaid with whatever `graph` declares. So the
    scale works on a graph that hasn't seeded the defaults, and a KB declaration extends it."""
    d = dict(degree_thresholds(_default_degree_graph()))
    d.update(degree_thresholds(graph))
    return d


def _graded_rule(adverb: str, value: float) -> Rule:
    """The generic 'gradable attribute -> embedding' rule, for one degree adverb.

    Fires for ANY word declared gradable (the CNL vocabulary): given the surface
    `?x is <adverb> ?adj` and the canonical `?adj is gradable`, it SETS
    `?x.embedding[?adj] = value` via `propagate`. The `value` is the declared degree (KB
    data), not a hardcoded constant — domain-independent, and the scale lives in the graph."""
    return Rule(
        key=f"grade.{adverb}",
        lhs=[Pat("?adj", "is", "gradable"),
             Pat("?x", "next", "is?"), Pat("is?", "next", f"{adverb}?"),
             Pat(f"{adverb}?", "next", "?adj")],
        rhs=[],                                     # the only effect is the embedding write
        propagate={"op": "set", "var": "?x", "dim": "?adj", "value": value},
    )


def graded_rules(graph: Graph) -> list[Rule]:
    """One embedding-write rule per degree adverb declared in (or defaulted for) `graph`
    (a §8 tool, like `relation_forms`). The degree VALUES come from the KB, not config."""
    return [_graded_rule(a, v) for a, v in sorted(_degrees(graph).items())]


# The default write rules (over the default degree lexicon) — for back-compat and the batch
# loaders; the live Session uses `graded_rules(self.kb)` so KB-declared degrees apply.
GRADED_RULES: list[Rule] = graded_rules(Graph())


# Content predicates whose facts must COMPOSE across `same_as` coreference. Phase 2.5 removes the old
# hardcoded DOMAIN string list (`wants`/`in`/`has`/`before`/… — the leak). The set is now derived,
# content-blind, from three sources: the fixed SUBSTRATE primitives (`vocabulary.SUBSTRATE_COREF_PREDS`
# — copula/subsumption/congruence, composing in EVERY KB), every relation PREDICATE actually present
# in the graph (`relation_predicates` — the faithful additive-coref analog: the destructive merge
# shared ALL of a mention's relations, so coref must too), and the KB's declared relations/prepositions
# (for a predicate declared but not yet materialized). No domain vocabulary is named in the engine.
def _coref_propagation(graph: Graph) -> list[Rule]:
    """`same_as` propagation rules over the content predicates present, so facts on one mention
    reach its coreferent siblings (what the destructive `canonicalize` merge gave for free)."""
    preds = (SUBSTRATE_COREF_PREDS | set(relation_predicates(graph))
             | declared_relations(graph) | declared_prepositions(graph))
    return same_as_rules(sorted(preds))


def _recognize(graph: Graph, sentences: list[str], forms: list[Rule]) -> list[str]:
    """Tokenize `sentences` into `graph` and recognize them on the ISA FORWARD driver `run_bank`.

    This routes recognition OFF the forward `rewriter` onto the ISA forward Machine (`isa.lowering.
    run_bank` — the reference opcode `Machine` + a dumb `Rule`->program lowering, driven to fixpoint)
    — the "one engine" move (decision-attrgraph-rehost, recognition on the ISA). `run_bank` is a
    forward, seed-and-walk matcher like `rewriter` (SEED a rel by name, FOLLOW bare edges), so it
    recognizes WHOLE-BATCH and reproduces `rewriter.run` EXACTLY on `_ALL_FORMS` (differential-tested:
    real facts AND recognized rules identical) — no per-sentence isolation needed (that was a
    workaround for a since-retired backward demand-all-heads driver, which over-recognized globally).
    NAC guards are handled as the driver's match-time filter, keeping the opcode set purely positive.

    Bare-`yes` recognition tags (`is_kw`/`kw_not`/`is_bnd`/…) are stripped after: they are ephemeral
    NAC-guard scaffolding consumed DURING recognition (real yes-facts use the inert `<yes>`), so they
    must not persist — and `run_bank` MINTs a FRESH `yes` per firing (label-less: two same-named nodes
    are two), which `wire_same_as` would otherwise coref-link spuriously. Returns the anchor ids."""
    anchors = [tokenize(graph, s) for s in sentences]
    run_bank(graph, forms)
    for r in list(graph.nodes_named("yes")):         # ephemeral NAC-guard scaffolding, not a fact
        graph.remove_node(r)
    graph.gc_disconnected()
    return anchors


def load_facts(graph: Graph, text: str) -> list[str]:
    """Load CNL facts into `graph`: recognize -> additive coref -> graded rules.

    Recognition runs on the ISA forward driver (`_recognize` -> `run_bank`) — the "one engine" move
    (decision-attrgraph-rehost); the whole-batch forward pass, not a backward solve.
    Coreference is the ADDITIVE `same_as` wiring (vision §3), NOT the destructive `canonicalize`
    node-merge (a fact-edge deletion, retired for §5). Same-named mentions are LINKED, then
    `same_as` propagation composes their facts — so a gradable declaration (`urgent is gradable`)
    reaches the surface `urgent` token of its use (`alice is very urgent`) before the graded rule
    fires, and `propagate_embeddings` spreads the resulting degree to every coreferent mention.
    Returns the sentence-anchor ids. The scenario half of a CNL demo.
    """
    rules = FORM_RULES + FACT_FORMS
    anchors = _recognize(graph, [ln for ln in text.splitlines() if ln.strip()], rules)
    wire_same_as(graph, rules)                       # additive coref (was: canonicalize merge)
    run_bank(graph, _coref_propagation(graph))       # compose facts across the same_as links (ISA)
    run_bank(graph, graded_rules(graph))  # gradable word -> embedding (propagate EMIT); degrees from KB
    propagate_embeddings(graph)                      # spread degrees to coreferent mentions
    return anchors


# ---------------------------------------------------------------------------
# Stage 2 — native rule CNL, folded into rule structure by in-graph forms
# ---------------------------------------------------------------------------
#
# A native rule line is:   HEAD  when  COND and COND and ...
#   HEAD  = `S P O`        (the consequent, one triple)
#   COND  = `S P O`        (any positive relation)    e.g. `?c wants ?f`, `?x visits dog`
#         | `not S P O`    (a NAC)                    e.g. via the shared `not`-clause
#         | `S is a O`     (is_a sugar)               e.g. `?c is a customer`
#         | `S is not O`   (is-negation sugar)        e.g. `?c is not urgent`
#         | `S is <adv> O` (graded sugar)             e.g. `?c is very urgent`
#         | `S not in O`   (context-default sugar)    e.g. `?c not in ?other`
# The condition body is the SHARED spine (`BODY_SPINE_FORMS`), the SAME grammar the
# machine surface uses (`machine_rules.py`) — there is NO fixed condition menu: a bare
# `S P O` folds for ANY predicate. The copula variants above are prose SUGAR on top,
# handling the multi-token forms the generic triple can't express. This is the grammar
# unification (handoff 1a proper-fix): prose and machine rules share one condition grammar,
# differing only in the HEAD (prose = a single triple before `when`; machine = a clause
# conjunction with `drop`). Variables are `?x` and tokenize straight into `?x` nodes.
#
# The folding is pure graph rewriting: forms accrete a canonical rule fragment on the token
# chain, then `expand_rules` (a §8 tool) reflects each fragment into an executable `Rule`.
# The fragment meta-relations (all rule-source-only):
#   <rule> --rl_subj/rl_pred/rl_obj--> head tokens     (the prose consequent triple)
#   <rule> --rl_lhs/rl_nac/rl_graded--> <cond>         (one per body condition)
#   <cond> --k_subj/k_pred/k_obj[/k_adv]--> tokens     (the condition triple)
#   ?tok --body_subj/body_end--> <rule>                (the clause-flow domino markers)
# Rule-source is NOT canonicalized: a rule's repeated `?c` tokens must stay the variable
# `?c` (joined by name inside the Rule), never merged across rules.

def _is_kw_tag(kw: str) -> Rule:
    """Tag every token named `kw` with `is_kw yes`, so the GENERIC body clause NACs it and defers
    to the sugar forms (`is a`, `is not`, `is <adverb>`, `not in`). Fires at step 1 (needs only a
    token's predecessor), long before the clause-flow domino reaches it — so the NAC is never raced
    (same guarantee the machine grammar relies on for `kw_not`/`kw_drop`)."""
    return Rule(key=f"rule.kw.{kw}", lhs=[Pat("?x", "next", f"{kw}?")],
                rhs=[Pat(f"{kw}?", "is_kw", "yes")])


# ---------------------------------------------------------------------------
# The SHARED body / condition grammar — one spine for prose AND machine rules.
# ---------------------------------------------------------------------------
#
# handoff 1a proper-fix (grammar unification): a rule BODY is folded by these forms, used by BOTH
# the prose grammar (RULE_FORMS below) and the machine grammar (machine_rules.py) — there is NO
# fixed condition menu. A body clause is a bare triple `S P O` (ANY predicate) or a `not S P O`
# NAC; an `and` domino walks a `body_subj`/`body_end` marker down the chain. Only the HEAD differs
# between the two surfaces (prose: a single `S P O` before `when`; machine: a `and`-conjunction of
# clauses with `drop`), so only the head is grammar-specific. `k_pred` is the clause's own
# predicate TOKEN (a rule-source token, never a fact node — the prose/machine parsers run in a
# PRIVATE, un-canonicalized graph; the Session is un-canonicalized too, so b1 holds).

def _body_kw_tags(kw: str, tag: str) -> list[Rule]:
    """Tag `kw` tokens with `tag` from BOTH `next` and `first` (a rule may START with the kw, e.g.
    machine's `drop ... when ...`) — set at step 1 so the clause forms' NAC on the tag is unraced."""
    return [Rule(key=f"body.kw.{kw}.next", lhs=[Pat("?t", "next", f"{kw}?")],
                 rhs=[Pat(f"{kw}?", tag, "yes")]),
            Rule(key=f"body.kw.{kw}.first", lhs=[Pat("?s", "first", f"{kw}?")],
                 rhs=[Pat(f"{kw}?", tag, "yes")])]


# A plain positive condition `S P O`. Defers (NAC) to a `not`-led clause (kw_not) and to the prose
# sugar (is_kw on the predicate or object — inert in the machine grammar, which emits no is_kw tag).
_GENERIC_BODY_CLAUSE = Rule(
    key="body.clause.rl_lhs",
    lhs=[Pat("?cs", "body_subj", "?r"), Pat("?cs", "next", "?cp"), Pat("?cp", "next", "?co")],
    nac=[Pat("?cs", "kw_not", "yes"), Pat("?cp", "is_kw", "yes"), Pat("?co", "is_kw", "yes"),
         Pat("?cp", "is_bnd", "yes")],   # a boundary kw (then/when/and) is never a clause predicate
    rhs=[Pat("?r", "rl_lhs", "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
         Pat("<cond>?", "k_pred", "?cp"), Pat("<cond>?", "k_obj", "?co"), Pat("?co", "body_end", "?r")],
)

# A `not S P O` negative condition / NAC (the marker sits on the `not` token).
_BODY_NOT_CLAUSE = Rule(
    key="body.clause.not.rl_nac",
    lhs=[Pat("?d", "body_subj", "?r"), Pat("?d", "kw_not", "yes"),
         Pat("?d", "next", "?cs"), Pat("?cs", "next", "?cp"), Pat("?cp", "next", "?co")],
    nac=[Pat("?cp", "is_bnd", "yes")],   # `not <mod> then …` is an elliptical NAC, not `mod then …`
    rhs=[Pat("?r", "rl_nac", "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
         Pat("<cond>?", "k_pred", "?cp"), Pat("<cond>?", "k_obj", "?co"), Pat("?co", "body_end", "?r")],
)

# `and` continues the body: the previous clause's end token seeds the next clause's subject.
_BODY_AND = Rule(
    key="body.and",
    lhs=[Pat("?co", "body_end", "?r"), Pat("?co", "next", "and?"), Pat("and?", "next", "?ns")],
    rhs=[Pat("?ns", "body_subj", "?r")],
)


# ---- elliptical copula conjunction — `?x is round and big`, `?x is young and not rough` ----
#
# A SHARED-SUBJECT ellipsis: `and <mod>` / `and not <mod>` after a COPULA clause `?cs is ?co`
# reuses that clause's subject AND its `is`, folding `?cs is <mod>` (a positive rl_lhs) or a NAC on
# `?cs is <mod>` (rl_nac). The full `S P O` conjunct (`... and they are calm`) already works via
# `_BODY_AND` + the generic clause; this is the ONE-token elliptical modifier the generic clause
# can't fold on its own. `_BODY_AND` still marks the modifier `body_subj` (a harmless dangling
# marker: the generic clause never fires on a lone token, so it folds nothing).
#
# Disambiguation (elliptical modifier vs the subject of a full new clause) is content-blind: an
# elliptical modifier is a bare token that CLOSES the clause — it is either the last token (`end`)
# or immediately followed by a BOUNDARY keyword `then`/`when`/`and` (`bnd`, tagged `is_bnd`). A
# token followed by a non-boundary word is a subject `S` with its own `P O`, so neither variant
# fires and the generic-clause path handles it. The reused copula is pinned to `is` (`?prev k_pred
# is?`), so an elliptical only chains off a plain copula clause (not `is a` / `is <adverb>` / a NAC).
# Marking the modifier `body_end` lets the head grammar (`rule.if.then`) and a further `and`
# (chaining `round and big and small`) continue seamlessly past it.
_BND_TAGS: list[Rule] = [*_body_kw_tags("then", "is_bnd"),
                         *_body_kw_tags("when", "is_bnd"), *_body_kw_tags("and", "is_bnd")]


def _ellipsis_cond(key: str, *, negated: bool, terminal: str) -> Rule:
    # The prior clause is found by its object (= the `body_end` token, unique per position); its
    # role is not pinned, so an ellipsis chains off a positive OR a NAC conjunct (`not rough and not
    # sad`). `?r` comes from the `body_end` marker. `?prev k_pred is?` restricts to a plain copula.
    prev = [Pat("?co", "body_end", "?r"), Pat("?prev", "k_obj", "?co"),
            Pat("?prev", "k_subj", "?cs"), Pat("?prev", "k_pred", "is?"),
            Pat("?co", "next", "and?")]
    if negated:
        prev += [Pat("and?", "next", "not?"), Pat("not?", "next", "?mod")]
    else:
        prev += [Pat("and?", "next", "?mod")]
    nac: list[Pat] = []
    if terminal == "end":
        nac = [Pat("?mod", "next", "?z")]              # modifier is the last token
    else:                                              # terminal == "bnd"
        prev += [Pat("?mod", "next", "?b"), Pat("?b", "is_bnd", "yes")]   # ... then a boundary kw
    role = "rl_nac" if negated else "rl_lhs"
    rhs = [Pat("?r", role, "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
           Pat("<cond>?", "k_pred", "is?"), Pat("<cond>?", "k_obj", "?mod"),
           Pat("?mod", "body_end", "?r")]
    return Rule(key=key, lhs=prev, rhs=rhs, nac=nac)


_ELLIPSIS_FORMS: list[Rule] = [
    _ellipsis_cond("body.and.ellipsis", negated=False, terminal="end"),
    _ellipsis_cond("body.and.ellipsis.bnd", negated=False, terminal="bnd"),
    _ellipsis_cond("body.and.ellipsis.not", negated=True, terminal="end"),
    _ellipsis_cond("body.and.ellipsis.not.bnd", negated=True, terminal="bnd"),
]

# The shared body spine. machine_rules.py imports this and appends it to its own HEAD forms.
BODY_SPINE_FORMS: list[Rule] = [*_body_kw_tags("not", "kw_not"),
                                _GENERIC_BODY_CLAUSE, _BODY_NOT_CLAUSE, _BODY_AND,
                                *_BND_TAGS, *_ELLIPSIS_FORMS]


# ---- prose copula SUGAR — the multi-token variants the generic triple can't say ----

def _sugar_cond(key: str, mid: str, role: str, k_pred: str | None) -> Rule:
    """`?cs is <mid> ?o` (mid = the bound-literal `a?` / `not?` / `<adverb>?`) -> a condition folded
    under `role`, marking `?o` `body_end` so the `and` domino continues past all four tokens. is_a /
    is_not carry a bound-literal `k_pred` (a fresh rule-scope predicate node); a graded condition
    carries `k_adv` (the adverb, read by `expand_rules` into a GradedCondition threshold)."""
    rhs = [Pat("?r", role, "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
           Pat("<cond>?", "k_obj", "?o"), Pat("?o", "body_end", "?r")]
    rhs.append(Pat("<cond>?", "k_pred", k_pred) if k_pred else Pat("<cond>?", "k_adv", mid))
    return Rule(key=key,
                lhs=[Pat("?cs", "body_subj", "?r"), Pat("?cs", "next", "is?"),
                     Pat("is?", "next", mid), Pat(mid, "next", "?o")],
                rhs=rhs)


def _graded_cond_form(adverb: str) -> Rule:
    """`?cs is <adverb> ?o` -> a graded condition on the rule, per declared/default degree adverb."""
    return _sugar_cond(f"rule.cond.{adverb}", f"{adverb}?", "rl_graded", None)


# `?cs is a O` -> is_a; `?cs is not O` -> NAC on `is`.
_SUGAR_IS_A = _sugar_cond("rule.cond.is_a", "a?", "rl_lhs", "is_a?")
_SUGAR_IS_NOT = _sugar_cond("rule.cond.is_not", "not?", "rl_nac", "is?")
# `?cs not in O` -> NAC context (the defeasible-default idiom; `form.fact.in` defeats it). Disjoint
# from the generic `not`-led clause: the generic clause NACs `?cp is_kw`, and `not` is is_kw-tagged.
_SUGAR_NOT_IN = Rule(
    key="rule.cond.not_in",
    lhs=[Pat("?cs", "body_subj", "?r"), Pat("?cs", "next", "not?"),
         Pat("not?", "next", "in?"), Pat("in?", "next", "?o")],
    rhs=[Pat("?r", "rl_nac", "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
         Pat("<cond>?", "k_pred", "in?"), Pat("<cond>?", "k_obj", "?o"), Pat("?o", "body_end", "?r")],
)


# VERB negation: `?cs <aux> not ?v ?o` (aux = does/do/did) -> a NAC on the RELATION `?cs ?v ?o`.
# The verb-negation counterpart of the copula `is not` sugar: `the cat does not like the cow` /
# `they do not eat the cow` -> block when `?cs ?v ?o` holds. The auxiliary do-support is English
# scaffolding (no meaning), consumed by the form. `?v` is a bound VARIABLE position so any relation
# works. The aux set is DATA (`declared_auxiliaries` = DEFAULT_AUX + declared); each aux is
# `is_kw`-tagged so the generic clause defers, and gets the negation sugar (generated, like degrees).


def _verb_not_sugar(aux: str) -> Rule:
    return Rule(
        key=f"rule.cond.{aux}_not",
        lhs=[Pat("?cs", "body_subj", "?r"), Pat("?cs", "next", f"{aux}?"),
             Pat(f"{aux}?", "next", "not?"), Pat("not?", "next", "?v"), Pat("?v", "next", "?o")],
        rhs=[Pat("?r", "rl_nac", "<cond>?"), Pat("<cond>?", "k_subj", "?cs"),
             Pat("<cond>?", "k_pred", "?v"), Pat("<cond>?", "k_obj", "?o"), Pat("?o", "body_end", "?r")],
    )


def verb_neg_forms(graph: Graph) -> list[Rule]:
    """The verb-negation forms per `declared_auxiliaries(graph)` (a §8 tool, like
    `degree_grammar_forms`): an `is_kw` tag (so the generic clause defers) + the `<aux> not V O`
    NAC sugar, per auxiliary. DEFAULT_AUX + any user-declared `X is an auxiliary`."""
    aux = sorted(declared_auxiliaries(graph))
    return [_is_kw_tag(a) for a in aux] + [_verb_not_sugar(a) for a in aux]


def degree_grammar_forms(graph: Graph) -> list[Rule]:
    """The rule-grammar forms for the degree adverbs declared in (or defaulted for) `graph` (a §8
    tool): an `is_kw` tag (so the generic body clause defers to the graded sugar) plus the graded
    condition `?cs is <adverb> ?o`, per adverb. Generated from KB data, so a newly declared adverb
    (`extremely is 0.95`) parses in rule bodies with no code change."""
    advs = sorted(_degrees(graph))
    return [_is_kw_tag(a) for a in advs] + [_graded_cond_form(a) for a in advs]


RULE_FORMS: list[Rule] = [
    # The prose head: `S P O when ...` -> a fresh <rule> carrying the single consequent triple
    # (rl_subj/rl_pred/rl_obj — a stable `rule.S.P.O` key + the frame/loose machinery), and SEED the
    # shared body spine by marking the token after `when` as the first `body_subj`.
    Rule(
        key="rule.head",
        lhs=[Pat("?s", "first", "?hs"), Pat("?hs", "next", "?hp"),
             Pat("?hp", "next", "?ho"), Pat("?ho", "next", "when?"), Pat("when?", "next", "?bs")],
        rhs=[Pat("<rule>?", "rl_subj", "?hs"), Pat("<rule>?", "rl_pred", "?hp"),
             Pat("<rule>?", "rl_obj", "?ho"), Pat("?bs", "body_subj", "<rule>?")],
    ),
    # The shared body/condition grammar (generic `S P O`, `not S P O`, `and` domino) — the SAME
    # forms the machine grammar uses; NO fixed condition menu (any relation folds).
    *BODY_SPINE_FORMS,
    # Structural is_kw tags (a/not) so the generic clause defers to the copula sugar below.
    _is_kw_tag("a"), _is_kw_tag("not"),
    # Prose copula sugar + verb negation (`does not V O`) + the DEFAULT graded conditions. A live
    # Session also adds `verb_neg_forms(self.kb)` / `degree_grammar_forms(self.kb)` so KB-declared
    # auxiliaries/adverbs parse; the static banks below carry the DEFAULT auxiliaries + degrees.
    _SUGAR_IS_A, _SUGAR_IS_NOT, _SUGAR_NOT_IN,
    *verb_neg_forms(Graph()),
    *degree_grammar_forms(_default_degree_graph()),
]


# ---------------------------------------------------------------------------
# NL universal laws — `if BODY then HEAD` (universals->laws)
# ---------------------------------------------------------------------------
#
# A natural-language universal `if someone is rough then they are young` is the SAME rule
# structure the prose `S P O when ...` head builds — only the surface differs: the body leads
# (after `if`) and the head trails (after `then`). So these two forms REUSE the shared body spine
# (BODY_SPINE_FORMS) and the copula sugar, and fold the trailing head clause into the same
# rl_subj/rl_pred/rl_obj the `when` grammar uses. `expand_rules` then maps the quantifier/anaphor
# words to variables (`rule_var_name`), so `someone` and `they` unify to `?x` with NO coreference —
# the decision_quantification_coreference point that a universal binds all witnesses by NAME.
#
# Scope (first slice): COPULA laws — a single trailing head triple `S P O` where the clauses are
# copula (`is [not] O`); the body is the shared spine (one clause, or non-elliptical `S is A and S
# is B`). `are`->`is` is normalized by `normalize_lexical` first. NOT yet: n-ary VERB clauses
# (`the lion eats the dog`) — an undeclared verb is indistinguishable from a multi-word NP, so a
# determiner+verb clause mis-decomposes (the same n-ary/relational gap as facts); and elliptical
# conjunction (`is round and big`, a shared subject/copula). The `then` of a rule is kept distinct
# from `form.then` sequencing by the `if_ctx` NAC (forms.py).
IF_THEN_FORMS: list[Rule] = [
    # `if <body-subject> ...` — mint the rule node and hand its first token to the body spine.
    Rule(key="rule.if.start",
         lhs=[Pat("?s", "first", "if?"), Pat("if?", "next", "?bs")],
         rhs=[Pat("?bs", "body_subj", "<rule>?")]),
    # `... then S P O` — the trailing head triple folds onto the SAME rule (bound via the last
    # body clause's `body_end --> <rule>`), exactly like the prose `when` head. NAC: nothing after
    # the object, so only a clause-final S P O head folds (a longer head is left unrecognized, not
    # mis-folded — a documented first-slice limit).
    Rule(key="rule.if.then",
         lhs=[Pat("?co", "body_end", "?r"), Pat("?co", "next", "then?"),
              Pat("then?", "next", "?hs"), Pat("?hs", "next", "?hp"), Pat("?hp", "next", "?ho")],
         nac=[Pat("?ho", "next", "?z")],
         rhs=[Pat("?r", "rl_subj", "?hs"), Pat("?r", "rl_pred", "?hp"), Pat("?r", "rl_obj", "?ho")]),
]


# ---------------------------------------------------------------------------
# Plural-noun universals — `Cold things are kind` (a second universal surface)
# ---------------------------------------------------------------------------
#
# `<Adj> <plural-noun> are <Pred>` (e.g. `Cold things are kind`, `Cold people are green`) is a
# universal law over an attribute: "all things that are Cold are Kind" -> `?x is Kind when ?x is
# Cold`. It reuses the same rule fragment + variable machinery as `IF_THEN_FORMS`: the plural noun
# is the bound variable (`forms.rule_var_name` maps `things`->`?y`, `people`->`?x`), the leading
# adjective is the single body condition, and the copula predicate (after `are`->`is`) is the head.
# FIRST SLICE: a SINGLE leading adjective + single predicate (the `?adj first` + `?pred` last-token
# NAC pin both). Multi-adjective (`All young, cold people are green`) and the `All`/comma surface are
# deferred — they stay unrecognized (never mis-folded), the same conservatism as elsewhere. The
# noun set is DATA: `declared_univ_nouns` = DEFAULT {things, people} + any declared variable word,
# so `Cold critters are kind` works once `critters is a variable` (like `relation_forms`).


def _plural_universal_form(noun: str) -> Rule:
    return Rule(
        key=f"rule.plural.{noun}",
        lhs=[Pat("?s", "first", "?adj"), Pat("?adj", "next", f"{noun}?"),
             Pat(f"{noun}?", "next", "is?"), Pat("is?", "next", "?pred")],
        nac=[Pat("?pred", "next", "?z")],       # single predicate (pred is the last token)
        rhs=[Pat("<rule>?", "rl_subj", f"{noun}?"), Pat("<rule>?", "rl_pred", "is?"),
             Pat("<rule>?", "rl_obj", "?pred"), Pat("<rule>?", "rl_lhs", "<cond>?"),
             Pat("<cond>?", "k_subj", f"{noun}?"), Pat("<cond>?", "k_pred", "is?"),
             Pat("<cond>?", "k_obj", "?adj")],
    )


def plural_universal_forms(graph: Graph) -> list[Rule]:
    """A plural-noun universal form per `declared_univ_nouns(graph)` (a §8 tool, like
    `relation_forms`): DEFAULT {things, people} + any declared variable word."""
    return [_plural_universal_form(n) for n in sorted(declared_univ_nouns(graph))]


# Default forms (over {things, people}) for the static banks; a live Session/loader also adds
# `plural_universal_forms(kb)` so declared variable-nouns parse (like `degree_grammar_forms`).
PLURAL_UNIVERSAL_FORMS: list[Rule] = plural_universal_forms(Graph())


# ---- expand_rules: reflect rule fragments into executable Rules (a §8 tool) -----

def _obj(graph: Graph, node: str, rel: str) -> str | None:
    for r, o in graph.relations_from(node):
        if graph.has_key(r, rel):
            return o
    return None


def _objs(graph: Graph, node: str, rel: str) -> list[str]:
    return [o for r, o in graph.relations_from(node) if graph.has_key(r, rel)]


def _cond_pat(graph: Graph, cond: str, declared: set[str] = frozenset()) -> Pat:
    # `rule_var_name` maps a quantifier/anaphor token (`someone`/`they` -> `?x`) or a domain-declared
    # variable word (`critters` -> `?critters`) to a bound variable — the universals->laws name-op (a
    # §8 calculator step, past the quote/eval wall). A literal entity (`lion`) is unchanged, so a
    # ground rule reflects with no variable.
    return Pat(rule_var_name(graph.name(_obj(graph, cond, "k_subj")), declared),
              rule_var_name(graph.name(_obj(graph, cond, "k_pred")), declared),
              rule_var_name(graph.name(_obj(graph, cond, "k_obj")), declared))


def _pat_key(p: Pat) -> tuple[str, str, str]:
    return p.tokens()


def _expand_rule_node(graph: Graph, R: str, declared: set[str] = frozenset()) -> Rule:
    """Reflect one folded rule fragment (rule node `R`) into an executable `Rule`.

    Two head encodings are accepted: the legacy single triple (`rl_subj`/`rl_pred`/`rl_obj`,
    from the prose grammar's one-triple `HEAD when ...`) and a CONJUNCTION of head conditions
    (`rl_head`, from the machine grammar's multi-triple head — G2). `rl_drop` conditions
    become the rule's control deletions (G3). Head clause order is irrelevant: `apply_rule`
    creates a fresh bound-literal node on first reference (subject or object), so a clause
    that references a fresh node before the clause that "introduces" it still shares it.
    `declared` are the domain-declared variable words (mapped to `?<word>` by `rule_var_name`)."""
    head_conds = _objs(graph, R, "rl_head")
    legacy_subj = _obj(graph, R, "rl_subj")
    if head_conds:
        rhs = sorted((_cond_pat(graph, k, declared) for k in head_conds), key=_pat_key)
    elif legacy_subj is not None:
        rhs = [Pat(rule_var_name(graph.name(legacy_subj), declared),
                   rule_var_name(graph.name(_obj(graph, R, "rl_pred")), declared),
                   rule_var_name(graph.name(_obj(graph, R, "rl_obj")), declared))]
    else:
        rhs = []                                 # a drop-only rule (empty create head)
    lhs_conds = _objs(graph, R, "rl_lhs")
    nac_conds = _objs(graph, R, "rl_nac")
    # Every `not P` body clause is a NAC — DEMAND-DRIVEN NEGATION (firmware v3): the chain decides it on
    # demand by negation-as-failure (nested negative demand -> positive closure -> absence decides). A
    # closed-world `is not P` is NO LONGER upgraded to a positive `is_not` match + a forward completion
    # rule (the retired `decide.solve` apparatus); the `cleared is closed world` marker is now vestigial
    # for reasoning — a NAC IS the closed-world reading, decided on demand. So there is one uniform NAC
    # path, whatever the CWA declaration says (open/closed is a QUERY-time concern via `open_preds`).
    lhs = sorted((_cond_pat(graph, k, declared) for k in lhs_conds), key=_pat_key)
    nac = sorted((_cond_pat(graph, k, declared) for k in nac_conds), key=_pat_key)
    drop = sorted((_cond_pat(graph, k, declared) for k in _objs(graph, R, "rl_drop")), key=_pat_key)
    degrees = _degrees(graph)
    graded = [
        GradedCondition(
            var=graph.name(_obj(graph, k, "k_subj")),
            embedding={graph.name(_obj(graph, k, "k_obj")): 1.0},
            threshold=degrees[graph.name(_obj(graph, k, "k_adv"))],
        )
        for k in _objs(graph, R, "rl_graded")
    ]
    prose = legacy_subj is not None and not head_conds
    return Rule(key=_rule_key(rhs, lhs, nac, drop, prose=prose),
                lhs=lhs, rhs=rhs, nac=nac, drop=drop, graded=graded)


def _rule_key(rhs: list[Pat], lhs: list[Pat], nac: list[Pat], drop: list[Pat],
              *, prose: bool) -> str:
    """A rule key. PROSE single-head rules keep the stable, human `rule.S.P.O` (the prose
    grammar's tests pin these). MACHINE rules append a deterministic digest of the whole
    pattern signature, because two machine rules may share a head triple (e.g. planning's
    `ground_state` and `reach_effect` both produce `?c reachable <yes>`) and would otherwise
    collide in the fired-set/stratifier. Drop-only rules (empty head) anchor on their drop."""
    anchor = rhs[0] if rhs else (drop[0] if drop else (lhs[0] if lhs else None))
    label = f"{anchor.s}.{anchor.p}.{anchor.o}" if anchor is not None else "empty"
    if prose:
        return f"rule.{label}"
    sig = "|".join(f"{role}:{p.s}/{p.p}/{p.o}"
                   for role, pats in (("h", rhs), ("l", lhs), ("n", nac), ("d", drop))
                   for p in sorted(pats, key=_pat_key))
    return f"rule.{label}.{zlib.crc32(sig.encode()) & 0xFFFFFF:06x}"


def _frame_body_tokens(graph: Graph) -> set[str]:
    """Head-subject tokens of lexicon frame bodies (their rule nodes are templates,
    not standalone rules — they must be skipped by `expand_rules`)."""
    return {o for n in graph.nodes() for r, o in graph.relations_from(n)
            if graph.has_key(r, "body")}


def expand_rules(rule_graph: Graph) -> list[Rule]:
    """Reflect every folded rule fragment in `rule_graph` into an executable `Rule`.

    A §8 calculator tool (cf. `rules_in_graph`): reads the meta-relations the forms
    accreted and emits `Rule`s — structural conditions as `Pat`s, `rl_graded` as
    `GradedCondition`s. Lexicon frame bodies are skipped (they are templates).

    DEMAND-DRIVEN NEGATION (firmware v3, the only model): every `not P` body clause reflects to a NAC
    (`_expand_rule_node`), decided ON DEMAND by the chain's negation-as-failure — NO closed-world
    upgrade, NO forward completion rule (the retired `decide.solve` apparatus). The CWA marker is
    vestigial for reasoning; a NAC IS the closed-world reading.
    """
    skip = _frame_body_tokens(rule_graph)
    declared = declared_rule_variables(rule_graph)   # domain variable words -> `?<word>`
    rule_nodes = [
        R for R in rule_graph.nodes()
        if (_objs(rule_graph, R, "rl_pred") or _objs(rule_graph, R, "rl_head")
            or _objs(rule_graph, R, "rl_drop"))
        and _obj(rule_graph, R, "rl_subj") not in skip
    ]
    rules = [_expand_rule_node(rule_graph, R, declared) for R in rule_nodes]
    return sorted(rules, key=lambda r: r.key)


def _dropped_conditions(graph: Graph, R: str) -> list[str]:
    """Body clauses of prose rule `R` that folded into NO condition (`<cond>`).

    With the unified generic clause, ANY `S P O` folds, so this now catches only a genuinely
    MALFORMED clause (wrong arity — a lone token, or trailing words a clause can't consume) —
    never a plain relation. Every clause subject carries `body_subj --> R`; a folded condition
    records `<cond> --k_subj--> ?cs`. A `not`-led clause carries `body_subj` on its `not` token
    (its `k_subj` is the inner subject), so keyword-led subjects (`kw_not`/`kw_drop`) are excluded.
    A `body_subj` token that is neither a folded `k_subj` nor a keyword lead led an unrecognized
    clause (handoff 1a: report, never silently drop). Returns each such clause's surface text.

    An elliptical modifier (`... and big`, `... and not sad`) is a `body_subj` token (marked by the
    inert `_BODY_AND` domino) that folded as a clause OBJECT, not subject — so folded `k_obj` tokens
    count as consumed too, or the modifier would be mis-reported as a dropped clause."""
    folded: set[str] = set()
    for role in ("rl_lhs", "rl_nac", "rl_graded"):
        for c in _objs(graph, R, role):
            for slot in ("k_subj", "k_obj"):
                tok = _obj(graph, c, slot)
                if tok is not None:
                    folded.add(tok)
    def _tagged(t: str, rel: str) -> bool:                # a `<tag> yes` marker (compare the NAME,
        o = _obj(graph, t, rel)                           # not the object id) — kw_not / kw_drop
        return o is not None and graph.name(o) == "yes"
    dropped: list[str] = []
    for t in graph.nodes():
        if (_obj(graph, t, "body_subj") == R and t not in folded
                and not _tagged(t, "kw_not") and not _tagged(t, "kw_drop")):
            dropped.append(_clause_text(graph, t))
    return dropped


def _clause_text(graph: Graph, cs: str) -> str:
    """Reconstruct a body clause's surface text: `cs` then `next` tokens, stopping before the next
    clause's subject (a `body_subj` token) or a separator (`and`/`when`) or the end of the chain."""
    toks: list[str] = []
    t: str | None = cs
    while t is not None:
        toks.append(graph.name(t))
        nxt = _obj(graph, t, "next")
        if (nxt is None or _obj(graph, nxt, "body_subj") is not None
                or graph.name(nxt) in ("and", "when")):
            break
        t = nxt
    return " ".join(toks)


def load_universal_rules(text: str) -> list[Rule]:
    """Parse NL universal-law CNL (`if BODY then HEAD`) into executable `Rule`s (universals->laws).

    The natural-language surface of a rule: `if someone is rough then they are young` ->
    `?x is young when ?x is rough`. Each line is lexically normalized (`are`->`is`), surface-
    normalized (determiners stripped), folded by the if/then head forms + the shared body spine,
    and reflected by `expand_rules`, which maps the quantifier/anaphor words to variables
    (`someone`/`they` -> `?x`, `something`/`it` -> `?y`) so a universal binds all witnesses by NAME.
    A literal-entity subject (`if the lion is angry then the lion is loud`) reflects with no variable.

    Runs in a private rule-source graph that is NOT canonicalized (a rule's variables must stay
    variables). Blank/`#` lines skipped. FIRST-SLICE limits (see IF_THEN_FORMS): copula clauses
    only — n-ary verb clauses (`the lion eats the dog`) mis-decompose (undeclared-verb gap) and are
    dropped; no elliptical conjunction (`is round and big`)."""
    from .forms import form_keywords, normalize_surface, surface_forms
    forms = RULE_FORMS + IF_THEN_FORMS + PLURAL_UNIVERSAL_FORMS
    strata = surface_forms(form_keywords(forms))
    rg = Graph()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        anchor = tokenize(rg, normalize_lexical(s))
        normalize_surface(rg, anchor, strata)
    run_bank(rg, forms)          # recognition on the ISA forward driver (Phase 0.2)
    return expand_rules(rg)


def load_rules(text: str, *, policy=None, lint: bool = True) -> list[Rule]:
    """Parse native rule CNL into executable `Rule`s (tokenize -> fold -> expand).

    Runs in a private rule-source graph that is NOT canonicalized (a rule's repeated `?c` must
    stay the variable `?c`, joined by name inside the Rule). The body grammar is the SHARED spine
    (`BODY_SPINE_FORMS`), so ANY relation condition (`?x visits dog`) folds — no fixed menu, no
    declaration needed (grammar unification, handoff 1a proper-fix). Prose copula sugar
    (`is a` / `is not` / `is <adverb>` / `not in`) sits on top.

    RAISES `ValueError` only if a body clause is genuinely MALFORMED (wrong arity — the generic
    clause could not fold it), naming the clause (handoff 1a: report, never silently drop)."""
    rg = Graph()
    load_text(rg, text)
    run_bank(rg, RULE_FORMS)     # recognition on the ISA forward driver (Phase 0.2)
    rules = expand_rules(rg)
    dropped = [c for R in rg.nodes() if _objs(rg, R, "rl_pred")
               for c in _dropped_conditions(rg, R)]
    if dropped:
        raise ValueError(
            "rule grammar could not fold these body clause(s): "
            + "; ".join(f"'{c}'" for c in dropped)
            + ". A body clause must be `S P O` (any relation), `not S P O`, or a copula "
            "form (`is a` / `is not` / `is <adverb>` / `not in`).")
    if lint and _on_cycle(policy) == "raise":          # firmware STANCE: reject a negation cycle at
        lint_stratifiable(rules, source="load_rules")  # load (default), or leave it for run_rules to
    return rules                                       # degrade (drop NAF rules) — see `policy.py`.
    # `lint=False` defers the check to the caller — the runtime-authoring path (`intake.ingest`) owns it
    # so a mid-session cycle becomes a CONVERSATION (accept-degrade / reject), not a raise (§6/Phase 8.6).


# ---- stratified execution: NAC over a derived fact must run in a later stratum --

def _head_pred(rule: Rule) -> str | None:
    return rule.rhs[0].p if rule.rhs else None


# Stratification is OBJECT-AWARE for EVERY predicate, content-blind (no relation name is special-
# cased in the engine — vision §1/§10): a producer of `?x P young` and a NAC on `?c P rough` are
# about DIFFERENT facts once the object is read, so they don't falsely cycle through the shared
# predicate `P`. Keyed on `(pred, literal-obj)`; a variable-object producer (`?x P ?y`) is a
# WILDCARD every `P`-NAC depends on. This only REFINES deps (never adds a cycle), so it is safe for
# every bank; where a predicate always uses one object (planning's `?o viable <yes>`) it collapses
# to the old name-keying. Cures the copula `is`-overload false cycle without hardcoding `is`.
_WILD = object()   # sentinel: a producer with a variable object (a wildcard for any NAC on its pred)


def _prod_key(pat: Pat):
    """The producer key a head pattern registers: `(pred, obj)`, or `(pred, _WILD)` for a variable
    object. Uniform over all predicates — no relation name is special-cased."""
    return (pat.p, _WILD if _is_var(pat.o) else literal_name(pat.o))


def stratify(rules: list[Rule]) -> list[list[Rule]]:
    """Partition `rules` into strata so a rule's NAC is evaluated only AFTER every
    rule that could PRODUCE the negated predicate has reached fixpoint.

    This is Datalog's stratified negation (vision §11), the static-analysis cure for
    the order-dependence of NAC over a *derived* fact (e.g. `serve_regular`'s
    `is not urgent` must see the `mark`-derived `is urgent`). Positive dependencies
    need no stratum — same-stratum forward chaining resolves them. Keyed OBJECT-AWARE on
    `(pred, literal-obj)` (`_prod_key`) — uniformly, no relation name special-cased — so `P young`
    and `P rough` don't falsely cycle. Sound (it only ever delays, never reorders wrongly). Raises
    if negation is cyclic. The scheduler stays dumb (vision §6): within a stratum every rule fires.
    """
    producers: dict = {}
    for i, r in enumerate(rules):
        if r.rhs:
            producers.setdefault(_prod_key(r.rhs[0]), set()).add(i)

    def nac_deps(pat: Pat) -> set[int]:
        if _is_var(pat.o):                               # variable-obj NAC: all producers of pred
            return set().union(*(v for k, v in producers.items() if k[0] == pat.p), set())
        return (producers.get((pat.p, literal_name(pat.o)), set())
                | producers.get((pat.p, _WILD), set()))

    memo: dict[int, int] = {}

    def stratum(i: int, stack: tuple[int, ...]) -> int:
        if i in memo:
            return memo[i]
        if i in stack:
            raise ValueError("rules are not stratifiable (negation cycle)")
        deps = set().union(*(nac_deps(pat) for pat in rules[i].nac)) \
            if rules[i].nac else set()
        deps.discard(i)                                  # self-NAC (idempotency) is fine
        s = 1 + max((stratum(d, stack + (i,)) for d in deps), default=-1)
        memo[i] = s
        return s

    for i in range(len(rules)):
        stratum(i, ())
    layers: dict[int, list[Rule]] = {}
    for i, s in memo.items():
        layers.setdefault(s, []).append(rules[i])
    return [layers[s] for s in sorted(layers)]


def lint_stratifiable(rules: list[Rule], *, source: str = "<bank>") -> None:
    """Phase 1.3 (implementation_plan.md): check stratifiability at BANK-LOAD time, not only when
    `run_rules` first hits the cycle at runtime and silently degrades (`_strata_or_degrade`). A
    negation cycle is a static, content-blind defect (`lint.py`'s `negation-cycle` Smell reuses this
    same `stratify` call) — an author should see it the moment a bank finishes loading, not as a
    buried `warnings.warn` the first time the bank happens to run. Raises `ValueError` naming
    `source` (the bank/corpus being loaded) with the cycle detail; call sites that WANT graceful
    runtime degradation instead (e.g. `run_rules(strict=False)`) are unaffected — this is purely an
    earlier, louder checkpoint, not a change to execution semantics."""
    try:
        stratify(rules)
    except ValueError as e:
        raise ValueError(f"{source}: not stratifiable - {e}") from e


def _on_cycle(policy) -> str:
    """The `on_cycle` stance of `policy` (`policy.py`), defaulting to the shipped `"raise"` when a
    loader was called with no policy. Kept a tiny local reader so `authoring` needn't import the
    policy module at top level (it is a leaf-ward dependency; a None policy means the default stance)."""
    return getattr(policy, "on_cycle", "raise") if policy is not None else "raise"


def _strata_or_degrade(rules: list[Rule], *, strict: bool) -> tuple[list[list[Rule]], list[Rule]]:
    """`(strata, dropped)`. Normally the full stratification. If negation is CYCLIC (not
    stratifiable) and not `strict`, DEGRADE to the monotone (no-NAC) subset — which is always
    stratifiable (a rule with no NAC has no negation dep) — so the theory's positive chains
    still answer, and RETURN the dropped NAF rules to report (handoff 2a). `strict=True`
    re-raises the cycle (the old all-or-nothing behaviour)."""
    try:
        return stratify(rules), []
    except ValueError:
        if strict:
            raise
        dropped = [r for r in rules if r.nac]
        return stratify([r for r in rules if not r.nac]), dropped


def run_rules(graph: Graph, rules: list[Rule], *,
              max_steps: int = 200, provenance: bool = True,
              tools: dict | None = None, strict: bool = False) -> list:
    """Run `rules` over `graph` stratum by stratum (stratified negation), each layer
    to fixpoint via the ISA forward Machine (`run_bank`) — the ONE production engine
    (recognition, planner control/teardown, decide's completion/defeat, TMS retraction
    via the INTERPOSE opcode, graded/coref passes). run_bank mints provenance when
    asked, services `<call>` tools at fixpoint, DROP_CTRL/INTERPOSE handle control
    deletion + reversible retraction; stratification is still done here (per layer).
    Returns the (always-empty) journal for back-compat with callers that still
    unpack a return value.

    GRACEFUL DEGRADATION (handoff 2a): if negation is cyclic (not stratifiable), the monotone
    (no-NAC) subset is run so positive derivations still answer, and a WARNING names the dropped
    NAF rules (never silently lose the whole theory). Pass `strict=True` to re-raise instead."""
    strata, dropped = _strata_or_degrade(rules, strict=strict)
    if dropped:
        warnings.warn(
            f"{len(dropped)} negation rule(s) dropped - theory not stratifiable "
            f"(negation cycle); reasoning with the monotone subset only: "
            + ", ".join(r.key for r in dropped), stacklevel=2)
    journal: list = []
    for layer in strata:
        run_bank(graph, layer, max_rounds=max_steps, tools=tools, provenance=provenance)
    return journal


# ---------------------------------------------------------------------------
# Stage 3 — a looser phrasing, translated into the native form (the user's ask)
# ---------------------------------------------------------------------------
#
# "Rules that translate a loose phrasing into the native rule" are exactly the
# vision's normalization tax (§7/§3), applied to the rule sublanguage. But a loose
# imperative like `serve urgent customers first` carries no variables and no frame:
# the verb's meaning ("serving someone gives them an express portion of an in-stock
# flavour they want") must be DECLARED. So the looseness is anchored by a CNL
# LEXICON that defines the frame as a native rule template:
#
#   serve ?x first means ?x served express when ?x wants ?f and ?f is in_stock
#
# Recognition of the loose sentence is a form (in-graph). Emission is a TOOL: the
# native rule INVENTS pattern variables (`?x`), and a Pat-rule RHS cannot mint a
# node literally named `?x` (the token reader treats `?x` as a variable, not a
# name) — the documented quote/eval wall (handoff §7, cf. expand_relation_properties).
# The tool stays on the calculator side of that wall: it clones the declared
# template and adds the adjective condition.

# Recognizer: a 4-word imperative `VERB ADJ NOUN ADVERB` -> a <use> annotation.
TRANSLATION_FORMS: list[Rule] = [
    Rule(
        key="form.loose.imperative",
        lhs=[Pat("?s", "first", "?verb"), Pat("?verb", "next", "?adj"),
             Pat("?adj", "next", "?noun"), Pat("?noun", "next", "?adverb")],
        rhs=[Pat("<use>?", "u_verb", "?verb"), Pat("<use>?", "u_adj", "?adj"),
             Pat("<use>?", "u_adverb", "?adverb")],
    ),
]


def parse_lexicon(text: str) -> dict[tuple[str, str], tuple[Rule, str]]:
    """Parse `VERB ?x ADVERB means <native rule>` frame definitions.

    Returns {(verb, adverb): (template_rule, subject_var)}. The body after `means`
    is ordinary native rule CNL, parsed by `load_rules` (so the frame's variables
    come from the lexicon TEXT — no var invention needed here).
    """
    lexicon: dict[tuple[str, str], tuple[Rule, str]] = {}
    for line in text.splitlines():
        if " means " not in line:
            continue
        sig, body = line.split(" means ", 1)
        sig_toks = sig.split()
        verb, adverb = sig_toks[0], sig_toks[-1]
        template = load_rules(body)[0]
        subject_var = template.rhs[0].s            # e.g. "?x"
        lexicon[(verb, adverb)] = (template, subject_var)
    return lexicon


def expand_loose(graph: Graph, lexicon: dict[tuple[str, str], tuple[Rule, str]]) -> list[Rule]:
    """TOOL: turn each recognized <use> into a native `Rule` via its lexicon frame.

    Clones the frame's template and adds the loose adjective as a marker condition
    (`subject_var is ADJ`). Unknown frames are skipped.
    """
    rules: list[Rule] = []
    for nid in graph.nodes():
        verb = _obj(graph, nid, "u_verb")
        if verb is None:
            continue
        key = (graph.name(verb), graph.name(_obj(graph, nid, "u_adverb")))
        if key not in lexicon:
            continue
        template, subj = lexicon[key]
        adj = graph.name(_obj(graph, nid, "u_adj"))
        rules.append(Rule(
            key=f"loose.{key[0]}.{adj}.{key[1]}",
            lhs=[*template.lhs, Pat(subj, "is", adj)],
            rhs=list(template.rhs), nac=list(template.nac), graded=list(template.graded),
        ))
    return sorted(rules, key=lambda r: r.key)


def load_loose_rules(loose_text: str, lexicon_text: str) -> list[Rule]:
    """Translate loose imperative rule CNL into native `Rule`s, using a CNL lexicon."""
    lexicon = parse_lexicon(lexicon_text)
    rg = Graph()
    load_text(rg, loose_text)
    run_bank(rg, TRANSLATION_FORMS)   # recognition on the ISA forward driver (Phase 0.2)
    return expand_loose(rg, lexicon)


# ---------------------------------------------------------------------------
# Q1a — one corpus, emergent recognition (no Python classifier)
# ---------------------------------------------------------------------------
#
# `load_corpus` loads an entire mixed corpus (facts, native rules, a lexicon frame,
# loose phrasings) and lets WHICH FORM FIRES decide what each statement is. There is
# NO Python classifier inspecting a line to route it — the KEYWORDS route it:
#   - a statement with `when`  -> `rule.head` (the fact forms self-exclude on it);
#   - a statement with `means` -> `form.lexicon` (re-anchors the body as a rule
#     template, so `rule.head` folds it; the template is skipped by `expand_rules`);
#   - a 4-word imperative       -> a `<use>` (matched to a frame, or harmlessly dropped);
#   - a plain assertion         -> the fact forms;
#   - anything matching nothing  -> raw tokens (the linter's "no form recognized this").
#
# Facts and rules go into SEPARATE graphs fed the SAME corpus. This is NOT a content
# classifier — each graph runs its recognition forms over the whole corpus and simply
# ignores what doesn't match (a fact line forms no rule; a rule line forms no fact,
# since the fact forms self-exclude). It is the b1 pattern-space segregation: rules
# must live apart from facts, because running `RULE_FORMS` in the fact graph makes the
# engine REUSE fact nodes for a rule's concept literals (`k_pred -> is_a`), polluting
# the fact space — exactly what b1 forbids. Folding rules INTO the fact graph is the
# parked b2 (meta-circular) milestone; until then this split stands.

# The lexicon frame: `VERB ?x ADVERB means <native rule>`. Recognizing `means`
# re-anchors the body (`<frame> first ?body`) so `rule.head` folds it into a rule
# template, and records the frame signature for the loose translator.
LEXICON_FORMS: list[Rule] = [
    Rule(
        key="form.lexicon",
        lhs=[Pat("?s", "first", "?verb"), Pat("?verb", "next", "?var"),
             Pat("?var", "next", "?adv"), Pat("?adv", "next", "means?"),
             Pat("means?", "next", "?body")],
        rhs=[Pat("<frame>?", "frame_verb", "?verb"), Pat("<frame>?", "frame_adverb", "?adv"),
             Pat("<frame>?", "body", "?body"), Pat("<frame>?", "first", "?body")],
    ),
]

# Forms recognized in the rule-source graph (rules, lexicon frames, loose uses, NL universals).
RULE_SOURCE_FORMS: list[Rule] = (RULE_FORMS + IF_THEN_FORMS + PLURAL_UNIVERSAL_FORMS
                                 + LEXICON_FORMS + TRANSLATION_FORMS)


def frames_in_graph(graph: Graph) -> dict[tuple[str, str], tuple[Rule, str]]:
    """Read `<frame>` nodes into a lexicon {(verb, adverb): (template_rule, subj_var)}.

    The emergent counterpart of `parse_lexicon` (no `" means "` split in Python):
    the frame's body was folded into a rule node by `rule.head`; this finds it.
    """
    lexicon: dict[tuple[str, str], tuple[Rule, str]] = {}
    for n in graph.nodes():
        if graph.name(n) != "<frame>":
            continue
        verb, adv, body = (_obj(graph, n, "frame_verb"),
                           _obj(graph, n, "frame_adverb"), _obj(graph, n, "body"))
        if verb is None or adv is None or body is None:
            continue
        R = next((m for m in graph.nodes()
                  if _objs(graph, m, "rl_pred") and _obj(graph, m, "rl_subj") == body), None)
        if R is not None:
            lexicon[(graph.name(verb), graph.name(adv))] = (
                _expand_rule_node(graph, R), graph.name(body))
    return lexicon


def expand_loose_from_graph(graph: Graph) -> list[Rule]:
    """Translate `<use>` nodes into native `Rule`s via the `<frame>`s in the SAME graph."""
    return expand_loose(graph, frames_in_graph(graph))


def _corpus_lines(text: str) -> list[str]:
    """The CNL statements of a corpus (drop blank lines and '#' comments)."""
    return [s for line in text.splitlines()
            if (s := line.strip()) and not s.startswith("#")]


_ALL_FORMS: list[Rule] = FORM_RULES + FACT_FORMS + RULE_SOURCE_FORMS


def load_corpus(text: str, *, policy=None) -> tuple[Graph, list[Rule]]:
    """Load a whole mixed CNL corpus into ONE graph; what each statement IS emerges
    from the forms (no Python classifier — the keywords route it).

    Returns (kb, rules): `kb` is the single substrate (facts + the graded layer, and
    the recognized rule/frame structure, which reasoning ignores by data); `rules`
    are the executable rules. Answer demand-driven with `ask_goal`/`check` (DEMAND-DRIVEN NEGATION,
    firmware v3 — every `not P` clause is a NAC decided on demand by negation-as-failure); a full
    forward snapshot, if needed for inspection/export, is `run_rules(kb, rules)`. Lines starting with
    '#' are comments.

    Facts and rule-source COEXIST safely here (the parked b1 separation is no longer
    needed) because (1) rule fragments are built with bound-literals, so recognition
    never grabs a fact node, and (2) reasoning rules bind a context node (e.g. a shop)
    that rule-source can't satisfy — isolation by DATA, not by an engine scope.
    """
    kb = Graph()
    # Recognize every statement on the ISA FORWARD driver (`_recognize` -> `run_bank`), NOT the
    # forward `rewriter` — the "one engine" move. Whole-batch, reproducing `rewriter.run` exactly:
    # facts and rule-source COEXIST because rule fragments are built with bound-literals (recognition
    # never grabs a fact node), exactly as under `rewriter`.
    _recognize(kb, _corpus_lines(text), _ALL_FORMS)
    wire_same_as(kb, _ALL_FORMS)         # ADDITIVE coreference (was: destructive canonicalize merge)
    prop = _coref_propagation(kb)        # `same_as` propagation over the content predicates present
    run_bank(kb, prop)                   # compose facts across links (ISA): closed-world markers
                                         # (`closes`) reach a rule's `is not P` clause, etc.
    run_bank(kb, graded_rules(kb))       # gradable word -> embedding (propagate EMIT); degrees from KB
    propagate_embeddings(kb)             # spread degrees to coreferent mentions
    # Reflect to executable Rules; APPEND the propagation so `run_rules(kb, rules)` composes derived
    # facts across the same_as links too (the merge gave that permanently; additivity needs it live).
    rules = expand_rules(kb) + expand_loose_from_graph(kb) + prop
    if _on_cycle(policy) == "raise":                     # firmware STANCE (see `policy.py`)
        lint_stratifiable(rules, source="load_corpus")
    return kb, rules
