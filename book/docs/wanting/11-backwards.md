# Reading a rule backwards

So far every rule has been read forwards: *these things hold, therefore this
follows*.

A rule can be read the other way. *I want this. What would bring it about?*

```
rule <boil> = causes( { +heat($a, $w), +water($w) }, { +boiling($w) } )

fact +water(kettle)
fact +goal(boiling(kettle))
```

```
asked for:
  boiling(kettle)  [open]  via <boil>
    water(kettle)  [held]
    heat($a, kettle)  [BLOCKED]
```

The machine found the rule that could produce what you wanted, unified the goal
against its consequent, and turned the antecedent members into subgoals — with
the binding carried through, so it's `heat($a, kettle)`, not `heat($a, $w)`.
Then it reported honestly on each: the water it already has; heating it does
not, and cannot obtain.

## Both readings, one statement

This is the first requirement the whole design was built around:

> Planning reads a rule **backwards**. Execution reads it **forwards**. Both
> readings must come from the same statement.

Two statements — one per direction — would drift apart with no way to detect the
disagreement, because neither is the premise of the other. Here there is one
node, and direction is a **query over the rule**, never a field in it.

And the second requirement, which is what keeps the backward reading honest:

> **The reading must be recoverable.**

Reading a rule backwards is reading its converse. *Four wheels ⇒ car*, run
backwards, licenses *a cart is a car*. That is perfectly legitimate as a
hypothesis and catastrophic if a planner treats it as entailment. So the licence
recorded on the resulting entry says which reading produced it, permanently.

## Not every reading is useful

R1 asks that both readings come from one statement. It does **not** promise that
both are informative, and one shape makes that sharp — a consequent that's a
bare variable:

```
rule <trust> = implies( { +says($c, $p, plus) }, { +$p } )
```

Forwards this is exact: whatever the channel said, believe it (Chapter 21).

Backwards it says *this rule can conclude anything*. It proposes itself for
every goal, and its subgoal is another goal of the same shape, without end. It
isn't wrong. It's vacuous.

The backward reader therefore declines what it can't use, and the index over
what a rule concludes gives that decision a natural home rather than a special
case: a bare-variable consequent has no bucket, so it's never a candidate.

## How the backward reading is actually done

Here's the interesting part, and it's the thing this design had to get right
before Part 3 could exist at all.

Reading a rule backwards means matching a goal against a stored pattern — and
that's the operation no rule may perform (Chapter 6). So the natural design is:
*ask whether this pattern matches, and be given the binding*.

That cannot work:

> **A binding is a map from variables to nodes, and a rule cannot hold one — let
> alone apply one, because applying is substitution, and substitution is a floor
> primitive.**

So the answer has to arrive **already instantiated**. The backward reading is a
**request**:

```
+fit(<R>, goal)                     could this rule produce this?
+fits(<R>, goal)                    it could
+need(<R>, goal, <subgoal>)         one per antecedent member, substituted
+unfit(<R>, goal)                   it could not
```

Which gives the general statement:

> **Match and substitute travel together, because the caller cannot do the
> second half.**

That also settles a question that had been open for a while: does this need a
sixth floor primitive? No. A primitive a rule invokes would hand back a binding
the rule can't use, so it wouldn't help; and the moment the answer is
instantiated, the service is doing the substitution too — which makes it a
request and not a primitive.

> A floor item returns a **binding**. A service returns a **thing**.

Two other capabilities are the same shape: composing two rules is a service that
returns a finished **rule**, and learning from examples is a service that
returns a finished **pattern**. Both in Chapter 29.

## Six rules, and no phase

Backward reading used to be a *phase* in the interpreter — a stage the loop ran
before anything else. It is now six ordinary rules: ask-recall, ask-fit, plan,
expand, ask-check, and the verdict.

That change bought something concrete, and it's a good illustration of why this
design keeps deleting phases.

The phase ran before recall and matching, and returned early. So while any goal
was unexpanded, **no ordinary rule could apply**. Measured: a goal that *is*
satisfiable — `water(kettle)`, derivable forwards from the same corpus — read as
unsatisfied, because the phase never let anything derive it.

The rule-level reader interleaves, being ordinary rules, and finds it.

> **A phase does not merely hold a convention. It asserts that it should go
> first, and it asserts it where nothing can argue.**

You can watch the whole thing happen. Here's the trail for the *acting* version
of this corpus (Chapter 14), read bottom-up:

```
    because +goal(boiling(kettle)), licensed by loaded(goal(boiling(kettle)))
    because +recall(boiling(kettle)), licensed by applied(<ask-recall>)
    because +recalled(<boil>, boiling(kettle)), licensed by recall(boiling(kettle))
    because +fit(<boil>, boiling(kettle)), licensed by applied(<ask-fit>)
    because +fits(<boil>, boiling(kettle)), licensed by wanted(<boil>, boiling(kettle))
    because +need(<boil>, boiling(kettle), heat(anna, kettle)), ...
    because +goal(heat(anna, kettle)), licensed by applied(<expand>)
```

Every step of the planner's own reasoning is a dated, licensed claim you can ask
about — because the planner is made of rules.

---

**Next:** what happens once you have a subgoal, and the trap that makes a plan
quietly wrong.
[Plans and subgoals →](12-plans.md)
