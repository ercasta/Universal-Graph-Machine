# KB: Facts and Passes

A Kb contains statements that must hold in our system.

KB:
```
is_a(car, ?x) made_of(?x, wheel, wheel, wheel, wheel) # a car is made of four wheel

is_a(party, dancing(people))
is_rule(?x), is_rule(?y), by(?x, boss), by(?y, vice), overrides(?x, ?y) # rules by boss override rules by vice
is_rule(?x), is_rule(?y), overrides(?x, ?y)
SYNONIM override, overrides   # the two terms are treated as equal by the engine

answer(why(crossed(chicken,road)), because(get(chicken,other side)))
answer((imagine(on(?a,?b), on(?b,?c)), question_is(above(?a,?c))), yes )

transitive(?x), ?x(?a, ?b), ?x(?b,?c), ?x(?a, ?c)

```

From this my system can learn PASSES that COMPLETE the graph; if I MASK some part and try to find a pass that reconstructs it. E.g. mask the first part and try to find it back:

made_of(?x, wheel, wheel, wheel, wheel)

could lead to learn:

pass: [optional name] made_of(?x, wheel, wheel, wheel, wheel) {
    car = MINT "car"
    is_a = MINT "is_a"
    LINK is_a ?x
    LINK is_a car
}


this pass means that if there is a "made_of" node that connects to a given node (?x) and to 4 nodes "wheel", then we create a is_a node

a pass is a program expressed as data. The learning system uses delta and heuristics to find passes e.g. missing link -> add a link, missing node -> add a node.
The learning system runs all the passes it knows (it runs the EVAL ISA, that must do exactly that, it takes a parameter like ?x and runs the applicable rules by looking at what ?x is connected to, e.g. made_of, to find applicable passes), and checks the result. Note that passes are what describes the "open class", and they form a "web". A pass might "learn" to trigger other EVALS.

For optimization reasons the engine shall maintain an index (a web) of what passes are linked to others, the "connective" is the same terms. 

When a pass changes, potentially other passes might need to change to. This is what requires the "harmonization" process

"harmonization" is the process of replaying memories of the episodes and "finding" passes that match.

We can manually bootstrap the KB and then leverage harmonization







