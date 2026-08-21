"""§20's floor gate for quiescence: the verdict *this would change nothing*,

native against rule-level. agreement does it for the read, arbitration for the
move, state for what is kept. ⚠ This is recorded rather than acted on.

See docs/design/quiescence.md.
"""

from .. import corpora as _corpora
import time
from typing import Dict, List, Optional, Tuple

from .agreement import READ
from ..core.machine import Machine
from ..core.rules import Application, Member, _bounded, substitute
from ..core.text import load, load_file

# Quiescence, as rules. Every member is structural -- the imported read's `best`
# and `entry_of`, the chain's `mentioned`, and the five relations the harness
# mints about the candidate -- so every rule here is stratum 0 by §6's own test
# and concludes structure. That is what makes the two negations below mean *not
# derived* rather than *something denies it*.
QUIET = """
rule <holds> = implies(
  { best(?seat, ?prop, ?e), entry_of(?e, ?pe, ?sign) },
  { holds_as(?seat, ?prop, ?sign) } )

rule <mention-inherited> = implies(
  { consumed_by(?a, ?e), mentioned(?e) },
  { mentioning(?a) } )

rule <mention-authored> = implies(
  { about_rules(?a) },
  { mentioning(?a) } )

rule <silent> = implies(
  { unbound(?a), -mentioning(?a) },
  { silent(?a) } )

rule <changes> = implies(
  { proposes(?a, ?seat, ?prop, ?sign),
    -holds_as(?seat, ?prop, ?sign), -silent(?a) },
  { would_change(?a) } )

rule <quiet> = implies(
  { candidate(?a), -would_change(?a) },
  { settled(?a) } )
"""

# The harness's own relations: what a candidate application IS, in the graph.
# Registered as structural for `_bounded`'s stated reason -- these exist only
# because the gate asked, so enumerating them enumerates what the anchor already
# admitted -- and because an application is machinery's own bookkeeping and not
# a claim about a world. A `-` on one has to mean *not derived*, which is what
# the whole comparison turns on.
SUPPLIED = ("candidate", "proposes", "unbound", "consumed_by", "about_rules")

# The probe deletes nothing, and the first version did.
# → docs/design/quiescence.md#the-probe-deletes-nothing-and-the-first-versi
NEVER = "never-satisfied"

# The corpora used as fixtures, and how far to run each. Several stopping points
# per corpus, because a candidate set harvested only at quiescence is all quiet
# and a gate over it would agree with anything. The run prints the mix.
CORPORA = ("delay.ugm", "worked.ugm", "quest-p1.ugm")
STOPS = (0, 1, 3, 8)
# ...and a shorter set for the kill-probe, which runs the whole comparison once
# per rule. The rule-level read is a fixpoint over the chain, so it grows with
# the history; the probe asks a cheaper question -- *can deleting this rule be
# noticed at all* -- and does not need the deepest stop to answer it.
PROBE_STOPS = (0, 1, 3)

# A fourth fixture, written here because three real corpora between them reach
# none of these shapes -- and a gate whose fixture cannot reach a rule is a
# gate that reports agreement about it forever.
# → docs/design/quiescence.md#a-fourth-fixture-written-here-because-three-rea
SHAPES = """
fact tidy(room)
fact -tidy(room)
fact dirty(room)
rule <keep> = implies( { +dirty(room) }, { +tidy(room) } )

fact clean(hall)
fact swept(hall)
rule <mess>  = causes(  { +dirty(room) }, { -clean(hall) } )
rule <again> = implies( { +swept(hall) }, { +clean(hall) } )

rule <echo>   = implies( { +con(?r, ?pat, plus, ?i) }, { +echoed(?pat) } )
rule <attach> = implies( { +swept(hall) }, { +resume(hall, <echo>) } )
"""


class Harvest:
    """One stopping point: the candidates, their native verdicts, and which of
    them the rule-level side is allowed to be asked about."""

    def __init__(self) -> None:
        self.apps: List[Application] = []
        self.native: Dict[int, bool] = {}
        self.skipped: Dict[str, int] = {
            "stratum0": 0, "forbidden": 0, "span": 0, "generic": 0,
        }


def _harvest(m: Machine) -> Harvest:
    """Every candidate application here, and `_would_change` on each.

    Taken BEFORE anything is loaded or minted. `_decide_change` calls
    `substitute`, which interns, and the stratum-0 branch asks whether the
    conclusion is already in the graph -- so a harness that minted first would
    be reading its own footprints.
    """
    h = Harvest()
    proposed = m._recall()
    state = m._situation()
    for app in m._applications(proposed, state, materialise=True):
        h.native[id(app)] = m._would_change(app)
        h.apps.append(app)
    return h


def _admissible(m: Machine, h: Harvest, app: Application) -> Optional[List[tuple]]:
    """The conclusions this application would write, as (prop, sign) -- or None
    if it falls in one of the uncompared branches, tallied.

    ⚠ It was `(locus, prop, sign)`, and the locus came from `_conclude_at`,
    which resolved a member's `at ?m` against the bindings. Both are gone, and
    with them the `span` branch -- *the bound locus is not a moment*. Its
    counter is kept in the tally as a permanent zero rather than removed,
    because a counter that disappears reads as a branch nobody reached.
    """
    if m.rules.is_stratum0(app.rule):
        h.skipped["stratum0"] += 1
        return None
    pending = [(substitute(m.g, mem.pattern, app.bindings), mem.sign)
               for mem in app.rule.consequent]
    # A trigger may drop a conclusion, and a conclusion that will not land is
    # not something to be quiet or noisy ABOUT. Asked of the same seam the loop
    # asks, so this cannot drift from it.
    after = m._intercept(app, list(pending))
    if len(after) != len(pending) or any(x != y for x, y in zip(after, pending)):
        h.skipped["forbidden"] += 1
        return None
    return list(pending)


def _describe(m: Machine, ldr, h: Harvest, admitted) -> Dict[int, int]:
    """Mint what the rules read: one node per candidate and one fact per
    conclusion it would write.

    That is the whole of what is handed over. Grounding is `substitute`; the
    seat is the chain's own end -- there is no locus and no register left to
    ask. No verdict, no comparison, and
    nothing about whether the proposition already holds -- which is the half
    being tested."""
    g = m.g
    rel = {name: ldr.term(name) for name in SUPPLIED}
    names: Dict[int, int] = {}
    for i, (app, conclusions) in enumerate(admitted):
        a = g.atom(f"candidate-{i}")
        names[id(app)] = a
        g.rel(rel["candidate"], a)
        for grounded, sign in conclusions:
            g.rel(rel["proposes"], a, m.chain.now.node,
                  grounded, m.rules.SIGN[sign])
            if g.has_var(grounded):
                # `has_var` is the substrate's own question about a node, so it
                # may be handed over. What it MEANS -- nothing to deposit,
                # unless the conclusion is about a rule -- is <silent>'s to say,
                # and that is the half being compared.
                g.rel(rel["unbound"], a)
        for e in app.consumed:
            g.rel(rel["consumed_by"], a, e.node)
        if app.rule.mentions:
            # The one input with no graph counterpart: `reify` records a rule's
            # members, their loci and their `as` names, and not this. The other
            # source of mention -- §14's inheritance, a conclusion drawn from a
            # mentioned entry -- is derived rather than handed over, by
            # <mention-inherited>, and until §7's test was fixed it could not be.
            g.rel(rel["about_rules"], a)
    return names


def _ambiguous(m: Machine, ldr, admitted) -> set:
    """Candidates whose verdict the rule-level READ cannot settle, because more
    than one sign survives for a proposition it would write.

    `agreement` raises on this and calls it the point: a read answers with one
    entry, so several unbeaten candidates means the ordering rules are
    incomplete. Here it is tallied instead of raised, because it is not
    quiescence's failure and hiding it inside one would misattribute the defect
    -- see the module docstring's fifth branch.
    """
    holds = {}
    for n in m.g.instances_of(ldr.term("holds_as")):
        if m.g.has_var(n):
            continue
        seat, prop, sign = m.g.members(n)
        holds.setdefault((seat, prop), set()).add(sign)
    out = set()
    for app, conclusions in admitted:
        for grounded, _ in conclusions:
            if len(holds.get((m.chain.now.node, grounded), ())) > 1:
                out.add(id(app))
    return out


def _ruled(m: Machine, ldr, names: Dict[int, int]) -> Dict[int, Tuple[bool, bool]]:
    """The rule-level verdict for each candidate: (would_change, settled).

    Both are read, not one and its negation, because they are derived by
    different rules and a gate that read one and inverted it could not tell
    <quiet> from arithmetic.
    """
    changing = {m.g.members(n)[0] for n in m.g.instances_of(ldr.term("would_change"))}
    settled = {m.g.members(n)[0] for n in m.g.instances_of(ldr.term("settled"))}
    return {k: (a in changing, a in settled) for k, a in names.items()}


def _work(stops: Tuple[int, ...]) -> List[Tuple[str, int]]:
    """Every (corpus, stopping point) the comparison runs over, flattened, so the
    kill-probe can prune and reorder it instead of always running all of it."""
    return [(c, s) for c in CORPORA + ("shapes",) for s in stops]


_CONCLUDES: Optional[Dict[str, set]] = None


def _concludes() -> Dict[str, set]:
    """Rule name -> the relations it concludes.

    Read off the LOADED rules rather than parsed out of the source text. The
    prune in `run` is only sound if this is what the matcher actually holds, and
    a regex over `rule <...> = implies(...)` would go stale the first time a
    rule grew a second consequent member -- silently, and in the direction that
    skips work rather than the direction that does too much.
    """
    global _CONCLUDES
    if _CONCLUDES is None:
        m = Machine()
        load(m, READ + QUIET)
        # Only these two rule sets: a Machine arrives with its own rules already
        # loaded, and one of them concludes a BARE VARIABLE (§13's channel rule),
        # which has no relation to be named. Filtering by name rather than
        # guarding `relation_of` keeps the map to rules the probe can suppress.
        wanted = set(_names(QUIET)) | set(_names(READ))
        _CONCLUDES = {
            r.name: {m.g.show(m.g.relation_of(mem.pattern)) for mem in r.consequent
                     if m.g.relation_of(mem.pattern) is not None}
            for r in m.rules.rules if r.name in wanted
        }
    return _CONCLUDES


def _relations() -> set:
    return {x for s in _concludes().values() for x in s}


def _compare(drop: Tuple[str, ...] = (), stops: Tuple[int, ...] = STOPS,
             work: Optional[List[Tuple[str, int]]] = None,
             first_only: bool = False) -> dict:
    """`work` is the (corpus, stop) list to run, defaulting to all of them;
    `first_only` stops at the first disagreement. Both exist for the kill-probe
    -- see `run` -- and neither changes what is compared, only how much of the
    fixture is reached before the answer is known."""
    tally = {
        "compared": 0, "changing": 0, "quiet": 0,
        "disagreed": [], "unsettled": [], "skipped": {"stratum0": 0, "forbidden": 0, "span": 0, "generic": 0},
        "corpora": 0, "ambiguous": 0,
        # What each run cost and what it DERIVED, so the probe can plan itself
        # off the baseline pass rather than off a guess.
        "cost": {}, "derived": {}, "noticed": None,
    }
    for corpus, stop in (_work(stops) if work is None else list(work)):
        started = time.time()
        tally["derived"][(corpus, stop)] = set()
        m = Machine()
        if corpus == "shapes":
            load(m, SHAPES)
        else:
            load_file(m, _corpora.path(corpus))
        for _ in range(stop):
            if m.tick().state in ("stopped", "quiescent"):
                break
        h = _harvest(m)
        admitted = []
        for app in h.apps:
            conclusions = _admissible(m, h, app)
            if conclusions is not None:
                admitted.append((app, conclusions))
        for k, v in h.skipped.items():
            tally["skipped"][k] += v
        if not admitted:
            tally["cost"][(corpus, stop)] = time.time() - started
            continue
        tally["corpora"] += 1

        # The rules go in AFTER the harvest, and the machine is not ticked
        # again: this is an observer, and a gate that added rules to a
        # running loop would be a second agent (the retired `arbitration`'s own note).
        ldr = load(m, READ + QUIET)
        for name in SUPPLIED:
            m.rules.structural[ldr.term(name)] = _bounded
        m.rules._skeleton = None
        if drop:
            # GENERIC, and the first version was ground -- which minted
            # `candidate(never-satisfied)` and thereby created the very
            # instance it was supposed to be unable to find. Every rule of
            # the read then read as exercised-by-nothing, 0/10, which is the
            # interning trap wearing the probe's own clothes. A pattern with
            # a variable in it is skipped by `_bounded` as a pattern rather
            # than a fact (§7), so nothing can ever satisfy it.
            dead = m.g.rel(m.g.atom(NEVER), m.g.var("z"))
            m.rules.structural[m.g.relation_of(dead)] = _bounded
            m.rules._skeleton = None
            impossible = Member("+", dead)
            for r in m.rules.rules:
                if r.name in drop:
                    r.antecedent = list(r.antecedent) + [impossible]

        names = _describe(m, ldr, h, admitted)
        # ...and about WHAT. The read is a fixpoint, so without this it
        # derives candidates, beatings and a winner for every proposition
        # the chain mentions, to answer a question about the handful this
        # gate is comparing. Measured on `agreement`'s own fixture once §7
        # stopped hiding the reified entries: 10,638 derived facts and 90
        # seconds, against 61 facts and 0.3 seconds asked this way.
        m.ask_read(m.chain.now, about=[p for _, cs in admitted
                                       for p, _ in cs])
        m.settle_structure()
        verdicts = _ruled(m, ldr, names)
        ambiguous = _ambiguous(m, ldr, admitted)
        # What the two rule sets actually DERIVED here -- ground instances only.
        # A rule's own consequent member is interned among the instances of its
        # relation (the interning trap, yet again), so counting instances
        # without this reports `silent` firing twice in every corpus when it has
        # never fired anywhere at all. That miscount is exactly what would make
        # the prune below unsound, so it is the one line it rests on.
        tally["derived"][(corpus, stop)] = {
            nm for nm in _relations()
            if any(not m.g.has_var(n) for n in m.g.instances_of(ldr.term(nm)))
        }

        for app, _ in admitted:
            if id(app) in ambiguous:
                tally["ambiguous"] += 1
                continue
            native = h.native[id(app)]
            ruled, settled = verdicts[id(app)]
            tally["compared"] += 1
            tally["changing" if native else "quiet"] += 1
            if native != ruled:
                tally["disagreed"].append(
                    f"{corpus}@{stop} {app.rule.name}: native={native} rules={ruled}"
                )
            if settled == ruled:
                # <quiet> is the universal, and it must be the complement of
                # <changes> on every candidate. Equal means one of them
                # derived nothing at all.
                tally["unsettled"].append(
                    f"{corpus}@{stop} {app.rule.name}: "
                    f"would_change={ruled} settled={settled}"
                )
        tally["cost"][(corpus, stop)] = time.time() - started
        if first_only and (tally["disagreed"] or tally["unsettled"]):
            # The probe's question is *can suppressing this rule be noticed at
            # all*, and one disagreement answers it. Running the other eleven
            # fixtures to raise the count is work nothing reads -- the verdict
            # is `n == 0`, never how large n is.
            tally["noticed"] = f"{corpus}@{stop}"
            break
    return tally


def _names(text: str) -> List[str]:
    return [line.split("<")[1].split(">")[0]
            for line in text.splitlines() if line.startswith("rule <")]


def run() -> int:
    t = _compare()
    print("§20 floor gate -- quiescence, native against rule-level")
    print("  the rule-level side is ORDINARY RULES, under the ordinary matcher")
    print(f"  candidates compared   {t['compared']}")
    print(f"    native says CHANGES {t['changing']}")
    print(f"    native says QUIET   {t['quiet']}")
    print(f"  and {t['ambiguous']} more the rule-level READ could not settle "
          f"-- see the fifth branch")
    print("  uncompared branches, by why:")
    for k, v in t["skipped"].items():
        print(f"    {k:10} {v}")
    for f in t["disagreed"][:6]:
        print(f"  FAIL  {f}")
    if len(t["disagreed"]) > 6:
        print(f"  ...   and {len(t['disagreed']) - 6} more")
    for f in t["unsettled"][:6]:
        print(f"  FAIL  the universal and the existential agree: {f}")
    if not t["disagreed"] and not t["unsettled"]:
        print("  ok    every verdict agrees, and <quiet> is <changes>'s complement")

    print()
    print("  can this fixture fail? -- one rule suppressed at a time")
    # ⭐⭐⭐ The probe used to re-run the whole fixture for every rule, and four
    # fifths of the gate's 16 minutes were spent doing it. ⚠ And the count it
    # used to print is gone deliberately, because with an early exit it would
    # mean *how far we got*, not *how wrong it is*.
    # → docs/design/quiescence.md#the-probe-used-to-re-run-the-whole-fixture
    concl = _concludes()
    order = sorted(_work(PROBE_STOPS), key=lambda w: t["cost"].get(w, 0.0))
    quiet_names = _names(QUIET)
    blind = []
    for name in quiet_names + _names(READ):
        rels = concl.get(name, set())
        items = [w for w in order if rels & t["derived"].get(w, set())]
        d = _compare((name,), work=items, first_only=True) if items else None
        n = 0 if d is None else len(d["disagreed"]) + len(d["unsettled"])
        note = ""
        if name not in quiet_names:
            # The imported read's own rules. Their gate is `ugm.agreement`,
            # whose fixture is built for them; printed here because a read this
            # gate leans on is worth watching, and NOT counted as this gate's
            # blindness. The five ordering rules come out blind for a reason
            # worth reading -- see the fifth branch above: the cases that would
            # exercise them are the cases §7 turns into an ambiguous read.
            note = "   (agreement's)"
        elif not n:
            blind.append(name)
            note = "   <-- BLIND"
        if d is not None and d["noticed"]:
            where = f"noticed at {d['noticed']}"
        elif not items:
            where = f"derived nothing in any of {len(order)} fixtures"
        else:
            where = f"survived {len(items)} suppressions"
        print(f"    {name:18} {where:38}{note}")

    print()
    bad = len(t["disagreed"]) + len(t["unsettled"])
    print(f"{t['compared']} candidates, {bad} disagreeing; "
          f"{len(quiet_names) - len(blind)}/{len(quiet_names)} of quiescence's "
          f"own rules exercised")
    if t["changing"] == 0 or t["quiet"] == 0:
        print("  every candidate got the SAME verdict: this run measured nothing")
        return 1
    return bad + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
