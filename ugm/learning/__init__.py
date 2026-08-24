"""Calibration: search the numbers, never the rules.

An episode is a `.ugm` file holding everything it needs -- the starting
condition and the judge -- so a run is one corpus plus one episode and
nothing else. A mutator changes only what a bracket or an `attend` tail
says. Rule bodies are not touched in this phase, which is why there is no
anti-unification here and no claim to be learning rules.
"""

from .calibrate import Episode, calibrate, fitness, mutate, numbers, run_episode

__all__ = ["Episode", "calibrate", "fitness", "mutate", "numbers",
           "run_episode"]
