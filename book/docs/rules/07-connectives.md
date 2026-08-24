# The one connective, and the one that didn't survive

```
rule <weather> = implies( { +cloudy($d, morning), no likely(rain($d, afternoon)) },
                          { +likely(rain($d, afternoon)) } )
```

There is one connective. It used to be two, and this chapter used to be about
the test that kept both. Run the second one now and here is what happens:

```
rule <boil> = causes( { +heat($a, $w), +water($w) }, { +boiling($w) } )
```

```
$ python -m ugm boil.ugm
ugm.core.text.ParseError: line 1: 'causes' is not a connective. There is one
-- `implies` -- and a second earns its place only by licensing a different
(forward, backward) reading pair. `causes` did not: all it did was land its
conclusion in a later moment, and there are no moments.
```

That message is the whole obituary. `causes` meant *this lands one moment
later than its antecedent*. Once the chain of moments went (this book's Part
1), there was nowhere later left to land — so `causes` had nothing left to
mean, and the loader says so instead of accepting a word that no longer names
anything.

## What the second connective bought, and why it's gone rather than merged

The old test for keeping a connective was: *does it license a different
(forward, backward) reading pair?* `implies` and `causes` passed it, because
retracting the antecedent behaved differently:

> Retract the antecedent. Does the consequent go with it? Yes → `implies`,
> derived, same moment. No → `causes`, asserted, persists into a later moment.

That test needed two moments to compare — the one a claim was deposited at,
and the one being asked about. With one graph and no history, there is
exactly one moment: now. There is nothing left for the two readings to
disagree about, so there is nothing left for a second connective to decide.
Watch it happen:

```
rule <derive>  = implies( { +cloudy($d), no likely_rain($d) }, { +likely_rain($d) } )
rule <retract> = implies( { +wasnt_cloudy($d), no unwind($d) },
                          { -cloudy($d), +unwind($d) } )
fact +cloudy(today)
fact +wasnt_cloudy(today)
```

```
cloudy(today): not believed
likely_rain(today): believed
```

`cloudy(today)` was erased. `likely_rain(today)` — which a rule *derived from*
it — stayed. Under the old two-connective design this was `causes`'s
signature, not `implies`'s: a derived claim was supposed to go when its
premise did. It doesn't, not any more, for either connective, because nothing
in the engine tracks *what a belief was derived from* well enough to take it
back automatically. A rule has to erase a conclusion on purpose, the same way
it erases anything else. **Persistence is not a connective's decision now. It
is the only behaviour there is**, and Chapter 9 in Part 4 is about what that
costs.

## The termination question the old chapter asked, and the different one that replaced it

The old chapter's warning was: *`causes` can loop, because it keeps minting a
fresh moment to re-ask in.* That hazard is gone with `causes`. A different one
took its place, and it is more dangerous because it isn't about a keyword —
it can happen to the plainest classification rule you write.

```
rule <blades> = implies( { +blade($x) }, { +weapon($x) } )
fact +blade(dagger)
```

```
$ python -m ugm blades.ugm
blades.ugm: 400 ticks, ended applied
  stopped at the tick limit (400); it had not finished
```

Four hundred ticks to conclude one fact. `weapon(dagger)` is written on tick
one and never changes again — but the antecedent, `blade(dagger)`, never
stops being true either, so `<blades>` matches again on tick two, and every
tick after that, forever. Nothing notices the second application achieved
nothing:

> **There is no per-candidate filter.** An application that was tried and
> changed nothing is offered again, because deciding that a rule has nothing
> further to give is the corpus's judgement, not the engine's.

That line is in the loop's own source, not a metaphor. The fix is the same
one Chapter 6 already used without remarking on it — guard the rule with its
own negated conclusion:

```
rule <blades> = implies( { +blade($x), no weapon($x) }, { +weapon($x) } )
fact +blade(dagger)
```

```
$ python -m ugm blades.ugm
blades.ugm: 2 ticks, ended quiescent
```

Two ticks: one to fire, one to confirm nothing else matches. `no weapon($x)`
stops being true the moment `<blades>` fires, so the second attempt finds
nothing to match.

!!! warning "This is not optional for occasional rules any more"
    Every rule shipped in `ugm/rules/delay.ugm` — including one as inert as
    *a storm makes a flight extraordinary* — carries a `no <its own
    conclusion>` guard. Under the old design that pattern (Chapter 8's
    "an occasion is consumed, a fact is not") was for rules modelling
    something *happening*. Now it is for every rule whose antecedent can
    still be true after it has already fired once, which in practice means
    nearly every rule. **Write the guard by default; leave it off only when
    you can say why the antecedent can never hold twice.**

## Neither hazard needed engine support to explain

Both stories above come from the same fact, read twice. The engine does not
ask *has this rule already done what it can do* before matching it, and it
does not ask *what got this belief here* before erasing something upstream of
it. Deciding either would mean keeping a record the design deliberately
stopped keeping (Chapter 9, Part 4, is what that removal cost). What's left is
smaller than the two-connective design and, on this evidence, easier to get
wrong — a plain `implies` rule loops by default unless the corpus says
otherwise.

---

**Next:** enough theory. Let's write a working corpus, and meet the patterns
worth building on.
[Writing a corpus →](08-writing-a-corpus.md)
