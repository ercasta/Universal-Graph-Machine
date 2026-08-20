"""Floor gates: RELEASE CRITERIA, not findings.

Each holds a fast implementation to the slow definition of the same thing, over
a path the loop actually takes. They are the modules that must be green to ship,
which is what separates them from `probes` -- a probe that goes red has
discovered something, a gate that goes red is a regression.

⚠ 20l retired three instruments for measuring a path nothing executed. A gate
over a dead path measures nothing and reads exactly like one that passes, so the
question *does the loop still take this path* belongs to every module here.
"""
