# `agreement.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

§20's floor gate: the rule-level read must agree with the native one.

    For every bundled convention, the rule-level definition exists, and the
    compiled path produces identical answers.

This runs it for the one convention an implementation is most certain to have
compiled into itself -- §10's read. `Chain.resolve` walks in Python; the rules
below derive the same answer under **the ordinary interpreter**. If they
disagree, either the walk is not a program or the rules are wrong, and both are
worth knowing.

⭐⭐⭐ **The baseline moved, and that is the point of this commit.** Until now
the rule-level side was `stratum0.py` -- a second engine with its own rule type,
its own item type and its own solver, which §5's *one interpreter* forbids and
§6 explicitly disclaims. It is deleted. What replaces it is a list of ordinary
rules, written in the surface a corpus writes, matched by the matcher every
other rule is matched by.

Three things had to exist for that, and each is §6's own sentence made
operational rather than a new construct:

  * the **skeleton as members** -- `anc`, `in_delta`, `entry_of`, `delta_next`
    (`rules.structural_relations`), so an antecedent can mention the raw chain
    instead of the resolved state;
  * **§6's test deciding where a conclusion lands** -- *every antecedent member
    is structural* is computable, so a rule that reads only structure concludes
    structure, which is the price §6 states and the reason the circle does not
    return;
  * **negation as failure on a structural member**, which needs no notation: a
    structural member has no entry, so a `-` on one can only mean *not derived*.

    python -m ugm.gates.agreement

## The read, as rules. Written in the surface, so t

The read, as rules. Written in the surface, so this is also the expressibility
claim: nothing here is a notation the document invented for the engine.

⚠ The order within a delta is walked back from a CANDIDATE, not closed over
every entry. Both give `<beaten-deposit>` the same answers -- it only ever
asks about two entries that are already candidates for one proposition -- but
the closure is the difference between one walk per candidate and one per pair
of entries in the history. It went unnoticed while §7 hid two thirds of the
chain from the matcher: with the reified entries visible the same fixture
stopped finishing at all (docs/observations.md Part 6.6).

⚠ Every member is ANCHORED, and the order is what anchors it. `anc($seat, $d)`
walks upward from a bound seat; `in_delta($d, $e)` enumerates a bound moment's
entries; `entry_of($e, ...)` reads a bound entry's own three members. A member
whose turn comes before anything binds it finds nothing -- so the authored
order is load-bearing here in a way §12 already says it is everywhere.

## A revision of the past: the SAME locus as the fi

A revision of the past: the SAME locus as the first claim, deposited later.
This is the one case the deposit index exists for, and it is the case a
fixture omits by accident -- an earlier version of this file wrote the
revision at a different locus, whereupon the locus key decided every read
and `beaten-deposit` could be deleted with no effect at all.
Two revisions of the same claim inside ONE moment's delta, SEPARATED by an
entry about something else. The delta's own order is the only thing that
decides between them, and the separation is what makes the order need to be
transitive: the entry in between does not compete, so it cannot pass the
verdict along. Adjacent revisions leave the transitive rule unexercised,
and an unexercised rule is one no fixture can kill.
