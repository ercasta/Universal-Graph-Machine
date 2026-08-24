# The bootstrap

If rules are facts, and applying a rule means checking whether its antecedent
holds, and checking whether something holds is itself something the agent has
to *do* — then reading a rule requires doing work, and if that work is also
made of rules, nothing ever starts.

This chapter states that circle precisely, and shows why the design never
falls into it.

## Only one of four steps could be circular

Applying a rule takes four steps:

| step | what it needs | circular? |
|---|---|---|
| 1. propose candidate rules | **recall** — a function from situation to node ids | no |
| 2. read the rule's structure | members and positions | no |
| 3. check that its antecedent's members hold | **belief lookup** | no |
| 4. commit | the gate, the total step | no |

Step 2 is where it's easy to go wrong. Reading a rule's *structure* is not
reading its meaning: an antecedent is a node with members, and getting at them
needs ordering and nothing else — floor, per Chapter 30.

Step 3 is the one that looks dangerous, because *checking whether X holds* is
exactly the operation a rule's antecedent performs. The reason it doesn't
recurse is `Scratchpad.holds`: one dict lookup. It is not a rule, was never
compiled from rules, and has no rule-level definition standing behind it the
way `Graph.has_var` has `_has_var_slow` (Chapter 30). It is floor by the same
argument that makes matching floor — *checking whether a proposition is
anchored* is exactly the kind of question a read needs answered before it can
do anything else, so it is not implemented as a read.

## Recall runs before any rule has applied

Step 1 is worth demonstrating, because recall is the only component consulted
**before** any rule has applied at all:

```python
kb = load(m, "rule <boil> = implies( { +heat($w) }, { +boiling($w) } )")
about = kb.term("boiling(x)")
m.gate.write(m.g.rel(m.RECALL, about), generic=True)
m.run(limit=5)
```

```
recalled <boil>? True
```

`_answer_recall` (`ugm/core/machine.py`) answers this from `by_conclusion`, an
index kept by conclusion — populated at the moment each rule is authored. It's
a lookup, not a search over the rule set, which is what makes it eligible to
run before any antecedent has been checked.

## Three regresses, one escape

The bootstrap is one instance of a shape this design meets three times:

| regress | what stops it | what stops it is |
|---|---|---|
| reading needs reading | belief is a floor lookup, never a rule | a function |
| selecting needs selecting | the total tiebreak | a function |
| proposing needs proposing | recall | a function |

All three bottom out in **a function, not a search** — the same shape as the
two irreducible floor items in Chapter 30. That recurrence is the strongest
evidence available that the floor is drawn in the right place.

## Rules are ordinary data

`Machine.reify` believes `rule(<R>)` and every member of every side the moment
a rule is authored, which is a write like any other — floor, needing only the
gate and the total step. An agent can author a rule at run time and have it
enter recall and the table on the next tick.

What it cannot do is author a *replacement for the read itself*. The read a
rule performs — `match`, `candidates`, `Scratchpad.holds` — is Python,
permanently, with no rule-level definition standing beside it the way there is
for `has_var`. Promoting it into an ordinary rule would reinstate exactly the
regress described above, so nothing does. That's deliberate, at a real and
named cost: you cannot ask *why did you read it that way* through the same
mechanism you ask *why do you believe that* — see
[what is not built](../horizon/34-not-built.md).

---

**Next:** the number that says whether any of this is true of the implementation.
[Zero phases →](32-zero-phases.md)
