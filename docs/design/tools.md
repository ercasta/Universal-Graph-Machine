# `tools.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Can a tool be data? (§5, §17, §19, §21)

A tool -- a lookup, a solver, a small model -- is not a new kind of thing in this
design. It is the shape `_fit` and `_verdict` already have: **a request answered
by a function rather than by a search**, which is how stratum 0 escapes §5's wall
and is the only shape something outside the agent can honestly take. What was
wrong with it was never the shape. It was that the BINDING lived in Python:

    _fit answers `fit` because a Python line says so

so a corpus could not ask which tools existed, could not retire one on evidence,
and could not reason about one. §21 has carried that as honest debt since the
phases went. This closes it with two ordinary relations and no new primitive:

    answers(<M>, ask)          M answers `ask` requests -- a FACT, hence deniable
    answered(<M>, ask(x), y)   what M said -- a RECORD, hence not yet believed

    python -m ugm.probes.tools

⭐⭐⭐ **A tool may propose; it may never conclude.** What lands is a record that
the tool said so, and a corpus rule turns it into a claim, as weakly as it likes
-- exactly the `arrived` -> `says` -> trust-rule path channels have had all along.
This is not fastidiousness. Let a tool write a belief directly and §12's weakest
link has a link with nothing behind it, `why()` stops answering at the one place
the agent cannot introspect, and §2's not-lossy criterion fails where it matters
most. The restriction is what makes an unreliable tool *safe to be wrong*.

⭐⭐ **One credit walk reaches rules and tools alike.** `review` and `blame` follow
`applied(...)` licences; a tool's answer carries one; so a tool that gave bad
advice is named by `blame` with no machinery added (`Machine._statements`). That
is the whole of what *jointly trained* can honestly mean here -- **a shared
credit assignment, not a shared update rule**. The rule side rewrites its corpus;
a model side would fine-tune on labels the same walk produced.

 **A tool mints nodes, and minting is where this design keeps getting hurt.**
Registering `oracle` to answer `guess` by NAME mints a second `guess` beside the
one the corpus writes, so the tool waits forever for a request nobody can make;
and an answer built with `g.atom("vessel")` is a node no rule can name. Both were
measured here, both silent. **Anything that binds a name must go through the
table that resolves it** -- `Loader.answerer`, and `Loader.atom` for the answer.
That matters more for a real model than for this stub, because a model returns
*strings*, and every one of them has to be interned in the corpus's scope.
