# `experts.py` 

## Module overview

Experts: one graph, one history, several tables and several rule sets.

    python -m ugm.probes.experts

`ugm/table.py` puts several agents in a room. This is the other axis, and the
two should not be confused:

| | `ugm.table` -- AGENTS | `ugm.experts` -- EXPERTS |
|---|---|---|
| what differs | what they **believe** | what they **know how to do** |
| the graph | one per agent, disjoint | **one, shared** |
| what crosses | an **utterance**, re-read in the hearer's scope | nothing -- a conclusion is simply there |
| fog of war | structural | none, by construction |

So an expert is not a small agent. Two agents can disagree about whether the
door is locked; two experts cannot, because there is one chain and one answer.
What an expert has of its own is **a rule set and a table** -- which is exactly
what §19 says expertise consists of: *the right rules coming to mind at the
right moment.*