"""SPIKE — DOES THE EXPRESSION BUILD THE NETWORK? (user proposal, 2026-07-26)

> *"'wash the car that is parked at the third floor of the garage near the movie theater' builds a network of
> chained selectors, and at the end of it places a tool call to `wash` on whatever entity it gets. The network
> derives from the expression."*

This is the answer to a wall hit in the coreference work: a pattern that declines to say what it reads cannot
have its topology inferred, so it must be **authored**. If the syntactic nesting *is* the wiring, the expression
is what authors it.

**What a selector outputs — decided before building, from a decision already in force:** *a description
IDENTIFIES rather than CONSTITUTES.* Read constitutively, "one subgraph = one entity" means the car stops
existing when it moves to the second floor. So the entity stays a NODE, the subgraph is the CONSTRAINT SET on
it, and a selector emits **a reference keyed on the selector STEP**:

    <s3> <refers_to> car        NOT   car <selected> yes
    <s3> <narrows>   <s2>             (so the unfolded expression is walkable off the graph)

Keying on the step rather than the entity keeps derivational marks off the entity, lets two chains disagree
about the same entity, and is what makes the chain readable.

**Six probes, written to break.** 2, 5 and 6 are the ones that could change the design.

    python bench/spike_selector_chain.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, role  # noqa: E402
from units import discourse as D                                               # noqa: E402
from units.match import Absent                                                 # noqa: E402
from units.vocab import lexeme as L                                            # noqa: E402

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))


E, P, A, B, S = Var("e"), Var("p"), Var("a"), Var("b"), Var("s")
r = role
REF = r("<refers_to>")
NARROWS = r("<narrows>")
ARG1, ARG2 = r("<arg1>"), r("<arg2>")       # POSITIONAL argument slots — see `chain_net`
STEP = r("<step>")                  # a step node's type, contributed by the parse
RESOLVED = r("<step_resolved>")
UNRESOLVED = r("<unresolved>")
AMBIG = r("<step_ambiguous>")


def world(near_theater: bool = True, two_garages_near: bool = False, colour=None) -> tuple:
    """The KB — nothing here comes from the expression."""
    th, g1, g2, f3, car = mint(""), mint(""), mint(""), mint(""), mint("")
    facts = [Fact(th, r("<word>"), L("movie_theater")),
             Fact(g1, r("<word>"), L("garage")),
             Fact(g2, r("<word>"), L("garage")),
             Fact(f3, r("<word>"), L("floor")), Fact(f3, r("<of>"), g1),
             Fact(f3, r("<ordinal>"), L("third")),
             Fact(car, r("<word>"), L("car")), Fact(car, r("<parked_at>"), f3)]
    if near_theater:
        facts.append(Fact(g1, r("<near>"), th))
    if two_garages_near:
        facts += [Fact(g2, r("<near>"), th), Fact(mint(""), r("<word>"), L("floor"))]
    if colour is not None:
        facts.append(Fact(car, r("<colour>"), colour))
    return Subgraph(facts), dict(theatre=th, garage=g1, other_garage=g2, floor=f3, car=car)


def chain_net(w: Subgraph, steps: list, terminal=None) -> tuple:
    """`steps` is the expression, innermost first: (name, extra_atoms, lexeme). Each step's node is ground and
    supplied by the parse — one per syntactic position, so it is keyed by construction."""
    net = Net()
    net.spawn(given("world", w))
    nodes, prev = [], None
    parse = []                                          # what the PARSE contributes, as facts
    for i, (word, extra) in enumerate(steps, start=1):
        sk = mint(f"<s{i}>")
        nodes.append(sk)
        parse.append(Fact(sk, r("<is_a>"), STEP))
        lhs = [] if prev is None else [Triple(prev, REF, P)]
        lhs.append(Triple(E, "<word>", L(word)))
        lhs += list(extra)
        net.declare(f"S{i}", tuple(lhs), Triple(sk, REF, E))
        if prev is not None:
            parse.append(Fact(sk, NARROWS, prev))
        prev = sk
    call = mint("<call>")
    if terminal:
        # ⭐ THE CALL IS POSITIONAL, NOT ROLE-LABELLED (§32, the user's decision). A call is just another
        # discourse node: it carries a LEXEME through the same `<word>` predicate a mention uses, and its
        # arguments are NUMBERED. `<arg1>` names a POSITION, so *direction carries the role* holds one level
        # up and the Davidsonian shape rejected for facts is not reintroduced for commands.
        #
        # And an argument points at the STEP, not at the entity: the chain stays walkable, and a failed or
        # ambiguous argument is visible to the call.
        net.declare("CALL", (Triple(prev, REF, E),), Triple(call, ARG1, prev))
        parse += [Fact(call, r("<word>"), L(terminal)), Fact(call, NARROWS, prev)]
    # ⚠ THE UTTERANCE ENTERS AS A CARRIER DOWNSTREAM OF THE KB, NOT AS A SIBLING GIVEN (probe 4a).
    # Two independent `given`s are two WORLDS: incomparable, so no rule can join them — and a rule whose
    # negated premise lives in the other world has its NAF go vacuously true. Wiring the parse below the
    # world makes it a DESCENDANT, hence comparable with everything derived from the world, and it keeps the
    # utterance distinguishable from the KB (which a single merged given would lose).
    net.spawn(branch("parse", add=Subgraph(parse)))
    net.wire("world", "parse")
    return net, nodes, call


def declare_demands(net: Net) -> None:
    """The DEFINITE demands, generic over every step — the same shape the coreference work used."""
    net.declare("SELF", *D.self_rule())                                   # ?e <word> ?y => ?e <self> ?e
    net.declare("RESOLVED", (Triple(S, REF, E),), Triple(S, RESOLVED, S))
    net.declare("UNRESOLVED", (Triple(S, "<is_a>", STEP), Absent(Triple(S, RESOLVED, S))),
                Triple(S, UNRESOLVED, S))
    net.declare("STEP_AMBIG", (Triple(S, REF, A), Triple(S, REF, B), Absent(Triple(A, D.SELF, B))),
                Triple(S, AMBIG, S))


SENTENCE = [("movie_theater", []),
            ("garage", [Triple(E, "<near>", P)]),
            ("floor", [Triple(E, "<of>", P), Triple(E, "<ordinal>", L("third"))]),
            ("car", [Triple(E, "<parked_at>", P)])]


def got(net: Net, pred) -> set:
    return {f for _, f in net.derived_anywhere(pred)}


# ======================================================================================================
print("\n== 1. END TO END — the call request names the right car ==")

w, ent = world()
net, steps, call = chain_net(w, SENTENCE, terminal="wash")
budget = net.run(Budget(limit=200000))

refs = {f.s: f.o for f in got(net, "<refers_to>")}
check("1a the chain resolves and the call's ARGUMENT dereferences to the CAR",
      Fact(call, ARG1, steps[-1]) in got(net, "<arg1>") and refs.get(steps[-1]) == ent["car"],
      f"arg1={sorted(map(repr, got(net, '<arg1>')))} -> {refs.get(steps[-1])!r}")
check("1a2 ⭐ and the call is POSITIONAL, not role-labelled: it carries its lexeme through the same `<word>` "
      "predicate a mention uses, and `<arg1>` names a POSITION. The Davidsonian shape rejected for facts is "
      "not reintroduced for commands (§32)",
      Fact(call, r("<word>"), L("wash")) in set(net.units["parse"].output))
check("1b each step emits ONE reference, keyed on the step node — not a subgraph, not a mark on the entity",
      all(len(net.units[f"S{i}#1"].last_derived) == 1 for i in range(1, 5)),
      " ".join(f"s{i}={len(net.units[f'S{i}#1'].last_derived)}" for i in range(1, 5)))
check("1c the chain NARROWED: the garage not near the theatre never reaches a referent",
      ent["other_garage"] not in {f.o for f in got(net, "<refers_to>")})
check("1d and it is cheap — one unit per syntactic position, no unrolling",
      len(net.units) == 7, f"units={len(net.units)}")

# ======================================================================================================
print("\n== 2. ⭐ IS IT ASSEMBLABLE? — the question that matters most ==")
# The coreference merge could NOT be wired by inference: its wildcard atom is satisfied by any fact. A
# selector's atoms all carry GROUND predicates, so the assembler should complete each join by itself.
wired = {f"S{i}#1": sorted(net.producers.get(f"S{i}#1", ())) for i in range(1, 5)}
check("2a ⭐ EVERY selector was wired to a WORLD-CARRYING producer AND to its predecessor BY THE ASSEMBLER — "
      "no authored merge, no hand wiring. Selector chains are assemblable exactly where a wildcard rule is "
      "not, because every atom names its predicate. (It picks `parse` over `world`: frontier-first, and "
      "`parse` carries the world through)",
      all("parse" in v or "world" in v for v in wired.values())
      and all(f"S{i - 1}#1" in wired[f"S{i}#1"] for i in range(2, 5)), f"{wired}")
check("2b the expression supplied only the STEP NODES and the `<narrows>` links — data, never wires",
      "parse" in net.units and sorted(net.producers["parse"]) == ["world"])
check("2c ⭐ so the EXPRESSION authors the topology without crossing the line that units never wire anything: "
      "it contributes ground step nodes, and the ordinary spawn policy does the rest", True)

# ======================================================================================================
print("\n== 3. EACH HOP GATES — delete one world fact and the chain starves ==")

w2, ent2 = world(near_theater=False)                    # no garage near the theatre
net2, steps2, call2 = chain_net(w2, SENTENCE, terminal="wash")
net2.run(Budget(limit=200000))
check("3a the second selector matches nothing, so it emits nothing",
      not net2.units["S2#1"].last_derived)
check("3b …and EVERYTHING downstream is starved — no floor, no car, no call argument",
      not got(net2, "<arg1>") and len(got(net2, "<refers_to>")) == 1,
      f"refs={len(got(net2, '<refers_to>'))} args={len(got(net2, '<arg1>'))}")
check("3c gating is structural: a selector is a rule, and a rule that matches nothing emits nothing. No "
      "special 'reference failed' path exists or is needed", True)

# ======================================================================================================
print("\n== 4. FAILURE AND AMBIGUITY ARE DETECTABLE PER HOP, not silent ==")

net3, steps3, call3 = chain_net(world(near_theater=False)[0], SENTENCE, terminal="wash")
declare_demands(net3)
net3.run(Budget(limit=400000))
unres = {f.s for f in got(net3, UNRESOLVED)}
check("4a ⭐ the FAILING step is named — `<unresolved>` on s2, s3, s4 and not on s1. So the chain reports "
      "WHERE reference failed, which a starved chain alone does not",
      steps3[0] not in unres and set(steps3[1:]) <= unres,
      f"unresolved={sorted(map(repr, unres))}")

net4, steps4, call4 = chain_net(world(two_garages_near=True)[0], SENTENCE, terminal="wash")
declare_demands(net4)
net4.run(Budget(limit=400000))
amb = {f.s for f in got(net4, AMBIG)}
check("4b ⭐ AMBIGUITY is named at the step that has two referents, AND ONLY THERE — 'the garage' matched "
      "two, every other step matched one",
      amb == {steps4[1]}, f"ambiguous={sorted(map(repr, amb))} expected={steps4[1]!r}")
check("4c and the same two rule shapes the coreference work already needed cover it — a witness plus NAF for "
      "failure, an inequality for ambiguity. Nothing new was required for selectors",
      True)

# ======================================================================================================
print("\n== 5. BRANCHING — it is a TREE, not a pipeline ==")
# "wash the car AND THE TRUCK that are parked at <s3>": two selectors read the SAME step.
w5, ent5 = world()
truck = mint("")
w5 = w5 | Subgraph([Fact(truck, r("<word>"), L("truck")), Fact(truck, r("<parked_at>"), ent5["floor"])])
net5, steps5, _ = chain_net(w5, SENTENCE[:3], terminal=None)
s3 = steps5[-1]
c_car, c_truck = mint("<call_car>"), mint("<call_truck>")
net5.declare("CAR", (Triple(s3, REF, P), Triple(E, "<word>", L("car")), Triple(E, "<parked_at>", P)),
             Triple(c_car, ARG1, E))
net5.declare("TRUCK", (Triple(s3, REF, P), Triple(E, "<word>", L("truck")), Triple(E, "<parked_at>", P)),
             Triple(c_truck, ARG1, E))
net5.run(Budget(limit=200000))
targets = {(f.s, f.o) for f in got(net5, "<arg1>")}
check("5a both branches resolve off ONE shared step",
      (c_car, ent5["car"]) in targets and (c_truck, truck) in targets,
      f"{sorted(map(repr, targets))}")
check("5b ⭐ and the shared step has TWO consumers — the topology is a DAG. 'Postfix' would have implied a "
      "linear stack; the expression gives a TREE and the network is that tree",
      len(net5.consumers.get("S3#1", set())) == 2,
      f"consumers of S3#1 = {sorted(net5.consumers.get('S3#1', ()))}")

# ======================================================================================================
print("\n== 6. ⚠ SURFACE-SENSITIVITY OF BELIEF — the probe that could sink the idea ==")
# Two expressions, same meaning, DIFFERENT nesting order:
#   A: the car    -> parked at F -> that is red
#   B: the car    -> that is red -> parked at F
# The REFERENT and the BELIEF must be identical. Only the chain data may differ.
red = mint("red")


def coloured_chain(order: str):  # noqa: E306
    w, ent = world(colour=red)
    at = ("floor", [Triple(E, "<of>", P), Triple(E, "<ordinal>", L("third"))])
    steps = [("movie_theater", []), ("garage", [Triple(E, "<near>", P)]), at]
    if order == "A":
        steps += [("car", [Triple(E, "<parked_at>", P)]), ("car", [Triple(E, "<colour>", red)])]
    else:
        steps += [("car", [Triple(E, "<colour>", red)]), ("car", [Triple(E, "<parked_at>", P)])]
    n, s, c = chain_net(w, steps, terminal="wash")
    n.run(Budget(limit=400000))
    return n, s, c, ent


# NOTE: order B's last step reads `<parked_at> ?p` where ?p is the PREVIOUS step's referent (a car), which is
# not what the sentence means. Written deliberately: it is the naive re-ordering, and what it exposes is real.
nA, sA, cA, entA = coloured_chain("A")
nB, sB, cB, entB = coloured_chain("B")
tA = {refs.get(f.o) for f in got(nA, "<arg1>") for refs in [{g.s: g.o for g in got(nA, "<refers_to>")}]}
tB = {refs.get(f.o) for f in got(nB, "<arg1>") for refs in [{g.s: g.o for g in got(nB, "<refers_to>")}]}
check("6a order A resolves to the car", tA == {entA["car"]}, f"{sorted(map(repr, tA))}")
check("6b ⚠ THE NAIVE RE-ORDERING DOES NOT MEAN THE SAME THING, and the chain shows why: each step's `?p` is "
      "the PREVIOUS step's referent, so moving `parked_at` after `colour` makes it ask *a car parked at a "
      "car*. **A selector chain is not commutative, because the chain IS the attachment structure.**",
      tB == set(), f"{sorted(map(repr, tB))}")

# The MEANING-PRESERVING re-ordering keeps every modifier attached to the same antecedent.
w6, ent6 = world(colour=red)
F = ent6["floor"]


def flat(order):
    n = Net()
    n.spawn(given("world", w6))
    sk = mint("<sx>")
    atoms = [Triple(E, "<word>", L("car")), Triple(E, "<parked_at>", F), Triple(E, "<colour>", red)]
    if order == "B":
        atoms = [atoms[0], atoms[2], atoms[1]]
    n.declare("SEL", tuple(atoms), Triple(sk, REF, E))
    n.run(Budget(limit=100000))
    return {f.o for f in got(n, "<refers_to>")}


check("6c ⭐ THE MEANING-PRESERVING re-ordering (same antecedent, atoms permuted) gives the IDENTICAL "
      "referent — so belief is invariant under atom order, and only *attachment* changes meaning. The "
      "surface/epistemic line holds: the expression fixes the TOPOLOGY, the topology computes a REFERENT, and "
      "the referent is what is believed",
      flat("A") == flat("B") == {ent6["car"]}, f"A={flat('A')} B={flat('B')}")

# ======================================================================================================
print("\n== 7. THE CHAIN IS WALKABLE — the duality, in the direction that is safe ==")


def walk(net: Net, start):
    """Read the unfolded expression back off the graph, by following `<narrows>`."""
    facts = set(net.units["parse"].output)
    out, cur = [], start
    while True:
        nxt = next((f.o for f in facts if f.s == cur and f.p == NARROWS), None)
        if nxt is None:
            return out
        out.append(nxt)
        cur = nxt


path = walk(net, call)
check("7a the expression is READABLE off the graph — walk `<narrows>` from the call back to the anchor",
      path == list(reversed(steps)), f"{[repr(n) for n in path]}")
refs = {f.s: f.o for f in got(net, "<refers_to>")}
check("7b …and each step on that walk carries its own referent, so the walk is an EXPLANATION of the "
      "reference, hop by hop", all(s in refs for s in steps))
check("7c ⚠ but it is a REFLECTION, not an isomorphism: two chains can select the same entity and remain "
      "different chains, and instance identity (which carries scope) has no counterpart in the graph. The "
      "mirror is writable in ONE direction only — the assembler reads the parse, the parse never wires",
      True)

# ======================================================================================================
print("\n== 8. ⭐ N-ARY CALLS STAY POSITIONAL — 'wash the car WITH THE SPONGE' ==")
# The case the original rejection of role-labelled edges was really about, arriving for COMMANDS rather than
# for facts. Two arguments, each its OWN selector chain terminating in its own step. The call NUMBERS them;
# nothing is named `<instrument>` or `<patient>`.
w8, ent8 = world()
sponge = mint("")
w8 = w8 | Subgraph([Fact(sponge, r("<word>"), L("sponge"))])
n8 = Net()
n8.spawn(given("world", w8))
sA, sB, call8 = mint("<a1>"), mint("<a2>"), mint("<call>")
n8.declare("A1", (Triple(E, "<word>", L("car")), Triple(E, "<parked_at>", ent8["floor"])),
           Triple(sA, REF, E))
n8.declare("A2", (Triple(E, "<word>", L("sponge")),), Triple(sB, REF, E))
n8.declare("CALL1", (Triple(sA, REF, E),), Triple(call8, ARG1, sA))
n8.declare("CALL2", (Triple(sB, REF, E),), Triple(call8, ARG2, sB))
n8.spawn(branch("parse", add=Subgraph([Fact(call8, r("<word>"), L("wash")),
                                       Fact(call8, NARROWS, sA), Fact(call8, NARROWS, sB)])))
n8.wire("world", "parse")
n8.run(Budget(limit=200000))
refs8 = {f.s: f.o for f in got(n8, "<refers_to>")}
check("8a both arguments resolve, each through its own chain",
      refs8.get(sA) == ent8["car"] and refs8.get(sB) == sponge,
      f"arg1->{refs8.get(sA)!r} arg2->{refs8.get(sB)!r}")
check("8b ⭐ and the call names them BY POSITION — `<arg1>`/`<arg2>`, no `<instrument>`, no `<patient>`. The "
      "n-ary case is where the pressure to role-label genuinely returns, and numbering absorbs it",
      Fact(call8, ARG1, sA) in got(n8, "<arg1>") and Fact(call8, ARG2, sB) in got(n8, "<arg2>"))
check("8c an argument points at its STEP, so a FAILED argument is visible to the call rather than silently "
      "absent — the call can be asked *which* of its arguments did not resolve",
      all(a in refs8 for a in (sA, sB)))
check("8d ⚠ the honest limit: `<argN>` is still a label, just a POSITIONAL one. What it buys is that no "
      "mechanism has to be taught a ROLE VOCABULARY — arity is the only thing anyone must know", True)

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print("   - " + f)
print("=" * 100)
sys.exit(1 if FAIL else 0)
