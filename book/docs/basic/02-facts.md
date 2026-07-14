# Telling the machine facts

We've seen the world is made of dots and arrows. Now let's learn how to *put*
things into it. Everything you tell the machine is a **fact** — a small,
definite claim about the world. This chapter covers the handful of ways to
write one.

The good news: there aren't many, and they read like English.

## Three ways to state a fact

### 1. "is a" — what kind of thing something is

```
ada is a suspect
cy is a detective
```

`is a` (or `is an`) says something belongs to a **category**. It's the arrow we
drew as `ada ──is_a──▶ suspect` back in the substrate chapter. Use it whenever
you'd naturally say "so-and-so is a kind of thing."

### 2. "is …" — a quality or state

```
ada is nervous
ada is alibied
bo is guilty
```

Plain `is` (with no "a") attaches a **quality** to a thing — a property it has
right now. `ada is nervous` doesn't put ada in a category; it describes her.

!!! tip "The little word 'a' changes everything"
    `ada is a suspect` (category) and `ada is nervous` (quality) look almost
    identical, but the `a` is the difference between *"ada is one of the
    suspects"* and *"ada is in a nervous state."* The machine treats them
    differently — so watch that little word.

### 3. "in" — where something is

```
bo in library
cy in kitchen
```

`in` places one thing inside another. It's how our detective records *where
people were* — often the key to an alibi.

## That's (almost) all you need

With just these three shapes you can describe a whole scene:

```
ada is a suspect
bo is a suspect
cy is a suspect

ada is nervous
ada is alibied
bo in library
```

Six facts, and we've set a stage: three suspects, one of them nervous, one with
an alibi, one seen in the library. Every rule and question in the rest of the
book runs on facts written exactly like this.

## The machine believes you

Here's something important — and a little bit dangerous. **The machine believes
every fact you give it.** It doesn't fact-check. If you tell it
`the moon is a suspect`, then as far as it's concerned, the moon is a suspect,
and it will reason accordingly.

This is by design. Your job is to tell it what's true about *your* world; its
job is to work out the consequences. Garbage in, garbage out — so the facts you
feed it matter.

## But it won't pretend to understand nonsense

There's a flip side to that trust. The machine only understands the shapes it
knows. If you type something that doesn't fit any pattern —

```
glorp the flarn
```

— it does **not** quietly swallow it or guess what you meant. It flags the line
as **unrecognized** and moves on, so a typo can never silently rot your
knowledge. (In this book's playground you'll see it simply decline to act on a
line it can't read.)

This honesty has a name in language design — *habitability* — and it's a
deliberate feature: a controlled language you can trust is one that tells you
when you've stepped outside it, rather than misinterpreting you.

??? info "Deep dive: why a *controlled* language?"
    Ordinary English is gloriously ambiguous — "I saw the man with the
    telescope" has two meanings. A reasoning machine can't afford that. So UGM
    speaks a **controlled natural language (CNL)**: a small, carefully chosen
    slice of English where every accepted sentence has exactly one meaning.
    That's why the fact forms feel a little rigid — the rigidity is what buys
    you unambiguous reasoning. We'll look at the CNL properly in the
    intermediate part; the [appendix has a short note](../appendix/index.md) too.

## Try it

Open the playground and add a couple of facts of your own to the world — try
`cy is nervous` or `ada in library` — then, in the next chapter, we'll start
asking the machine questions about what you told it.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Next:** we can describe a world — now let's *interrogate* it.
[Asking questions →](03-questions.md)
