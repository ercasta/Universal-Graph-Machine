# Stretches, not instants

Some claims aren't about a moment at all.

*They are taking turns* isn't true of any instant. Its subject is a
**stretch**. So is *it rained throughout*, and so is any constraint on the
order in which things happen.

## What says a stretch: two ordinary arguments, and nothing else

A stretch is the plainest thing there is: **two node names, carried as
arguments of an ordinary proposition, asserted by the corpus like anything
else.** Nothing mints them, nothing orders them, nothing derives their
contents. What you assert about the stretch is what you know about it — no
more.

Adapted from the passenger-rights domain in `ugm/rules/delay.ugm`: a
disruption stretches from the scheduled departure to whenever the flight
actually left, and a rule about the whole stretch reads the two endpoints
without ever being told what happened between them.

```
rule <span>
  +disrupted($f)
  +scheduled($f, $s)
  +departed($f, $a)
  no stretch($f, $s, $a)
->
  +stretch($f, $s, $a)

rule <care>
  +stretch($f, $s, $a)
  +booked($p, $f)
  no owed($p, meals)
->
  +owed($p, meals)

fact +disrupted(bl204)
fact +scheduled(bl204, "09:40")
fact +departed(bl204, "13:15")
fact +booked(ana, bl204)
```

```
$ python -m ugm span.ugm --ask "owed(ana, meals)"
span.ugm: 3 ticks, ended quiescent

what it believes, newest first:
  owed(ana, meals)
  stretch(bl204, 09:40, 13:15)
  ...

owed(ana, meals): believed
```

`stretch(bl204, 09:40, 13:15)` is not engine vocabulary. It is a relation
this corpus invented, the same way `owed` and `booked` are. `<care>` reads it
the way it reads any other proposition — no walk, no ancestry check.

That `no stretch($f, $s, $a)` guard on `<span>` is not decoration. An
application that writes nothing new is still an *application*, and it is
offered again on the next tick, and the one after that, for as long as its
antecedent still matches:

> **An application that changes nothing is offered again.** Guard your own
> recursion, or the loop never reaches quiescence — it hits the tick limit
> instead, having done nothing since the second tick.

## What stays true about representing a stretch

**Endpoints, never contents.** What you know about a stretch is *exactly*
what you asserted and nothing else — not "derivable but not listed,"
genuinely absent until said.

| | endpoints only | enumerate the moments | a description of the stretch |
|---|---|---|---|
| not leaking | asserted, not derived — nothing to disagree with | invents a number of intervening events | fine |
| not lossy | fine | records the extent, not why those | fine |
| readable | fixed 2-ary | arity varies with duration | — |
| composable | compare two pairs of endpoints | comparing stretches means comparing lists | comparing descriptions isn't expressible |

**Participants stay out.** `anna` and `bo` are members of the *proposition* —
`taking_turns($a, $b, $s)` — never of the stretch itself. One stretch can
still host several unrelated claims: *they took turns* and *it rained
throughout*, over the same two named endpoints.

**Ordering stays out too, unless you assert it.** Nothing orders two named
endpoints for you. If a corpus needs *the scheduled time comes before the
actual one*, that is a fact it writes (`before(09:40, 13:15)`) or a
computator it calls — never something the engine checks on its behalf.

---

**Next:** claims with no fixed length at all.
[Shapes →](20-shapes.md)
