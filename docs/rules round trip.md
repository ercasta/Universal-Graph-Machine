# Rules round trip.

The RHS of a rule is a microprogram. If we represent it in the graph with its ast, and we have rules that "read" the ast, and do the reverse, then we can "read" the rules and also write them back:


`$y.label = "Runs" [+7]`, written in the graph as:

assign(label($y),"runs",attention(+7))

is the "reading" of the rule

And then for simplicity we could have a "read" function that reads the graph representation.


Better yet: we don't need to "read" rules in reverse. We need to build a "reverse association". 

x causes y.... want y -> want x

It's all system 1.

Also: a veto or prohibition must iterate all the rules that create an action, an mark them as forbidden. (Maybe)






