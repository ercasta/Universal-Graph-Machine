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

## What the engine won't tell you

There is no walk from `owed(raj, money): not believed` back to the fact that
blocked it. Belief is one fact per proposition, present or absent, and a
retraction deletes it rather than superseding it — there is nothing left over
that a derivation trail could be made of.

## What a corpus can tell you about itself

Two things, and neither is a trail of one belief's derivation:

**Presence and absence**, which is what `--ask` already showed. You can find
out *what* is believed.

**A rule's own shape, read back as data** (Chapter 6). Authoring a rule
deposits `rule(<R>)`, `ant(<R>, pattern, mode, i)`, `con(<R>, pattern, mode,
i)` — so you can ask *which rules conclude `owed($p, money)`* or *which rules
carry a guard*. That's a real, queryable fact about the **corpus**, written
down at load time regardless of whether the rule ever fires:

```
rule <pays> = implies( { +con($r, owed($p, money), assert, $i) },
                       { +about_money($r) } )
```

```
about_money(<compensate>): believed
about_money(<care>): not believed
```

That query cannot tell you whether `<compensate>` actually fired for Raj,
only that it is the kind of rule that concludes money.

If your corpus needs to explain a specific decision to a person, write that
into the corpus: a rule that concludes `reason($p, crew_shortage)` alongside
`owed($p, money)` is an ordinary fact, sitting in `believed()` with
everything else, and it survives exactly as long as you keep it there.
`horizon/34-not-built.md` tracks gaps like a derivation walk that have no
current replacement.

---

**Next:** rules are nodes, so let's actually ask some questions about them.
[Asking about rules →](10-rules-are-subjects.md)
</content>
