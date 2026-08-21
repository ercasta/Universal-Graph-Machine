# `core/gate.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Frames and the gate (§13).

A rule cannot name a locus -- it is generic, and a locus is anchored. The frame
is what the machinery supplies one from:

    seat    the moment its writes are deposited in     -- where I am standing
    topic   the locus its writes are stamped with      -- what I am about

Normally they coincide. They come apart exactly twice: reasoning about the past,
where the topic is earlier than the seat, and reasoning under a supposition,
where the seat is inside it.

The requirement is narrower than a prohibition on rules writing:

    No write bypasses the stamp.

What must be impossible is an entry whose provenance is absent or false. An entry
a rule caused to exist is not forgery -- it arrives through the gate and leaves it
stamped with the rule that caused it, which is the ordinary record. That is what
lets `the user says it is raining` become `it is raining` by a rule the agent can
be asked about, rather than by a hard-wired intake nobody can argue with.

## The third thing a frame supplies, beside t

⭐⭐⭐ **The third thing a frame supplies, beside the seat and the
topic** (`docs/situations.md`). A rule cannot name a situation any
more than it can name a locus, so this is where one comes from.

Seat and situation are not the same answer to the same question, and
the probe that separates them is the one that motivated the design:
the seat contains ENTRIES, because a read walks ancestry and a
supposition's seat is not on the caller's walk; it does nothing at all
about STRUCTURE, because a stratum-0 conclusion is enumerated straight
out of an index that no walk is consulted for. The situation is what
contains the second kind.

## Effects leave the agent HERE, not in a phase of

Effects leave the agent HERE, not in a phase of the loop. §16 already
places action dispatch at the write -- *the one place effects leave the
agent, where the set is small and known* -- and §19 puts the
prohibition check in the same place for the same reason. An
implementation that polls for intents once a tick has moved that
decision into control flow, where nothing can override it.

These are Python callables, which is honest debt: §21 records that the
bundle should be rules, and a hook is not one.

## §19's carve-out, and the shape of it is the argu

§19's carve-out, and the shape of it is the argument:

    Recall may be incomplete about what to do.
    It may not be incomplete about what you must not do.

A malformed write that fails to be caught is a claim that
nothing notices, so a norm may not be a rule competing for attention.
It is a veto here, consulted on **every** write, indexed by what is
about to be written -- a set that is small and known, which is what
makes an exhaustive check affordable at the one place effects leave.

A vetoer returns the node that forbids the write, or None.

## `reseat`

Move a frame to a later seat, and SAY SO. What it is for: the agent's
        own frame must be able to advance while the register is pointing
        somewhere else, because the world does not stop talking while the agent
        is reasoning under a hypothesis.

        The frame node is re-minted, so `frame(seat, topic)` keeps saying where
        the frame is rather than where it began.

        ⭐⭐⭐ **`+moved(<from>, <to>)`, which is §17's *every seat move is a
        write* and was §21's oldest owed item.** Position is where, and it was
        always recorded -- `at(?w, ?x)` is an ordinary fact, which is the whole
        reason walkers needed no engine support. The seat is WHEN, and it was
        not recorded at all: the register advanced on every `causes` application
        and the only trace was a frame node being re-minted, which no rule can
        read.

        ⚠ **And it is not derivable from the chain, which is why a fact about a
        moment is the only place it can live.** `pred` says the new moment
        follows the old one; it does not say the REGISTER went there, because
        moments are minted for spans, predictions and suppositions too. `succeed`
        makes that explicit -- it stopped carrying a licence precisely because
        *what a moment is FOR is a fact about it*, and this is that fact. So the
        licence is passed in rather than invented here: `applied(<R>)` when a
        `causes` rule advanced the register, the channel when the world did.

        The write happens AFTER the move, so the entry is seated where the agent
        now is and reads as *I am here, and I came from there* -- a trail, which
        is what §17 asks for, rather than a state that would need the previous
        one denied to stay true.

## Pinned to the frame's situation for the deposi

⭐ Pinned to the frame's situation for the deposit, and only for the
deposit. The entry node and its `in_delta` are the structural record
of a claim, so they belong to the situation the claim was made in --
otherwise a supposition's own entries would be minted wherever the
register happened to be pointing and the containment would have a hole
in it at the one place claims are made.

⚠ The hooks run OUTSIDE the pin. `_enter` is an `on_write` hook and
it opens a supposition, which moves the register; restoring around it
would put the register back and leave the machine reasoning inside a
frame whose situation nothing is standing in.
