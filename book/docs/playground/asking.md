# Ask it something — live

Same engine, different verb. This world knows that **paul is a person**, and it
has two ways to establish that someone is mortal:

- `conclude_mortal` — works it out. Touches nothing outside.
- `ask_the_registrar` — reaches the outside world to find out.

Only one of those may be used to answer a question (Chapter 23). Watch which one
turns up in the reasoning.

Three verbs share one grammar. Change the first word and the same body means
something different:

- **`goal`** — go and make this true.
- **`ask`** — tell me whether it's true, or could be.
- **`why`** — tell me how it came to be true.

<div class="ugm-playground"
     data-wheel="../wheels/universal_graph_machine-0.2.0-py3-none-any.whl"
     data-mode="ask">

  <label class="ugm-label" for="ugm-ask-text">Say something to it</label>
  <textarea id="ugm-ask-text" class="ugm-corpus" spellcheck="false" rows="4">
ask is paul mortal?:
    paul.mortal = true
</textarea>

  <div class="ugm-controls">
    <button class="ugm-run" type="button">Run</button>
  </div>

  <div class="ugm-quick">
    <span class="ugm-quick-label">Try:</span>
    <button class="ugm-ask" type="button"
            data-text="ask without that rule?:&#10;    paul.mortal = true&#10;    never conclude_mortal">ban the rule</button>
    <button class="ugm-ask" type="button"
            data-text="ask is paul organic?:&#10;    paul.organic = true">something unknowable</button>
    <button class="ugm-ask" type="button"
            data-text="why is paul mortal?:&#10;    paul.mortal = true">why?</button>
    <button class="ugm-ask" type="button"
            data-text="ask is nobody mortal?:&#10;    nobody.mortal = true">a name it doesn't know</button>
  </div>

  <div class="ugm-steps"></div>
</div>

## Things worth trying

**The default question.** `YES`, in one step, *because `conclude_mortal(p=paul)`*
— the answer arrives carrying the reasoning that produced it. Note which rule it
used: `ask_the_registrar` establishes the very same fact and is never offered,
because it reaches outside.

**Ban the rule it wants.** `never conclude_mortal` turns `YES` into `UNKNOWN`
after **zero** imagined steps. Constraining the route works on questions exactly
as it works on goals — nothing was added to support it.

**Ask something unknowable.** `paul.organic` comes back `UNKNOWN`, with the
machine spelling out that this *says nothing about the world*. It has learned
about its own library, not about paul.

**Ask why, on a fresh world.** Each run starts clean, so nothing has been worked
out yet — and `why` will tell you the fact doesn't hold rather than inventing a
derivation for it. That refusal is Chapter 8's whole point.

**Use a name it doesn't have.** `nobody` is refused with a line number. A name
that matches nothing, or matches *more than one thing*, is a refusal — never a
guess.

!!! note "Asking changes nothing"
    When it answers `YES` by working out that `conclude_mortal` would do it, it
    does **not** conclude that for real during the search. The reasoning happens
    on a private copy. That's why you can ask freely, and why `why` on a fresh
    world has nothing to report.

---

Next: [make it check itself →](selftest.md)
