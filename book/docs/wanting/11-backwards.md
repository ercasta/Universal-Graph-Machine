# Reading a rule backwards

So far every rule has been read forwards: *these things hold, therefore this
follows*.

A rule can also be asked the other way: *what could produce this?* That
question is answered today by one shipped mechanism — **recall** — and it is
worth being exact about how far recall actually goes, because the rest of
backward reading (turning a candidate into subgoals, checking whether it
fits) is a design argument this project has made and not yet connected to
running code.

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

## Two requirements this still has to satisfy

Even though the mechanism is thin today, the requirements the fuller version
would have to meet are already settled, because they follow from what a rule
*is* rather than from how much of backward reading got built:

> Planning would read a rule **backwards**. Execution reads it **forwards**.
> Both readings must come from the same statement.

Two statements — one per direction — would drift apart with no way to detect
the disagreement, because neither is the premise of the other. There is one
node, `<boil>`, and direction is a **query over it**, never a field in it.
Recall already honours this: it reads the same rule object execution would
apply, off the same consequent.

> **The reading must be recoverable.**

Reading a rule backwards is reading its converse. *Four wheels ⇒ car*, run
backwards, licenses *a cart is a car* — legitimate as a hypothesis, wrong if a
planner treats it as entailment. Today recoverability is cheap to get right
because `recalled(<R>, p)` and an ordinary forward conclusion of `p` are
different relations, deposited by different code paths, and a corpus can
always tell which one it's looking at. A fuller backward reader would owe the
same guarantee under more pressure — a recalled candidate that gets
*expanded* has to keep saying so all the way down, and nothing today builds
that far.

## Why a rule can't do this itself

Recall is a function the machine runs, not something a rule computes, and
that's not an accident of how far the implementation got — it's forced.

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
`kb.computator` (Chapter 22), not a sixth floor primitive. A primitive a rule
invoked would hand back a binding the rule still couldn't use; the moment the
answer is instantiated, whatever computed it is doing the substitution too,
which makes it a request rather than a primitive addition to the floor.

> A floor item returns a **binding**. A service returns a **thing**.

Recall is the first, thin instance of such a service: given a goal, it
returns rule references, already resolved against the goal's relation — no
binding leaks out. Turning that into `+need(<R>, goal, <subgoal>)` — one
instantiated subgoal per antecedent member, the way Chapter 12 describes — is
the same shape of service, sketched, and not built. `docs/feature-requests.md`
and `horizon/34-not-built.md` track it; neither shows it as shipped, so this
chapter won't claim it is.

## What this buys you today

Not a planner. What it buys is a fast, exact answer to *what in this corpus
even claims to produce this relation* — the first move a planner would need,
and the one piece of it that turned out cheap enough to ship as an ordinary
index rather than a search. `<boil>` recalled in one lookup, no scan, no
binding computed early and thrown away.

---

**Next:** what a corpus does with a recalled candidate once you're willing to
follow it further — where the design goes, and where it currently stops.
[Plans and subgoals →](12-plans.md)
