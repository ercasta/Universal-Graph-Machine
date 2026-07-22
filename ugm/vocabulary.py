"""
Substrate vocabulary — the ONE canonical source of truth for the logic fragment's fixed predicate
tokens (Phase 2.5, `docs/attic/vocabulary_declaration_design.md`, crux §7 ratified "consolidate").

These are the CLOSED logical vocabulary `logic_fragment.md` fixes: the copula/membership/negation/
subsumption/congruence primitives, universal to EVERY KB, NOT domain-specific. `logic_fragment.md` §5
already treats `same_as` as a fixed distinguished predicate; this module extends that status to the
whole substrate set so each token appears ONCE instead of scattered, duplicated magic strings across
`decide`/`goal`/`check`/`query`/`universal`.

This is a LEAF module: it imports nothing from the package (stdlib-only), so `world_model`/`attrgraph`/
`goal`/`cnl/*` can all import it without a cycle. Do NOT add intra-package imports here.

This is TIER 1 (fixed substrate). The engine's DOMAIN vocabulary (`wants`/`in`/`has`/`before`/…) is NOT
here — it comes solely from a KB's declared relations/prepositions (Tier 2). The CNL surface's English
lexicon (recognizing the word "is", the `are`->`is` morphology) is Tier 3 and lives in `cnl/forms.py`;
it folds English to the CANONICAL names below.
"""
from __future__ import annotations

# --- copula / membership ----------------------------------------------------
COPULA = "is"                 # the copula / membership predicate: P(c) == c is P
NEG_COPULA = "is_not"         # the materialized negative copula: c is_not P
NEG_SUFFIX = "_not"           # the R -> R_not negation-naming convention (subsumes is -> is_not)

# --- subsumption ------------------------------------------------------------
IS_A = "is_a"                 # subsumption / category membership
IS_A_NOT = "is_a_not"         # negated subsumption (entailed from disjointness)

# --- congruence / disjointness ----------------------------------------------
SAME_AS = "same_as"           # declared congruence (logic_fragment.md §5)
DISJOINT = "disjoint_from"    # disjointness -> entailed negation
MENTION = "<mention>"         # universal surface-mention marker (coreference-as-rules Stage 4): every
                              # ingested ENTITY is `is_a <mention>`, the handle the declared same-name
                              # coref rule seeds BOTH vars from — so coref binds any entity regardless of
                              # its structural position, without a per-domain type. Filtered from output.

# --- surface vs interpretation ----------------------------------------------
DENOTES = "denotes"           # surface token -> the entity it is TAKEN to denote (the judgement).
                              # STRUCTURAL, not domain: it is the substrate's answer to "is this node
                              # discourse or is it the world". A node carrying it is SURFACE, so content
                              # addressed by its NAME belongs to its denotation, not to it
                              # (`chain.resolve_write_node`). Defined here rather than in
                              # `interpretation` because `chain` must see it and this is the leaf.
                              # Nothing on the token-is-entity route writes it, so that route is
                              # unaffected BY CONSTRUCTION — declare-before-use, as with the fork.

INTERPRETS = "interprets"     # entity -> every surface mention it was derived from (provenance).
                              # The inverse of DENOTES, and the hop a rule uses to reach SURFACE data
                              # from an interpretation node — see `assert_bank`'s deny rule.

# --- closed-world policy ----------------------------------------------------
CLOSES = "closes"             # P closes <closed_world>  (P is closed-world DATA)
CWA = "<closed_world>"        # the closed-world marker node

# --- scope / hypothesis -----------------------------------------------------
HYPOTHESIS = "<hypothesis>"   # the scope node's NAME/KEY (suppose.py). A `<hypothesis>` node holds a
                              # scope's band/kind/derivations and is referenced by its pencils via a
                              # `scope` VALUED ATTR, not a graph edge — so it is EDGELESS by design yet
                              # load-bearing. Incidental edge-based GC (lowering.final_gc,
                              # AttrGraph.gc_disconnected) must EXEMPT it: a scope is deleted only
                              # explicitly, by suppose._drop_scope. Shared here so the low-level GC
                              # passes can name it without importing suppose (cycle).

# --- relation-property / structural declarations ----------------------------
REL_PROPERTY = "rel_property"     # relation-property declaration (e.g. transitive)
TRANSITIVE = "transitive"         # a declared relation property
EVERY_IS_A = "every_is_a"         # universal subsumption declaration
IS_UNIQUE = "is_unique"           # uniqueness declaration
TARGET = "target"                 # goal plumbing: the goal's subject of interest
TYPE = "type"                     # goal plumbing: the goal's wanted category


def neg_pred(pred: str) -> str:
    """The negative predicate paired with `pred`: the single R -> R_not convention
    (`is` -> `is_not`, an arbitrary relation `R` -> `R_not`)."""
    return pred + NEG_SUFFIX


def is_neg_pred(pred: str) -> bool:
    """Whether `pred` is a NEGATIVE predicate under the `R -> R_not` convention (the inverse test of
    `neg_pred`). It names internal NAF / entailed-negation machinery, not a human-gatherable positive
    premise — so evidence-gathering skips it (§8.5b)."""
    return pred.endswith(NEG_SUFFIX)


# Substrate predicates that ALWAYS compose across `same_as` coreference — the fixed part of the coref
# predicate set. A KB's DOMAIN relations extend this at load time (via `declared_relations` /
# `declared_prepositions`); they are NOT enumerated here (that was the Phase-2.5 leak). `target`/`type`
# are structural goal-plumbing (universal reasoning), so they are substrate, not domain.
SUBSTRATE_COREF_PREDS = frozenset({
    IS_A, COPULA, SAME_AS, DISJOINT, REL_PROPERTY, CLOSES, EVERY_IS_A, IS_UNIQUE, TARGET, TYPE,
})
