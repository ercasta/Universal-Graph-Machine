# Supposing

`likely(rain)` is a claim. It is not `rain`.

So an ordinary rule about rain — *if it rains, the streets get wet* — does not
apply to it. That's correct, and it's also a problem: nothing would ever follow
from anything hedged.

The answer is to **enter it**.

> **Unwrap on the way in. Re-wrap on the way out.**
>
> Inside the frame the assumption is an ordinary fact, and the ordinary rules
> apply to it by ordinary matching. What crosses back out is `likely(q)` — a
> claim about what was concluded under the supposition — never `q`.

## Watch it happen

```
rule <weather> = implies( { +cloudy(?d, morning) }, { +likely(rain(?d, afternoon)) } )
rule <cross>   = implies( { +likely(?p) },          { +suppose(?p, likely) } )
rule <wet>     = implies( { +rain(?d, ?t) },        { +wet(streets) } )

fact +cloudy(monday, morning)
```

```
why likely(wet(streets))?
  +likely(wet(streets)) @M0, licensed by concluded(frame(moment(), moment()))
    because +wet(streets) @M1, licensed by applied(<wet>)
    because +rain(monday, afternoon) @M1, licensed by supposing(rain(monday, afternoon))
```

Read the licences bottom-up. `supposing(rain(...))` — inside the frame, rain is
just true. `applied(<wet>)` — an ordinary rule, unchanged, with no idea it's
inside a hypothesis. `concluded(frame(...))` — and what comes back out is
`likely(wet(streets))`.

The corpus wrote three rules. None of them mentions frames, entering, leaving,
or lifting. `<wet>` didn't need a "hedged" twin.

**No rule needs a lifted twin.** That's the whole payoff of unwrapping: the
alternative — a version of every rule that handles `likely(p)` as well as `p` —
doubles a corpus and can't nest.

## Crossing is a decision, not a mechanism

`<cross>` above is an ordinary rule. That matters more than it looks.

The standing objection to supposition is combinatorial explosion: twenty
independently uncertain facts would be a million moments.

That objection doesn't survive the distinction between a frame per **subset**
and a frame per **derivation**.

> **Crossing `likely(p)` is one hypothesis, and more when something says so.**

Considering the *other* case is another ordinary rule. So there is **no
branching factor in the machinery to set** — the number of branches is however
many `suppose` facts get concluded, gated on whatever a corpus gates them on.

Why the default has to be one, stated as a cost rather than a preference: at one
branch per uncertain fact, what's spent is a frame per derivation, which is
linear. At two branches, *n* independent uncertainties give 2ⁿ combinations and
the objection returns intact.

> **The first branch is free and every branch after it is exponential.** Which is
> exactly why the second must be earned.

## Containment is free rather than enforced

Nothing prevents your imaginings from being mistaken for the world. Nothing
needs to.

The frame's seat is a **successor** of the caller's moment. So the caller's walk
— which goes backwards, towards the root — cannot reach it. Chapter 5's
at-or-before test is doing the work, and this is exactly why it has to be a real
ancestry test rather than a depth comparison: supposing forks by construction.

Measured on a chain forking 31 times: 129 structural conclusions, none of them
off its own walk. Nothing is refused to achieve it. A pattern that reaches
downward loads fine and finds nothing, exactly as a rule matching an entry
nobody wrote matches nothing.

> Nothing is prohibited; everything is stamped.

The one thing that is *not* in the chain, and therefore needs an explicit rule,
is **acting** — Chapter 14. Supposing something must not bring it about.

## Two things this costs, both found by building

**The alternative must be opened on resume.** If you propose the second case
alongside the first, it gets enacted while you're already *inside* the first —
so it becomes a sub-hypothesis rather than a sibling, and comes back wrapped in
the first.

`left(<frame>, <assumption>)` is the occasion for *this hypothesis is over*, and
opening the alternative there is what makes them siblings. That's what the frame
forest is for.

**A crossing rule that can match its own output runs away.** A discharged
conclusion is itself `likely(...)`, and a rule keyed on `left` fires again when
the alternative is left in turn. Measured: **32 sibling frames** before the
budget stopped it.

Chapter 3 records the same trap for negation translation. The corpus stops it,
and that it must is a property of self-applying rules rather than of any one
rule.

## The same construction, used for change

Supposition isn't only for uncertainty. Once you have *enter a moment, conclude,
come back out with a wrapper*, you have the machinery for counterfactuals,
for planning ahead, and for asking *what would happen if*.

They're all one thing: a moment whose licence says *I decided to suppose this*.

!!! note "Deep dive: superseded, not invalidated"
    A related question: when the world moves, what happens to what you derived
    from the old state?

    Nothing. And that's correct.

    > **A dated derived fact needs no invalidation.**

    At M7 the agent recognised something. At M12 the situation changed. The M7
    recognition is still true *of M7* — it was a correct reading of that moment
    — and the read (Chapter 5) simply prefers the later claim when asked about
    M12.

    Losing your reason is also not the same as acquiring a counter-reason. If
    the source that told you something is discredited, that does not make what
    it told you false; it leaves you **without a reason**, which is a different
    situation and calls for a different response. This design deposits
    `unsupported(p)` as an occasion and lets a corpus decide what to do about
    it, rather than deciding on the corpus's behalf.

---

**Next:** two rules, one situation, opposite conclusions.
[When two rules disagree →](17-disagreement.md)
