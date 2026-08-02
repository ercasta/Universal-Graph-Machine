"""NATIVE — primitives the kernel EXECUTES but does not KNOW.

**⭐⭐ This exists to settle a conflict between two principles that were both right.**

* `isa.py`'s `PLAN` docstring argued, correctly, that search is a **primitive**: the closed-class test is
  *can it be composed from what already exists*, and there is no sequence of `GET`/`SET`/`LINK` that
  imagines a state. So it earns a place beside `DISPATCH`.
* The kernel rule says Python may do the **substrate** and must never do *business* — where business is
  **anything we decided about how to represent** plans, time, goals, criteria — because the system has to
  port to another substrate (Rust, Excel macros, a redstone machine) by re-implementing the kernel while
  the data carries over unchanged. **The kernel never sees the representation above it.**

Those collided in `isa.py`, which imported `driver` so that two opcodes could call the planner. Measured
in `docs/microfunctions/kernel_boundary.md`: **a Rust port would have had to port the entire planner in
order to implement two opcodes.** The instruction set — the most kernel thing there is — knew what a plan
was.

**⭐ Both principles hold once a primitive stops having to be an OPCODE.** A native is still primitive
(nothing composes it) and still uninterruptible-by-design where it must be; what changes is that the
kernel reaches it **by name through a table it does not populate**. The dependency inverts:

```
    before:   isa  ──imports──>  driver          (the kernel names the planner)
    after:    isa  ──looks up──>  native  <──registers──  driver
```

⚠ **The table is substrate; its CONTENTS are not.** This module names nothing from the layer above — no
goal, no plan, no criterion — and that is the property to preserve. A `register` call belongs in the
module that owns the thing being registered, never here; a dict of names in this file would be the same
leak with an extra hop.

⚠ **Registration is an import side effect, so a native is only callable once its owner has been
imported.** That is why `call` refuses by naming what *is* registered: the failure mode worth designing
for is a program reaching for a primitive whose module nobody loaded, and *"unknown native 'plan'"* with
no list is indistinguishable from a typo.

⚠ **Deliberately not policed.** Anything registered here can do anything Python can do, exactly as the
opcodes it replaces could. `HANDOFF` §5y's position stands: policing is triggered by loading untrusted
`.mf`, and nothing does that yet. Moving the planner out of the opcode set does not change what a body is
allowed to do — only who has to know about it.
"""
from __future__ import annotations

from typing import Callable

from .graph import Graph

_REGISTRY: dict[str, Callable] = {}


class UnknownNative(KeyError):
    """Asked for a primitive nobody registered. ⚠ Usually means the owning module was never imported."""


def register(name: str, fn: Callable) -> None:
    """Make `fn` reachable as `NATIVE R(dst) "<name>" …`.

    ⚠ Re-registering the same name is **refused** rather than silently overwriting. Two modules claiming
    one primitive is a conflict somebody has to resolve, and last-import-wins would resolve it by accident
    — the same silent tie-break `search-was-irreproducible-set-tiebreak` records at length."""
    if name in _REGISTRY and _REGISTRY[name] is not fn:
        raise ValueError(f"native {name!r} is already registered to "
                         f"{getattr(_REGISTRY[name], '__module__', '?')}."
                         f"{getattr(_REGISTRY[name], '__name__', '?')}; refusing to overwrite it")
    _REGISTRY[name] = fn


def call(g: Graph, name: str, args: tuple):
    """Run a registered primitive. The kernel gets here knowing only a name and some nodes."""
    fn = _REGISTRY.get(name)
    if fn is None:
        raise UnknownNative(
            f"no native {name!r}. Registered: {', '.join(sorted(_REGISTRY)) or '(none)'} — "
            f"a native is registered when its module is imported, so this usually means nothing has "
            f"imported the module that owns it")
    return fn(g, *args)


def names() -> tuple:
    """Every registered native, sorted. For a reader, and for the refusal above."""
    return tuple(sorted(_REGISTRY))


__all__ = ["register", "call", "names", "UnknownNative"]
