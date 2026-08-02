"""Native — primitives the kernel executes but does not know.

This settles a conflict between two principles that are both right.

Search is a primitive: the closed-class test is whether it can be composed from what already
exists, and there is no sequence of `GET`, `SET` and `LINK` that imagines a state. So it earns a
place beside dispatch.

The kernel rule says Python may do the substrate and must never do business, where business is
anything decided about how to represent plans, time, goals or criteria. The system has to port to
another substrate by re-implementing the kernel while the data carries over unchanged, so the
kernel must never see the representation above it.

Those collided when the instruction set imported the planner so that two opcodes could call it: a
port would have had to port the entire planner in order to implement two instructions.

Both principles hold once a primitive stops having to be an opcode. A native is still primitive,
nothing composes it, and still uninterruptible where it must be; what changes is that the kernel
reaches it by name through a table it does not populate. The dependency inverts:

    before:   isa  --imports-->  driver          (the kernel names the planner)
    after:    isa  --looks up--> native  <--registers--  driver

The table is substrate; its contents are not. This module names nothing from the layer above — no
goal, no plan, no criterion — and that is the property to preserve. A `register` call belongs in
the module that owns the thing being registered; a dictionary of names in this file would be the
same leak with an extra hop.

Registration is an import side effect, so a native is callable only once its owner has been
imported. That is why `call` refuses by naming what is registered: the failure worth designing
for is a program reaching for a primitive whose module nobody loaded, and a bare "unknown native"
is indistinguishable from a typo.

Deliberately not policed. Anything registered here can do anything Python can, exactly as the
opcodes it replaces could. Policing becomes necessary when untrusted rule files are loaded, and
nothing does that yet.

See `docs/execution-model.md`.
"""
from __future__ import annotations

from typing import Callable

from .graph import Graph

_REGISTRY: dict[str, Callable] = {}


class UnknownNative(KeyError):
    """Asked for a primitive nobody registered. Usually means the owning module was never imported."""


def register(name: str, fn: Callable) -> None:
    """Make `fn` reachable as `NATIVE R(dst) "<name>" …`.

    Re-registering the same name is refused rather than silently overwriting. Two modules claiming
    one primitive is a conflict somebody has to resolve, and last-import-wins would resolve it by accident
    — the same silent tie-break `search-was-irreproducible-set-tiebreak` records at length."""
    if name in _REGISTRY and _REGISTRY[name] is not fn:
        raise ValueError(f"native {name!r} is already registered to "
                         f"{getattr(_REGISTRY[name], '__module__', '?')}."
                         f"{getattr(_REGISTRY[name], '__name__', '?')}; refusing to overwrite it")
    _REGISTRY[name] = fn


def call(g: Graph, name: str, args: tuple, act: str | None = None):
    """Run a registered primitive. The kernel gets here knowing only a name, some nodes, and which
    activation is asking.

    `act` is passed to every native, whether it wants it or not, because the alternative — a registry
    that records which primitives take context — is a second thing to keep in step with the primitives
    themselves. A primitive that ignores it costs one parameter; one that needs it and cannot get it
    cannot be written at all. `isa.INVOKE` already threads `caller=act` for exactly this reason: a call
    that does not know who made it is invisible to `activation.chain`."""
    fn = _REGISTRY.get(name)
    if fn is None:
        raise UnknownNative(
            f"no native {name!r}. Registered: {', '.join(sorted(_REGISTRY)) or '(none)'} — "
            f"a native is registered when its module is imported, so this usually means nothing has "
            f"imported the module that owns it")
    return fn(g, act, *args)


def names() -> tuple:
    """Every registered native, sorted. For a reader, and for the refusal above."""
    return tuple(sorted(_REGISTRY))


__all__ = ["register", "call", "names", "UnknownNative"]
