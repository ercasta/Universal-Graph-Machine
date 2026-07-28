# 0041. Calls are positional, not role-labelled

**Status — current (2026-07-28): REPLACED.** `../../model.md` §3 — role nodes, not positional calls.

**Status — as recorded:** Accepted
**Source:** user decision, 2026-07-26; `bench/spike_selector_chain.py` probe 8

## Context

A selector chain terminates in a **call** — *"wash the car that is parked at…"*. The first
implementation gave the call node role edges: `<call> <verb> #wash`, `<call> <target> ?e`. That is the
Davidsonian shape the project had rejected for facts, reintroduced for commands, and unlike reification or the
assembly journal a call is **content** produced by the discourse.

And n-ary calls are where the pressure genuinely returns: *"wash the car **with the sponge"*** needs a second
argument, which is the case the original rejection was really about.

## Decision

**A call is just another discourse node.** It carries a lexeme through the same `<word>` predicate
a mention uses, and its arguments are **numbered**:

```
<call>  <word>  #wash          the lexeme, exactly as a mention carries one
<call>  <arg1>  <s4>           positional; the argument IS a selector step
<call>  <arg2>  <s7>
```

**An argument points at the STEP, not at the entity**, so the chain stays walkable and a failed or ambiguous
argument is visible to the call.

## Evidence

- Measured for two arguments: *"wash the car with the sponge"* resolves both, each through its own
  selector chain, numbered — **no `<instrument>`, no `<patient>`.**
- **`<argN>` names a position, so *direction carries the role* holds one level up.** Nothing has to be taught a
  role vocabulary; arity is the only thing anyone must know.
- Rejected alternatives: **verb-as-predicate** (`<call> #wash ?e`) is path-shaped but strictly binary, and
  finding all calls regardless of verb needs a wildcard `?c ?v ?e` — the one pattern the index cannot restrict
  (`0022`). **Role edges** are n-ary and indexable but are the rejected shape.

## Consequences

- An argument list is the same kind of thing as a selector chain rather than a new construct,
  which is `0036` extended by one hop.
- **⚠ The honest limit: `<argN>` is still a label, just a positional one.** What it buys is that the label set is
  fixed and content-free — a mechanism needs to know arity, never semantics.
- Whether a call's arguments should be *dereferenced* for execution, or passed as steps so the executor can see
  a failed argument, is not yet decided. Suspend is not built.
