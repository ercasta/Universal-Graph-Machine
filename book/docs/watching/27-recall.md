# What comes to mind

Before the machine can choose a rule, something has to hand it a set of rules to
choose from.

That step is called **recall**, and it is the most consequential *policy* in
the design — not a primitive. Against the actual floor (Chapter 30), match and
write are floor operations; arbitrate is only partly floor, since *totality*
is floor but *precedence* is a claim in the graph; and recall is **entirely
convention** — an index plus a policy. Calling recall a primitive would
obscure that it is a **choice**.

## Two layers share the job

**Recall is coarse.** It answers *which rules are live at all*. A rule claimed
`dormant` is skipped unless something has marked it `due`; a budget caps how
many rules are considered at once — and the cap may not starve a woken callback
or a `standing` rule, a carve-out you will meet again below.

> **Nothing derived narrows this step.** The cut is just a cut — nothing is
> ordered by preference before it happens.

**The table is fine.** Everything live gets a score — `standing` rules at the
apparatus's height, everything else at the floor — and the loop of Chapter 28
works the table from the top, taking the first rule that matches. Which rules
are *matched at all* is decided by the score; **attention on a thing**
(`attention(goblin1)` — an ordinary claim about a node, never about a rule)
lifts the rules that could be about it into the window.

The rest of this chapter is three laws that any such mechanism has to obey —
about the problem recall solves, not about the table that solves it today.

## Nothing came to mind is not nothing is left to do

Any selection worth having is **incomplete by design**. It may fail to surface
a rule that would have helped. That is an acceptable cost only if the failure
is distinguishable from the other kind:

> **Nothing came to mind is not nothing is left to do.**

A window that ran dry must **widen** — look further down the table, consider
more. A search that finished must escalate outward. They look identical from
the outside, and conflating them is how a reasoner starts claiming things it
hasn't earned. Without widening, a miss in the top of the table would deposit
*quiet* while work remained, the agent would give up on goals it could have
reached, and the trail would show a completed search that never ran.

## One thing it may never be incomplete about

There is one carve-out, and it is stated as a safety property:

> **Recall may be incomplete about what to do. It may not be incomplete about
> what you must not do.**

Prohibitions come off the selection path entirely: they are consulted on what a
rule concluded, never recalled. However narrow the window gets, a forbidden
conclusion is refused before it lands, on the record. Chapter 18.

## A selection trained on its own outputs narrows monotonically

Selection learns from outcomes — which rules, having been reached for,
actually helped. And there is a failure mode with a name:

> **Training a selection on its own accepted outputs narrows it
> monotonically.**

A rule that never gets into the window never gets a chance to be useful, so it
never earns a lesson, so it never gets into the window. The selection
contracts towards whatever it happened to like first, and nothing in the loop
can notice.

Which is why *widen when dry* is not politeness. It is the only thing keeping
the distribution honest.

## Doubt is a tie

> **Two rules are close when their scores differ by no more than the
> tolerance.** Confidence is a gap.

When two rules in the window are close, the loop does not secretly pick one:
the doubt is deposited as a fact — `close(<A>, <B>)` — and settling it is the
next move's business (Chapter 28). *The agent was unsure here* becomes a claim
with a trail rather than a coin flip nobody recorded.

And the measurement that most changed how this design thinks about what
selection is worth:

> **Experience has almost nothing to decide, because the apparatus wins most
> of the agent's choices — and permuting a dependency chain cannot shorten
> it.**

Most of what the loop does is forced. What learning can touch is the narrow
band where two genuinely different options are available, and that band is
smaller than it looks from outside.

!!! note "Deep dive: where the cost actually was"
    This project spent a while assuming selection was where the time went. It
    was not. Measured: the **read** was 86% of runtime on the fixture that
    mattered, and the fix was 67×. Selection was a rounding error next to it.

    > Measure before optimising. The named lever was 6% of the cost.

    And the second measurement, which is the one that reordered the roadmap:
    **an ideal selection saves nothing while the loop runs to quiescence.**
    Narrowing changes the order and nothing else, until there is a reason to
    stop.

    So: stopping first, then selection, then learning. Not the order anyone
    proposed.

## Callbacks are directed recall

An **occasion** is a fact the machinery deposits when something notable
happens. The table loop never matches everything, so it can only report what
it actually saw: `bounded(ticks)` (the run hit its limit still applying) and
`close(<a>, <b>)` (Chapter 28's doubt) — both genuinely deposited, both things
a corpus can key a callback on.

A corpus keys on one, and that is the first thing a corpus can say to this
step: *when this happens, think of me* — the `due` mark that recall's budget
may never starve.

> **A callback is directed recall, not invocation.** The woken rule still has
> to match, can still lose, and can still be dormant.

That distinction is the whole reason this is safe. A callback that *invoked*
would be control flow that owns the loop, which Chapter 25 spent its length
arguing against.

And a request can be **re-asked**, with a rule to govern when:

> **An occasion warrants a re-ask only if re-asking cannot produce one.**

Otherwise you have built a loop. Chapter 7 has the two-line demonstration.

---

**Next:** the score, the window, and the loop that works them.
[The table →](28-the-table.md)
