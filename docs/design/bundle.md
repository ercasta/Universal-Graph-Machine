# `bundle.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Is every bundled rule -- and every shipped answerer -- load-bearing? (§20)

    Every gate must delete each rule of the thing it checks, one at a time, and
    report any rule the fixture cannot kill. A rule no fixture can kill is a rule
    the fixture is not testing.

The bundle (§4) is the part of the design that used to be interpreter phases and
is now data. Data can rot in a way a branch cannot: a rule that never applies
costs nothing, breaks nothing, and looks exactly like a rule that works. So this
deletes each bundled rule in turn and re-runs the whole selftest.

It found three the first time it ran. Noticing a deviation had been one Python
comparison -- *the observed sign is not the expected one* -- and writing it as
rules turned its four cases into four nodes, of which only one had ever been
exercised. The phase was not tested either; the rules made that visible.

Since the apparatus's own request-answerers are bound by `answers(<M>, ask)`
rather than by a Python line, the same question is askable of them -- and it
splits into two, which is the second half below:

    REMOVED   the answerer is not there at all      -- is it load-bearing?
    DENIED    a corpus writes `-answers(<M>, ask)`  -- may it be turned off?

The two columns are not the same measurement and neither implies the other. A
`standing` binding is **overridable but not forgettable** (§19's carve-out), so
denying it is refused and costs nothing -- which is the carve-out working, and
would read as blindness in a one-column table.

    python -m ugm.gates.bundle

## -- and the same question of the apparatus's own

-- and the same question of the apparatus's own answerers ------------

Two columns, because they are two questions. REMOVED asks whether the
answerer does anything: a shipped answerer nothing needs is exactly the rot
this file exists to catch, and it rots the same way whether it is a rule or
a function. DENIED asks whether a CORPUS may switch it off -- and for the
four marked `standing` the answer must be no, refused on the record. A zero
there is the carve-out holding, not a blind spot, which is why one column
could not carry both.
