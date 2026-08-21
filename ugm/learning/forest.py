"""Can an ensemble VOTE, and can it hand its work back? (§3, §12, §17, §19)

machine.forest is a gated NEGATIVE result: bagging loses to one tree, because
_priority SUMS, and summation is not VOTING -- an over-general member fires
everywhere and no majority can overrule it. ⚠ And what the tool buys is not
accuracy -- it is the ability for a minority to LOSE.

See docs/design/forest.md.
"""

from typing import Dict, List, Optional, Sequence, Tuple

from ..core.machine import Machine
from ..core.text import Loader

# -- the world -------------------------------------------------------------
#
# A cathedral is its parts. Each property below is an ordinary relation a corpus
# could have written for any other reason, which is the point: the hypothesis
# space is the corpus's own vocabulary, exactly as `induce`'s tests are.
PROPS = ("pointed", "ribbed", "flying", "tracery",
         "round", "barrel", "thick", "apse")

GOTHIC, ROMAN = "gothic", "romanesque"

# ⚠⚠⚠ NO single property separates these, and the first version of this file
# had one that did.
# → docs/design/forest.md#no-single-property-separates-these-and-th
CATHEDRALS: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    ("chartres", ("pointed", "ribbed", "flying", "tracery", "apse"), GOTHIC),
    ("amiens",   ("pointed", "ribbed", "flying", "tracery"),         GOTHIC),
    ("wells",    ("pointed", "ribbed", "tracery", "thick"),          GOTHIC),
    ("laon",     ("pointed", "ribbed", "flying", "round", "apse"),   GOTHIC),
    ("durham",   ("pointed", "ribbed", "round", "thick", "apse"),    ROMAN),
    ("speyer",   ("round", "barrel", "thick", "apse"),               ROMAN),
    ("pisa",     ("round", "barrel", "thick"),                       ROMAN),
    ("vezelay",  ("round", "barrel", "thick", "apse"),               ROMAN),
)
# Held out of training entirely. `conques` is the case the whole comparison
# turns on: romanesque, but transitional -- it has pointed arches, so any tree
# that learned *pointed means gothic* is confidently wrong about it.
HELD_OUT: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    ("ely",     ("pointed", "ribbed", "tracery", "thick"),        GOTHIC),
    ("conques", ("pointed", "round", "barrel", "thick", "apse"),  ROMAN),
)

# ⭐ THE CONTROL, and it is this file's own first mistake kept on purpose. These
# are the same eight buildings with the transitional cases removed, so `pointed`
# separates the classes perfectly. Every member then agrees, and the question
# *what does voting buy* has a measurable answer: on this fixture, nothing.
CLEAN: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    ("chartres", ("pointed", "ribbed", "flying", "tracery", "apse"), GOTHIC),
    ("amiens",   ("pointed", "ribbed", "flying", "tracery"),         GOTHIC),
    ("wells",    ("pointed", "ribbed", "tracery", "apse"),           GOTHIC),
    ("laon",     ("pointed", "ribbed", "flying"),                    GOTHIC),
    ("durham",   ("round", "ribbed", "thick", "apse"),               ROMAN),
    ("speyer",   ("round", "barrel", "thick", "apse"),               ROMAN),
    ("pisa",     ("round", "barrel", "thick"),                       ROMAN),
    ("vezelay",  ("round", "barrel", "thick", "apse"),               ROMAN),
)
CLEAN_HELD: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    ("ely",     ("pointed", "ribbed", "tracery"),      GOTHIC),
    ("conques", ("round", "barrel", "thick", "apse"),  ROMAN),
)

SEED = 7
TREES = 5
# ⚠ Stated up front and not chosen afterwards: the comparison is run over every
# one of these and all of them are printed, because a claim about a combination
# rule that holds on one seed is a claim about that seed.
SEEDS = (1, 2, 3, 4, 5, 6, 7, 8)


# -- the learner -----------------------------------------------------------

def _rng(seed: int):
    """A stated generator, not the platform's. §3 wants the seed readable and
    the sequence reproducible; `random` gives neither across versions."""
    state = seed

    def nxt(n: int) -> int:
        nonlocal state
        state = (state * 1103515245 + 12345) % (1 << 31)
        # ⚠ The HIGH bits. An LCG's low bits have short periods -- taking
        # `state % n` gave every bag the same composition and therefore every
        # tree the same shape, which read exactly like a fixture with nothing
        # to disagree about.
        return (state >> 16) % n
    return nxt


def _bag(examples, nxt) -> List:
    return [examples[nxt(len(examples))] for _ in examples]


def _grow(examples, label: str, nxt=None, tries: int = 3) -> Tuple[str, ...]:
    """One tree: the conjunction of tests that best isolates `label`.

    Greedy and positive-only, and it stops when no test improves purity -- so a
    bag with nothing to separate returns the EMPTY conjunction, which matches
    everything. ⚠ Per-split FEATURE subsampling, and leaving it out is what
    made the first fixture unmeasurable.

    See docs/design/forest.md#grow.
    """
    conj: List[str] = []
    while True:
        here = [e for e in examples if _matches(tuple(conj), e[1])]
        pos = [e for e in here if e[2] == label]
        if not pos or len(pos) == len(here):
            break
        offer = set(PROPS)
        if nxt is not None:
            offer = {PROPS[nxt(len(PROPS))] for _ in range(tries)}
        best, best_score = None, None
        for p in PROPS:
            if p in conj or p not in offer:
                continue
            kept = [e for e in here if p in e[1]]
            if not kept:
                continue
            good = sum(1 for e in kept if e[2] == label)
            # Purity first, coverage as the tie-break -- the same *ties go to
            # the more general claim* that `induce` had to learn, and for the
            # same reason: a longer conjunction transfers less far.
            score = (good / len(kept), len(kept))
            if best_score is None or score > best_score:
                best, best_score = p, score
        if best is None or best_score[0] <= len(pos) / len(here):
            break
        conj.append(best)
    return tuple(conj)


def _matches(conj: Sequence[str], props: Sequence[str]) -> bool:
    return all(p in props for p in conj)


class Forest:
    """Trees over bootstrap samples, and a vote -- the whole model."""

    def __init__(self, examples=CATHEDRALS, seed: int = SEED, trees: int = TREES,
                 bag: bool = True):
        nxt = _rng(seed)
        self.seed, self.n = seed, trees
        ex = list(examples)
        # `bag=False` is the unanimity control: no resampling and no feature
        # subsampling, so every member is the SAME tree. An ensemble that cannot
        # disagree is the only way to ask what the disagreement was worth.
        self.trees: List[Tuple[str, ...]] = [
            _grow(_bag(ex, nxt) if bag else ex, GOTHIC, nxt if bag else None)
            for _ in range(trees)]
        self.roman: List[Tuple[str, ...]] = [
            _grow(_bag(ex, nxt) if bag else ex, ROMAN, nxt if bag else None)
            for _ in range(trees)]

    def votes(self, props) -> Tuple[int, int]:
        return (sum(1 for t in self.trees if _matches(t, props)),
                sum(1 for t in self.roman if _matches(t, props)))

    def deciding(self, props, concept: str = GOTHIC) -> Optional[Tuple[str, ...]]:
        """The path a majority of the voting trees agreed on -- what gets
        rendered back as a rule. The MOST SPECIFIC among the trees that fired,
        because a shorter one is a weaker claim and would over-generalise the
        moment it left the forest."""
        fired = [t for t in (self.trees if concept == GOTHIC else self.roman)
                 if _matches(t, props)]
        return max(fired, key=len) if fired else None


def render(conj: Sequence[str], concept: str, name: str) -> List[str]:
    """A conjunction, as an ordinary rule a corpus could have been written with.

    Each test gets its own part variable and they all join on `?c`, which is what
    makes it a claim about a KIND of cathedral. The consequent binds `?c` from
    the antecedent, so the loader's rule is satisfied -- the freedom `induce` had
    for free (a `prefer` consequent holds no variables) has to be earned here,
    and this is what earning it looks like.
    """
    tests = ["+cathedral(?c)"]
    for i, p in enumerate(conj):
        tests += [f"+part(?c, ?p{i})", f"+{p}(?p{i})"]
    return [f"rule <{name}> = implies( {{ {', '.join(tests)} }},"
            f" {{ +{concept}(?c) }} )", f"fact standing(<{name}>)"]


# -- the corpus ------------------------------------------------------------

def facts_for(examples) -> List[str]:
    out = []
    for name, props, _ in examples:
        out.append(f"fact +cathedral({name})")
        for p in props:
            out.append(f"fact +part({name}, {name}_{p})")
            out.append(f"fact +{p}({name}_{p})")
    return out


ASK = "rule <ask> = implies( { +cathedral(?c) }, { +classify(?c) } )"
# The corpus's WRAPPER, mapped from the count -- rows, not branches, and the whole
# of what *the corpus governs, not the tool's confidence* means when the
# tool has a real number to report. Nothing here is arithmetic: five trees make
# six sayable counts and each is a line.
TRUST = [
    "rule <g5> = implies( { +answered(<forest>, classify(?c), gothic(5)) },"
    " { +certain(is_gothic(?c)) } )",
    "rule <g4> = implies( { +answered(<forest>, classify(?c), gothic(4)) },"
    " { +likely(is_gothic(?c)) } )",
    "rule <g3> = implies( { +answered(<forest>, classify(?c), gothic(3)) },"
    " { +possible(is_gothic(?c)) } )",
    "rule <r0> = implies( { +answered(<forest>, classify(?c), gothic(0)) },"
    " { +certain(is_romanesque(?c)) } )",
    "rule <r1> = implies( { +answered(<forest>, classify(?c), gothic(1)) },"
    " { +likely(is_romanesque(?c)) } )",
    "rule <r2> = implies( { +answered(<forest>, classify(?c), gothic(2)) },"
    " { +possible(is_romanesque(?c)) } )",
]
SEED_FACT = f"fact +seeded(<forest>, {SEED})"


def classify(examples, model: Optional[Forest] = None, rules: Sequence[str] = (),
             retire: bool = False, extra: Sequence[str] = ()):
    """One run. The forest answers `classify`, or is retired and does not."""
    m = Machine()
    m.actuator("hands")
    kb = Loader(m)
    props = {name: set(p) for name, p, _ in examples}
    asked: List[str] = []

    def answerer(mach, e):
        who = mach.g.show(mach.g.member(e.proposition, 0))
        asked.append(who)
        g, _r = (model or Forest()).votes(props.get(who, set()))
        return kb.term(f"gothic({g})")

    kb.answerer("forest", "classify", answerer)
    src = facts_for(examples) + [ASK, SEED_FACT] + list(TRUST) + list(rules)
    if retire:
        src.append("fact -answers(<forest>, classify)")
    kb.load("\n".join(src + list(extra) + [""]))
    m.run(limit=8000)
    return m, kb, asked


def verdicts(m, kb, examples) -> Dict[str, str]:
    """What the agent ended up believing about each cathedral, and how surely.

    ⚠ BOTH concepts are read and both are reported. An earlier version kept only
    the last one it found, which quietly turned the rules-as-ensemble's real
    failure -- asserting gothic AND romanesque about one building -- into a
    tidy single verdict. A contradiction is a result; hiding it is not.
    """
    # ⚠ The verdict is WRAPPED, where it used to be a bare claim with a grade
    # on the entry. Grades are gone: how sure the corpus is about the tool's
    # count is said in the conclusion -- `likely(is_gothic(x))` -- which is a
    # proposition a rule can read and an entry's field never was.
    out = {}
    for name, _, _ in examples:
        held = []
        for concept in ("is_gothic", "is_romanesque"):
            # ⚠ Bare AND wrapped, because the two encodings say it differently:
            # a rules-as-ensemble member concludes `is_gothic(?c)` flat, and the
            # tool's corpus concludes `likely(is_gothic(?c))`. An unqualified
            # claim is the strongest thing a corpus can say, so it reads as
            # `certain` -- which is what its entry's grade used to be by
            # default, before there were grades.
            for term, label in (
                [(f"{concept}({name})", "certain")]
                + [(f"{w}({concept}({name}))", w)
                   for w in ("certain", "likely", "possible")]
            ):
                e = m.chain.resolve(kb.term(term))
                if e is not None and e.sign == "+":
                    held.append(f"{concept[3:]}/{label}")
                    break
        out[name] = " AND ".join(held) if held else "-"
    return out


def correct(v: Dict[str, str], examples) -> int:
    """How many were classified right -- and a building called both is called
    neither, because an agent that asserts both has not answered."""
    return sum(1 for n, _, truth in examples
               if v.get(n, "-").startswith(truth[:6]) and " AND " not in v.get(n, ""))


def as_rules(model: Forest) -> List[str]:
    """The same ensemble, loaded as rules -- every member concluding directly."""
    out: List[str] = []
    for i, t in enumerate(model.trees):
        out += render(t, "is_gothic", f"g-tree-{i}")
    for i, t in enumerate(model.roman):
        out += render(t, "is_romanesque", f"r-tree-{i}")
    return out


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing, ran = 0, 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__.strip().split("\n")[0])
    print()

    model = Forest()
    print(f"  five trees for `gothic`, bagged on seed {SEED}:")
    for t in model.trees:
        print(f"    {' & '.join(t) if t else '(empty -- matches everything)'}")
    print()
    # ⚠ Not *is there an empty tree* -- that was the first version of this check
    # and it was measuring the wrong thing. Seeds 4, 5 and 18 grow no empty tree
    # and the rules still fail, because what breaks them is a member that fires
    # on the WRONG CLASS, of which an empty tree is only the extreme case.
    con = dict((n, set(p)) for n, p, _ in HELD_OUT)["conques"]
    misfiring = [t for t in model.trees if _matches(t, con)]
    print(f"  members that fire on the held-out ROMANESQUE: {len(misfiring)}/{TREES}")
    print()
    gate("⚠ some member is wrong about the transitional building, or there is "
         "no disagreement here to resolve", bool(misfiring))
    gate("...and it is a MINORITY, which is the only circumstance in which a "
         "vote and an accumulation can differ",
         len(misfiring) < TREES / 2)

    # -- rules accumulate; a function votes --------------------------------
    print("The SAME five trees, combined two ways, on two held-out cathedrals:\n")
    rows = as_rules(model)
    m_rules, kb_rules, _ = classify(HELD_OUT, model, rules=rows, retire=True)
    m_tool, kb_tool, asked = classify(HELD_OUT, model)
    rule_v = verdicts(m_rules, kb_rules, HELD_OUT)
    tool_v = verdicts(m_tool, kb_tool, HELD_OUT)
    print(f"  {'held out':<9} {'truth':<11} {'as RULES':<34} as a TOOL")
    for name, props, truth in HELD_OUT:
        g, _r = model.votes(set(props))
        print(f"  {name:<9} {truth:<11} {rule_v.get(name, '-'):<34} "
              f"{tool_v.get(name, '-')}  ({g}/{TREES})")
    print()
    gate("⭐⭐⭐ loaded as RULES the ensemble asserts BOTH about the transitional "
         "one -- an over-general member has concluded, and a majority has no "
         "way to un-conclude it", " AND " in rule_v.get("conques", ""))
    gate("⭐⭐⭐ ...and the SAME trees as a tool answer it, because the vote "
         "happens inside the answerer",
         tool_v.get("conques", "").startswith("romanesque"))
    gate("...and it is not that the tool says romanesque to everything: the "
         "held-out gothic is still gothic",
         tool_v.get("ely", "").startswith("gothic"))
    gate("neither example was trained on", not any(
        h[0] == c[0] for h in HELD_OUT for c in CATHEDRALS))

    # ⚠ One seed is an anecdote. The claim is about the COMBINATION RULE, so it
    # is measured over seeds -- and reported even where the tool wins nothing.
    print("\n  the same comparison across seeds, both held-out right out of 2:\n")
    print(f"    {'seed':<6} {'as RULES':<10} as a TOOL")
    sweep = []
    for seed in SEEDS:
        mdl = Forest(seed=seed)
        mr, kr, _ = classify(HELD_OUT, mdl, rules=as_rules(mdl), retire=True)
        mt, kt, _ = classify(HELD_OUT, mdl)
        a = correct(verdicts(mr, kr, HELD_OUT), HELD_OUT)
        b = correct(verdicts(mt, kt, HELD_OUT), HELD_OUT)
        sweep.append((seed, a, b))
        print(f"    {seed:<6} {a:<10} {b}")
    print()
    gate("⭐⭐⭐ voting is never WORSE than accumulating, on any seed",
         all(b >= a for _, a, b in sweep))
    gate("⭐⭐ ...and strictly better on EVERY one of them, so the single seed "
         "above is not the finding",
         all(b > a for _, a, b in sweep))

    # -- was it the OVERLAP?
    # → docs/design/forest.md#was-it-the-overlap-measured-and-the-answer
    print("\n  was it the class OVERLAP? the separable fixture says no:\n")
    print(f"    {'seed':<6} {'as RULES':<10} as a TOOL")
    clean = []
    for seed in SEEDS:
        mdl = Forest(CLEAN, seed=seed)
        mr, kr, _ = classify(CLEAN_HELD, mdl, rules=as_rules(mdl), retire=True)
        mt, kt, _ = classify(CLEAN_HELD, mdl)
        a = correct(verdicts(mr, kr, CLEAN_HELD), CLEAN_HELD)
        b = correct(verdicts(mt, kt, CLEAN_HELD), CLEAN_HELD)
        clean.append((seed, a, b))
        print(f"    {seed:<6} {a:<10} {b}")
    print()
    gate("⚠⚠⚠ separability does NOT save the rules encoding -- a degenerate bag "
         "grows an over-general member out of clean data, so the failure is "
         "bagging's and not the fixture's",
         all(b >= a for _, a, b in clean) and any(b > a for _, a, b in clean))

    # -- the control that isolates it ---------------------------------------
    print("\n  the CONTROL -- an ensemble that CANNOT disagree (no bagging, no\n"
          "  feature subsampling, so all five members are one tree):\n")
    print(f"    {'seed':<6} {'members':<26} {'as RULES':<10} as a TOOL")
    same = []
    for seed in SEEDS[:3]:
        mdl = Forest(seed=seed, bag=False)
        mr, kr, _ = classify(HELD_OUT, mdl, rules=as_rules(mdl), retire=True)
        mt, kt, _ = classify(HELD_OUT, mdl)
        a = correct(verdicts(mr, kr, HELD_OUT), HELD_OUT)
        b = correct(verdicts(mt, kt, HELD_OUT), HELD_OUT)
        same.append((a, b))
        one = " & ".join(mdl.trees[0]) or "(empty)"
        print(f"    {seed:<6} {('5x ' + one):<26} {a:<10} {b}")
    print()
    gate("⭐⭐⭐ with nothing to disagree about, voting and accumulating are the "
         "SAME -- so the win above is a minority being outvoted, not a tool "
         "being used", all(a == b for a, b in same))
    gate("...and the control is not vacuous: the unanimous ensemble is right "
         "about something, so a tie at zero is not what is being read",
         all(b > 0 for _, b in same))

    # -- the grade is the corpus's, and the count is the tool's -------------
    print("Every cathedral, and how sure the CORPUS made the count:\n")
    m_all, kb_all, asked_all = classify(list(CATHEDRALS) + list(HELD_OUT), model)
    v = verdicts(m_all, kb_all, list(CATHEDRALS) + list(HELD_OUT))
    for name, props, truth in list(CATHEDRALS) + list(HELD_OUT):
        g, r = model.votes(set(props))
        print(f"  {name:<10} {truth:<12} {v.get(name, '-'):<24} gothic({g})")
    print()
    graded = {x.split("/")[1] for x in v.values() if "/" in x}
    gate("⭐⭐ the tool reports a COUNT and the corpus decides how sure that "
         "makes it -- more than one wrapper is reached, so the mapping is live",
         len(graded) > 1)
    pisa_g, _ = model.votes(set(dict((n, p) for n, p, _ in CATHEDRALS)["pisa"]))
    gate("the answer is a RECORD before it is a claim",
         m_all.holds(kb_all.term(
             f"answered(<forest>, classify(pisa), gothic({pisa_g}))")) == "+")
    gate("the binding is a fact a corpus can ask about, and the SEED is on the "
         "record (§3)",
         m_all.holds(kb_all.term("answers(<forest>, classify)")) == "+"
         and m_all.holds(kb_all.term(f"seeded(<forest>, {SEED})")) == "+")

    every = {n for n, _, _ in list(CATHEDRALS) + list(HELD_OUT)}
    gate("every cathedral got a verdict, so nothing is passing by declining",
         set(v) == every)
    gate("⭐ and the verdicts are right", all(
        v[n].startswith(truth[:6]) for n, _, truth in
        list(CATHEDRALS) + list(HELD_OUT)))

    # -- the forest hands its work back ------------------------------------
    print("\nThe deciding path, rendered as a rule, with the forest RETIRED:\n")
    path = model.deciding(set(dict((n, p) for n, p, _ in HELD_OUT)["ely"]))
    distilled = render(path, "is_gothic", "distilled")
    for r in distilled:
        print(f"    {r}")
    m_d, kb_d, asked_d = classify(HELD_OUT, model, rules=distilled, retire=True)
    dv = verdicts(m_d, kb_d, HELD_OUT)
    print()
    print(f"    forest called: {asked_d or 'never'}   verdict: {dv.get('ely', '-')}")
    print()
    gate("⭐⭐⭐ the rendered path reproduces the forest's verdict WITHOUT the "
         "forest -- the model hands its work to the engine and leaves",
         dv.get("ely", "").startswith("gothic"))
    gate("...and the forest really was retired, not merely unused",
         not asked_d)
    gate("⚠ and it is the DECIDING path that carries it: the empty member "
         "would have said gothic about everything",
         bool(path) and not _matches(path, dict(
             (n, p) for n, p, _ in HELD_OUT)["conques"]))

    # -- one credit walk ----------------------------------------------------
    print("\nA misclassification that costs a goal:\n")
    TREAT = [
        # ⚠⚠ What this corpus is willing to act on, in two lines.
        # → docs/design/forest.md#what-this-corpus-is-willing-to-act-on-in-t
        "rule <believe> = implies( { +certain(?p) }, { +?p } )",
        "rule <believe-maybe> = implies( { +possible(?p) }, { +?p } )",
        "rule <treat> = implies( { +is_gothic(?c), +restoring(?c) },"
        " { +doing(repoint(?c)) } )",
        "rule <spoil> = implies( { +did(repoint(?c)), +part(?c, ?p), +barrel(?p) },"
        " { -intact(?c) } )",
        "fact +restoring(conques)", "fact +intact(conques)",
        "fact +goal(intact(conques))",
    ]
    m_b, kb_b, _ = classify(HELD_OUT, model, rules=rows, retire=True,
                            extra=TREAT)
    blamed_rules = sorted({r.name for r, _ in m_b.blame()})
    m_t, kb_t, _ = classify(HELD_OUT, model, extra=TREAT)
    blamed_tool = sorted({r.name for r, _ in m_t.blame()})
    print(f"  {'ensemble as rules':<20} lost intact? "
          f"{m_b.holds(kb_b.term('intact(conques)')) == '-'}   blamed {blamed_rules}")
    print(f"  {'ensemble as a tool':<20} lost intact? "
          f"{m_t.holds(kb_t.term('intact(conques)')) == '-'}   blamed {blamed_tool}")
    print()
    gate("⭐⭐ the wrong verdict really costs something, so there is something "
         "to blame", m_b.holds(kb_b.term("intact(conques)")) == "-")
    gate("⭐ blame reaches the guilty MEMBER by name, not merely the ensemble",
         any(n.startswith("g-tree-") for n in blamed_rules))
    gate("⭐⭐⭐ ...and when the ensemble IS a tool the vote avoids the damage "
         "altogether -- the safety property is the same one as the accuracy",
         m_t.holds(kb_t.term("intact(conques)")) != "-")

    # ⚠ The gate above cannot show that blame reaches the TOOL, because on this
    # seed the tool is right and a tool that is right is not blamed. So: a seed
    # where the vote itself goes wrong.
    wrong = Forest(seed=3)
    m_w, kb_w, _ = classify(HELD_OUT, wrong, extra=TREAT)
    blamed_w = sorted({r.name for r, _ in m_w.blame()})
    print(f"  {'a seed where the VOTE is wrong':<20} lost intact? "
          f"{m_w.holds(kb_w.term('intact(conques)')) == '-'}   blamed {blamed_w}")
    print()
    gate("⭐⭐⭐ one credit walk reaches rules and tools alike: when the forest's "
         "own answer costs a goal, `blame` names <forest>",
         "forest" in blamed_w)
    gate("...so the tool is not privileged -- being a model buys no exemption "
         "from the walk that supervises every rule",
         m_w.holds(kb_w.term("intact(conques)")) == "-")

    print(f"\n{ran} checks, {failing} failing")
    print("""
  ⭐⭐⭐ RULES ACCUMULATE; ONLY A FUNCTION CAN TAKE A VOTE. `machine.forest`
  files bagging as a measured failure and blames `_priority` for summing. The
  sharper statement is that combining ensemble members AS RULES cannot be
  voting at all, whatever the arithmetic: a rule that applies has concluded,
  and a majority has no way to un-conclude it. Move the combination inside an
  answerer -- which `ugm.tools` already made a first-class, deniable, blameable
  thing -- and the same five trees are right about the example the same five
  rules are wrong about. Nothing was added to the engine.

  ⭐⭐⭐ AND THE MODEL CAN LEAVE. A tool's price, stated in `ugm.tools`, is that
  §12's weakest link gets a link with nothing behind it. A forest is the model
  class that can pay: a root-to-leaf path IS a rule, so the deciding path
  renders as corpus text, and with the forest RETIRED the rules reproduce its
  verdict. That is the ML seam running in the direction nobody builds it --
  the model shrinking as the corpus learns.

  ⚠⚠⚠ AND IT IS NOT THE CLASS OVERLAP -- a section written to confirm that
  refuted it instead. The separable fixture, where `pointed` sorts the two
  kinds perfectly, still breaks the rules encoding: a bag that happens to draw
  one class grows an EMPTY tree, which fires on everything. **Bagging
  manufactures the over-general member by itself**, so the failure follows the
  ensembling method rather than the data. The control that does isolate it is
  an ensemble that cannot disagree -- no resampling, no feature subsampling,
  five copies of one tree -- and there voting and accumulating tie exactly.

  > **What the tool buys is not accuracy. It is the ability for a minority to
  > LOSE.**

  ⚠ WHAT IS NOT SHOWN. Nothing here distils automatically or decides WHICH
  paths are settled enough to hand over; the gate renders one path chosen by a
  test. The obvious policy -- hand over what the trees are unanimous about,
  keep the residue -- is untried, and it is the same *agreement is invisible,
  disagreement is the signal* that `machine.forest`'s note arrives at from the
  other side.

  ⚠ AND THE FEATURE SUBSAMPLING WAS LOAD-BEARING, which was not expected.
  Bagging the rows alone left every tree identical, because one property here
  is perfectly pure and won every split of every bag. Withholding features per
  split is what produced an ensemble with anything to disagree about -- so the
  *random* in random forest is not a detail of the training loop here, it is
  the thing the whole comparison measures.

  ⚠ POSITIVE TESTS ONLY (§9), so the two classes are two concepts and not a
  predicate and its complement. That is a representation decision the fixture
  cannot argue with, and it has a cost: a path can only ever say what a
  cathedral HAS. `round` is what distinguishes conques, and the tree can use it
  because somebody wrote it down -- in a corpus that named only gothic
  features, romanesque would be unlearnable and nothing here would say so.

  ⚠ AND THE LABELS ARE AUTHORED. This is supervised, the eight training
  examples are hand-labelled, and no part of this discovers that there are two
  styles. That gap is unchanged.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
