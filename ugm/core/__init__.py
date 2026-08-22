"""The engine: the transitive closure of `machine`, `attention` and `text`.

Nine modules, and nothing outside this package is needed to run an agent. They
layer, and the layering is checked by nothing but this note:

    graph                 no ugm imports at all
    chain, channels       -> graph
    gate, rules           -> chain, graph
    machine               -> chain, channels, gate, graph, rules
    text                  -> chain, graph, machine, rules
    attention             -> the above

 Four pairs are genuinely circular and are broken by imports INSIDE functions
rather than at module level: `machine`/`text`, `machine`/`attention`,
`rules`/`text`. Moving the files into a package did not create
that and does not fix it. It is named here so the layering above is read as what
is TRUE at module level rather than as a claim about the whole package.
"""
