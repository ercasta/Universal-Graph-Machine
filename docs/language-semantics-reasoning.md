# Language, semantics, and reasoning

## Language (form)

- Superficial form
- Can vary from country to country
- We don't care about natural language
- We can use a CNL


## Semantics (meaning)

"meaning". Quine says meaning of a thing can be expressed only in relation to other things. This means: be prepared to work with things that only work if they are together (e.g. coinductive)

There are many semantics, e.g.:
- Denotation: e.g. top means there is nothing higher 
- Cause - effect: fast means takes less time to move from a to b
- Constraints: x has more authority than y means orders by x must have precedence over orders by y

Other examples: taking turns means a goes, then b goes, then c goes.


- Our KB contains semantics
- Of course we need a form (language) to express semantics

## Reasoning (operations)

Use the various semantics (manipulate them) to perform things such as:
- planning
- explaning "why something happened"
- recognizing things e.g. x takes short time to go from a to b -> fast 
- checking / confirming (e.g. constraints)

IMPORTANT: operations need to explicitly support the various CATEGORIES of semantics, otherwise they can't use them. And the operations supported by the system are a finite set, not an arbitrary number; but they need to compose (e.g. recognition happens during planning)

# UGM 

Ugm is a system with a specific CNL that allows expressing a defined set of semantics, and instances of them (via the KB), and performing a finite set of reasonings on them.



