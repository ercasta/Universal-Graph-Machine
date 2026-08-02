"""PLAN — backward chaining over declared return types, producing a LAZY chain.

**The shape, in one sentence:** to obtain a `T`, find the functions that return `T`, make their parameter
types the subgoals, and recurse — collecting a chain of *pending* calls that nothing has executed yet.

**Lazy is the important word, and it is the Spark analogy taken seriously.** Planning builds a chain; it
does not run one. Transformations compose; an action materialises. That separation buys three things this
project has wanted for a long time and previously had to engineer separately:

* **A plan is data.** The chain is nodes and ordered edges like everything else, so it can be inspected,
  compared against a rival plan, pointed at by a hypothesis, or handed to a language model to critique —
  all before anything happens. This is what "rules as data" was ultimately for.
* **Nothing is committed by thinking.** The old design needed a supposition mechanism to explore a plan
  without acting. Here exploring is just... not calling `run`. There is no mode to be in.
* **Two rival plans are two chains**, comparable side by side, which is exactly what non-greedy selection
  will need.

**Mutation needs no representation of its own — it is a CAST.** A type is a schema constraining a
subgraph, attributes included (`types.declare_type`), in the way a Pydantic schema constrains a frame. So
`service(c: car) -> serviced_car` is not "a function with a side effect"; it is a function that **casts a
`car` into a `serviced_car`**, and the change to the graph is how the cast is achieved. Precondition and
effect are just the parameter type and the return type. Nothing anywhere records that a mutation happened,
because nothing needs to: the node either satisfies the stronger schema or it does not, and that is
checkable at any moment rather than being a historical claim.

Two consequences worth stating, because they simplify things that looked like special cases:

* **Planning is chaining casts.** A function that creates a genuinely new node and a function that
  strengthens an existing one are planned identically — both are "given these types, obtain that type."
* **A cast returns its subject.** That is why `run` falls back to the first bound argument when a function
  sets no `result`: it is not a convention papering over ambiguity, it is what a cast *is*. Creating
  something new is the case that must say so, by setting `result`.

**Honest scope, stated rather than discovered later.** This is depth-limited depth-first search taking the
first solution it finds. There is no cost model, no preference between rival producers beyond declaration
order, and no backtracking across an already-committed subgoal. It is a planner adequate for chains of a
handful of steps, which is the size this system actually needs — not a general-purpose one, and it should
not be mistaken for it. A recursion guard on the set of types currently being satisfied keeps a cyclic
library from spinning; the depth limit is the backstop.
"""
from __future__ import annotations

from . import function as fn
from .graph import Graph
from .types import instances, is_a


def _binding(g: Graph, call: str, param: str, src) -> None:
    kind, value = src
    b = g.mint("binding", param=param)
    g.link(b, "value" if kind == "node" else "from", value)
    g.link(call, "arg", b)


def _satisfy(g: Graph, want: str, subject, calls: list, depth: int, seen: frozenset):
    """Return a source for a value of type `want`: `("node", n)` if one already exists, or
    `("call", c)` if a pending call will produce one. `None` if it cannot be obtained."""
    if subject is not None and is_a(g, subject, want):
        return ("node", subject)
    existing = [n for n in instances(g, want) if g.kind(n) != "type"]
    if existing:
        return ("node", existing[0])
    if depth <= 0 or want in seen:
        return None
    for name in fn.producers(g, want):
        params, _ = fn.load(g, name)
        ptypes = fn.param_types(g, name)
        resolved, ok = {}, True
        for param in params:
            declared = ptypes.get(param)
            if declared is None:
                ok = False
                break
            src = _satisfy(g, declared, subject, calls, depth - 1, seen | {want})
            if src is None:
                ok = False
                break
            resolved[param] = src
        if not ok:
            continue
        call = g.mint("pending_call", function=name, produces=want)
        for param, src in resolved.items():
            _binding(g, call, param, src)
        calls.append(call)
        return ("call", call)
    return None


def plan(g: Graph, want: str, subject=None, *, depth: int = 8):
    """Build a lazy chain that would obtain a `want`. Returns the chain node, or `None` if no chain of
    declared functions reaches it — an ordinary answer, not an error.

    A chain whose `call` list is empty means the goal is *already satisfied*, which is different from
    being unreachable and is reported differently on purpose."""
    calls: list = []
    src = _satisfy(g, want, subject, calls, depth, frozenset())
    if src is None:
        for c in calls:
            g.drop(c)
        return None
    chain = g.mint("chain", want=want)
    if subject is not None:
        g.link(chain, "subject", subject)
    for c in calls:
        g.link(chain, "call", c)          # ordered: dependencies were appended first
    if src[0] == "node":
        g.link(chain, "already", src[1])
    return chain


def calls_of(g: Graph, chain: str) -> tuple:
    return g.targets(chain, "call")


def describe(g: Graph, chain: str) -> str:
    """A readable rendering of a plan that has not run — for inspection, and for handing to a model."""
    if chain is None:
        return "<no plan>"
    steps = [f"{i}. {g.attr(c, 'function')} -> {g.attr(c, 'produces')}"
             for i, c in enumerate(calls_of(g, chain), 1)]
    head = f"plan for {g.attr(chain, 'want')}"
    if not steps:
        return f"{head}: already satisfied"
    return head + ":\n" + "\n".join(steps)


def run(g: Graph, chain: str):
    """THE ACTION. Execute a chain's pending calls in order and return the final node.

    A call's output is whatever its function left in `result`, and otherwise the node bound to its first
    parameter — because **a cast returns its subject**. Setting `result` is how a function says "I made
    something new" rather than "I strengthened what you gave me"; the fallback is the ordinary case, not a
    guess."""
    produced = {}
    last = g.target(chain, "already")
    for call in calls_of(g, chain):
        name = g.attr(call, "function")
        args = {}
        for b in g.targets(call, "arg"):
            param = g.attr(b, "param")
            direct = g.target(b, "value")
            args[param] = direct if direct is not None else produced.get(g.target(b, "from"))
        _focus, out = fn.invoke(g, name, args)
        first_param = fn.load(g, name)[0][0]
        last = out.get("result") or args.get(first_param)
        produced[call] = last
        g.link(call, "produced", last)
        g.put(call, done=True)
    g.put(chain, done=True)
    return last


__all__ = ["plan", "calls_of", "describe", "run"]
