# "No" and "I don't know"

At the end of Part 1 we left a rule with a dragon inside it:

```
?someone is thief when ?someone is a suspect and ?someone is not cleared
```

To use that `not`, the machine does something bold: it goes looking for a reason
someone is cleared, and **if it can't find one, it concludes they're not.** This
chapter is about when that move is brilliant — and when it's dangerous.

## Absence isn't always evidence

Look someone up in the school directory and they're not there. Two honest
reactions:

- *"Then they don't go here."* — you trust the directory to be **complete**.
- *"Then I can't tell — the directory might be missing someone."* — you don't.

Neither is wrong. It depends on whether your list of facts is the *whole* story.
These two attitudes have names, and the machine can adopt either one.

## The closed world: "if I can't prove it, it's false"

By default, the machine **closes the world**. It assumes that what it can't
establish is false. This is the **closed-world assumption**, and it's why the
thief rule works: the machine has no evidence cy is cleared, so — world closed —
cy is *not* cleared, and the rule fires.

Closing the world is exactly right when your facts really are complete: a
chessboard, a train timetable, a finished case file. If it's not on the board,
it's not on the board.

## The open world: "if I can't prove it, I don't know"

But suppose the case *isn't* closed — new clues could still turn up. Then treating
"no evidence" as "false" is reckless. So the machine can instead **keep an open
mind**: what it can't establish is simply **unknown**, not false.

Meet **zz**, a name the machine has never heard a single fact about. Ask the same
question two ways:

```
is zz thief          (closed world)   →  no (assumed)
is zz thief          (open mind)      →  unknown
```

Same question, same (empty) evidence — but a very different, more honest answer.
Closed-world says *"nothing points to zz, so no."* Open-minded says *"I have
nothing on zz, and I won't pretend otherwise."*

!!! tip "In the playground: what the toggle really does"
    The playground's **keep an open mind** switch flips exactly this. But watch
    carefully — it only changes answers the machine **couldn't prove anyway**:

    - `is zz thief` and `is ada thief` → **`no (assumed)` becomes `unknown`** ✅
    - `who is thief` and `is cy thief` → **no change** — the machine can *prove*
      these, and proof doesn't care about your attitude toward absence. (The
      `(assumed)` tag is the tell: only tagged answers can flip.)

    So if you toggle it on a question the machine can already answer and nothing
    happens — that's not a bug, that's the point. Open-mindedness only matters
    where evidence runs out.

## The three answers

Most machines have two answers. This one has three, and the third is the whole
lesson of this chapter:

| Answer | Meaning |
|--------|---------|
| **yes** | The machine established it. |
| **no** | It couldn't — *and, closing the world, it treats that as false.* |
| **unknown** | It couldn't — *and it declines to guess.* |

The deep point: the machine's ordinary **"no" usually means *"I found no reason
to believe it,"* not *"this is impossible."*** That's a humbler, more accurate
kind of "no" than most software offers — and switching to an open mind makes the
humility explicit by turning it into "unknown."

Because that kind of "no" is held only *until better evidence turns up*, it has a
name — a **defeasible** answer — and the machine is built to take it back cleanly
when the evidence changes. There's [a short appendix
note](../appendix/index.md#defeasible-reasoning) on it, and Part 4 shows the
belief-revision machinery underneath.

??? info "Deep dive: negation-as-failure"
    The technical name for "look for a proof, and if you fail, conclude the
    opposite" is **negation-as-failure**. It's what the 🔍 checks in the
    playground's step view are doing: to decide *cy is **not** cleared*, the
    machine raises the positive goal *cy is cleared*, chases it to exhaustion,
    and reads the **failure** as the answer. The [appendix has
    more](../appendix/index.md). It's efficient and intuitive — and its one risk
    is exactly the closed-world trap this chapter is about.

??? info "Deep dive: can it ever *prove* something false?"
    Yes — and that's a stronger "no" than the closed-world default. If you teach
    the machine that two categories are incompatible (*a penguin is **not** a
    flyer*), then for a penguin it doesn't merely *fail* to prove flight — it
    **proves the opposite**. Logicians call this an *entailed* negation, a "hard
    no," as trustworthy as a yes. It's a more advanced capability than the
    everyday no-vs-unknown you can play with here, but it's worth knowing the
    machine can go that far.

## Why this is the heart of the book

A machine that can't tell *"no"* from *"I don't know"* will confidently mislead
you the moment its information is incomplete — which, in the real world, is
always. This one can tell the difference, and it lets *you* choose which stance
fits the problem. That single choice — closed world or open — quietly shapes
every answer it gives.

## Try it

In the playground, ask `is ada thief`. Note the `no (assumed)`. Now tick **keep
an open mind** and ask again — watch it become `unknown`. Then try the same
toggle on `who is thief` and confirm it *doesn't* change. Feel the difference
between "proven" and "assumed" — the machine is already telling you which is
which.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button .md-button--primary }

---

**Next:** we keep saying the machine is "lazy on purpose." Time to see exactly
what that means. [Only chase what you need →](06-only-what-you-need.md)
