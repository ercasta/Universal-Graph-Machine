"""The engine: the transitive closure of `machine`, `attention` and `text`.

Eight modules, and nothing outside this package is needed to run an agent.
They layer, and the layering is checked by nothing but this note:

    graph                   no ugm imports at all
    scratchpad, channels    -> graph
    gate, rules             -> graph, scratchpad
    machine                 -> channels, gate, graph, rules, scratchpad
    text                    -> graph, machine, rules
    attention               -> the above

Three pairs are genuinely circular and are broken by imports INSIDE functions
rather than at module level: `machine`/`text`, `machine`/`attention`,
`rules`/`text`. Moving the files into a package did not create that and does
not fix it. It is named here so the layering above is read as what is TRUE at
module level rather than as a claim about the whole package.

`chain` was here, and it was the biggest module in this list after `machine`.
It held the history -- moments, entries, signs, licences, support -- and belief
was a VIEW computed over it: *the last claim about this proposition wins*. The
graph is now the state itself, `scratchpad` is the two lines that say what that
means, and the read is a dict lookup rather than a walk.
"""
