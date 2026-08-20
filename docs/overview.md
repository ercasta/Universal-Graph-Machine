# Overview

The system works in a very simple way. It's a loop: look at the current state, decide what to do next. This simplicity hides where the real complexity is: "decide what to do next" is actually the hard part.

Let's go from the beginning. First of all, the "system" is an "almost empty" engine. The engine has no "decision rules" embedded; it only knows the conventional representation of some concepts, and this is for performance reason and to provide mechanisms like "short term memory" independently of all the decision rules.

We speak about rules because, to accomplish anything, it needs a knowledge base, and a competence base over it. The knowledge base is actually the "world model": it specifies how things relate to each other, inference rules, cause-effects relationships. It also specifies what actions can be performed over this world model.

Then there is competence. In any non-trivial world model, there are lots of possible actions to perform; if you consider actions can be parametric, the actual actions you can perform are a very high number. So how does the system decide? 

Enter competence

Besides the world model, authors can provide competence, i.e. "what to do" in given situation. Imagine having to solve a Hanoi Tower or a Rubik's cube: you can have perfect knowledge of the model (how they work, i.e. what happens when you move something) and still be completely clueless about how to solve them. Competence fills this gap.

Learning

Competence can be provided by authors as a starting point. But the system has the possibility to improve its competence via learning mechanisms.

What the system offers:
transparent, ownable, explainable, private reasoning over KBs