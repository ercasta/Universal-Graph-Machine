# UGM documentation

This directory documents the Universal Graph Machine as it currently stands. It is written to be
read, not scanned: each page covers one part of the system in prose, states what that part does and
why it is shaped that way, and says plainly where its limits are.

There is also a **[tutorial book](https://ercasta.github.io/Universal-Graph-Machine/)** in `book/`,
which teaches the machine from scratch with pages that run the real engine in the browser. The book
is for learning; these pages are for working.

## Where to start

If you are new to the system, read **[Overview](overview.md)**, then
**[Concepts](concepts.md)**. That is enough to understand what the machine is and what it holds.

If you are going to author a domain — goals, types, advice, methods, expert judgement — read
**[Authoring](authoring.md)**. It is the one text surface a domain writes, and its examples are
extracted from the file and parsed by the self-test, so they cannot go stale.

If you are going to change the engine, read **[Execution model](execution-model.md)** and
**[Reference: modules](reference/modules.md)**.

## The pages

| page | what it covers |
|---|---|
| [Overview](overview.md) | what the system is, the two ideas it is built on, and a first worked example |
| [Concepts](concepts.md) | the data model — graph, focus, types, functions, hypotheses, and why everything is one representation |
| [Planning and acting](planning.md) | goals as constraints, imagining on a workbench, finding a plan, carrying it out, divergence and recovery |
| [Deliberation](deliberation.md) | how the next step is chosen: guidelines, methods, criteria, directives, and defeasible norms |
| [Memory and time](memory.md) | the thread, episodes, observation, the clock, discourse, and forgetting |
| [Execution model](execution-model.md) | the outer loop, the instruction set, activations, dispatch, and the kernel boundary |
| [Authoring](authoring.md) | the controlled language a domain writes |
| [Limits](limits.md) | what the system does not do, what cannot be said, and what is known to be weak |
| [Reference: modules](reference/modules.md) | module-by-module map with entry points |
| [Reference: instruction set](reference/isa.md) | opcodes, operands, and the assembly surface |
| [Reference: glossary](reference/glossary.md) | one sentence per term |

## Verification

```bash
python -m ugm.selftest
```

The self-test is the project's verification, in place of pytest. It is a single runner that prints
every check's named observations and counts any `False` as a failure. It currently reports **221
checks, 0 FAILED**. Several checks read this documentation directly: the authoring guide's examples
are parsed, so a guide that drifts from the parser turns the run red.
