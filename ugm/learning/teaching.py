"""Bootstrapping the table from use. (the author's design)

    python -m ugm.learning.teaching

> A human is the first, manual user of the KB. ⭐⭐⭐ AND IT PAYS, which is
measured here for the first time. ⚠ It cannot be learned from the teacher, and
finding that out is half the result.

See docs/design/teaching.md.
"""

from typing import Dict, List, Optional, Tuple

from .. import corpora as _corpora

from ..core.attention import SETTLE, Table, run
from ..core.graph import NodeId
from ..core.machine import Machine
from ..core.chain import PLUS
from ..core.rules import (Application, Member, Situation, arbitrate,
                    generalise, unify)
from ..core.text import ParseError, load, load_file


def teacher(m: Machine, table: Table, window, state: Situation):
    """The shipped arbitration, as a gold teacher.

    It chooses over the FULL option set -- `_materialise` is the slow definition
    the retired `ugm.arbitration` held the fast one to -- rather than over the window, so
    it is a genuine teacher and not a re-ranking of what the table already
    liked. Offline cost, which is what a teacher is allowed.
    """
    everything = m._materialise(m.rules.rules, state)
    if not everything:
        return window[0] if window else None
    # ⚠ No priority key. `_rank` used to put `standing` rules first and then sort
    # by the `prefer` table; both are retired, so the gold teacher chooses by
    # defeat and then authored order -- which is what `arbitrate` does with no
    # key at all, and is simpler than what it replaced.
    chosen = arbitrate(m.rules, everything)
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
        # ⭐⭐⭐ What the move just bound, and whether the next move was about it
        # too. ⚠ This signal comes from PLAY and not from the teacher, and it
        # has to.
        # → docs/design/teaching.md#what-the-move-just-bound-and-whether-the
        self.carried: Dict[Tuple[str, str], int] = {}
        # ...and WHAT THE NEXT MOVE CONSUMED on each of those occasions, anchored
        # back to the previous rule's own variables. This is what makes a focus
        # lesson conditional, and a corpus with ONE action rule cannot be taught
        # without it: every move is the same rule, so an unconditional
        # `after <move> => attend($d)` says the same thing at every step and
        # therefore says nothing. What distinguishes the steps is the SHAPE of
        # the situation, and that is what a query is.
        self.focused: Dict[Tuple[str, str], List[Tuple]] = {}
        self.values: Dict[Tuple[str, str], set] = {}
        self.fired: Dict[str, int] = {}
        self.agreed = 0
        self.moves = 0
        self.last: Optional[str] = None
        self.last_bindings: Dict = {}
        self.last_example: Optional[Tuple] = None

    def watching(self, m: Machine, table: Table, window, chosen, tick: int,
                 step=None):
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
        # keying went round a full circle to get back here.
        # →
        # docs/design/teaching.md#the-rule-s-own-situation-what-made-this-move
        self.occasions.setdefault(name, []).append(
            tuple(_say(m, e.proposition) for e in chosen.consumed))
        # ...and what carried, which is the attention lesson's whole signal.
        if self.last is not None:
            self.fired[self.last] = self.fired.get(self.last, 0) + 1
            landed = set(chosen.bindings.values())
            back = {v: k for k, v in self.last_bindings.items()}
            for var, val in self.last_bindings.items():
                if val in landed:
                    key = (self.last, m.g.show(var))
                    self.carried[key] = self.carried.get(key, 0) + 1
                    self.focused.setdefault(key, []).append(tuple(
                        _anchor(m, e.proposition, back) for e in chosen.consumed))
        for var, val in chosen.bindings.items():
            self.values.setdefault((name, m.g.show(var)), set()).add(
                m.g.show(val))
        self.last = name
        self.last_bindings = dict(chosen.bindings)

    # -- what a demonstration becomes -------------------------------------

    def focuses(self, m: Machine, conditional: bool = False) -> dict:
        """What to think ABOUT after each rule: one variable per rule, learned

        from what carried into the following move. ⭐⭐⭐ One per rule, and
        choosing which is the whole design. ⚠ Two firings at least, for this
        file's standing reason: one example generalises to itself.

        See docs/design/teaching.md#focuses.
        """
        out = {"rules": {}, "declined": 0, "collided": 0}
        best: Dict[str, Tuple] = {}
        for (rule, var), n in self.carried.items():
            fired = self.fired.get(rule, 0)
            if n < 2 or fired < 2 or n * 2 < fired:
                # Seen once, or carried less than half the time: not experience.
                out["declined"] += 1
                continue
            # Distinctness first, then how often it carried, then the name --
            # which is only ever a tie-break and is here so two runs of the same
            # demonstration teach the same lesson (§3).
            key = (len(self.values.get((rule, var), ())), n, var)
            if rule not in best or key > best[rule][0]:
                best[rule] = (key, var, n)
        for rule, (_key, var, n) in best.items():
            if not conditional:
                out["rules"][rule] = (var, n, "")
                continue
            # ⭐ The query, by the same anti-unification a bigram lesson uses.
            # What the occasions have in common is the lesson; an individual
            # that appears in all of them is kept only because the evidence is
            # thin, which is why experience means more than one run.
            query = _query(m, self.focused.get((rule, var), []))
            if not query:
                out["declined"] += 1
                continue
            text = "q(" + ", ".join(m.g.show(x.pattern) for x in query) + ")"
            out["rules"][rule] = (var, n, text)
        return out

def install_focuses(m: Machine, ldr, learned: dict) -> int:
    """The attention lessons, as postconditions.

    ⚠⚠⚠ **`unattend` first, and it is what bounds the mechanism.** A buff has
    `LIFE` and a saturation ceiling; a deposited claim has neither, so a lesson
    that only ever attends accumulates until everything is attended -- and
    `ugm.selftest` measures that attending to everything narrows nothing. Spent
    as a pair, attention becomes a FOCUS: one thing at a time, replaced each
    time the lesson fires, and the replacement is on the record as a denial
    rather than as a forgetting.

    ⚠ Nothing here is `frozen`. These are exactly what a calibration process is
    supposed to move, and marking learned experience unmovable would be the
    calibrator protecting its own output from the next demonstration.
    """
    lines = focus_lines(m, ldr, learned)
    added = 0
    for line in lines:
        try:
            ldr.load(line)
        except ParseError:
            learned["unspeakable"] = learned.get("unspeakable", 0) + 1
            continue
        added += 1
    return added


def focus_lines(m: Machine, ldr, learned: dict) -> List[str]:
    """The learned attention lessons, as SURFACE TEXT -- one line each.

    ⭐⭐⭐ **One renderer for the document and for what runs**, so the two cannot
    drift. `install_focuses` loads exactly these lines and `emit` writes exactly
    these lines; a lesson that is inspectable but not the lesson that ran would
    be worse than none.
    """
    by_name = {r.name for r in m.rules.rules if r.name}
    out: List[str] = []
    for name, (var, times, text) in sorted(learned["rules"].items()):
        if name not in by_name:
            continue
        query = " "
        if text:
            try:
                whole = ldr.term(text)
            except ParseError:
                learned["unspeakable"] = learned.get("unspeakable", 0) + 1
                continue
            query = " { %s } " % ", ".join(
                "+" + m.g.show(x) for x in m.g.members(whole))
        out.append(FOCUS % (name, query, var, min(times, 9)))
    return out


def emit(m: Machine, ldr, learned: dict, note: str = "") -> str:
    """What was learned about ATTENTION, as a document a person can read.

    ⭐⭐⭐ This file has claimed since it was written that a lesson is a document
    -- *savable, diffable, arguable, and loadable into a corpus that was never
    taught* -- and it had no open and no write in it. ⚠ It is the ORDINARY
    SURFACE, so it round-trips by construction: Loader reads it back with no
    special path, a person can edit a line in place, and an edited...

    See docs/design/teaching.md#emit.
    """
    head = ["# Learned by `ugm.teaching`. Ordinary corpus text: edit it, diff",
            "# it, delete a line you disagree with, or load it into a corpus",
            "# that was never taught.",
            "#",
            "# `learned` marks what play added. Strip those lines and what is",
            "# left is exactly what a person wrote."]
    if note:
        head.append("# " + note)
    return chr(10).join(head) + chr(10) + chr(10) + "".join(
        focus_lines(m, ldr, learned))


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
        out.append(Member(PLUS, lgg, None))
    return tuple(out)


EXTRA_SEEDS = (11, 13, 17)

# The trigger form, as text: a lesson is a document. ⚠ There were two more --
# WHEN and AFTER, both writing boost(<R>, n).
# → docs/design/teaching.md#the-trigger-form-as-text-a-lesson-is-a-documen
FOCUS = "learned after <%s>%s=> attend(%s, %d)" + chr(10)


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


# ⭐⭐⭐ What a taught table is allowed to conclude differently. ⚠ attention is
# here, and leaving it out flattered the mechanism.
# → docs/design/teaching.md#what-a-taught-table-is-allowed-to-conclude
BOOKKEEPING = frozenset({"close", "settled", "spent", "exercised", "attention"})


def _domain_only(diff):
    return {(p, s) for p, s in diff if p.split("(")[0] not in BOOKKEEPING}


def _machine(name: str):
    """A fresh machine and the loader that is its name scope -- a lesson is
    re-read through it, since a bare name outside a scope names nothing."""
    if name == "dungeon":
        from ..probes import dungeon
        m, ldr, _asked = dungeon.fight(seed=7, limit=0)
    else:
        m = Machine()
        ldr = load_file(m, _corpora.path(name))
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
        from ..probes import dungeon
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
    # ⚠ none is the UNCALIBRATED arm, and it went missing.
    # → docs/design/teaching.md#none-is-the-uncalibrated-arm-and-it-went-mi
    for label in ("none", "focus"):
        m, ldr = _machine(name)
        if label == "none":
            taught, added, declined, collided = {"unspeakable": 0}, 0, 0, 0
        else:
            # ⭐⭐⭐ **Keyed on a THING, not on a rule.** Every arm above teaches
            # the table which RULE to reach for. This one teaches the agent what
            # to think ABOUT -- and so it is the only one that can reach the
            # binding, which no buff can name.
            learned = lesson.focuses(gold_m)
            added = install_focuses(m, ldr, learned)
            declined, collided = learned["declined"], 0
            taught = {"unspeakable": learned.get("unspeakable", 0)}
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
            # Reported: what a taught run failed to reach ABOUT THE WORLD.
            "lost": len(_domain_only(gold.state - r.state)),
            "lost_what": sorted(_domain_only(gold.state - r.state)),
            # ...and the raw figure beside it, so the exclusion is visible
            # rather than silently applied.
            "diff": len(gold.state - r.state),
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
        for label in ("none", "focus"):
            d = c[label]
            print(f"    {label:7} {d['posts']:>3} posts "
                  f"({d['declined']} said nothing, {d['collided']} too general, "
                  f"{d['unspeakable']} unsayable)  "
                  f"{d['moves']:>4} moves  "
                  f"{d['matched_per_move']:>6.1f} matched/move  "
                  f"{d['prefix_agreement']:>4} moves agree with the teacher  "
                  f"{d['conclusions']:>4} conclusions, {d['lost']} lost "
                  f"({d['diff']} incl. bookkeeping)  "
                  f"{d['doubts']} doubts")
        # The claim being gated: calibration must not cost conclusions the
        # uncalibrated table already reached.
        # →
        # docs/design/teaching.md#the-claim-being-gated-calibration-must-not-cost
        if name == "dungeon":
            gm2, gl2 = _machine(name)
            lesson2 = Lesson()
            run(gm2, limit=400, chooser=teacher, watch=lesson2.watching)
            doc = emit(gm2, gl2, lesson2.focuses(gm2, conditional=True),
                       "%s, one taught fight" % name)
            print()
            for line in doc.splitlines():
                print("    " + line)
            print()
        for label in ("focus",):
            if c[label]["lost"] > c["none"]["lost"]:
                print(f"    FAIL  {label} lost {c[label]['lost']} against "
                      f"{c['none']['lost']} uncalibrated")
                bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
