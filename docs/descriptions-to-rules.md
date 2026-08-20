# From descriptions to rules

**Status: designed and measured, not built. This is the brief for its own
session.** Everything below was probed against `5c0a92f`..`0e023cd` on the
engine as it stands; no engine change was made to take any of it.

The subject is the first item in `docs/todo.md`: *instead of `rule <something>:`,
could we use `rule(something, implies(...))` and `action(move(?x,?y))`... this
would make everything be "facts"*. What follows is what that costs and what
stands in its way, in the order the pieces have to be taken.

---

## 1. The theory holds: rules can compile a description into working rules

A corpus can author a live rule with no Python and no engine change. The whole
compiler is five rules and one named fact:

    fact <anchor> = +anchor(?w)

    rule <twin>       = implies( { +lift(?r), +conn(?r, ?c) },
                                 { +rule(+t), +conn(+t, ?c), +twin(?r, +t) } )
    rule <lift-ant>   = implies( { +twin(?r,?t), +anchor(?w), +ant(?r,?p,?s,?i) },
                                 { +ant(?t, holds_in(?w, ?p), ?s, ?i) } )
    rule <lift-con>   = implies( { +twin(?r,?t), +anchor(?w), +con(?r,?p,?s,?i) },
                                 { +con(?t, holds_in(?w, ?p), ?s, ?i) } )
    rule <lift-at>    = implies( { +twin(?r,?t), +at(?side,?r,?i,?m) },
                                 { +at(?side, ?t, ?i, ?m) } )
    rule <lift-names> = implies( { +twin(?r,?t), +names(?side,?r,?i,?n) },
                                 { +names(?side, ?t, ?i, ?n) } )

Given two ordinary domain rules that mention no hypothesis, it authored both
anchored twins, and they chain:

    holds_in(actual, act(replace, pump7))    +
    holds_in(h1, act(replace, pump9))        +
    act(replace, pump9)                      None    containment, by BINDING

⭐ **This retires the cost that killed the anchor shape.** `docs/todo.md` records
*the cost is on EVERY rule ... on 51 of the 72 authored rules* and supersedes
anchors on exactly that. Measured, the cost is five rules paid once, and no
domain rule is touched.

Multi-member antecedents survive: positions carry, and a variable shared across
two members stays one variable.

---

## 2. Three defects, all silent, and one check catches two of them

**The parser refuses a malformed WRITTEN rule. Nothing refuses a malformed
DESCRIBED one.** That is the whole of it, and both faults below are instances:

    a description split across two statements   consequent `?x` unbound  REFUSED
    a compiler that drops the `as` slot         consequent `?n` unbound  REFUSED
    a description in ONE statement (control)    nothing unbound          accepted

`Loader._rule` already applies this check. It has to be applied where rules now
also come from.

⚠ It cannot fire per-write, because a description arrives over several ticks and
is legitimately incomplete in between. **Complete-but-unbindable is an aggregate
over a finished search**, so it belongs at quiescence, beside `blocked` and
`unsupported`.

**The third defect is `adopt`.** Same description, same facts, only the
declaration order of the adopting rule differs:

                      twin facts  adopt asks  ant facts  authored  refusals
    <take> last            1           1          46         1         0
    <take> FIRST           1           1          46         0         0

`_adopt` is an `on_write` hook: it reads at the instant `+adopt` lands, finds
`con` still empty, returns once, records nothing, never retries.

---

## 3. Deposit-as-install: `adopt` is not needed, and it is not what carries
   propose/dispose

Prototyped as one `on_write` hook -- when a describing fact lands, re-read that
rule and install or revise it -- with no `adopt` in the corpus at all:

    suite               641 checks, 2 failing
    wall                15.1s, of which `_read_rule` 0.0s
    reads 461     installs 9     revisions 97     no-revision 36

⭐⭐⭐ Every rule in the suite goes through the round trip and 639 checks pass.
That is a far stronger fidelity test of `_read_rule` than `adopt` has ever had,
and it costs nothing measurable. **The race is gone in both orders.**

Two implementation facts, both silent when wrong:

    the NAME must survive a revision -- `show(node)` is `<a>` where the loader
      called the rule `a`, and re-installing renamed every corpus rule
    revise by MUTATING the Rule, never by re-minting -- a fresh object for the
      same node is one rule in the graph and a twin in Python. Re-minting failed
      two checks comparing `step.applied.rule is r1`; mutating passed them.

What it spends is two checks, and one of them (*adopted while supposing is
REFUSED*) goes with situations anyway. **One property is really at stake:
propose/dispose** -- *a tool only PROPOSES: without the rule that adopts, the
offer is on the record and nothing is live*.

⭐ And `adopt` is not what carries it. An arrival already has that shape:
`_report` writes `arrived(ch, p, sign)`, so a channel uttering a described rule
deposits a claim ABOUT one and a corpus rule must lift it. The hole is the TOOL
boundary -- the `<builder>` answerer writes `rule`/`conn`/`ant`/`con` straight
into the graph.

> **The repair is to put propose/dispose at the boundary a description CROSSES,
> not in a special install request.** A tool that describes a rule should deposit
> under `answered(...)` like every other tool answer. Then `adopt` has nothing
> left to do that a deposit does not do.

---

## 4. Variable identity could be a CLAIM, and today nothing reads it

`Loader.var`: *variables are scoped to a rule -- `?w` in two rules is two
variables, because a rule is a statement and not a fragment of a larger one.*
That is uniform for written and described rules, and there is no asymmetry: a
rule described in ONE statement behaves exactly like a written one.

The engine can already represent two `?w` nodes as one thing -- `Graph.merge`
does congruence over leaves, and a variable is a leaf. What does not follow is
behaviour:

    one shared ?w node                             q(a) = +
    two ?w nodes, no coreference                   q(a) = None
    two ?w nodes, MERGED                           q(a) = None
    two ?w nodes, MERGED, substitute resolving     q(a) = +      <- one line

`substitute` is `bindings.get(pattern, pattern)`, a raw node-id lookup that never
consults `identity_of`. **So the coreference is real in the index and inert in
matching**, and one line would change that.

Why it was never needed, in the design's own words -- *the loader's name table
decides it at intake ... **which is why coreference does not arise in authored
knowledge at all***. ⭐⭐⭐ That premise is exactly what a COMPUTED description
breaks: it is authored knowledge whose identity is not settled at intake.

⚠ Against: `merge` is global and permanent, and variable identity is per-rule.
And `<anchor>` -- sharing by BINDING -- already serves the computed case, with
the parser enforcing it. **On the record as the answer to *why not*, which is
not "the representation cannot express it".**

---

## 5. A rule IS already a subgraph -- and that is where the real blocker is

    <rich> = implies( { +p(?x) at ?mm as ?nn, -b(?x) }, { +q(?nn) } )
    node 1432, relation `implies`, members (1429, 1431)
      antecedent moment -> moment( entry(p(?x), +), entry(b(?x), -) )

Built with `Graph.instance`, which does NOT intern, so two textually identical
rules are two nodes -- which `RuleSet.rule` requires: *two rules that happen to
say the same thing are still two rules*. ⭐ An interning term form could not
express that, which is one reason an explicit constructor is needed at all.

**But it is lossy, and the two kinds of rule are two representations:**

    Python Rule   ant[0] pattern=p(?x) sign=+ locus=?mm binds=?nn
    the subgraph  entry(p(?x), +)                    both slots GONE

    a LOADED rule's node    <compile>   2 members, full structure
    an ADOPTED rule's node  #1554       relation None, 0 members

⚠⚠⚠ And reusing a node leaves both readable forms describing the OLD rule:

    live members  p(?y) => z(?y)
    its subgraph  moment(entry(p(?x), +)) => moment(entry(q(?x), +))
    reified       ant(<r>, p(?x), +, 0)   con(<r>, q(?x), +, 0)

`RuleSet.rule` mints the moments only when `node is None`; `reify` returns early
on a node it has seen. Not reachable today, because `_adopt` declines a live
node -- **reachable the moment revision is allowed**, which deposit-as-install
does.

### If a rule is a subgraph, the slots get SIMPLER

`_reify_locus` keeps the slots separate because *§5 refuses a shape whose arity
varies with how much happens to be known about it*. That argument is about
`ant`/`con`, which have no node for the member and must address it as
`at(SIDE, rule, position, locus)`. **In the subgraph the member IS a node**, so:

    at(<entry>, ?m)        instead of   at(ANT, <rule>, 0, ?m)
    names(<entry>, ?n)     instead of   names(ANT, <rule>, 0, ?n)

...and position stops being an argument at all, because a moment's members are
ordered. `_read_rule`'s sort-by-numeral, the `?i` in every compiling rule, and
the side argument all go.

### ⭐⭐⭐ The blocker: a rule cannot build a node of runtime arity

A moment has one entry per member, and a consequent writes terms whose arity is
fixed at authoring. **That is why `ant(?r, ?p, ?s, ?i)` exists as scattered facts
with position as an ARGUMENT: N ground facts is the only variable-arity thing a
rule can produce.**

> So the reified vocabulary is not a redundant second representation -- it is the
> workaround for a missing constructor. `_rel` earns its place exactly here: to
> make a rule a subgraph, a rule must be able to BUILD one, and that needs a
> constructor taking a relation and a *collection* of members. **Explicit
> composition is the requirement, not a preference.**

⚠ Nothing in the tree has a list or `cons` idiom to build such a collection from.
This is upstream of everything else in this document.

---

## 6. Open: naming a bound node inline

The author's, 2026-08-20, and not yet probed:

    runs(named(paul, ?x=person)) implies moves(?x)

*We currently can't share a node with a given name with this syntax.* The
existing `as` slot (§12's `binds`) names **what a whole member matched**, not a
sub-term of it, and there is no way to attach a name to a node bound inside a
pattern.

⚠ Two readings, and they want different things -- **settle this before
building**:

    (a) a TYPE on the binding: bind `?x`, and constrain it to be a person
    (b) a NAME on the node: bind `?x`, and call this node `person` so another
        statement can refer to the same node

Reading (b) is the cross-statement sharing question of §4 arriving in the
surface notation, and would be an alternative to `<anchor>`.

---

## Order to take it in

    1. the binding check at quiescence          smallest, catches two defects
    2. propose/dispose at the tool boundary     prerequisite for 3
    3. deposit-as-install, retire `adopt`       measured at 639/641
    4. the runtime-arity constructor (`_rel`)   upstream of 5
    5. rule-as-subgraph, one representation     the point of the exercise

⚠ 4 is the one with no design yet. 1-3 are measured and could be taken now.
