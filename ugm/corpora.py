"""Where the `.ugm` corpora live, as one accessor rather than seven.

from .corpora import path # inside ugm/ from ..corpora import path # inside
ugm/core, ugm/probes, ...  Seven modules used to compute this themselves,
each with its own os.path.join(os.path.dirname(__file__), "rules", name).

See docs/design/corpora.md.
"""

import os

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def path(name: str) -> str:
    """The absolute path of a shipped corpus, by file name."""
    return os.path.join(DIR, name)
