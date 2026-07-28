# 0031. `units/` may not import from `ugm/`

**Status — current (2026-07-28): SURVIVES.** in force. Invariant 10, pinned by `tests/units/test_no_ugm_import.py`.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §15; `tests/units/test_no_ugm_import.py`

## Context

The two packages solve the same problem with opposite paradigms (`0004`). Sharing code would make it
impossible to tell which shared assumptions were genuine and which were store-shaped.

## Decision

**No imports from `ugm/`. Anything needed is copied**, and what gets copied is then evidence about
what is genuinely shared.

## Evidence

- Asserted by a test, not by intention — this is exactly the sort of rule that is kept on paper and
  broken in the build.
- `ugm/` stays working and untouched; nothing is retired until this substrate answers a real question end to
  end, at which point deletion is the honest move rather than archiving.

## Consequences

- Some duplication is deliberate and should not be "cleaned up".
- The copied surface is small, which is itself a result.
