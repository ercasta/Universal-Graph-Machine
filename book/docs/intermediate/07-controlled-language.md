# Talking to the machine

Look back at everything you've typed into the machine:

```
ada is a suspect
bo in library
?someone is thief when ?someone is a suspect and ?someone is not cleared
who is thief
```

It reads like English — but it isn't *quite* English. It's a small, carefully
fenced-off slice of it, and that fence is doing important work. This slice has a
name: a **controlled natural language**, or **CNL**.

## Why not just plain English?

Because plain English is a swamp of ambiguity, and a reasoning machine can't wade
through it. Take a sentence like:

> *I saw the detective with the telescope.*

Who has the telescope — you, or the detective? English shrugs. A machine that has
to *reason* can't shrug; it needs each sentence to mean exactly one thing.

So UGM speaks a **controlled** language: a deliberately limited set of sentence
shapes where every accepted sentence has a single, unambiguous meaning. `ada is a
suspect` can mean only one thing. That rigidity you may have felt — *"why do I
have to write it just so?"* — is not clumsiness. It's the price of never being
misunderstood, and it's a bargain.

## The shapes you know

You've already met the whole everyday vocabulary:

- **Facts:** `X is a Y`, `X is Y`, `X in Y`
- **Rules:** `HEAD when CONDITION and CONDITION …`, with `not` for negation
- **Questions:** `is …`, `who …`, `why …`

That's a real language — enough to describe worlds and interrogate them — and
it's small enough to hold in your head. Controlled doesn't mean crippled.

## It tells you when you've stepped outside

We saw this in Chapter 2, and it's worth repeating because it's central. Type
something the language doesn't recognize —

```
glorp the flarn
```

— and the machine **doesn't guess**. It flags the line as unrecognized rather
than quietly misreading it. A controlled language you can *trust* is one that
tells you when you've left it. (The jargon for this friendliness is
*habitability* — the language is a place you can comfortably live because it never
silently lies about understanding you.)

## You can teach it new shapes

Here's the part that surprises people. The list of accepted shapes — `X is a Y`,
`who …`, `why …` — is **not** wired into the machine's guts. Those shapes are
themselves just entries in the knowledge base, the same kind of thing as your
facts and rules. Which means you can *add* to them, in the language itself,
without anyone editing the machine.

Say your world needs a question the built-in shapes don't cover — you'd like to
ask `whether ada likes bo` instead of the usual phrasing. You teach the machine
that shape once, and from then on it recognizes every question of that form:

```
form ask.whether : ⟨build a yes/no question⟩ when ⟨the words "whether S P O"⟩
```

After that line, `whether ada likes bo` is a sentence the machine understands —
it parses it, answers it, and if you later type a half-formed version it will
even suggest your new shape as one of the "did you mean…" hints. It has become a
first-class part of *your* dialect. And if you decide you don't want it, `disable
that rule` takes it back out, exactly like disabling any other rule.

This is the same idea as the "parsing *is* reasoning" point below, followed to its
conclusion: if recognizing a sentence is done by rules, then teaching a new
sentence shape is just **adding a rule**. The grammar isn't a wall around the
language — it's more knowledge, and knowledge is the thing you're allowed to grow.

??? info "Deep dive: what a form actually looks like"
    A shape is taught with a `form` line that has two halves around `when`, just
    like an ordinary rule. The half *after* `when` is the word pattern to match —
    the sentence's words, in order. The half *before* is what to build when that
    pattern is seen: the internal "question" object the machine then answers. A
    real one, spelled out, is more technical than the sketch above:

    ```
    form ask.whether :
      <query>? qtype yesno and <query>? q_s ?qs
      and <query>? q_p ?qp and <query>? q_o ?qo
      when ?s first whether? and whether? next ?qs
      and ?qs next ?qp and ?qp next ?qo
    ```

    You won't often write these by hand at this level of detail — a friendlier
    "*a whether-question looks like whether S P O*" surface is planned to sit on
    top. Two guard rails keep the feature safe: a new form may only read the
    *words* of the incoming sentence (never your facts — a "form" that peeked at
    the knowledge base would be a disguised rule, and the machine rejects it), and
    teaching the same shape twice is fine as long as the two definitions agree,
    while two *different* definitions under one name are flagged rather than
    silently fighting. Whole files of facts, rules, and `form` lines load in order,
    so a file can teach a shape and then immediately use it.

## The one boundary the machine draws on purpose

You might wonder: if plain English is so troublesome, how would a *person* who
doesn't know the exact forms ever talk to this machine? The answer reveals a
deliberate design choice.

Turning messy human English into clean CNL is a **separate job**, handled *before*
the machine reasons — today, by a language model that translates *"I think the
butler did it, he's got no alibi"* into the tidy forms above. Everything in this
book lives on the machine's side of that line, where language is already precise.

Drawing the boundary there is intentional: keep the ambiguity-wrangling in one
clearly-marked place, and keep the reasoning core speaking a language it can
never misunderstand.

??? info "Deep dive: parsing *is* reasoning"
    Here's something beautiful hiding under the surface. In most systems,
    understanding a sentence and reasoning about it are two different machines
    with glue between them — a parser hands a tree to an engine. In UGM they're
    the *same* process: recognizing that `ada is a suspect` is a fact is itself
    done by rules over the graph, exactly like working out that cy is the thief.
    Reading and reasoning are one activity at different moments. It's why the
    machine can explain itself in the same language you spoke to it — output is
    just input, run backward. You don't need this to use the machine, but it's
    one of the ideas that makes it elegant.

## Try it

In the playground, try writing a fact in a way the machine *won't* recognize —
maybe `ada really seems quite suspicious to me` — and watch it decline rather
than guess. Then rewrite it in a form it accepts (`ada is suspicious`) and see it
land. You're feeling the edges of the controlled language.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Next:** the machine's signature trick, finally explained — how it can always
show its work. [Because… →](08-because.md)
