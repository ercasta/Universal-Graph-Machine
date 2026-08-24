# Supposing

*Suppose it rains on Monday.* Then the streets are wet, the match is off, and
none of that is something you believe — it is something that **follows from an
assumption you are holding at arm's length**.

Any reasoner that plans has to do this. There's no dedicated supposition
mechanism in the engine: a corpus holds the hypothesis in an ordinary
proposition, and writes the hypothetical version of whatever rules it wants
to reason with inside it.

## Holding a hypothesis in a proposition

Wrap the hypothesis in `given($h, ...)`. The wrapper is the containment:

```
rule <wet>   = implies( { +rain($d) }, { +wet(streets) } )
rule <carry> = implies( { +given($h, rain($d)) }, { +given($h, wet(streets)) } )

fact +given(h1, rain(monday))
```

```
given(h1, rain(monday))   -> +
given(h1, wet(streets))   -> +     the consequence, under h1
rain(monday)              -> None  nothing is believed outright
wet(streets)              -> None  and <wet> never fired
```

`<wet>` is the ordinary rule about the world and it does not fire, because
nothing asserts `rain(monday)` — only `given(h1, ...)` does. That is the whole
of the containment, and it is visible in the corpus rather than in the engine.

What it costs is honest and stated: **you write the hypothetical version of
the rules you want to reason with**. `<carry>` above is `<wet>` again, one
level in. For a corpus that supposes about a narrow question that is a line;
for one that wants to reason hypothetically about everything, it is the whole
rule set twice.

## Saying it once instead of rule by rule

The cost above — writing the hypothetical version of every rule you want to
reason with — has one half that can be recovered, and it is worth knowing
which.

A **trigger** is an ordinary rule the engine consults on what another rule is
about to conclude, in the moment between *the rule concluded this* and *this
was written*. Mark it with `intercepts(<T>, after)` and it matches
`producing(<R>, p)` — the conclusion `<R>` is about to write, a fact that
exists only while that question is being asked and is never deposited.

```
rule <wrap> = implies( { +supposing($h), +producing($r, $p) },
                      { +instead($p, likely($p)) } )
fact intercepts(<wrap>, after)

rule <boil> = implies( { +heat($a, $w), +water($w) }, { +boiling($w) } )

fact +supposing(h1)
fact +heat(anna, kettle)
fact +water(kettle)
```

```
boiling(kettle)          -> None
likely(boiling(kettle))  -> +
```

`<boil>` is the ordinary rule and its consequent says `+boiling($w)`. Nothing
in it mentions a wrapper. *Everything concluded while supposing is uncertain*
is said once, by one rule, and it applies to rules written before it existed.

A trigger's conclusion is read as an instruction: `instead(p, q)` replaces,
`drop(p)` refuses, and anything else lands as well — so **marking** what a
hypothesis produced (`+hypothetical($p, $h)`) is the same mechanism with a
different verb. Two triggers on one conclusion run in table order, and the
second sees what the first left.

What this recovers is the **labelling**, and not the containment. A trigger
runs after the match, so it cannot change which premises a rule saw: an
ordinary rule about the world still reads the world. If you want a rule to
reason *inside* a hypothesis, you still write the hypothetical version of it.
What you no longer have to do is write the wrapper into every consequent by
hand.

Worth trying, because the result is not obvious. Add a second rule that reads
what the first concluded:

```
rule <wet>  = implies( { +rain($d) },     { +wet(streets) } )
rule <slip> = implies( { +wet(streets) }, { +slippery(streets) } )

fact +rain(monday)
```

```
wet(streets)                -> None
likely(wet(streets))        -> +
slippery(streets)           -> None
likely(slippery(streets))   -> None
```

`<wet>` fires — `rain(monday)` is asserted outright, and a trigger cannot stop
a rule from seeing the world. But its conclusion lands wrapped, so `<slip>`,
which asks for `+wet(streets)`, never matches. **The wrapper labels one step
and stops the chain there.** Reasoning further inside the hypothesis is the
`<carry>` shape above, written out: one wrapped rule per step you want to
take.

And because a conclusion is now not always what the rule that licensed it
said, that has to be on the record somewhere a rule can read it — not in a
trail (this CLI has none: no `--why`, no derivation to walk), but as an
ordinary fact the trigger itself deposits:

```
$ python3 -m ugm kettle.ugm --ask "boiling(kettle)" \
                            --ask "likely(boiling(kettle))" \
                            --ask "rewrote(<wrap>, boiling(kettle), likely(boiling(kettle)))"
boiling(kettle): not believed
likely(boiling(kettle)): believed
rewrote(<wrap>, boiling(kettle), likely(boiling(kettle))): believed
```

> **A conclusion that is not what the rule said it concluded cannot be reported
> as the rule's alone.** `rewrote(<trigger>, old, new)` names the trigger, what
> it changed, and what it changed it to — the one thing belief on its own
> (`believed(p)`, present or absent, nothing else) cannot say, and the reason
> this fact exists rather than staying implicit in what got written.

---

**Next:** two rules that disagree, and what settles it.
[When two rules disagree →](17-disagreement.md)
