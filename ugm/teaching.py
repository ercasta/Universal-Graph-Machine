"""Bootstrapping the table from use. (the author's design)

    python -m ugm.teaching

> A human is the first, manual user of the KB.

Not a labelling task run beside the system: the ordinary first use of a corpus,
by a person who steps it and picks the next rule. They are doing exactly what
the table will later do, so what they leave behind is the table. The learning is
the residue of the use, which is this repo's recurring shape.

Two signals come out of that use and only one of them is calibration:

    the wrong order        a buff -- this rule should have come first here
    none of these fits     a MISSING RULE, which no calibration can supply

The second is the more valuable one early, and only manual use surfaces it. This
file is about the first.

## Why there is a teacher here that is not a human

The reflex experiment in `ugm.attention` settled what a demonstration may
produce: damping every rule that was tried and missed cost 125 conclusions,
because *tried and missed* is not evidence a rule is unimportant -- it is
evidence it did not apply **in that state**. So a demonstration has to produce
something conditional, and the smallest conditional thing that carries a
sequence is a bigram on the rule that just applied:

    rule <A> = ...
      after => boost(<R>, n)          after A, prefer R

...with a query added later, by anti-unification, when the same `A` is taught
towards different `R` in different situations.

**And the mechanism can be validated with no human at all.** The shipped loop's
arbitration already picks a move at every step, deterministically, over the full
option set. Let it teach; then ask whether the table loop, calibrated from its
sequence, makes the same moves it does. If bootstrapping cannot imitate a
teacher that is right by construction, it will not learn from a person either.

Three things are measured, and they are the three claims:

    agreement    does the table pick what the teacher picked
    matched/move does the cost claim move (29.6 uncalibrated)
    conclusions  does anything get lost
"""

import os
from typing import Dict, List, Optional, Tuple

from .attention import (
    SETTLE, Table, _fight, _load, _state, run,
)
from .graph import NodeId
from .machine import Machine
from .chain import PLUS
from .rules import (Application, Member, Situation, arbitrate,
                    generalise, unify)
from .text import ParseError, load, load_file


def teacher(m: Machine, table: Table, window, state: Situation):
    """The shipped arbitration, as a gold teacher.

    It chooses over the FULL option set -- `_materialise` is the slow definition
    `ugm.arbitration` holds the fast one to -- rather than over the window, so
    it is a genuine teacher and not a re-ranking of what the table already
    liked. Offline cost, which is what a teacher is allowed.
    """
    everything = m._materialise(m.rules.rules, state)
    if not everything:
        return window[0] if window else None
    keys = m._in_play()
    chosen = arbitrate(m.rules, everything, lambda r: m._rank(r, keys))
    return chosen or (window[0] if window else None)


class Lesson:
    """What the use left behind: which rule was picked after which, and what
    made the picked rule applicable at the time."""

    def __init__(self) -> None:
        self.pairs: Dict[Tuple[str, str], int] = {}
        # One example per demonstration: the propositions the chosen rule
        # CONSUMED, with the previous rule's own bindings folded back in. Not
        # the whole state -- the state is enormous and mostly irrelevant, and
        # the premises are precisely the reason the move was available.
        self.examples: Dict[Tuple[str, str], List[Tuple]] = {}
        # ...and the same demonstrations keyed on the RULE ALONE, unanchored.
        # A lesson keyed on a predecessor fires on the move after that
        # predecessor and never otherwise, so most moves have nothing lifted
        # and the scan pays for the whole pool. Keyed on the situation it fires
        # whenever the situation arises, which is what experience is.
        self.occasions: Dict[str, List[Tuple]] = {}
        self.agreed = 0
        self.moves = 0
        self.last: Optional[str] = None
        self.last_bindings: Dict = {}
        self.last_example: Optional[Tuple] = None

    def watching(self, m: Machine, table: Table, window, chosen, tick: int):
        self.moves += 1
        # By RULE, not by application identity: the teacher builds its own
        # `Application` objects from `_materialise`, so `is` compares two
        # objects that describe the same move and answers no every time. It
        # reported 0/149 before this was fixed, which reads as *the table is
        # never right* and meant *the comparison cannot be right*.
        if window and chosen.rule is window[0].rule:
            self.agreed += 1
        name = chosen.rule.name or "?"
        if self.last is not None:
            key = (self.last, name)
            self.pairs[key] = self.pairs.get(key, 0) + 1
            # Anchored to the PREVIOUS rule's bindings: an individual the last
            # move was about becomes that move's own variable, so the query
            # says *this orc* rather than *some orc*. §14's one-mapping rule,
            # one level up -- a query and the rule it hangs off must share
            # variables or the postcondition is about nothing in particular.
            back = {v: k for k, v in self.last_bindings.items()}
            self.examples.setdefault(key, []).append(tuple(
                _anchor(m, e.proposition, back) for e in chosen.consumed
            ))
        # THE RULE'S OWN SITUATION -- what made this move available -- and the
        # keying went round a full circle to get back here. As a learned RULE a
        # recogniser keyed this way can never fire in time, because by the time
        # its query holds the target is already applicable; that is why it was
        # moved to the precursor, the state one move earlier. As a RERANKER the
        # objection is gone: it is consulted while the shortlist is being
        # ordered, which is exactly when the target is applicable.
        #
        # And the precursor turned out to be unusable here for a reason worth
        # keeping: a player's moves are separated by bookkeeping -- settling a
        # doubt, recording an act -- so the previous move's premises share
        # nothing across 15 demonstrations and generalise to nothing at all.
        # A pipeline has stable precursors; a decision does not.
        #
        # As TEXT, from the start: experience comes from several fights, a fight
        # is its own machine, and a node id from one means nothing in another.
        # The utterance is what crosses (`ugm/table.py`), here at the moment the
        # example is taken rather than at the end.
        self.occasions.setdefault(name, []).append(
            tuple(_say(m, e.proposition) for e in chosen.consumed))
        self.last = name
        self.last_bindings = dict(chosen.bindings)

    # -- what a demonstration becomes -------------------------------------

    def lessons(self, m: Machine, conditional: bool = True) -> dict:
        """What was learned, as TEXT.

        A node id means nothing outside the graph that minted it, and the
        lesson is learned on the teacher's machine and applied on the student's
        -- so what crosses is an **utterance**, rendered here and re-read in the
        receiver's own name scope. That is this repo's own rule for what may
        cross between machines (`ugm/table.py`), arriving from the learning
        side, and it makes a lesson a document: savable, diffable, arguable,
        and loadable into a corpus that was never taught.

        The whole query is rendered as ONE term, because `Loader.term` gives
        each call a fresh scope -- two members parsed separately would not
        share `?g0`, and a query whose variables do not co-refer is a different
        and much weaker claim.
        """
        out = {"posts": {}, "declined": 0, "collided": 0}
        for (first, then), seen in self.pairs.items():
            if first == then:
                continue
            text = ""
            if conditional:
                query = _query(m, self.examples.get((first, then), []))
                if not query:
                    # It generalised to nothing that says anything. Emitting an
                    # unconditional buff instead is exactly the failure already
                    # measured twice, so the lesson is declined.
                    out["declined"] += 1
                    continue
                if _collides(m, query, self.examples, first, then):
                    # The query also holds where the teacher chose otherwise
                    # after the same rule, so it is too general to be a reason.
                    out["collided"] += 1
                    continue
                text = "q(" + ", ".join(m.g.show(x.pattern) for x in query) + ")"
            out["posts"][(first, then)] = (text, 3 * min(seen, 3))
        return out


    def recognisers(self, m: Machine, ldr) -> dict:
        """The demonstrations keyed on the situation: for each rule taught,
        what the situations it was taught in have in common.

        The example is the same one -- what made the move available -- but
        UNANCHORED, because there is no predecessor to anchor to and that is the
        point: the query binds its own variables, so it holds whenever a
        situation of that shape arises.
        """
        out = {"rules": {}, "declined": 0, "unspeakable": 0}
        for name, examples in self.occasions.items():
            read = []
            for ex in examples:
                if not ex:
                    continue
                try:
                    # One term per example, so its own variables co-refer and
                    # two examples share nothing by accident.
                    whole = ldr.term("q(" + ", ".join(ex) + ")")
                except ParseError:
                    out["unspeakable"] += 1
                    continue
                read.append(tuple(m.g.members(whole)))
            if len(read) < 2:
                # One example generalises to itself, which is a query about one
                # goblin. Two is the least that can say anything general, and
                # `generalise` decides what they share.
                out["declined"] += 1
                continue
            query = _query(m, read)
            if not query:
                out["declined"] += 1
                continue
            out["rules"][name] = (
                "q(" + ", ".join(m.g.show(x.pattern) for x in query) + ")",
                3 * min(len(read), 3),
            )
        return out


def install_recognisers(m: Machine, ldr, learned: dict) -> int:
    """The situation-keyed lessons, as RERANKERS.

    They were learned rules first -- `<when-N>` concluding `noticing(<R>)` --
    and that failed for a structural reason worth keeping: in a one-move-per-
    tick loop a rule that recognises a situation has to WIN A MOVE to be heard,
    and it never does (2 firings out of 16 installed). A ranking-time trigger is
    heard without winning anything, costs no move, and adds nothing to the pool.
    """
    by_name = {r.name: r for r in m.rules.rules if r.name}
    added = 0
    for name, (text, weight) in sorted(learned["rules"].items()):
        if by_name.get(name) is None:
            continue
        try:
            whole = ldr.term(text)
        except ParseError:
            learned["unspeakable"] = learned.get("unspeakable", 0) + 1
            continue
        members = ", ".join("+" + m.g.show(x) for x in m.g.members(whole))
        try:
            ldr.load(WHEN % (members, name, weight))
        except ParseError:
            learned["unspeakable"] = learned.get("unspeakable", 0) + 1
            continue
        added += 1
    return added


def install(m: Machine, ldr, lessons: dict) -> int:
    """Read the lessons back in the student's own scope, as trigger documents.

    Nothing is written into a rule: what a rule MEANS and when it is worth
    reaching for are different claims, and they now live in different
    statements. A corpus loads its experience or does not.
    """
    added = 0
    for (first, then), (text, weight) in lessons["posts"].items():
        names = {r.name for r in m.rules.rules if r.name}
        if first not in names or then not in names:
            continue
        query = ""
        if text:
            try:
                whole = ldr.term(text)
            except ParseError:
                # The lesson cannot be WRITTEN DOWN. A sign atom renders as `+`
                # and `+` opens a member, so a premise that mentions one is a
                # fact the graph holds and the surface cannot say. Counted
                # rather than worked around: a calibration nobody can read
                # cannot be argued with or frozen, which is why it belongs in
                # the corpus in the first place.
                lessons["unspeakable"] = lessons.get("unspeakable", 0) + 1
                continue
            query = " { %s } " % ", ".join(
                "+" + m.g.show(x) for x in m.g.members(whole))
        try:
            ldr.load(AFTER % (first, query or " ", then, weight))
        except ParseError:
            lessons["unspeakable"] = lessons.get("unspeakable", 0) + 1
            continue
        added += 1
    return added


def _say(m: Machine, node: NodeId) -> str:
    """Render a proposition so the surface can read it back.

    `Graph.show` writes a sign atom as `+`, and `+` opens a member -- so every
    example mentioning `says(dm, ..., +)` was unsayable, which is every example
    a player has, because a player acts on what it was told. Measured before
    this: 86 lessons declined as unwritable and not one of them about a rule the
    corpus author wrote.

    The parser already accepts `plus`, `minus` and `unsure` in argument
    position; only the renderer had no way to say them. So this is a rendering
    fix rather than a new notation, which is the honest kind: the graph could
    always hold it and the surface could always read it.
    """
    signs = {m.rules.SIGN[s]: name
             for s, name in (("+", "plus"), ("-", "minus"), ("?", "unsure"))}
    if node in signs:
        return signs[node]
    members = m.g.members(node)
    if not members:
        return m.g.show(node)
    rel = m.g.relation_of(node)
    return "%s(%s)" % (_say(m, rel) if rel is not None else "?",
                       ", ".join(_say(m, x) for x in members))


def _anchor(m: Machine, prop: NodeId, back: Dict) -> NodeId:
    """Replace anything the previous move bound with the variable it bound it
    to. Recursive, because an individual may sit inside a structure."""
    if prop in back:
        return back[prop]
    members = m.g.members(prop)
    if not members:
        return prop
    rel = m.g.relation_of(prop)
    return m.g.rel(back.get(rel, rel), *[_anchor(m, x, back) for x in members])


def _query(m: Machine, examples: List[Tuple]):
    """Anti-unify the examples into a query, or answer nothing.

    Aligned by relation: a relation that appears exactly once in every example
    is generalised across them; anything else is dropped rather than guessed at.
    ONE mapping across every member, which is `generalise`'s own rule -- the
    same disagreement must give the same variable everywhere, or the query is
    strictly more general than the answer and fires on everything.
    """
    if not examples:
        return ()
    by_rel: List[Dict[NodeId, NodeId]] = []
    for ex in examples:
        seen: Dict[NodeId, List[NodeId]] = {}
        for p in ex:
            seen.setdefault(m.g.relation_of(p), []).append(p)
        by_rel.append({k: v[0] for k, v in seen.items() if len(v) == 1})
    shared = set(by_rel[0])
    for d in by_rel[1:]:
        shared &= set(d)
    mapping: Dict = {}
    out = []
    for rel in sorted(shared):
        lgg = by_rel[0][rel]
        for d in by_rel[1:]:
            lgg = generalise(m.g, lgg, d[rel], mapping)
        if m.g.is_var(lgg):
            continue  # a bare variable is true of everything and says nothing
        out.append(Member(PLUS, lgg, None, None))
    return tuple(out)


def _collides(m: Machine, query, examples, first: str, then: str) -> bool:
    """Does this query also hold where the same rule was followed by a
    DIFFERENT one? The negatives are free -- the teacher's own run recorded
    them -- and a reason that is equally true of the alternative is not one."""
    for (a, b), other in examples.items():
        if a != first or b == then:
            continue
        for ex in other:
            if all(any(unify(m.g, mem.pattern, p, {}) is not None for p in ex)
                   for mem in query):
                return True
    return False
EXTRA_SEEDS = (11, 13, 17)

# The two trigger forms, as text: a lesson is a document.
WHEN = "when { %s } => boost(<%s>, %d)" + chr(10)
AFTER = "after <%s>%s => boost(<%s>, %d)" + chr(10)


def _agree(mine: List[str], theirs: List[str]) -> int:
    """How much of the teacher's sequence the student reproduced, as the
    longest common subsequence.

    ⚠ Positional comparison is wrong here and reported 5 of 149 before this,
    which would have read as *situation-keyed lessons destroy the behaviour*
    and meant *the comparison cannot see them*. A learned recogniser and a
    settled doubt are moves the teacher never made; they SHIFT everything after
    them, so a positional check counts one insertion as a hundred
    disagreements. The bookkeeping moves are dropped and the rest is aligned.
    """
    skip = lambda xs: [x for x in xs
                       if not x.startswith("when-") and x != "settle-doubt"]
    a, b = skip(mine), skip(theirs)
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(cur[j], prev[j + 1]))
        prev = cur
    return prev[-1]


def _machine(name: str):
    """A fresh machine and the loader that is its name scope -- a lesson is
    re-read through it, since a bare name outside a scope names nothing."""
    if name == "dungeon":
        from . import dungeon
        m, ldr, _asked = dungeon.fight(seed=7, limit=0)
    else:
        m = Machine()
        ldr = load_file(m, os.path.join(
            os.path.dirname(__file__), "rules", name))
    load(m, SETTLE)
    return m, ldr


def measure(name: str, limit: int = 400) -> dict:
    """One teacher run gives both the lesson and the target; then the table
    loop runs twice, uncalibrated and calibrated, against it."""
    gold_m, gold_ldr = _machine(name)
    lesson = Lesson()
    gold = run(gold_m, limit=limit, chooser=teacher, watch=lesson.watching)
    # ...and more experience, from fights that are not this one. A
    # generalisation over two runs of the SAME fight keeps `goblin1`, because
    # both examples really do contain it -- `generalise` is right and the
    # evidence is thin. Different seeds are what turn a constant into a
    # variable, which is the difference between having seen a thing twice and
    # having experience of it.
    for seed in EXTRA_SEEDS:
        if name != "dungeon":
            break
        from . import dungeon
        other, _kb, _asked = dungeon.fight(seed=seed, limit=0)
        load(other, SETTLE)
        run(other, limit=limit, chooser=teacher, watch=lesson.watching)

    out = {
        "corpus": name, "pairs": len(lesson.pairs),
        "gold_moves": gold.ticks, "gold_state": gold.state,
        # How often the teacher wanted what the table's own order offered
        # first. This is the ceiling the calibration is trying to reach, and if
        # it is already high the corpus has nothing to teach.
        "teacher_took_the_top": lesson.agreed,
    }
    # ⚠ `none` is the UNCALIBRATED arm, and it went missing. This function's
    # own docstring says the loop runs twice, uncalibrated and calibrated, and
    # the gate in `main` still read `before`/`after` -- keys nothing here has
    # produced for some time. So the gate raised `KeyError` on the first corpus
    # every run: it could not fail, because it never got as far as comparing,
    # and `dungeon` was never measured at all. A gate that crashes reports the
    # same thing as a gate that passes -- nothing -- and it does it loudly
    # enough that nobody reads the rest.
    for label in ("none", "bigram", "query", "occasion", "both"):
        m, ldr = _machine(name)
        if label == "none":
            taught, added, declined, collided = {"unspeakable": 0}, 0, 0, 0
        elif label == "both":
            # The two kinds of attention doing their own jobs: persistent
            # buffs decide WHO IS IN the shortlist, which is speed, and
            # rerankers decide who wins INSIDE it, which is accuracy. The
            # shortlist restriction is what makes that division of labour
            # necessary rather than merely tidy -- a reranker cannot shorten a
            # scan whose chunks were chosen before it ran.
            taught = lesson.lessons(gold_m, conditional=False)
            added = install(m, ldr, taught)
            learned = lesson.recognisers(gold_m, gold_ldr)
            added += install_recognisers(m, ldr, learned)
            declined = taught["declined"] + learned["declined"]
            collided = taught["collided"]
        elif label == "occasion":
            # Keyed on the SITUATION: a learned recogniser that concludes
            # `noticing(<R>)` and spends its attention on R, so the lift arrives
            # whenever the occasion arises rather than only after one
            # particular predecessor.
            learned = lesson.recognisers(gold_m, gold_ldr)
            added = install_recognisers(m, ldr, learned)
            declined = learned["declined"]
            collided = 0
            taught = {"unspeakable": learned.get("unspeakable", 0)}
        else:
            taught = lesson.lessons(
                gold_m, conditional=(label == "query"))
            added = install(m, ldr, taught)
            declined, collided = taught["declined"], taught["collided"]
        r = run(m, limit=limit)
        # ⚠ The learned recognisers are moves the teacher never made, so they
        # SHIFT the sequence and a positional comparison counts every later
        # move as a disagreement. It reported 5 of 149 before this line, which
        # would have read as *situation-keyed lessons destroy the behaviour*
        # and meant *the comparison cannot see them*. A recogniser concludes
        # `noticing(<R>)` about the agent's own attention and nothing about the
        # world, so it is dropped from both sides.
        same = _agree(r.applied, gold.applied)
        out[label] = {
            "posts": added, "declined": declined, "collided": collided,
            "unspeakable": taught.get("unspeakable", 0),
            "moves": r.ticks,
            "matched_per_move": r.tried / max(1, len(r.windows)),
            "prefix_agreement": same,
            "conclusions": len(r.state),
            "lost": len(gold.state - r.state),
            "doubts": r.doubts,
        }
    return out


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## Why there is a teacher")[0].strip())
    print()
    bad = 0
    for name in ("quest-p1.ugm", "dungeon"):
        c = measure(name)
        print(f"  {c['corpus']}  -- {c['pairs']} bigrams from one taught run; "
              f"the teacher took the table's top choice "
              f"{c['teacher_took_the_top']}/{c['gold_moves']} times")
        for label in ("none", "bigram", "query", "occasion", "both"):
            d = c[label]
            print(f"    {label:7} {d['posts']:>3} posts "
                  f"({d['declined']} said nothing, {d['collided']} too general, "
                  f"{d['unspeakable']} unsayable)  "
                  f"{d['moves']:>4} moves  "
                  f"{d['matched_per_move']:>6.1f} matched/move  "
                  f"{d['prefix_agreement']:>4} moves agree with the teacher  "
                  f"{d['conclusions']:>4} conclusions, {d['lost']} lost  "
                  f"{d['doubts']} doubts")
        # The claim being gated: calibration must not cost conclusions the
        # uncalibrated table already reached. It may cost MOVES -- that is the
        # point of it -- and it may disagree with the teacher, who is one
        # person on one run. Losing an answer is the failure.
        for label in ("bigram", "query", "occasion", "both"):
            if c[label]["lost"] > c["none"]["lost"]:
                print(f"    FAIL  {label} lost {c[label]['lost']} against "
                      f"{c['none']['lost']} uncalibrated")
                bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
