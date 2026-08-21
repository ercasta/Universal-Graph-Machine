# The guide — writing corpora and running the machine

For someone who wants to *use* UGM: author a world, run it, read what came out,
and embed it in a program. Everything here was run against the tree it ships
with; if an example is in a fenced block, it executed.

Where the other documents sit:

| | |
|---|---|
| **[the book](https://ercasta.github.io/Universal-Graph-Machine/)** | the tutorial — teaches the machine from scratch, no background needed |
| **this guide** | the practical reference — the whole surface, with a worked example each |
| **`authoring.md`** | what *bites*, ordered by how much time it costs before you find it. Read it after your first corpus misbehaves |
| **`rules-design.md`** | the argument — why the design is this and not something else |
| **`code-walkthrough.md`** | for changing the engine rather than using it |

---

## 1. Install and run

No dependencies, Python 3.9 or later.

```bash
git clone https://github.com/ercasta/Universal-Graph-Machine
cd Universal-Graph-Machine
python -m ugm.selftest              # 537 checks, 0 failing
```

Run a corpus and ask why it concluded something:

```bash
python -m ugm ugm/rules/delay.ugm --why "owed(ana,money)"
```

```
ugm/rules/delay.ugm: 14 ticks, ended quiescent

why owed(ana,money)?
  +owed(ana, money), via kb, licensed by applied(<compensate>)
    because +disrupted(bl204), via kb, licensed by applied(<cancel>)
    because +booked(ana, bl204), via kb, licensed by loaded(booked(ana, bl204))
    because -extraordinary(bl204), via kb, licensed by applied(<crewing>)
    because +cause(bl204, crew), via kb, licensed by loaded(cause(bl204, crew))
    because +cancelled(bl204), via kb, licensed by loaded(cancelled(bl204))
```

Nothing here is a log. Every entry records what licensed it and every
application records what it consumed, because the machine needs those records
for its own correctness — `--why` is a walk over structure that was already
there.

**The flags**, all of which compose:

```
python -m ugm <corpus.ugm> [--limit N] [--why TERM] [--save FILE]
python -m ugm --resume FILE  [--limit N] [--why TERM] [--save FILE]
```

`--limit` bounds the run (default 400) and **says so when it bites**: a run
that hit the limit prints `stopped at the tick limit; it had not finished`,
which is a different outcome from finishing.

---

## 2. The two layers

The loop is simple: look at the state, decide what to do next, do it. What you
supply comes in two layers, and keeping them apart is most of what authoring
well means.

**The world model** — how things relate, what follows from what, what causes
what, and which actions exist. This says what *is* and what *would happen*.

**Competence** — what to *do*. In any non-trivial world the possible actions
are legion, and knowing how the world works does not tell you what to reach
for: you can know exactly what every move of a Rubik's cube does and still be
clueless about solving one. Competence is scores, attention, when to stop, what
to try after what.

You can write the first and none of the second, and the machine will still run
— it will just derive everything derivable and stop when nothing changes. You
add competence when *deriving everything* stops being good enough.

---

## 3. The surface

A corpus is a `.ugm` text file. Comments start with `#`. There are seven kinds
of statement: `fact`, `rule`, `alias`, `action`, `expert`, `say`, and the
trigger forms (`after`, `frozen`, `learned`).

### 3.1 Facts and signs

```
fact +cancelled(bl204)
fact -extraordinary(bl204)
fact ? maybe(rain)
```

A **proposition** — `cancelled(bl204)` — claims nothing on its own. A **fact**
is a claim about one, and the sign is which claim:

| sign | means |
|---|---|
| `+` | asserted |
| `-` | **denied** — someone said it is not so |
| `?` | unsure — held, and known to be unsettled |
| *no statement at all* | **inherit**: nothing has been said |

The distinction that costs two levels of structure and buys the most: `-` means
*denied*, never *absent*. Silence is a third thing, and open-world reasoning
stays honest because of it. Absence has its own notation — §3.4.

!!! warning "`? p(x)` needs the space"
    `?maybe` tokenises as a **variable**, so `fact ?maybe(rain)` is read as a
    variable applied to `rain` and refused (*a fact may not contain a
    variable*). Write `fact ? maybe(rain)`. `+` and `-` need no space.

### 3.2 Rules

```
rule <cancel>     = implies( { +cancelled(?f) }, { +disrupted(?f) } )
rule <boil>       = causes(  { +heat(?a, ?w), +water(?w) }, { +boiled(?w) } )
```

A rule is `connective( { antecedent }, { consequent } )`, each side a
comma-separated list of signed members. The name in angle brackets is how
everything else refers to it — and the brackets are what keeps rule names out
of the relation namespace.

**There are exactly two connectives**, and the difference is not decoration:

| | lands in | means |
|---|---|---|
| `implies` | the **same** moment | derived — retract the antecedent and the conclusion goes with it |
| `causes` | a **later** moment | asserted — it persists |

Water you have stopped heating stays boiled, which is why a zero-delay cause is
still not an implication. If you write `implies` where you meant `causes`, your
world will quietly un-happen things.

A consequent may deny: `{ +served(?p), -wants(?p, ale) }` concludes one thing
and retracts another in the same move.

### 3.3 Variables

`?x` is a variable, scoped to its statement — `?w` in two rules is two
variables. A variable may sit in **relation** position too (`?p(?t)`), which is
what makes *apply the effect named by this ability* one rule instead of one
rule per ability.

Everything a consequent concludes about must be bound by the antecedent. A rule
that concludes about a free variable is refused at load, because the gate could
not deposit it anyway.

### 3.4 Absence — `no p(?x)`

`-p` means *someone denied p*. To ask whether anything *asserts* p — including
the case where nothing has ever spoken about it — use `no`:

```
rule <thirsty> = implies( { +is(?p, traveller), no served(?p) },
                          { +wants(?p, ale) } )
```

This is a distinct mode, not a spelling of `-`, and the reason is exact: a rule
that *materialises* a denial has to ask about absence first, so `-` could never
bootstrap it. The classic case:

```
rule <dark> = implies( { +lamp(?l), no lit(?l) }, { -lit(?l) } )
```

Three rules about `no`, all enforced at load with a message:

- **It checks; it does not bind.** Every variable in a `no` member must be
  bound by an earlier member. `no p(?x)` with `?x` free would mean *for no
  ?x* — a claim about a set that a member cannot make.
- **It cannot be concluded.** `no` in a consequent is an error: absence is
  asked, never asserted. To say something is not so, conclude `-p(...)`.
- **It cannot be a fact.** A fact states; `no` asks.

A denied proposition is absent too — `no` asks the prior question.

### 3.5 Entities, relationships and denotations

An **entity** is a labelless node: nothing but an id. Anything it answers to is
an ordinary claim about it, so a name is deniable like anything else. Rules
create entities with the `+` mint marker, one fresh node per firing:

```
rule <intro> = implies( { +said(?m, ?x) },
                        { +named(+person, ?x), +denotes(?m, +person) } )
```

`+person` is a marker, not a name — one node per marker per application, so
`+named(+person, ?x)` and `+denotes(?m, +person)` are about the *same* new
thing, and two firings are about two things.

A **relationship** reified this way has an id of its own, so it can be placed
in time, denied, or take part in another relationship. A **denotation** — a
compound expression like `attack(goblin, you)` — has no id: it is a *query*, a
criterion for picking things out.

You can hold the two apart with a declaration, and the gate will enforce it:

```
fact +relationship(agent)
```

A relation declared `relationship` may only relate things that have ids —
entities, atoms, other relationships. An expression in one of its argument
places is **refused**, on the record, with the declaration that forbade it.
Undeclared relations quote expressions freely, which is what keeps
`mention(m, attack(gob, you))` writable.

### 3.6 Aliases — shorthand for a structure

Reified structure is several lines where a flat fact was one. Name the shape
once:

```
alias sale(?seller, ?buyer, ?item) = { +is(+e, sale),
                                       +seller(+e, ?seller),
                                       +buyer(+e, ?buyer),
                                       +item(+e, ?item) }

fact +sale(elara, brin, ale)
```

The loader expands a use into its members and nothing downstream ever sees an
alias. The `+e` marker is the entity the shorthand stands up, and what it
becomes depends on where you use it:

| used in | `+e` becomes |
|---|---|
| a `fact` | one labelless entity, minted at load — several claims about one thing |
| an antecedent | a fresh variable joining the members — a **query** over the structure |
| a consequent | a mint marker still — one entity per firing |

So `rule <threat> = implies( { +sale(?s, ?b, ale) }, { +barkeep(?s) } )` reads
the structure however it was deposited.

**A nested occurrence is not expanded.** `mention(m9, sale(elara, brin, ale))`
keeps the compound exactly as written — nested is a *denotation*, and expanding
it would put words in the mention's mouth.

Refused, each with a message: a signed use (`-sale(...)` — a sign does not
distribute over several claims), `as` on a use, naming an alias fact, aliasing
a reserved word, and an alias that expands into itself.

### 3.7 Names, and rules as subjects

A fact may be named, in the same brackets a rule uses, because it is the same
namespace — names of *statements*:

```
fact <no-smashing> = +forbidden(smash(?x))
```

A rule is a node, so rules are ordinary subjects. Two claims you will reach for
constantly:

```
fact +overrides(<flag>, <grump>)     # defeat: <grump> loses where both match
fact standing(<watch>)               # height: <watch> is in the table above the floor
```

`overrides` is **defeat**, not ranking — the loser does not apply at all.
`standing` is competence: it lifts a rule so it is considered early.

A prohibition is checked at the **write**, never in the competition, so nothing
about which rule won can bypass it:

```
fact +fragile(jug)
rule <tempted> = implies( { +fragile(?x) }, { +smash(?x) } )
```

With `<no-smashing>` above loaded, the rule applies and the write is refused,
once, on the record:

```
refused(smash(jug), +, forbidden(smash(?x)))
```

Deny the prohibition later and the rule applies on its own — a refusal is a
deferral, not a rejection.

### 3.8 Actions

```
action pour(?vessel)
```

A signature and nothing else — no brackets. It declares that the agent *may
deliberately do* this, which makes the palette **discoverable**: `+action(?a)`
is an ordinary premise, so one fallback rule can range over every action,
including ones declared after it was written.

### 3.9 Channels — what arrived, and whether to believe it

```
say user: +raining(here)
```

An arrival is not a belief. What is written is *the channel said so*; a rule is
what turns it into a claim about the world:

```
rule <trust> = implies( { +says(user, ?p, plus) }, { +likely(?p) } )
```

That rule's consequent is a bare variable — *whatever the channel says, believe
it* — but only as `likely`, which is the rule's own contribution and is now an
ordinary claim a corpus can ask about. Trust is a rule, so it can be
per-channel, conditional, or argued with. If you write no trust rule, the
arrival sits there and nothing believes it. That is the intended default.

!!! warning "The most common surprise here"
    If a corpus reads a relation that nothing writes, the loader says so at
    load: *nothing writes `raining`, and a rule reads it — so that rule can
    never apply.* A `say` without a trust rule produces exactly that note.

### 3.10 Goals and reading backwards

```
fact +goal(boiled(kettle))
```

A goal makes the machine read its rules **backwards** — same rules, other
direction — and `--why` will show the plan alongside the trail:

```
asked for:
  boiled(kettle)  [held]  via <boil>
    water(kettle)  [held]
    heat(?a, kettle)  [open]
```

`[open]` is a subgoal nothing has satisfied. If no rule fits at all, the
machinery deposits `blocked`, and a corpus can key a rule on it — *when you get
stuck, do this*.

### 3.11 Experts

```
expert kitchen
rule <k1> = implies( { +tap(?t) }, { +source(?t) } )

expert bar extends kitchen
rule <b1> = implies( { +source(?s) }, { +usable(?s) } )
```

Rules following a declaration belong to that expert. One graph, one history,
separate rule sets — and `knows`/`extends` are ordinary facts, so inheritance
is one rule and *which rules has this expert* is an ordinary query.

### 3.12 Triggers — where competence is written

A trigger hangs a postcondition off a rule: when that rule applies and the
query holds, spend something.

```
after <serve> => attend(?p, 3)
after <done> => stop
after <spot> { +dangerous(?x) } => attend(?x, 5)
```

There are five things to spend, and none of them is a score:

| | |
|---|---|
| `attend(?x, n)` | think about this node — one the move itself bound |
| `unattend` | stop thinking about whatever it was |
| `stop` | end the run |
| `push(...)` / `pop` | suspend this line of work for another, and return |

`frozen after ...` marks a lesson a calibration process may not touch;
`learned after ...` marks one that was written by learning rather than by you.

**`attend` names a thing, never a rule.** That is deliberate: a rule id goes
stale the moment a rule is adopted, composed or renamed, so a corpus of
experience written against rule names stops *loading* rather than going quietly
wrong. `boost`, `damp` and `reset` were the rule-naming version and are
retired; a ranking-time `when` trigger is now an error with a message.

**`stop` is what makes *done* mean anything.** Without it a completion check
concludes and the agent carries on to quiescence anyway — measured, 64 moves
against 9.

---

## 4. Tools — arithmetic and outside answers

Two doors, both registered from Python on the loader whose corpus uses them.

**A computator** takes values and returns a value. It is evaluated inside the
application, so the whole thing stays atomic:

```python
from ugm.core.machine import Machine
from ugm.core.text import Loader

m = Machine()
kb = Loader(m)
kb.computator("plus", lambda a, b: int(a) + int(b))
kb.load("""
rule <total> = implies( { +hits(?a, ?n), plus(?n, 2) as ?t }, { +score(?a, ?t) } )
fact +hits(bo, 5)
""")
m.run(limit=40)
# score(bo, 7)
```

Note `as ?t` — that is how a computed value is bound.

**An answerer** is a request answered by a function, and it may **decline**,
which is a real answer:

```python
kb = Loader(m)
kb.answerer("oracle", "advice", lambda mach, e: kb.term("route(north)"))
kb.load("""
rule <ask> = implies( { +lost(?w) }, { +advice(?w) } )
fact +lost(hero)
""")
m.run(limit=60)
# answered(oracle, advice(hero), route(north))
```

Register tools on the **loader**, not beside it: a value turned into a node any
other way is a *twin* — the rule fires, the fact lands, and every question
about it answers nothing.

---

## 5. Embedding it

```python
from ugm.core.machine import Machine
from ugm.core.text import load, load_file

m = Machine()
kb = load_file(m, "world.ugm")        # or load(m, "...source...")
steps = m.run(limit=400)

m.holds(kb.term("owed(ana, money)"))  # '+', '-', '?' or None
kb.atoms["owed"]                      # the relation node, for graph queries
m.g.instances_of(kb.atoms["owed"])    # every instance of it
```

`m.holds(p)` returning `None` means *nothing has been said* — not false.

**Saving and resuming.** `m.save(path)` writes the session as *what it was
told*, rendered back into surface text you can read, diff and argue with:

```python
m.save("session.json")

back = Machine()
import json
back.replay(json.load(open("session.json"))["session"], limit=400)
```

Two things worth knowing about the round trip:

- A resumed session **does not act again** — the boundary is muted, so acts
  land as remembered rather than performed. Resume a session that opened a
  door and the door is not opened twice.
- It cannot carry a **tool's answers**. An answerer is a Python function, so a
  resumed session must re-register its tools.
- A labelless entity has no name to render, so the file gives it a surrogate
  handle (`entity-1501`) that keeps every fact about it landing on one node.
  The handle is a name the document mints, not a claim.

---

## 6. When it does not do what you meant

**Read the load-time notes.** The loader reports names that are read and never
written (*that rule can never apply*) and names that collide with the
machinery's own vocabulary. Both are almost always a typo or a fact you meant
to assert and did not.

**Ask why.** `--why TERM`, or `m.review()` / `m.blame()` from Python.

**Ask what it could not do.** A run that ends with something still wanted says
so; `blocked` and `unsupported` are ordinary facts you can key a rule on.

**Check the ticks.** `ended quiescent` means nothing further would change
anything. `ended stopped` means a rule spent `stop`. `stopped at the tick
limit` means neither — it was still working.

**Run the instruments** over your own corpus:

```bash
python -m ugm.probes.atlas         # islands, bridges, dead rules, pairs that could disagree
python -m ugm.gates.vocabulary     # names read and never written, with a planted typo as a control
```

**Then read `authoring.md`.** It is the shorter, meaner document: the traps
that have actually cost time, ordered by how long they hide.

---

## 7. Where to go next

- The **[book](https://ercasta.github.io/Universal-Graph-Machine/)** if you
  want the ideas rather than the notation.
- **`docs/authoring.md`** once you have written something that misbehaved.
- **`docs/rules-design.md`** for why any of this is the way it is.
- **`docs/world-model.md`** for entities, relationships and denotations in
  full.
