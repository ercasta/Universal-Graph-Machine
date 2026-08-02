# `ugm/` — the engine

The package is the whole system: a graph substrate, an instruction set, stored rules, goals,
planning, deliberation, memory, and one outer loop over all of it. There are no dependencies and
nothing to initialise beyond a `Graph`.

```bash
python -m ugm.selftest      # verification, in place of pytest
```

Documentation lives in [`../docs`](../docs/README.md). Rather than duplicating it here, this file
points at the page that covers each part:

| what you want | read |
|---|---|
| what the system is and why | [docs/overview.md](../docs/overview.md) |
| the data model — graph, focus, types, functions, hypotheses | [docs/concepts.md](../docs/concepts.md) |
| goals, imagining, plans, acting, divergence, questions | [docs/planning.md](../docs/planning.md) |
| how the next step is chosen | [docs/deliberation.md](../docs/deliberation.md) |
| the thread, observation, time, discourse, forgetting | [docs/memory.md](../docs/memory.md) |
| the outer loop, activations, dispatch, the kernel boundary | [docs/execution-model.md](../docs/execution-model.md) |
| the controlled language a domain writes | [docs/authoring.md](../docs/authoring.md) |
| a module-by-module map with entry points | [docs/reference/modules.md](../docs/reference/modules.md) |
| the opcode set and the assembly surface | [docs/reference/isa.md](../docs/reference/isa.md) |
| what the system does not do | [docs/limits.md](../docs/limits.md) |

`rules/*.mf` is the knowledge base on disk, written in the assembly surface.

Each module's own docstring states what it is for and which decisions it implements; those are the
place for detail that belongs next to the code rather than in the documentation.
