# The one connective

```
rule <weather> = implies( { +cloudy($d, morning), no likely(rain($d, afternoon)) },
                          { +likely(rain($d, afternoon)) } )
```

There is one connective: `implies`. Every rule in this book is `implies(side,
side)`, read two ways — forward, as *what follows*; backward, as *what would
make this true* (Part 3 is the backward reading). One statement, both
readings, cited by the same node.

Persistence follows from that. A conclusion is a write like any other — it
stays until some rule erases it, on purpose, the same way it erases anything
else. Nothing in the engine tracks *what a belief was derived from* well
enough to take it back automatically when its premise goes:

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

`cloudy(today)` was erased. `likely_rain(today)`, which a rule derived from
it, stayed — because persistence isn't a connective's decision, it's the only
behaviour there is. Chapter 9 covers what that costs when you want to explain
a belief later.

## The termination hazard

A plain `implies` rule can loop, and it doesn't take anything exotic to
trigger it — the plainest classification rule you can write is enough.

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

The fix: guard the rule with its own negated conclusion.

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

!!! warning "Guard by default"
    Every rule shipped in `ugm/rules/delay.ugm` — including one as inert as
    *a storm makes a flight extraordinary* — carries a `no <its own
    conclusion>` guard. Any rule whose antecedent can still be true after it
    has already fired once needs one, which in practice means nearly every
    rule. **Write the guard by default; leave it off only when you can say
    why the antecedent can never hold twice.**

The engine does not ask *has this rule already done what it can do* before
matching it — deciding that would mean keeping a record the design doesn't
keep. A plain `implies` rule loops by default unless the corpus says
otherwise.

---

**Next:** enough theory. Let's write a working corpus, and meet the patterns
worth building on.
[Writing a corpus →](08-writing-a-corpus.md)
</content>
</invoke>
