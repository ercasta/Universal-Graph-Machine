"""A map of a corpus: what can be inferred from what, and what never can.

    python -m ugm.probes.atlas <corpus.ugm> [--mermaid]

<corpus.ugm> [--mermaid] ugm.vocabulary asks whether a NAME has a web. This
asks the same question of the whole corpus and one step further out: which
relations can ever be established, and therefore which rules can ever apply. ⚠
It is a static over-approximation, and saying which direction matters.

See docs/design/atlas.md.
"""

import sys
from typing import Dict, List, Optional, Set, Tuple

from ..core.machine import Machine
from ..core.text import load_file


def _rel(m: Machine, pattern) -> Optional[str]:
    r = m.g.relation_of(pattern)
    return None if r is None else m.g.show(r)


def grounded_by_facts(m: Machine) -> Set[str]:
    """Relations some entry already claims -- the corpus's own facts, whatever
    the machinery deposited, and anything a channel delivered."""
    out: Set[str] = set()
    for mo in m.chain.moments:
        for e in mo.delta:
            r = _rel(m, e.proposition)
            if r is not None:
                out.add(r)
    return out


def reachable(m: Machine, rules) -> Tuple[Set[str], List]:
    """The fixpoint: what can be established, and which rules stay dead.

    ⭐ Monotone and built from BELOW, which is the same discipline `RuleSet.
    skeleton` uses to derive the strata: a relation is reachable only because
    something already grounded makes it so, so a ring of rules concluding about
    each other adds nothing and cannot bootstrap itself into looking live.
    """
    have = grounded_by_facts(m) | set(m.reserved)
    live: Set[int] = set()
    anything = False
    changed = True
    while changed:
        changed = False
        for i, r in enumerate(rules):
            if i in live:
                continue
            need = {_rel(m, x.pattern) for x in r.antecedent}
            need.discard(None)
            if need <= have:
                live.add(i)
                for x in r.consequent:
                    # ⚠⚠⚠ A bare-variable consequent concludes ANYTHING, and
                    # every corpus that believes what it is told has one.
                    # →
                    # docs/design/atlas.md#a-bare-variable-consequent-concludes-anyth
                    if m.g.is_var(x.pattern):
                        anything = True
                        continue
                    got = _rel(m, x.pattern)
                    if got is not None and got not in have:
                        have.add(got)
                changed = True
    if anything:
        # Nothing can be shown unreachable, and saying so is the answer. The
        # alternative -- reporting the dead rules anyway -- is a list that is
        # wrong exactly where a corpus is most ordinary.
        return have, []
    return have, [r for i, r in enumerate(rules) if i not in live]


def concludes_anything(m: Machine, rules) -> List[str]:
    """Rules whose consequent is a bare variable, so they can conclude anything.

    Reported rather than silently worked around: it is why the checks above go
    quiet, and an author is owed the reason. `<denial>` and `<assert-act>` are
    the bundle's own, deliberately; a corpus's trust rule is the common case.
    """
    return [r.name or str(r.node) for r in rules
            if any(m.g.is_var(x.pattern) for x in r.consequent)]


def chains(m: Machine, rules) -> Dict[str, List[Tuple[str, List[str]]]]:
    """For each relation a rule concludes: which rule concludes it, from what.
    This is the web as edges rather than as a set -- the inferential chains."""
    out: Dict[str, List[Tuple[str, List[str]]]] = {}
    for r in rules:
        src = sorted({x for x in (_rel(m, y.pattern) for y in r.antecedent) if x})
        for x in r.consequent:
            got = _rel(m, x.pattern)
            if got is not None:
                out.setdefault(got, []).append((r.name or str(r.node), src))
    return out


def mermaid(m: Machine, rules, have: Set[str]) -> str:
    """The map, as something that can be looked at.

    ⚠ Rendered rather than printed because a corpus of any size is a graph and a
    list of edges is not a map -- the whole point of asking for one is to see
    which way the arrows run.
    """
    lines = ["graph LR"]
    seen: Set[str] = set()
    facts = grounded_by_facts(m)
    for r in rules:
        src = sorted({x for x in (_rel(m, y.pattern) for y in r.antecedent) if x})
        dst = sorted({x for x in (_rel(m, y.pattern) for y in r.consequent) if x})
        for a in src:
            for b in dst:
                lines.append(f"  {a} -->|{r.name or 'rule'}| {b}")
                seen |= {a, b}
    for n in sorted(seen):
        if n not in have:
            lines.append(f"  {n}:::dead")
        elif n in facts:
            lines.append(f"  {n}:::given")
    lines.append("  classDef given fill:#dfd,stroke:#393")
    lines.append("  classDef dead fill:#fdd,stroke:#933")
    return "\n".join(lines)


def links(m: Machine, rules) -> Set[frozenset]:
    """A rule joins every relation it READS to every relation it WRITES.

    ⚠ A relation joined only to ITSELF is not joined: `{+p($x)} ⟹ {+p($y)}`
    gives `p` no meaning it did not have, because meaning is being connected to
    something else. So self-links are dropped rather than counted.
    """
    out: Set[frozenset] = set()
    for r in rules:
        src = {_rel(m, x.pattern) for x in r.antecedent}
        dst = {_rel(m, x.pattern) for x in r.consequent}
        for a in src - {None}:
            for b in dst - {None}:
                if a != b:
                    out.add(frozenset((a, b)))
    return out


def islands(nodes: Set[str], es: Set[frozenset]) -> Tuple[List[Set[str]], Dict[str, Set[str]]]:
    """The connected components of the web, and its adjacency.

    ⭐⭐⭐ **The web of meaning is islands joined by bridges, not a dense mesh** --
    predicted before it was measured, and measured: two domains and the agent's
    own apparatus in one machine give **43 relations, 37 links, density 0.041**,
    in **nine** islands. A domain's special terminology clusters; the common
    terminology is what holds the clusters together.

    ⚠ `worked.ugm` reports **two** islands, and that is the measure being right
    about something known independently: the file is two unrelated worked
    examples, a kettle and some rain.
    """
    adj: Dict[str, Set[str]] = {n: set() for n in nodes}
    for e in es:
        a, b = tuple(e)
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen: Set[str] = set()
    comps: List[Set[str]] = []
    for n in sorted(nodes):
        if n in seen:
            continue
        stack, group = [n], set()
        while stack:
            c = stack.pop()
            if c in group:
                continue
            group.add(c)
            seen.add(c)
            stack.extend(adj[c] - group)
        comps.append(group)
    return comps, adj


def bridges(nodes: Set[str], adj: Dict[str, Set[str]]) -> List[str]:
    """Relations whose removal breaks the web into more pieces -- the terms that
    hold two bodies of knowledge together, and therefore the load-bearing ones.

    Measured across two domains plus the bundle, and the split is the one worth
    seeing: each domain's own hubs (`disrupted`, `owed`, `amount`; `likely`)
    alongside the agent's COMMON vocabulary (`says`, `did`, `goal`, `subgoal`,
    `verdict`) -- which is what a bridge between domains is made of.
    """
    def count(ns: Set[str]) -> int:
        es = {frozenset((a, b)) for a in ns for b in adj.get(a, ()) if b in ns}
        return len(islands(ns, es)[0])
    base = count(nodes)
    return [n for n in sorted(nodes) if count(nodes - {n}) > base]


def latent_conflicts(m: Machine, rules) -> List[Tuple[str, str]]:
    """Pairs of the corpus's own rules that could conclude opposite signs of one

    thing -- the offline half of harmonization. ⚠⚠⚠ Filtered to a SPECIFIC
    unifier, and that filter is the whole instrument.

    See docs/design/atlas.md#latent-conflicts.
    """
    from ..core.rules import rename, unify_patterns
    g = m.g
    # A rule already taken out of the running is not a live conflict.
    asleep = {r.node for r in rules
              if m._claims(g.rel(m.DORMANT, r.node))}
    out: List[Tuple[str, str]] = []
    for i, r1 in enumerate(rules):
        for r2 in rules[i + 1:]:
            for c1 in r1.consequent:
                for c2 in r2.consequent:
                    if c1.sign == c2.sign or "?" in (c1.sign, c2.sign):
                        continue
                    if g.is_var(c1.pattern) or g.is_var(c2.pattern):
                        continue  # a bare variable fights everything
                    a, b = rename(g, c1.pattern, {}), rename(g, c2.pattern, {})
                    if unify_patterns(g, a, b) is None:
                        continue
                    if r1.node in asleep or r2.node in asleep:
                        continue  # an author already took one of them out
                    pair = (r1.name or str(r1.node), r2.name or str(r2.node))
                    if pair not in out:
                        out.append(pair)
    return out


def survey(m: Machine, rules, label: str = "", show_mermaid: bool = False) -> List[str]:
    """The whole report for one corpus, as lines. Returns the problems found."""
    have, dead = reachable(m, rules)
    facts = grounded_by_facts(m)
    web = chains(m, rules)
    problems: List[str] = []

    print(f"  {len(rules)} rules, {len(web)} relations concluded, "
          f"{len(facts - set(m.reserved))} asserted as facts")
    print()

    # The chains, deepest first: what rests on what.
    print("  what is concluded, and from what")
    for got in sorted(web):
        for name, src in web[got]:
            mark = " " if got in have else "x"
            print(f"   {mark} {got:22} <- {', '.join(src) if src else '(nothing)'}"
                  f"   [{name}]")
    print()

    wild = concludes_anything(m, rules)
    missing = [] if wild else sorted(m.unwebbed(rules))
    if missing:
        problems.append(f"nothing writes {', '.join(missing)}")
    print(f"  names read and never written : {missing if missing else 'none'}"
          f"{'   (undecidable -- see below)' if wild else ''}")

    if dead:
        for r in dead:
            need = sorted({x for x in (_rel(m, y.pattern) for y in r.antecedent) if x})
            gap = [n for n in need if n not in have]
            problems.append(f"<{r.name or r.node}> can never apply (needs {gap})")
        print(f"  rules that can NEVER apply   : "
              f"{[r.name or r.node for r in dead]}")
    else:
        print("  rules that can NEVER apply   : none")

    # -- the shape of the web ---------------------------------------------
    nodes = {x for r in rules
             for y in list(r.antecedent) + list(r.consequent)
             for x in [_rel(m, y.pattern)] if x}
    es = links(m, rules)
    comps, adj = islands(nodes, es)
    density = (2 * len(es)) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
    print(f"  the web                      : {len(nodes)} relations, {len(es)} "
          f"links, density {density:.3f}, {len(comps)} island(s) "
          f"{sorted(len(c) for c in comps)}")
    alone = sorted(next(iter(c)) for c in comps if len(c) == 1)
    if alone:
        # ⚠⚠⚠ **`not` will appear here and is a false positive**, which is the
        # bare variable distorting a measurement for the third time. `<denial>`
        # concludes `-$p` -- a bare variable, with no relation to draw a link to
        # -- so `not` looks joined to nothing while it is in fact joined to
        # everything the agent can deny.
        print(f"  joined to nothing else       : {alone}"
              f"{'   (undecidable -- see below)' if wild else ''}")
        # ⚠ A rule concluding a bare variable draws no edge, because there is no
        # relation on its consequent to draw one to -- so the term it reads looks
        # isolated while it is in fact joined to everything the agent can be told.
        problems += [f"{n} is in the corpus and joined to nothing else"
                     for n in alone if n != "not" and not wild]
    span = bridges(nodes, adj)
    print(f"  terms holding it together    : {span if span else 'none'}")
    if wild:
        # ⚠ ASCII only in what is PRINTED -- this goes to a console whose
        # encoding is the platform's, and a mark it cannot encode turns the
        # whole report into a traceback. Second time today.
        print(f"  concludes ANYTHING           : {wild} -- a rule whose "
              f"consequent is a bare variable can conclude any proposition, so "
              f"nothing here can be shown unreachable. Every corpus that "
              f"believes what it is told has one.")

    # ⚠ Printed apart from the problems above, and not counted as one: a latent
    # conflict is a QUESTION for an author -- the two antecedents may never hold
    # together -- where a dead rule is a defect whatever else is true.
    fights = latent_conflicts(m, rules)
    print(f"  pairs that could disagree    : "
          f"{[f'{a} vs {b}' for a, b in fights] if fights else 'none'}"
          f"{'   (nobody has said who wins)' if fights else ''}")

    if show_mermaid:
        print()
        print("```mermaid")
        print(mermaid(m, rules, have))
        print("```")
    return problems


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    want_mermaid = "--mermaid" in argv
    argv = [a for a in argv if a != "--mermaid"]
    if not argv:
        # ⚠ A short line rather than the module docstring: this prints to a
        # console whose encoding is the platform's, and the docstring is full of
        # marks that a cp1252 terminal cannot encode -- so printing it turned
        # `--help` into a traceback.
        print("python -m ugm.probes.atlas <corpus.ugm> [--mermaid]")
        print("no corpus given, so here are the ones in this repository:")
        argv = ["ugm/rules/delay.ugm", "ugm/rules/worked.ugm"]

    problems: List[str] = []
    for path in argv:
        m = Machine()
        before = {r.node for r in m.rules.rules}
        try:
            load_file(m, path)
        except Exception as exc:
            # ⚠ A corpus that registers TOOLS cannot be loaded from its text
            # alone -- `ugm/rules/dungeon.ugm` names three answerers its host
            # installs -- so the map is available to a host that has built the
            # machine, and the command line reaches only self-contained corpora.
            # Reported rather than swallowed: a map that silently skipped what it
            # could not read would be a clean bill of health for nothing.
            print(f"\n{path}: will not load on its own -- {str(exc)[:70]}")
            print("  (a corpus that registers tools needs its host; call "
                  "`atlas.survey(machine, rules)` from there)")
            problems.append(f"{path} needs its host to be mapped")
            continue
        m.run(limit=300)
        rules = [r for r in m.rules.rules if r.node not in before]
        print()
        print(f"{path}")
        problems += survey(m, rules, path, want_mermaid)

    print()
    for p in problems:
        print(f"  FOUND  {p}")
    print(f"{len(problems)} problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
