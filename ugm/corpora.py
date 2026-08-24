"""Where the `.ugm` corpora live, as one accessor rather than seven.

from .corpora import path # inside ugm/ from ..corpora import path # inside
ugm/core, ugm/probes, ...  Seven modules used to compute this themselves,
each with its own os.path.join(os.path.dirname(__file__), "rules", name).

See docs/design/corpora.md.
"""

import os
from typing import List

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def path(name: str) -> str:
    """The absolute path of a shipped corpus, by file name."""
    return os.path.join(DIR, name)


def folder(name: str) -> List[str]:
    """Every `.ugm` file directly under `ugm/rules/<name>/`, sorted by file
    name -- so an entry point can load "whatever is in this folder" and a
    corpus dropped in later is picked up on the next run, no code edited
    to name it. Sorted rather than directory order, for the same reason
    `run` is deterministic: two runs of one machine should not depend on a
    filesystem's own listing order."""
    d = os.path.join(DIR, name)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith(".ugm")]
