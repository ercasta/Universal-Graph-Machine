# The Universal Graph Machine — the book

A multi-chapter, mobile-friendly tutorial that explains the Universal Graph
Machine to curious beginners. Built with
[MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and published to
GitHub Pages.

**Live site:** https://ercasta.github.io/Universal-Graph-Machine/

Every code block in the book was **run** against the engine before it was
written down, and every output is copied from a real run. That is the house
rule: a claim with no measurement behind it is an opinion, and it gets marked as
one.

The playground pages run the *real* engine in the reader's browser via
[Pyodide](https://pyodide.org/) — the pure-Python `ugm` package is compiled to a
wheel and loaded with `micropip`. No server, no backend.

They go through `text.load`, `Machine.run`, `Machine.report` and `Machine.why` —
the same four calls `python -m ugm` makes — so the browser is running the engine
rather than an imitation of it.

## Structure

```
book/
  mkdocs.yml            # site config + nav
  requirements.txt      # mkdocs-material
  docs/
    index.md            # landing page
    basic/              # Part 1 — what the world is made of
    rules/              # Part 2 — rules
    wanting/            # Part 3 — goals, plans, acting
    unsure/             # Part 4 — modality, supposition, precedence, norms
    world/              # Part 5 — spans, shapes, channels, tools, time
    watching/           # Part 6 — the agent's own state, stopping, recall, learning
    floor/              # Part 7 — the floor, the bootstrap, zero phases
    horizon/            # Part 8 — the web of meaning, and what is not built
    playground/         # live Pyodide pages
    appendix/           # plain-language concept explainers
    javascripts/        # the playground widget (Pyodide loader)
    stylesheets/        # widget styling
    wheels/             # built ugm wheel (gitignored — CI builds it)
```

## Preview locally

From the repo root:

```bash
python -m pip install build -r book/requirements.txt

# Build the wheel the playground needs, into the docs tree:
python -m build --wheel --outdir book/docs/wheels .

# Serve with live reload:
cd book && mkdocs serve
```

Then open http://127.0.0.1:8000/. The playground's first "Run" downloads Pyodide
from a CDN (a few seconds); after that it's instant.

If you bump the version in `pyproject.toml`, update the `data-wheel` attribute
on both playground pages to match — the filename is pinned there.

## Publishing

`.github/workflows/book.yml` builds the wheel, builds the site, and deploys to
GitHub Pages on every push to `main` that touches `book/`, `ugm/`, or
`pyproject.toml`.

**One-time setup:** in the GitHub repo, go to **Settings → Pages → Build and
deployment → Source** and choose **GitHub Actions**.
