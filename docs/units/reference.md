# `units` — reference

**What this document is.** The current state of the `units` substrate, organised by concept, with a runnable
example for each. It describes what *is*, never what changed. If something here is not true of the code, the
document is wrong.

- **Why a decision was taken** → `docs/units/decisions/` (one file per decision).
- **What is being worked on now** → `docs/units/STATUS.md`.
- **The original reasoning trail** → `docs/design/substrate_inversion.md`, kept as history and no longer
  maintained as a reference.

---

## 1. The claim

`ugm/` is a mutable graph with an interpreter stepping over it. `units/` inverts that:

> **The computation units are the substrate.** Each unit holds a whole subgraph as its state, fires when its
> input matches its pattern, and emits a new subgraph. **A graph is not a store; it is the value flowing on a
> wire.** Connections are built at run time, so depth is *assembled on demand* rather than pre-wired.

Two consequences that shape everything else:

- **Semantics are functional; the implementation memoizes.** A unit is `output = f(inputs)` over immutable
  values. Its mutable fields are a cache. That cache is why "output unchanged" is simultaneously the
  termination condition, the change-propagation rule, and the reason there is no retraction machinery.
- **Isolation is a calling convention, not a policy.** A unit cannot see what was not piped into it, because
  no address for it exists. Nothing has to be forbidden.

`units/` may not import from `ugm/` (asserted by `tests/units/test_no_ugm_import.py`).

---

## 2. Five minutes, end to end

```python
from units import Budget, Fact, Net, Triple, Var, given, mint, role

X = Var("x")
socrates, man, mortal = mint("socrates"), mint("man"), mint("mortal")

net = Net()
net.spawn(given("base", [Fact(socrates, role("is_a"), man)]))     # a fact
net.declare("MORTAL", (Triple(X, "is_a", man),),                  # a rule, not yet instantiated
            Triple(X, "is_a", mortal))
net.run(Budget(limit=1000))                                       # assemble + propagate to quiescence

net.derived_anywhere("is_a")        # {('MORTAL#1', socrates is_a mortal)}
net.why(Fact(socrates, role("is_a"), mortal))                     # an explanation tree
```

`declare` puts a rule in the **library**. Nothing is instantiated until a producer exists that could feed it,
so rules nobody needed are never materialised. `run` alternates assembly and propagation until neither
changes anything.

---

## 3. Values — what flows on a wire

```python
from units import Fact, Subgraph, mint, role

lion = mint("lion")                        # a node. The name is a label for humans; identity is the id
v = Subgraph([Fact(lion, role("roars"), mint("loudly"))])
v.predicates()                             # frozenset({roars})
v.by_pred(role("roars"))                   # the facts with that predicate
v | other                                  # union — values are immutable, every operation returns a new one
```

| type | what it is |
|---|---|
| `Node` | an identity. `mint(name)` always produces a **fresh** node — two `mint("mary")` calls do **not** match. |
| `Fact` | subject–predicate–object. All three slots are nodes; the predicate is a node too. |
| `Subgraph` | an immutable set of facts with a local per-predicate index. |

**Nodes are nameless in the sense that matters:** matching compares identities, never names. This is what
stops two independently created `mary`s from silently fusing. Names that *are* shared come from the
**vocabulary** (§7), which is the form set's to own.

---

## 4. Units — one class, and the taxonomy is read off the wiring

There is no fact/rule distinction, only **in-degree**.

```python
from units import Unit, branch, given, rule

given("base", [fact])                      # no inputs, fixed output
rule("R", lhs, rhs)                        # a pattern; its inputs are wired later
branch("H", add=[hypothesis], remove=[])   # carries its input through, modified
```

These are three constructors, not three types — they all build a `Unit`. And `kind` is **reported from the
current wiring**, not from which constructor was used:

```python
rule("R", lhs, rhs).kind        # "given"  — nothing is wired into it YET
net.units["R#1"].kind           # "rule"   — it has inputs and a pattern
net.units["H"].kind             # "carrier"— it has inputs and no pattern
```

So `kind` changes as the net is assembled, which is the point: an axiom, a hypothesis branch and a merge are
the same construct at different in-degree. A merge is a carrier at in-degree ≥ 2; a hypothesis branch is a
`branch` with something wired into it.

**What `run()` does, and the one line that matters:**

> **A rule emits only what it derived. Everything else emits its view.**

```python
u.view()      # the union of its inputs, plus `adds`, minus `removes` — ALL it can see
u.run()       # recompute; returns whether the output CHANGED
u.output      # a rule: just its conclusions. A carrier: its whole rewritten view
u.derived()   # what it concluded on its last run, recorded at run time
```

Because a rule emits only its conclusions, **a unit that matches nothing emits nothing and starves everything
downstream.** That is what makes silence a real gate, and it is why routing around a unit is a change of
meaning rather than a shortcut.

A unit's **in-degree bounds its epistemic reach**. There *is* a store — precisely what its in-edges deliver.
What is abolished is an unbounded *shared* store.

---

## 5. Patterns — how a unit says what it reads

```python
from units import Triple, Var, role
from units.match import Absent, Mint

X, Y, P = Var("x"), Var("y"), Var("p")

Triple(X, "is_a", man)          # every slot is a Var to bind or a Node to match
Triple(X, P, Y)                 # the predicate slot is uniform, so a predicate VARIABLE is free
Absent(Triple(X, "is_a", dead)) # negation as failure, over the value on the wire
Triple(X, "has", Mint("g"))     # head-only: mint a node, KEYED on the match that produced it
```

Two safety rules, checked at construction so a unit cannot exist with an order-dependent meaning:

- a variable in a negated atom must be bound by a positive atom;
- a variable in the head must be bound by the body. (`Mint` is not a variable — it names a function of the
  binding, which is the sound form.)

**The binding *is* the datum.** A unit's state is a subgraph, so the value of `?y` is simply a node in that
subgraph. There is no separate binding mechanism to get wrong, which is the difference between this and
marker propagation: markers cannot correlate two matches, so a two-place join becomes a cross-product.

---

## 6. The network — two wires, and who is allowed to be global

```python
net.declare(name, lhs, rhs)     # add a TEMPLATE to the library (not instantiated)
net.spawn(unit)                 # put a unit in the net
net.wire(producer, consumer)    # the OBJECT wire
net.run(budget)                 # assemble + propagate until quiescent
```

**The index** maps predicates to units. It indexes *computation*, never data — the subgraph values still
travel only along wires. It is the one permitted global structure; a second one would mean something had
leaked back into being a store.

**Two wires accrete in opposite directions:**

| wire | carries | accretion |
|---|---|---|
| **object** | what the computation is about | subset output — a rule's silence gates |
| **trace** | provenance: which firing produced which conclusion | append-only |

They must stay separate, or negation-as-failure starts answering *"was P mentioned in the derivation?"*
instead of *"is P absent from the world I was handed?"* — two different questions with the same syntax. A unit
sees the trace **only if its pattern asked for it** (i.e. names a firing predicate), and subset output is what
keeps that contained. Asserted by `Net.trace_leaks()`.

---

## 7. Vocabulary — roles and lexemes

```python
from units import role
from units.vocab import lexeme

role("is_a")        # a PREDICATE node, resolved through the form set
lexeme("lion")      # a WORD node ("#lion"), also the form set's
```

A role cannot be minted per occurrence (two independently minted `likes` nodes would not match) and cannot be
interned from a surface word at run time (that would fuse two utterances by name). So the vocabulary is **part
of the form set**: forms mint their roles once, at load.

> **The line: a form may mint through the vocabulary; an utterance may not.**

A `lexeme` is the same kind of thing one level down. *The word "lion"* is vocabulary — shared across every
utterance. *The lion* is a nameless entity node. That distinction is what makes reference possible without
lookup (§12).

---

## 8. How assembly decides

Every pass, for each template in the library and each unit whose current output could feed it:

**1. Does this producer offer anything?** Can any fact on the wire satisfy any atom of the pattern? This is
exact and fact-level, not predicate-level.

```
producer emits:  socrates is_a mortal
template reads:  ?x is_a man
                 -> predicates agree, objects do not -> REFUSED, nothing spawned
```

**2. Spawn, or join an existing instance?**

> A producer joins an existing instance only if it is **comparable** — ancestor, descendant, or identical —
> with **every** producer already wired into that instance. Two sibling branches are incomparable, so the
> second **spawns a new instance**.

The quantifier is load-bearing. `base` is an ancestor of both branches, so an *any*-test would let the second
branch join the instance holding the first, and the two hypotheses would collapse into one.

**This is where scope comes from, and there is no scope object.** Two instances differ by their in-edges;
hypothesis-ness rides in the subgraph they carry. Scope is a **chain**, never a key.

**3. Frontier first.** Candidates are tried deepest-upstream first. Two producers in one lineage can look
identical while the deeper one carries strictly more context — a hypothesis marker, a time index. Taking the
shallower one silently drops that context, which is exactly a bypass.

**4. Complete the pattern.** A rule reading two premises gets one from the chain and must get the other from
somewhere; the assembler wires it. A wire supplying a predicate no unit in the chain produces is a **join**; a
wire supplying a predicate a chain unit *gates* is a **bypass**, and is refused.

**5. What it cannot decide.** An all-variable atom (`?x ?p ?y`) is satisfied by *any* fact, so there is nothing
for the assembler to infer. **A pattern that declines to say what it reads must have its topology authored** —
typically a merge carrier assembled by whatever produced the pattern. See §12.

Every one of these decisions — including every refusal, with its reason — is recorded in the **assembly
journal** (§11).

---

## 9. Termination, and what "I don't know" means

```python
from units import Budget, Verdict

budget = net.run(Budget(limit=1000))
budget.verdict(found=False)     # Verdict.NO if fuel remained, Verdict.UNKNOWN if it was exhausted
```

An assembled net is a DAG, so a fixpoint is guaranteed and quiescence is reached when no output changes.
Recursion is not a back edge — it is **another instance wired on**, which is where "arbitrary depth by dynamic
assembly" actually happens. So the loop cannot be bounded by the topology; it is bounded by **fuel**.

`Verdict` refuses to be truthy, so an exhausted budget cannot silently become a negative answer.

`Net.wellformed()` reports the problems a *hand-wired* net can have that the assembler would never build —
cycles chiefly, because a cycle plus negation does not oscillate, it converges to a different answer depending
on work-list order, which is worse.

---

## 10. Negation — there are two, and only one is cheap

| kind | question | cost |
|---|---|---|
| `Absent` | is P missing from **the value I was handed**? | exact, immediate, no fuel — the value is finished |
| derivability | is P underivable **at all**? | open, semi-decidable, answered by fuel |

Conflating them is how a resource limit silently becomes a claim about the world. `Absent` is the one that is
free here, and it is free *because* values are bounded.

**Explicit negation** is a third thing: *"probably not P"* is a graded denial about a reified fact, not the
absence of one. `Absent` does not distinguish *unknown* from *denied*; the rule author chooses which is meant.

```python
from units import negation
negation.deny(view, fact, band)     # a <denies> node — talks ABOUT the fact without asserting it
```

---

## 11. Provenance — the trace, `why`, and the journal

```python
net.why(fact)                       # walk the trace value some unit actually holds
net.units["R#1"].why(fact)          # ...or from a named vantage
net.journal                         # the ASSEMBLER's own decisions, as facts
net.index_audit()                   # what the wiring permitted vs what actually fired
```

A firing record is built forward, as it happens — a derivation is a fact about a *run* and is not recoverable
afterwards. `why` walks what **fired**; it never walks the wires, because wires say only what *could* have fed
a unit.

The **journal** records `<spawned>`, `<wire_from>`/`<wire_to>`/`<wire_kind>`, `<declined>` with a reason, and
`<unused>` for a template accepted and never wired. **A refusal is a fact**, so *"what did you not consider?"*
has an answer. The journal is **observable, never writable** — nothing lets a unit wire anything.

Journal and firing predicates are provenance, so they are stratified: a unit that reads the trace is never
wired to the trace of a unit that reads the trace. Level 0 is the world, level 1 is about level 0, and level 2
would need a deliberate act.

---

## 12. Reference — decided, not resolved

*"The lion"* in the second sentence must reach the same entity as the first, and may **not** be looked up by
name. So reference is **decided**: intake mints a fresh node per mention, and rules decide which mentions are
the same entity.

```python
from units import discourse as D

m_a,   f_a   = D.mention("lion", D.INDEFINITE, [(role("roars"), role("#loudly"))])
m_the, f_the = D.mention("lion", D.DEFINITE,   [(role("sleeps"), role("#now"))])

net = Net()
net.spawn(given("discourse", D.utterance((m_a, f_a), (m_the, f_the))))
D.declare_all(net)                  # SELF, COREF, RESOLVED, AMBIG, DANGLING
net.run(Budget(limit=80000))
# -> m_the same_as m_a
```

Everything here is data — declared rules, no engine support.

| rule | what it does |
|---|---|
| `self_rule` | `?x <word> ?y ⇒ ?x <self> ?x`. Identity as **data**, so `Absent(?x <self> ?z)` **is** `?x ≠ ?z` |
| `coref_rule` | a **definite** mention corefers with an **indefinite** mention of the same lexeme |
| `ambiguity_rule` | two distinct antecedents ⇒ `<ambiguous>` |
| `resolved_rule` + `dangling_rule` | a definite with no antecedent ⇒ `<dangling>` |
| `symmetry_rule` | `same_as` is an equivalence; the *decision* is not, so symmetrise after deciding |
| `substitution_rule` | `?x ?p ?y ∧ ?x same_as ?z ⇒ ?z ?p ?y` — needs an **authored merge** (§8.5) |

Three things to know:

- **The decision is definiteness, not the word.** Matching on the lexeme alone merges *"a lion roars. A lion
  sleeps."* — two different lions. That is a wrong *decision*, not a substrate failure.
- **Ambiguity and reference failure are sayable.** Neither is resolved, but neither is silent either.
- **Substitution unions properties; it does not collapse identity.** Both mentions survive and both end up
  carrying both properties, so coref is sound for what rules *match* and silent for what is *counted*. A rule
  cannot remove — see `decisions/0032`.

**Coref is a chain position.** Downstream of a merge two mentions are one; downstream of a sibling that
declined the merge they remain two. Two chains may legitimately disagree about identity.

---

## 13. Degree — bands, not numbers

```python
from units import band as B
B.grade(view, fact, B.LIKELY)       # attach a band (this ASSERTS the fact)
B.band_of(view, fact)               # its band, or None
B.inheritance_rule()                # (lhs, rhs): a conclusion inherits its premises' band
```

The lattice is finite and `meet` is `min`. Finiteness is load-bearing for **termination**, not style: a
continuous degree can be revised by ever-smaller amounts forever.

Degree inheritance is one generic **rule** over the firing record — it reads the trace wire and writes the
object wire. `band.inherit` is a Python equivalent kept as a reference.

---

## 14. Authoring — the system's own output can become computation

```python
from units import authoring as A

enc = A.encode("MORTAL", lhs, rhs)   # a rule, as an ordinary subgraph
A.declare_all(net, enc)              # any subgraph -> templates in the library
```

A rule is describable as data, using the same reification vocabulary a fact uses. So a unit can *derive* a
rule and the bridge declares it — the system's own output becomes computation. The bridge adds **zero wires**;
the ordinary spawn policy still decides who feeds the new template.

> **The contract: a CNL front-end must target a subgraph, never the `Net` API.** Otherwise output→network
> needs a second implementation, the two drift, and the system can *say* things it cannot *learn*.

A round-trip through text would be unsound, not merely slow: rendering names nodes and re-ingesting resolves
names, which is the by-name fusion the substrate abolished.

---

## 15. Reading a net

```python
net.output_of("R#1")            # a unit's current output
net.derived_anywhere("is_a")    # {(unit, fact)} — a debugging read over units, not a query over data
net.upstream("R#1")             # transitive producers
net.instances["MORTAL"]         # which instances a template has
net.wellformed()                # problems a hand-wired net can have
net.trace_leaks()               # provenance that leaked onto an object wire
net.index_audit()               # wiring permitted vs firings observed; `unsound` must be empty
```

---

## 16. Invariants

Each is asserted by a test, because each is the kind of thing that is right on paper and wrong in the build.

1. `units/` imports nothing from `ugm/`.
2. Provenance never accretes onto an object wire (`trace_leaks`).
3. An assembled net is a DAG.
4. Anything minted per run is **keyed**, so re-running yields the same node and the output settles.
5. A fact's handle is a pure function of its three identities — any two reifications anywhere name the same
   node, with no registry.
6. Units never wire anything. If routing must ever be learned, units *propose* wirings as facts and the
   assembler stays the only writer.
7. An exhausted budget surfaces as `UNKNOWN`, never as `NO`.
8. Re-running a quiescent net changes no unit, no output, and no journal entry.

---

## 17. What is not built

- **FORCE** — assert / author / ask / suppose / command / retract as unit shapes. Designed, not built.
- **A sink** — *query = a unit whose output is the answer*. `Net.why` is a Python reader.
- **SUSPEND** — no continuation machinery, so no procedures and no world-touching calls.
- **A grammar** — a front-end onto the §14 contract.
- **Derived removal** — a rule cannot remove; see `decisions/0032`, which is an open question, not an
  oversight.
- **Fan-out scale** — measured on chains and wide nets; sibling-hypothesis fan-out is unmeasured.
