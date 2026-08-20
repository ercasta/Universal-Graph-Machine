"""Where the `.ugm` corpora live, as one accessor rather than seven.

    from .corpora import path          # inside `ugm/`
    from ..corpora import path         # inside `ugm/core`, `ugm/probes`, ...

⚠⚠⚠ **Seven modules used to compute this themselves**, each with its own
`os.path.join(os.path.dirname(__file__), "rules", name)`. That works exactly
while every one of them sits directly in `ugm/`, and breaks silently the moment
one moves into a subpackage -- `dirname(__file__)` follows the MODULE, and the
corpora do not move with it. Splitting the tree into `core/`, `learning/`,
`gates/` and `probes/` is precisely that move, so the computation is done once,
here, next to the data.

⚠ `ugm/rules/` is the directory of corpora and `ugm/core/rules.py` is the rule
engine. They used to be `ugm/rules/` and `ugm/rules.py` -- a package and a
module with one name, where Python resolves the module first and nothing says
so. The split ended that collision as a side effect; this file is what makes the
remaining name unambiguous at every call site.
"""

import os

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def path(name: str) -> str:
    """The absolute path of a shipped corpus, by file name."""
    return os.path.join(DIR, name)
