# `artefact.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Building something, noticing which half of the goal it already meets, and
repairing the other half -- then rendering it.

The user's case: *write an `ls` + `grep` that finds all Python files containing a
class definition.* Can the agent produce a first attempt, "reread" it, see that it
satisfies **find the Python files** but not **containing a class definition**, and
fix that half without redoing the first?

    python -m ugm.probes.artefact

⭐⭐⭐ **The goal is a conjunction, so backward reading splits it, and `check`
answers each half SEPARATELY.** That per-conjunct answer is the whole of what
"partial result" means here -- there is no new machinery for it, and there is no
score of how nearly done something is. A half either holds or it does not, and
the repair is an ordinary rule keyed on `unmet`.

⭐⭐ **The artefact is a node; what it DOES is claims about it.** The goal
decomposes over `finds($c, py_files)`, never over shell syntax. That is what
makes the repair a rule rather than a string edit, and it is why the rendering
below is a TOOL and not a parser: composing the text is a function, and §17 says
a request answered by a function is exactly what a tool is.

 **And the honest half, which this file exists to pin: WITHOUT A RE-ASK THE
SIGNAL IS STALE.** `check` is asked the moment a subgoal appears -- before
anything has been derived -- answered `unmet`, and nothing asks again. So both
halves report `unmet`, including the one that was satisfiable from the start, and
a repair rule fires for the right half only because the author happened to name
it. One corpus line fixes it, and nothing ships concluding it (§19: what ships is
the occasion, not the reaction).

 What is NOT here, and it is the design's last open hat: nothing revises a
BINDING. *Fix it* therefore means *derive a better candidate*, never *amend the
one you have*. This corpus works because the command is one node accumulating
properties; a repair that had to REPLACE `ls_py` would leave `binds(plan, $c, cmd)`
pointing at the old one with nothing able to reconsider it.

## Asked STRUCTURALLY, and finding out why is wo

 Asked STRUCTURALLY, and finding out why is worth more than the check.
`kb.term("answered(<render>, spell(cmd), ls *.py | ...)")` is a ParseError:
the tool's answer is a node whose NAME the surface cannot spell -- stars,
spaces and quotes are not term syntax.

> **A tool may return something no corpus can name.**

Not a defect, and not nothing. A rule reaches it by BINDING (`$s` in
`<believe>`), which is all any rule here needs; what is impossible is a
rule that mentions one particular rendered string literally. That is the
same wall as `forbidden(...)` not being revisable from the surface -- a
thing the engine holds that the language has no way to write down -- and
it lands exactly at the artefact boundary, where the values stop being the
corpus's vocabulary and start being someone else's.
