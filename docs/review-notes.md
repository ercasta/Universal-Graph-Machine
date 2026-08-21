# Review Notes

Attention.py contains several functions that might not be needed anymore: is_defeated, is_superseded, etc.

Chain.py has lots of boring stuff related to provenance, support, licence, etc. Probably overengineered.

Channels.py: probably we should demote channels to more "open world". An channels arrivals should get attentioned, using the standard mechanism

Gate.py talks about vetoes, review


sexpr.py probably to be deleted.


# New Features required:
- available to agent:
    - compute delta : computes the delta between two subgraphs (useful to get delta between desired and current state and make informed choices). Takes three nodes as param. Materializes 
    - install / remove pre-application or post-application "triggers" (they can query the delta and perform actions such as changing it). Stored in graph, but managed by engine. The agent could use this to "always remember" a prohibition or a directive.
- safety triggers (queries on rules - managed by the engine - e.g. to block "sensitive" actions, tool calls)
