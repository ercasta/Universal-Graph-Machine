"""INTAKE — turning something said into a goal, as data.

The loop is driven entirely by a goal, and until now the only way to get one was to call `goal.py` from
Python. So the one thing that starts the system was the one thing the system had no way to receive.

**⭐ Why intake is tractable now, when it was not before.** The `ugm/`-era attempts translated prose into
*arbitrary graph structure* and got 0/50 on raw prose, with the gap recorded as "100% constructional" —
unsurprising, because the target was unbounded. A goal is no longer arbitrary structure: it is a handful of
**constraint nodes** from a closed vocabulary (link, attribute, type; never, must, at most). Translating
into eight forms is a different problem from translating into anything, and that is the whole reason this
is a small module rather than a research programme.

**The border, and where the language model sits.** `asm.py` is already "the text surface and LLM border"
for *functions*; this is its sibling for *goals*. The division is the project's standing one — **the model
is a boundary tool, never the computation model**: a model may write this text, and the parser then accepts
or refuses it deterministically. What a model must never do is reach past the surface and write graph
structure directly, because then nothing could refuse it.

**⚠ The translator must be able to refuse, and refusal is the feature.** Three ways in, all loud:

* a line that matches no form — the vocabulary is closed, so an unrecognised sentence is not "best effort";
* a name that matches nothing;
* a name that matches **more than one thing**. Nodes here are nameless and a `label` is a convenience for
  humans, so resolving one is a lookup that can genuinely be ambiguous. `docs/units` records the lesson at
  length: *never identify by name alone*. Guessing between two candidates would be inventing a referent,
  which is exactly the failure a controlled language exists to prevent.

**The grammar**, deliberately boring — each form is recognisable by its shape or leading keyword:

```
goal stack them:            # or `ask`, `why`, `plan` — same body, different force
    # what must be true of the world
    a on b                      a link between individuals
    b.clear = true              an attribute value
    d.contents known            a KNOWLEDGE claim — go and look, rather than make it so
    some file                   SOMETHING of this type must exist
    a is a serviced_car         this individual must satisfy this type

    # what the plan itself may do
    never unstack               a forbidden operator
    never touch c               an individual that must not be bound
    must paint                  the plan has to include this
    at most 3 steps             a budget
```

```
type car:
    is a vehicle                    inherit another type's demands
    has 4 wheel each a wheel        a count, a label, and what each target must BE (recursive)
    has 1 body each of kind body    ...or merely what it was minted as (one level, cheap)
    has at most 1 trailer           a count is a RANGE
    weight between 800 and 2000     an attribute, bounded
    colour = "red"                  an attribute, exact
    wheel[0].pressure == wheel[1].pressure     two places inside the subgraph agreeing
    wheel[0].rim is not wheel[1].rim           ...and not being the same node
```

```
what it is:          where it is:         when it was:
    parcel               parcel               by start        # or `by at`, a point
                         by contains          delivery
```

```
criterion clear the block that must move:   # expert judgement — see `criterion.py`
    wants link on               key on an UNMET goal constraint; binds `subject` and `object`
    some top in subject by ^on  bind a FURTHER role by walking a relation, transitively
    when top is a clear_block   a condition; also `unless …`, and `x.k = v`, `x l y`, `x is there`
    unless wants link on from object        a condition about the GOAL, not the world
    do unstack b = top, floor = the ground  the action, WITH its arguments
    because …

directive …:                    # the same body, MANDATORY force
```

⭐⭐ **The wh-questions are a different FORM, not a fifth force.** `goal` / `ask` / `why` / `plan` state a
whole proposition and differ in what is done with it; `what` / `where` / `when` have a **gap** in them and
are answered by locating a thing in an order the world already has (`locate.py`). Hence a different body —
one bare name per line — and an answer that is **returned and never recorded**.

## ⭐⭐ ONE reference language, and where each block may use it

Everything that refers to something not directly at hand goes through `path.py`: `car.wheel[1].pressure`,
unbounded depth, `^label` for the backward direction. It is one grammar because it used to be three — a
private regex in `driver.role_node`, a hand-split on the first dot here, and the dotted roles
`establishes` emits, none of which knew about the others.

**What differs per block is only what the FIRST segment names**, which is why one language can serve
surfaces with nothing else in common:

| block | the base is | depth available |
|---|---|---|
| `type` | the node being checked | **any** — a type only ever *checks*, so nothing downstream can be misled |
| `goal` / `ask` / `why` / `plan` | a **named individual**, resolved by `resolve` | one hop, to an attribute |
| `method` / `procedure` | a **role** (`subject`, `object`), never a name | one hop, to an attribute |
| `prefer` / `avoid` | a named individual (whole, no hops) | none |
| `criterion` / `directive` | a **role** — `subject`, `object`, or one drawn by `some` — or `the <name>` | **any** |
| `establishes` (not authored) | a **parameter** of the function | any |

⚠ **The goal and method rows are a REFUSAL, not an omission, and they were a silent bug first.**
`a.wheel[1].pressure = 3` used to split on the first dot and build a constraint about an attribute
literally called `wheel[1].pressure` — a slot nothing has, and `describe_constraint` rendered it back
looking right. What blocks the honest version is downstream of intake: `conflict.unsatisfiable` keys a slot as
`(subject, key)` and would read two different wheels' pressures as one contended slot, while `goal.holds`,
`goal.undetermined` and `query.refutes` all read the attribute off the **base** node rather than the one
the reference reaches. Until they understand a navigated subject, `_one_hop` refuses and says so.

## ⭐⭐ FOUR verbs, ONE grammar — because a question IS a goal, and so is an instruction

`goal`, `ask`, `why` and `plan` take **exactly the same body**. That is not an economy in the parser; it
is the data model showing through. A goal is a set of constraints, a question is a set of constraints, and
what differs is only what you then *do* with them — record, answer, explain, or pursue.

```
goal make it so:   ask is it so?:   why is it so?:   plan make it so:
    a on b             a on b           a on b           a on b
```

**⭐⭐ `plan` is where this surface stops only DESCRIBING and starts DRIVING.** Every other verb records
something or asks something; none could make the system *work*. It reaches `driver.pursue`, which is
reachable at all only because deliberation stopped being a closed Python loop (`HANDOFF.md` §5z).

**⚠⚠ And it stops at a plan. The safety property is structural, not intended:** the whole search happens
on a workbench and `dispatch.service` refuses an imagined target, so a `plan` block **cannot change the
world however wrong the text is**. That is what makes it safe to put a driving verb on a surface a
language model may write. A verb that *carried out* the plan would cross into real effects, and it is
deliberately absent until that is discussed on its own terms.

⚠ **`replan` is NOT here, and the reason is a real gap rather than an omission.** Re-pursuing means naming
a goal that already exists, and `resolve` finds individuals by `label` **under `root`** — goals do not hang
off root, so the CNL has no form for referring to one. Inventing one here would be the same guess this
module exists to refuse.

**⚠ So what distinguishes them in the graph? Only a record of how it arrived.** The constraints are
identical, and the `verb` attribute is *not* a labelling error of the kind `HANDOFF.md` warns about —
structure does not entail it. Which speech act something was is genuinely extra information, unrecoverable
from the constraints, and it is exactly the project's standing **force-is-the-missing-axis** finding: force
is a property of the intake **route**, not of the form. Two people can want and doubt the same proposition.

**⭐ Plan constraints work in a question, and mean something useful.** `never phone_the_registrar` in an
`ask` block is *"is this derivable without asking anyone?"*; `at most 2 steps` is *"is it derivable in two
steps?"*. Nothing had to be added for this — constraining the route is constraining the route, whether the
route is a plan of action or a derivation.

⚠ `why` differs from `ask` in **what it reports, not in what it searches**: it wants the history behind
something that already holds (`query.account`), where `ask` wants a verdict on something that may not. A
`why` about a fact that is not true is answered by saying so, never by inventing a derivation for it.
"""
from __future__ import annotations

import re

from . import criterion as CR
from . import goal as G
from .graph import Graph
from . import guideline as GL
from . import locate as L
from . import method as M
from . import path as P
from . import types as TY
from .workbench import reachable


class Unreadable(Exception):
    """A line the closed vocabulary cannot represent, or a name that cannot be resolved to one node.

    Loud on purpose — see the module docstring. Carries the line number and the text."""


class Ambiguous(Unreadable):
    """A name matching **more than one** thing, carrying the candidates it refused to choose between.

    ⭐ A subclass, so every existing `except Unreadable` still catches it — the refusal is unchanged and
    only gains an attribute. `feedback_from_harneskills` §7, and the same shape already granted to
    `../pystrider` for unresolved roles: when the engine refuses *and already knows the answer set*,
    handing it over lets a UI ask a human to pick rather than making them guess."""

    def __init__(self, message: str, *, candidates: tuple = (), name: str | None = None):
        super().__init__(message)
        self.candidates = candidates
        self.name = name


def _literal(tok: str):
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    if tok in ("true", "false"):
        return tok == "true"
    if tok in ("null", "none"):
        return None
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d+\.\d+", tok):
        return float(tok)                # a range like `pressure between 2.1 and 2.5` needs these
    return tok


def resolve(g: Graph, name: str, *, under: str = "root") -> str:
    """The one node labelled `name` in the world. Refuses on none, and refuses on more than one.

    ⚠ Searched by **traversal from `under`**, never by scanning — the same discipline as
    `types.instances`, and for the same reason: a scan would find the system's own imaginings and offer a
    workbench copy as the referent of a word someone said."""
    hits = [n for n in reachable(g, under) if g.attr(n, "label") == name]
    if not hits:
        raise Unreadable(f"nothing here is called {name!r}")
    if len(hits) > 1:
        # ⭐ The candidates ride on the exception. `feedback_from_harneskills` §7: this is the harshest
        # refusal on the surface AND the one where the answer set is already in hand — `hits` is right
        # here — and it was dropped to report a count. For a UI that is the difference between telling a
        # person "2 things are called that" and showing them the two so they can pick one.
        # ⚠ It does not weaken *never identify by name alone*: the engine still refuses, and the
        # disambiguation is a human choosing ABOVE the border, who then writes an unambiguous reference.
        # Same division as for a language model — they may draft, this parser decides.
        raise Ambiguous(f"{name!r} is ambiguous — {len(hits)} things are called that; "
                        f"a name is not an identity", candidates=tuple(hits), name=name)
    return hits[0]


def _one_hop(text: str, lineno: int, what: str) -> tuple:
    """`"b.clear"` → `("b", "clear")`. **Refuses a deeper reference rather than mis-reading one.**

    ⚠ **This was a silent mis-parse, and it is the reason a shared reference language had to come with a
    composition review rather than after one.** `a.wheel[1].pressure = 3` split on the first dot and left a
    constraint whose *attribute* was literally named `wheel[1].pressure` — a slot nothing has, so the goal
    could never be met, and `describe_constraint` rendered it back looking exactly right. A round trip that
    a model checks itself against must not be able to lie.

    ⚠ **Why refused rather than supported here, when a `type` block takes any depth.** Three readers take
    a constraint's subject to BE the node the constraint is about, which a navigated subject makes false:

    * `conflict.unsatisfiable` identifies a slot as `(subject, key)`, so `a.wheel[0].pressure` and
      `a.wheel[1].pressure` would look like one contended slot — a contradiction reported where there is
      none, which is the unsound direction;
    * `goal.holds` and `goal.undetermined` read `g.attr(view(subject), key)` — the wrong node;
    * `query.refutes` does the same, and would answer a positive *no* about a slot nobody asked about.

    A type schema has none of these problems **because it only ever checks**. So the depth is available
    where it is correct, and refused — loudly, with this reason — where the machinery behind it has not
    caught up. That boundary is recorded rather than papered over."""
    base, rest = P.split_base(text)
    if rest is None or len(rest.hops) != 1 or rest.hops[0].index is not None or rest.hops[0].back:
        raise Unreadable(
            f"line {lineno}: {text!r} reaches deeper than a {what} can go. One hop from a named "
            f"individual to one of its attributes is what this form supports (`b.clear`); a `type` block "
            f"takes references of any depth")
    return base, rest.hops[0].label


#: ⭐⭐⭐ ONE PROPOSITION GRAMMAR, RECOGNISED IN ONE PLACE.
#:
#: A goal constraint, a method step and a criterion condition are three renderings of the same handful of
#: claims, and they were parsed by three hand-written dispatchers. Measured, they had drifted in four ways
#: that nobody chose:
#:
#:   * transitive `l+` existed only in a goal, though a condition is exactly the query it was built for;
#:   * the five comparison operators existed only in a `type` block — everywhere else `=` and nothing else;
#:   * `x is there` existed only in a criterion;
#:   * negation existed only in a criterion, via `unless`.
#:
#: That is the island problem `path.py` already solved one level down: *"It is one grammar because it used
#: to be three."* Same move, one level up. ⚠ **This recognises SHAPE ONLY and resolves nothing** — which
#: is what lets one grammar serve positions with genuinely different rules about what a name may mean and
#: how deep a reference may go (§8's table). Those differences are principled and stay; the four above
#: were accidents and go.
_SHAPE_FORMS = ("x l y", "x l+ y", "x.k = v", "x.k known", "x is a T", "x is there")

#: ⭐⭐ **THE BODY-LINE VOCABULARY, PER FAMILY, AS DATA** — and every refusal below renders *from* this,
#: so the error message and this table cannot disagree.
#:
#: Asked for by `docs/feedback_from_harneskills.md` §6, whose job is making this surface **writable**:
#: completion, live validation, a language model drafting CNL. The verbs were already reachable
#: (`VERBS`, `GOAL_VERBS`, …) and the body lines existed **only as display strings inside raise sites**,
#: so a consumer building completion had to re-type all six grammars into another repo with nothing
#: checking the copy. `cnl.md`'s own opening argues against exactly that: *"documentation that is merely
#: checked by a human rots exactly like a comment does"* — said of a docstring that had already gone stale
#: on a whole verb family. A second copy in a consumer's UI is that failure with a network boundary in it.
#:
#: ⚠ Prose shapes, not a machine-readable grammar, and deliberately: they asked for the closed sets by
#: name, explicitly **not** a parser API, an AST, or partial-input parsing. Promising structure here would
#: be promising a stability nothing tests.
FORMS: dict = {
    "goal": _SHAPE_FORMS + ("some T", "never f", "never touch x", "must f", "at most n steps"),
    "type": ("is a T", "has <count> label [each a T | each of kind K]", "key = v", "key <op> v",
             "key between lo and hi", "path <op> path", "path is [not] path", "because …"),
    "advice": ("action f", "touching x", "when T", "because …"),
    "method": ("handles S l", "when T", "within m", "some n in r by l", "step …", "because …"),
    "method step": _SHAPE_FORMS,
    "criterion": ("wants <sort> [label]", "some x in r by l", "when …", "unless …", "do f a = r, …",
                  "because …"),
    "condition": _SHAPE_FORMS + ("wants <sort> <label> from x",),
    "question": ("<one bare name>", "by <link>"),
}


def forms_for(family: str) -> tuple:
    """The legal body-line forms of a family — what a completer offers inside a block.

    ⚠ Keys are the names used in refusals (`FORMS`), not verbs: `method` and `procedure` share a body,
    as do `criterion`/`directive` and all four goal verbs, which is the whole point of a *force* pair."""
    if family not in FORMS:
        raise KeyError(f"no family {family!r}; known: {', '.join(sorted(FORMS))}")
    return FORMS[family]


def _shape(words: list, line: str, lineno: int, *, what: str, ops=("=",)):
    """Recognise one proposition. Returns a tagged tuple of **raw text**, or `None` if nothing matches.

    Ordered most-specific first, so a keyword form is never shadowed by the bare three-word link form —
    the discipline `_constrain` already followed and which now only has to be right once.

    `ops` is which comparison operators this position honours. ⚠ It is a parameter rather than a constant
    because a *constraint* is checked by readers that only understand equality (`goal.holds` compares with
    `==`), while a *condition* and a `type` relation are evaluated by machinery that already handles the
    full set. Widening it is a real change to those readers, not a parser edit — so the parameter records
    the limit at the boundary instead of letting each family invent its own answer."""
    if len(words) == 2 and words[1] == "known" and "." in words[0]:
        return ("known", words[0])
    if len(words) >= 3 and words[-2] == "is" and words[-1] == "there":
        return ("exists", " ".join(words[:-2]))
    if len(words) >= 4 and words[-3] == "is" and words[-2] == "a":
        return ("type", " ".join(words[:-3]), words[-1])
    if len(words) == 3 and words[1] in ops and "." in words[0]:
        return ("attr", words[0], words[1], words[2])
    if len(words) == 3 and words[1] in TY.VALUE_OPS and "." in words[0]:
        raise Unreadable(f"line {lineno}: {words[1]!r} is not available in a {what}; here a comparison is "
                         f"{' or '.join(ops)}. The full set ({', '.join(TY.VALUE_OPS)}) works in a "
                         f"`type` block, whose machinery evaluates them")
    if len(words) == 3:
        return ("link", words[0], words[1], words[2])
    return None


def _shape_refused(words: list, line: str, lineno: int, what: str, extra: str = "") -> Unreadable:
    """⚠ Rendered FROM `FORMS`, never from a literal beside the raise. That is `feedback_from_harneskills`
    §6's actual ask: the error message and the completion list have to be the same object, or the copy in
    a consumer's UI drifts and nothing notices."""
    return Unreadable(f"line {lineno}: cannot read {line!r} — the {what} vocabulary is closed "
                      f"({' | '.join(FORMS.get(what, _SHAPE_FORMS))}){extra}")


def _constrain(g: Graph, goal: str, words: list, line: str, lineno: int, under: str) -> None:
    """One line to one constraint. Ordered most-specific first, so a keyword form is never shadowed."""
    node = lambda w: resolve(g, w, under=under)          # noqa: E731

    if words[:2] == ["at", "most"] and len(words) >= 3:
        G.limit_steps(g, goal, int(words[2]))
    elif words[:2] == ["never", "touch"] and len(words) == 3:
        G.forbid_action(g, goal, on=node(words[2]), reason=line)
    elif words[0] == "never" and len(words) == 2:
        G.forbid_action(g, goal, function=words[1], reason=line)
    elif words[0] == "must" and len(words) == 2:
        G.require_action(g, goal, function=words[1])
    elif words[0] == "some" and len(words) == 2:
        G.require_type(g, goal, words[1])
    else:
        # ⭐ Everything below is the SHARED proposition grammar — see `_shape`. What stays here is only
        # what a goal does with each shape, plus the plan constraints above, which are about the ROUTE
        # rather than about the world and so are genuinely a goal's own vocabulary.
        shape = _shape(words, line, lineno, what="goal constraint")
        if shape is None:
            raise _shape_refused(words, line, lineno, "goal")
        kind = shape[0]
        if kind == "type":
            G.require_type(g, goal, shape[2], about=node(shape[1]))
        elif kind == "known":
            # ⭐ A KNOWLEDGE claim: *go and look*, as opposed to *make it so*. The surface distinguishes
            # them because the system now can — see `graph.UNKNOWN`.
            subject, key = _one_hop(shape[1], lineno, "goal constraint")
            G.require_known(g, goal, node(subject), key)
        elif kind == "attr":
            subject, key = _one_hop(shape[1], lineno, "goal constraint")
            G.require_attr(g, goal, node(subject), key, _literal(shape[3]))
        elif kind == "exists":
            # ⚠ `x is there` has no home in a goal: a goal says what must BE true, and *"it resolves"* is
            # a claim about the reference rather than about the world. Refused with the form that means it.
            raise Unreadable(f"line {lineno}: `is there` asks whether a reference resolves, which is a "
                             f"condition, not something to make true. A goal that wants something to "
                             f"exist says `some <type>`")
        else:
            # ⭐ `wh contains+ parcel` — reach at any depth, the one closed-class item §5x measured as
            # real. The `+` qualifies the RELATION, not a name, which is why it is read here.
            label, transitive = P.parse_link(shape[2])
            G.require_link(g, goal, node(shape[1]), label, node(shape[3]), transitive=transitive)


# ⭐⭐ FOUR forces on ONE body. `plan` is the fourth, and it joins here rather than getting its own family
# because it changes nothing about what is *said* — only what is then done with it. That is the module's
# own thesis paying rent: a goal is a set of constraints, and `goal` / `ask` / `why` / `plan` differ in
# force, not in form.
#
# ⚠ **`plan` is safe to put on the surface, and `do` is not — the difference is not a matter of degree.**
# Planning happens entirely on a workbench, so `plan` cannot touch the world however wrong the text is;
# `dispatch.service` refusing an imagined target makes that structural rather than intended. A verb that
# *carried out* the plan would cross into real effects, and it is deliberately absent until that is
# discussed on its own terms rather than arriving as a fifth item in a tuple.
GOAL_VERBS = ("goal", "ask", "why", "plan")
ADVICE_VERBS = ("prefer", "avoid")
METHOD_VERBS = ("method", "procedure")
TYPE_VERBS = ("type",)
CRITERION_VERBS = ("criterion", "directive")

# ⭐⭐ **THE WH-QUESTIONS, AND THEY ARE A DIFFERENT FORM — not a fifth force on the same body.** Every verb
# above states a whole proposition and differs only in what is then done with it (`goal.py`'s constraints,
# four ways). These three have a **gap** in them: they name a thing and ask which way it stands in an order
# the world already has — `locate.py`. So they take a different body, one bare name per line, and they
# **answer** rather than record. `docs/units`' standing finding is that a category is a PRODUCT of content,
# force and level; this is the content axis moving, where `ask` versus `goal` was the force axis.
#
# ⚠ `when` is also a *body* keyword in an advice and a method block (`when T`, a guard). No parse can
# confuse them — only the first line of a block is read as a verb — but the two are unrelated words and
# nobody should try to unify them.
READER_VERBS = L.VERBS

VERBS = GOAL_VERBS + ADVICE_VERBS + METHOD_VERBS + TYPE_VERBS + READER_VERBS + CRITERION_VERBS

ROLES = (M.SUBJECT, M.OBJECT)

_SORTS = ("link", "attr", "type")


def _ref(g: Graph, text: str, lineno: int, line: str, under: str, names=None) -> str:
    """Validate a reference at AUTHORING time, so a bad one is refused where it is written.

    ⚠ The alternative — checking when the criterion is consulted — would report a typo from inside a
    search, thousands of steps later, as *silence*. A criterion that says nothing because it is
    mis-written is indistinguishable from one that says nothing because the situation does not call for
    it, and that is the single worst failure this surface could have."""
    words = text.split()
    if len(words) == 4 and words[0] in CR.SELECTORS and words[2] == "by":
        P.parse_link(words[3].lstrip("^") or words[3])
        return _ref(g, words[1], lineno, line, under, names) and text
    if len(words) == 2 and words[0] == "the":
        # ⚠ Resolved HERE, not when the criterion is consulted — `prefer`/`avoid` already resolves
        # `touching x` at parse time, and the reason is sharper for a criterion: a name that resolves to
        # nothing would surface thousands of search steps later AS SILENCE, indistinguishable from a
        # criterion that simply had nothing to say. A typo must never look like a judgement.
        resolve(g, words[1], under=under)
        return text
    if len(words) != 1:
        raise Unreadable(f"line {lineno}: cannot read the reference {text!r} — a reference is a role, "
                         f"a path from one, `the <name>`, or `<{'|'.join(CR.SELECTORS)}> <ref> by <link>`")
    base, rest = P.split_base(words[0])
    legal = CR.ROLES if names is None else names
    if base not in legal:
        raise Unreadable(f"line {lineno}: {base!r} is not a role — a criterion speaks of "
                         f"{', '.join(legal)}, never a named individual, or it would be about that "
                         f"individual and could not be reused. A further role is introduced by "
                         f"`some <name> in <ref> by <link>`, BEFORE it is used")
    _ = rest                                          # `split_base` already parsed and would have raised
    return text


def _criterion_test(g: Graph, c: str, words: list, negated: bool, line: str, lineno: int,
                    under: str) -> None:
    """One `when` / `unless` line. ⭐ Each becomes its OWN node, which is what lets `governing` say
    *which* line stopped a criterion — the property §6 needs and an opaque predicate could never give."""
    if words[0] == "wants" and len(words) in (4, 5) and words[-2] == "from":
        if words[1] not in _SORTS:
            raise Unreadable(f"line {lineno}: a goal wants {', '.join(_SORTS)} — not {words[1]!r}")
        CR.test(g, c, sort="wants", negated=negated, want_sort=words[1],
                label=words[2] if len(words) == 5 else None, left=_ref(g, words[-1], lineno, line, under, CR.names_of(g, c)))
    else:
        # ⭐ The SHARED proposition grammar (`_shape`). A condition is the same handful of claims a goal
        # and a step make; what differs is that a referring position may be a role, a drawn name or
        # `the <name>`, and may reach any depth — because a condition only ever CHECKS.
        ref = lambda t: _ref(g, t, lineno, line, under, CR.names_of(g, c))     # noqa: E731
        shape = _shape(words, line, lineno, what="condition")
        if shape is None:
            raise _shape_refused(words, line, lineno, "condition")
        kind = shape[0]
        if kind == "exists":
            CR.test(g, c, sort="exists", negated=negated, left=ref(shape[1]))
        elif kind == "type":
            CR.test(g, c, sort="type", negated=negated, label=shape[2], left=ref(shape[1]))
        elif kind == "attr":
            who, key = _one_hop(shape[1], lineno, "criterion")
            CR.test(g, c, sort="attr", negated=negated, key=key, value=_literal(shape[3]),
                    left=ref(who))
        elif kind == "known":
            # ⚠ Deliberately still refused here, and now the refusal is stated once. `known` reads an
            # attribute slot for ignorance; `criterion.test` has no `known` sort, so accepting it would
            # build a condition nothing evaluates.
            raise Unreadable(f"line {lineno}: `known` asks whether a slot has been looked at, which a "
                             f"condition cannot yet evaluate — it is a goal constraint")
        else:
            label, transitive = P.parse_link(shape[2])
            # ⭐ TRANSITIVE REACH IN A CONDITION — previously available only in a goal, which was an
            # accident of three hand-written parsers rather than a decision. `cnl.md` §8 says `+` belongs
            # "in a link position — a goal line or a query", and a condition IS the query.
            CR.test(g, c, sort="link", negated=negated, label=label, transitive=transitive,
                    left=ref(shape[1]), right=ref(shape[3]))


def _criterion_line(g: Graph, c: str, words: list, line: str, lineno: int, under: str) -> None:
    if words[0] == "wants" and len(words) in (2, 3):
        if words[1] not in _SORTS:
            raise Unreadable(f"line {lineno}: a goal wants {', '.join(_SORTS)} — not {words[1]!r}. "
                             f"That vocabulary is closed because it is also what an index would key on")
        CR.wants(g, c, words[1], words[2] if len(words) == 3 else None)
    elif words[0] == "some" and len(words) == 6 and words[2] == "in" and words[4] == "by":
        name = words[1]
        if name in CR.names_of(g, c):
            raise Unreadable(f"line {lineno}: {name!r} is already bound here; a second `some` of the "
                             f"same name would silently shadow the first")
        label, back = (words[5][1:], True) if words[5].startswith("^") else (words[5], False)
        P.parse_link(label)
        CR.draw(g, c, name, _ref(g, words[3], lineno, line, under, CR.names_of(g, c)), label, back=back)
    elif words[0] in ("when", "unless") and len(words) > 1:
        _criterion_test(g, c, words[1:], words[0] == "unless", line, lineno, under)
    elif words[0] == "do" and len(words) > 1:
        rest = " ".join(words[1:])
        name, _, argtext = rest.partition(" ")
        args = {}
        for piece in argtext.split(",") if argtext.strip() else []:
            param, eq, ref = piece.strip().partition("=")
            if not eq:
                raise Unreadable(f"line {lineno}: cannot read {piece.strip()!r} — an argument is "
                                 f"`param = <reference>`")
            args[param.strip()] = _ref(g, ref.strip(), lineno, line, under, CR.names_of(g, c))
        if not args:
            raise Unreadable(f"line {lineno}: `do {name}` binds no arguments; a criterion names an "
                             f"action WITH its arguments, which is the whole of what it adds")
        CR.does(g, c, name, args)
    elif words[0] == "because" and len(words) > 1:
        g.put(c, because=" ".join(words[1:]))
    else:
        raise _shape_refused(words, line, lineno, "criterion")


def _advise(g: Graph, gl: str, words: list, line: str, lineno: int, under: str) -> None:
    """One line of a `prefer`/`avoid` block. Closed, keyword-led, and deliberately tiny."""
    if words[0] == "action" and len(words) == 2:
        g.put(gl, function=words[1])
    elif words[0] == "touching" and len(words) == 2:
        g.link(gl, "on", resolve(g, words[1], under=under))
    elif words[0] == "when" and len(words) == 2:
        g.put(gl, when=words[1])
    elif words[0] == "because" and len(words) > 1:
        g.put(gl, because=" ".join(words[1:]))
    else:
        raise _shape_refused(words, line, lineno, "advice")


def _reader(g: Graph, q: str, words: list, line: str, lineno: int, under: str) -> None:
    """One line of a `what` / `where` / `when` block: a bare name, or the word the question walks.

    ⭐ **The body is the smallest one on this surface, and that is the finding rather than an economy.**
    §5x measured all three as needing no machinery — `types.recognize` exists, and ordering over a
    comparable value became sugar the same morning — so what was missing was a *verb*, and a verb needs
    nowhere near the vocabulary a goal does. Anything richer here would be a question the reader could
    not answer.

    ⚠ **`by` keeps the vocabulary out of the machinery.** `where` walks `contains` and `when` reads `at`
    because those are conventions worth shipping as content, not because anything here knows what a
    container or a clock is. An author who keeps parts in `part_of` writes `by part_of` and the same
    traversal answers."""
    if words[0] == "by" and len(words) == 2:
        # ⚠ Validated HERE rather than when the answer is computed. `by ^` would otherwise author cleanly
        # and raise from inside `locate.where` at reading time, which is the wrong place to find out and
        # the wrong exception to get.
        P.parse_link(words[1].lstrip("^") or words[1])
        g.put(q, by=words[1])
    elif len(words) == 1:
        g.link(q, "about", resolve(g, words[0], under=under))
    else:
        raise Unreadable(f"line {lineno}: cannot read {line!r} — a question names ONE thing per line, "
                         f"or the word it walks (`by part_of`). It asks about what is there; it does not "
                         f"say anything about it")


def _step(g: Graph, m: str, words: list, line: str, lineno: int) -> None:
    """One `step …` line. ⭐ **The step grammar is the GOAL grammar with roles instead of names** — the
    only legal subjects are `subject` and `object`, meaning the matched constraint's. A method that named
    an individual would be about that individual and could not be reused, which is the same reason
    `types.py` refuses to let a schema name a target."""
    known_roles = ROLES + tuple(g.attr(d, "name") for d in M.draws_of(g, m))

    def role(w: str) -> str:
        if w not in known_roles:
            raise Unreadable(f"line {lineno}: {w!r} is not a role — a step may only speak of "
                             f"{' or '.join(known_roles)}, never a named individual. Draw a further role "
                             f"with `some <name> in <ref> by <link>` before using it")
        return w

    # ⭐ The SHARED proposition grammar (`_shape`) — a step is a subgoal, so it says the same things a
    # goal constraint says. What differs is only that a referring position holds a ROLE.
    shape = _shape(words, line, lineno, what="method step")
    if shape is None:
        raise _shape_refused(words, line, lineno, "method step", " — with roles, not names")
    kind = shape[0]
    if kind == "attr":
        who, key = _one_hop(shape[1], lineno, "method step")
        M.step(g, m, sort="attr", key=key, value=_literal(shape[3]), subject=role(who), note=line)
    elif kind == "type":
        M.step(g, m, sort="type", label=shape[2], subject=role(shape[1]), note=line)
    elif kind == "link":
        # ⚠ A step is something to ACHIEVE, and `l+` says *reachable at any depth* — which is a query, not
        # a thing to bring about: nothing names which edge to add. Refused with the reason.
        label, transitive = P.parse_link(shape[2])
        if transitive:
            raise Unreadable(f"line {lineno}: `{shape[2]}` asks about reach at any depth, which is a "
                             f"question rather than something a step can achieve — no single edge would "
                             f"make it true. Say the link a step actually establishes")
        M.step(g, m, sort="link", label=label, subject=role(shape[1]),
               object=role(shape[3]), note=line)
    else:
        raise Unreadable(f"line {lineno}: `{kind}` has no meaning as a step — a step is something to "
                         f"achieve, and `{'is there' if kind == 'exists' else 'known'}` is a condition")


def _method_line(g: Graph, m: str, words: list, line: str, lineno: int) -> None:
    if words[0] == "handles" and len(words) == 3:
        if words[1] not in ("link", "attr", "type"):
            raise Unreadable(f"line {lineno}: a method handles link, attr or type — not {words[1]!r}")
        g.put(m, handles=words[1], label=words[2])
    elif words[0] == "when" and len(words) == 2:
        g.put(m, when=words[1])
    elif words[0] == "within" and len(words) == 2:
        hits = [n for n in M.methods(g) if g.attr(n, "name") == words[1]]
        if len(hits) != 1:
            raise Unreadable(f"line {lineno}: {words[1]!r} names {len(hits)} methods; "
                             f"a method's context must be exactly one declared method")
        g.link(m, "within", hits[0])
    elif words[0] == "because" and len(words) > 1:
        g.put(m, because=" ".join(words[1:]))
    elif words[0] == "some" and len(words) == 6 and words[2] == "in" and words[4] == "by":
        # `some t in subject by test` — bind a FURTHER role, exactly as a criterion does. A method could
        # previously speak only of the matched constraint's `subject` and `object`, so a decomposition
        # whose steps concern a THIRD individual ("run its tests, then commit the repo") had no form —
        # the same gap `expert_judgement.md` §8f closed for criteria and left open here.
        name = words[1]
        if name in M.roles_of(g, m):
            raise Unreadable(f"line {lineno}: {name!r} is already a role of this method; a name cannot be "
                             f"drawn twice")
        label, back = words[5], words[5].startswith("^")
        M.draw(g, m, name=name, ref=words[3], label=label[1:] if back else label, back=back)
    elif words[0] == "step" and len(words) > 1:
        _step(g, m, words[1:], line, lineno)
    else:
        raise _shape_refused(words, line, lineno, "method")


_COUNTS = {"some": (1, None), "no": (0, 0), "a": (1, 1), "an": (1, 1), "one": (1, 1),
           "any": (0, None)}


def _count(words: list, lineno: int, line: str) -> tuple:
    """A count spec and the label it counts, from the words between `has` and the end of the phrase.

    ⚠ **A bare `has wheel` is REFUSED**, and the temptation to read it as "at least one" is exactly what a
    controlled language exists to resist: the author who wrote it may have meant one, or four, or any. The
    surface has a word for each of those, so it costs nothing to say which."""
    if len(words) >= 2:
        head, label = words[:-1], words[-1]
        if len(head) == 1 and head[0] in _COUNTS:
            return _COUNTS[head[0]] + (label,)
        if len(head) == 1 and re.fullmatch(r"\d+", head[0]):
            return int(head[0]), int(head[0]), label
        if len(head) == 3 and head[1] == "to" and all(re.fullmatch(r"\d+", h) for h in (head[0], head[2])):
            return int(head[0]), int(head[2]), label
        if len(head) == 3 and head[:2] == ["at", "least"] and re.fullmatch(r"\d+", head[2]):
            return int(head[2]), None, label
        if len(head) == 3 and head[:2] == ["at", "most"] and re.fullmatch(r"\d+", head[2]):
            return 0, int(head[2]), label
    raise Unreadable(f"line {lineno}: cannot read the count in {line!r} — a count is "
                     f"(n | n to m | at least n | at most n | some | no | a | any), and it is never "
                     f"left out")


def _type_line(g: Graph, t: str, words: list, line: str, lineno: int) -> None:
    """One line of a `type` block. Ordered most-specific first, so a keyword form is never shadowed.

    ⭐ **Both sides of a comparison are `path.py` references, so a demand may reach as deep as it likes.**
    That is the whole of what lifted the one-level limit at the surface: nothing here counts hops, and
    nothing here has its own idea of what a reference is."""
    if words and words[0] == "-":
        words = words[1:]                            # a bullet is punctuation, not vocabulary
    if not words:
        return
    is_ref = lambda w: P.is_reference(w)          # noqa: E731

    if words[:2] == ["is", "a"] and len(words) == 3:
        g.put(t, base=words[2])
    elif words[0] == "because" and len(words) > 1:
        g.put(t, because=" ".join(words[1:]))
    elif words[0] == "has":
        rest = words[1:]
        kind = type_ = None
        if "each" in rest:
            head, tail = rest[:rest.index("each")], rest[rest.index("each"):]
            if len(tail) == 3 and tail[1] in ("a", "an"):
                type_ = tail[2]
            elif len(tail) == 4 and tail[1:3] == ["of", "kind"]:
                kind = tail[3]
            else:
                raise Unreadable(f"line {lineno}: cannot read {' '.join(tail)!r} — what each target must "
                                 f"be is (each a TYPE | each of kind KIND)")
            rest = head
        lo, hi, label = _count(rest, lineno, line)
        # ⚠ **A `has` label is ONE named edge, not a reference**, and saying so out loud matters because
        # the two look alike. `has 1 ^contains` read `^contains` as a plain label and counted the targets
        # of an edge nobody has — silently zero, so the requirement was unmeetable and looked fine.
        # `require_edge` counts `g.targets(node, label)`; it does not navigate. Refuse rather than pretend.
        if P.is_reference(label) or label.startswith("^"):
            raise Unreadable(f"line {lineno}: `has` counts the targets of ONE named edge, and {label!r} is "
                             f"a reference. Depth belongs on a comparison line "
                             f"(`{label}.something == …`), which is navigated; a count is not")
        TY.require_edge(g, t, label, TY.Req(kind=kind, type=type_, lo=lo, hi=hi))
    elif len(words) == 5 and words[1] == "between" and words[3] == "and":
        _demand(g, t, words[0], "between", words[2], lineno, line, hi=words[4])
    elif len(words) == 4 and words[1:3] == ["is", "not"]:
        TY.require_relation(g, t, TY.Rel(words[0], "is not", words[3], True))
    elif len(words) == 3 and words[1] == "is":
        TY.require_relation(g, t, TY.Rel(words[0], "is", words[2], True))
    elif len(words) == 3 and words[1] in ("=",) + TY.VALUE_OPS:
        _demand(g, t, words[0], "==" if words[1] == "=" else words[1], words[2], lineno, line)
    else:
        raise _shape_refused(words, line, lineno, "type")


def _demand(g: Graph, t: str, left: str, op: str, right: str, lineno: int, line: str, hi=None) -> None:
    """⭐⭐ **The one place the surface decides ATTRIBUTE-OF-THIS-NODE versus RELATION-BETWEEN-TWO-PLACES**,
    and it decides it by reading the operands rather than by asking the graph.

    `weight between 800 and 2000` constrains *this* node's weight; `wheel[0].pressure == wheel[1].pressure`
    relates two places within the subgraph. A bare word on the left is a one-hop path — this node's own
    attribute — and a bare word on the right is a **literal**, so `colour = red` compares against the
    string. An author who means a reference on the right writes a hop (`colour = body.colour`). That rule
    lives in `path.is_reference`, once, so every block reads it identically."""
    try:
        P.parse(left)
    except P.BadPath as e:
        raise Unreadable(f"line {lineno}: {e} (in {line!r})") from None
    if not P.is_reference(left) and not P.is_reference(right):
        TY.require_value(g, t, left, TY.AttrReq(op, _literal(right),
                                                None if hi is None else _literal(hi)))
        return
    if op == "between":
        raise Unreadable(f"line {lineno}: `between` constrains one attribute of this node, so its left "
                         f"side is a bare key — {left!r} is a reference")
    ref = P.is_reference(right)
    TY.require_relation(g, t, TY.Rel(left, op, right if ref else _literal(right), ref))


def read(g: Graph, text: str, *, under: str = "root") -> tuple:
    """Parse one `<verb> <label>:` block. Returns `(verb, node)`. Raises `Unreadable`.

    **⭐ One block grammar, three families**, because the standing principle is that microfunctions ship
    with the engine and *everything a domain contributes is data*. Until this existed the border held for
    goals alone: a guideline or a method could only be authored by calling Python, which is exactly the
    "reach past the surface and write graph structure" the module docstring says must never happen. The
    principle was stated and unenforced.

    | verb | produces |
    |---|---|
    | `goal` / `ask` / `why` / `plan` | a **goal** — same body, different thing done with it |
    | `prefer` / `avoid` | a **guideline** — reorders, can never exclude |
    | `method` / `procedure` | a **method** — a decomposition, advisory or mandatory |
    | `type` | a **type** — a schema over a subgraph, of any depth |
    | `criterion` / `directive` | a **criterion** — expert judgement, naming an action with its arguments |
    | `what` / `where` / `when` | a **question** — a gap, answered by locating a thing in an order |

    ⚠ **`criterion` and `directive` differ ONLY in force, exactly as `method` and `procedure` do.** An
    advisory criterion suppresses enumeration but **defers** it, so being wrong costs imagined states; a
    directive says the alternatives are not worth building, and **refuses** when it recognises a situation
    it cannot act in. `deliberation.md` §3 in a third place: force is about *failure*.

    ⚠ **`method` and `procedure` differ ONLY in force, and that is the point.** The bodies are identical;
    what changes is what happens when a step does not work out — fall back to searching, or refuse to
    improvise. `deliberation.md` §3: force is about *failure*, not strength, and it cannot be inferred
    from content, so the surface makes the author say which word they mean.

    ⚠ **Refusal leaves nothing behind, now via the JOURNAL rather than by hand.** The old goal path dropped
    its constraints one by one on failure, which had to be kept in step with everything a body could mint —
    exactly the maintenance a transactional substrate exists to remove. `savepoint`/`rollback` is what the
    journal was built for, and this is its first real consumer outside `selftest.py`. ⚠ It is transactional
    only: nothing between the savepoint and the rollback may `commit`, and nothing here does."""
    lines = [(i + 1, ln.split("#")[0].rstrip())
             for i, ln in enumerate(text.splitlines())]
    lines = [(i, ln) for i, ln in lines if ln.strip()]
    if not lines:
        raise Unreadable("nothing to read")

    lineno, header = lines[0]
    m = re.fullmatch(r"(%s)\s+(.+?)\s*:" % "|".join(VERBS), header.strip())
    if not m:
        raise Unreadable(f"line {lineno}: expected `<verb> <label>:` with verb one of "
                         f"{', '.join(VERBS)}, got {header.strip()!r}")
    verb, label = m.group(1), m.group(2)

    sp = g.savepoint()
    try:
        node = _open(g, verb, label)
        for lineno, raw in lines[1:]:
            # ⚠ A SECOND BLOCK HEADER IS NOT A BAD BODY LINE, and reporting it as one blamed the wrong
            # thing: `feedback_from_harneskills` §2 measured `type b:` refused identically to
            # `frobnicate the widget`, though the corrective action is completely different — *"you
            # passed me two blocks and I take one"* versus *"that line has no form"*. The parser already
            # knows: a `<verb> <label>:` at zero indent is a header and never a body line.
            if not raw[:1].isspace() and re.fullmatch(r"(%s)\s+(.+?)\s*:" % "|".join(VERBS), raw.strip()):
                raise Unreadable(
                    f"line {lineno}: {raw.strip()!r} looks like a second block; `read` takes ONE block "
                    f"per call. Split the text on blank lines and call `read` for each.")
            _body(g, verb, node, raw.split(), raw.strip(), lineno, under)
        _seal(g, verb, node, label)
    except (Unreadable, P.BadPath) as e:
        # ⚠⚠ **A `BadPath` USED TO ESCAPE, and with it the whole no-half-built-goal guarantee.** A goal
        # line of three words is read as a link, so `a.size > b.size` reached `parse_link(">")`, which
        # raises `BadPath` — a different exception, uncaught, so the savepoint was never rolled back and
        # an EMPTY GOAL was left in the graph. Measured. The module docstring says a refusal leaves
        # nothing behind *because a half-built goal would be pursued and would look like it was working*;
        # that held for every refusal this border authored and not for one it merely passed through.
        # A reference that cannot be read IS unreadable here, so it is re-raised in this border's own
        # vocabulary and callers keep having exactly one exception type to catch.
        g.rollback(sp)
        msg = str(e) if "line " in str(e) else f"line {lineno}: {e}"
        # ⚠ **The subclass has to survive the re-wrap**, or §7's candidates are collected and then thrown
        # away one frame later. Caught by running the consumer's own repro rather than the unit — every
        # `except Unreadable` still catches this, since `Ambiguous` is one.
        if isinstance(e, Ambiguous):
            raise Ambiguous(msg, candidates=e.candidates, name=e.name) from None
        raise Unreadable(msg) from None
    return verb, node


def _open(g: Graph, verb: str, label: str) -> str:
    if verb in GOAL_VERBS:
        goal = G.open_goal(g, label=label)
        g.put(goal, verb=verb)
        return goal
    if verb in ADVICE_VERBS:
        return g.mint("guideline", stance=GL.PREFER if verb == "prefer" else GL.AVOID, label=label)
    if verb in READER_VERBS:
        # ⚠ A question node is minted for the same reason a goal is, and it is NOT the labelling error this
        # codebase keeps catching: *that this was asked* is not entailed by any structure, exactly as force
        # is not (`force-is-the-missing-axis`). What it must never hold is the ANSWER — see `locate.py`.
        return g.mint("question", verb=verb, label=label)
    if verb in CRITERION_VERBS:
        # ⚠ Two verbs, ONE body — the `method`/`procedure` pattern exactly, and for the same reason:
        # force is about FAILURE and cannot be inferred from content, so the author has to say the word.
        return CR.declare(g, label, force=(G.MANDATORY if verb == "directive" else G.ADVISORY))
    if verb in TYPE_VERBS:
        # ⚠ Refuses a REDECLARATION rather than minting a second type of the same name. Two would both
        # be found by `type_names` and `find_type` would answer with whichever came first — the same
        # "a name is not an identity" failure `resolve` refuses for individuals, one level up.
        if TY.find_type(g, label) is not None:
            raise Unreadable(f"{label!r} is already declared; a second declaration would not replace it, "
                             f"it would sit beside it")
        return TY.declare_type(g, label)
    return g.mint("method", name=label, handles="link", force=(G.MANDATORY if verb == "procedure"
                                                               else G.ADVISORY))


def _body(g: Graph, verb: str, node: str, words: list, line: str, lineno: int, under: str) -> None:
    if verb in GOAL_VERBS:
        _constrain(g, node, words, line, lineno, under)
    elif verb in READER_VERBS:
        _reader(g, node, words, line, lineno, under)
    elif verb in ADVICE_VERBS:
        _advise(g, node, words, line, lineno, under)
    elif verb in TYPE_VERBS:
        _type_line(g, node, words, line, lineno)
    elif verb in CRITERION_VERBS:
        _criterion_line(g, node, words, line, lineno, under)
    else:
        _method_line(g, node, words, line, lineno)


def _seal(g: Graph, verb: str, node: str, label: str) -> None:
    """⚠ **Every family refuses a body that says nothing**, and each needs its own closure fact — the
    generalisation `goal_machinery.md` §8 reached as *don't trust an open-ended absence without an explicit
    closure fact*. A guideline matching everything is not advice; a method with no steps decomposes into
    nothing, which `goal.decomposed` would then read as an undecomposed goal."""
    if verb in GOAL_VERBS:
        if not G.constraints(g, node):
            raise Unreadable(f"a {verb} with no constraints says nothing")
    elif verb in READER_VERBS:
        if not g.targets(node, "about"):
            raise Unreadable(f"`{verb} {label}` asks about nothing; a question needs something to be "
                             f"about (a `by` line on its own only says how to look)")
    elif verb in ADVICE_VERBS:
        if g.attr(node, "function") is None and g.target(node, "on") is None:
            raise Unreadable(f"`{verb} {label}` names neither an action nor a thing — advice that "
                             f"matches everything is not advice")
    elif verb in TYPE_VERBS:
        # ⚠ A type that demands nothing is satisfied by everything, so it is not recognition — the same
        # stance `types.type_names` and `subsumes` already take, enforced at the surface that authors one.
        # A bare `is a <base>` is enough: it demands whatever the base demands.
        if not (g.attr(node, "base") or TY.schema_of(g, label) or TY.attrs_of(g, label)
                or TY.rels_of(g, label)):
            raise Unreadable(f"`type {label}` demands nothing, so everything is one; "
                             f"that is not a type, it is a word")
    elif verb in CRITERION_VERBS:
        # ⚠ Both halves, and each is a different way of saying nothing. Without `wants` a criterion has
        # no variables and no index key; without `do` it recognises a situation and then declines to say
        # what to do about it, which is the one thing it exists for.
        if g.attr(node, "wants_sort") is None:
            raise Unreadable(f"`criterion {label}` never says what it keys on; a criterion without a "
                             f"`wants` line has no variables to speak of")
        if CR.action_of(g, node) is None:
            raise Unreadable(f"`criterion {label}` names no action; recognising a situation and not "
                             f"saying what to do in it is not judgement")
    elif not M.steps_of(g, node):
        raise Unreadable(f"`{verb} {label}` has no steps; it would decompose into nothing")


def read_goal(g: Graph, text: str, *, under: str = "root") -> str:
    """Parse a `goal …:` block. Refuses `ask` and `why` — a caller wanting one of those wants `read`."""
    sp = g.savepoint()
    verb, goal = read(g, text, under=under)
    if verb != "goal":
        g.rollback(sp)
        raise Unreadable(f"this is a {verb!r} block, not a goal; use `read` to take any of {VERBS}")
    return goal


def respond(g: Graph, text: str, thread: str, subject: str = "root", *,
            under: str = "root", keep: bool = True, **kw) -> str:
    """Read something said and do the right thing with it. The whole conversational surface, in one call.

    ⚠ **`ask` settles by default (`keep=True`), and that is a choice worth seeing.** The derivation ran on
    a workbench, so nothing is committed unless it is replayed; keeping it means the next question does not
    re-derive what this one worked out, and — the part that matters more — it is what gives `why` anything
    to answer from later. Pass `keep=False` for a question that should leave no trace.

    ⭐⭐ **`plan` is where the surface stops only describing and starts driving**, which is what this module
    was missing: every other verb either records something or asks something, and none of them could make
    the system *work*. It reaches `driver.pursue`, which is reachable at all because deliberation stopped
    being a closed Python loop (`HANDOFF.md` §5z).

    ⚠ **And it stops at a plan.** Nothing is carried out — the whole search is on a workbench, so a `plan`
    block cannot change the world no matter what it says. Acting is a separate verb that does not exist
    yet, on purpose."""
    from . import driver as D, query as Q, thread as T
    verb, goal = read(g, text, under=under)
    if verb in READER_VERBS:
        # ⚠ **Answered, never settled.** `ask` keeps what it derived because a derivation ran and costs a
        # search to repeat; a reader computed nothing that is not a traversal away, so keeping the answer
        # would be storing something that can drift from the world it describes (§6g, and `types.tag`).
        # The *question* reaches the thread — that it was asked is history — and the answer does not.
        T.attend(g, thread, goal, why="asked", note=verb)
        return "\n".join(L.describe(g, verb, n, by=g.attr(goal, "by"), under=under)
                         for n in g.targets(goal, "about"))
    if verb in TYPE_VERBS:
        return TY.describe(g, g.attr(goal, "name"))     # declaring is the whole of what a type block does
    if verb == "goal":
        return G.describe(g, goal)                 # pursuing is the caller's to schedule, not intake's
    if verb == "plan":
        return D.describe(g, D.pursue(g, goal, thread, subject, **kw))
    if verb == "why":
        return Q.account(g, goal, thread, subject)
    answer = Q.ask(g, goal, thread, subject, **kw)
    if keep and answer["verdict"] == Q.YES:
        Q.settle(g, answer, thread)
    return Q.describe(g, answer) + ("\n" + Q.explain(g, answer) if answer["proof"] else "")


def describe(g: Graph, goal: str) -> str:
    """Render a goal back to the surface it came from — the round trip a model reads to check itself.

    ⚠ **Refuses anything that is not a goal rather than rendering it badly.** Handed a guideline it would
    otherwise emit `goal <label>:` with an empty body — well-formed, wrong, and exactly the "best effort"
    this module exists to refuse. A round trip a model checks itself against must not be able to lie."""
    if g.kind(goal) == "question":
        # ⚠ A question round-trips to what was ASKED, never to what was answered. A rendering that included
        # the answer would read back as a block nobody wrote and could not be re-parsed to the same thing.
        lines = [f"{g.attr(goal, 'verb')} {g.attr(goal, 'label')}:"]
        if g.attr(goal, "by"):
            lines.append(f"    by {g.attr(goal, 'by')}")
        lines.extend(f"    {g.attr(n, 'label') or n}" for n in g.targets(goal, "about"))
        return "\n".join(lines)
    if g.kind(goal) != "goal":
        raise Unreadable(f"describe renders a goal; {goal} is a {g.kind(goal)}")
    lines = [f"{g.attr(goal, 'verb') or 'goal'} {g.attr(goal, 'label')}:"]
    lines.extend(f"    {G.describe_constraint(g, c)}" for c in G.constraints(g, goal))
    return "\n".join(lines)


__all__ = ["Unreadable", "VERBS", "GOAL_VERBS", "ADVICE_VERBS", "METHOD_VERBS", "TYPE_VERBS",
           "READER_VERBS", "ROLES",
           "resolve", "read", "read_goal", "respond", "describe"]
