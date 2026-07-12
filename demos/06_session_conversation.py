#!/usr/bin/env python
"""DEMO 6 — a live SESSION: one KB, a stream of turns.

    python demos/06_session_conversation.py

Demos 1-5 are `.cnl` files: `run.py` answers each bare question line against a FRESHLY loaded
copy of the corpus (see its docstring) — great for isolated, clean `why` traces, but it
never shows the SAME kb changing turn over turn. `ingest` is the layer that does: one
utterance at a time, against one live `kb` + `rules`, so a fact asserted in turn 3 is
still there in turn 8, a rule added mid-conversation reasons IMMEDIATELY, and `focus`
tracks what the conversation is "about" without any of that being a special mechanism —
it all runs on the SAME CNL surface demos 1-5 use (see `docs/architecture.md` §8).

What this buys over calling `ask_goal` by hand, turn by turn:
  - ONE entry (`ingest`) routes a raw utterance to fact / question / rule / focus-move /
    rule-disable by WHICH RECOGNITION FORM FIRES — never a Python classifier sniffing the
    string. (`docs/cnl_intake_design.md` §D.) A fact and a question look the same to the
    caller: hand over text, read the `Outcome`.
  - A `HEAD when ...` utterance authors a REAL rule mid-conversation, and it reasons on
    the very next question — no reload, no restart.
  - `forget that rule` disables the last-authored rule (a marker, not a deletion) if it
    turns out to be wrong.
  - `focus on X` / `forget that` track the discourse's working set; ordinary utterances
    widen it automatically.
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ugm as h


def turn(kb, rules, utterance):
    """Run one utterance through `ingest` and print the turn like a transcript."""
    outcome = h.ingest(kb, rules, utterance)
    print(f"\n  >  {utterance}")
    if outcome.kind == "answer":
        for i, line in enumerate(outcome.answer):
            arrow = "  => " if i == 0 else "     "
            print(f"  {arrow}{line}")
    elif outcome.kind == "rule":
        if outcome.added_rules:
            print(f"     [rule added: {outcome.added_rules[0].key}]")
        else:
            print("     [rule rejected]")
    elif outcome.kind == "rule-disable":
        print(f"     [disabled: {outcome.disabled_keys}]")
    elif outcome.kind == "focus":
        print(f"     [focus: {outcome.focus_op}]")
    elif outcome.kind == "fact":
        print("     [ok]")
    else:
        print(f"     [{outcome.kind}]")
    return outcome


def main():
    print("=" * 70)
    print("  06_session_conversation.py — a live, multi-turn session")
    print("=" * 70)

    kb, rules = h.load_corpus("")   # start empty; the conversation builds the KB

    print("\n  -- Facts and a question, same KB across turns --")
    turn(kb, rules, "mango is in_stock")
    turn(kb, rules, "alice is a customer")
    turn(kb, rules, "alice wants mango")
    turn(kb, rules, "?c gets ?d when ?c wants ?d and ?d is in_stock")
    turn(kb, rules, "is alice gets mango")

    print("\n  -- A fact that doesn't satisfy the rule yet --")
    turn(kb, rules, "bob is a customer")
    turn(kb, rules, "bob wants durian")
    turn(kb, rules, "is bob gets durian")           # durian: not in_stock -> no

    print("\n  -- Mid-conversation rule repair (no reload) --")
    turn(kb, rules, "durian is in_stock")           # a new fact, live
    turn(kb, rules, "is bob gets durian")            # now yes: the SAME rule, same kb

    print("\n  -- Runtime rule authoring: teach the agent a new consequence --")
    turn(kb, rules, "?c is happy when ?c gets ?d")
    turn(kb, rules, "why alice is happy")              # copula-state predicate needs the "is" (see README)

    print("\n  -- Disabling a rule stops FUTURE derivations (not past ones) --")
    turn(kb, rules, "forget that rule")               # disables 'happy', the last one added
    turn(kb, rules, "carol is a customer")
    turn(kb, rules, "carol wants mango")
    turn(kb, rules, "is carol gets mango")            # still reasons: 'gets' rule untouched
    turn(kb, rules, "is carol happy")                 # 'happy' rule disabled -> no longer derivable

    print("\n  -- Focus: an explicit discourse move (inspectable, not a hidden intent) --")
    turn(kb, rules, "focus on alice")
    print(f"     current focus centers: {sorted(h.focus.top_centers(kb))}")
    turn(kb, rules, "forget that")                    # pop back to the broader implicit frame
    print(f"     current focus centers: {sorted(h.focus.top_centers(kb))}")

    print()


if __name__ == "__main__":
    main()
