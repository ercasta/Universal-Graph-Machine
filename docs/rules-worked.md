# Worked representations — one scenario, every case

**Status: a design, worked.** Companion to [rules.md](rules.md); every block below is written in that
document's shapes and nothing else. ⚠ **Three of them did not fit**, and those are the point — see
*What this exercise found* at the end. Intended to become self-test fixtures, the way
[authoring.md](authoring.md)'s examples already are.

## Notation

```
p1 = on(a, b)                  a PROPOSITION — a hub. Claims nothing (§2.2)
e1 = entry(M4, p1, +)          an ASSERTION — locus, proposition, sign. Three members, fixed
     grade(e1, likely)         a fact ABOUT the entry, never a fourth member
M4 = moment(M3, <licence>)     delta + predecessor + licence (§2.1)
```

Anchored moments are `M*` (real), `I*` (imagined), `P*` (predicted). A rule's members are **generic**:
variables, no predecessor.

---

## The scenario

A kitchen. The agent wants boiling water. Anna is present. Something goes wrong.

### M0 — the world as first known

```
M0 = moment(—, <opened>)                      no predecessor: the first moment

p1 = attribute(kettle, contains, water)       an attribute is a hub, values are nodes
p2 = attribute(water, state, liquid)
p3 = on(kettle, stove)
p4 = attribute(stove, lit, false)

e1 = entry(M0, p1, +)   e2 = entry(M0, p2, +)   e3 = entry(M0, p3, +)   e4 = entry(M0, p4, +)
     licensed_by(e1..e4, <observation o1>)     grade(e1..e4, certain)
```

⚠ Note `p4`: *the stove is not lit* is written as a **positive** entry on an attribute whose value is
`false` — not as `entry(M0, lit(stove), −)`. Both are expressible and they mean different things:
the first says *I looked and it is off*, the second says *"the stove is lit" does not hold here*.
The first is a claim about the stove; the second is a claim about the moment. **Choose deliberately;
the shape will not choose for you.**

### The gas valve — what is NOT said

```
p5 = attribute(valve, open, true)
(no entry anywhere)
```

Nothing has been observed about the valve. There is no entry, so the chain walk returns nothing and
the answer is **UNKNOWN**. This is the case the whole three-state design exists for, and it is free:
it costs no node.

### M1 — Anna speaks

```
M1 = moment(M0, <utterance u1>)

u1 = utterance(anna, <at M1>)                  the saying is a world event
p6 = rain(this_afternoon)                      the CONTENT — note it carries its own time
e5 = entry(M1, p6, +)
     licensed_by(e5, u1)      said_by(e5, anna)      grade(e5, possible)
```

⭐ Two times, and they are not the same time. `M1` is when the **claim** was made; `this_afternoon`
is a member of the **proposition**. That is Reichenbach's speech-time / event-time distinction, and
the shape gets it right — but it means **the moment chain is not the only place time lives**, which
§4 should say and does not.

⚠ The alternative — making the locus a future moment — is not available and should not be wanted: a
moment that has not happened has no predecessor to hang from, and asserting into it would be
asserting that it *will* happen.

### M2 — a goal is taken, and planning branches

```
M2 = moment(M1, <goal g1 opened>)

p7 = wants(self, boiling(water))
e6 = entry(M2, p7, +)          licensed_by(e6, <the request>)
```

Planning imagines off `M2`. The imagined moments are **anchored** — they have predecessors and
individuals — and are distinguished only by their licence:

```
I1 = moment(M2, <supposed: applied R_light>)
I2 = moment(I1, <supposed: applied R_heat>)

e7 = entry(I1, attribute(stove, lit, true), +)     licensed_by(e7, <application of R_light in I1>)
e8 = entry(I2, attribute(water, state, boiling), +) licensed_by(e8, <application of R_heat in I2>)
```

⭐ Nothing marks these as "hypothetical" beyond the licence saying *supposed*. **Supposing takes no
time**: `I1` follows `M2` by succession, and no clock stamp is written. A real moment gets one.

### The rule that was applied — generic, no predecessor

```
R_heat = causes(
    { +attribute(?v, lit, true),  +on(?k, ?v),  +attribute(?k, contains, ?w),  ~vessel_open(?k) },
    { +attribute(?w, state, boiling) @certain,   −attribute(?w, state, liquid) @certain,
      ?attribute(?w, volume)                                                              } )

timing(R_heat, end→start, [4min, 7min])
```

⚠ **The rule says `+attribute(?w, state, boiling)` and never says `entry`.** The locus is an
indexical the rule cannot name (§2.4). `write` supplies locus, licence and grade; the author supplies
the proposition and the sign.

### M3 — the agent acts for real, and a prediction is deposited

```
M3 = moment(M2, <event: lit the stove>)
e9 = entry(M3, attribute(stove, lit, true), +)   licensed_by(e9, <dispatch d1>)  grade(e9, certain)

P1 = moment(M3, <predicted: R_heat applied at M3>)
e10 = entry(P1, attribute(water, state, boiling), +)   licensed_by(e10, <R_heat>)  grade(e10, certain)
      due(P1, [M3+4min, M3+7min])                      from R_heat's timing member
```

⭐ **`P1` is an ordinary moment.** An expectation is not a special proposition — it is a moment whose
licence says *predicted*, sitting as a sibling of what actually follows `M3`. That makes surprise a
comparison of two moments, which is machinery that already exists.

### M4 — nine minutes later

```
M4 = moment(M3, <event: clock advanced; looked>)
e11 = entry(M4, attribute(water, state, liquid), +)   licensed_by(e11, <observation o2>)
```

**The surprise** is not a stored fact. It is what `match` finds when a rule asks: `P1` predicted
`+boiling` due by `M3+7min`; `M4` is past that and carries `+liquid`, which the same rule's `−liquid`
says is incompatible.

```
p8  = surprised(self, P1, M4)
e12 = entry(M4, p8, +)      licensed_by(e12, <application of R_surprise at M4>)
```

### M5 — the discovery, which is *not* a change in the world

```
M5 = moment(M4, <event: looked at the valve>)

e13 = entry(M5, attribute(valve, open, false), +)     licensed_by(e13, <observation o3>)
```

And the correction to the record — note what it is **not**:

```
p9  = mistaken(e9)                       a proposition ABOUT an entry
e14 = entry(M5, p9, +)                   licensed_by(e14, <application of R_explain at M5>)
```

⭐ `e9` is untouched. *The stove was lit at M3* remains what the record says was believed at M3; `e14`
says that belief was wrong. Contrast the other revision:

| | what happened | written as |
|---|---|---|
| the stove **went out** | the world moved | a **new entry**, `attribute(stove, lit, false) +`, locus M5 |
| the stove **was never lit** | the record was wrong | `mistaken(e9) +`, locus M5, **e9 unchanged** |

Under a value stored on the node these are the same operation, which is how a system silently
rewrites its own history.

### S1 — a recognition, whose subject is a stretch

```
S1  = span(M3, M4)                       two members: start, end. Contents derived from the chain
p10 = waiting(self, boiling(water))
e15 = entry(S1, p10, +)                  the LOCUS is the span, not a moment
      licensed_by(e15, <application of R_recognise_waiting over S1>)   grade(e15, certain)
```

As time passes this is superseded rather than mutated: `span(M3, M5)`, a new span, a new entry.
⭐ **Recognising an ongoing pattern needs no unbound member** — that is versioning. Only *predicting
that it continues* would.

### A claim about claims

```
p11 = outranks(e5, <some entry of bo's>)
e16 = entry(M5, p11, +)      licensed_by(e16, <norm n1: authority>)
```

An ordinary rule **about** entries — which is exactly the direction §2.4 permits. A rule that
**wrote** `e5` itself would be forging provenance, and that is the direction it forbids.

### The agent's own state

```
p12 = doing(self, <pursuit pr1>)
p13 = phase(pr1, acting)
e17 = entry(M4, p12, +)      e18 = entry(M4, p13, +)
```

No new shape. *"What are you doing?"* is a chain walk, and *"why are you acting?"* is `licensed_by`
on `e18` — the trigger's own condition, which is the residue applied to the agent's control flow.

---

## What this exercise found

Three things did not fit, and one of them is a genuine correction to [rules.md](rules.md).

### 1. ⚠⚠⚠ "No entry" means INHERIT, not UNKNOWN — and the design says otherwise

`rules.md` §2 says *signed membership, three states: **present / absent / no entry***, and treats
no-entry as UNKNOWN throughout. **In a chain that is false.** The walk continues past a moment with
no entry and finds an older one, so:

> absence in an **anchored** moment = *unchanged, inherit from the predecessor*
> absence in a **generic** moment (a rule's member — no predecessor) = *don't care / unknown*

The two readings differ, and the difference falls out of §2.1's anchored/generic split rather than
being a wart. But it is currently unstated, and one consequence is a **hole**:

`R_heat`'s third consequent entry is `?attribute(?w, volume)` — *the volume changes, I cannot say to
what*. Under "no entry = unknown" that is written by writing nothing. But writing nothing in an
anchored moment means **inherit**, so the chain walk cheerfully returns the *old* volume. **The
one thing the operator was trying to say is the one thing that cannot be said.**

⭐ The fix is a fourth state, and it belongs on the entry rather than in the walk:

| sign | anchored meaning |
|---|---|
| `+` | holds here |
| `−` | does not hold here |
| `?` | **held before, does not now, and I cannot say what does** — invalidates without replacing |
| *no entry* | unchanged; inherit |

⚠ This is not the same `?` as the generic one, and they must not share a symbol without saying so.

### 2. ⚠⚠ §10's `expected(+boiling(w), by t+7)` is not writable in this vocabulary

It puts a **sign inside a proposition**, and a sign is a member of an entry. Written properly, an
expectation is `P1` above — an ordinary moment whose licence says *predicted*, with a `due` fact.

⭐ That is strictly better than the bespoke relation: surprise becomes a **comparison of two
moments**, which `deviates` already is, rather than a new predicate. §10 should be rewritten to say
so — the mechanism it wanted already exists and it invented a shape to reach it.

### 3. ⚠ Two times, and §4 only knows about one

`e5` — *Anna said it might rain this afternoon* — has its **locus** at M1 and its **event time** as a
member of the proposition. Both are correct and both are needed, but §4 talks only about timing
between a rule's two moments and never says that a proposition may carry its own temporal members.

⚠ The hazard is the recorded one: *one relation under several names*. Locus-time and event-time must
share the moment vocabulary or they become the sixth and seventh unrelated orders.

---

## Coverage

| case | shown at | exercises |
|---|---|---|
| plain fact, attribute as hub | M0 | §2.2 |
| negation vs a false-valued attribute | M0, `p4` | §2.2 — **the shape does not choose for you** |
| genuine UNKNOWN, costing nothing | the valve | §2.2 |
| utterance provenance, grade, speaker | M1 | §5.1 |
| goal as an ordinary proposition | M2 | §2.2 |
| supposition; imagined moments; no clock | I1, I2 | §2.1 |
| a rule, generic, naming no entry | `R_heat` | §2.4 |
| real action, dispatch as licence | M3 | §2.2 |
| prediction as a moment | P1 | finding 2 |
| surprise as a comparison, then a fact | M4 | §10 |
| world-changed vs I-was-wrong | M5 | §2.2 |
| span as locus; supersession | S1 | §2.3 |
| a claim about a claim | `p11` | §2.4 — read, never write |
| the agent's own doing | `p12`, `p13` | §2.2 |
| **partial effect — `?volume`** | `R_heat` | ❌ **not writable**; finding 1 |
