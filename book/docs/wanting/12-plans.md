# Plans and subgoals

Chapter 11 got one real mechanism out of "reading a rule backwards": recall,
a lookup from a goal's relation to the rules that could conclude it. This
chapter is about turning what you want into something a corpus can act on —
the gap between where things stand and where you want them to.

## The gap between here and there

A plan starts from a difference: what holds now, and what you want to hold.
That's not something a rule can compute — a rule matches one entry at a time
and can say nothing about a *set* — so it's a tool. `delta` answers a request
naming two states and a node to hang the answer on:

```
fact +at(home)
fact +holds(p1, torch)

fact +delta(state(at(home), holds(p1, torch)),
            wanted(at(work), holds(p1, key1), holds(p1, torch)),
            gap1)

rule <want-what-is-missing> = implies(
  { +missing(gap1, $p), no goal($p) }, { +goal($p) } )
```

```
3 ticks, ended quiescent

what it believes, newest first:
  goal(at(work))
  goal(holds(p1, key1))
  holds(p1, torch)
  at(home)
```

`missing(gap1, at(work))` and `missing(gap1, holds(p1, key1))` are what the
tool wrote; `<want-what-is-missing>` is an ordinary rule deciding what's worth
wanting. What the torch shows is that a difference is only what differs —
both states hold it, so it appears in neither `missing` nor `extra`.

That `no goal($p)` guard is load-bearing, not decoration. Leave it off and the
rule matches the same `missing` entry every tick forever — writing a fact
that's already believed is a no-op, but the engine still counts it as an
**application**, and only a genuinely empty match set ends a run
`quiescent`. Every corpus in this chapter that concludes something durable
needs a guard like this one, the same way `ugm/rules/worked.ugm`'s own
`<boil>` guards on `no boiling($w)`.

And when the two states differ in **nothing**, the tool says that outright:

```
fact +at(work)
fact +delta(state(at(work)), wanted(at(work)), gap1)
```

```
matched(gap1): believed
```

Which looks like a convenience and is not:

> A rule reads differences one at a time, so it can act on every `missing`
> there is — and it can never conclude that there were none. *No missing* is
> a claim about the whole set. The tool is the only party that has seen the
> whole set, so the tool is the one that says it.

Try to write "no missing" as a rule guard instead and the loader refuses it,
for the same reason absence never picks out a variable (Chapter 6):

```
rule <bad> = implies( { no missing(gap1, $p) }, { +done(gap1) } )
```

```
rule 'bad' asks `no missing(gap1, $p)` with a variable no earlier
member binds -- an absence is a check on things already picked out,
never a way of picking them out
```

`matched($g)` is what a corpus reads instead — the tool's own claim that the
set closed, not a rule's attempt to say so:

```
rule <done> = implies( { +matched($g) }, { +enough($g) } )
```

Set a goal, compute the gap against where you are, and stop when it closes.
Chapter 26 has what `enough` then does with that.

A state here is either a compound you built — read one deep, so `at(work)` is
a proposition *in* the state while `at` and `work` are what that proposition
is made of — or `state(...)`/`now`, which is already how *the world as it
stands* gets built without anybody assembling it: `now` reads the whole
scratchpad, minus the machinery's own bookkeeping.

There's no built-in mechanism that turns a `missing` entry into a rule to
apply next — that's left to a corpus's own rules, the way
`<want-what-is-missing>` above turns a `missing` fact into a `goal`.

---

**Next:** what the machine says when it runs out of ideas, and why that
answer is harder to get right than it looks.
[Blocked, and what silence means →](13-blocked.md)
</content>
