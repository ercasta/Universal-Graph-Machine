"""The NO-IMPORT RULE, enforced rather than promised (`docs/design/substrate_inversion.md` §14).

`units/` may not import from `ugm/`. The point is not hygiene — it is that anything the new substrate
needs must be COPIED, and what gets copied is then evidence about what is genuinely shared versus what was
a store-shaped assumption riding along unexamined. A single `from ugm import ...` would make that evidence
unavailable, silently.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
UNITS = ROOT / "units"

_IMPORT = re.compile(r"^\s*(?:from\s+ugm(?:\.|\s)|import\s+ugm(?:\.|\s|$))", re.M)


def test_no_source_level_ugm_import():
    offenders = [p.relative_to(ROOT).as_posix()
                 for p in UNITS.rglob("*.py") if _IMPORT.search(p.read_text(encoding="utf-8"))]
    assert offenders == [], f"units/ must not import from ugm/: {offenders}"


def test_importing_units_does_not_pull_in_ugm():
    """The static check catches the obvious form; this catches the indirect one (a transitive import
    through some shared helper), which is the way the rule would actually be broken."""
    code = ("import units, sys; "
            "print(sorted(m for m in sys.modules if m == 'ugm' or m.startswith('ugm.')))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]", f"importing units pulled in: {out.stdout.strip()}"
