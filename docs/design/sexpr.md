# `core/sexpr.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A second surface: s-expressions, beside the default notation.

    python -m ugm.core.sexpr

⭐ **A surface is a reader, not the language.** The graph is the truth and
`docs/rules-design.md`'s notation is one way of writing it down; nothing in the
substrate knows which notation a node was authored in. So a second reader costs
a parser and nothing else -- `Loader.build`, the name scope, the gate and every
check downstream are untouched, because both readers produce the same AST.

Two ways to ask for it, and they are the same reader exposed twice:

    syntax: lisp              as the first line -- the whole document
    lisp: (fact + (on a b))   as a statement    -- one statement, inside a
                                                   document in the default
                                                   notation

The default is unchanged and stays the default. Every corpus that parsed before
this module existed parses identically, because nothing dispatches unless one of
those two markers is present.

## Why it earns its place, beyond taste

⭐⭐⭐ **Two readers are each other's check.** The same corpus written both ways
must build the identical graph -- same nodes, same order, same renderings -- and
that is a far stronger statement about a parser than any set of examples. A
differential oracle over notations is what `main()` runs.

And the s-expression form reaches two shapes the default notation cannot say,
because in `(f a b)` the head is a term like any other rather than a name token:

    ((a b) c)     a composed with b, applied to c -- now sayable in both, but
                  native here rather than a loop bolted onto head-plus-args
    (moment)      a relation instance with NO members, which `show` prints as
                  `moment()` and the default parser refuses

⚠ The second is why the capability lives HERE rather than in the default
notation. `a` and `(a)` are different nodes -- an atom and a zero-member
instance -- and adding that distinction to the default notation would add a twin
trap this repo has already recorded six times. In a notation whose whole point is
that parentheses mean application, it is not a trap but the rule.

## The grammar

    statement := ( fact  sign term )        |  ( fact  <name> term )
               | ( fact  sign <name> )      |  ( say channel sign term )
               | ( rule  <name> connective ( member... ) ( member... ) )
    member    := ( sign term )  |  term          -- a bare term is `+`
    term      := name | $var | <rulename> | ( term... )

A list's first element is its relation and the rest are its members, which is
exactly what a node is (§3). `(a)` has a relation and no members; `a` is an atom,
which has neither.

## The AST the default notation produces, whereve

⭐ The AST the default notation produces, wherever the shapes coincide.
A leaf head with arguments is `Term(head, args)` -- byte-identical to
what `a(b, c)` parses to -- so everything downstream that reads
`term.head` (spotting `forbidden`, the reserved-name shadow check) sees
exactly what it always has. Only the two shapes the default notation
cannot write take the `fn` form.
⚠⚠⚠ The head must be a LEAF to fold into `Term(head, args)`. Testing
only `head.fn is None` was wrong and silently wrong: `((a b) c)` has a
head that is itself `Term("a", (b,))`, and folding took its `head`
string while throwing its arguments away -- so it read as `a(c)`, a
perfectly valid node nobody wrote. The one check that caught it was
the one comparing against a rendering.
