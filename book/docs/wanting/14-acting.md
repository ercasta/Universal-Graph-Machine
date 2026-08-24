# Acting

**An action is not a new kind of thing.**

`attack(hero, goblin1)` is a fact like any other. A rule concludes it like
any other conclusion. There is no action construct, no operator schema, and
no plan-step type alongside the rules.

## What's real: declare it, conclude it, read it

`action` marks a relation as something a host program should watch for —
discoverable, not enumerated:

```
action deploy($service)

fact +want(deploy(web))

rule <request> = implies( { +want(deploy($s)) },
                          { +deploy($s), -want(deploy($s)) } )
```

That's the shape `ugm/rules/tools_approval.ugm` ships with (Chapter 22's
worked example, and `docs/tools-approval.md`). `deploy($s)` is an ordinary
conclusion, gated on the way to it by an ordinary trigger
(`+intercepts(<hold>, after)`, Chapter 18) that can hold it for approval,
swap it for something else, or let it through. Nothing here crosses a
boundary the engine enforces. What crosses is whatever a Python program
watching this machine chooses to read: after `run()`, or via `watch` on each
`Step`, it asks `m.holds(kb.term("deploy(web)"))` and, if true, does the
deployment for real. The engine's contribution stops at depositing a belief
a host can trust was reached the way the corpus says it was reached.

## The marker: same act, different behaviour

An intent that arrives at a rule as `declares($act, $r)` has two parts worth
telling apart:

```
rule <trust-player> = implies(
  { +says(player, declares($act, $r)), no intends(hero, $act, $r) },
  { +intends(hero, $act, $r) } )

rule <focus> = implies(
  { +intends(hero, attack($d), focus($t)), no target(hero, $t) },
  { +target(hero, $t) } )

fact +present(goblin1)
fact +present(goblin2)

say player: +declares(attack(goblin1), focus(goblin2))
```

```
4 ticks, ended quiescent

target(hero, goblin2): believed
```

`attack(goblin1)` is the act with its binding; `focus(goblin2)` is the
**marker** — free structure a rule may read or ignore. `<trust-player>`
doesn't look inside it; `<focus>` does, and picks a different target for the
same declared act. This pattern is real and shipped: `ugm/rules/dungeon.ugm`,
`dungeon_gut.ugm`, and `dungeon_micro.ugm` all carry `<trust-player>` reading
`says(player, declares($act, $r))` exactly this way, over `ugm/probes` fight
fixtures this book won't re-quote numbers from without re-measuring them
against the tool registrations those probes require.

> **The marker is read by rules and never followed by machinery.** The
> moment a host-language function dereferences one to decide what happens
> next, the loop has stopped being the only thing that decides.

**A marker nothing matches is not an error.** Change the marker to something
no rule discriminates on and the declared act still goes through — `intends`
gets written, nothing narrows the target, and the corpus looks entirely
normal:

```
say player: +declares(attack(goblin1), 1)
```

```
3 ticks, ended quiescent

target(hero, goblin1): not believed
intends(hero, attack(goblin1), 1): believed
```

A mistyped or unmatched marker **quietly stops steering** — the intent still
forms, nothing downstream reacts to the marker, and a policy that has
stopped steering looks identical to one with nothing to say. Chapter 13's
silence taxonomy, arriving inside one agent: check what actually got
concluded, not just whether the run finished cleanly.

## Deciding and acting stay two different things

A conclusion is a claim, and it can be deposited freely. An **act**
shouldn't be — deciding to act and acting are two different things, and only
the first should be recoverable purely from what got concluded. Today that
separation is a matter of convention, not something the engine enforces: a
corpus concludes `deploy($s)` or `attack(goblin1)`, and it's up to the host
wrapping the `Machine` to treat that belief as the trigger for a real effect
exactly once, the way `tools_approval.ugm`'s `kb.answerer` binding does.
Nothing stops a corpus from writing the same conclusion twice, or a host
from acting on it twice — that discipline lives outside the engine.

A corpus that wants to reason about a hypothesis writes it into the
proposition itself — `given(h1, p)` — and contains its claims exactly as
well as it writes them.

---

That's Part 3: the machine can conclude that something should be done, and a
host reading its beliefs can act on that. That's as far as the engine goes;
the rest is up to the corpus and the host around it.

**Next:** everything so far has been stated flatly. Time to say things
you're not sure about.
[How strongly →](../unsure/15-how-strongly.md)
</content>
