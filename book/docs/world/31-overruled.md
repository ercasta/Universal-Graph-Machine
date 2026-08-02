# Overruled

Chapter 12 gave the machine three absolute limits, and `never` was the sharpest
of them: name an action in a goal's `never` line and it is pruned, everywhere,
with no appeal. That's exactly right for a law.

It's exactly wrong for almost everything else people call a rule.

## The thing that couldn't be said

Consider a shop:

- *We don't sell.* A standing house policy — the default stance, not a law.
- *Never counterfeit.* Genuinely absolute. Nothing overrules it.
- *Today it's good to sell.* A transient instruction that ought to win over the
  standing policy, and must not touch the law.

Three statements that look alike and behave completely differently. Look at what
the machine had to say them with:

| | why it doesn't fit |
|---|---|
| `never sell` | absolute. Right for the law; makes the house policy unbreakable |
| `avoid sell` | only reorders, deliberately (Chapter 17). Never actually stops it |
| `criterion` | names an action to **take**. There is no *don't* |

Someone using this machine hit exactly that and solved it the way anyone would:
about seventeen lines of Python, run before the goal was built, working out
which prohibitions survived and writing those in.

It worked. It got the right answer every time. And the loss was precise and
total: *"it used to be auditable."* Python that runs before the machine sees
anything cannot answer **"why is selling not excluded?"** — the reasoning
happened somewhere the machine can't look.

!!! note "The ruling that decided this"
    The tempting response is to declare it out of scope: the machine wasn't
    built to model shop policy. The project's own rule says otherwise, and it's
    worth stealing:

    > **Anything that can be said is in scope.** We decide the *how*, never the
    > *whether* — and the how must be data, never Python, because a Python
    > answer creates the next place the machine can't look at itself.

## A norm is a thing that has a source

Here's the whole design, and the pleasing part is how little of it is new.

A **norm** says one thing about one action: forbidden or permitted, from a
**source**, optionally inviolable, optionally with a reason. And to arbitrate
between norms that disagree, you need a ranking over their sources...

...which is exactly what Chapter 30 just built. *"Today outranks the standing
policy"* is the same shape as *"the supervisor outranks the agent"*. So there is
**no second ranking mechanism, and no norm-specific idea of strength**. A norm's
source is its speaker, and *who says so* is answered by the ordinary record of
who said what.

```
house : forbid  sell         "the house does not sell"
law   : forbid  counterfeit  "it is illegal"          [inviolable]
today : permit  sell         "there is a fair on"
```

## What happens when they disagree

Nothing, until you say who wins:

```
norms about 'sell' disagree and their sources are not ranked: house, today.
Say who outranks whom — arbitrating by declaration order would be an
undeclared tie-break.
```

Refused, loudly, naming both sources and the action. It would be so easy to
break the tie by declaration order, and the machine won't: a deterministic
answer that depends on something nobody declared is the exact failure this
project has caught in itself more than once.

Declare the ranking and it settles:

```
today outranks house

sell        : permit — today (there is a fair on); overriding house's forbid
counterfeit : forbid — law (it is illegal), inviolable
```

Read that second line again — that's the audit. The winner, its source, its
reason, and **the norms it beat, still there to be cited**. That's the thing the
seventeen lines of Python couldn't give.

## Inviolable is not just "very high"

Let `today` claim authority over `law` and try again:

```
today outranks law   (declared!)

counterfeit : forbid — law (it is illegal), inviolable
```

Unmoved. An inviolable norm isn't top of the ranking — it's **outside** it.
Something merely top-ranked can be outranked by anyone who declares themselves
above it, which would make "inviolable" a promise the machine couldn't keep.

## And then it's an ordinary `never`

Here's the part that makes this cheap. Once the norms are settled, they're
written into the goal as plain Chapter 12 constraints:

```
constraints written : ('never counterfeit',)
```

That's all. `sell` isn't there — it was permitted, so nothing excludes it. And
`never counterfeit` is an ordinary `never`, indistinguishable from one you typed
yourself.

Which means **nothing downstream changed at all.** The planner, the pruning, the
explanations — none of them know that norms exist. There is no fourth kind of
force in the search.

That was a real choice, and the alternative was tempting: a "soft never" that
prunes unless outranked, evaluated inside the search. The person who raised this
flagged that shape as the one they *didn't* want, and they were right. What
makes this version work is that arbitration happens when every norm is in hand
and **none of them is about a state of the search**. It's a step that runs
against the world, before planning starts, and its output is data anyone can
read.

!!! note "And it's in the conversation, so it can be taken back"
    A norm is an authored block like any other, so Chapter 30's retraction
    reaches it:

    ```
    (house declares: forbid haggle)
    (that utterance is withdrawn)

    haggle : no norm speaks about it
    ```

    You didn't have to build that. It works because the norm is on the record
    the same way advice is.

---

**Next:** the last thing an agent in the world has to do, and it's the hardest
one to do gracefully. [Waiting →](32-waiting.md)
