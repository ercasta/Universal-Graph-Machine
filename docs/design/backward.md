# `backward.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Backward reading, as rules -- and what deleting the phase changed (§5, §18).

Goal expansion was the last interpreter phase. It is gone (`nophases`), and what
replaced it ships in the bundle: `<ask-fit>`, `<plan>`, `<expand>`, `<ask-check>`,
`<give-up>`, over three requests the machinery answers at the write.

    python -m ugm.probes.backward

This file used to *compare the two readers*, and that comparison is the reason
the phase could go, so the result is kept here rather than deleted with it:

    by the phase    28 facts
    by rules        29 facts

    RULES ONLY      achieved(water(kettle))

**The phase starved forward reasoning.** It ran ahead of recall and returned
early, so while any goal was unexpanded no ordinary rule could apply.
`water(kettle)` is derivable forwards from this corpus, and the phase judged it
unsatisfied because it had not let anything derive it yet. That is not a
disagreement about backward reading -- it is a precedence claim that had been
written in control flow, where §18 says nothing can see it or override it.

**That extra fact is not reproduced by this run, and the reason is a second
finding.** Backward reading now ships in the bundle, so it is authored *before*
the corpus rather than after, and `<ask-check>` reaches `water(kettle)` earlier --
before anything has derived it. It answers `unmet`, and nothing ever asks again:
a request is a fact, so **a request can only be made once**. Quiescence stops the
re-ask (`+check` is already written, so re-concluding it changes nothing).

So the phase's starvation was real and its repair is not automatic. What the
rules gain is that the timing is now a corpus's to fix -- a rule may re-ask under
a fresh request node -- where under the phase it was not expressible at all.
`ugm.backward`'s original 29th fact is therefore recorded here as a *claim about
the phase*, not as a current output.

 **The re-ask now exists** (`again(<request>, <occasion>)`, §13) and this run
still does not use one, deliberately: what it measures is the replacement on its
own, and a corpus rule that recovers the fact would measure the corpus. The
`a_request_can_be_re_asked` checks in `ugm.selftest` are where the recovery is
shown, on a fixture built for it.

What the run measures now is the replacement, on its own: does it reach the plan,
and is every one of the five rules load-bearing? The second half is not optional.
Three checks in this project reported success while unable to fail, and the one
that caught them each time was **delete each rule of the thing you are checking,
one at a time, and report any rule the fixture cannot kill.**

What the request has to return was the finding that made any of it possible. The
obvious design -- answer with a yes and a binding -- does not work, and not for
an implementation reason: a binding is a map from variables to nodes, and a rule
cannot hold one, let alone apply it. So the answer arrives already instantiated:

    +fits(<R>, goal)             it could
    +need(<R>, goal, <subgoal>)  one per antecedent member, already substituted

> **Match and substitute travel together, because the caller cannot do the
> second half.**

And the last verdict cannot be a rule at all. The natural sixth rule is

    implies( {+goal($w), +unfit($r, $w)}, {+blocked($w)} )

and it is wrong: it fires when **some** rule does not fit, while `blocked` claims
that **no** rule does -- an aggregate over a *finished* search. A `-` member
cannot say it either (§9's `-` is *an entry denies this*, never *for no `$r`*).
So `blocked` is answered by the machinery, to a `+verdict($w)` request that
`<give-up>` makes at `quiet` -- when the search that the aggregate is over has
actually finished.

## §18's silent failure, made reachable: tap($t)

§18's silent failure, made reachable: `tap($t)` is satisfiable by
`sink`, `under(kettle, $t)` only by `drain`. Checked independently both
report achieved and the plan is wrong with nothing saying so.

⭐⭐⭐ **And the report now NAMES the tap the plan committed to.** This
check wanted `blocked(under(kettle, $t))` and gets
`blocked(under(kettle, sink))`, which is the same finding with the
reason in it: not *something about `under` failed* but *the plan chose
`sink`, and the kettle is not under `sink`*. A foreign corpus
(`docs/quest-feedback.md` §1) reported the generic form as unutterable
-- §14 refuses to dispatch a generic intent -- so an agent could not say
what it was stuck on. The binding was always known and recorded as
`binds(plan, $t, sink)`; it was simply not read back when the verdict
was written. Asserting the instantiated form makes this check stronger:
it now fails if the reason disappears again.
