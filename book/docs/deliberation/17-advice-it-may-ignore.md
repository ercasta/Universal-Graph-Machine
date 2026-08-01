# Advice it may ignore

The cheapest thing you can tell this machine is what you'd *prefer* it did.
Not what it must do, not what it may never do — just a nudge.

```
prefer settle the base first:
    touching c
    because a tower is built bottom up
```

```
avoid the slow crane:
    action unstack
    because the crane is slow
```

Two words, `prefer` and `avoid`, and the second one is the interesting half of
this chapter — because `avoid` means **later**, and it must never quietly come
to mean **never**.

## Why that distinction is the whole thing

Chapter 7 left you with a rule:

> **Rank a guess; prune a proof.**

A guideline is a guess. You wrote it because you believe unstacking is slow, or
that towers go up from the bottom, and you may simply be wrong about this
particular puzzle. The machine has no way to check whether you are.

So the test that matters is Chapter 7's awkward puzzle, the one where the
winning move is the one that looks useless. `c` is on `a`; we want `a` on `b`
and `b` on `c`; and the only route starts by unstacking `c`, which closes
nothing.

Now avoid exactly that move — tell the machine the crane is slow — and see what
happens:

```
avoided : found=True  plan=('unstack', 'stack', 'stack')  imagined=76
```

It still solved it. **By the very move you told it to avoid**, because avoiding
was only ever a request to try other things first.

Compare a `never` line from Chapter 12, on the same puzzle:

```
forbidden: found=False  imagined=172
```

Honestly unsolvable, and it burned three times the search establishing that.
That's the correct behaviour for a prohibition — the crane really is out of
service, so there is no plan. It would be the *wrong* behaviour for advice.

Notice the cost of the advice, too: 76 imagined states where the unadvised
search takes 50. Bad advice made the machine slower and left it just as
correct. That's the trade you're accepting when you write a guideline, and it's
a good trade precisely because the downside is measured in time rather than in
wrong answers.

## Where advice is allowed to move things

Relevance sorts candidate moves into bands. Band 4 means *this exact move, with
these exact arguments, makes something the goal wants true* — and that isn't an
opinion, it's read off the rule's own instructions (Chapter 22).

A guideline is an author's hunch. So the rule is:

> **Advice reorders inside a band. It never moves anything across one.**

Here's the whole set of candidate moves for a tower goal, with `prefer touching
c` and `avoid paint` in force:

```
  stack    band 4  score 4.800
  stack    band 4  score 4.200
  stack    band 3  score 3.800
  stack    band 3  score 3.200
  unstack  band 2  score 2.800
  stack    band 2  score 2.800
  stack    band 2  score 2.800
  unstack  band 2  score 2.200
  unstack  band 2  score 2.200
  paint    band 0  score 0.800
  paint    band 0  score 0.000
  paint    band 0  score 0.000
```

The score is the band plus a fraction that's always less than one. Both band-4
moves stay ahead of everything else; your preference decides which of the two
goes first. The avoided moves sink to the *bottom of their own band* — the
`.000` rows — and no further.

That fraction is not a weight. There is no number in it to tune — it's an
**encoding of an order**, and the order is: avoided, then unmentioned, then
preferred, with earlier declarations beating later ones.

The odd row out is instructive. One `paint` scores `.800` — preferred — even
though `avoid paint` is in force. It's the one that would paint `c`, and
`prefer touching c` was declared first, so it matched first and decided. That's
not a bug to be smoothed over; it's the precedence rule being visible. If you
don't want it, swap the order of the two lines.

!!! note "Why letting advice cross a band would be a mistake"
    It's tempting to allow it. Sometimes an author really does know that a
    band-4 move is a trap.

    But band 4 is derived from the rule's own body, and a guideline is a
    sentence someone typed. Letting the weaker evidence beat the stronger is
    exactly how authored advice makes a system **dumber than it was before** —
    and the failure is silent, because a plan is still produced. If you want a
    band-4 move gone, that's a `never` line, and a `never` line is a claim you
    can be held to.

## Two guidelines that disagree

Declare contradictory advice and the earlier one wins:

```
prefer - declared first
avoid - declared second, must not win
```

That's the list of guidelines that spoke to one particular move, in precedence
order, each carrying the `because` you wrote. You can ask that question of any
move at any time — which is the point.

> Advice nobody can interrogate afterwards is a magic number, and it's no less
> a magic number for having been typed by a person rather than learned by a
> model.

The `because` line isn't decoration. It's the difference between "the machine
preferred this move" and "the machine preferred this move because a tower is
built bottom up."

## The part that isn't in the guidelines at all

Here is the finding that came out of testing this, and it's better than the
feature.

Someone tried to break the safety property deliberately — rigged the scoring so
that every avoided move got a catastrophic score, advice behaving as an outright
filter rather than a nudge. The awkward puzzle **still solved**, still by the
avoided move.

Which means "advice cannot exclude" isn't a promise made by the advice
machinery. It's a property of the search itself: the frontier only ever
*orders* what it's given, so no score, however dreadful, puts a move out of
reach. Nothing was ever thrown away to begin with.

That's worth separating carefully:

| the guarantee | comes from |
|---|---|
| advice can't lose you a solution | the **search**, which only orders |
| advice can't overturn structural evidence | the **band** rule, which is guideline machinery's own job |

The first one is architectural and holds no matter what anyone authors. The
second is the one that had to be got right here, and it's the one the planted
bugs actually bit on.

---

**Next:** advice you may ignore is the safe end of the spectrum. Now the end
with teeth — knowledge that *replaces* the search, and knowledge you're not
allowed to work around.
[Recipes, and rules you must follow →](18-recipes-and-rules.md)
