# The CNL surface

**Status: design, not code as of 2026-07-28; force-marking corrected 2026-07-30 (§2, §4, §5) to match
`forms_cnl.md` and the checked probes — this document previously and wrongly claimed force is unmarked and
concluded by a rule.** The companion to `model.md`, answering the item its §13 named *"the next design
conversation."* Where the two disagree, `model.md` wins — this document is downstream of it and cites it
throughout.

**What this document is.** What the front end emits, what the boundary does with it, and what that commits the
graph to. Four questions were open: how a statement is delimited, how nesting is written, how a rule is
expressed as data, and how much of the graph transcription commits to. This answers all four, and one that
turned out to be underneath them: *who unrolls a statement into a chain.*

Read `model.md` §§3, 6, 9, 11 first. Sections here are in dependency order.

---

## 1. The line: create, never merge

`model.md` §9 says the boundary **transcribes** and never interprets, and §12 invariant 6 tests it. But
*"interprets nothing"* is not operational — every encoding is a commitment, so the invariant needs a criterion
sharp enough to fail a diff.

> **The boundary may create nodes. It may never merge two.**

Everything the boundary does is minting: one node per bracket, one per role, one per mention. It never asks
*is this the same as that* — not for two occurrences of `"Paul"`, not for a pronoun and its antecedent, not for
two mentions of the same predicate. Every identification is a rule's decision, graded, and able to be wrong
(§4, §11 *IDs are plumbing*).

This is why transcription can be mechanical while interpretation is not: **merging is where judgement lives,
and merging is the one thing the boundary cannot do.** It is also total and injective, which is what makes
`model.md` §12 invariant 2 (round-tripping) checkable at all.

Two consequences worth stating before they surprise someone:

- **No interning, no vocabulary, no lexeme table.** Two mentions of `"discount"` are two nodes. `ugm`'s
  lexeme-as-licensed-bridge (`0026`) does not carry over; it was a merge performed at the boundary.
- **The graph grows fast, and per-mention.** This is the retention question of `model.md` §13, arriving
  earlier than expected.

### What the translator commits to, and what it does not

The LLM handles construction and ambiguity; the CNL is unambiguous by construction (§11). Splitting the labour
precisely:

| decides | who | why |
|---|---|---|
| which words fill which roles; where a statement ends; what is nested in what | the **translator**, written explicitly in the CNL | syntax. There is no ambiguity left for anyone downstream to resolve |
| what refers to what; whether this asserts or asks; whether it is true; whether it applies here | **rules, in the loop** | judgement. Revisable, gradable, explainable |

The translator's honesty is the whole guarantee on the first row — a well-formed but wrongly-bounded
translation is worse than a refusal, because it is silently confident (§9). Which is why the surface below has
**no free-text escape hatch**: nothing can be half-translated. Refusal is out-of-band, never a gap in a
structure.

---

## 2. The surface is a linearisation of the graph

Because transcription is mechanical, the CNL is not a language that *describes* structure — it **is** the
structure, written on one line. `model.md` §3's worked sentence, linearised:

```
s1: [ went | agent: Paul | agent: Mary | destination: the park | time: yesterday | means: bicycle+ ]
```

Reading it against the §3 diagram: the bracket is the occurrence node `e1`; each `role:` is a role node; each
filler is a participant node; `+` is `number = plural` as an ordinary attribute. Adding *"with Sue"* adds
`| companion: Sue` — one role node, two edges, nothing else moves.

**Roles are the surface convention `model.md` §11 licenses.** The engine grants no shortcut: a rule about
destinations matches `name = "destination"` on the role node explicitly. `destination:` is where that
boilerplate is generated, which is exactly where the privileged treatment is supposed to live — inspectable, in
the front end, never in the matcher.

### Roles are a closed class; content vocabulary is open

**Decided 2026-07-26.** The CNL ships a **fixed inventory of role names** — the prepositions and
relators: `agent:`, `patient:`, `destination:`, `time:`, `means:`, `of:`, `member:`, `when:`, `then:`,
`content:`. Content words — nouns, verbs, adjectives, the names of things — are **unrestricted**, and
the translator invents them freely.

This is natural language's own closed-class / open-class split, and it lands exactly where
`baroque-vs-fundamental` predicts: the closed set is small, structural, and designed in; the open set is
absorbed by the LLM and costs the system nothing.

**It settles `model.md` §13's *role node sharing*.** That question asked whether the role-name equality
rule is loaded once as KB data or restated per rule, and warned that the first *"risks becoming a
de-facto vocabulary through the back door."* The answer is that there **is** a shared vocabulary, and it
comes through the front door: declared, closed, and part of the language rather than of any KB.

**The build supplied the evidence, twice, before the decision was taken:**

- **Retrieval stopped discriminating.** A pattern reaching a participant through a role matches
  `name = "agent"` explicitly, so `"agent"` enters its vocabulary — and *every* world containing any
  agent then resembles *every* rule with an agent role (`units/recall.py`).
- **Default coreference nearly ate the graph.** A rule merging *"two nodes with the same name"* fuses
  every role node called `"agent"` into one, destroying every occurrence's participants
  (`tests/units/test_coref.py`).

Both are the same fact: **role names already behave as a shared vocabulary whether or not one is
declared.** Given that, declaring it and bounding it is strictly better than pretending otherwise.

**What it costs.** The inventory must be complete enough to express what the grammar needs, and
extending it is a change to the CNL rather than a KB edit — deliberately, since that is what keeps it
closed. A translator emitting a role outside the set must refuse rather than invent (§1).

**The engine still grants no privilege.** This is a front-end fact. A rule about destinations still
matches `name = "destination"` explicitly, and the matcher has no idea the class is closed — §11's *"the
CNL grants the shortcut the engine refuses"*, applied to the inventory as well as to the notation.

**Degree rides on the bracket.** A trailing `~band` grades the occurrence node it closes:

```
[ likes | agent: Paul | patient: Mary ]~sortof
```

Nothing else can carry a degree, which is `model.md` §3's fourth point holding: no edge ever needs one.

**Force is marked, but not as punctuation.** No `?`, no `!`, no special bracket-shape for a question versus a
command — that part of the original claim survives. **Corrected, 2026-07-30, against `forms_cnl.md`'s own
entry-format table (force carrier: "marked at the boundary") and the checked probes
(`units/force_probe_experiment.py`, `units/level_probe_experiment.py`), which this document contradicted
without either side noticing until it mattered for building the parser:** the translator *does* mark force,
as an ordinary tagged attribute on the utterance occurrence (`force: ask`), the same way it marks a role
filler or a coindex — not as a privileged syntax, just as one more small, closed-class judgement the
translator is asked to make (*"is this phrased as a question, a command, or a plain assertion"*), refusable
like any other mark. What the engine still owns entirely is what a given force *does* — `ask_to_goal`,
`command_to_goal` and their siblings are trivial, generic meta-rules that read the mark and mint a goal;
they recognize nothing. "Force stops being a router" (§9) still holds — it names what happens *after* the
mark exists, not a claim that the mark itself must arise unmarked from bare content.

---

## 3. Delimitation and nesting: brackets, labels, and the seal

**A statement is delimited by its brackets.** `[` is the begin marker, `]` the end marker (§6). Both become
nodes; the closing one is the tunnel's output port.

**Nesting is literal.** A filler may be a statement, and containment in the text is containment in the graph —
which is `model.md` §6's *nesting is physical*, with nothing in between:

```
s2: [ knows | agent: Paul | content: [ when: [ sees | agent: a lion | ... ] then: [ ... ] ] ]
```

**The seal is enforced by the namespace.** This is the part that makes the syntax earn its keep. Only a
statement may carry a label, and a label denotes its **end marker**. So:

- writing `s1` elsewhere attaches to `s1`'s output port — which *is* the crossing act of §6, one explicit
  wire, no permission rule, no crossing predicate;
- there is **no way to write** a reference to a statement's interior, because interiors have no names.

`model.md` §12 invariant 9 (*only end markers are attachable*) therefore holds by construction at the surface
rather than by a check. A hypothesis is a labelled statement like any other; *"suppose it rains"* and *"Paul
knows that…"* differ only in containment and content. There is no scope syntax, no world identifier, and — per
invariant 1 — nothing a rule could match even if it wanted to.

### Local coindexing is syntax; cross-statement identity is a decision

Inside one statement, *"a lion … it runs"* must bind, and it cannot bind by name (§4 — nothing matches by name
implicitly). So binding is written, with a statement-scoped local name:

```
s3: [ when:  [ sees | agent: x/a lion | patient: y/a gazelle ]
      then:  [ runs | agent: x | purpose: [ catch | agent: x | patient: y ] ] ]
```

`x/` introduces, bare `x` re-uses. These are plumbing IDs (§11), erased into node identity by transcription —
*not* merging, because the two occurrences never denoted two nodes to begin with.

The sharp line, and the reason it is safe:

> **Within a statement, identity is syntax. Across statements, identity is a graded rule decision.**

⚠ **This reverses `cnl_intake_design.md` §4.** That design ratified anaphora as a *boundary* concern — the SLM
resolves *"she" → "ada"* using exposed focus centers, and the substrate never sees a pronoun, on the argument
that a resolver *"bought nothing structural."* Under `model.md` it buys the thing the whole model is about: a
resolution that can be **wrong, graded, and reconsidered by a later step** (§9, §10 step 0). So pronouns and
descriptions now transcribe *unresolved*, as fresh nodes carrying whatever attributes the surface gave them,
and a rule decides. The old argument was correct against `ugm`'s engine, where reference had nowhere to be
graded; it does not survive graded matching.

---

## 4. A rule is a statement — and who unrolls it

There is **no rule syntax**. `s3` above is a rule, and it is a statement with `when:` and `then:` roles;
*"a customer gets the loyalty discount when…"* is the same shape. Nothing in the surface says *this is a rule* —
being a rule is a conclusion an interpretation rule reaches, **unlike force (§2, corrected), which is marked**.
The distinction is exactly `closed_class_rechallenged.md`'s: `when`/`then` is a *conventional shape* the
translator transcribes structurally (which filler goes in `when`, which in `then` — a closed-class judgement
about structure), and a separate, generic engine meta-rule decides what that shape *becomes* — a standing rule,
a plan step, a `requires` fact — never the boundary's call. One syntax, and the atomicity that makes *"if
tomorrow rains, bring the umbrella"* unbreakable is the bracket, not a rule construct.

That leaves the question underneath the other four. `model.md` §11 pins two constraints that look
incompatible:

- the assembler **may not unroll** a statement, or the outer driver would be doing semantics on day one — so a
  statement's *chain and markers must be described in the data*;
- the boundary **may not unroll** either, since choosing a chain is judgement.

Neither end can do it, which is the answer: **the unrolling is done by rules, in the loop.** It is what
`model.md` §10's step 0 is *for* — comprehension is ordinary reasoning, and what it produces is the wiring.

So the surface has **two registers**, both ordinary data:

| register | who writes it | who reads it |
|---|---|---|
| **prose** — §§2–3 above: statements, roles, nesting | the translator, via the boundary | interpretation rules, in the loop |
| **wiring** — units, gates, wires, begin/end markers | interpretation rules, at write-back | the assembler |

The assembler reads only the second, and wires only what it finds — it never sees a statement and does not know
what one is. `model.md` §12 invariants 3 and 4 are unaffected; invariant 6 gets sharper, because the boundary
now demonstrably touches only the first register.

**Bootstrapping, stated rather than discovered later.** Interpretation rules cannot themselves have been
interpreted, so the bundled ones **ship pre-written in the wiring register**. That is the same asymmetry
`model.md` §7 already requires for attention (*linguistic competence must be attended even when nothing is*),
showing up a second time — which is mild evidence it is a real seam and not a convenience. It is also the whole
of what is privileged: the bundle is ordinary data, replaceable and extensible, and a domain KB can add to it.

The wiring register's concrete syntax is the same brackets over a small role vocabulary —

```
u1: [ unit | pattern: … | gate: g1 | gate: g2 | out: o1 ]
w1: [ wire | from: o1 | to: g3 ]
```

— but the vocabulary itself is **open** (§7). What is settled is that it is data in the same notation, not an
API.

⚠ **This reverses `form_authoring_design.md` §6.** That arc cut full forms-as-KB-data, on the ground that the
only capability Python-hosted banks blocked was *"the machine reasoning about its own grammar in-engine"* —
ruled out at the time as *"not even a hypothesis in a remote future."* `model.md` §9 makes grammar-as-rules the
mechanism by which there is no interpretation stage at all, so the cut is void and the surviving `form KEY :
HEAD when BODY` finding — *rule-source CNL already spans the form language* — is the direct ancestor of the
wiring register. **Forms-as-data stops being one feature and becomes the whole game** (§9).

---

## 5. What transcription commits to, exhaustively

The closed list, so that anything else appearing in a transcriber is a defect:

| surface | graph |
|---|---|
| `[ … ]` | one occurrence node, plus a begin- and an end-marker node |
| `role:` | one fresh role node with `name = "role"`, edge from occurrence to it |
| a filler | one fresh node, edge from the role node to it |
| a bare word | `name = "word"` on that node — an ordinary crisp attribute, no privilege (§12 inv. 7) |
| `+`, `~band` | `number` / degree attributes |
| `x/…`, `x` | the same node — statement-local, erased |
| `label:` | binds the label to that statement's **end marker** |
| nesting | containment: the inner occurrence node is the filler |
| `force:`, `level:` (§2, corrected) | ordinary crisp attributes on the occurrence — marked, not concluded, and no different in kind from any other role or bare word above |

And the three things outside it (§9's irreducible seam): minting the turn's goal, and the actual reads and
writes. Marking force/level is a closed-class judgement about which of a small, fixed set of tags applies —
transcription, same as marking a role. What transcription still never does is decide what a mark *means* or
*leads to* — whether this content is true, which occurrence a reference resolves to, whether a rule applies,
what a supposition's scope is. Those stay rules, in the loop, every time.

**Costs, plainly.** Role-slotted CNL is verbose and unpleasant to read, which is acceptable because a human
is not the author — but it makes the translator's output hard for a human to *audit*, which was one of
`cnl_intake_design.md`'s claimed wins (*"the intent is the literal CNL sitting in the graph"*). A renderer back
to prose is the mitigation and is not designed. Second: one node per mention with no interning is a lot of
nodes, and it lands on `model.md` §13's retention question.

---

## 6. Worked: the `model.md` §10 walkthrough, in surface

The utterance *"Should Paul get the loyalty discount?"* transcribes with no force marker and no resolution:

```
g0: [ get | agent: Paul | patient: the loyalty discount | modality: should ]
```

Step 0's interpretation rules read that and conclude — as data — that it asks, that the `Paul` node is a
mention to be resolved, and what would satisfy the subgoal. The knowledge it is answered from is one labelled
statement:

```
s7: [ when:  [ and: [ member-for | agent: c/a customer | duration: over a year ]
                   | [ standing | agent: c | value: good ] ]
      then:  [ gets | agent: c | patient: the loyalty discount ] ]
```

Step 1 retrieves `s7`, and the wiring register written for it during comprehension is what the assembler turns
into a chain with two open gates. Step 5's follow-up *"what if he pays them off?"* is nesting plus one label
reference:

```
h1: [ suppose | content: [ settled | patient: p/the late payments ] ]
```

— and the crossing is whatever attaches to `h1`. Nothing in `s7` mentions a hypothesis, and `s7` is the same
statement in both steps. That is `model.md` §10's last two rows, at the surface.

---

## 7. Open

- **The wiring register's vocabulary.** Which roles a unit description needs, and whether a pattern is written
  in the same bracket notation as content (probably; it would make `model.md` §13's homoiconicity item nearly
  free, which is a reason to be careful rather than pleased).
- **The role inventory's contents.** *Settled* that roles are a **closed class** and content vocabulary is open
  (§2). Still open: which roles are in it; whether structural nesting (`member:`) belongs in the same class as
  thematic roles (`agent:`) or forms a second, more primitive tier; and how a domain that genuinely needs a new
  relator is served without reopening the class.
- **Containment direction is decided but under-documented here.** It runs **container → contained**, and the
  reason is not taste: a pattern atom has `out` and no backward traversal, so *"find something containing both
  of these"* is only expressible if the container is the source (`units/graph.py::contains`). The consequence
  for the surface is unwritten — *"x is in y"* transcribes as an ordinary occurrence, and deciding that it
  establishes **structural nesting** is an interpretation rule's job, not the transcriber's.
- **Bands.** `~sortof` names a band. The lattice survives from `ugm` and moves into matching, but which words
  name which bands, and whether that is authored data, is undecided.
- **Quantification and plurals beyond `+`.** *"every customer"*, *"three of them"*, mass terms. Untouched.
- **Rendering back to prose.** Needed for auditability (§5), unspecified.
- **A grammar for the CNL itself.** The surface is regular enough to parse trivially, which is the point — but
  nothing has been written, and *trivially* should be demonstrated, not asserted.

---

## What this settles in `model.md` §13

| §13 item | status |
|---|---|
| how a statement is delimited | **settled** — brackets; the label names the end marker (§3) |
| how nesting is written | **settled** — literal containment (§3) |
| how a rule is expressed as data | **settled** — it isn't; a rule is a statement with `when:`/`then:` (§4) |
| how much the transcription commits to | **settled** — §5's closed list, under *create-never-merge* (§1) |
| *who unrolls a statement* | **newly raised and settled** — rules do, into a second register (§4) |
| role node sharing | **settled** — roles are a CLOSED class, content vocabulary is open (§2). The inventory's contents remain open |
| homoiconicity | **unchanged** — but §7's first item is where it would arrive |
