# The bootstrap

If rules are facts, and facts are entries read by walking a chain, and the walk
is made of rules — then reading a rule requires applying rules, and nothing ever
starts.

This chapter states that circle precisely, which turns out to make it much
narrower than it first appears, and then closes it.

## Only one of four steps is circular

Applying a rule takes four steps, and the temptation is to say all of them need
a read:

| step | what it needs | circular? |
|---|---|---|
| 1. propose candidate rules | **recall** — a function from situation to node ids | no |
| 2. read the rule's structure | members and positions | no |
| 3. check that its antecedent's entries hold | **the chain walk** | **yes** |
| 4. commit | the register, the stamp, the total step | no |

Step 2 is where earlier drafts went wrong. Reading a rule's *structure* is not
reading the chain: an antecedent is a node with members, and getting at them
needs ordering and nothing else.

What needs the walk is deciding whether the antecedent's entries **hold**, which
is step 3 alone.

## Stratum 0

Look at what a chain-walking rule actually asks for:

```
given  ?m' = predecessor(?m)
       ?e ∈ delta(?m)
       ?e = entry(?p, ?s)
then   candidate(?e, ?p)
```

Every member is **structural** — membership, position, node identity,
predecessor. Not one of them is *does X hold at Y*.

So step 3 for these rules is answered by matching alone, and they bottom out.
That's the fixed point, and it gives a criterion decided by **inspecting an
antecedent** rather than by a designer assigning layers:

> **Stratum 0** — every antecedent member is structural. Applied without a read.
>
> **Stratum 1 and above** — some antecedent member is an entry. Applied by the
> read that stratum 0 implements.

The check is a scan. An implementation can run it over its own shipped rules and
report which ones claim stratum 0 and aren't entitled to it.

## Two stratifications, and only one of them boots

There's a second, obvious way to stratify: **metarules about how to think,
independent of the business domain**.

That cut is real and useful — it's what makes the shipped rulebase *shippable*,
since one knowledge base of thinking-rules can serve every corpus.

It is **not** the cut that breaks the circle. Trust rules, surprise rules and
goal expansion are all domain-independent thinking-rules, and every one of them
talks about entries and beliefs — so all of them are stratum 1 or above.

> Domain-independence makes the rulebase shippable. Structural antecedents make
> it **bootable**.

Keeping those apart matters, because the first is much easier to satisfy and
looks like it should be enough.

## Three regresses, one escape

The bootstrap isn't a special problem. It's the third instance of a shape the
design already meets twice:

| regress | escape | what the escape is |
|---|---|---|
| reading needs reading | stratum 0 | a set of rules that need no read |
| selecting needs selecting | the total tiebreak | a lookup that does not reason |
| proposing needs proposing | recall | a function |

All three bottom out in **a function, not a search** — which is also the shape
of the three irreducible floor items. That recurrence is the strongest evidence
available that the floor is drawn in the right place.

Recall is the one worth dwelling on, because it's the only component that can be
consulted **before any rule has been applied at all**. A function has no
antecedent to read. Whether it's an index, a table with defaults, or a trained
network is an implementation choice among function approximators — which is the
specification of an approximator, written before anyone said the word.

## It runs under the same interpreter

It would defeat the purpose if stratum 0 needed a second interpreter. It
doesn't:

- **recall** for stratum 0 is *all of them, every time* — the set is small and
  fixed, so the policy is a different table, not a different mechanism;
- **match** is floor;
- **arbitrate** is the same total tiebreak, over a precedence nobody has claimed.

One more row, not one more branch.

!!! note "Deep dive: there were two matchers, and one had to go"
    This is worth telling, because the version with two matchers *worked* for a
    long time.

    A skeleton member like `sanc(?mq, ?mp)` was said to be unmatchable, on the
    grounds that it has no sign, no locus and no licence — nobody asserted it, so
    it has no entry.

    That doesn't follow. `pred(M3, M2)` is an ordinary relation instance. It
    simply wasn't in the *resolved state*, which was what the matcher was given
    — while stratum 0 matched the very same nodes **with a second matcher**.

    Which is the branch that *one interpreter* forbids, hiding in plain sight.

    Merging them deleted an entire module — a second engine with its own rule
    type, item type and solver, matching the very same nodes. And two things
    fell out that weren't obvious:

    - **Negation needs no notation.** A structural member has no entry, so a sign
      on one can only mean *not derived*.
    - **The layers must be derived, not assigned.** Structure has no sign, so a
      fact concluded against a half-built negation cannot be taken back the way a
      superseded entry can. The layers are the strongly connected components of
      the dependency graph — which makes recursion ordinary and negation *inside*
      a recursion a refusal.

## The price, stated

**Stratum 0 must produce structure, not entries.** If the walk deposited its
intermediate results as claims, it would be reading claims to do so, and the
circle would return.

So the read's own working state is undated, unattributed and unexplained.

And this price **charges itself**, which is the elegant part. *Produce structure*
is a constraint on the consequent; *every antecedent member is structural* is a
test on the antecedent. They're the same line: a rule whose antecedent is
entirely structural is applied without a read, and therefore concludes without
one.

So the engine needs no rule subtype, no marker on the surface, and no second
interpreter. **One predicate, read off the antecedent, decides both halves.**

The consequence is worth writing down rather than discovering:

> **You cannot ask *why did you read it that way* through the same mechanism you
> ask *why do you believe that*.**

Promoting the read into stratum 1 to fix this reinstates the circle, so the gap
is structural rather than an oversight.

And it gets charged somewhere unexpected. An entry's **support** — what it was
derived from — is structural by exactly this test: it's *how the entry was
made*, not a claim about the world. Which made it readable by stratum 0 and not
by ordinary rules — and Chapter 29 ran into that wall from the learning side,
where the agent's own trail is the best source of examples it has and the one
source its own rules couldn't see.

The resolution was the same test rather than a promotion: **an ordinary rule
reads the skeleton and concludes into it.** `rests_on` is a member like any
other, and nothing becomes an entry.

## What this buys

Stratum 0 rules are ordinary data. Creating one is a write, and a write needs
only the register and the stamp, both floor. Therefore:

> **The read is replaceable at run time.**

That's the whole claim this design opens with — that an agent with a better
internal representation of reality reasons better, and that the representation
is something you can hand it — turned from an aspiration into a mechanism.

The shipped rulebase is not merely shipped rather than compiled in. It is
editable by the agent that runs it.

---

**Next:** the number that says whether any of this is true of the implementation.
[Zero phases →](32-zero-phases.md)
