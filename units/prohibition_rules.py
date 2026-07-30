"""DANGER DETECTION — "don't do anything dangerous" as a generic, KB-driven prohibition, not a hardcoded
safety check.

Two small, generic rules, each the same "declare it, read it generically" shape this whole project keeps
finding, now reused deliberately rather than reinvented:

**`dangerous_to_forbidden_rule`** — exactly `causation-core-was-sugar`'s shape: a declared `dangerous`
fact (authored via `units/author_rules.py`, from KB content like *"the production database is
dangerous"*) propagates into a `forbidden` fact via one generic rule. Get-or-create, the same NAC idiom
`goal_experiment.py`'s lineage interning already uses.

**`attempt_command_rule`** — the exact veto shape `meta_concept_unification_experiment.py` already
checked (`absent(forbidden)`, linked to the specific candidate), generalized from that experiment's
hardcoded procedure step into something a real command utterance drives: `units/goal_rules.py`'s
`command_to_goal` is reused **completely unmodified** — it still just mints a goal wanting the command's
content, force-blind and content-blind as always. This rule is a separate, independent watcher: a goal
born from a command, whose wanted content names a `target:` role, gets marked `executed` only if nothing
forbids that specific target.

**⚠ Corrected once, the hard way — worth recording rather than smoothing over.** The first version of
both patterns matched `target` as a crisp *attribute* (`atom("act", target="production_database")`),
copying the shape `identity_merge_probe_experiment.py`/`transitivity_probe_experiment.py` used for their
own, different keys. Those needed `AttrVar` because they were quantifying over *which* attribute or
relation applied. Here the relation name (`target`) is fixed at authoring time — only *which node* fills
it varies — so it needs to be matched the way `units/cnl.py` actually produces it: a role node
(`role("target", atom("t"))`), with the filler bound as an ordinary reusable match variable. The bug was
silent in hand-built test graphs (which happened to build `target` as an attribute too, matching the wrong
assumption) and only surfaced once real parsed CNL text — which correctly treats `target:` as relational —
was run through it: the veto patterns simply never matched, so every "vetoed" check was passing
vacuously. Fixed by matching through the role node with a shared variable, needing no `AttrVar` at all.

**What "executed" means, precisely, and what it deliberately does not.** This is a stand-in for "the
action was actually performed," distinct from `achieved` (which is about the wanted world-state becoming
true, `goal_rules.py`). Building a real action-dispatch mechanism (an actual `<call>`, real side effects,
`STATUS.md`'s procedures/tool-boundary arc) is a separate, larger, already-designed-but-mostly-unbuilt
piece; this rule only proves the veto composes correctly with an ordinary command-to-goal pipeline, not
that a real tool call is safely suppressed.
"""
from __future__ import annotations

from .engine import Attribute, Emit, Link, StandingUnit
from .match import absent, atom, role

DANGEROUS_PAT = (
    atom("d", name="dangerous", out=(role("target", atom("t")),)),
    absent(atom("f", name="forbidden", out=(role("target", atom("t")),))),
)

ATTEMPT_COMMAND_PAT = (
    atom("g", name="goal", from_force="command", executed=None,
         out=(role("wants", atom("act", out=(role("target", atom("t")),))),)),
    absent(atom("f", name="forbidden", out=(role("target", atom("t")),))),
)


def dangerous_to_forbidden_rule() -> StandingUnit:
    return StandingUnit("dangerous_to_forbidden", DANGEROUS_PAT,
                         Emit("forbidden", as_="f"), Link("f", "t", role="target"),
                         mutating=True)


def attempt_command_rule() -> StandingUnit:
    return StandingUnit("attempt_command", ATTEMPT_COMMAND_PAT,
                         Attribute("g", "executed", True), mutating=True)


def rules() -> dict[str, StandingUnit]:
    return {"dangerous_to_forbidden": dangerous_to_forbidden_rule(),
            "attempt_command": attempt_command_rule()}


__all__ = ["DANGEROUS_PAT", "ATTEMPT_COMMAND_PAT", "dangerous_to_forbidden_rule",
           "attempt_command_rule", "rules"]
