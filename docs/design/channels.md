# `core/channels.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Channels (§13).

Every entry names where it arrived from, and that has two layers which must not
be fused:

    channel     the intake path -- this socket, this sensor, the knowledge base.
                Mechanically observed, so it cannot be wrong, in the way a sensor
                cannot misreport its own reading.

    authority   who is taken to have spoken, and what their word is worth.
                An ordinary claim, defeasible like any other.

Fusing them would make authority unforgeable by fiat, so that anyone reaching the
right socket would thereby be the boss. The knowledge base is a channel like any
other: reading it faithfully is guaranteed, and what it *says* stays contestable,
which is what `by(R, boss)` and `overrides(R1, R2)` depend on.
