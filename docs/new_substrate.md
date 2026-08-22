# New substrate

The new substrate adds entities as first class citizens, and modifies the syntax to allow expressing concepts precisely.

nodes in the graph can point to entities. 

"Paul" points to an entity. *Paul is the entity the "paul" node points at.

Aliases can be created for denotational expressions. If declared, the engine must be able to use them interchangeably (potentially computing a canonicalization):

Brother_in_law($x) = brother(wife($x))

To get to the enity:

*(Brother_in_law($x))

$x denotes an entity.

Relationships are entities. $y($x, $z) :  $y is a relationship i.e. a node pointing to entities $x and $z. it can also be written as:
$y[0] = $x
$y[1] = $z

We can attach "meaning" to relationships (note: we have the "loves" pointing to the entity $y):

&($y)=loves

so $y represents $x loves $z.

# Representing verbs and time

"Paul is running" = there is a relationship between "paul" and "run" and the "current moment". 


"A glass ball shatters if it crashes" -> there is a "causes" relationship between the relationship between "crash" and "ball" and a "moment" and "shatter", the same "ball" and another "moment", and a "future" relationship between the two moments


