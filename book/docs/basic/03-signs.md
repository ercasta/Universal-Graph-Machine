# Three signs, and silence

A rule member is written with one of three marks. Two are **signs** — `+` and
`−` — and the third, `no`, is a question about silence rather than a claim at
all. Where each is allowed depends on which side of a rule it's on, and that
restriction is not incidental — it's the whole chapter.

| mark | in an antecedent | in a consequent |
|---|---|---|
| `+` | must be believed | assert it — mint the anchor |
| `−` | **refused** | erase it — delete the anchor |
| `no` | must not be believed by anyone | **refused** |

The two blank cells are the load-bearing part, so let's earn them rather than
just state them.

## Absence is not denial

`no p` and `+not(p)` sound like two ways of saying the same thing, and they
are not. Here is the trap, run for real. The rule says *heal the wounded,
unless poisoned*:

```
rule <regen> = implies( { +wounded($x), no poisoned($x), no heals($x) },
                        { +heals($x) } )

fact +wounded(a)
fact +poisoned(a)
fact +wounded(b)
```

`b` is wounded and nobody has ever mentioned poison in connection with `b`.
Does `b` heal?

```
$ python -m ugm poison.ugm --ask "heals(a)" --ask "heals(b)"
poison.ugm: 2 ticks, ended quiescent

heals(a): not believed

heals(b): believed
```

`b` heals. `a` doesn't, because something believes `poisoned(a)`. And that's
the whole of what `no poisoned($x)` is asking: *does anything, anywhere,
currently claim this* — not *is it false*, not *has it ever been true*. If
nothing has ever mentioned `poisoned(c)`, `no poisoned(c)` matches exactly the
way it matches for `b`.

> **`no` asks whether anything anchors a claim. It never asks what's true.**

You don't have to write your negatives by hand for every case. Deriving a
default is an ordinary rule:

```
rule <clean> = implies( { +wounded($x), no bitten($x) }, { -poisoned($x) } )
```

...which of course needs `no bitten` to come from somewhere in turn. At some
point a corpus has to say what its defaults are, and here it says so in the
corpus, where you can read it and argue with it, rather than in the engine's
semantics, where you cannot.

## There is no `-` premise, and the machine says why

Try to write the poison rule the way it reads in most languages — *unless
denied* rather than *unless claimed* — and the loader refuses it outright:

```
rule <regen> = implies( { +wounded($x), -poisoned($x) }, { +heals($x) } )
```

```
ParseError: line 1: `-` is a consequent mode -- it erases. A premise cannot
erase, and there is no denying sign left to read it as. Say which you meant:
`no ...` (nothing anchors it) or `+not(...)` (its denial is believed).
```

This isn't the parser being fussy. `-` used to be able to sit in an antecedent
because there used to be a stored **sign** on every claim, and a `-` premise
asked to match the ones whose sign said *denied*. That stored sign is gone
(Chapter 2): belief is presence of an anchor, full stop, and there is nothing
left for `-` to mean on the reading side. Guessing which of the two real
questions you meant — *is it absent* or *is its denial believed* — would turn
a change in the engine into a silent change in what your corpus says. Refusing
loudly is the honest alternative, and it names both readings so you can pick.

Symmetrically: `no` never appears in a consequent (*absence is asked, never
asserted*), never in a `fact` (*a fact states; `no` asks*), and `-` never
appears on a `say` arrival (*a channel reports what it heard, not what to do
about it*). Each of those is a real load error with its own message, not a
silent no-op — the same discipline `@` and `at $m` get elsewhere in the
surface.

## Sign and *not* are not rivals

There is also a proposition `not(p)`. Isn't that just `-p` under another name?

No, and both exist, for one reason each:

| | what it is | what it's for |
|---|---|---|
| the `−` **mode** | an action, spent in a consequent | the ordinary case: stop believing something |
| `not(p)` | an ordinary **proposition** | saying a denial *is itself believed*, and reasoning about that |

`-poisoned(a)` takes back the belief that `a` is poisoned. It says nothing
about whether anyone thinks the opposite. `+not(poisoned(a))` is a completely
different act: it asserts a *new* proposition, one that happens to be about
`poisoned(a)`'s denial, and that proposition can be matched, nested, and
believed alongside `poisoned(a)` itself without the substrate objecting
(Chapter 2's closing note). Concluding `-b` from inside a rule about a
*likely* supposition would be nonsense — there is no entry to erase inside a
hypothesis someone else is reasoning about — but concluding `+not(b)` there
works exactly as any other proposition does: what you get out is *likely,
not-b*, a claim, not an act on the machine's bookkeeping.

> **The mode is what the machinery does. The proposition is what a rule can
> hold and reason with.**

The translation runs one way only, by convention rather than by force: a
corpus that wants "a positive claim implies its negation is retracted" writes
that itself, as an ordinary rule — `{+cured($x)} => {-poisoned($x)}` — rather
than the engine doing it silently. Minting `+not(p)` automatically for every
erasure would double every negative fact for no reason; nothing requires it,
and nothing does it for you.

## What used to need a third sign, and why it doesn't any more

An earlier version of this surface had a `?` sign: *held before, does not now,
and I can't say what does*. It existed because, under the old chain, silence
meant *unchanged* — so an interim state that genuinely wasn't known yet had no
honest way to be written. Take away silence-as-unchanged and the problem
disappears with it: **there is no more "unchanged" for a third mark to
override.** A proposition is believed or it isn't, checked fresh against the
one current state every time, so a value in flux is written the same way any
other fact is — erase what's stale, and let an ordinary proposition
(`+unsettled(transfer($a, $b))`) say that a downstream reader shouldn't treat
the gap as an answer. Chapter 4 is the rest of that story: what "unchanged"
used to mean, and why there's nothing left for it to mean now.

---

**Next:** we keep saying *believed now*. What happened to keeping track of
*when*?
[Moments →](04-moments.md)
