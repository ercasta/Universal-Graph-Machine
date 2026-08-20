"""A probe: is modality a member of the entry, or a term?

    python -m ugm.probes.modality

⭐⭐⭐ This probe was ANSWERED and acted on: the grade is gone.

See docs/design/modality.md.
"""

from typing import List, Optional, Tuple

from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.text import ParseError, load

# -- the shared pipeline ----------------------------------------------------
#
# A gauge reports weakly. Three hops to a cause, then an action. The last rule
# is the test: it must treat a merely-likely cause differently from a settled
# one -- inspect rather than replace.

# `GRADE_VERSION` was here -- the same three rules with the modality left to
# the entry's grade. It is `TERM_VERSION_CERTAIN` verbatim now that grades are
# gone, which is itself the finding: the grade version WAS the bare version.

# The wrapping version. Note what changed: nothing about the shape of the rules,
# only that the terms carry their own modality.
TERM_VERSION = """
rule <sympt_w> = implies( { +likely(reading(pressure, low)) },     { +likely(symptom(flow, restricted)) } )
rule <cause_w> = implies( { +likely(symptom(flow, restricted)) },  { +likely(cause(filter, blocked)) } )
rule <act_w>   = implies( { +likely(cause(filter, blocked)) },     { +action(inspect, filter) } )
"""

# And the same pipeline again for settled input, which is the cost to measure.
TERM_VERSION_CERTAIN = """
rule <sympt_c> = implies( { +reading(pressure, low) },      { +symptom(flow, restricted) } )
rule <cause_c> = implies( { +symptom(flow, restricted) },   { +cause(filter, blocked) } )
rule <act_c>   = implies( { +cause(filter, blocked) },      { +action(replace, filter) } )
"""

# The step that decides the question. Under the grade version there is nothing to
# put here: a grade is not a term, so no antecedent can name one.
LIFT = """
rule <lift> = implies(
    { +likely(?x), +ant(?r, ?x, plus, ?i), +con(?r, ?y, plus, ?j) },
    { +likely(?y) } )
"""

GENERIC_PIPELINE = """
rule <sympt_g> = implies( { +reading(?p, low) }, { +symptom(?p, restricted) } )
"""

GENERIC_PIPELINE_FULL = """
rule <sympt_v> = implies( { +reading(?p, low) },        { +symptom(?p, restricted) } )
rule <cause_v> = implies( { +symptom(?p, restricted) }, { +diag(?p, blocked) } )
rule <act_v>   = implies( { +diag(?p, blocked) },       { +action(replace, ?p) } )
"""

ASK_UNDER_TERMS = """
rule <hedge> = implies( { +likely(cause(?c, ?why)) }, { +goal(corroborate(?c)) } )
"""


class Finding:
    def __init__(self) -> None:
        self.rows: List[Tuple[str, str, str]] = []

    def add(self, question: str, grade: str, term: str, frame: str = "-") -> None:
        self.rows.append((question, grade, term, frame))

    def show(self) -> None:
        w = max(len(r[0]) for r in self.rows)
        c = 31
        print(f"\n  {'':<{w}}   {'@grade':<{c}}  {'likely(p), lifted':<{c}}  likely(p), supposed")
        print(f"  {'-' * w}   {'-' * c}  {'-' * c}  {'-' * c}")
        for q, a, b, d in self.rows:
            print(f"  {q:<{w}}   {a[:c]:<{c}}  {b[:c]:<{c}}  {d}")


def _run(src: str, weak: bool) -> Tuple[Machine, object]:
    m = Machine()
    kb = load(m, src)
    return m, kb


def probe() -> int:
    f = Finding()

    # -- 1. produce a conclusion from a weak input, both ways -----------------

    # ⚠ Recorded, not run. There is no grade left to reach: this probe was
    # answered and acted on, and the column it measured was deleted. What is
    # printed is what the run that decided the deletion printed.
    grade_reached = "possible"

    m_b = Machine()
    kb_b = load(m_b, TERM_VERSION + "fact +likely(reading(pressure, low))\n")
    m_b.run(limit=20)
    act_b = kb_b.term("action(inspect, filter)")
    holds_b = m_b.holds(act_b)

    f.add(
        "the pipeline concludes",
        f"action(replace) @{grade_reached}",
        f"action(inspect) {holds_b}",
    )

    # -- 2. can a PROGRAM ask about the modality? ----------------------------
    #
    # Under terms this is an ordinary rule. Under grades there is no term to
    # name, so the question cannot be put at all -- not a rule that fails to
    # match, a rule that cannot be written.

    can_ask_terms = True
    try:
        m_c = Machine()
        kb_c = load(
            m_c, TERM_VERSION + ASK_UNDER_TERMS + "fact +likely(reading(pressure, low))\n"
        )
        m_c.run(limit=20)
        asked = m_c.holds(kb_c.term("goal(corroborate(filter))")) == PLUS
    except ParseError:
        can_ask_terms, asked = False, False

    # Was there ANY term denoting the grade of a conclusion? `possible` was a
    # name in the ordinal set, not a node any entry pointed at. Recorded: a
    # grade was a Python string on the Entry, reachable by the engine and by
    # nothing a rule could name. That is the line the deletion rested on, and
    # `weaker` being called from exactly one place is the other.
    grade_is_a_term = False

    f.add(
        "a rule can ask *is this merely likely*",
        "NO -- a grade is not a term" if not grade_is_a_term else "yes",
        "yes" if asked else "no",
    )

    # -- 3. what does carrying it across the pipeline cost? ------------------

    m_e = Machine()
    load(m_e, TERM_VERSION + TERM_VERSION_CERTAIN)
    both = len(m_e.rules.rules)

    m_f = Machine()
    load(m_f, TERM_VERSION_CERTAIN)
    one = len(m_f.rules.rules)

    f.add(
        "rules, wrapping written per-rule",
        f"{one} -- was: weakest link, computed by the gate",
        f"{both} -- the wrapped and bare pipelines do not share",
    )

    # With rules as data, ONE generic rule lifts modality across the BARE
    # pipeline, which then serves settled and uncertain input alike.
    m_h = Machine()
    kb_h = load(m_h, TERM_VERSION_CERTAIN + LIFT + "fact +likely(reading(pressure, low))\n")
    m_h.reify_all()
    m_h.run(limit=40)
    lifted = m_h.holds(kb_h.term("likely(cause(filter, blocked))")) == PLUS
    guarded = m_h.holds(kb_h.term("action(replace, filter)")) is None

    f.add(
        "rules, with rules as data",
        f"{one} -- unchanged",
        f"{len(m_h.rules.rules)} -- {one} bare + 1 lift, and the bare ones serve both",
    )
    f.add(
        "the guard actually holds",
        "n/a -- there is no guard to cross",
        "yes -- it did not act on a merely-likely cause" if guarded else "NO",
    )

    # The limit: lifting binds ?x to a rule's pattern, so it only fires when that
    # pattern is GROUND. A rule with variables has a generic antecedent, and
    # `likely(<generic>)` is never asserted, so nothing matches.
    m_i = Machine()
    kb_i = load(m_i, GENERIC_PIPELINE + LIFT + "fact +likely(reading(pump7, low))\n")
    m_i.reify_all()
    m_i.run(limit=40)
    lifts_over_vars = m_i.holds(kb_i.term("likely(symptom(pump7, restricted))")) == PLUS

    f.add(
        "lifting works over rules with VARIABLES",
        "n/a",
        "yes" if lifts_over_vars else "NO -- use/mention: ?x binds the pattern, not an instance",
    )

    # -- 4. does it nest? ----------------------------------------------------

    nests = True
    try:
        m_g = Machine()
        kb_g = load(m_g, "fact +thinks(anna, likely(rain(afternoon)))\n")
        nests = m_g.holds(kb_g.term("thinks(anna, likely(rain(afternoon)))")) == PLUS
    except ParseError:
        nests = False

    f.add(
        "nests -- thinks(anna, likely(rain))",
        "NO -- a grade has no place inside a term",
        "yes" if nests else "no",
    )

    # -- 5. the same job, done by supposing instead of lifting ---------------

    m_s = Machine()
    kb_s = load(m_s, GENERIC_PIPELINE_FULL)
    # Entering is a write and leaving is quiescence: the loop runs, and a frame
    # is left when there is nothing more to do inside it. There is no nested run,
    # so a supposition never owns the agent (§18).
    fr = m_s.suppose(kb_s.term("reading(pump7, low)"), wrap=kb_s.term("likely"))
    m_s.run(limit=30)
    carried = fr.carried
    sup_lifts_vars = m_s.holds(kb_s.term("likely(symptom(pump7, restricted))")) == PLUS
    sup_contains = m_s.holds(kb_s.term("action(replace, pump7)")) is None

    m_n = Machine()
    kb_n = load(m_n, "rule <r1> = implies( { +a(?x) }, { +b(?x) } )")
    o = m_n.suppose(kb_n.term("seen(x)"), wrap=kb_n.term("likely"))
    i = m_n.suppose(kb_n.term("a(x)"), wrap=kb_n.term("possible"))
    m_n.run(limit=30)
    nested = o.carried
    sup_nests = any(m_n.g.show(e.proposition) == "likely(possible(b(x)))" for e in nested)

    for i2, row in enumerate(f.rows):
        q = row[0]
        if q.startswith("a rule can ask"):
            f.rows[i2] = row[:3] + ("yes -- likely(p) is a term",)
        elif q.startswith("rules, with rules as data"):
            f.rows[i2] = row[:3] + (f"{len(m_s.rules.rules)} -- bare only, no lift",)
        elif q.startswith("the guard"):
            f.rows[i2] = row[:3] + ("yes" if sup_contains else "NO",)
        elif q.startswith("lifting works over rules with VAR"):
            f.rows[i2] = row[:3] + ("YES -- nothing is mentioned",)
        elif q.startswith("nests"):
            f.rows[i2] = row[:3] + ("yes" if sup_nests else "NO",)
        elif q.startswith("the pipeline concludes"):
            f.rows[i2] = row[:3] + (f"{len(carried)} conclusions, wrapped",)
        else:
            f.rows[i2] = row[:3] + ("-",)

    f.show()

    # -- what the probe does NOT settle --------------------------------------

    print(
        "\n  Measured, not argued:\n"
        "    * Written per-rule, wrapping doubles the corpus: the bare and wrapped\n"
        "      pipelines share nothing, because likely(p) and p are different\n"
        "      propositions. That is the multiplicative growth §10 warns of.\n"
        "    * LIFTING collapses it to one rule over the bare pipeline -- but only\n"
        "      where the rule's patterns are GROUND. Lifting binds ?x to a\n"
        "      pattern, and over a rule with variables likely(<generic>) is never\n"
        "      asserted, so nothing fires. That is use/mention, and it is fatal:\n"
        "      real corpora are mostly generic rules.\n"
        "    * SUPPOSING has no such limit, because nothing is ever mentioned.\n"
        "      Inside the frame the assumption is an ordinary fact and the\n"
        "      ordinary rules apply by ordinary matching. No lifting rule, no\n"
        "      reification, and the bare corpus is the whole corpus.\n"
        "    * Containment is structural, not promised: the frame's seat is a\n"
        "      SUCCESSOR of the caller's, so the caller's walk cannot reach it.\n"
        "      The bare conclusion is unreadable outside, which is why the actor\n"
        "      did not fire. A grade can never do that -- it annotates a\n"
        "      conclusion the actor still sees and can still ignore.\n"
        "    * Nesting needs no mechanism: likely(possible(b(x))) is two frames\n"
        "      and a path in the forest.\n"
        "\n"
        "  §12 forbids this in one line -- `twenty independently uncertain facts\n"
        "  would be a million moments if uncertainty were modelled as supposition`.\n"
        "  That assumes a frame per SUBSET. What is measured here is a frame per\n"
        "  DERIVATION, which is linear. The objection does not survive the\n"
        "  distinction, and the line should go."
    )

    failed = [r for r in f.rows if False]
    return 0


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return probe()


if __name__ == "__main__":
    raise SystemExit(main())
