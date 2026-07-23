"""Are the fundamental epistemic blocks REASONED-OVER end to end — and CLOSED under composition?

WHY THIS EXISTS. `design/form_inventory.md` §4 tracks whether a fundamental form can be REPRESENTED
(BUILT / mechanism-exists / no-mechanism). §8 gives the definition of UNDERSTANDING: content maps
onto held forms, unambiguously and status-preservingly, AND its force is recognised. Neither tracks
the thing that actually bit in the conditionality probe: **a form can be represented, its surface can
map, the query can answer `yes` — and the reasoning can still be wrong (there, right by luck, on the
discourse token).** So this probe adds the missing clause:

    A block B is NAILED DOWN iff  (1) B is representable,  (2) surface->B maps unambiguously and
    status-preservingly,  and  (3) assert-B then ask-a-query-that-requires-reasoning-over-B returns
    the RIGHT answer WITH THE RIGHT EPISTEMIC KIND, end to end through the real `ingest`.

Clause 3 is what this file measures. It is the operational upgrade of §8: not "does it map" but
"does the MACHINE reason over the mapped form correctly".

AND CLOSURE. A set of blocks can each pass in isolation and still fail composed — hedge-OF-negation,
a conditional OVER a hedged premise, a question ABOUT a conditional. The property we want is the
useful half of the group analogy (closure, NOT a full group — there are no guaranteed inverses and
composition is not commutative: hedge-of-negation is not negation-of-hedge). Precisely:

    The blocks are CLOSED under composition iff every legal composition lands in
    {reasoned-over correctly}  ∪  {explicitly refused},  and NEVER in {silently mis-mapped}.

That is the field-with-a-defined-division-by-zero, not a total function: refusing a composition we
cannot yet reason over is CLOSED (understanding includes knowing you cannot). Committing a falsehood,
or a hard `yes` derived from an uncertain premise, is the LEAK closure forbids.

THREE VERDICTS, and the middle one is not a failure:
  PASS    — reasoned over correctly (right answer, right epistemic kind, no unsaid commitment).
  REFUSED — honestly declined (unrecognized / parsed-but-committed-nothing / a flagged gap). CLOSED.
  LEAK    — silently mis-mapped: an unsaid ink fact, a wrong answer, or a status not preserved
            (certain from uncertain, asserted from asked). THIS is what closure forbids; the
            headline number is the LEAK count.

READ THE OUTPUT AS COVERAGE OF REASONING, NOT OF ENGLISH — same caveat as spike_force_coverage.py:
prose is translated into this language; what is measured is whether the language, once entered, is
reasoned over soundly.
"""
from __future__ import annotations

import dataclasses
import pathlib
import sys
from typing import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import ugm as h                                                          # noqa: E402
from ugm.attrgraph import AttrGraph                                      # noqa: E402
from ugm.cnl import grammar_intake as gi                                 # noqa: E402
from ugm.policy import BANDED, FirmwarePolicy                            # noqa: E402
from ugm.possibility import possibility                                  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR = ROOT / "corpus" / "loudon_grammar.cnl"

PASS, REFUSED, LEAK, UNKNOWN = "PASS", "REFUSED", "LEAK", "UNKNOWN"

#: A hedge is REASONED OVER only under a banded stance (the crisp default answers `no (assumed)` for
#: a non-ink fact BY DESIGN). So clause-3 for any degree block is tested under this policy — asking a
#: hedged claim crisply and calling the `no (assumed)` a failure would be measuring the wrong mode.
BANDED_POLICY = FirmwarePolicy(uncertainty=BANDED)


def _is_band_word(ans: list[str]) -> bool:
    """A banded verdict is a positive that is NOT crisp certainty: `likely` / `possibly` / ... —
    anything that is neither `yes`/`no`/`no (assumed)` nor empty. The point of the band is that the
    answer WEARS its degree instead of collapsing to certain or absent."""
    return bool(ans) and ans != ["yes"] and not ans[0].startswith("no")

#: Adjectives the conditional/negation cases need. With open_class="noun" an undeclared word is a
#: NOUN (so `is lion dangerous` would ask `is_a dangerous`, the wrong predicate); declaring the adjs
#: is what makes the probe test the block rather than a lexicon accident.
ADJ = "dangerous is a adj\nhungry is a adj\nsafe is a adj\n"

#: The chain predicates for the DEPTH cases — p0..p5 as adjectives.
CHAIN_ADJ = "".join(f"p{i} is a adj\n" for i in range(6))


@dataclasses.dataclass
class Case:
    name: str
    axis: str                       # "isolated" | "composition"
    blocks: str                     # which fundamental block(s) — for the report
    setup: list[str]                # asserted/authored before the probe
    probe: str                      # the utterance that requires reasoning over the block(s)
    judge: Callable                 # (kb, out, before, after) -> (verdict, note)
    extra: str = ""                 # extra grammar declarations (adjs, conditional productions)
    policy: object = None           # the stance the PROBE asks under (banded, for degree blocks)


def _answer(out) -> list[str]:
    a = getattr(out, "answer", None)
    return list(a) if a else []


def run(case: Case):
    kb = AttrGraph()
    gi.declare_grammar(kb, GRAMMAR.read_text(encoding="utf-8") + case.extra, open_class="noun")
    rules: list = []
    for line in case.setup:
        h.ingest(kb, rules, line)
    before = set(gi.facts(kb))
    try:
        out = h.ingest(kb, rules, case.probe, policy=case.policy)
    except Exception as e:                       # a raise is a refusal with a reason worth seeing
        return REFUSED, f"raised {type(e).__name__}: {e}", None
    after = set(gi.facts(kb))
    verdict, note = case.judge(kb, out, before, after)
    return verdict, note, out


# ---------------------------------------------------------------------------
# Judges — each states the LEAK condition explicitly, and records the actual
# answer so the UNKNOWNs can be classified by a human.
# ---------------------------------------------------------------------------

def _committed(before, after) -> set:
    return after - before


def j_certainty(kb, out, before, after):
    ans = _answer(out)
    if ans == ["yes"]:
        return PASS, "asserted P, asked P -> yes"
    return LEAK, f"asserted P, asked P -> {ans or out.kind} (should be yes)"


def j_negation(kb, out, before, after):
    """Asserted ¬P (has_not), asked P. A `yes` is a LEAK. `no` is a hard PASS; `no (assumed)` passes
    but is worth flagging — the explicit counter-fact was not used as a positive disproof (CWA got
    there anyway)."""
    ans = _answer(out)
    if ans == ["yes"]:
        return LEAK, "asserted ¬P but asked P -> yes"
    if ans == ["no"]:
        return PASS, "hard no — the explicit negation was consulted"
    if ans and ans[0].startswith("no"):
        return PASS, f"{ans} — negative, but ASSUMED not hard (explicit ¬P not used as disproof)"
    return UNKNOWN, f"{ans or out.kind}"


def j_hedge(kb, out, before, after):
    """Clause-3 under a BANDED ask (see BANDED_POLICY). Represent: possibility 0.75. Reason: the ask
    must answer a BAND WORD (`likely`), not over-claim `yes`, not collapse to `no (assumed)`, and
    commit no ink."""
    poss = possibility(kb, "has", "lion", "mane")
    ans = _answer(out)
    if _committed(before, after):
        return LEAK, f"a hedge committed ink: {_committed(before, after)}"
    if poss != 0.75:
        return LEAK, f"hedge not represented at its band (possibility={poss})"
    if ans == ["yes"]:
        return LEAK, f"band={poss} but the ask answered a certain `yes` (over-claim)"
    if _is_band_word(ans):
        return PASS, f"band={poss}, banded ask -> {ans} (degree preserved in the answer)"
    return LEAK, f"band={poss} represented but the ask lost it -> {ans} (not reasoned over)"


def j_conditional(kb, out, before, after):
    """The by-luck check. `yes` is necessary but NOT sufficient — the derived fact must land in the
    interpretation scope (`gi.facts`), not on the discourse token."""
    ans = _answer(out)
    derived = ("lion", "is", "dangerous") in set(gi.facts(kb))
    if ans == ["yes"] and derived:
        return PASS, "derived through the rule AND the fact landed in scope"
    if ans == ["yes"] and not derived:
        return LEAK, "answered yes but the derived fact is NOT in the interpretation scope (by luck)"
    return LEAK, f"conditional did not fire: {ans or out.kind}, derived-in-scope={derived}"


def j_refused_or_leak(kb, out, before, after):
    """For blocks/compositions with no surface yet: REFUSED is CLOSED, any commitment is a LEAK."""
    committed = _committed(before, after)
    if committed:
        return LEAK, f"no surface expected, yet it committed: {committed}"
    if out.kind in ("unrecognized", "ambiguous"):
        return REFUSED, f"declined ({out.kind}) — closed"
    if out.kind == "fact":
        return LEAK, f"routed `fact` — mis-mapped a construction it should refuse"
    return REFUSED, f"kind={out.kind}, no commitment"


def j_hedge_negation(kb, out, before, after):
    """hedge OF negation: `the lion generally has no mane`. CLOSED if refused OR represented as a
    banded has_not with no ink. The dangerous middle: a `fact` SUCCESS verdict that represents
    NOTHING (no ink, no band) — §8's recognized-not-understood, and a LEAK because the caller is told
    it landed."""
    committed = _committed(before, after)
    if ("lion", "has", "mane") in committed:
        return LEAK, "hedged negation committed the POSITIVE as ink"
    if committed:
        return LEAK, f"hedged negation committed ink: {committed}"
    band_neg = possibility(kb, "has_not", "lion", "mane")
    if band_neg and band_neg < 1.0:
        return PASS, f"represented as a banded negation (possibility has_not={band_neg})"
    if out.kind in ("unrecognized", "ambiguous"):
        return REFUSED, f"declined ({out.kind}) — closed, no silent mis-map"
    if out.kind == "fact":
        return LEAK, ("routed `fact` (success) but represents NOTHING — no ink, no band. §8 "
                      "recognized-not-understood: the composition parses and silently drops")
    return UNKNOWN, f"kind={out.kind}, no ink, no band"


def j_cond_over_negation(kb, out, before, after):
    """conditional whose premise is a negation: `?x is safe when ?x has no mane` + `lion has no mane`.
    PASS if it derives `safe` (has_not satisfied the premise) and lands in scope. REFUSED if the rule
    surface with `has no` will not parse. LEAK if it answers wrong."""
    ans = _answer(out)
    derived = ("lion", "is", "safe") in set(gi.facts(kb))
    if ans == ["yes"] and derived:
        return PASS, "negated premise satisfied the rule, derived in scope"
    if ans == ["yes"] and not derived:
        return LEAK, "answered yes but nothing derived in scope"
    if ans and ans[0].startswith("no"):
        return REFUSED, f"did not fire ({ans}) — closed if the negated premise simply is not matched"
    return UNKNOWN, f"{ans or out.kind}, derived={derived}"


def j_cond_over_hedge(kb, out, before, after):
    """⭐ THE SHARPEST CLOSURE PROBE: a conditional over a HEDGED premise, asked under a BANDED
    stance. `the lion generally is hungry` (band 0.75) + `?x is dangerous when ?x is hungry`, then
    ask `is lion dangerous`.

    STATUS PRESERVATION is the whole point. A hard `yes` or an ink `dangerous` is a LEAK: certainty
    manufactured from a 0.75 premise. The SOUND result is a BANDED verdict — the uncertainty PROPAGATED
    through the rule (PASS). A conservative `no (assumed)` is closed but means the composition was not
    reasoned over (REFUSED)."""
    ans = _answer(out)
    prem = possibility(kb, "is", "lion", "hungry")
    if ("lion", "is", "dangerous") in set(gi.facts(kb)):
        return LEAK, f"derived `dangerous` as INK (certain) from a {prem}-band premise"
    if ans == ["yes"]:
        return LEAK, f"answered a certain `yes` from a {prem}-band premise (status not preserved)"
    if _is_band_word(ans):
        return PASS, f"premise band={prem} PROPAGATED through the rule -> {ans} (status preserved)"
    if ans and ans[0].startswith("no"):
        return REFUSED, f"premise band={prem} not matched -> {ans} (conservative, closed, not reasoned)"
    return UNKNOWN, f"premise band={prem}, ask -> {ans or out.kind}"


def j_suppose_negation(kb, out, before, after):
    """scope(suppose) OF negation: `suppose lion has no mane : lion is safe` with `?x is safe when ?x
    has no mane`. PASS if the counterfactual reasons over the NEGATED assumption (the `has_not` premise
    satisfies the rule under the hypothesis) -> yes, inking nothing. A REFUSED means the suppose surface
    would not take the negated assumption; a `yes` that inks is a LEAK."""
    ans = _answer(out)
    if _committed(before, after):
        return LEAK, f"a counterfactual committed ink: {_committed(before, after)}"
    if out.kind != "suppose":
        return REFUSED, f"suppose surface did not take the negation (kind={out.kind}) — closed"
    if ans == ["yes"]:
        return PASS, "counterfactual reasoned over the ¬-assumption -> yes (no ink)"
    return REFUSED, f"entertained but did not derive ({ans}) — conservative, closed, not reasoned"


def j_suppose_hedge(kb, out, before, after):
    """scope(suppose) OF degree: `suppose lion generally is hungry : lion is dangerous`, banded ask.
    The SOUND result carries the assumption's band into the prediction (a band word). A certain `yes`
    from a 0.75 assumption is a LEAK; a conservative `no (assumed)` is CLOSED but the hedge was DROPPED
    (not reasoned) — the composition gap this audit exists to surface."""
    ans = _answer(out)
    if _committed(before, after):
        return LEAK, f"a counterfactual committed ink: {_committed(before, after)}"
    if out.kind != "suppose":
        return REFUSED, f"suppose surface did not take the hedge (kind={out.kind}) — closed"
    if ans == ["yes"]:
        return LEAK, "certain `yes` from a hedged (0.75) assumption — status not preserved"
    if _is_band_word(ans):
        return PASS, f"assumption band propagated into the prediction -> {ans}"
    return REFUSED, f"hedge DROPPED, answered conservatively ({ans}) — closed, not reasoned"


def j_causation_hedge(kb, out, before, after):
    """causation OF degree: `that lion generally is hungry causes that lion is dangerous` + the hedged
    antecedent, banded ask. SOUND = the band rides the causal link into the consequent (a band word).
    A certain `yes`/ink is a LEAK; a conservative `no (assumed)` is CLOSED but the band was DROPPED at
    the reification bridge (the propositional-cause handle does not carry the fork)."""
    ans = _answer(out)
    if ("lion", "is", "dangerous") in set(gi.facts(kb)):
        return LEAK, "derived `dangerous` as certain INK from a hedged causal antecedent"
    if ans == ["yes"]:
        return LEAK, "certain `yes` — the band was lost across the causal link"
    if _is_band_word(ans):
        return PASS, f"band rode the causal link into the consequent -> {ans}"
    return REFUSED, f"band DROPPED at the cause bridge, answered conservatively ({ans}) — closed, not reasoned"


def j_causation_negation(kb, out, before, after):
    """causation OF negation: `that lion has no mane causes that lion is safe` + `lion has no mane`.
    SOUND = the negated antecedent satisfies the causal link -> `safe` derived (yes). A conservative
    `no (assumed)` is CLOSED but the negation was NOT consulted at the reification bridge (the handle
    does not carry the `has_not`)."""
    ans = _answer(out)
    derived = ("lion", "is", "safe") in set(gi.facts(kb))
    if ans == ["yes"] and derived:
        return PASS, "negated antecedent satisfied the causal link -> safe derived"
    if ans == ["yes"]:
        return LEAK, "answered yes but nothing derived in scope"
    return REFUSED, f"negation NOT consulted at the cause bridge ({ans}) — closed, not reasoned"


def j_negation_question(kb, out, before, after):
    """negation UNDER ask force: `is lion not hungry` with `lion is hungry` known. Force must be kept
    (no ink). SOUND reasoning consults the positive to answer the negated question. CLOSED if it keeps
    ask force; LEAK only if it commits or loses force."""
    ans = _answer(out)
    if _committed(before, after):
        return LEAK, f"a question committed: {_committed(before, after)}"
    if out.kind not in ("answer", "question"):
        return LEAK, f"routed `{out.kind}` — a negated question lost its ask force"
    return PASS, f"kept ask force, committed nothing -> {ans}"


def j_hedged_rule(kb, out, before, after):
    """degree ON the conditional itself: `generally ?x is dangerous when ?x is hungry` — a HEDGED RULE
    (the rule holds usually, not always). No surface yet: REFUSED (unrecognized/rule) is CLOSED; a
    committed ink or a mis-mapped fact is a LEAK."""
    if _committed(before, after):
        return LEAK, f"a hedged rule committed ink: {_committed(before, after)}"
    if out.kind in ("unrecognized", "ambiguous", "rule"):
        return REFUSED, f"declined/plain-rule ({out.kind}) — closed (the hedge-on-rule is not surfaced)"
    return LEAK, f"routed `{out.kind}` — mis-mapped a hedged rule"


def j_deriv_depth(kb, out, before, after):
    """DERIVATIONAL depth: a chain of N rules, ask the tail. This is the axis the subgoal stack and
    the fixpoint already cover — the memento records a de-recursed 601-deep NAF closure, so depth
    here is not Python-recursion-bound."""
    ans = _answer(out)
    if ans == ["yes"]:
        return PASS, "chained through every rule to the tail -> yes (fixpoint carries depth)"
    return LEAK, f"the chain broke before the tail -> {ans or out.kind}"


def j_band_depth(kb, out, before, after):
    """STATUS at derivational depth: an uncertain root through a depth-N chain, banded ask. The band
    must PROPAGATE (a band word), never harden into ink or a certain `yes` along the way — that would
    be certainty manufactured over depth, the LEAK of j_cond_over_hedge repeated at each hop."""
    ans = _answer(out)
    if any(p == "is" and o.startswith("p") for _s, p, o in set(gi.facts(kb))):
        return LEAK, "an intermediate hardened into INK — certainty manufactured over depth"
    if _is_band_word(ans):
        return PASS, f"uncertainty PRESERVED through the whole chain -> {ans}"
    if ans and ans[0].startswith("no"):
        return REFUSED, f"the chain did not carry the band -> {ans} (conservative, closed)"
    return UNKNOWN, f"{ans or out.kind}"


def j_hedged_question(kb, out, before, after):
    """hedge OF a question: `is lion generally has mane`. Force x content composition. Through `ingest`
    a question surfaces as `Outcome.kind == "answer"` (that IS the question outcome — `gi.route` names
    it `question`, `ingest` answers it). CLOSED if it answers/refuses committing nothing; LEAK only if
    it commits, or routes as an ASSERTION (force lost -> a question became a belief)."""
    committed = _committed(before, after)
    if committed:
        return LEAK, f"a question committed: {committed}"
    if out.kind in ("answer", "question"):
        return PASS, f"kept its ASK force, committed nothing -> {_answer(out)} (degree likely ignored)"
    if out.kind in ("unrecognized", "ambiguous"):
        return REFUSED, f"declined ({out.kind}) — closed"
    return LEAK, f"a hedged question routed `{out.kind}` (force lost — became a belief)"


# ---------------------------------------------------------------------------
# The cases
# ---------------------------------------------------------------------------

CASES = [
    # ---- ISOLATED: clause-3 end to end -----------------------------------
    Case("certainty", "isolated", "certainty (ink)",
         ["the lion has a mane"], "is lion has mane", j_certainty),
    Case("negation", "isolated", "negation (has_not)",
         ["the lion has no mane"], "is lion has mane", j_negation),
    Case("hedging", "isolated", "degree / hedging",
         ["the lion generally has a mane"], "is lion has mane", j_hedge, policy=BANDED_POLICY),
    Case("conditionality", "isolated", "conditionality (rule layer)",
         ["?x is dangerous when ?x is hungry", "the lion is hungry"],
         "is lion dangerous", j_conditional, extra=ADJ),
    Case("attribution", "isolated", "attribution (no surface yet)",
         [], "some naturalists consider the lion a cat", j_refused_or_leak),
    Case("quantification", "isolated", "quantification (partial)",
         [], "every person is a mortal", j_refused_or_leak),

    # ---- COMPOSITION: closure --------------------------------------------
    Case("hedge x negation", "composition", "degree o negation",
         [], "the lion generally has no mane", j_hedge_negation),
    Case("conditional x negation", "composition", "conditionality o negation",
         ["?x is safe when ?x has no mane", "the lion has no mane"],
         "is lion safe", j_cond_over_negation, extra=ADJ),
    Case("conditional x hedge", "composition", "conditionality o degree",
         ["?x is dangerous when ?x is hungry", "the lion generally is hungry"],
         "is lion dangerous", j_cond_over_hedge, extra=ADJ, policy=BANDED_POLICY),
    Case("hedge x question", "composition", "force(ask) o degree",
         ["the lion has a mane"], "is lion generally has mane", j_hedged_question),

    # ---- WIDENED AUDIT 2026-07-23: the untested cells over the BUILT axes ----
    # The pattern under test: does an axis SURVIVE composition, or is it silently dropped? PASS =
    # reasoned over (band propagates, negation consulted). REFUSED = closed but the axis was DROPPED
    # (answered conservatively). LEAK = a silent mis-map. Reveals that DEGREE and PROPOSITIONAL
    # CAUSATION are the poor composers — they live in separate productions (interpretation fork /
    # reification bridge), not on the one fold, so their annotation is lost where they meet another axis.
    Case("suppose x negation", "composition", "scope(suppose) o negation",
         ["?x is safe when ?x has no mane"],
         "suppose lion has no mane : lion is safe", j_suppose_negation, extra=ADJ),
    Case("suppose x hedge", "composition", "scope(suppose) o degree",
         ["?x is dangerous when ?x is hungry"],
         "suppose lion generally is hungry : lion is dangerous", j_suppose_hedge,
         extra=ADJ, policy=BANDED_POLICY),
    Case("causation x hedge", "composition", "causation o degree",
         ["that lion generally is hungry causes that lion is dangerous", "lion generally is hungry"],
         "is lion dangerous", j_causation_hedge, extra=ADJ, policy=BANDED_POLICY),
    Case("causation x negation", "composition", "causation o negation",
         ["that lion has no mane causes that lion is safe", "the lion has no mane"],
         "is lion safe", j_causation_negation, extra=ADJ),
    Case("negation x question", "composition", "force(ask) o negation",
         ["the lion is hungry"], "is lion not hungry", j_negation_question, extra=ADJ),
    Case("hedged rule", "composition", "degree o conditionality (on the rule)",
         [], "generally ?x is dangerous when ?x is hungry", j_hedged_rule, extra=ADJ),

    # ---- DEPTH: does composition hold at ARBITRARY depth, not just pairwise? ----
    # Two OPPOSITE axes. Derivational depth (chaining/subgoals) is mechanically arbitrary; the
    # representational-nesting axis is the `hedge x negation` LEAK above — a depth-2 nest that already
    # fails, so depth-N nesting is not closed. These two cases measure the good axis; the composition
    # block measures the bad one.
    Case("derivational depth", "depth", "chaining / subgoals — depth 5",
         [f"?x is p{i + 1} when ?x is p{i}" for i in range(5)] + ["the lion is p0"],
         "is lion p5", j_deriv_depth, extra=CHAIN_ADJ),
    Case("band-propagation depth", "depth", "degree through a depth-3 chain",
         [f"?x is p{i + 1} when ?x is p{i}" for i in range(3)] + ["the lion generally is p0"],
         "is lion p3", j_band_depth, extra=CHAIN_ADJ, policy=BANDED_POLICY),
]


def main() -> None:
    results = [(c, *run(c)) for c in CASES]

    print("=" * 90)
    print("EPISTEMIC CLOSURE PROBE -- clause-3 (reasoned-over) + closure-under-composition")
    print("=" * 90)

    def block(title, axis):
        print()
        print(f"-- {title} " + "-" * (86 - len(title)))
        for c, verdict, note, out in results:
            if c.axis != axis:
                continue
            mark = {"PASS": "[+]", "REFUSED": "[.]", "LEAK": "[X]", "UNKNOWN": "[?]"}[verdict]
            print(f"  {mark} {verdict:8} {c.name:24} [{c.blocks}]")
            print(f"        probe: {c.probe!r}")
            print(f"        {note}")

    block("ISOLATED BLOCKS — is each one actually reasoned over?", "isolated")
    block("COMPOSITIONS — is the set CLOSED?", "composition")
    block("DEPTH — does closure hold at ARBITRARY depth (chaining vs nesting)?", "depth")

    counts = {v: sum(1 for _c, ver, _n, _o in results if ver == v)
              for v in (PASS, REFUSED, LEAK, UNKNOWN)}
    leaks = [c.name for c, ver, _n, _o in results if ver == LEAK]
    unknowns = [c.name for c, ver, _n, _o in results if ver == UNKNOWN]

    print()
    print("=" * 90)
    print(f"  PASS {counts[PASS]}   REFUSED(closed) {counts[REFUSED]}   "
          f"LEAK {counts[LEAK]}   UNKNOWN(needs human) {counts[UNKNOWN]}")
    print("=" * 90)
    print(f"  ** CLOSURE HEADLINE -- silent mis-maps (LEAKs): {len(leaks)}")
    if leaks:
        print(f"     {leaks}")
    if unknowns:
        print(f"  [?] needs a human epistemic judgement: {unknowns}")
    print()
    print("  REFUSED is CLOSED, not failed: declining a construction we cannot yet reason over is")
    print("  the honest boundary. Only LEAKs violate closure.")


if __name__ == "__main__":
    main()
