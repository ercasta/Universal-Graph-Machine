# 0006. A producer joins an instance only if comparable with EVERY producer already wired

**Status:** Accepted
**Source:** substrate_inversion.md §3b — the correction that made assembly work at all

## Context

With the index alone, every producer of a matching predicate is wired into one instance. That
instance then sees every hypothesis at once and derives all of them, which destroys the whole point of
assembling scope from topology.

## Decision

**A producer joins an existing instance only if it is comparable — ancestor, descendant, or
identical — with *every* producer already wired into that instance.** Otherwise it spawns a new instance.

The test is purely local over the topology that already exists, and it names no scope.

## Evidence

- **The quantifier is load-bearing.** `base` is an ancestor of both branches, so an *any*-test lets
  the second branch join the instance holding the first, and the chains collapse regardless. Measured.
- **The policy is only half a mechanism.** A freshly spawned sibling instance is wired to one branch only and
  sees `base` solely because that branch carries it through. Without accretion on carriers the spawned instance
  is starved and derives nothing — which is exactly how the first spike run failed.

## Consequences

- Sibling hypotheses stay separate for free, and no scope object exists anywhere.
- Two independent `given`s are two *worlds*: negation does not see across them, and joining worlds is what a
  merge carrier is for. This presents identically to a bug and is the opposite of one.
- Instance count is sensitive to how offers are *identified*, which is where `0023` went wrong.
