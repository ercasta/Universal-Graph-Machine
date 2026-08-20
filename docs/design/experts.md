# `experts.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

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

## An expert is a subset, read off the graph

Nothing here keeps a registry. An expert's rules are what the graph says they
are:

    knows(geometry, <area>)             this expert has this rule
    extends(geometry, arithmetic)       ...and everything that one has

and inheritance is **one ordinary rule**, which is why `extends` needed no
engine support and is transitive for free:

    rule <inherit> = implies( { +extends(?e, ?f), +knows(?f, ?r) },
                              { +knows(?e, ?r) } )

The surface keyword is a convenience over exactly that and nothing more:

    expert geometry extends arithmetic
    rule <area> = implies( ... )

`which rules does this expert have` is therefore an ordinary query, and a rule
can conclude `knows(...)` at run time -- an expert that learns a rule is the
`adopt` door plus one fact.

## Consulting one

    +consult(geometry, area(rect(3, 4)))        the request
    +question(area(rect(3, 4)))                 what the consulted expert sees
    +reply(area(rect(3, 4)), 12)                what it concludes
    +answered(geometry, area(rect(3, 4)), 12)   what the caller sees

⭐ **The last line is deliberately a tool's answer.** From the caller's side an
expert and a tool are the same shape, so a corpus that consults one can be
pointed at the other without touching a rule. That is the honest reading of what
an expert is: a request answered by *a search* rather than by a function, where
a tool is answered by a function rather than by a search.

⚠⚠⚠ **An expert may consult an expert, so this is a STACK and it needs a cycle
test.** Depth alone is not enough: `A -> B -> A` is legitimate when the second
question is a different one, and a loop when it is not. So what is refused is a
repeated **(expert, question)** pair already on the stack, which is precise --
and it is refused onto the record as `refused_consult(...)` rather than silently,
because a consultation that quietly returns nothing is indistinguishable from
one that had nothing to say.

## What this does NOT do, stated rather than discovered

* It is a **loop**, not a gate door, so it belongs to the table loop and not to
  the shipped one. Consultation is where one expert's table stops being consulted
  and another's starts, and a table is the one thing the shipped loop has not got.
* An expert's conclusions are **not contained**. One chain was the point, so a
  consulted expert that concludes nonsense has concluded it for everybody. That
  is the cost of sharing beliefs and it is the reason `ugm.table` exists for the
  other case.
