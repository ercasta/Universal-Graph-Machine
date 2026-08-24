# Reading a rule backwards

So far every rule has been read forwards: *these things hold, therefore this
follows*.

A rule can also be asked the other way: *what could produce this?* That
question is answered by **recall**.

```
rule <boil>
  +heat($a, $w)
  +water($w)
  no boiling($w)
->
  +boiling($w)

fact +water(kettle)
fact +recall(boiling(kettle))
```

```
recalled(<boil>, boiling(kettle)): believed
```

Writing `+recall(boiling(kettle))` asked the question; `<boil>` came back
because its consequent unifies with `boiling($w)`. Nothing was searched — the
rules are indexed by the relation they conclude, so *what could produce
`boiling(kettle)`* is a lookup, not a scan of every rule the corpus knows.

## What recall actually is

> **A relation a rule concludes is a bucket. Recall is a lookup into it.**

`Rules.by_conclusion` is built once, when a rule is authored, by reading its
consequent's relation. `+recall(p)` looks up `p`'s relation and writes
`recalled(<R>, p)` for every rule whose bucket it's in. That's the whole
mechanism. It does not unify `p` against `<boil>`'s pattern, does not bind
`$w` to `kettle`, and does not ask whether `<boil>`'s other members could ever
hold. It answers *which rules even mention this*, nothing more.

## Not every reading is useful

A bare-variable consequent makes that sharp:

```
rule <trust> = implies( { +says($c, $p, plus) }, { +$p } )
```

Forwards this is exact: whatever the channel said, believe it (Chapter 21).
Backwards it would say *this rule can conclude anything*, which is not a
recall candidate worth having — so it isn't one:

```
fact +recall(boiling(kettle))
```

```
recalled(<trust>, boiling(kettle)): not believed
recalled(<boil>, boiling(kettle)): believed
```

`by_conclusion` only ever buckets a consequent member whose pattern is not a
bare variable. `<trust>` never gets a bucket, so recall never surfaces it,
with no special case written for it — the index is simply built that way.

## Recall and application share one node

> Reading a rule backwards and applying it forwards are two queries over the
> same rule, never two separate statements. There is one node, `<boil>`, and
> direction is a **query over it**.

That matters because a rule read backwards is read as its converse. *Four
wheels ⇒ car*, run backwards, licenses *a cart is a car* — legitimate as a
hypothesis, wrong if treated as entailment. Recall keeps the two apart:
`recalled(<boil>, boiling(kettle))` and an ordinary forward conclusion of
`boiling(kettle)` are different relations, deposited by different code
paths, so a corpus can always tell which one it's looking at.

## Recall is a service, not something a rule computes

Reading a rule backwards means matching a goal against a stored pattern, and
that's the operation no rule may perform (Chapter 6): matching is a floor
primitive. So a rule cannot itself ask *does this fit* and be handed a
binding, because:

> **A binding is a map from variables to nodes, and a rule cannot hold one —
> let alone apply one, because applying is substitution, and substitution is
> a floor primitive too.**

Whatever answers *would this rule produce this goal* has to hand back
something a rule can use, which means the answer has to arrive **already
instantiated** — a service, in the same family as `kb.answerer` and
`kb.computator` (Chapter 22), not a sixth floor primitive.

> A floor item returns a **binding**. A service returns a **thing**.

Recall is exactly such a service: given a goal, it returns rule references,
already resolved against the goal's relation — no binding leaks out.

## What this buys you today

A fast, exact answer to *what in this corpus even claims to produce this
relation*. `<boil>` recalled in one lookup, no scan, no binding computed
early and thrown away.

---

**Next:** what a corpus does with a recalled candidate.
[Plans and subgoals →](12-plans.md)
</content>
