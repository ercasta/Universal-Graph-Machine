# Reflection — the machine as a description of itself

Two questions were asked a session apart and turned out to be one question from two sides.

> *The planning machine must be built purely out of rules, not prebuilt — an algorithmic description of
> how to proceed, which the engine literally executes. Some of those rules are non-verbal: they
> manipulate references rather than express actions.*

> *If the system learns its own rules for reading utterances, is there a controlled language at all?
> Are there two sets of rules, some innate and some learnable — or are they not really segregated?*

The first is about the machine, the second about the language, and the answer to both is the same: **one
substrate, a floor that is not rules, and a gradient of revisability in between.** There are no two
categories. What looks like a category is a *rate*, and this document ends with the rate measured.

## 1. The pattern has a name, and several

None of this is novel, which is the standing position of [comparison.md](comparison.md): *no feature here
is new; the claim is the residue.* Worth knowing what the neighbours are called.

| | |
|---|---|
| **Computational reflection** (Maes, 1987) | The general name, and its two halves are the useful cut: *introspection* — the system reads its own state — versus **intercession** — it changes its own behaviour. Everything this project has built is introspection. The claim above is intercession. |
| **Procedural reflection / the reflective tower** (B.C. Smith, 3-Lisp, 1982) | The interpreter's own state reified as ordinary data the program can manipulate, with an infinite tower of interpreters. The tower is infinite in theory and finite in practice, because levels are reified **on demand**. |
| **The vanilla meta-interpreter**, and **amalgamating language and metalanguage** (Bowen & Kowalski, 1982) | The sharpest match. In Prolog the entire proof procedure is three clauses *in Prolog*; extend them and proof trees, explanations and tracing fall out — the machine's own operation leaving the same residue as everything else. |
| **Meta-level KAs in PRS** (Georgeff & Lansky) | The planner's own decisions written as KAs in the same language as domain KAs. The claim, in the agent literature, in 1987. |
| **Soar's impasses** | A small fixed part decides *when* to go meta; productions do the rest. The shape to copy. |
| **The metaobject protocol** (Kiczales) | A language's dispatch and inheritance exposed as ordinary objects. `precedence.py` already is one, for rule arbitration. |

For the language half the tradition is equally direct — **Hobbs' *Interpretation as Abduction*** for
interpretation as inference rather than parsing, and **Construction Grammar** (Fillmore, Goldberg, Croft;
Steels' FCG for the computational one) for the rule form. Those are argued in
[comparison.md](comparison.md) §Language and are not repeated here.

⭐ **What would be this system's own** is narrower than any of them: in FCG the constructions are data but
the engine and the learning operators are Lisp. Here, a rule writes a rule — so the learner is itself a
rule, revisable, attributable, retractable, and *which construction was chosen and why it beat the
others* is residue. `rules/teach.mf` is that claim reduced to a check.

## 2. Non-verbal rules are the closed class

Rules that manipulate references without expressing an action already have a name here: they are the
**closed class** — the eight mediated names, the sorts, the consequent kinds. The linguistic parallel is
not decorative. Talmy's split between the closed-class *grammatical* subsystem, which encodes reference,
structure and perspective, and the open-class *lexical* one, which encodes content, is the same
distinction; and it predicts what we see, which is that the closed-class members look nothing like verbs.

What the framing adds is the *reason*: **the planning machine's own operations are structural**, so of
course they are closed-class. It is not a coincidence to be explained but a consequence.

## 3. Why "purely out of rules" needs a floor

A tower needs a bottom that **runs** rather than is described. Three things get called innate, and only
the first is a category of thing:

1. **The floor** — opcodes and natives. Innate because a description must terminate in execution. This is
   not a kind of rule; it is the absence of rule.
2. **The closed class** — perfectly expressible as rules. Not innate by nature: it is *what every other
   rule is written in terms of*.
3. **The termination condition** — see §5. Innate because without it, self-application does not bottom
   out.

So the honest form of *purely out of rules, not prebuilt* is: **nothing above the horizon is prebuilt,
and the horizon is declared.** Which is already the position in [concepts.md](concepts.md) — a primitive
is admissible only if every decision it embodies can be an argument.

## 4. The closed class is closed by answerers, not by prohibition

This is the hinge, and it is what dissolves the innate/learnable split.

Nothing stops a rule *right now* from building a constraint with `sort="mysort"`. It would build fine.
It would **mean nothing**, because `holds` dispatches on sort and has no branch for it — which is this
project's own recorded failure mode, *a tag with nothing that runs it is worse than no form*.

So the closed class is not a list that forbids the rest. It is closed because **every member has an
answerer**. Extending it is not prohibited; it is expensive in a specific and measurable way: **you must
supply the answerer too.** And an answerer is a rule.

⭐ **That makes the closed class learnable in principle and rare in practice — a rate, not a kind.** It
also predicts the mechanism, and the mechanism has a name: **grammaticalization** (Meillet; Hopper &
Traugott). In natural language, open-class items *become* closed-class over time — *going to* becomes a
future marker. The classes are not segregated; they are a gradient with a direction. Goldberg's central
claim in Construction Grammar is the same collapse: no principled line between grammar and lexicon, only
a continuum from substantive idioms to schematic argument structures.

⚠ **One real asymmetry survives, and it is a bootstrapping constraint rather than a category.** A new way
of *saying* something can be learned from a single example, because there is somewhere to put it. A new
*sort* cannot be learned from an example of someone using it, because there would be nothing to represent
the example **in**. Same reason a child acquires a noun in one exposure but not a new grammatical case.
That is the whole of what "innate" honestly means here: not a protected set, but the fact that the
vocabulary you interpret *into* cannot be acquired by interpretation alone.

## 5. The self-application regress, and the floor that is already in the code

When `rank` becomes a rule — that is **P3** — selecting which `rank` applies requires ranking. Every
reflective architecture meets this and answers with a fixed floor: Soar's architecture decides when to go
meta, PRS puts meta-KAs above a default that always decides.

⭐ **This codebase already has that floor and had not noticed.** `precedence.seal_rule` refuses a
tie-break rule whose last stage is not total:

> *the last stage must decide every pair … or two rules sit in an order nobody chose.*

Read at P3, that stops being a nicety about ordering and becomes **the stratification condition**: a base
level that always decides, so the tower terminates. `add_stage` already refuses to let a *function* stage
sit last, on the grounds that its totality cannot be shown — which is exactly the property a learned
`rank` will not have. Write the argument down before building P3.

## 6. The gradient, measured

`python -m ugm.horizon`. For each closed set: how many places switch on **what that set is** — which is
what it would cost to change it. The unit is a **dispatcher**, defined so it can be derived rather than
judged: *a function naming two or more members of one set is switching on that set*.

| closed set | dispatchers | members | declared at |
|---|---|---|---|
| constraint sort | **17** | 4 | `goal.WORLD_SORTS` |
| access vocabulary | **9** — all in the *surface* | 8 | `access.VOCABULARY` |
| consequent kind | 3 | 4 | `consequent.KINDS` |
| goal force | 3 | 2 | `goal.FORCES` |
| plan sort | 2 | 3 | `goal.PLAN_SORTS` |
| precedence stage | **0** | 4 | `precedence.STAGES` |
| strength | **0** | 3 | `precedence.STRENGTHS` |

**Nothing is forbidden; things are expensive.** A fifth constraint sort costs seventeen dispatchers. A
fifth precedence stage costs one table entry and one comparator. Same word, two orders of magnitude
apart.

⭐⭐ **The cheap end is not an accident — it is where work has already been done, and that gives the
migration a mechanism.** The two zero-cost sets are exactly the two this project already moved above the
horizon, by making the ranking authored data dispatched through a **table** (`precedence._COMPARE`)
rather than a switch. Nothing switches on them because *the switch is itself data*. So:

> **A closed set becomes revisable when its dispatch becomes a lookup keyed by the member.**

That is grammaticalization as an engineering operation, and it has happened here twice without anyone
calling it that. It is also the concrete instruction for making any other set revisable.

⚠ **The dearest set was the one nobody had declared.** `goal.WORLD_SORTS` did not exist until this
measurement asked for it; what stood in was `intake._SORTS` — private to the parser, restated as a
literal at a second site, and **missing `known`**. *A closed class earns its place by being declared*,
arriving as a measurement rather than as advice: an undeclared class is precisely what accretes switches,
because there is nothing to consult and nothing for a check to hold it to. Note the corollary the same
line exposes — **the parser accepts a strict subset of what the representation supports**, so there is a
sort a rule can build and the front door cannot say.

⚠ And one connection between the arcs: **4 of the 17 constraint-sort dispatchers are `intake`**. Dropping
the parser would itself cut the most expensive set by nearly a quarter.

## 7. What follows

* **P3 must open with the stratification argument** (§5), not close with it.
* **The gradient is a progress measure, not a curiosity.** `python -m ugm.horizon` beside
  `python -m ugm.reach`: one says what a rule can *start*, the other what it would cost to *change*.
  Both should fall.
* **The next set to move is the constraint sorts**, and the mechanism is known rather than open — turn
  the seventeen switches into a lookup keyed by the sort, so a sort carries its own answerer. That is the
  same move `precedence` already made, and it is what would let an interpretation introduce a sort
  instead of only choosing among four.
* ⚠ **This is measurement, not achievement.** The system does not revise its own closed class today, and
  nothing here claims it does. What has changed is that the question *how far is it from doing so* has a
  number instead of an opinion.
