# KB: Facts and Passes

A Kb contains statements that must hold in our system.

syntax:
?x unbounded node - it references a node in the graph
<x> reference to a node in the expression

KB:
```
is_a(car, ?x) made_of(?x, wheel, wheel, wheel, wheel) # a car is made of four wheel

<a>=dancing(people), is_a(party, likely(<a>))  # <a> is a reference in CNL (not reference in subgraph)
<t> = implies(?a, ?b) | EVAL (<t>, ?a) | (?a, ?b, because(?a, <t>))   # the "behaviour" of the system. () is subgraph -> this makes the system "learn" a reusable pass for implies, always valid no matter what we are talking about.

causes(see(is_a(?x, dog),(is_a(?y,cat))), chase(?x,?y))  # this is a pure fact in the KB. 


is_rule(?x), is_rule(?y), by(?x, boss), by(?y, vice), overrides(?x, ?y) # rules by boss override rules by vice
is_rule(?x), is_rule(?y), overrides(?x, ?y)
SYNONIM override, overrides   # the two terms are treated as equal by the engine

answer(why(crossed(chicken,road)), because(get(chicken,other side)))

answer((imagine(on(?a,?b), on(?b,?c)), question_is(above(?a,?c))), yes ) # () is subgraph

transitive(?x), ?x(?a, ?b), ?x(?b,?c), ?x(?a, ?c)

```

From this my system can learn PASSES that COMPLETE the graph; if I MASK some part and try to find a pass that reconstructs it. E.g. mask the first part and try to find it back:

made_of(?x, wheel, wheel, wheel, wheel)

could lead to learn:

pass: [optional name] made_of(?x, wheel, wheel, wheel, wheel) {
    car = MINT "car"
    is_a = MINT "is_a"
    LINK is_a ?x
    LINK is_a car
}


this pass means that if there is a "made_of" node that connects to a given node (?x) and to 4 nodes "wheel", then we create a is_a node

a pass is a program expressed as data. The learning system uses delta and heuristics to find passes e.g. missing link -> add a link, missing node -> add a node.
The learning system runs all the passes it knows (it runs the EVAL ISA, that must do exactly that, it takes a parameter like ?x and runs the applicable rules by looking at what ?x is connected to, e.g. made_of, to find applicable passes), and checks the result. Note that passes are what describes the "open class", and they form a "web". A pass might "learn" to trigger other EVALS.

For optimization reasons the engine shall maintain an index (a web) of what passes are linked to others, the "connective" is the same terms. 

When a pass changes, potentially other passes might need to change to. This is what requires the "harmonization" process

"harmonization" is the process of replaying memories of the episodes and "finding" passes that match.

We can manually bootstrap the KB and then leverage harmonization





# Review findings

Recorded from a design session; see [addressability.md](addressability.md) for the wider argument. The
sketch above is kept verbatim because the reasoning trail is worth more than a tidy version.

## What already exists under other names

| here | what it already is |
|---|---|
| `pass: head { MINT/LINK }` | an `fn` with a `when` guard. Bodies are already data (`function.define` writes `instr` edges) |
| `EVAL(?x)` — "look at what ?x is connected to, find applicable passes" | `fn.select` + `INVOKE`. ⚠ **There is no `EVAL` opcode and there should not be one** — *decompose before believing something is primitive*. The one real delta is that `fn.select` dispatches on a **name** and this wants dispatch on a **pattern**, which is an index over guards, not a primitive |
| the pass-web index, "the connective is the same terms" | the maintained index `(relation, position, participant) → facts` in [facts-as-nodes.md](facts-as-nodes.md) §*Pattern matching becomes a join*. Standing policy: **index → measure → RETE only if a measurement demands it** |
| `overrides(?x,?y)`, boss beats vice | `precedence`, `by authority`, already authored data — and already **table-dispatched at zero dispatchers**, which is the model for moving machinery content into the KB |
| replay episodes and find matching passes | `application.py` + `compile_episode` / `generalise`, all built |

## ⚠ Three collisions

**1. ⚠⚠⚠ Masking teaches the CONVERSE, and the converse is a leak.** `is_a(car,?x) made_of(?x, wheel×4)`
masked in the reconstruction direction learns *anything with four wheels is a car*. A cart has four
wheels. The KB statement licensed one direction and the pass asserts the other — **a derivation with no
premise**, harmony criterion 1. This is not fatal: it is abduction, and abduction is fine *if it is marked
as abduction*. But the pass form as written has nowhere to record which statement licensed it or whether
the direction is deductive.

**2. A pass MINTs and LINKs, i.e. it ASSERTS — and a proposition is not an assertion.** Line 14 gets this
right (`because(?a, <t>)` is a residue); the learned pass at line 37 does not. Make `because` obligatory
in the pass form, and `ugm.leak`'s invariant generalises one level up: **every node a pass writes must be
attributable to the statement that licensed the pass.**

**3. "When a pass changes, other passes might need to change too" is a TMS.** Propagation along a
dependency web is what this codebase deleted twice and declined again under *no settling, no interning*.
[harmonization.md](harmonization.md) has the answer and this page should adopt it verbatim: **each offline
pass rebuilds from the episode record rather than patching the previous one** — re-derivation, not
message-passing, consistent with *extend ≡ rebuild*. Likewise saturation: passes that write derived facts
re-open invalidation unless the writes are attributed and live in **signed frame membership**.

## ⚠ Smaller, but real

* **`SYNONIM override, overrides`** is the collapse `harmonization.md` §*What must not happen* forbids —
  unconditional, unscoped equivalence between open-class terms. It is also a *morphological* variant,
  which is the **language layer** and must not be smuggled into semantics. A conditioned substitution is
  predicate dispatch, and it needs **slice 3** (guards over context of use), which is not built.
* **`made_of(?x, wheel, wheel, wheel, wheel)`** is a **count** claim wearing positional clothes — *one
  shape, several membership semantics*, inside a single fact. Related: **cardinality is a declared
  property of a relation, per position** (how many things can be on `b`; how many things `a` can be on —
  a wide block spans two supports), and it belongs on the relation node beside arity, ordered/unordered,
  transitivity and converse.
* **The `answer(...)` lines are a different kind of object.** A stored Q→A pair is a lookup table wearing
  a rule's clothes. If they are *supervision targets* for the masking (learning from denotations), say
  so — otherwise the KB becomes a memoised answer table.
* ⚠ **Reconstruction is the wrong acceptance gate.** It is representational — *can the system recover the
  text* — and the standing rule is behavioural: **would the agent act differently**. A pass that
  reconstructs the masked line and never changes a plan is bought and never spent.

## ✅ What is genuinely right here

* `transitive(?x), ?x(?a,?b), ?x(?b,?c) ⇒ ?x(?a,?c)` **looks second-order and is not** — under the hub
  encoding `?x` is the type member of a fact node. That is `then --is--> transitive` being exercised, and
  it is the strongest evidence in this document that the edges-as-nodes decision is right.
* `causes(see(is_a(?x,dog), is_a(?y,cat)), chase(?x,?y))` — nested facts three deep, **no new shape**.
  Exactly the property that decided (iv) over (iii).
* ⭐ **Masking is the cheapest instrument on the whole list.** `harmonization.md` §*The cheap probe that
  decides it* proposes blanking the address half of guards; this generalises it past guards to whole
  statements. **Run it before building anything.** ⭐ And mask a statement that supplies *machinery*
  content — an `overrides` fact — not only a world fact: if the learner recovers a ranking, "the machinery
  is KB-derived" stops being a preference and becomes measured.

## ⚠ The scope question this owes an answer to

[HANDOFF.md](HANDOFF.md)'s frame says **learning is not a requirement** — narrow domain, rules provided by
authors — and that demotion is load-bearing for the current plan. This page puts learning back at the
centre. The justification that survives is **not** *the system should learn*: it is **theory revision from
an authored seed**, which is behaviour-preserving improvement with the seed as reference, the
`_python_step` pattern one level up. *Bootstrap the KB manually and then leverage harmonization* is
already that; write the sentence down or the next session re-litigates it.

## ⭐ A pass should be a HUB, scored

The representation decision this page takes is *what is a pass*:

```
(A) a new construct: pattern head + MINT/LINK body        (as drafted above)
(B) an fn with a pattern guard                             (existing machinery)
(C) a fact node: pass(licensing_statement, guard, body, direction)
```

| | (A) new construct | (B) fn + guard | (C) pass as a hub |
|---|---|---|---|
| not leaking | ❌ asserts with no premise; direction unrecorded | ❌ same | ✅ the licensing statement is a member |
| not lossy | ❌ which statement taught it, and deduction-vs-abduction, both gone | ⚠ recoverable from the episode record, not from the pass | ✅ |
| readable | ⚠ data, but **B3**: operations-as-data is *write-only* | ⚠ same | ✅ a rule can ask *which passes are about time* |
| composable | ⚠ the pass-web indexes by shared term; nothing relates a pass to the category it serves | ⚠ same | ✅ |

⭐ A later session took this question fresh and went further — see [rules.md](rules.md), which drops
the pass as a knowledge object entirely: a rule is `connective(moment, moment)`, direction is a query
rather than a field, and a pass is a *compilation* (derived, cacheable, never authored).

**Write passes as (C), keep (B) as the execution mechanism, drop (A).** (C) costs nothing new — it is the
hub shape applied to operations — and it is the same move that promotes **B3** out of the seams.

# World model

We cannot work purely on symbols; the agent needs a world model that is compliant with the semantics in
the KB. ⭐ **But the engine already has one: the operator set plus the workbench.** `predicted_changes`
runs it forward, `deviates` compares it to reality, `unmet_expectations` says where it fell short — all
live. So the design question is not *what shape is a model*. It is **how does the model say *I don't know
what happens here* rather than silently saying *nothing happens*.**

## Partiality has one shape, and it is three axes

| axis | *"I don't know…"* | form today |
|---|---|---|
| **coverage** | …what happens in this situation at all | ❌ silence, indistinguishable from "nothing happens" |
| **precision** | …how much / how far / how long | ❌ nothing between a bound value and no value |
| **confidence** | …how firmly, and on whose word | ✅ force/deontic + `because` + discourse authority |

⭐⭐⭐ **All three take the same shape, which is already specified for another reason** —
[facts-as-nodes.md](facts-as-nodes.md) §*Frames*: **present / absent / no entry → UNKNOWN**. A *total*
model has an entry for every fact after every action; a **partial** model just does not, and the third
state is what makes the difference readable instead of silent. That is `unknown_is_not_no_unless_you_say_so`
extended from utterances to the world, and it is STRIPS's add/delete lists **plus the state STRIPS never
had**.

⚠ So the world model is blocked on the same item as `retract`, which is already the named next step.

## Not a map, and not code

The draft above offered *a map with hardcoded values* or *actual code*. Both fail the same way:

| | map | code | operators as passes, partiality declared |
|---|---|---|---|
| not leaking | ✅ trivially — any interpolation leaks silently | ⚠ walking and inventing indistinguishable | ✅ each prediction cites its operator |
| not lossy | ❌ no *why* | ❌ no residue | ✅ |
| readable | ⚠ data that says nothing about itself | ❌ **an island**, and it is matrix finding 1 verbatim: cause–effect authored in the engine's language | ✅ |
| composable | ❌ two maps cannot merge | ❌ | ✅ join over declared gaps |

⚠ **And *map to/from world model / graph language* is a translation** — which must commute with the
operations, not merely round-trip, and **a translation is an island with a bridge that appears in every
explanation crossing it**. Under the third column there is nothing to translate, because the model is in
the graph.

## The composition argument is the decisive one

Two models each silent about different things:

* silence means *nothing happens* → the composite is wrong in both places **and cannot say so**
* silence means *UNKNOWN* → composition is a join, and the gaps survive as gaps

That is conservative extension landing on the world model. **A model that is partial-by-silence is one you
can only ever have one of** — and cross-domain composition is requirement 2, not a nice-to-have.

## ⭐⭐⭐ And a gap is a WANT, not a refusal

When the model has no entry, the right outcome is a **subgoal** — *find out what `pour` does to `level`* —
closable by asking a person, deriving from the web, or **observing**, which is `deviates` in reverse. That
makes the partial model **self-extending through ordinary reasoning**, which is exactly the test
[comparison.md](comparison.md) sets for the whole claim.

An LLM's world model is total and confabulates at the edges. A model whose gaps are **addressable goals**
differs in kind, not in accuracy — and on the benchmark's own axes rather than the one where pretraining
wins.

## Two smaller shape decisions

* **Delta-producing, not state-producing.** An operator says *what changes*, never *what the world now
  is*, or every prediction is O(world) and the frame problem returns. Same shape as the frame it writes.
* ⭐ **"Compliant with the KB semantics" is checkable, and it is `deviates` pointed inward.** Today
  `deviates` compares prediction to *reality*; compliance compares prediction to the *KB* — every
  predicted fact expressible in KB vocabulary, none violating a KB constraint. Same machinery, second use,
  and the natural home for the harmony instrument at this level: **every fact a prediction adds must be
  attributable to the operator that predicted it.**

⚠ The one axis with no form at all is **precision** — *the level rises, by an unknown amount*. It wants
`attribute(tank, level, ?v)` with the value member constrained rather than bound, which is the same
unbuilt capability as the order core and `has 0 <label>`. Prior art if it is ever built as a KB rather
than a feature: qualitative physics (de Kleer, Forbus) — *the sign of the change is known, the magnitude
is not*.




