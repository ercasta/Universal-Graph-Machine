# Asking questions

A world full of facts isn't much use if you can't ask about it. This chapter is
about the other half of the conversation: **questions**. We'll use this little
world throughout —

```
ada is a suspect
bo is a suspect
cy is a suspect
ada is nervous
bo in library
ada is alibied
```

— and just ask things.

## Yes-or-no questions

Start any yes/no question with **`is`** (or **`does`**). The machine checks its
world and answers:

```
is ada a suspect          →  yes
is bo nervous             →  no (assumed)
is bo in library          →  yes
is ada in library         →  no (assumed)
```

Notice the pattern: a yes/no question is just a *fact with a question mark*.
`ada is nervous` is a statement; `is ada nervous` asks whether that statement
holds. If the machine can establish it, you get **yes**; if not, **no** — and
look closely at how it says no: **`no (assumed)`**. That little tag is the
machine being honest about *what kind* of no this is. We'll come back to it.

## "Who" questions — let the machine find them

Often you don't know *who* fits — that's the whole point of asking. Start with
**`who`** and leave the subject blank:

```
who is nervous            →  ada is nervous
who is a suspect          →  ada is a suspect, bo is a suspect, cy is a suspect
```

The machine sweeps its world and hands back **everyone** who fits. Ask
`who is nervous` and it finds ada; ask `who is a suspect` and it finds all three. This
is the same kind of question we opened the book with — `who is thief` — except
that one needed *rules* to work out the answer (that's the next chapter).

## "Why" questions — make it show its work

This is the machine's party trick, and you met it in Chapter 0. Put **`why`** in
front of any fact and it hands back the *reasoning*, not just the verdict:

```
why cy is thief
```

gives back the trail of rules and facts that led there. For a fact you simply
*told* it, the "why" is short — *"because you said so."* For a fact it *worked
out*, the trail shows every step. We'll lean on `why` heavily once rules enter
the picture.

## The three answers: yes, no, and *I don't know*

Most machines only ever say yes or no. This one has a **third** answer, and it's
one of the most important ideas in the whole book:

| Answer | What it means |
|--------|---------------|
| **yes** | The machine could establish the fact. |
| **no** | It could not — *as far as it knows*. |
| **unknown** | It has no basis to decide either way, and won't guess. |

That middle row hides a subtlety — and the machine wears it on its sleeve. When
it says **`no (assumed)`**, it doesn't mean *"this is impossible"* — it means
*"I found no reason to believe it."* Ask `is bo nervous` and you get
`no (assumed)`, not because bo is provably calm, but because nothing in the
world says he's nervous. (A **plain `no`** is reserved for the rarer, harder
case: when the machine can actually *prove* the opposite.)

And sometimes even that "no" is too strong. If the machine is told to keep an
open mind — because its information might be incomplete — it will say
**`unknown`** instead of pretending the absence of a clue is a clue. You saw
this with the stranger `zz` back in Chapter 0.

!!! note "This deserves a whole chapter — and gets one"
    *Why* is "no" usually really "I didn't find it," and when should a machine
    say "unknown" instead? That question — the **closed world** versus the
    **open world** — is the heart of the intermediate part. For now, just hold
    onto the idea that this machine can tell the difference between *"no"* and
    *"I don't know,"* and that it considers that difference a matter of honesty.

## Try it

Open the playground and ask away. Try a yes/no question, then a `who` question,
then a `why`. Change a clue and watch an answer flip.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Next:** so far the machine only knows what we *tell* it. Time to teach it to
**work things out on its own** — the word `when`, and the magic of rules.
[Rules: the word "when" →](04-rules.md)
