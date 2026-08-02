# The kernel boundary — what may be Python, measured

> **The rule, stated 2026-08-02.** The Python layer is a **kernel** that, with its sidecar, decides what
> gets processed and processes it. It **may and must** do everything about the **substrate** — nodes,
> edges, refs, indices, the journal, focus, the instruction set, scheduling. It must **never** perform
> *business* computation, and *business* explicitly includes **anything we decided about how to represent**
> plans, time, goals, criteria, norms.
>
> **The kernel never really "sees" the representation above it.**
>
> **Why:** the system should be portable to any substrate — Rust, Excel macros, a redstone machine in
> Minecraft. Porting means re-implementing the kernel; the data carries over unchanged. Anything
> decided-but-written-in-Python must be re-decided by every port, which means it was never a
> representation in the first place.

**⭐ The operative test is not *"is this a control loop?"* but *"would a Rust port have to re-make a
decision here?"*** That reframing matters: it was going to be a count of Python control loops, and that
measures the wrong thing. `criterion.decide`'s Python loop is a problem not because it loops but because
it is Python that **knows what a criterion is**.

---

## 1. What was measured, and how much to trust it

Two passes, because the first is a proxy and the second is not.

**(a) Hardcoded upper-layer vocabulary** — string literals naming kinds and attribute keys of the
*decided* representation (`criterion`, `goal`, `subject_role`, `moment`, `force`, …). A module that is
pure substrate should name none of them. ⚠ **A proxy**: a module can know the representation without
using a literal, so this can undercount. It cannot overcount, which is what makes the zeros meaningful.

**(b) Dependency direction** — does a kernel module import anything above it? **Not a proxy.** A kernel
that imports the planner is not a kernel, whatever its literals say.

## 2. ⭐ The bottom is already clean, and that is the control

| module | upper-layer literals | imports upward |
|---|---|---|
| `graph.py` | **0** | none |
| `focus.py` | **0** | none |
| `activation.py` | **0** | none |
| `path.py` | **0** | none |

Four modules, ~1,300 lines, that genuinely do not see the layer above. **This is the control that makes
the rest of the measurement mean something** — if everything had scored non-zero the metric would just be
measuring how much code there is.

## 3. ✅ `isa.py` WAS the leak — closed 2026-08-02

The instruction set imported `driver` and `types`, so **a Rust port would have had to port the planner and
the type system in order to implement three instructions.**

| was | reached up to | now |
|---|---|---|
| `PLAN` | `driver.open_planning` | ✅ native `"plan"` |
| `STEP` | `driver.step` | ✅ native `"plan_step"` |
| `CHECK` | `types.check` | ✅ native `"check"` (spelling kept — see below) |
| `DISPATCH` | `dispatch.service` | kept — the substrate's single exit |
| `INVOKE` | `function.invoke` | kept — a stored program is substrate |

```
    before:   isa  ──imports──>  driver, types
    after:    isa  ──looks up──>  native  <──registers──  driver, types
```

**⭐ The fix keeps BOTH principles, which had genuinely collided.** `isa.py`'s own argument was right —
search is a **primitive**, because no sequence of `GET`/`SET`/`LINK` imagines a state, so it is not sugar.
What was wrong was concluding that a primitive must therefore be an **opcode**. `native.py` is a
name→callable table: the kernel reaches a primitive **by name**, and the module that owns it puts it
there. Registration lives beside the thing registered, never in the table — a dict of names in the kernel
would be the same leak with an extra hop.

⚠⚠ **Removing the `CHECK` opcode breaks `../pystrider`**, whose `strider/rules/app.mf` carries half a
safety guarantee on it: *"NO PLAN builds the unsafe app — carried by the parameter type. NO CALL builds it
either — carried by `CHECK`, at invocation time, which is the only thing that makes the declared type
binding on someone who bypasses the planner."* Their `.mf` must change to `NATIVE "check" F(b) "T"`; the
guarantee itself is unaffected, since it is the same primitive.

> ⭐ **An `asm.MNEMONICS` table was built to spare them that edit, and then REMOVED** when the constraint
> was withdrawn (*"i don't care about pystrider, they will adapt"*). Keeping it would have left a second
> name for one primitive, an asymmetry against `plan`/`plan_step` that had to be apologised for in a
> comment, and — worst — a **stale reason** in the source. `islands.md` §5 item 3 records exactly this
> hazard: *closing a gap can invalidate the justification for a design without invalidating the design,
> and a stale reason is what somebody copies into a new module because they trusted it.*

⚠ Enforced rather than achieved once: `check_the_KERNEL_cannot_see_the_representation_above_it` parses
`isa.py`'s import graph from source. A single `from . import driver` inside a handler would restore the
leak, pass every behavioural test, and never be noticed — which is how it got there.

## 4. The scale, stated honestly

```
kernel   1,899 lines   (graph, focus, activation, path, native, isa, asm)
above   10,005 lines   (27 modules — currently Python; must become DATA to port)
         ~84% of the engine is above the line
```

⚠ **This is not a defect count.** Most of those 10,005 lines are *supposed* to exist — the question is
what form they take. `criterion.py` deciding how a criterion meets a situation is correct work; it being
**Python** is what makes it unportable. The standing line *"microfunctions ship with the engine"* is about
**distribution**, not about being kernel: shipping with the engine and being written in the engine's
implementation language are different claims, and they have been conflated.

⚠ **`clock.py` is business by the rule's own example** (time is a representation we decided), and it
scores only 2 — which is the proxy undercounting, exactly as warned. Do not read the per-module numbers as
a ranking of how bad each module is; read the **zeros** as the finding.

## 5. What this changes about the next arc

`HANDOFF` §9 item 0 (the nested pursuit) and `islands.md` G (the sidecar) were two items about *Python
control loops*. Under this rule they are **one item about one thing**: Python that embodies decisions
rather than executing them. And a third, larger one joins them — `isa.PLAN`.

Ranked by how much of the boundary each one buys back:

1. ✅ **DONE — `isa.PLAN` / `isa.STEP` / `isa.CHECK`.** The only leak *below* the line is closed; the
   kernel now names nothing from the layer above.
2. **`criterion.decide`'s Python loop** (`islands.md` G) — **half done.** The *hidden channel* is closed:
   guidance was a `propose=` keyword and therefore a property of the Python caller, so the outer loop lost
   it (3 imagined states became 52, measured; `probe_hidden_decision.py`). A search now points at a
   `decider` node and resolves it when no hook is given — 3 and 3, with the no-decider control at 52.
   ⚠ The **loop itself** is still Python: reachable from the graph rather than handed in, which is what
   makes a search resumable, but not yet data. That remainder is the architecture's vacuity test and
   `loop.py`'s standing claim is still false until it lands.
3. **`driver.follow`** (`HANDOFF` §9 item 0, the nested pursuit) — design already done in
   `granularity.md` §7.

⚠ 2 and 3 are **above** the line, so they are migrations rather than boundary violations: the fix is to
make the thing that *decides* into data, not to move an import. `native.py` does not help there — a native
is still Python, and registering `criterion.decide` as one would launder the problem rather than solve it.

⚠ **Do not start a mass migration off the back of this document.** The ~84% is context, not a work item;
`north_star.md`'s bet is *content as data*, and the useful move is to keep converting the things that
**decide** — one at a time, each with the vacuity guard that the behaviour it drives is unchanged.
