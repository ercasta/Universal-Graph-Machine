# Tools, actions, and approval

A proposal. Nothing here is implemented yet.

## Claim

No new engine primitive is needed for tool activation or approval. Three
pieces already exist and compose:

- `action name(...)` — declares the palette. Deposits `action(name(...))`, an
  ordinary node any rule can range over via `+action($a)`. (`core/text.py`,
  `_action`.)
- `kb.answerer(name, request, fn)` — a tool. Proposes a fact a tick later
  (`answered(<tool>, req, result)`); never concludes directly. Multi-tick
  effects use `?` on the interim state, no special-casing.
  (`core/machine.py:861`.)
- `after <rule>` triggers — the write-time gate. A trigger sees a pending
  conclusion as `producing(<rule>, p)` and can `drop(p)`, `instead(p, q)`, or
  let it stand. This is what the guide's "prohibition checked at the write"
  example (`docs/guide.md` §3.7, `forbidden(...)`) is built from — checked:
  there is no `forbidden`/`refused` string anywhere in `ugm/core`. It's a
  worked pattern, not shipped machinery. (`core/machine.py:_intercept`.)

So "approval strategy" is not a feature to add. It's a small corpus:

```
action deploy($service)

rule <request>  = implies( { +want(deploy($s)) },
                            { +action(deploy($s)) } )

# the gate: intercept the write, hold it open pending a decision
rule <hold>     = implies( { +producing(<request>, action(deploy($s))) },
                            { +pending(deploy($s)) } )

# the answerer blocks on real input -- terminal prompt, Slack, whatever --
# and reports a tick later
kb.answerer("approve", "pending", ask_a_human)

rule <approved> = implies( { +answered(<approve>, pending($s), yes) },
                            { +applied(deploy($s)) } )
rule <denied>   = implies( { +answered(<approve>, pending($s), no) },
                            { -pending($s) } )
```

`ask_a_human` runs synchronously between ticks — `input()` at the terminal is
enough for a first cut. No session, no resume, no new machinery: the block
happens *inside* one `run()` call, the same way a slow tool already works.

## What this buys

- **Swappable strategy, not a mode.** "Auto-approve reads, ask for writes",
  "ask once per service per run", "deny anything after 5pm" are each just a
  different `<hold>`/`<approved>` rule pair — ordinary competence, loadable
  per corpus, arguable and inspectable the same as any other rule.
- **Discoverable, not enumerated.** A generic `<hold>` keyed on
  `+action($a)` rather than one hold-rule per action covers actions declared
  later, same as the palette does.
- **A trail.** `why applied(deploy(x))` walks through `<approved>`,
  `answered(<approve>, ...)`, `<hold>`, `<request>` — the approval is an
  ordinary licensed conclusion, not a side channel.

## "Graph protocol" — a convention, not a new standard

Resisting inventing one before a second tool needs it (house rule: no
feature is novel until something falsifies the claim). What's proposed is
naming, not machinery:

```
action  <name>(...)                    # existing
answers(<tool>, <name>)                # existing
pending(<name>(...))                   # this proposal
applied(<name>(...)) / denied(...)     # this proposal
```

Any tool that wants approval gating produces a `pending(...)` before it
produces its effect; any corpus that wants a different strategy overrides
`<hold>`. That's the whole contract.

## What's still missing: a REPL

`python -m ugm` loads one corpus, runs to quiescence or a tick limit,
prints, exits. There is no interactive loop — `docs/HANDOFF.md`'s note that
`--save`/`--resume` were deliberately not built still holds. For a *human*
to answer `ask_a_human` for real (not a canned test double), the answerer's
`input()` is enough — it doesn't need a session. What a REPL would add on
top is: injecting new `say` facts between runs, re-running, watching state
evolve across turns. That's a separate piece of work from approval itself
and should stay separate until there's a worked example asking for it.

## Next step

One worked corpus (`ugm/rules/` or a new `ugm/probes/tools.py`) implementing
the `<hold>`/`<approved>`/`<denied>` pattern above, wired into
`ugm.selftest`, with a fake `ask_a_human` for the test and a real one for
manual runs. That makes the pattern falsifiable before anything about it is
called settled.
