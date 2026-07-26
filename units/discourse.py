"""DISCOURSE REFERENCE — reference DECIDED, never resolved (`docs/design/substrate_inversion.md` §24.3, §30).

*"The lion"* in the second sentence must reach the same entity as the first. On a store you look it up by
name. **Here you may not:** §21.2 makes entities NAMELESS, and §22.5 rules that interning a surface word
into a node is §3's forbidden second global structure — it would fuse two utterances BY NAME, which is
precisely the label this substrate abolished.

So reference is **decided, not resolved**, and everything in this module is DATA: a mention is a fresh node
with facts on it, and every decision below is a declared rule. Nothing here is engine.

**⭐ THE LICENSED BRIDGE IS THE LEXEME** (`vocab.lexeme`, §30.1). The word *lion* belongs to the FORM SET —
supplied at load, shared across utterances, exactly as a role is. THE LION is a nameless mention. A mention
carries `m <word> lexeme("lion")`, so coref is a rule over LEXEME identity and nothing about the ENTITY is
resolved by name. Both rules survive intact, and the distinction was already being made for roles.

**⭐ INEQUALITY DISSOLVES INTO IDENTITY-AS-DATA** (§30.2). Coref needs *"?x ≠ ?z"* and the matcher has no
such primitive. It needs none: `self_rule()` derives `?x <self> ?x` for every mention, and `Absent(?x <self>
?z)` **is** `?x ≠ ?z` — exact, over the value on the wire (§6a). A recorded gap of the same shape as §17.E's
predicate variable, dissolved rather than filled. It works only because §28/§29 made the negated-premise
join sound: the inequality rule's producer has to be WIRED, and until §28.1 it was not.

**⚠ WHAT THIS MODULE DOES NOT CLAIM.** `substitution_rule` unions properties; it does not COLLAPSE identity,
because a rule cannot remove (§30.4). Two coreferent mentions end up indistinguishable by their properties
and remain two nodes, so coref here is sound for MATCHING and silent for COUNTING. That is §17.F's logged
uniqueness gap, unchanged in kind.
"""
from __future__ import annotations

from .match import Absent, Triple, Var
from .value import Fact, Subgraph, mint
from .vocab import lexeme, role

WORD = role("<word>")            # mention -> its LEXEME (form set)
DET = role("<det>")              # mention -> <definite> | <indefinite>
SELF = role("<self>")            # x -> x. Identity AS DATA, so NAF over it is inequality
SAME_AS = role("same_as")        # the DECISION: this mention is that entity

DEFINITE = role("<definite>")
INDEFINITE = role("<indefinite>")

AMBIGUOUS = role("<ambiguous>")  # more than one antecedent — §17.F's uniqueness claim, as a FACT
RESOLVED = role("<resolved>")    # the existential witness `dangling_rule` needs
DANGLING = role("<dangling>")    # a definite with NO antecedent — §17.F's reference failure, as a FACT

_X, _Y, _Z, _Z2, _W, _P = (Var("x"), Var("y"), Var("z"), Var("z2"), Var("w"), Var("p"))


def mention(word: str, det=INDEFINITE, facts=()) -> tuple:
    """One mention: a **fresh nameless node** plus its surface facts.

    The node is minted with no name at all — there is nothing for a later utterance to look it up BY, which
    is the property §24.3 requires. What makes it findable is the LEXEME it carries, and a lexeme is the
    form set's, not the discourse's.

    Returns `(node, facts)`; `facts` is what intake would contribute to the utterance's value."""
    m = mint("")
    out = [Fact(m, WORD, lexeme(word)), Fact(m, DET, det)]
    out += [Fact(m, p if not isinstance(p, str) else role(p), o) for p, o in facts]
    return m, Subgraph(out)


def utterance(*mentions) -> Subgraph:
    """The union of several mentions' facts — one discourse value, ready to be a `given`."""
    v = Subgraph()
    for _, facts in mentions:
        v = v | facts
    return v


# -- the rules, and every one of them is DATA ------------------------------------------------------

def self_rule() -> tuple:
    """`?x <word> ?y ⇒ ?x <self> ?x` — **identity as data, which is how inequality becomes sayable.**

    Keyed on `<word>` rather than on everything, so it ranges over MENTIONS and not over the whole value:
    the point of `<self>` is to let one mention be distinguished from another."""
    return ((Triple(_X, WORD, _Y),), (Triple(_X, SELF, _X),))


def coref_rule() -> tuple:
    """**THE DECISION.** A DEFINITE mention corefers with an INDEFINITE mention of the same lexeme:

        ?x <word> ?w ∧ ?x <det> definite ∧ ?z <word> ?w ∧ ?z <det> indefinite ∧ ?x ≠ ?z ⇒ ?x same_as ?z

    **The asymmetry is the whole content.** Keying on the shared lexeme ALONE merges *"a lion roars, a lion
    sleeps"* — two different lions — which is not a substrate failure but a WRONG DECISION, and §24.3 says
    reference must be decided. Definiteness is what carries the decision: *"the"* claims an antecedent,
    *"a"* introduces one. Measured both ways.

    This is a FIRST decision, not the last one; recency, salience and description-matching are further
    premises on the same rule shape, and none of them needs new machinery."""
    return ((Triple(_X, WORD, _W), Triple(_X, DET, DEFINITE),
             Triple(_Z, WORD, _W), Triple(_Z, DET, INDEFINITE),
             Absent(Triple(_X, SELF, _Z))),
            (Triple(_X, SAME_AS, _Z),))


def ambiguity_rule() -> tuple:
    """`?x same_as ?z ∧ ?x same_as ?z2 ∧ ?z ≠ ?z2 ⇒ ?x <ambiguous> ?x`

    ⭐ **§17.F's UNIQUENESS CLAIM, WHICH IT LOGGED AS HAVING NO MECHANISM** (*"two cars matched; both would
    be derived over, silently"*). Two distinct antecedents for one definite is now a FACT other units can
    read — [[epistemic-closure-under-composition]]'s *reasoned ∪ refused, never silently mis-mapped*,
    reaching discourse reference. It does not RESOLVE the ambiguity; it makes it sayable, which is what was
    missing."""
    return ((Triple(_X, SAME_AS, _Z), Triple(_X, SAME_AS, _Z2), Absent(Triple(_Z, SELF, _Z2))),
            (Triple(_X, AMBIGUOUS, _X),))


def resolved_rule() -> tuple:
    """`?x same_as ?z ⇒ ?x <resolved> ?x` — the existential WITNESS.

    `Absent` may only test variables the positive body bound (`match.check_safety`), so *"there is NO ?z
    such that ?x same_as ?z"* cannot be written directly. Projecting the existential onto a witness first is
    the standard datalog idiom, and it costs one rule."""
    return ((Triple(_X, SAME_AS, _Z),), (Triple(_X, RESOLVED, _X),))


def dangling_rule() -> tuple:
    """`?x <det> definite ∧ ¬(?x <resolved> ?x) ⇒ ?x <dangling> ?x`

    ⭐ **§17.F's REFERENCE FAILURE, which it logged as *indistinguishable from negation*.** An unresolved
    definite is now positively marked, so presupposition failure stops collapsing into falsity. Same move as
    `ambiguity_rule`: the failure becomes a fact rather than an absence."""
    return ((Triple(_X, DET, DEFINITE), Absent(Triple(_X, RESOLVED, _X))),
            (Triple(_X, DANGLING, _X),))


def symmetry_rule() -> tuple:
    """`?x same_as ?z ⇒ ?z same_as ?x` — **and it is needed for a reason worth stating** (§30.5).

    `coref_rule` is deliberately ASYMMETRIC: the definite points at the indefinite, and that asymmetry is
    the whole content of the decision. But `substitution_rule` follows the arrow, so it copies the DEFINITE
    mention's properties onto the antecedent and not the reverse — facts stated about *"the lion"* reach the
    entity, while what is already known about the entity never reaches the mention.

    **The asymmetry that makes the DECISION right makes the SUBSTITUTION one-directional.** Sameness is an
    equivalence and the decision is not, so the two need separating: decide asymmetrically, then symmetrize.
    Found by getting the direction wrong in the spike and reading what came out."""
    return ((Triple(_X, SAME_AS, _Z),), (Triple(_Z, SAME_AS, _X),))


def substitution_rule() -> tuple:
    """`?x ?p ?y ∧ ?x same_as ?z ⇒ ?z ?p ?y` — §17.D's generic merge, unblocked by role nodes (§22.3).

    **⚠ TWO THINGS TO KNOW BEFORE USING IT.**

    1. **It needs an AUTHORED MERGE** (§30.3). Its wildcard atom is satisfied by ANY fact, so the assembler
       cannot tell that it needs the DISCOURSE as well as the decision — wired to the coref rule alone it
       substitutes over `same_as` facts and nothing else. A wildcard LHS carries no information for the
       assembler, so this rule's topology must be authored: a carrier at in-degree 2 over the discourse and
       the decision. **This is the first place where wiring is not inferable, and it is not a defect: it is
       what declining to say what you read costs.**
    2. **It UNIONS properties; it does not COLLAPSE identity** (§30.4). A rule cannot remove, so both
       mentions survive and both end up carrying both properties. Sound for matching, silent for counting."""
    return ((Triple(_X, _P, _Y), Triple(_X, SAME_AS, _Z)), (Triple(_Z, _P, _Y),))


def declare_all(net, substitution: bool = False) -> None:
    """Declare the reference machinery into a net's LIBRARY. Nothing is instantiated (§3, lazy spawn).

    `substitution` is off by default because it needs an authored merge to be useful — see
    `substitution_rule`. Declaring it without one gets a unit that fires on nothing but its own control
    facts, which §27's journal will report and which is not what anyone wants."""
    net.declare("SELF", *_split(self_rule()))
    net.declare("COREF", *_split(coref_rule()))
    net.declare("RESOLVED", *_split(resolved_rule()))
    net.declare("AMBIG", *_split(ambiguity_rule()))
    net.declare("DANGLING", *_split(dangling_rule()))
    if substitution:
        net.declare("SYMM", *_split(symmetry_rule()))       # sameness is an equivalence; the DECISION is not
        net.declare("SUBST", *_split(substitution_rule()))


def _split(rule) -> tuple:
    lhs, rhs = rule
    return lhs, rhs


__all__ = ["WORD", "DET", "SELF", "SAME_AS", "DEFINITE", "INDEFINITE", "AMBIGUOUS", "RESOLVED", "DANGLING",
           "mention", "utterance", "self_rule", "coref_rule", "ambiguity_rule", "resolved_rule",
           "dangling_rule", "symmetry_rule", "substitution_rule", "declare_all"]
