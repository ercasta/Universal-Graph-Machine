- Maybe we don't need "attention", but we need triggers and timers. "attention" is just passing a specific node to whatever we want to process.

- "Expert rules" must be <criteria> (set of constraints) -> (list of) goal(s)/subgoal(s) or <criteria> -> (list of) action(s). Planning is a goal/subgoal. The first step of these list could be "discard current goal stack" 

- Actions are tool calls. Some tools operate OUTSIDE of the system (can have side effects), other operate INSIDE, e.g. a calculator. In general the distinction is having or not side effects in the world. A calculator, specifically, might be a utility we could use even during planning, without having to implement arithmetics in rules.


- Users should not write functions. Functions is what CNL must lower to, with weaving and all the rest. We need to provide a CNL way to express functions without low level ISA.

- The strength of the system is the computation model: adapts on divergence. This is made possible by the "outer loop" that does not blindly follow a program. A program would require ifs everywhere to adapt

- Even immediate actions must be plans; one step plans, but nevertheless plans, with their own expectations

- We need "dynamic" attributes; like types, they are assigned by constrains. for the block example: a is clear if there is nothing on top of it. We can create "rules" used on read, keyed by attributes. It's like having getters that derive their return value by exploring the world. Alternatively we can also cache the values and apply reverse keying triggers to change them, or at least dirty markers - but this can't always be perfect, so it could be that recomputation is triggered only on explicit asking, not every read (but this could be unsafe). Relying on pure recomputation on read could also lead to loops in case of malformed rules. One practical way could be recomputing attrs after nodes are touched, with an automatic set of "triggers" installed by the system.
