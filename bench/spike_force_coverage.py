"""Can the canonical grammar take in the CNL this repo actually speaks? — and how much of the gap
was FORCE?

WHY THIS EXISTS. `design/form_inventory.md` §4b rests on a measurement: "over the 68 unique CNL
utterances the repo's own tests actually ingest, a canonical grammar covers 37 (54%), and 25 of the
31 failures are force (18 questions, 4 goals, 3 speech acts)". That number is the entire
justification for the force arc — and it was produced by a scratch probe that no longer exists, so
it could not be re-run after ASK/GOAL/COMMAND landed. A claim you cannot re-run is a claim you
cannot defend. This re-derives it from the tests themselves.

THE CORPUS IS EXTRACTED, NOT HAND-LISTED, and that is the point: a hand-kept list drifts toward the
things we know work. Every string literal the test suite passes to `ingest` is fair game, which
means this measures the grammar against what the repo genuinely says rather than against a sample
chosen after the fact.

⭐ WHAT THIS BENCH FOUND ON ITS FIRST HONEST RUN (2026-07-20), which is the argument for having
written it: **declaring a word as a relation makes the DECLARATION SENTENCE itself unparseable.**
`produces is a relation` parses while `produces` is unknown and REFUSES once it is a `transitive`,
because a verb-category word can no longer head an np and so cannot be a subject. The grammar has
no use-mention distinction — it cannot talk ABOUT its own vocabulary. Consequence, measured through
real `ingest`: the SAME declaration ingested TWICE routes `fact` then `unrecognized`. See
`implementation_plan.md`; it matters for making this route the default, since the multi-KB-file
model makes re-declaration the normal case.

READ THE OUTPUT AS COVERAGE OF *CNL*, NEVER OF ENGLISH. `spike_loudon_prose.py` settled that raw
prose is 0/50 and not the target (plan re-point 2026-07-20): an LLM/SLM translates prose into this
language, so what matters is whether the language is adequate for what we need to say.
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm.attrgraph import AttrGraph                                    # noqa: E402
from ugm.cnl import grammar_intake as gi                               # noqa: E402
from ugm.cnl.grammar import AMBIGUOUS, PARSED, REFUSED, parse          # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR = ROOT / "corpus" / "loudon_grammar.cnl"

#: `ingest(kb, rules, "…")` / `h.ingest(g, [], "…")` — the third positional argument is the CNL.
_INGEST = re.compile(r"\bingest\(\s*[^,()]+,\s*(?:\[\]|[^,()]+),\s*([\"'])(.*?)\1")


def corpus() -> list[str]:
    """Every distinct utterance the test suite ingests, in first-seen order."""
    seen: dict[str, None] = {}
    for path in sorted((ROOT / "tests").glob("*.py")):
        for _q, text in _INGEST.findall(path.read_text(encoding="utf-8")):
            t = text.strip()
            if t and "\\" not in t and "{" not in t:      # skip escapes and f-string templates
                seen.setdefault(t, None)
    return list(seen)


def force_of(kb, toks, banks) -> str:
    """Which FORCE the parse recovered — the declaration the router dispatches on."""
    if gi.question_of(kb, toks, banks) is not None:
        return "ask"
    if gi.goal_of(kb, toks, banks) is not None:
        return "goal"
    if gi.command_of(kb, toks, banks) is not None:
        return "command"
    if gi.asserts_content(kb, toks, banks):
        return "assert"
    return "none"


#: `R is a relation` declarations found anywhere in tests/ or corpus/. A predicate has ALWAYS needed
#: a declaration — the shipped route refuses `get_beans produces beans` until the KB says
#: `produces is a relation` — and `sync_vocabulary` derives the grammar lexicon from exactly these.
#: Not declaring them here measured a BENCH ARTIFACT (a bare KB) rather than the language: the first
#: run counted `get_beans produces beans` as a language gap when it is a vocabulary one.
#: NOT anchored to end-of-line: in a .py file the declaration sits INSIDE a string literal, so a
#: quote follows `relation` and `$` never matches. The first version silently found nothing and the
#: vocabulary fix appeared not to work — the measurement harness being the bug, for the third time
#: in this arc (`clear_fresh`, `mark_tokens`, this).
_RELATION = re.compile(r"\b([a-z_]+) is a relation\b")


def declared_relations() -> list[str]:
    found: set[str] = set()
    for d in ("tests", "corpus"):
        for path in sorted((ROOT / d).rglob("*")):
            if path.suffix in (".py", ".cnl") and path.is_file():
                found.update(_RELATION.findall(path.read_text(encoding="utf-8")))
    return sorted(found)


RELATIONS = declared_relations()

#: ⚠ DELIBERATE NEGATIVE FIXTURES — utterances the tests ingest precisely to assert they are
#: REFUSED. A refusal is the CORRECT outcome, so scoring them as coverage failures would penalise
#: the grammar for working. Hand-listed and hand-justified, because nothing in the string
#: distinguishes "gibberish on purpose" from "a construction we cannot yet say" — that judgement is
#: exactly what must not be automated away.
NEGATIVE_FIXTURES = {
    "glorp the flarn": "gibberish — pins `unrecognized`",
    "asdf qwer zzz": "gibberish — pins `unrecognized`",
    "izit bo is a suspect": "malformed question — pins refusal, not a question form",
    "whether bo suspect nonsense trailing words": "malformed — pins refusal on trailing junk",
}


def classify(text: str) -> tuple[str, str]:
    """(outcome, force) for one utterance, each on a FRESH KB so nothing leaks between lines."""
    kb = AttrGraph()
    gi.declare_grammar(kb, GRAMMAR, open_class="noun")
    banks = gi.session_banks(kb)
    for r in RELATIONS:                      # the vocabulary a real session would have declared
        banks.grammar.lexicon.setdefault(r, [gi.RELATION_CATEGORY])
    from ugm.cnl.grammar import compile_grammar
    banks = compile_grammar(banks.grammar, open_class=banks.open_class)
    kb.registers[gi.GRAMMAR_REGISTER] = banks
    try:
        outcome, toks, _eos = parse(kb, text, banks)
    except Exception as e:                      # a raise is a refusal with a reason worth seeing
        return "raised", type(e).__name__
    if outcome != PARSED:
        return outcome, ""
    gi.extend(kb, banks)
    return PARSED, force_of(kb, toks, banks)


#: The routes intake recognizes AHEAD of the grammar, by design — bank AUTHORING, which the fold
#: structurally cannot produce (`form_inventory.md` §4b class (b)). A refusal here is CORRECT, not a
#: gap, so counting it against coverage would understate the language by exactly the amount we
#: deliberately chose not to put in it.
_AUTHORING = re.compile(r"^(form |to .*:|disable that rule|forget that rule)|\bwhen\b|\?[a-z]")


def main() -> None:
    lines = corpus()
    results = [(t, *classify(t)) for t in lines]

    by_outcome = collections.Counter(o for _t, o, _f in results)
    by_force = collections.Counter(f for _t, o, f in results if o == PARSED)
    authored = [t for t, o, _f in results if o != PARSED and _AUTHORING.search(t)]
    negative = [t for t, o, _f in results if o != PARSED and t in NEGATIVE_FIXTURES
                and not _AUTHORING.search(t)]
    gaps = [(t, o) for t, o, _f in results if o != PARSED and not _AUTHORING.search(t)
            and t not in NEGATIVE_FIXTURES]

    n = len(results)
    parsed = by_outcome[PARSED]
    print("=" * 78)
    print(f"FORCE COVERAGE — {n} unique CNL utterances extracted from tests/")
    print("=" * 78)
    print(f"  parsed     {parsed:4}/{n}  ({parsed / n:.0%})")
    for k in (AMBIGUOUS, REFUSED, "raised"):
        if by_outcome[k]:
            print(f"  {k:10} {by_outcome[k]:4}/{n}  ({by_outcome[k] / n:.0%})")
    print()
    print("  by FORCE recovered (of those parsed):")
    for f, c in by_force.most_common():
        print(f"      {f:10} {c:4}")
    if by_force["none"]:
        print("      ⚠ `none` = PARSED BUT COMMITS NOTHING — the slice-2b failure shape:")
        print("        recognized, not understood (form_inventory.md §8). Worth listing below.")
    print()
    print(f"  refused BY DESIGN — bank authoring, routed ahead of the grammar : {len(authored)}")
    print(f"  refused BY DESIGN — deliberate negative fixtures                : {len(negative)}")
    print(f"  REAL GAPS                                                       : {len(gaps)}")
    sayable = n - len(authored) - len(negative)
    print()
    print(f"  ⭐ COVERAGE OF WHAT THE LANGUAGE IS MEANT TO SAY: {parsed}/{sayable} "
          f"({parsed / sayable:.0%})")
    print("     (excluding authoring, which is deliberately NOT in the grammar, and the negative")
    print("      fixtures, whose refusal is the behaviour under test)")

    if by_force["none"]:
        print()
        print("-" * 78)
        print("PARSED BUT COMMITTED NOTHING — check each: is a force missing, or is it a hedge?")
        print("-" * 78)
        for t, o, f in results:
            if o == PARSED and f == "none":
                print(f"    {t}")

    print()
    print("-" * 78)
    print("THE REAL GAPS — every one is a candidate inventory entry (form_inventory.md §5)")
    print("-" * 78)
    for t, o in gaps:
        print(f"    [{o:9}] {t}")

    print()
    print("-" * 78)
    print("REFUSED BY DESIGN (bank authoring — NOT a gap in the language)")
    print("-" * 78)
    for t in authored:
        print(f"    {t}")


if __name__ == "__main__":
    main()
