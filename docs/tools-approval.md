# Tools, actions, and approval

Shipped, not a proposal. `ugm/rules/tools_approval.ugm` is the corpus; `ugm/probes/tools.py` runs it
both ways (approved and denied) as a self-test.

## The pattern

Three existing pieces compose into "hold an action for approval," with no new engine primitive:

- **`action name(...)`** declares the palette. Deposits `action(name(...))`, an ordinary node any
  rule can range over via `+action($a)`.
- **`kb.answerer(name, request, fn)`** is a tool. It proposes a fact a tick later
  (`answered(<tool>, req, result)`); it never concludes directly.
- **A GATE** is what holds the action. The gated rule carries `keep gate(...)` in its own antecedent
  and simply cannot conclude the action until something opens it.

```
action deploy($service)

rule <request> = implies( { +want(deploy($s)), keep gate(deploy($s)) },
                          { +deploy($s) } )

rule <hold> = implies( { keep want(deploy($s)), no gate(deploy($s)),
                         no asked(deploy($s)) },
                       { +pending(deploy($s)), +asked(deploy($s)) } )

rule <approved> = implies( { +answered(<approve>, pending(deploy($s)), yes) },
                           { +gate(deploy($s)), -pending(deploy($s)),
                             -answered(<approve>, pending(deploy($s)), yes) } )
rule <denied> = implies( { +answered(<approve>, pending(deploy($s)), no) },
                         { -pending(deploy($s)), -want(deploy($s)),
                           -answered(<approve>, pending(deploy($s)), no) } )
```

`asked(...)` makes the tool asked once. Without it a denial erases `pending` while the want still
stands, `<hold>` re-creates it, and the same question is asked every tick for ever.

## Why a gate, and not a write-time trigger

`<hold>` used to be an `intercepts`/`producing`/`instead` trigger: it watched `<request>` about to
conclude `deploy($s)` and swapped the pending write for `pending(deploy($s))`, so the action was
never believed. Triggers are retired, and **consumption does not replace them** — every rule whose
antecedent is on fires, so a `<hold>` that merely *consumed* `deploy($s)` would not stop a tool rule
reading the same occasion in the same tick. That is measured, in `triggers_are_retired()`.

A gate is stronger, not weaker. The dangerous proposition is never minted rather than
minted-and-rewritten, and the condition is visible in the rule it governs instead of in a hook
somewhere else.

The `approve` tool answers synchronously between ticks — `input()` at a terminal is enough for a
human in the loop. No session, no resume: the block happens inside one `run()` call, the same way any
slow tool already works.

## What this buys

- **Swappable strategy, not a mode.** "Auto-approve reads, ask for writes", "ask once per service per
  run", "deny anything after 5pm" are each a different `<hold>`/`<approved>` pair — ordinary
  competence, loadable per corpus. The gate line in `<request>` is the socket; `<hold>` is what plugs
  into it, and swapping strategies never touches `<request>`.
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
