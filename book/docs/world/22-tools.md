# Arithmetic is not reasoning

Nothing in this machine knows about numbers.

A numeral is an ordinary atom whose *name* happens to read as a number. `20`
is a node, exactly like `kettle` is a node. Nothing in the graph knows that
`20` is bigger than `17`, and no rule can work it out.

That's deliberate, and it's the right shape: arithmetic is a **function**,
and a function is not a search.

## A computator runs during the match

```python
kb = load_file(machine, "purse.ugm")
kb.computator("minus", lambda a, b: int(a) - int(b))
kb.computator("plus",  lambda a, b: int(a) + int(b))
```

```
rule <pay> = implies(
    { +pays($a, $b, $n), +purse($a, $x), +purse($b, $y),
      minus($x, $n) as $x2, plus($y, $n) as $y2 },
    { -purse($a, $x), +purse($a, $x2), -purse($b, $y), +purse($b, $y2),
      -pays($a, $b, $n) } )

fact +purse(anna, 10)
fact +purse(bo, 5)
fact +pays(anna, bo, 3)
```

```
$ python -m ugm purse.ugm
purse.ugm: 2 ticks, ended quiescent

what it believes, newest first:
  purse(bo, 8)
  purse(anna, 7)
  ...
```

A **computator** is a function given values and returning a value. It never
sees the graph. So it runs *during the match*, which means the whole
transfer lands in one application: a standing observer sees `purse(anna, 10)`
and then `purse(anna, 7)`, and **never a moment with both purses half-updated**.

Three details in that rule are load-bearing:

- **`as $x2`** names what the computator returned, so the consequent can use
  it. `kb.computator` resolves the returned value in the corpus's own
  scope — `minus` cannot hand back a fresh node with the same name as the
  numeral `7` the corpus already has, or the rule would fire and every
  question about the result would answer nothing.
- **`-purse($a, $x)`** retracts the old amount. There is no grade of belief
  between believed and not; a proposition is anchored or it isn't. Erasing
  the stale purse and asserting the new one, in the same application, is
  what "update a value" means here.
- **`-pays($a, $b, $n)`** consumes the trigger. Without it the rule matches
  again next tick — its own antecedent is still fully true, since nothing
  about `pays(anna, bo, 3)` changed — and an application that changes
  nothing is offered again (Chapters 19–21) until the tick limit cuts it
  off. This is Chapter 7's turn loop, arriving in a corpus instead of the
  machinery.

## A tool answers through a fact, a tick later

A **tool** is a request answered by a function rather than by a search.
Unlike a computator, it can talk to the world — a clock, a file, a network —
and its answer therefore lands **after** the request, once the gate notices
it was asked.

```python
pre = load(machine, "", scope="shop")
pre.answerer("calc", "minus", lambda m, req: m.g.atom(
    str(int(m.g.show(m.g.members(req)[1])) - int(m.g.show(m.g.members(req)[2])))))
kb = load_file(machine, "shop.ugm", scope="shop")
```

```
rule <spend> = implies(
    { +purse($b, $n), +buying($b, sword), +cost(sword, $c),
      no minus($b, $n, $c) },
    { +minus($b, $n, $c) } )

rule <apply_it> = implies(
    { +answered(<calc>, minus($b, $n, $c), $r) },
    { -purse($b, $n), +purse($b, $r), -buying($b, sword),
      -answered(<calc>, minus($b, $n, $c), $r) } )

fact +purse(bo, 10)
fact +cost(sword, 3)
fact +buying(bo, sword)
```

```
$ python -m ugm shop.ugm --ask "purse(bo, 7)"
shop.ugm: 3 ticks, ended quiescent
purse(bo, 7): believed
```

Registering the tool has to happen through the **same corpus scope** the
rule that names `<calc>` will load into — `pre = load(m, "", scope="shop")`
first, `pre.answerer(...)`, *then* `load_file(..., scope="shop")` — because
a value marshalled outside that table is a twin of the node the corpus
writes, not the node itself. That's the same twin trap `as` guards against
for a computator, one door along.

Both `<spend>`'s `no minus(...)` guard and `<apply_it>`'s consuming
`-answered(...)` are necessary for the same reason as the computator's
`-pays(...)`: nothing here forgives a rule that keeps matching its own
already-satisfied antecedent.

Use a **computator** wherever the arithmetic is pure. Keep a **tool** for
anything that talks to the world.

And the rule for both:

> **A tool proposes; it never concludes.**

The answer arrives as a fact — `answered(<calc>, request, result)` — and an
ordinary rule decides what to make of it. A tool that concluded directly
would be a piece of the world's authority hidden inside the machinery,
unattributable and unarguable.

This is also why the tool's own binding is deposited — `answers(<calc>,
minus)` — rather than kept in a registry. The machinery knew which function
answered which request, and no rule could ask.

## When a change takes more than one tick

If your transfer waits on a die roll, a person, or anything outside, then
part-way through the purses genuinely have not changed — and there is no
mid-way value to assert; a proposition is asserted or it isn't, nothing in
between. The honest move is: don't touch the amounts until settlement, and
mark the in-between state with an ordinary fact.

```
rule <trust_bank> = implies( { +says(bank, $p), no $p }, { +$p } )

rule <start> = implies(
  { +pays($a, $b, $n), +purse($a, $x), +purse($b, $y), no pending($a, $b, $n) },
  { +pending($a, $b, $n) } )

rule <complete> = implies(
  { +pending($a, $b, $n), +confirmed($a, $b),
    +purse($a, $x), +purse($b, $y),
    minus($x, $n) as $x2, plus($y, $n) as $y2 },
  { -purse($a, $x), +purse($a, $x2), -purse($b, $y), +purse($b, $y2),
    -pending($a, $b, $n), -confirmed($a, $b), -pays($a, $b, $n) } )

fact +purse(anna, 10)  fact +purse(bo, 5)  fact +pays(anna, bo, 3)
```

Run to quiescence with no confirmation yet:

```
purse(anna, 10)   purse(bo, 5)   pending(anna, bo, 3)
```

Then the bank speaks — `say bank: confirmed(anna, bo)` — and the run
continues:

```
purse(anna, 7)   purse(bo, 8)   -- pending, pays and confirmed all consumed
```

No marker anyone forgot to check: `pending(...)` is either there or it
isn't, and while it's there the purses simply have not moved. An observer
that reads `purse(anna, $x)` mid-transfer gets the *true, unrevised* answer,
not a special third value meaning "ask again later."

The tempting alternative — skip `pending` and just leave the purse
untouched — works by accident here and fails the moment two transfers
overlap, for exactly the reason Chapter 15 rejected grades: an unmarked
"in progress" state is a separate read from the value it qualifies, so an
observer that doesn't think to check it sees a settled state that isn't
one.

## Where a model would go

A last note, because it's the question everyone asks.

If you wanted to put a learned model in this machine — a classifier, a
language model, a scorer — where would it go?

**Where there is no algorithm.** Not in the match, not in the read: those
have definitions, and a model there can only approximate something already
correct.

The place a model belongs is where the current answer is a guess: what
comes to mind (Chapter 27), and how good an option looks. And the shape it
should return is a **pair** — a score (*how good*) and a strength (*how
sure*) — because those are two different things and this design has already
learned not to collapse them into one number.

A model reached through a tool is data like anything else: it proposes, a
rule decides, and the decision is an ordinary belief like any other —
attributable to `answered(<model>, ...)`, arguable, and revisable.

---

**Next:** clocks, calendars, and what ordering is left.
[When things happened →](23-time.md)
