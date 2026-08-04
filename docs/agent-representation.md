# We are building an agent — what that requires of the representation

This is the clean statement. [expressiveness-and-uniformity.md](expressiveness-and-uniformity.md) and
[defining-terms.md](defining-terms.md) are the reasoning trail that produced it, including the wrong turns;
this document is what survived.

## 1. What is being built, and what is not

**A reasoning agent for a narrow domain**, whose rules and experience are **authored into KBs by people**.
The one thing wanted on top is **composing knowledge from different domains**.

**The benchmark is an LLM doing agentic work, on two axes:**

* **Inspectability** — an LLM's account of its reasoning runs *alongside* the computation and cannot be
  addressed, queried or held to. Here the account **is** the computation.
* **Computational cost** — an LLM re-derives everything on every call. Here, **reasoning that has been
  done stays done**.

⚠⚠⚠ **Guarantees are not a goal and never were.** Not decidability, not completeness, not soundness under
composition. Nothing in this design is rejected for failing to offer proofs, and **bounded and defeasible
is the design rather than a shortfall**. The lineage is Soar, PRS, Maes, Smith's 3-Lisp, Bowen & Kowalski,
Hobbs — none of which offered guarantees, and all of which produced agents. The formal tradition is worth
reading for **where the cliffs are** and worth ignoring for **where to sail**; it answered a different
question well.

⭐ The agent's own standard is **task competence plus graceful degradation** — does it handle the case,
and when it fails does it fail *visibly and recoverably*? Which this project already states three ways:
*silent failure is acceptable, unrecorded failure is not*; *blocked-on-ignorance is a third search
outcome*; *"UNKNOWN — I did not finish looking within fuel" is an honest answer.*

## 2. Execution and readability are different obligations

**Python may execute.** What may not be Python is the **data** and the **decisions**.

⭐⭐ **The reason is an asymmetry, not a preference: representation debt compounds, execution debt does
not.** A Python function swaps later behind its wrapper — done three times in this codebase, each bounded,
each changing nothing outside the wrapper. A representation is referenced by every rule that touched it;
when *an edge names an identity, never a version* landed, a dozen fixtures went red and the corpus was
rewritten. **Representation is the irreversible commitment; execution is the reversible one.**

So the obligations are:

| | |
|---|---|
| **execution** | may be Python, indefinitely |
| **the data it reads and writes** | must be nodes — *could a rule have produced this value?* |
| **the decisions it makes** | must be recorded with their alternatives and reasons, or the residue has a hole |
| **the trace it leaves** | must be **re-executable**, not merely legible — see §3 |

⚠ A Python function that decides *silently* breaks the residue — not because it is Python, but because
the decision left no trace. One that records what it chose, what else was available and on what basis
leaves a perfectly good one. That is a cost argument, not an impossibility.

## 3. ⭐⭐⭐ The core requirement: one representation, executable and readable

A concept must be usable in **three** ways, and there must not be a separate representation for each.

> To simulate a game the agent must be able to **execute** *taking turns* — not only describe it or
> recognise it. And there cannot be one *taking turns* for describing and another for executing. When it
> is executed it must leave a trace that can be read, and **the trace must itself be executable.**

The three readings:

| reading | question | *taking turns* |
|---|---|---|
| **recognise** | did this happen? | this past sequence alternated |
| **check** | would this be allowed? | this candidate plan alternates |
| **generate** | what happens next? | it is B's move |

⭐⭐⭐ **One object, three readings, distinguished only by what is bound.** A constraint with everything
bound is a **check**. A constraint read over a finished trace is a **recognition**. A constraint with one
position unbound is a **generator** — *solve for the agent whose move it is*. Nothing else has to exist.

This is the project's own finding extended by one: *advice-over-sequences.md* already says **recognition
and prescription are the same predicate read two ways**. Generation is the third way, and it is the one a
simulation needs.

⚠ **Two representations of one concept is the failure this rules out**, and it is not hypothetical — it
is the shape of every defect this codebase has recorded about duplication: *carrying one fact in two
shapes is what blocks a swap*; *a dormant twin rots*; *an island is created by the second caller*. A
describing *taking turns* and an executing *taking turns* would be two implementations of one meaning,
free to drift, with nothing holding them together.

### The symmetry, stated as a loop

```
    concept ──execute──▶ trace ──read──▶ concept
```

**Both arrows must exist.** Executing leaves a trace; the trace can be read back into something
executable. If either arrow is missing the concept has two representations after all — one that ran and
one that describes what ran.

## 4. ⭐⭐ Half of the loop is already built

`application.py` — **`compile_episode`** reads an episode and writes a function that invokes, in order,
each operation the episode recorded, with generalised bindings as parameters and everything else as a
`Ref` to the exact node. It is stored like any other function, runs like any other function, and *"can
itself be recorded in a later episode."*

**That is `trace ──read──▶ concept`, built, for sequences of operator applications.** The right arrow
exists and closes.

What else is already in place:

* **Executable things are graph data.** A microfunction is nodes; `function.define` authors one; a rule
  can author a rule.
* **The trace is graph data.** Applications, episodes, bindings — each a node, each addressable.
* **A goal constraint already reads two ways**: `holds` checks it, and the planner **satisfies** it. So
  *constraint as generator* is not a new idea here, it is the planner's whole operation.
* **Replay exists** — `open_replay`, `resume_replay`, `alternatives`, `matching_alternative`.

## 5. ⚠⚠⚠ What is missing, precisely

**A constraint and a procedure are still two unrelated things.** `type taking_turns` would be checkable
and not executable; a microfunction that alternates would be executable and unreadable as a claim. Nothing
relates them, so the game simulation would need both.

Three consequences, in the order they bite:

1. **A constraint cannot be run as a generator.** The planner solves constraints *about the world*; there
   is no way to say *solve this constraint for the next move* and get an answer. This is the single
   missing piece for the simulation case.
2. **The trace of a protocol records the moves, not the protocol.** Executing turn-taking leaves a trace
   of moves. Nothing in it says *this was taking turns*, so reading the trace back gives you the moves and
   not the concept — the right arrow closes for **sequences** and not for **patterns over sequences**.
3. **A plan step does not record who filled which role** (probed): `extend_trace` carries `function`,
   `touched` and `after`; the bindings live one node away on the candidate. So even *recognition* of
   turn-taking has nothing to read. ⚠ And `trace_tuple` hands the plan back as Python tuples, which fails
   *could a rule have produced this value?*

## 6. What this changes about the design list

Ordered by what the agent gains, not by what is tidy.

| | why, against §1's benchmark |
|---|---|
| **bindings on the plan step** | ⭐⭐⭐ prerequisite for all three readings; nothing else can proceed |
| **the shared ORDER core** | ⭐⭐⭐ **this is what cross-domain composition needs.** Two independently authored KBs that both speak of sequences must share it or they cannot compose — and *composing domains* is the one nice-to-have |
| **relative index over a named order** | ⭐⭐ the form the three readings are written in |
| **the plan / trace as a constrainable subject** | ⭐⭐ where a pattern over a sequence lives, preserving prefix-monotonicity (`SAFETY_SORTS`) |
| **constraint-as-generator** | ⭐⭐⭐ the missing third reading; the simulation case |
| **declared relation properties** | ⭐⭐ a narrow authored domain **stipulates** its relations, so a model's prior is unreliable — declaring them is right here even though *friendship is symmetric* is free to an LLM |
| **a reference set for *fast*** | ⭐ and it may be **authored**: if experience comes from authors, an author may simply write what fast means for this route. Probe the authored form first |
| ~~quantified / negative conditions~~ | ✅ **closed** — `has 0 above` already parses and checks |

⭐⭐ **And the closed class gets an admissibility test it did not have.** *When may something be a
primitive?* had one answer — *every decision it embodies can be an argument*. Scope adds a sharper one:
**something is closed class iff two independently authored domains must agree on it in order to compose.**
Order passes. `friend_of` does not.

⚠ **Cross-domain alignment is authored, and that is what keeps it honest.** *"Our `client` is their
`customer`"* is a **knowledge claim with a speaker**, which discourse already ranks and records — so it
leaves a residue (*we treated them as the same because Anna said so*) where a translation layer built into
the engine would leave none. Alignment stays **data**, never machinery.

## 7. The test to apply

Not *can the representation express this* — that is a theorem prover's question, and asking it produced a
wrong answer once in this project's notes already. The agent's version:

> **Produce two situations in which the agent should ACT differently. Does it?**

And for anything claiming to be executable-and-readable, the second test:

> **Execute it, read the trace, and execute the trace. Do you get the same behaviour?**

⭐ The first already has a precedent here: the guard-address probe reported *a worse plan, then no plan at
all* — behaviour throughout, never expressibility. The second has one too: `compile_episode` is exactly
that loop, and it is the model for everything above.
