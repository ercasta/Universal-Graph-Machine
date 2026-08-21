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
  +likely(wet(streets)), licensed by concluded(frame(moment(), moment()))
    because +wet(streets), licensed by applied(<wet>)
    because +rain(monday, afternoon), licensed by supposing(rain(monday, afternoon))
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

## Containment is free rather than enforced — for entries

Nothing prevents your imaginings from being mistaken for the world. Nothing
needs to, as long as what you imagined is an **entry**.

The frame's seat is a **successor** of the caller's moment. So the caller's walk
— which goes backwards, towards the root — cannot reach it. Chapter 5's
at-or-before test is doing the work, and this is exactly why it has to be a real
ancestry test rather than a depth comparison: supposing forks by construction.

Measured on a chain forking 31 times: a structural member walking the chain from
an anchored moment made 129 conclusions, none of them off its own walk. Nothing
is refused to achieve it. A pattern that reaches downward loads fine and finds
nothing, exactly as a rule matching an entry nobody wrote matches nothing.

> Nothing is prohibited; everything is stamped.

Two things fall outside that, and they are outside it for the same reason —
neither is in the chain.

The first was designed for: **acting**, which needs an explicit rule, Chapter 14.
Supposing something must not bring it about.

The second was not, and the next section is the correction to what this chapter
used to claim.

## Structure is not contained at all

Containment holds for entries and fails for **structure** — the layer Chapter 31
calls stratum 0, where a conclusion is an interned relation instance rather than
an assertion: undated, unattributed, deniable by nothing, and belonging to no
moment.

Probed. `<said>` is stratum 0 — it lifts every claim anyone ever made into
structure, which is what buys a `−` member the meaning *for no `?x`* instead of
*somebody denied it* (Chapter 26). `<alarm>` reads that structure from
**outside** the hypothesis:

```
rule <said>  = implies( { asking(?s), anc(?s, ?d), in_delta(?d, ?e),
                          entry_of(?e, ?l, ?p, ?sg) },
                        { said(?p, ?sg) } )
rule <cross> = implies( { +likely(?p) }, { +suppose(?p, likely) } )
rule <leak>  = implies( { +rumour(?x) }, { +secret(?x) } )
rule <alarm> = implies( { said(secret(?x), plus), +awake(guard) },
                        { +alarm(?x) } )

fact +awake(guard)
fact +likely(rumour(a))
```

Run twice, identical but for whether `<cross>` is present — that is, whether the
agent ever supposes anything:

| | `secret(a)` at the root | `said(secret(a))` | `alarm(a)` at the root |
|---|---|---|---|
| no supposition | `None` | absent | `None` |
| supposing | `None` | **present** | **`+`** |

The first column is containment working: the hypothesis stayed a hypothesis, and
what came back out was `likely(secret(a))`. The third is the defect. Nobody
believed `secret(a)` and the guard was raised anyway.

> **A frame contains what it says. It does not contain what it derives about
> what it says.**

Ancestry cannot fix this, and that is the part worth understanding: the leak is
not in the read. The at-or-before test — `at_or_after` in the code — is consulted
when an **entry** is resolved. A structural fact is never resolved: it is
enumerated straight out of the argument index, which no more knows about moments
than a dictionary knows what time it is.

And it is worse than a wrong answer, because the wrong answer cannot be traced:

```
why alarm(a)?
  +alarm(a), licensed by applied(<alarm>)
    because +awake(guard), licensed by loaded(awake(guard))
```

`said(secret(a))` is the premise that made the difference and it is not in the
trail, because structure carries no licence — Chapter 9's whole apparatus is
about entries.

> **A leak with no licence cannot be found by asking why.** The trail names the
> one premise that was true anyway.

This is not a corner of the design. Negation as failure, counting, and reading
rules as facts all run on that layer, so the defect is under exactly the
constructions the rest of the book recommends.

**The same shape, refused elsewhere.** Adopting a rule inside a supposition is
refused (Chapter 29) because the rule set is one list shared by every frame, and
a rule adopted while supposing would apply after it. That is this defect with a
guard in front of it. The stratum-0 index is the same global table with no guard,
and the difference between the two is that somebody noticed the first one.

**The proposed answer is *situations*** — a design, not a build, and Chapter 34
files it where it belongs. Its move is to stop asking a read to keep hypotheses
apart and make them apart: a situation is a branch and a moment is a commit,
interning is per-situation, and a situation is materialised from its deltas when
a rule asks about it. A structural conclusion is not an entry, so it is not in a
delta, so it is never replayed — containment falls out rather than being enforced
on every read, and it covers structure because it never treated structure
specially in the first place.

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
