# `compose.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Composition, measured (§4, §19, §21).

    Compilation makes a step cheaper. Composition makes the step unnecessary.

§4 argues composition is the larger lever because it is **algorithmic** where
compilation is a constant factor, and because the artifact is a node rather than
an opaque blob. This runs it.

    python -m ugm.probes.compose

Two things are measured and three are checked:

* how many selections a chain of length n costs, composed against uncomposed;
* whether the composed rule concludes the same thing;
* whether a rule that **defeats** a constituent still defeats the composition --
  §21's *a shortcut that has outlived its guards*, which here arrives at once
  rather than after a context change;
* ⚠⚠⚠ whether composing **across a `causes`** is refused. It flattens two
  moments into one antecedent, so the second rule's other premises are demanded
  a moment early -- measured, the derivation reaches its conclusion and the
  composite does not. *n steps become one* has to mean **with the same
  conclusion**, so the unsound shape is declined rather than approximated.

## `_causes_boundary`

Is the unsound composition refused, and is the refusal exact? (§4, §14)

    ⚠⚠⚠ A `causes` consequent lands in a SUCCESSOR, so the second rule's other
    premises are read where the first rule's effect holds -- one moment after
    the first rule's own premises. Flattening asks for all of them together,
    which is a stricter question, and the discriminating world is one where the
    extra premise only appears once the first rule has acted:

        <a> = causes(  { +p($x) },         { +q($x) } )
        <b> = implies( { +q($x), +r($x) }, { +s($x) } )
        <late> = implies( { +q($x) }, { +r($x) } )      -- r arrives WITH q

    Measured before the guard existed: the derivation reaches `s` and the
    composite does not. Under-derivation is the safer direction and is still a
    violation of *n steps become one **with the same conclusion***; an
    over-derivation was looked for and not found, which is not the same as
    impossible.

    ⭐ It also retires the question this was reached from. *Which connective
    should a mixed composition get* was the wrong question -- the real one is
    that some compositions must not happen. Once those are refused the
    connective is FORCED: a chain crossing a causal step has advanced a moment,
    so the result is `causes`.
