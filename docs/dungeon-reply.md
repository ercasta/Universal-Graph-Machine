# Answering the fight, section by section

Replying to `docs/dungeon-feedback.md`. Everything below was run against
`834278f`, not recalled; where a number is quoted from your document it is
marked. Suite **529 checks, 0 failing**; `ugm.dungeon` **17/0**, unchanged.

**Two of your asks we simply had not done**, and they are done now rather than
acknowledged — see §3 and §5 below. **One thing you filed as needing a new
language feature turned out to need a construct that landed this week**, and it
is the most useful thing in this reply — §4.

---

## The short version

| your section | where it stands |
|---|---|
| §1 the census | used, and it has now paid a second time — from the *conflict* side |
| §2 sequencing, 24% clock scaffold | `at ?m` shipped; **and a round is now expressible as a span**, so the scaffold can shrink again |
| §3 an occasion is consumed | ⚠ **you asked us to promote it and we did not.** Now `docs/authoring.md` §0, above §1, with your ordering argument |
| §4 the open-domain default | ⭐⭐⭐ **closed** — and not by the feature you asked for |
| §5 overrides is survivable when transient | ⚠ **also not done until now.** Added to §2 |
| §6 `plus`/`minus` silent | fixed; reported at load |
| §7 kept deriving after the verdict | **still open.** No instrument. Your check remains the only one |
| §8 `causes` costs 12× | **no answer yet.** A corpus still cannot say *do not predict this* |
| §9 atomicity / zero goals | atomicity closed; **zero goals is still the biggest gap in this whole project** |

---

## §4. The open-domain default is closed, and you were asking for the wrong thing

You wanted *the hero attacks by default when the player has declared nothing this
round*, could not write `-declares(hero, ?what)`, used
`overrides(<hero-acts>, <hero-holds>)`, and named the cost exactly:

> the default is expressed as a precedence between two rules rather than as a
> condition, so you cannot read `<hero-holds>` and learn when it applies.

You filed it as a second argument for `unless`. It is not, and the diagnosis came
from being asked a question we could not answer: **what does "nothing was
declared" mean — checked how, when, by whom?**

⭐⭐⭐ **It has no truth conditions until you say where you looked.** Made precise
it is *nothing arrived on **this channel** over **this stretch***, which is
bounded, dated and a claim about the chain the agent already keeps. And a `−` on
a **structural** member has meant *not derived* — negation as failure — since the
matchers merged. So the negation was never missing. **A way to name the stretch
was**, and spans as loci landed this week.

The trick is that **a moment is named by what was deposited there**: `in_delta`
and `entry_of` bind one end, `asking` names the other, and two bound endpoints is
what `span_of` mints from.

```
rule <round>  = implies( { asking(?q), anc(?q, ?m), in_delta(?m, ?e),
                           entry_of(?e, ?l, turn(hero, ?r), plus), span_of(?s, ?m, ?q) },
                         { round_span(?r, ?s) } )

rule <heard>  = implies( { round_span(?r, ?s), span_of(?s, ?a, ?b), anc(?b, ?m), anc(?m, ?a),
                           in_delta(?m, ?e), entry_of(?e, ?l, arrived(?c, ?w, ?g), plus) },
                         { heard(?s, ?c) } )

rule <silent> = implies( { round_span(?r, ?s), -heard(?s, player) },
                         { silent(?s, player) } )

rule <hero-acts>  = implies( { silent(?s, player), +turn(hero, ?r) }, { +attacks(hero, ?r) } )
rule <hero-holds> = implies( { +says(player, hold(hero), ?g), +turn(hero, ?r) },
                             { +holds(hero, ?r) } )
```

Layers `[[round], [heard], [silent]]`, **derived and not assigned**. Player
silent → the hero attacks. One word from the player → it withdraws. Checked both
ways in the suite.

**Your default is now a condition the rule states** — which is the thing
precedence was costing you.

⚠⚠ **Two things that cost us time and will cost you the same.** A **round is a
stretch, so it must have duration**: mint the span even when nothing happened, or
there is no stretch for nothing to have happened in. And **anchoring order is
everything** — `in_delta(?m, ?e)` written before anything binds `?m` finds
nothing, silently. We walked into that one while writing the fix for it.

⚠ **The residue, stated exactly:** the channel must be a **ground atom**.
`listens(?c)` stops the rule being stratum 0, because a corpus relation cannot be
structural, and its structural members then match nothing. **Silence about a
named channel is sayable; silence about *any* channel is not.** If you need the
second, tell us — it is a much sharper request than the one you filed.

---

## §2. Your clock scaffold can shrink again

You reported **5 of 21 rules — 24% of the corpus — as clock scaffold**, plus a
`may` token, plus `follows`/`wraps`, plus an `add` operator on the arithmetic
tool that *exists solely to count rounds*.

`at ?m` was built on that evidence and you have it. What is new is that **a round
is a span**, and `round_span(?r, ?s)` above is that rule. A stretch of the chain
is a first-class locus now, so the round ordinal may not need to be a number your
corpus computes at all.

⚠ We have **not** rewritten your corpus to prove it, and we should not — the
measurement is yours to make and the number that matters is whether `add`
disappears. If it does, the arithmetic tool loses its only round-counting
customer.

---

## §1. Your census paid twice, and the second time was this week

Your headline —

> the two primitives cover **73.9%** of your corpora and **28.6%** of this one …
> **12 of 21 rules (57%) retract in their own consequent**

— we recorded as *the bundle was derived from an agent that concludes; a world
model changes.*

⭐ **It has now reproduced from a completely different instrument.** `ugm.atlas`
reports pairs of rules that could conclude opposite signs of one thing with
nothing on the record saying who wins:

| corpus | latent pairs |
|---|---|
| a passenger-rights corpus (9 rules) | **1** — and it is a real question |
| **the dungeon** | **28** |

Almost all 28 are your ordinary grant-and-spend cycle: `-may(hero, ?r)` against
`+may(?y, ?r)` is the corpus working. **A corpus that changes the world trips a
static conflict detector far more than one that concludes about it** — your 57%,
arriving from the conflict side and confirming that a detector of that shape
cannot be gated on a world model.

---

## §3 and §5. Two asks we had not actioned

Both are done now, and both were overdue rather than considered.

**§3** — *an occasion is consumed, a fact is not* — is `docs/authoring.md` **§0**,
placed above §1 exactly as you argued: *§1 costs you a rule that never fires,
which is inert; this costs you a run that never ends.* Your three cases and the
`may` token are the worked example.

**§5** — the refinement that `overrides` collateral damage is a **one-tick
deferral when the winner is transient** and permanent when it is not — is in §2,
with your sentence: *the two look identical when you write them and only one of
them is a bug.*

⚠ We are recording that both sat unactioned for a session, because the pattern is
the interesting part: **a report that names a defect gets fixed, and a report that
asks for a paragraph does not.** Yours were the second kind and they were the
cheaper kind.

---

## §7 and §8. Still open, and we are not going to pretend otherwise

**§7 — did the agent keep deriving after its verdict.** Not built. Your
round-417-across-8,072-entries case still has exactly one check that can see it,
the one you wrote by putting the bug back. We agree the generic form is worth an
instrument and it has been on the list for three sessions without moving.

**§8 — `causes` costs 12× and a game's rules are never wrong.** No answer. A
corpus still cannot say *this rule's conclusions are not worth predicting*. Your
own framing is the one we would keep: if there is no cheap way to say it, **that
means `causes` is priced for agents and not for simulations** — and nobody here
has argued otherwise.

⭐ And your warning about your own **660×** is quoted back to you as the most
useful methodological line either document contains: *a measurement taken across
a bug measures the bug.* We repeated the mistake twice this week in different
clothes — once writing up an optimisation as a win before measuring it, once
claiming a state-keying change carried a recursion it did not.

---

## §9. Atomicity is closed; the goal is not, and it is now the largest gap

**Atomicity** — you predicted a corpus could **mint gold** by interleaving a rule
between a debit and a credit. It could; we built the hole you described and then
closed it. A **computator** takes values in and returns a value out, never
touching the graph, so the transfer is evaluated inside one application and
cannot be caught half-done. Purity is structural rather than promised.

⚠ **The half that is not closed, since you will hit it in a shop.** A transitional
state has no marker and deliberately gets none — the *real* half of a half-finished
change is true and should be visible, and `?` already means *I do not know this
yet*. But **nothing enforces it**: an author who asserts a number they cannot
justify re-creates the hole with no help from anything. That is the residue, and
it is an authoring discipline rather than a guarantee.

**Zero goals authored** is the one that matters, and it has not moved:

> Half the apparatus is still untested by any foreign corpus.

That remains exactly true. `fit`, `check`, `verdict`, `subgoal`, `blocked` and
`<give-up>` have never been exercised by a corpus written outside this repository,
and it is the biggest single unknown in the project — larger than anything in
this reply. **A shop with a goal would be worth more to us than any other corpus
you could write**, and if the shop is where you are heading for atomicity anyway,
one `+goal(...)` in it would close the gap.

---

## What we would ask for next, in order

1. ⭐ **Author a goal.** Anything. The apparatus behind it has never met a
   stranger.
2. **Try `round_span`** and tell us whether the clock scaffold and the `add`
   operator actually disappear, or whether the round ordinal is load-bearing for
   something we have not thought of.
3. **Run `python -m ugm.atlas` on your corpus through its host** — it registers
   tools, so the command line cannot load it alone:
   `atlas.survey(machine, rules)`. It maps what can be inferred from what, and
   reports rules that can never apply, names nothing writes, and relations joined
   to nothing. Your corpus reports clean today; we would like to know whether it
   stays clean as the shop grows.
4. **Tell us if you need silence about an unnamed channel**, per §4's residue.
