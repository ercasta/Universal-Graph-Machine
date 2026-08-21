# Review Notes

Attention.py:
- check if _forgo and rivals can be removed.
- ⚠ Anchored at the SEAT rather than at every moment, which is the containment story as well as the cheap -> is this still true?
- "Satisfaction, ported from the tick this loop replaces" -> can't we leverage our "compute delta" to evaluate "satisfaction"? This would mean ALWAYS setting a "goal" and checking vs that.
- Is the following code section used? Moreover the second if repeats the "widened" instead of "recover"
```
if not window:
            # Nothing in the table matched. These are NOT ported logic.
            # →
            # docs/design/attention.md#nothing-in-the-table-matched-the-engine-says-so
            if m._widen():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._recover():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._wake():
                steps.append(Step(arrivals, 0, tried, None, (), "quiet"))
                continue
```

Chain.py has lots of boring stuff related to provenance, support, licence, etc. Probably overengineered.

Channels.py: probably we should demote channels to more "open world". An channels arrivals should get attentioned, using the standard mechanism

Gate.py talks about vetoes, review


sexpr.py probably to be deleted.


# New Features required:
- available to agent:
    - compute delta : computes the delta between two subgraphs (useful to get delta between desired and current state and make informed choices). Takes three nodes as param. Materializes 
    - install / remove pre-application or post-application "triggers" (they can query the delta and perform actions such as changing it). Stored in graph, but managed by engine. The agent could use this to "always remember" a prohibition or a directive.
- safety triggers (queries on rules - managed by the engine - e.g. to block "sensitive" actions, tool calls)
