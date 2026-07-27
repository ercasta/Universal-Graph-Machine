"""FORMS — the closed class, as runnable entries.

`docs/units/forms_cnl.md` §5 specifies a nine-field entry format and §10 records that the format is
**designed, not validated** — *"the test is writing ten real entries and seeing which field is always
empty or always fudged."* This module is that test, for the three fields that can be executed:

| §5 field | here |
|---|---|
| **introduction** — what licenses writing it | `introduce`, which decorates the claim |
| **elimination** — what may be read from it | `eliminate`, which returns the unit that reads it |
| **commits** — what believing it commits the system to | `commits` **and** `forbids`, two predicates |

The other six fields are prose and are carried as prose. **`commits` is the one that turns the format
from documentation into a test**, because a leak is precisely *a commitment respected alone and violated
in company* — which is checkable with no notion of what is true (`sieve.py`).

⚠ **§5's single `commits` field does not survive first contact, and this is a finding about the format.**
A commitment can fail in two opposite directions, and `P8` already names both: *elimination outrunning
introduction* (too much was concluded — a **leak**) and *introduction without elimination* (too little —
**inert**). One predicate cannot report which, so the classifier cannot tell a form that leaked from a
form that correctly went quiet. The field is split here into `commits` (what must hold) and `forbids`
(what must not), which is the same distinction the entry format's own `introduction`/`elimination` pair
already draws and then loses when it comes to state the commitment.

⚠ **And an honest commitment has to name the other axes.** `positive` commits you to the predicate only
when the claim is *asserted* at the *world* level — so writing its commitment requires mentioning FORCE
and LEVEL. That is the composability problem appearing in the **specification**, not merely in the
implementation, and `axis_appeals()` counts it.

## What is deliberately not here

**No open-class content.** The subject is an opaque node and the predicate is an opaque string. `P2`
says the boundary is a factorization and the engine holds only the closed half; a probe that used real
words would be testing the translator, which is not under test.

**No prose, and no CNL surface.** Every form decorates one **claim occurrence**, which is what the
transcriber would have produced. Generating a surface and parsing it back would put the untrusted
component inside the measurement.

## ⚠ The eliminations are written NAIVELY on purpose

Each `eliminate` is written the way an author would write it **thinking only about its own form** —
which is the realistic failure mode and the one `forms_discourse` §4.2 diagnosed in the single measured
leak. `guarded=True` rebuilds them consulting the co-present forms, so the two can be compared. Neither
setting is *the* answer; the comparison is the result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .engine import Attribute, Emit, Network, Stamp, StandingUnit
from .graph import EMPTY, Graph, Node, role_edge
from .match import atom, role
from .overlay import View

PREDICATE = "dangerous"          # opaque: the engine never needs to know what it means
CLAIM = "claim"
ABOUT = "about"
STRENGTH = "strength"

# Everything an elimination in this module may conclude. Naming it is what makes a run **comparable**
# to another run: `engine.readable()` keys by node id, and every run mints fresh nodes, so comparing
# its output across runs compares nothing. It also confines the comparison to what was *derived* —
# base decorations differ between a composite and its parts by construction, and folding them in makes
# every composite look like it gained something.
ANTECEDENT = "provoked"          # the antecedent's predicate — opaque, like PREDICATE
WHEN = "when"                    # tier 2 (`forms_cnl` §6): the conditional's carrier

CONCLUSIONS = (PREDICATE, f"not_{PREDICATE}", "raised", "mentions",
               # …and every candidate form's marker. ⚠ A form whose conclusion is missing from this
               # list has an **invisible state change**, and `P3` makes the state change the identity of
               # the form — so it then appears identical to every other invisible form and the
               # factorization sieve reports that everything is everything. Found exactly that way.
               "normative", "permitted", "held_then", "sourced", "surprising", "demanded",
               "conditional_read")


@dataclass
class Ctx:
    """One claim under construction, plus what the forms decorating it have said.

    `decor` is how a **guarded** elimination learns that another form is present. That it has to exist
    at all is the finding: an elimination that consults its neighbours is not a local rule any more."""

    graph: Graph
    subject: Node
    claim: Node
    guarded: bool = False
    decor: dict = field(default_factory=dict)
    refusal: str | None = None
    antecedent: Node | None = None      # the `when:` claim, if a conditional built one
    antecedent_holds: bool = False      # …and whether the world satisfies it

    def set(self, key: str, value: Any) -> bool:
        """Decorate the claim. **Refuses** rather than overwrites — two forms wanting one slot at
        different values is a genuine incompatibility, not a merge (`cnl.md` §1, create never merge)."""
        prior = self.decor.get(key)
        if prior is not None and prior != value:
            self.refusal = f"{key}: {prior!r} vs {value!r}"
            return False
        self.decor[key] = value
        self.graph = self.graph.with_node(self.claim, **{key: value})
        return True

    def grade(self, key: str, band: str) -> bool:
        self.decor[key] = band
        self.graph = self.graph.with_degree(self.claim, key, band)
        return True


def new_ctx(guarded: bool = False) -> Ctx:
    g = EMPTY
    subject = Node("subject")
    claim = Node(CLAIM)
    g = g.with_node(subject, name="subject")
    g = g.with_node(claim, name=CLAIM, predicate=PREDICATE)
    g = role_edge(g, claim, ABOUT, subject)
    return Ctx(g, subject, claim, guarded=guarded)


def claim_pattern(ctx: Ctx, **attrs) -> tuple:
    """*A claim about this predicate, and what it is about.* The shared skeleton every elimination
    matches, so every form reads the same structure and differences are the forms' own."""
    graded = attrs.pop("graded", ())
    return (atom("c", out=(role(ABOUT, atom("s")),), predicate=PREDICATE, graded=graded, **attrs),)


# -- the entry ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Form:
    """One closed-class form. `axis` is `content` / `force` / `level`.

    ⚠ **The single `axis` field is `forms_cnl` §5's, and it is exactly what is under suspicion.** `P1`
    says a category is a *point* in the product of the three axes; an entry carrying one axis value is
    an entry for an axis **value**, not for a point. The format is reproduced faithfully so the probe
    tests the format as specified rather than a repaired version of it."""

    name: str
    axis: str
    introduce: Callable[[Ctx], bool]
    eliminate: Callable[[Ctx], StandingUnit | None]
    commits: Callable[[Ctx, View], str | None] = lambda ctx, v: None
    forbids: Callable[[Ctx, View], str | None] = lambda ctx, v: None
    appeals: tuple = ()          # other AXES this form's commitment has to name
    note: str = ""

    def __repr__(self) -> str:
        return f"<{self.axis}:{self.name}>"


def _reads_true(view: View, ctx: Ctx) -> bool:
    return view.attr(ctx.subject, PREDICATE) is True


def _says_anything_about_the_world(view: View, ctx: Ctx) -> str | None:
    """Any content conclusion at all about the subject.

    ⚠ Narrower predicates are what let the first pair entry slip through: `ask` forbidding only the
    *positive* reading is silent when a composite concludes the **denial** instead, and asking commits
    you to neither. A commitment has to forbid the whole slot, not one value of it."""
    for key in (PREDICATE, f"not_{PREDICATE}"):
        if view.attr(ctx.subject, key) is True:
            return f"{key} concluded of the subject"
    return None


def _plain_frame(ctx: Ctx) -> bool:
    """Is this claim an unqualified assertion about the world?

    ⚠ **That a content form has to ask this is the result, not a convenience.** `positive` commits you
    to the predicate only when asserted at world level; under `ask` or `language` it commits you to
    nothing, and a commitment stated without that condition reports a correct silence as a failure."""
    return ctx.decor.get("force", "assert") == "assert" and         ctx.decor.get("level", "world") == "world"


# -- CONTENT --------------------------------------------------------------------------------------

def _positive_elim(ctx: Ctx) -> StandingUnit:
    """*From an affirmed claim, the predicate holds of the subject.*

    Naively: it asks about polarity, because that is its own form, and about nothing else."""
    pat = claim_pattern(ctx, polarity="pos")
    if ctx.guarded:
        pat = claim_pattern(ctx, polarity="pos", force="assert", level="world")
    return StandingUnit("elim:positive", pat, Attribute("s", PREDICATE, True))


POSITIVE = Form(
    "positive", "content",
    introduce=lambda ctx: ctx.set("polarity", "pos"),
    eliminate=_positive_elim,
    commits=lambda ctx, v: (None if not _plain_frame(ctx) or _reads_true(v, ctx)
                            else "affirmed, but nothing concluded"),
    appeals=("force", "level"),
    note="the baseline content form: an unqualified affirmation.",
)


def _negation_elim(ctx: Ctx) -> StandingUnit:
    """*From a denied claim, the denial holds.*

    ⚠ It concludes a **positive marker** rather than an absence — `model.md` §8's discipline. There is
    no strong negation in this engine to conclude instead."""
    pat = claim_pattern(ctx, polarity="neg")
    if ctx.guarded:
        pat = claim_pattern(ctx, polarity="neg", force="assert", level="world")
    return StandingUnit("elim:negation", pat, Attribute("s", f"not_{PREDICATE}", True))


NEGATION = Form(
    "negation", "content",
    introduce=lambda ctx: ctx.set("polarity", "neg"),
    eliminate=_negation_elim,
    commits=lambda ctx, v: (None if not _plain_frame(ctx)
                            or v.attr(ctx.subject, f"not_{PREDICATE}") is True
                            else "denied, but nothing concluded"),
    appeals=("force", "level"),
    forbids=lambda ctx, v: (f"{PREDICATE} still reads True under a denial"
                            if _reads_true(v, ctx) else None),
    note="the operator case for A1: negation OVER X changes what X commits you to.",
)


def _degree_elim(ctx: Ctx) -> StandingUnit:
    """*From a graded claim, the predicate holds — at that band.*

    Naively: it asks whether the claim carries a strength, and concludes the content qualified by it.
    It does **not** ask about polarity, because polarity is somebody else's form."""
    pat = claim_pattern(ctx, graded=(STRENGTH,))
    if ctx.guarded:
        pat = claim_pattern(ctx, graded=(STRENGTH,), polarity="pos",
                            force="assert", level="world")
    band = ctx.decor.get(STRENGTH, "likely")
    return StandingUnit("elim:degree", pat,
                        Attribute("s", PREDICATE, True), Stamp("s", PREDICATE, band))


def _degree_forbids(ctx: Ctx, v: View) -> str | None:
    """*If the predicate is readable at all, it is readable at no more than the asserted band.*

    The crisp/graded split is structural (`graph.py`), so a conclusion that carries no band is not a
    weaker claim — it is an **unqualified** one, and that is the loss this commitment exists to catch."""
    if not _reads_true(v, ctx):
        return None
    asserted = ctx.decor.get(STRENGTH)
    got = v.degree(ctx.subject, PREDICATE)
    if got is None:
        return f"graded at {asserted!r} but concluded unqualified"
    from .band import weaker
    return None if not weaker(asserted, got) else f"concluded at {got!r}, stronger than {asserted!r}"


DEGREE = Form(
    "degree", "content",
    introduce=lambda ctx: ctx.grade(STRENGTH, "likely"),
    eliminate=_degree_elim,
    commits=lambda ctx, v: (None if not _plain_frame(ctx)
                            or ctx.decor.get("polarity") == "neg" or _reads_true(v, ctx)
                            else "graded assertion concluded nothing"),
    forbids=_degree_forbids,
    appeals=("force", "level", "polarity"),
    note="the form the one measured leak was found on (`forms_discourse` §4.2).",
)


# -- FORCE ----------------------------------------------------------------------------------------

ASSERT = Form(
    "assert", "force",
    introduce=lambda ctx: ctx.set("force", "assert"),
    eliminate=lambda ctx: None,
    note="the default force; carried explicitly so that a cell always fixes one.",
)


def _ask_elim(ctx: Ctx) -> StandingUnit:
    """*An asked claim raises an issue.* Inquisitive semantics' shape: a question does not inform, it
    puts something on the table (`forms_discourse` §4.3 ②)."""
    return StandingUnit("elim:ask", claim_pattern(ctx, force="ask"),
                        Attribute("c", "raised", True))


ASK = Form(
    "ask", "force",
    introduce=lambda ctx: ctx.set("force", "ask"),
    eliminate=_ask_elim,
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "raised") is True
                            else "asked, but no issue raised"),
    forbids=lambda ctx, v: (None if (m := _says_anything_about_the_world(v, ctx)) is None
                            else f"asking it committed the system: {m}"),
    note="`forms_discourse` §8's worked failure: map the question perfectly, then assert it.",
)


# -- LEVEL ----------------------------------------------------------------------------------------

WORLD = Form(
    "world", "level",
    introduce=lambda ctx: ctx.set("level", "world"),
    eliminate=lambda ctx: None,
    note="the default level.",
)


def _language_elim(ctx: Ctx) -> StandingUnit:
    """*A claim at the language level says something about the expression, not about the subject.*"""
    return StandingUnit("elim:language", claim_pattern(ctx, level="language"),
                        Attribute("c", "mentions", True))


LANGUAGE = Form(
    "language", "level",
    introduce=lambda ctx: ctx.set("level", "language"),
    eliminate=_language_elim,
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "mentions") is True
                            else "mentioned, but nothing concluded about the expression"),
    forbids=lambda ctx, v: (None if (m := _says_anything_about_the_world(v, ctx)) is None
                            else f"a claim about the WORD committed the system: {m}"),
    note="use/mention. The level axis's only non-default value, and the test of whether LEVEL is an "
         "axis at all or a stratification homoiconicity has already deleted.",
)


# -- CANDIDATE FORMS -----------------------------------------------------------------------------
#
# Each one is a **hypothesis test on a decision the documents already took**, not a form added for
# coverage. `forms_discourse` §4b listed NINE forces; `forms_cnl` P1 ships six, and hedge, goal and norm
# were dropped with nothing recorded about why. Three of these test that drop. The last three test the
# opposite question — whether the three axes have room for what typology says languages actually
# grammaticalize (`forms_discourse` §3.6 level 2: time, space, causation, quantity, modality, evidence,
# discourse status).
#
# ⚠ Their eliminations conclude **their own marker on the claim** and nothing about the subject. That is
# deliberate: it keeps them out of the leak measurement, which is sensitive to how carefully an
# elimination was authored, while leaving the *slot* measurement — which is not — fully informative.


def _marker_elim(name: str, key: str, value, mark: str):
    def build(ctx: Ctx) -> StandingUnit:
        return StandingUnit(f"elim:{name}", claim_pattern(ctx, **{key: value}),
                            Attribute("c", mark, True))
    return build


DENY = Form(
    "deny", "force",
    introduce=lambda ctx: ctx.set("polarity", "neg"),
    eliminate=_negation_elim,
    commits=lambda ctx, v: (None if not _plain_frame(ctx)
                            or v.attr(ctx.subject, f"not_{PREDICATE}") is True
                            else "denied, but nothing concluded"),
    forbids=lambda ctx, v: (f"{PREDICATE} still reads True under a denial"
                            if _reads_true(v, ctx) else None),
    note="⚠ HYPOTHESIS: not a force at all. If deny = negation ∘ assert it should land in the polarity "
         "slot and be indistinguishable from it — the enumerate-the-product error P1 exists to prevent.",
)

HEDGE = Form(
    "hedge", "force",
    introduce=lambda ctx: ctx.grade(STRENGTH, "unlikely"),
    eliminate=_degree_elim,
    forbids=_degree_forbids,
    note="⚠ HYPOTHESIS: dropped from the force list because it is DEGREE at another band. If so it "
         "shares degree's slot — and then the question is whether a band is a form or a value.",
)

NORM = Form(
    "norm", "force",
    introduce=lambda ctx: ctx.set("modality", "obligation"),
    eliminate=_marker_elim("norm", "modality", "obligation", "normative"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "normative") is True
                            else "obliged, but nothing concluded"),
    note="⚠ HYPOTHESIS: deontic modality, i.e. CONTENT. If so it does not share the force slot.",
)

MODALITY = Form(
    "modality", "content",
    introduce=lambda ctx: ctx.set("modality", "permission"),
    eliminate=_marker_elim("modality", "modality", "permission", "permitted"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "permitted") is True
                            else "permitted, but nothing concluded"),
    note="the control for NORM: declared content, and they should turn out to be one slot.",
)

COMMAND = Form(
    "command", "force",
    introduce=lambda ctx: ctx.set("force", "command"),
    eliminate=_marker_elim("command", "force", "command", "demanded"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "demanded") is True
                            else "commanded, but nothing demanded"),
    forbids=lambda ctx, v: (None if (m := _says_anything_about_the_world(v, ctx)) is None
                            else f"commanding it committed the system: {m}"),
    note="the control for the force slot: a third value that should exclude assert and ask.",
)

PAST = Form(
    "past", "content",
    introduce=lambda ctx: ctx.set("time", "past"),
    eliminate=_marker_elim("past", "time", "past", "held_then"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "held_then") is True
                            else "tensed, but nothing concluded"),
    note="tense. Declared CONTENT — so if content were one axis it would exclude negation and degree.",
)

EVIDENTIAL = Form(
    "evidential", "content",
    introduce=lambda ctx: ctx.set("source", "hearsay"),
    eliminate=_marker_elim("evidential", "source", "hearsay", "sourced"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "sourced") is True
                            else "sourced, but nothing concluded"),
    note="⚠ HYPOTHESIS: fits NO declared axis. It is not what is claimed, nor what is done with it, nor "
         "what it is about — it is how the claim was come by. In `forms_discourse`'s own glossary, "
         "*a required provenance field on every record*. Filed under content only because there is "
         "nowhere else to file it.",
)

MIRATIVE = Form(
    "mirative", "content",
    introduce=lambda ctx: ctx.set("mirative", True),
    eliminate=_marker_elim("mirative", "mirative", True, "surprising"),
    commits=lambda ctx, v: (None if v.attr(ctx.claim, "surprising") is True
                            else "marked as unexpected, but nothing concluded"),
    note="⚠ HYPOTHESIS: also fits no axis. `forms_discourse` §3.2 names mirativity itself as something "
         "languages grammaticalize, in a caveat, and then never places it.",
)


# -- CONDITIONALITY ------------------------------------------------------------------------------
#
# ⚠ **The first candidate that is not a decoration on the claim**, and that is the point of adding it.
# Every form above writes a *field*: a polarity, a band, a force, a level. A conditional relates the
# claim to **another claim**, so it needs a second occurrence and a `when:` role — tier 2 of
# `forms_cnl` §6, and the first tier-2 role anything here has used.
#
# It is added as a form so the sieve can measure it. What the sieve **cannot** hold is the other half:
# on this engine a conditional is properly a **standing unit**, and a unit is not a claim decoration.
# See `test_sieve.py` and `forms_cnl` §13.


def add_antecedent(ctx: Ctx, holds: bool) -> bool:
    """Give the claim a `when:` antecedent, and optionally make the world satisfy it."""
    if ctx.antecedent is not None:
        return True
    ante = Node("antecedent")
    g = ctx.graph.with_node(ante, name="antecedent", predicate=ANTECEDENT)
    if holds:
        g = g.with_node(ante, satisfied=True)
    ctx.graph = role_edge(g, ctx.claim, WHEN, ante)
    ctx.antecedent = ante
    ctx.antecedent_holds = holds
    ctx.decor[WHEN] = ANTECEDENT
    return True


def _conditional_elim(ctx: Ctx) -> StandingUnit:
    """**Modus ponens**: from *if P then Q* together with *P*, conclude *Q*.

    The pattern reaches the antecedent through the `when:` role and requires it `satisfied` — so the
    unit simply does not fire when the antecedent is unmet, which is the whole of →-elimination.

    ⚠ Naively it does not consult polarity, force or level, exactly like the others."""
    ante = atom("a", predicate=ANTECEDENT, satisfied=True)
    attrs = {} if not ctx.guarded else {"polarity": "pos", "force": "assert", "level": "world"}
    pat = (atom("c", out=(role(ABOUT, atom("s")), role(WHEN, ante)),
                predicate=PREDICATE, **attrs),)
    return StandingUnit("elim:conditional", pat, Attribute("s", PREDICATE, True),
                        Attribute("c", "conditional_read", True))


def _conditional_forbids(ctx: Ctx, v: View) -> str | None:
    """⭐ **Harmony for →, and it is the only commitment here with real teeth.** *If P then Q* commits
    you to Q **when P**, and to nothing whatever when P is unknown. Detaching the consequent from an
    unsatisfied antecedent is the classic leak, and it is a leak no per-form check catches — the form
    looks fine in isolation."""
    if ctx.antecedent is None or ctx.antecedent_holds:
        return None
    if _reads_true(v, ctx):
        return "consequent detached from an unsatisfied antecedent"
    return None


CONDITIONAL = Form(
    "conditional", "content",
    introduce=lambda ctx: add_antecedent(ctx, holds=True),
    eliminate=_conditional_elim,
    commits=lambda ctx, v: (None if not _plain_frame(ctx) or _reads_true(v, ctx)
                            else "antecedent satisfied, but the consequent was not concluded"),
    forbids=_conditional_forbids,
    appeals=("force", "level", "polarity"),
    note="⚠ NOT a decoration: it relates the claim to another claim through `when:`. The first tier-2 "
         "role used here, and the first form whose real home is a UNIT rather than a field.",
)

UNMET = Form(
    "unmet", "content",
    introduce=lambda ctx: add_antecedent(ctx, holds=False),
    eliminate=_conditional_elim,
    commits=lambda ctx, v: None,
    forbids=_conditional_forbids,
    note="the same conditional with its antecedent UNSATISFIED — the control that makes the "
         "detachment leak visible. It shares `conditional`'s slot by construction.",
)


SEED = (POSITIVE, NEGATION, DEGREE, ASSERT, ASK, WORLD, LANGUAGE)
CANDIDATES = SEED + (DENY, HEDGE, NORM, MODALITY, COMMAND, PAST, EVIDENTIAL, MIRATIVE,
                     CONDITIONAL, UNMET)

BY_AXIS = {"content": (POSITIVE, NEGATION, DEGREE),
           "force": (ASSERT, ASK),
           "level": (WORLD, LANGUAGE)}

# ⚠ **Every cell fixes a polarity, a force and a level**, defaulting to these. An unmarked claim is not
# force-less and level-less; it is an affirmation about the world, and leaving a slot empty instead
# makes any elimination that consults it silently unable to fire — which measures the probe, not the
# forms.
DEFAULTS = (POSITIVE, ASSERT, WORLD)


def excludes(a: "Form", b: "Form") -> bool:
    """**Signal A.** Do these two forms refuse to co-occur? Decided by `introduce` alone — no network is
    run, because incompatibility is a property of what they write, not of what anything concludes."""
    ctx = new_ctx()
    return not (a.introduce(ctx) and b.introduce(ctx))


def writes(f: "Form") -> frozenset:
    """**Signal B.** Which fields of the claim this form touches, observed by running its introduction."""
    ctx = new_ctx()
    f.introduce(ctx)
    return frozenset(ctx.decor)


def competes(a: "Form", b: "Form") -> bool:
    """Two forms are in one slot if **either** signal says so.

    ⚠ **Signal A alone is blind in the graded sort, and that is a property of the engine.** Bands
    `meet` rather than disagree (`overlay.Grade`), so two forms writing different bands to one attribute
    never refuse each other — `degree` and `hedge` came out as separate slots under A, which is wrong.
    Signal B catches it because they touch the same field.

    ⚠ **Neither signal is free of the author.** The field name is chosen when the form is written. What
    keeps this from being circular is that the two signals are independent — a crisp pair is caught by
    refusal without reference to the name — and that they **agree everywhere both can see**
    (`signal_audit`). Where they disagree, the disagreement is the finding."""
    return excludes(a, b) or bool(writes(a) & writes(b))


def signal_audit(forms: tuple = SEED) -> dict:
    """Where the two slot signals disagree. Agreement is evidence; disagreement is a measurement limit
    worth naming rather than averaging away."""
    only_a, only_b = [], []
    for i, a in enumerate(forms):
        for b in forms[i + 1:]:
            ex, ov = excludes(a, b), bool(writes(a) & writes(b))
            if ex and not ov:
                only_a.append((a.name, b.name))
            elif ov and not ex:
                only_b.append((a.name, b.name))
    return {"refusal_only": only_a, "shared_field_only": only_b}


_SLOT_CACHE: dict = {}


def slots(forms: tuple = SEED) -> dict:
    """**The axes, recovered from behaviour rather than declared.**

    Two forms occupy one slot iff they exclude each other; independent forms combine freely. The
    transitive closure of exclusion gives the partition. This is the standard move in feature theory —
    an inventory is derived from complementary distribution, never asserted — and it is the only
    evidence available here about how many axes there are."""
    key = tuple(f.name for f in forms)
    if key in _SLOT_CACHE:
        return _SLOT_CACHE[key]
    parent = {f.name: f.name for f in forms}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(forms):
        for b in forms[i + 1:]:
            if competes(a, b):
                ra, rb = find(a.name), find(b.name)
                if ra != rb:
                    parent[rb] = ra
    groups: dict = {}
    for f in forms:
        groups.setdefault(find(f.name), []).append(f)
    return _SLOT_CACHE.setdefault(key, groups)


def slot_of(f: "Form", forms: tuple = SEED) -> str:
    for key, members in slots(forms).items():
        if f in members:
            return key
    return f.name


def frame(forms: tuple, inventory: tuple = SEED) -> tuple:
    """Complete a cell so every **slot with a default** is filled exactly once.

    ⚠ **By measured slot, not by declared axis, and it cannot be done the other way.** `degree` and
    `positive` are declared the same axis (`content`), so framing by axis treats a graded claim as
    already having a polarity and hands the guarded elimination a claim with no polarity to read. The
    declared axis assignment actively prevents the cells from being built correctly, which is the
    sharpest single piece of evidence that `content` is not one axis."""
    groups = slots(inventory)
    where = {m.name: key for key, members in groups.items() for m in members}
    filled = {where.get(f.name, f.name) for f in forms}
    return tuple(forms) + tuple(d for d in DEFAULTS if where.get(d.name, d.name) not in filled)


def signature(ctx: Ctx, view: View) -> frozenset:
    """What this run **concluded**, keyed so two runs are comparable.

    Positions rather than nodes (`subject` / `claim`), and only `CONCLUSIONS`. Bands are carried
    separately because crisp and graded are different sorts (`graph.py`) — a conclusion that lost its
    band has to look different from one that kept it, or `degree`'s commitment is untestable."""
    items: list = []
    for who, n in (("subject", ctx.subject), ("claim", ctx.claim)):
        for key in CONCLUSIONS:
            v = view.attr(n, key)
            if v is not None:
                items.append((who, key, v))
        for key in CONCLUSIONS:
            band = view.degree(n, key)
            if band is not None:
                items.append((who, f"{key}~", band))
    return frozenset(items)


# -- running a cell -------------------------------------------------------------------------------

def negated_degree_elim(ctx: Ctx) -> StandingUnit | None:
    """**A PAIR ENTRY** — an elimination for `negation ∘ degree` as a composite, not for either alone.

    *From a denied claim held at a band, the denial holds at that band.* It needs no second layer and no
    chaining: both forms decorate **one claim**, so the composite is readable in the same place the
    parts are. That is the cheap news. The expensive news is that it exists at all — it is an entry per
    *pair*, which is the O(n²) the local harmony check was supposed to avoid."""
    if ctx.decor.get("polarity") != "neg" or STRENGTH not in ctx.decor:
        return None
    band = ctx.decor[STRENGTH]
    pat = claim_pattern(ctx, polarity="neg", graded=(STRENGTH,))
    if ctx.guarded:
        pat = claim_pattern(ctx, polarity="neg", graded=(STRENGTH,),
                            force="assert", level="world")
    return StandingUnit("elim:negation×degree", pat,
                        Attribute("s", f"not_{PREDICATE}", True),
                        Stamp("s", f"not_{PREDICATE}", band))


PAIR_ENTRIES = {frozenset({"negation", "degree"}): negated_degree_elim}


def pair_entries(forms: tuple) -> tuple:
    """Every pair entry whose forms are all present in this cell."""
    names = {f.name for f in forms}
    return tuple(v for k, v in PAIR_ENTRIES.items() if k <= names)


def run(forms: tuple, guarded: bool = False, composed: bool = False) -> tuple:
    """Assert one claim bearing every form in `forms`, read it, and return `(ctx, view, network)`.

    **Every elimination is wired from the same axiom** and from nothing else. That is deliberate: all
    the forms decorate one claim, so each elimination can already see everything every other form
    contributed. If a composite still fails, the failure is in what the elimination *asks*, not in what
    it could reach — which is the distinction that makes the verdict mean something."""
    ctx = new_ctx(guarded)
    for f in forms:
        if not f.introduce(ctx):
            return ctx, None, None

    net = Network()
    axiom = net.given(ctx.graph, name="claim")
    builders = [f.eliminate for f in forms]
    if composed:
        builders += list(pair_entries(forms))
    for build in builders:
        u = build(ctx)
        if u is not None:
            net.wire(axiom, net.add(u))
    net.revive()
    return ctx, net.world(), net


__all__ = ["Ctx", "Form", "SEED", "BY_AXIS", "DEFAULTS", "CONCLUSIONS", "PREDICATE", "STRENGTH",
           "run", "new_ctx", "frame", "signature", "excludes", "writes", "competes", "signal_audit",
           "slots", "slot_of",
           "PAIR_ENTRIES", "pair_entries", "negated_degree_elim", "CANDIDATES",
           "DENY", "HEDGE", "NORM", "MODALITY", "COMMAND", "PAST", "EVIDENTIAL", "MIRATIVE",
           "CONDITIONAL", "UNMET", "ANTECEDENT", "WHEN", "add_antecedent",
           "POSITIVE", "NEGATION", "DEGREE", "ASSERT", "ASK", "WORLD", "LANGUAGE"]
