Example: finding a row in a kb.

list the files in the directory
for each file in the directory:
    open the file
    for each row in the file
        check if the row matches the one we wanted


how to get to this plan?


The plan is the sequence of actions, not a raw computation of the rules. The rules manipulate the REPRESENTATION of the plan, and the representation of the plan is not the rules themselves. A plan is a relationship of "do" "x" "expect" "y" FACTS (not LHS and RHS), built starting from rules such as "doing x usually causes y".
The system must FIND FACTS that end with say "usually cause y", and mint a 
"plan"->"x"->"expect"->"y" structure. So we need a FACT MANIPULATING RULE (note that we humans interpret this fact as is a cause-effect describing fact, but the engine happily ignores this because the engine only manipulates this fact via rules, has no actual notion of cause and effect)  , and we can only create this rule manipulating rule if we define the conventional form of rules. We are not EXECUTING the actual rules like "doing x usually causes y". We are READING it and deriving an "inert" representation of the plan. it's "meta".

and in general i think we have been conflating this also for other kind of business rules. 
THE ONLY RULES THAT CAN BE "EXECUTED" ARE INFERENCE RULES. "if a, then b" as an INFERENCE rule can be applied (LHS, RHS) "as is" on the graph nodes. 

"order over 500k must be shipped early" is not an inference rule. It's a fact. It needs a "meta" rule that finds an "order over 500k" and does not brutally produce "must be shipped early", it produces "REQUIRES shipping early"; then the agent must use "meta rules" to find things that REQUIRE something, and find other rules that specify how to satisfy this, like "REQUIRES shipping early -> <call>(fast_shipping)(order).
We have been working with "mechanical" LHS - RHS rules, but these rules represent transformations of the graph representation; they DO NOT represent business rules that define relationships or procedures about the world. 

