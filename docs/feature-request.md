# Feature request

- "want" as a LHS expression i.e. being able to express a "want" with the same language of the LHS queries. To do so: allow nodes to contain snippets of LHS/RHS. and allow the LHS side of a rule to do an eval: eval($x)
- triggers for learning: ALWAYS, NEVER, WANT. i.e. given a scenario, at the end of each tick check something (an LHS-like) is ALWAYS true, NEVER true, or in general consider the episode "successful" if we reach the "want"
- rule alternatives: given a LHS, being able to specify more RHSs; in the LHS line scoring conditions, specify bonuses to the various (numbered) RHS alternatives, and make them authorable / learnable; in this way a rule represents both world model and "agent style"
- Make RHS able to install triggers (a trigger is a normal rule, but it runs AFTER each tick's rule has run, the engine checks it LHS and if matched it runs). Allow the RHS of a trigger to cancel itself 
