# Blocked, and what silence means

```
fact +recall(freezing(kettle))
```

```
recalled(<boil>, freezing(kettle)): not believed
```

Ask what could produce `freezing(kettle)` and get nothing back. That's a
report about **recall** — nothing in this corpus's bucket for `freezing`
concludes it — and it's easy to over-read.

It does not mean *there is no way to freeze a kettle*. It means *nothing this
corpus's rules claim to do would*.

## `blocked` was designed, and it isn't shipped

An earlier version of this chapter described `blocked` as a fact the machine
deposits when a full backward search — expand a goal, recall candidates,
check each — exhausts every option. That search isn't built (Chapter 12), so
neither is `blocked`, nor `verdict`, nor a `quiet` fact a rule could read.
`grep`ping the engine for any of the three returns nothing. What follows is
the argument for why `blocked`, if it existed, would have to be a *reported
state* and not an ordinary conclusion — kept because the argument still
applies to whatever plays that role once backward search is built, and
because getting this wrong is a real way to make a reasoner overclaim.

Here's the natural-looking rule, and it's wrong regardless of whether
`blocked` ever ships:

```
implies( { +goal($w), +unfit($r, $w) }, { +blocked($w) } )
```

That would fire when **some** rule doesn't fit. What `blocked` is supposed to
claim is that **no** rule does. That's an aggregate over a *finished* search,
and an ordinary positive rule can't state it — a rule matches per-entry, not
over a set, which is the exact same limit that makes `delta` a tool instead
of a rule (Chapter 12). Nor does a `−` member help: *an entry says this does
not hold* and *no entry* are neither of them *for no `$r`*.

> **Bounded expansion would return a result and a state. `blocked` would be
> the state, not a belief a rule derived.**

## What actually exists to be silent about

Two pieces of this chapter's argument are real today, and worth keeping
apart precisely because the machine will not tell you which one you're
looking at.

**Recall returning nothing.** `recalled(<boil>, freezing(kettle))` above is
`not believed` because nothing was ever written that says otherwise — silence
means *unchanged*, never *false* (Chapter 3), and recall is no exception.
This is a report about *this corpus's rules*, not about freezing.

**Quiescence.** The run itself ends in one of two states, and only one of
them means *nothing more to try*:

```
fact +a
rule <r> = implies( { +a, no b }, { +b } )
```

```
2 ticks, ended quiescent
```

`quiescent` means the match set was genuinely empty — no rule, on any
binding, had anything left to write. That's a fact about the *search*, not
about the corpus's beliefs, and it's the nearest thing today to what
`blocked` was reaching for: an honest report that this run, right now, is
out of moves.

| silence | means |
|---|---|
| no entry for a proposition | **unchanged** — inherit from before (Chapter 3) |
| recall returns nothing | nothing in this corpus claims to produce it |
| the run ends `quiescent` | nothing anywhere had anything left to write |
| a write believed already | **silent by construction** — no new step at all |

That last row is the dangerous one. Matching returning nothing is observable.
A write refusing is observable. *This would change nothing* looks
indistinguishable from *there was nothing to apply* unless you check — and in
this engine it currently is **not** silent: a rule that re-derives an
already-believed fact still counts as an application, and a run only reaches
`quiescent` once nothing matches at all. Every guarded example in this book
(`no boiling($w)`, `no goal($p)`) exists to make the match itself go away
once satisfied, because the write staying silent isn't something you can
lean on.

## `bounded(ticks)` is real, and worth building on

One occasion in this family *is* a deposited fact a corpus can key on: a run
that hits its tick limit while still working writes `bounded(ticks)`.

```
fact +a
rule <loop> = implies( { +a, no b }, { +b } )
rule <unloop> = implies( { +b }, { -b } )

rule <panic> = implies(
  { +bounded(ticks), no diagnosing(myself) }, { +diagnosing(myself) } )
fact +lane(<panic>, watchdog)
```

Run this once to its limit and `<panic>` does **not** fire — the tick that
deposits `bounded(ticks)` is the last tick there is; nothing runs after it in
that call. Call `run` again on the same machine, and now it does:

```
first run:  15 ticks, ended applied (stopped at the tick limit)
second run: <panic> applies on its second step
diagnosing(myself): believed
```

Two things had to be true for that. `bounded(ticks)` had to survive between
calls — it does, because it's an ordinary belief, not a per-run flag. And
`<panic>` had to be on its own lane (`fact +lane(<panic>, watchdog)`) —
without one it competes for the single per-tick slot against `<loop>` and
`<unloop>`, which were winning every time. A watchdog that shares the main
lane with the thing it watches can starve; a lane gives it a guaranteed turn
regardless (Chapter 9's mechanism, `ugm/rules/circuit_breaker.ugm` for a
worked pattern). *A run is still working when it's cut off* is knowable and
actionable today; *the search is done and found nothing* is designed and
isn't yet.

## Stopping with a goal still open

There's a stronger claim in the same family, and it constrains Chapter 26
whether or not backward search exists yet:

> **The loop may end. It may not end quietly on something it was asked for.**

`horizon/34-not-built.md` is blunt about where this stands: *the open-goal
veto is not expressible in the table loop*. The shipped loop stops on a
rule's `stop`, and can't refuse to on its own, because the refusal would be
an aggregate — *nothing else is wanted and unmet* — over the very set of
matches a rule can't speak about. So today an open goal is a fact a corpus
can check after the run (`m.holds(...)`), not a veto the loop enforces for
you. Whether that gap gets closed is an open design question, not a solved
one dressed up as unsolved.

---

**Next:** the machine has a rule it could apply and a real reason to. What
does *doing* it actually mean here?
[Acting →](14-acting.md)
