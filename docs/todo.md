 I have two changes to propose, let's decide whether to do this now or later. One is syntactical: instead of rule <something>:, could we use rule(something,implies(...)) and rule(something,causes(...))? Same
  for actions: action(move(?x,?y)) where in this case ?x and ?y mean they will be bound at runtime. This would make everything be "facts". The second change is more significative. Right now we have some
  things automatically done by the engine like saving short term memory. What if we have multiple experts active in parallel, where "parallel" actually means there is an "outer loop" that make them act in a
  specific order; in particular we could have an "expert" dedicated to memorizing things, or do "accessory" work, with a separate "attention" table 
