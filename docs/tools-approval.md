# Tools, actions, and approval

Shipped, not a proposal. `ugm/rules/tools_approval.ugm` is the corpus; `ugm/probes/tools.py` runs it
both ways (approved and denied) as a self-test.

## The pattern

Three existing pieces compose into "hold an action for approval," with no new engine primitive:

- **`action name(...)`** declares the palette. Deposits `action(name(...))`, an ordinary node any
  rule can range over via `+action($a)`.
- **`kb.answerer(name, request, fn)`** is a tool. It proposes a fact a tick later
  (`answered(<tool>, req, result)`); it never concludes directly.
- **`after`/`intercepts` triggers** are the write-time gate. A trigger sees a pending conclusion as
  `producing(<rule>, p)` and can `drop(p)`, replace it with `instead(p, q)`, or let it stand.

```
action deploy($service)

rule <request> = implies( { +want(deploy($s)) },
                          { +deploy($s), -want(deploy($s)) } )

fact +intercepts(<hold>, after)
rule <hold> = implies( { +producing(<request>, deploy($s)) },
                       { +instead(deploy($s), pending(deploy($s))) } )

rule <approved> = implies( { +answered(<approve>, pending(deploy($s)), yes) },
                           { +deploy($s), -pending(deploy($s)),
                             -answered(<approve>, pending(deploy($s)), yes) } )
rule <denied> = implies( { +answered(<approve>, pending(deploy($s)), no) },
                         { -pending(deploy($s)),
                           -answered(<approve>, pending(deploy($s)), no) } )
```

The `approve` tool answers synchronously between ticks — `input()` at a terminal is enough for a
human in the loop. No session, no resume: the block happens inside one `run()` call, the same way any
slow tool already works.

## What this buys

- **Swappable strategy, not a mode.** "Auto-approve reads, ask for writes", "ask once per service per
  run", "deny anything after 5pm" are each a different `<hold>`/`<approved>` pair — ordinary
  competence, loadable per corpus.
- **Discoverable, not enumerated.** A generic `<hold>` keyed on `+action($a)` covers actions declared
  later, same as the palette does.
- **Nothing hidden.** The approval isn't a side channel: `pending(deploy(web))`,
  `answered(<approve>, ...)` and the eventual `deploy(web)` are ordinary beliefs, inspectable the same
  way as anything else the corpus concludes — `python -m ugm ... --ask "deploy(web)"`. There's no
  derivation trail behind a belief (see [`guide.md`](guide.md)), so this shows *that* the approval
  happened and what the corpus currently believes, not a step-by-step replay of how it got there.

## The convention, not a standard

```
action  <name>(...)
pending(<name>(...))
```

Any tool that wants approval gating produces `pending(...)` before its effect; any corpus that wants a
different strategy overrides `<hold>`. That's the whole contract — naming, not machinery.

## What's out of scope here

Interactive session loops (injecting new `say` facts between runs, watching state evolve across
turns) are [HarneSkills](https://github.com/ercasta/harneskills)'s job, not this engine's — see
[`guide.md`](guide.md).
