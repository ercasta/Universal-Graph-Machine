# `clock.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A wall clock, off by default, and what turning it on actually costs.

    python -m ugm.probes.clock

Moments are **ordered**, not **measured**. `pred` and `anc` say which came
first, exactly; `depth` is a position rather than a duration. So the chain could
not answer *how long ago* at all, and nothing in the core touched a clock --
deliberately, because §3's determinism is measured byte for byte here.

The clock is one structural relation, stamped where a moment is born:

    time(<moment>, <milliseconds since the epoch>)

Structural, like `pred`: nobody asserted it and nothing can deny it. Deposited
only when the clock is on, so a corpus asking for it on a clockless run finds
nothing, which is the honest answer rather than a zero.

## What it costs, measured rather than assumed

The first version of this note said a stamp per moment makes two runs differ by
construction. **That is false, and the correction is the useful half.** A stamp
is not an entry, so with the clock on:

    entries        identical across two runs
    stamps         different across two runs

`ugm.dungeon`'s *the same seed replays the same fight, entry for entry* is
untouched. What does diverge is a corpus that **reads** the clock: its
conclusions are ordinary entries carrying a number that was different last time.

So the clock is **inert until asked for**, and off by default because a source
of nondeterminism should be requested rather than inherited.

## The trap it walked into on the way in

`chain.TIME` is `g.atom("time")`, and **`atom` does not intern**. Registering the
relation without adding `"time"` to the machine's reserved-name table gives a
corpus a FRESH node of the same name: the rule parses, `is_stratum0` answers no
because the member's relation is not the chain's, the member matches nothing,
and nothing raises. That is the name-identity trap, which the chain's own
comment records as having cost this design four silent bugs -- this is the
fifth, and the check below is the one that would have caught it.

## What is not done

**Replay does not reproduce times.** `save` renders the session as what the
agent was told; a stamp is not an entry, so it is not rendered, and a resumed
session stamps its moments afresh. Making a run time-faithful means recording
the stamps the way `arrived` is recorded -- which is the same gap a sampled
tool's answer has, and it should be closed once for both.
