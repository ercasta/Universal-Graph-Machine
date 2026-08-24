# Because…

Here is a corpus about what an airline owes a passenger. It's a good example
because the domain is deliberately far from toys — entitlements, exceptions
and duties rather than blocks on a table. This is `ugm/rules/delay.ugm`,
shipped and run by `python -m ugm.gates.vocabulary` as one of its own checks.

```
rule <cancel>
  +cancelled($f)
  no disrupted($f)
->
  +disrupted($f)
rule <late>
  +delayed($f, long)
  no disrupted($f)
->
  +disrupted($f)

rule <care>
  +disrupted($f)
  +booked($p, $f)
  no owed($p, meals)
->
  +owed($p, meals)
  +owed($p, lodging)

rule <weather>
  +cause($f, storm)
  no extraordinary($f)
->
  +extraordinary($f)

rule <compensate>
  +disrupted($f)
  +booked($p, $f)
  no extraordinary($f)
  no owed($p, money)
->
  +owed($p, money)
```

Ana's flight was cancelled because of a crew shortage. Raj's was delayed by a
storm.

```
fact +cancelled(bl204)   fact +cause(bl204, crew)    fact +booked(ana, bl204)
fact +flying(ana, bl204) fact +distance(bl204, long)

fact +delayed(kt881, long)  fact +cause(kt881, storm)  fact +booked(raj, kt881)
```

## Ask it

```
$ python -m ugm delay.ugm --ask "owed(ana,money)" --ask "amount(ana,600)" \
                          --ask "owed(raj,money)" --ask "owed(raj,meals)"
delay.ugm: 14 ticks, ended quiescent

what it believes, newest first:
  rerouted(ana, zr9)
  amount(ana, 600)
  owed(ana, money)
  extraordinary(kt881)
  owed(ana, lodging)
  owed(ana, meals)
  owed(raj, lodging)
  owed(raj, meals)
  disrupted(kt881)
  disrupted(bl204)
  ...

owed(ana,money): believed
amount(ana,600): believed
owed(raj,money): not believed
owed(raj,meals): believed
```

Ana gets money — a crew shortage is the carrier's own doing. Raj gets meals
and lodging but not money — a storm is nobody's fault, and `<compensate>`'s
`no extraordinary($f)` guard withholds it. Meals yes, money no, and that much
the engine will tell you flatly: `believed` or `not believed`.

## What it will not tell you, and why that is a real cut and not an oversight

The obvious next question is *why* — walk `owed(raj, money)` back to the fact
that blocked it. The honest answer, checked against the source rather than
assumed, is that **there is no such walk any more**. `python -m ugm --help`
says so on purpose:

```
What is gone from this file is the same thing that is gone from the engine.
`--save` and `--resume` wrote and replayed a SESSION -- everything the agent
had been told, in order -- and `--why` walked a belief's support back to what
it rested on. Both were readings of a history, and there is no history: one
graph, one current state, and what it holds is all there is to print.
```

This isn't a missing CLI flag with a working method underneath it. `Machine`
has no `why`, no `licensed`, no `applied(<R>)` fact recording *that this
particular firing happened*. `ugm/core/gate.py` — the one door a belief goes
through — says what it used to carry and states plainly that it's gone:

> What the gate used to be is worth saying, because most of it is gone. It
> stamped every deposit with a licence, a source and a landing place... The
> licence and the source were the derivation record, and the derivation
> record went with the chain.

And `ugm/core/rules.py`, on the field an `Application` used to have:

> There was a third field, `consumed` — the entries the match ate, kept as
> half the derivation trail. The trail went with the chain, and nothing in
> the loop read `consumed` for any other purpose.

So the old two-part mechanism this chapter used to describe — every entry
recording what licensed it, every application recording what it consumed —
is not thinner today. It is not there. Belief collapsed to one fact per
proposition, `believed(p)`, present or absent, and a retraction *deletes* that
fact rather than superseding it with a later one. There is nothing left for a
support trail to be made of.

## What is actually left

Two things, and neither is a trail:

**Presence and absence**, which is what `--ask` already showed. You can find
out *what* is believed. You cannot ask the engine *what made it so*.

**A rule's own shape, read back as data** (Chapter 6). Authoring a rule
deposits `rule(<R>)`, `ant(<R>, pattern, mode, i)`, `con(<R>, pattern, mode,
i)` — so you can ask *which rules conclude `owed($p, money)`* or *which rules
carry a guard*. That is a real, current, queryable fact about the **corpus**.
It is not an account of any one belief's derivation, and confusing the two is
exactly the mistake this cut is designed to make impossible to make by
accident: there is nothing that *looks like* an explanation left lying around
half-working.

```
rule <pays> = implies( { +con($r, owed($p, money), assert, $i) },
                       { +about_money($r) } )
```

```
about_money(<compensate>): believed
about_money(<care>): not believed
```

That's a query over the *rulebook*, answerable because reification writes it
down at load time regardless of whether the rule ever fires. It cannot tell
you whether `<compensate>` actually fired for Raj, only that it is the kind of
rule that concludes money.

## The honest scoring

| | old trail (licence + consumed) | today |
|---|---|---|
| what is believed | a query | a query |
| what made it so | a walk over recorded structure | **not answerable** |
| what a rule *would* conclude, in general | a walk over reified members | a query |
| cost of keeping it | a derivation record on every write | none — nothing is kept |

The row that changed is real, and it is a loss, stated as one rather than
talked around. If your corpus needs to explain a specific decision to a
person, that has to be written *into the corpus* now — a rule that concludes
`reason($p, crew_shortage)` alongside `owed($p, money)` is an ordinary fact,
sitting in `believed()` with everything else, and it survives exactly as long
as you keep it there rather than as long as some trail happens to still hold
it. `horizon/34-not-built.md` is where this book tracks gaps like this one
that have no current replacement.

---

**Next:** rules are nodes, so let's actually ask some questions about them.
[Asking about rules →](10-rules-are-subjects.md)
