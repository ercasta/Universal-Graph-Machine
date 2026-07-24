"""
Fetcher for the EXTERNAL reasoning corpora used by the discourse-corpus experiment.

These are third-party research datasets with THIRD-PARTY LICENSES, so they are downloaded on
demand into a gitignored directory (`data/corpora/`) rather than vendored into the repo. Every
download records provenance (URL, sha256, retrieval date, license as we understand it) into
`data/corpora/PROVENANCE.json` and a human-readable `data/corpora/LICENSES.md`, so a later
reader can tell where a file came from and what may be done with it.

Stdlib only (the package declares zero dependencies) — urllib, no `requests`.

Usage:
    python bench/fetch_corpora.py --list          # show sources + licenses, download nothing
    python bench/fetch_corpora.py                 # fetch every source
    python bench/fetch_corpora.py --only fracas   # fetch one (repeatable)
    python bench/fetch_corpora.py --force         # re-download even if present

LICENSE SUMMARY (read `--list` output for the full statements; verify before redistributing):
  * fracas          — public domain (MacCartney's XML rendering), attribution requested. VENDORABLE.
  * proofwriter     — CC BY 4.0 (AI2). VENDORABLE with attribution.
  * commitmentbank  — NO stated license. NOT vendorable; fetch-only, do not commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "data" / "corpora"

UA = "ugm-bench-fetch/1.0 (research use; https://github.com/)"


class Source:
    def __init__(self, name, why, files, license_id, license_note, homepage, citation,
                 vendorable):
        self.name = name
        self.why = why                    # what phenomenon it stresses, for us
        self.files = files                # [(url, relative_path)]
        self.license_id = license_id
        self.license_note = license_note  # verbatim-ish statement + where we read it
        self.homepage = homepage
        self.citation = citation
        self.vendorable = vendorable      # may it be copied INTO this MIT repo?


SOURCES = [
    Source(
        name="fracas",
        why="346 hand-built inference problems, 9 phenomenon sections (quantifiers, plurals, "
            "anaphora, ellipsis, adjectives, comparatives, temporal reference, verbs, ATTITUDES). "
            "Gold is three-valued (yes/no/unknown) — matches our honest UNKNOWN. The primary "
            "source for the discourse corpus.",
        files=[
            ("https://nlp.stanford.edu/~wcmac/downloads/fracas.xml", "fracas/fracas.xml"),
            ("https://nlp.stanford.edu/~wcmac/downloads/fracas-problems.dtd",
             "fracas/fracas-problems.dtd"),
            ("https://nlp.stanford.edu/~wcmac/downloads/fracas-problems-to-html.xsl",
             "fracas/fracas-problems-to-html.xsl"),
        ],
        license_id="public domain (attribution requested)",
        license_note=(
            "Problems created by the FraCaS Consortium (1996). The XML rendering is Bill "
            "MacCartney's; his download page states: \"This page contains links to stuff I'm "
            "putting in the public domain. If you use my stuff, please give me credit as "
            "appropriate.\" (read from https://nlp.stanford.edu/~wcmac/downloads/, 2026-07-24). "
            "The 1996 originals carry no separate license notice we could find; they have been "
            "redistributed freely in the research literature for ~30 years."
        ),
        homepage="https://nlp.stanford.edu/~wcmac/downloads/",
        citation="Cooper et al. (1996), Using the Framework (FraCaS Deliverable D16). "
                 "XML rendering by Bill MacCartney.",
        vendorable=True,
    ),
    Source(
        name="proofwriter",
        why="Depth-stratified synthetic theories (facts + if/then rules) with entailment "
            "questions under CWA/NAF. Already wired in bench/proofwriter_coverage.py, which "
            "currently reads a zip from a scratchpad path — point it here instead.",
        files=[
            ("https://aristo-data-public.s3.amazonaws.com/proofwriter/"
             "proofwriter-dataset-V2020.12.3.zip", "proofwriter/proofwriter-dataset-V2020.12.3.zip"),
        ],
        license_id="CC BY 4.0",
        license_note=(
            "Allen Institute for AI releases the ProofWriter dataset under CC BY 4.0 "
            "(https://allenai.org/data/proofwriter). Attribution required; redistribution and "
            "modification permitted."
        ),
        homepage="https://allenai.org/data/proofwriter",
        citation="Tafjord, Dalvi Mishra, Clark (2021). ProofWriter: Generating Implications, "
                 "Proofs, and Abductive Statements over Natural Language. Findings of ACL 2021.",
        vendorable=True,
    ),
    Source(
        name="commitmentbank",
        why="1,200 naturally occurring discourses whose final sentence embeds a clause under an "
            "entailment canceller (negation, question, modal, conditional antecedent), 48 "
            "predicates, GRADED speaker-commitment judgements. The empirical counterpart of our "
            "scope-crossing rule; pairs with the banded layer, not the crisp one.",
        files=[
            ("https://raw.githubusercontent.com/mcdm/CommitmentBank/master/CommitmentBank-All.csv",
             "commitmentbank/CommitmentBank-All.csv"),
            ("https://raw.githubusercontent.com/mcdm/CommitmentBank/master/"
             "CommitmentBank-items.csv", "commitmentbank/CommitmentBank-items.csv"),
        ],
        license_id="NONE STATED — treat as all-rights-reserved",
        license_note=(
            "The repository github.com/mcdm/CommitmentBank has no LICENSE file and the README "
            "states only a citation (checked 2026-07-24; a 2020 PR offering to add license "
            "information appears unmerged). Under default copyright that means NO redistribution "
            "right. Fetch and use locally for research; DO NOT commit these files into this "
            "repository. The underlying text is excerpted from Switchboard / BNC / Wall Street "
            "Journal, which carry their own (more restrictive) terms."
        ),
        homepage="https://github.com/mcdm/CommitmentBank",
        citation="de Marneffe, Simons, Tonhauser (2019). The CommitmentBank: Investigating "
                 "projection in naturally occurring discourse. Sinn und Bedeutung 23.",
        vendorable=False,
    ),
]

BY_NAME = {s.name: s for s in SOURCES}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_urllib(url: str, tmp: Path, context=None) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180, context=context) as resp, tmp.open("wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)


def _get_powershell(url: str, tmp: Path) -> None:
    """Windows fallback: .NET/schannel uses the OS trust store, so it survives a TLS-intercepting
    proxy or AV root CA that Python's bundled/certifi roots do not know about."""
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
           f"$ProgressPreference='SilentlyContinue'; "
           f"Invoke-WebRequest -Uri '{url}' -OutFile '{tmp}' -UseBasicParsing -TimeoutSec 300"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise OSError((proc.stderr or proc.stdout or "powershell failed").strip()[:400])


def _strategies():
    """Download strategies in preference order: (name, callable(url, tmp))."""
    yield "urllib", lambda url, tmp: _get_urllib(url, tmp)
    try:
        import certifi
        import ssl
        ctx = ssl.create_default_context(cafile=certifi.where())
        yield "urllib+certifi", lambda url, tmp: _get_urllib(url, tmp, context=ctx)
    except ImportError:
        pass
    if sys.platform == "win32":
        yield "powershell", _get_powershell


def _download(url: str, dest: Path) -> str:
    """Try each strategy until one lands the file. Returns the strategy that worked."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    last = None
    for name, get in _strategies():
        try:
            get(url, tmp)
        except Exception as exc:            # noqa: BLE001 — any transport failure means "try next"
            last = f"{name}: {type(exc).__name__}: {exc}"
            tmp.unlink(missing_ok=True)
            continue
        if tmp.exists() and tmp.stat().st_size > 0:
            tmp.replace(dest)
            return name
        last = f"{name}: empty response"
        tmp.unlink(missing_ok=True)
    raise OSError(last or "no download strategy available")


def fetch(source: Source, force: bool = False) -> list[dict]:
    records = []
    for url, rel in source.files:
        dest = DEST / rel
        if dest.exists() and not force:
            print(f"  = {rel} (present, {dest.stat().st_size:,} bytes)")
        else:
            print(f"  GET {rel} <- {url}")
            try:
                how = _download(url, dest)
            except OSError as exc:
                print(f"  ! FAILED: {exc}")
                print(f"    fetch by hand from {source.homepage} and place at {dest}")
                continue
            print(f"    {dest.stat().st_size:,} bytes (via {how})")
        records.append({
            "source": source.name,
            "url": url,
            "path": rel,
            "sha256": _sha256(dest),
            "bytes": dest.stat().st_size,
            "retrieved": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "license": source.license_id,
            "vendorable": source.vendorable,
        })
    return records


def write_provenance(records: list[dict]) -> None:
    """Merge new records into PROVENANCE.json (keyed by path) and regenerate LICENSES.md."""
    prov_path = DEST / "PROVENANCE.json"
    existing = {}
    if prov_path.exists():
        try:
            existing = {r["path"]: r for r in json.loads(prov_path.read_text("utf-8"))}
        except (ValueError, KeyError):
            existing = {}
    for rec in records:
        existing[rec["path"]] = rec
    prov_path.write_text(
        json.dumps(sorted(existing.values(), key=lambda r: r["path"]), indent=2) + "\n",
        encoding="utf-8")

    present = {r["source"] for r in existing.values()}
    lines = [
        "# External corpora — provenance and licenses",
        "",
        "Generated by `bench/fetch_corpora.py`. These files are NOT part of this repository and",
        "are NOT covered by its MIT license. Each retains its own terms, recorded below.",
        "",
    ]
    for src in SOURCES:
        if src.name not in present:
            continue
        lines += [
            f"## {src.name}",
            "",
            f"- **Homepage:** {src.homepage}",
            f"- **License:** {src.license_id}",
            f"- **May be copied into this repo:** {'YES' if src.vendorable else 'NO'}",
            f"- **Cite as:** {src.citation}",
            "",
            src.license_note,
            "",
        ]
    (DEST / "LICENSES.md").write_text("\n".join(lines), encoding="utf-8")


def cmd_list() -> None:
    for src in SOURCES:
        flag = "VENDORABLE" if src.vendorable else "FETCH-ONLY (do not commit)"
        print(f"\n=== {src.name}  [{src.license_id}]  — {flag}")
        print(f"    {src.homepage}")
        print(f"    why: {src.why}")
        print(f"    license: {src.license_note}")
        print(f"    cite: {src.citation}")
        for url, rel in src.files:
            print(f"      - {rel}")
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print sources + licenses, download nothing")
    ap.add_argument("--only", action="append", metavar="NAME",
                    choices=sorted(BY_NAME), help="fetch only this source (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-download even if the file is present")
    args = ap.parse_args(argv)

    if args.list:
        cmd_list()
        return 0

    wanted = [BY_NAME[n] for n in args.only] if args.only else SOURCES
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for src in wanted:
        print(f"\n=== {src.name}  [{src.license_id}]")
        records += fetch(src, force=args.force)
    write_provenance(records)
    print(f"\nWrote {DEST / 'PROVENANCE.json'} and {DEST / 'LICENSES.md'}")
    print(f"Corpora in {DEST} (gitignored).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
